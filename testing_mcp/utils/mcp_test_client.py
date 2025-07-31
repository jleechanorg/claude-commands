"""
MCP Test Client

Provides utilities for testing MCP servers and protocols in WorldArchitect.AI.
Supports both mock and real MCP server connections.
"""

import asyncio
import logging
import os
import threading
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MCPTestClient:
    """Test client for MCP protocol communication."""

    def __init__(self, server_url: str = None, timeout: int = 30):
        self.server_url = server_url or os.environ.get("MCP_SERVER_URL", "http://localhost:8000")
        self.timeout = timeout
        self.session = None
        self.call_id = 0
        self._call_id_lock = threading.Lock()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Establish connection to MCP server."""
        try:
            self.session = httpx.AsyncClient(timeout=self.timeout)
            # Test connection with ping
            await self.ping()
            logger.info(f"Connected to MCP server at {self.server_url}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise

    async def disconnect(self):
        """Close connection to MCP server."""
        if self.session:
            await self.session.aclose()
            self.session = None

    async def ping(self) -> bool:
        """Test if MCP server is responding."""
        try:
            response = await self.session.get(f"{self.server_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def _next_call_id(self) -> int:
        """Generate next call ID for JSON-RPC (thread-safe)."""
        with self._call_id_lock:
            self.call_id += 1
            return self.call_id

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Call an MCP tool using JSON-RPC 2.0 protocol.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Dict containing the tool response
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self._next_call_id()
        }

        try:
            response = await self.session.post(
                f"{self.server_url}/mcp",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            data = response.json()

            # Check for JSON-RPC error
            if "error" in data:
                error = data["error"]
                raise MCPError(
                    error.get("code", -1),
                    error.get("message", "Unknown error"),
                    error.get("data")
                )

            return data.get("result", {})

        except MCPError:
            # Re-raise MCPError as-is
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling tool {tool_name}: {e}")
            raise MCPError(-32603, f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise MCPError(-32603, f"Internal error: {e}")

    async def get_resource(self, resource_uri: str) -> dict[str, Any]:
        """
        Get an MCP resource.

        Args:
            resource_uri: URI of the resource (e.g., "campaign://123/state")

        Returns:
            Dict containing the resource data
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {
                "uri": resource_uri
            },
            "id": self._next_call_id()
        }

        try:
            response = await self.session.post(
                f"{self.server_url}/mcp",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                error = data["error"]
                raise MCPError(
                    error.get("code", -1),
                    error.get("message", "Unknown error"),
                    error.get("data")
                )

            return data.get("result", {})

        except MCPError:
            # Re-raise MCPError as-is
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting resource {resource_uri}: {e}")
            raise MCPError(-32603, f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Error getting resource {resource_uri}: {e}")
            raise MCPError(-32603, f"Internal error: {e}")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available MCP tools."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self._next_call_id()
        }

        response = await self.session.post(
            f"{self.server_url}/mcp",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        return data.get("result", {}).get("tools", [])

    async def list_resources(self) -> list[dict[str, Any]]:
        """List all available MCP resources."""
        payload = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": self._next_call_id()
        }

        response = await self.session.post(
            f"{self.server_url}/mcp",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        return data.get("result", {}).get("resources", [])


class MCPError(Exception):
    """MCP protocol error."""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")


class WorldArchitectMCPClient(MCPTestClient):
    """
    Specialized MCP client for WorldArchitect.AI testing.
    Provides convenience methods for common game operations.
    """

    async def create_campaign(self, name: str, description: str, user_id: str) -> dict[str, Any]:
        """Create a new campaign."""
        return await self.call_tool("create_campaign", {
            "name": name,
            "description": description,
            "user_id": user_id
        })

    async def get_campaigns(self, user_id: str) -> dict[str, Any]:
        """Get all campaigns for a user."""
        return await self.call_tool("get_campaigns", {
            "user_id": user_id
        })

    async def get_campaign(self, campaign_id: str, user_id: str) -> dict[str, Any]:
        """Get a specific campaign."""
        return await self.call_tool("get_campaign", {
            "campaign_id": campaign_id,
            "user_id": user_id
        })

    async def create_character(self, campaign_id: str, character_data: dict[str, Any]) -> dict[str, Any]:
        """Create a character in a campaign."""
        return await self.call_tool("create_character", {
            "campaign_id": campaign_id,
            "character_data": character_data
        })

    async def process_action(self, session_id: str, action_type: str, action_data: dict[str, Any]) -> dict[str, Any]:
        """Process a game action."""
        return await self.call_tool("process_action", {
            "session_id": session_id,
            "action_type": action_type,
            "action_data": action_data
        })

    async def get_campaign_state(self, campaign_id: str, user_id: str) -> dict[str, Any]:
        """Get campaign state resource."""
        # For testing, we'll use the tool call instead of resource access
        # since the mock server doesn't have user context for resource URIs
        return await self.call_tool("get_campaign_state", {
            "campaign_id": campaign_id,
            "user_id": user_id
        })

    async def get_user_settings(self, user_id: str) -> dict[str, Any]:
        """Get user settings."""
        return await self.call_tool("get_user_settings", {
            "user_id": user_id
        })

    async def update_user_settings(self, user_id: str, settings: dict[str, Any]) -> dict[str, Any]:
        """Update user settings."""
        return await self.call_tool("update_user_settings", {
            "user_id": user_id,
            "settings": settings
        })

    async def export_campaign(self, campaign_id: str, export_format: str, user_id: str) -> dict[str, Any]:
        """Export a campaign."""
        return await self.call_tool("export_campaign", {
            "campaign_id": campaign_id,
            "format": export_format,
            "user_id": user_id
        })


def create_test_client(server_url: str = None, mode: str = "mock") -> WorldArchitectMCPClient:
    """
    Create a test client for the appropriate environment.

    Args:
        server_url: Override server URL
        mode: 'mock' for mock server, 'real' for actual MCP server

    Returns:
        Configured MCP test client
    """
    if mode == "mock":
        url = server_url or "http://localhost:8001"  # Mock server port
    else:
        url = server_url or "http://localhost:8000"  # Real MCP server port

    return WorldArchitectMCPClient(url)


async def wait_for_server(server_url: str, timeout: int = 30) -> bool:
    """
    Wait for MCP server to become available.

    Args:
        server_url: URL of the MCP server
        timeout: Maximum time to wait in seconds

    Returns:
        True if server becomes available, False otherwise
    """
    async with MCPTestClient(server_url) as client:
        for _ in range(timeout):
            if await client.ping():
                return True
            await asyncio.sleep(1)
    return False
