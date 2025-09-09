"""
World Logic MCP Server - D&D Game Mechanics

This MCP server exposes WorldArchitect.AI's D&D 5e game mechanics as tools and resources.
Extracted from the monolithic main.py to provide clean API boundaries via MCP protocol.
Tests verified passing locally on mcp_redesign branch.

Architecture:
- MCP server exposing D&D game logic as tools
- Clean separation from HTTP handling (translation layer)
- Maintains all existing functionality through MCP tools
- Supports real-time gaming with stateful sessions

Key MCP Tools:
- create_campaign: Initialize new D&D campaigns
- create_character: Generate player/NPC characters
- process_action: Handle game actions and story progression
- get_campaign_state: Retrieve current game state
- update_campaign: Modify campaign data
- export_campaign: Generate campaign documents
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# WorldArchitect imports
import logging_util
import world_logic

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from firestore_service import json_default_serializer

# Initialize MCP server
server = Server("world-logic")

# Global constants from main.py
KEY_ERROR = "error"
KEY_PROMPT = "prompt"
KEY_SELECTED_PROMPTS = "selected_prompts"
KEY_USER_INPUT = "user_input"


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available MCP tools for D&D game mechanics."""
    return [
        Tool(
            name="create_campaign",
            description="Create a new D&D campaign with character, setting, and story generation",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Firebase user ID"},
                    "title": {"type": "string", "description": "Campaign title"},
                    "character": {
                        "type": "string",
                        "description": "Character description",
                    },
                    "setting": {"type": "string", "description": "Campaign setting"},
                    "description": {
                        "type": "string",
                        "description": "Campaign description",
                    },
                    "selected_prompts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Selected prompt templates",
                    },
                    "custom_options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Custom options (companions, defaultWorld)",
                    },
                },
                "required": ["user_id", "title"],
            },
        ),
        Tool(
            name="get_campaign_state",
            description="Retrieve current campaign state and metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Firebase user ID"},
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign identifier",
                    },
                },
                "required": ["user_id", "campaign_id"],
            },
        ),
        Tool(
            name="process_action",
            description="Process user action and generate AI response for story progression",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Firebase user ID"},
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign identifier",
                    },
                    "user_input": {
                        "type": "string",
                        "description": "User's action or dialogue",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Interaction mode (character/narrator)",
                        "default": "character",
                    },
                },
                "required": ["user_id", "campaign_id", "user_input"],
            },
        ),
        Tool(
            name="update_campaign",
            description="Update campaign metadata and settings",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Firebase user ID"},
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign identifier",
                    },
                    "updates": {"type": "object", "description": "Fields to update"},
                },
                "required": ["user_id", "campaign_id", "updates"],
            },
        ),
        Tool(
            name="export_campaign",
            description="Export campaign to document format (PDF/DOCX/TXT)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Firebase user ID"},
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign identifier",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["pdf", "docx", "txt"],
                        "description": "Export format",
                    },
                },
                "required": ["user_id", "campaign_id", "format"],
            },
        ),
        Tool(
            name="get_campaigns_list",
            description="Retrieve list of user campaigns",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Firebase user ID"}
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_user_settings",
            description="Retrieve user settings and preferences",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Firebase user ID"}
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="update_user_settings",
            description="Update user settings and preferences",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Firebase user ID"},
                    "settings": {"type": "object", "description": "Settings to update"},
                },
                "required": ["user_id", "settings"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:  # noqa: PLR0911
    """Handle MCP tool calls for D&D game mechanics."""
    try:
        if name == "create_campaign":
            return await _create_campaign_tool(arguments)
        if name == "get_campaign_state":
            return await _get_campaign_state_tool(arguments)
        if name == "process_action":
            return await _process_action_tool(arguments)
        if name == "update_campaign":
            return await _update_campaign_tool(arguments)
        if name == "export_campaign":
            return await _export_campaign_tool(arguments)
        if name == "get_campaigns_list":
            return await _get_campaigns_list_tool(arguments)
        if name == "get_user_settings":
            return await _get_user_settings_tool(arguments)
        if name == "update_user_settings":
            return await _update_user_settings_tool(arguments)
        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logging_util.error(f"Tool {name} failed: {e}")

        # Security fix: Only include traceback in development/testing, not production
        is_production = os.environ.get("PRODUCTION_MODE", "").lower() == "true"
        error_response = {
            "error": str(e),
            "tool": name,
        }
        if not is_production:
            error_response["traceback"] = traceback.format_exc()

        return [
            TextContent(
                type="text",
                text=json.dumps(error_response, default=json_default_serializer),
            )
        ]


async def _create_campaign_tool(args: dict[str, Any]) -> list[TextContent]:
    """Create new D&D campaign using unified API."""
    try:
        result = await world_logic.create_campaign_unified(args)
        return [
            TextContent(
                type="text", text=json.dumps(result, default=json_default_serializer)
            )
        ]
    except Exception as e:
        logging_util.error(f"Campaign creation failed: {e}")
        error_response = world_logic.create_error_response(
            f"Failed to create campaign: {str(e)}"
        )
        return [TextContent(type="text", text=json.dumps(error_response))]


async def _get_campaign_state_tool(args: dict[str, Any]) -> list[TextContent]:
    """Get campaign state using unified API."""
    try:
        result = await world_logic.get_campaign_state_unified(args)
        return [
            TextContent(
                type="text", text=json.dumps(result, default=json_default_serializer)
            )
        ]
    except Exception as e:
        logging_util.error(f"Get campaign state failed: {e}")
        error_response = world_logic.create_error_response(
            f"Failed to get campaign state: {str(e)}"
        )
        return [TextContent(type="text", text=json.dumps(error_response))]


async def _process_action_tool(args: dict[str, Any]) -> list[TextContent]:
    """Process user action using unified API."""
    try:
        result = await world_logic.process_action_unified(args)
        return [
            TextContent(
                type="text", text=json.dumps(result, default=json_default_serializer)
            )
        ]
    except Exception as e:
        logging_util.error(f"Process action failed: {e}")
        error_response = world_logic.create_error_response(
            f"Failed to process action: {str(e)}"
        )
        return [TextContent(type="text", text=json.dumps(error_response))]


async def _update_campaign_tool(args: dict[str, Any]) -> list[TextContent]:
    """Update campaign using unified API."""
    try:
        result = await world_logic.update_campaign_unified(args)
        return [
            TextContent(
                type="text", text=json.dumps(result, default=json_default_serializer)
            )
        ]
    except Exception as e:
        logging_util.error(f"Update campaign failed: {e}")
        error_response = world_logic.create_error_response(
            f"Failed to update campaign: {str(e)}"
        )
        return [TextContent(type="text", text=json.dumps(error_response))]


async def _export_campaign_tool(args: dict[str, Any]) -> list[TextContent]:
    """Export campaign using unified API."""
    try:
        result = await world_logic.export_campaign_unified(args)
        return [
            TextContent(
                type="text", text=json.dumps(result, default=json_default_serializer)
            )
        ]
    except Exception as e:
        logging_util.error(f"Export campaign failed: {e}")
        error_response = world_logic.create_error_response(
            f"Failed to export campaign: {str(e)}"
        )
        return [TextContent(type="text", text=json.dumps(error_response))]


async def _get_user_settings_tool(args: dict[str, Any]) -> list[TextContent]:
    """Get user settings using unified API."""
    try:
        result = await world_logic.get_user_settings_unified(args)
        return [
            TextContent(
                type="text", text=json.dumps(result, default=json_default_serializer)
            )
        ]
    except Exception as e:
        logging_util.error(f"Get user settings failed: {e}")
        error_response = world_logic.create_error_response(
            f"Failed to get user settings: {str(e)}"
        )
        return [TextContent(type="text", text=json.dumps(error_response))]


async def _get_campaigns_list_tool(args: dict[str, Any]) -> list[TextContent]:
    """Get campaigns list using unified API."""
    try:
        result = await world_logic.get_campaigns_list_unified(args)
        return [
            TextContent(
                type="text", text=json.dumps(result, default=json_default_serializer)
            )
        ]
    except Exception as e:
        logging_util.error(f"Get campaigns list failed: {e}")
        error_response = world_logic.create_error_response(
            f"Failed to get campaigns list: {str(e)}"
        )
        return [TextContent(type="text", text=json.dumps(error_response))]


async def _update_user_settings_tool(args: dict[str, Any]) -> list[TextContent]:
    """Update user settings using unified API."""
    try:
        result = await world_logic.update_user_settings_unified(args)
        return [
            TextContent(
                type="text", text=json.dumps(result, default=json_default_serializer)
            )
        ]
    except Exception as e:
        logging_util.error(f"Update user settings failed: {e}")
        error_response = world_logic.create_error_response(
            f"Failed to update user settings: {str(e)}"
        )
        return [TextContent(type="text", text=json.dumps(error_response))]


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available MCP resources for D&D content."""
    return [
        Resource(
            uri="worldarchitect://campaigns",
            name="Campaign List",
            description="List of all user campaigns",
            mimeType="application/json",
        ),
        Resource(
            uri="worldarchitect://game-rules",
            name="D&D 5e Rules",
            description="Core D&D 5e rules and mechanics",
            mimeType="text/plain",
        ),
        Resource(
            uri="worldarchitect://prompts",
            name="Story Prompts",
            description="Available story prompt templates",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read MCP resources for D&D content."""
    if uri == "worldarchitect://campaigns":
        # This would require user context, return schema for now
        return json.dumps(
            {
                "schema": "campaigns",
                "description": "User-specific campaign list requires authentication",
            }
        )
    if uri == "worldarchitect://game-rules":
        return "D&D 5e Core Rules: Character attributes, dice mechanics, combat system"
    if uri == "worldarchitect://prompts":
        return json.dumps(
            {
                "available_prompts": ["fantasy", "sci-fi", "horror", "mystery"],
                "custom_options": ["companions", "defaultWorld"],
            }
        )
    raise ValueError(f"Unknown resource: {uri}")


def setup_mcp_logging() -> None:
    """Configure centralized logging for MCP server."""
    log_file = logging_util.LoggingUtil.get_log_file("mcp-server")

    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up formatting
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set level
    root_logger.setLevel(logging.INFO)

    logging_util.info(f"MCP server logging configured: {log_file}")


def run_server():
    """Run the World Logic MCP server."""

    # Auto-detect if we're being run by Claude Code with more specific criteria
    # Only trigger stdio mode when both stdin/stdout are non-TTY AND in specific environments
    # This prevents false positives in CI, I/O redirection, or background processes
    no_tty = not sys.stdin.isatty() or not sys.stdout.isatty()
    claude_env_indicators = (
        os.environ.get("CLAUDE_CODE") == "1"  # Explicit Claude Code flag
        or os.environ.get("MCP_STDIO_MODE") == "1"  # Explicit stdio mode flag
        or "claude" in os.environ.get("USER", "").lower()  # Claude user context
        or "claude" in sys.argv[0].lower()  # Called from claude-related script
    )
    is_claude_code = no_tty and claude_env_indicators

    parser = argparse.ArgumentParser(description="WorldArchitect.AI MCP Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio transport only (for Claude Code)",
    )
    parser.add_argument(
        "--http-only", action="store_true", help="Use HTTP transport only (legacy mode)"
    )
    parser.add_argument(
        "--dual",
        action="store_true",
        default=True,
        help="Run both HTTP and stdio transports simultaneously (default)",
    )
    args = parser.parse_args()

    # Set up logging first
    logging_util.info("🔧 DEBUG: MCP server environment check:")
    logging_util.info(
        "  TESTING environment variable no longer affects production behavior"
    )
    logging_util.info(
        f"  MOCK_SERVICES_MODE={os.environ.get('MOCK_SERVICES_MODE', 'UNSET')}"
    )
    logging_util.info(f"  PRODUCTION_MODE={os.environ.get('PRODUCTION_MODE', 'UNSET')}")

    # Override dual mode if specific transport is requested
    if args.stdio or is_claude_code or args.http_only:
        args.dual = False

    # Auto-enable stdio-only mode when detected or explicitly requested
    if args.stdio or is_claude_code:
        if stdio_server is None:
            logging_util.error(
                "stdio transport not available - install mcp package with stdio support"
            )
            sys.exit(1)

        logging_util.info("Starting MCP server in stdio mode for Claude Code")

        async def main():
            async with stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream, write_stream, server.create_initialization_options()
                )

        asyncio.run(main())
        return

    # Handle dual transport mode (default behavior)
    if args.dual:
        if stdio_server is None:
            logging_util.warning(
                "stdio transport not available - falling back to HTTP-only mode"
            )
        else:
            logging_util.info(
                f"Starting MCP server with dual transport: HTTP on {args.host}:{args.port} + stdio"
            )

            # Run dual transport using threading
            # threading and HTTPServer already imported at module level

            # HTTP handler for dual mode (simplified)
            class DualMCPHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == "/health":
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        health_status = {
                            "status": "healthy",
                            "server": "world-logic",
                            "transport": "dual",
                            "http_port": args.port,
                            "stdio_available": True,
                        }
                        self.wfile.write(json.dumps(health_status).encode())
                    else:
                        self.send_response(404)
                        self.end_headers()

                def log_message(self, format, *args):
                    pass  # Suppress HTTP server logs

            # Start HTTP server in background
            httpd = HTTPServer((args.host, args.port), DualMCPHandler)
            http_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            http_thread.start()
            logging_util.info(
                f"HTTP health endpoint started on http://{args.host}:{args.port}/health"
            )

            # Run stdio transport in main thread
            async def main():
                async with stdio_server() as (read_stream, write_stream):
                    await server.run(
                        read_stream,
                        write_stream,
                        server.create_initialization_options(),
                    )

            try:
                asyncio.run(main())
            except KeyboardInterrupt:
                logging_util.info("Dual transport server shutdown")
                httpd.shutdown()
            return

    # Fallback to HTTP-only mode
    logging_util.info(
        f"Starting World Logic MCP server on {args.host}:{args.port} (HTTP-only mode)"
    )

    # Configure centralized logging
    setup_mcp_logging()

    # Run HTTP server with JSON-RPC support
    # BaseHTTPRequestHandler and HTTPServer already imported at module level

    class MCPHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "healthy", "server": "world-logic"}')
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):  # noqa: N802
            if self.path == "/rpc":
                try:
                    # Parse JSON-RPC request
                    content_length = int(self.headers.get("Content-Length", 0))
                    post_data = self.rfile.read(content_length)
                    request_data = json.loads(post_data.decode("utf-8"))

                    # Handle JSON-RPC request
                    response_data = self._handle_jsonrpc(request_data)

                    # Send response
                    response_json = json.dumps(
                        response_data, default=json_default_serializer
                    )
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(response_json.encode("utf-8"))

                except Exception as e:
                    logging_util.error(f"JSON-RPC error: {e}")

                    # Security fix: Only include traceback in development/testing, not production
                    is_production = (
                        os.environ.get("PRODUCTION_MODE", "").lower() == "true"
                    )
                    error_data = None if is_production else traceback.format_exc()

                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": str(e),
                            "data": error_data,
                        },
                        "id": request_data.get("id")
                        if "request_data" in locals()
                        else None,
                    }
                    response_json = json.dumps(error_response)
                    self.send_response(500)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(response_json.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def _handle_jsonrpc(self, request_data):
            """Handle JSON-RPC 2.0 request"""
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")

            logging_util.info(f"JSON-RPC call: {method} with params: {params}")

            if method == "tools/call":
                # Handle tool call
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                # Use asyncio.run() instead of manual loop management for better performance
                result = asyncio.run(handle_call_tool(tool_name, arguments))

                # Extract text content from result
                if result and len(result) > 0 and hasattr(result[0], "text"):
                    result_data = json.loads(result[0].text)
                else:
                    result_data = {"error": "No result returned"}

                return {"jsonrpc": "2.0", "result": result_data, "id": request_id}

            elif method == "tools/list":
                # Handle tools list using asyncio.run() for better performance
                tools = asyncio.run(handle_list_tools())

                # Convert tools to JSON-serializable format
                tools_data = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in tools
                ]
                return {
                    "jsonrpc": "2.0",
                    "result": {"tools": tools_data},
                    "id": request_id,
                }

            elif method == "resources/list":
                # Handle resources list using asyncio.run() for better performance
                resources = asyncio.run(handle_list_resources())

                # Convert resources to JSON-serializable format
                resources_data = [
                    {
                        "uri": str(resource.uri),  # Convert AnyUrl to string
                        "name": resource.name,
                        "description": resource.description,
                        "mimeType": resource.mimeType,
                    }
                    for resource in resources
                ]
                return {
                    "jsonrpc": "2.0",
                    "result": {"resources": resources_data},
                    "id": request_id,
                }

            elif method == "resources/read":
                # Handle resource read
                uri = params.get("uri")

                # Use asyncio.run() instead of manual loop management for better performance
                result = asyncio.run(handle_read_resource(uri))
                return {"jsonrpc": "2.0", "result": result, "id": request_id}
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id,
                }

        def log_message(self, format, *args):
            # Suppress default logging for cleaner output
            pass

    httpd = HTTPServer((args.host, args.port), MCPHandler)
    logging_util.info(f"MCP JSON-RPC server running on http://{args.host}:{args.port}")
    logging_util.info("Endpoints: /health (GET), /rpc (POST)")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging_util.info("Server shutdown requested")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
