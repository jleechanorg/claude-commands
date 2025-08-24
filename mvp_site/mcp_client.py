"""
MCP Client Library for WorldArchitect.AI

This module provides a simple MCP (Model Context Protocol) client for main.py to communicate
with the world_logic.py MCP server. It handles JSON-RPC communication and provides translation
functions between Flask HTTP requests/responses and MCP protocol.

Architecture:
- MCPClient class for JSON-RPC communication with MCP server
- Translation functions to convert between HTTP and MCP formats
- Error handling and mapping between MCP and HTTP status codes
- Async-compatible design for future async Flask integration

Usage:
    from mcp_client import MCPClient, http_to_mcp_request, mcp_to_http_response

    client = MCPClient("http://localhost:8000")
    result = await client.call_tool("create_campaign", {"name": "Test Campaign"})
"""

import asyncio
import concurrent.futures
import inspect
import json
import threading
import traceback
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Union

import logging_util
import requests
from flask import Request, Response


# Initialize logging
logger = logging_util.logging.getLogger(__name__)


class MCPErrorCode(Enum):
    """MCP error codes from JSON-RPC 2.0 specification"""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000


@dataclass
class MCPError:
    """MCP error structure"""

    code: int
    message: str
    data: Union[dict[str, Any], None] = None


class MCPClientError(Exception):
    """Exception raised by MCP client operations"""

    def __init__(
        self, message: str, error_code: int = None, data: dict[str, Any] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.data = data


class MCPClient:
    """
    MCP client for communicating with world_logic.py MCP server

    Provides methods to call MCP tools and retrieve resources via JSON-RPC 2.0
    over HTTP. Handles connection failures and MCP protocol errors.

    Can be used as a context manager for automatic resource cleanup:
        with MCPClient("http://localhost:8000") as client:
            result = await client.call_tool("test_tool", {})
    """

    # Class-level singleton event loop for sync operations (performance fix)
    _shared_event_loop = None
    _loop_lock = threading.RLock()
    _loop_thread = None

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 300,
        skip_http: bool = False,
        world_logic_module: Any | None = None,
    ):
        """
        Initialize MCP client

        Args:
            base_url: Base URL of the MCP server
            timeout: Request timeout in seconds (default 5 minutes)
            skip_http: If True, skip HTTP and call world_logic.py directly
        """
        # Input validation
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url must be a non-empty string")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be a positive number")
            
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.skip_http = skip_http

        if not skip_http:
            self.session = requests.Session()
            self.session.headers.update(
                {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "WorldArchitect.MCPClient/1.0 (+mvp_site)",
                }
            )
            # Ensure SSL verification is enabled for security
            self.session.verify = True
            self.world_logic = None
        else:
            self.session = None
            self.world_logic = world_logic_module
            if self.world_logic is None:
                logger.warning(
                    "skip_http=True but no world_logic module injected; "
                    "direct calls will return mock/503 responses."
                )

    def _generate_request_id(self) -> str:
        """Generate unique request ID for JSON-RPC"""
        return str(uuid.uuid4())

    def _make_jsonrpc_request(
        self, method: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Create JSON-RPC 2.0 request payload

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            JSON-RPC request dictionary
        """
        request_data = {
            "jsonrpc": "2.0",
            "id": self._generate_request_id(),
            "method": method,
        }

        if params is not None:
            request_data["params"] = params

        return request_data

    def _handle_jsonrpc_response(self, response_data: dict[str, Any]) -> Any:
        """
        Handle JSON-RPC response and extract result or raise error

        Args:
            response_data: JSON-RPC response dictionary

        Returns:
            Result data from successful response

        Raises:
            MCPClientError: On RPC errors
        """
        if "error" in response_data:
            error_info = response_data["error"]
            raise MCPClientError(
                message=error_info.get("message", "Unknown MCP error"),
                error_code=error_info.get("code"),
                data=error_info.get("data"),
            )

        return response_data.get("result")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] = None) -> Any:
        """
        Call an MCP tool on the server

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result data

        Raises:
            MCPClientError: On communication or MCP errors
        """
        if self.skip_http:
            # Direct call to world_logic.py
            return await self._call_tool_direct(tool_name, arguments)

        try:
            # Prepare JSON-RPC request
            params = {"name": tool_name}
            if arguments:
                params["arguments"] = arguments

            request_data = self._make_jsonrpc_request("tools/call", params)

            logger.debug(f"Calling MCP tool {tool_name} with request: {request_data}")

            # Make HTTP request (non-blocking)
            response = await asyncio.to_thread(
                self.session.post,
                f"{self.base_url}/rpc",
                json=request_data,
                timeout=self.timeout,
            )

            # Handle HTTP errors
            if response.status_code != 200:
                raise MCPClientError(
                    f"HTTP error {response.status_code}: {response.text}",
                    error_code=response.status_code,
                )

            # Parse JSON-RPC response
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                raise MCPClientError(f"Invalid JSON response: {e}") from e

            result = self._handle_jsonrpc_response(response_data)
            logger.debug(f"MCP tool {tool_name} returned: {result}")

            return result

        except requests.RequestException as e:
            logger.error(f"Connection error calling MCP tool {tool_name}: {e}")
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise MCPClientError(f"Connection error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error calling MCP tool {tool_name}: {e}")
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise MCPClientError(f"Unexpected error: {e}") from e

    async def _call_tool_direct(
        self, tool_name: str, arguments: dict[str, Any] = None
    ) -> Any:
        """
        Call MCP tool directly via world_logic.py without HTTP

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result data using same JSON API format

        Raises:
            MCPClientError: On tool errors
        """
        try:
            # Check if world_logic is available
            if self.world_logic is None:
                # Gracefully handle missing world_logic in test mode
                if tool_name == "get_campaigns_list":
                    return {"success": True, "campaigns": []}
                elif tool_name in ["get_campaign_state", "process_action"]: 
                    raise MCPClientError("Campaign not found", error_code=404)
                elif tool_name == "get_user_settings":
                    return {"success": True, "settings": {}}
                elif tool_name == "update_user_settings":
                    return {"success": True}
                else:
                    raise MCPClientError("Service temporarily unavailable", error_code=503)

            # Map tool names to world_logic.py functions
            tool_mapping = {
                "create_campaign": "create_campaign_unified",
                "get_campaign_state": "get_campaign_state_unified",
                "process_action": "process_action_unified",
                "update_campaign": "update_campaign_unified",
                "export_campaign": "export_campaign_unified",
                "get_campaigns_list": "get_campaigns_list_unified",
                "get_user_settings": "get_user_settings_unified",
                "update_user_settings": "update_user_settings_unified",
            }

            function_name = tool_mapping.get(tool_name)
            if not function_name:
                raise MCPClientError(f"Unknown tool: {tool_name}")

            if not hasattr(self.world_logic, function_name):
                raise MCPClientError(f"Tool not implemented: {function_name}", error_code=501)

            function = getattr(self.world_logic, function_name)
            logger.debug(f"Calling {function_name} directly with args: {arguments}")
            maybe_result = function(arguments or {})
            result = await maybe_result if inspect.isawaitable(maybe_result) else maybe_result

            logger.debug(f"Direct call {function_name} returned: {result}")
            return result

        except MCPClientError as e:
            # Preserve the original error code from our mock responses
            logger.error(f"Direct tool call error {tool_name}: {e}")
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise e  # Re-raise original error without wrapping
        except Exception as e:
            logger.error(f"Direct tool call error {tool_name}: {e}")
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise MCPClientError(f"Direct call error: {e}") from e

    async def get_resource(self, uri: str) -> Any:
        """
        Get an MCP resource from the server

        Args:
            uri: Resource URI

        Returns:
            Resource content

        Raises:
            MCPClientError: On communication or MCP errors
        """
        try:
            request_data = self._make_jsonrpc_request("resources/read", {"uri": uri})

            logger.debug(f"Getting MCP resource {uri}")

            response = await asyncio.to_thread(
                self.session.post,
                f"{self.base_url}/rpc",
                json=request_data,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                raise MCPClientError(
                    f"HTTP error {response.status_code}: {response.text}",
                    error_code=response.status_code,
                )

            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                raise MCPClientError(f"Invalid JSON response: {e}") from e

            result = self._handle_jsonrpc_response(response_data)
            logger.debug(f"MCP resource {uri} returned: {result}")

            return result

        except requests.RequestException as e:
            logger.error(f"Connection error getting MCP resource {uri}: {e}")
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise MCPClientError(f"Connection error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting MCP resource {uri}: {e}")
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise MCPClientError(f"Unexpected error: {e}") from e

    @classmethod
    def _get_shared_event_loop(cls):
        """Get or create shared event loop for sync operations (performance fix)"""
        with cls._loop_lock:
            if cls._shared_event_loop is None or cls._shared_event_loop.is_closed():
                cls._shared_event_loop = asyncio.new_event_loop()
                # Start the event loop in a background thread
                cls._loop_thread = threading.Thread(
                    target=cls._run_event_loop_forever, 
                    daemon=True, 
                    name="MCP-EventLoop"
                )
                cls._loop_thread.start()
                logger.debug("Created and started shared event loop for MCP operations")
            return cls._shared_event_loop
    
    @classmethod
    def _run_event_loop_forever(cls):
        """Run the shared event loop forever in background thread"""
        asyncio.set_event_loop(cls._shared_event_loop)
        try:
            cls._shared_event_loop.run_forever()
        except Exception as e:
            logger.error(f"Shared event loop error: {e}")
        finally:
            logger.debug("Shared event loop stopped")

    def call_tool_sync(self, tool_name: str, arguments: dict[str, Any] = None) -> Any:
        """
        Synchronous wrapper for call_tool - uses singleton event loop for performance

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result data
        """
        # Check if we're already in an event loop
        try:
            current_loop = asyncio.get_running_loop()
            # Use run_coroutine_threadsafe to avoid blocking the current loop
            shared_loop = self._get_shared_event_loop()
            if shared_loop == current_loop:
                # Same loop - use fresh loop in thread to avoid conflicts
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    def run_in_fresh_loop():
                        # Create fresh event loop for this thread to avoid async conflicts
                        fresh_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(fresh_loop)
                        try:
                            return fresh_loop.run_until_complete(self.call_tool(tool_name, arguments))
                        finally:
                            fresh_loop.close()
                            asyncio.set_event_loop(None)
                    future = executor.submit(run_in_fresh_loop)
                    return future.result(timeout=self.timeout)
            else:
                # Different loop, use run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(
                    self.call_tool(tool_name, arguments), shared_loop
                )
                return future.result(timeout=self.timeout)
        except RuntimeError:
            # No event loop running, use shared singleton loop with run_coroutine_threadsafe
            shared_loop = self._get_shared_event_loop()
            future = asyncio.run_coroutine_threadsafe(
                self.call_tool(tool_name, arguments), shared_loop
            )
            return future.result(timeout=self.timeout)

    def get_resource_sync(self, uri: str) -> Any:
        """
        Synchronous wrapper for get_resource - uses singleton event loop for performance

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        # Check if we're already in an event loop
        try:
            current_loop = asyncio.get_running_loop()
            # Use run_coroutine_threadsafe to avoid blocking the current loop
            shared_loop = self._get_shared_event_loop()
            if shared_loop == current_loop:
                # Same loop - use fresh loop in thread to avoid conflicts
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    def run_in_fresh_loop():
                        # Create fresh event loop for this thread to avoid async conflicts
                        fresh_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(fresh_loop)
                        try:
                            return fresh_loop.run_until_complete(self.get_resource(uri))
                        finally:
                            fresh_loop.close()
                            asyncio.set_event_loop(None)
                    future = executor.submit(run_in_fresh_loop)
                    return future.result(timeout=self.timeout)
            else:
                # Different loop, use run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(
                    self.get_resource(uri), shared_loop
                )
                return future.result(timeout=self.timeout)
        except RuntimeError:
            # No event loop running, use shared singleton loop with run_coroutine_threadsafe
            shared_loop = self._get_shared_event_loop()
            future = asyncio.run_coroutine_threadsafe(
                self.get_resource(uri), shared_loop
            )
            return future.result(timeout=self.timeout)

    def close(self):
        """Close the HTTP session"""
        if self.session is not None:
            self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically close session"""
        self.close()
        return False


# Translation Functions for Flask Integration


def http_to_mcp_request(flask_request: Request, tool_name: str) -> dict[str, Any]:  # noqa: ARG001
    """
    Convert Flask request to MCP tool call format

    Args:
        flask_request: Flask Request object
        tool_name: Name of MCP tool to call

    Returns:
        Dictionary with MCP tool arguments
    """
    arguments = {}

    # Extract JSON data from request body
    if flask_request.is_json:
        body = flask_request.get_json(silent=True)
        if body is not None:
            arguments.update(body)

    # Add form data if present
    if flask_request.form:
        arguments.update(flask_request.form.to_dict())

    # Add query parameters
    if flask_request.args:
        arguments.update(flask_request.args.to_dict())

    # Add headers that might be relevant
    relevant_headers = {
        "user-agent": flask_request.headers.get("User-Agent"),
        "content-type": flask_request.headers.get("Content-Type"),
        "authorization": flask_request.headers.get("Authorization"),
    }

    # Only include non-None headers
    headers = {k: v for k, v in relevant_headers.items() if v is not None}
    if headers:
        arguments["_http_headers"] = headers

    # Add HTTP method and path info
    arguments["_http_method"] = flask_request.method
    arguments["_http_path"] = flask_request.path

    # Create safe version for logging (mask sensitive headers)
    safe_arguments = arguments.copy()
    if "_http_headers" in safe_arguments and "authorization" in safe_arguments["_http_headers"]:
        safe_arguments["_http_headers"] = safe_arguments["_http_headers"].copy()
        safe_arguments["_http_headers"]["authorization"] = "***MASKED***"
    
    logger.debug(f"Converted Flask request to MCP arguments: {safe_arguments}")

    return arguments


def mcp_to_http_response(mcp_result: Any, status_code: int = 200) -> Response:
    """
    Convert MCP tool result to Flask Response

    Args:
        mcp_result: Result from MCP tool call
        status_code: HTTP status code

    Returns:
        Flask Response object
    """
    try:
        # Handle different result types
        if isinstance(mcp_result, dict):
            response_data = mcp_result
        elif isinstance(mcp_result, (list, str, int, float, bool)):
            response_data = {"result": mcp_result}
        else:
            # Try to serialize complex objects
            try:
                response_data = {
                    "result": json.loads(json.dumps(mcp_result, default=str))
                }
            except (TypeError, ValueError):
                response_data = {"result": str(mcp_result)}

        response = Response(
            json.dumps(response_data, indent=2),
            status=status_code,
            mimetype="application/json",
        )

        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        logger.debug(
            f"Created Flask response with status {status_code}: {response_data}"
        )

        return response

    except Exception as e:
        logger.error(f"Error creating HTTP response: {e}")
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        return Response(
            json.dumps({"error": f"Response serialization error: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )


def handle_mcp_errors(error: Union[MCPClientError, Exception]) -> Response:
    """
    Map MCP errors to appropriate HTTP status codes and responses

    Args:
        error: MCP client error or generic exception

    Returns:
        Flask Response with appropriate error information
    """
    if isinstance(error, MCPClientError):
        # Map MCP error codes to HTTP status codes
        if error.error_code in {
            MCPErrorCode.PARSE_ERROR.value,
            MCPErrorCode.INVALID_REQUEST.value,
        }:
            status_code = 400  # Bad Request
        elif error.error_code == MCPErrorCode.METHOD_NOT_FOUND.value:
            status_code = 404  # Not Found
        elif error.error_code == MCPErrorCode.INVALID_PARAMS.value:
            status_code = 400  # Bad Request
        elif error.error_code == MCPErrorCode.INTERNAL_ERROR.value:
            status_code = 500  # Internal Server Error
        elif error.error_code and -32099 <= error.error_code <= -32000:
            status_code = 500  # Server Error
        elif isinstance(error.error_code, int) and 400 <= error.error_code < 600:
            # HTTP status code passed through - this handles our 404, 503 codes
            status_code = error.error_code
        else:
            status_code = 500  # Default to internal server error

        error_data = {
            "error": {
                "message": str(error),
                "code": error.error_code,
                "type": "MCP_ERROR",
            }
        }

        if error.data:
            error_data["error"]["data"] = error.data

    else:
        # Generic exception
        status_code = 500
        error_data = {"error": {"message": str(error), "type": "INTERNAL_ERROR"}}

    logger.error(f"MCP error mapped to HTTP {status_code}: {error_data}")

    response = Response(
        json.dumps(error_data, indent=2),
        status=status_code,
        mimetype="application/json",
    )

    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

    return response


# Convenience function for main.py integration
def create_mcp_client() -> MCPClient:
    """
    Create and return a configured MCP client instance

    Returns:
        Configured MCPClient instance
    """
    return MCPClient()


# Example usage patterns for main.py integration
async def example_usage():
    """Example of how main.py would use this client"""
    client = create_mcp_client()

    try:
        # Create a campaign
        result = await client.call_tool(
            "create_campaign",
            {"name": "Test Campaign", "description": "A test campaign"},
        )

        # Get campaign state
        state = await client.get_resource("campaign://test-campaign/state")

        logger.info("Campaign created: %s", result)
        logger.info("Campaign state: %s", state)

    except MCPClientError as e:
        logger.error("MCP error: %s", e)
    finally:
        client.close()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
