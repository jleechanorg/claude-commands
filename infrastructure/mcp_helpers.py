"""
MCP Client Initialization Helpers

Thread-safe MCP client initialization for Flask applications using Gunicorn
gthread workers. Provides lazy initialization with proper synchronization to
prevent race conditions when multiple threads access the client simultaneously.
"""
import os
import threading
from typing import Any, Optional

from mvp_site.mcp_client import MCPClient


def create_thread_safe_mcp_getter(app, world_logic_module: Optional[Any] = None):
    """
    Create a thread-safe MCP client getter function for a Flask app.

    This factory function sets up the necessary state on the Flask app object
    and returns a getter function that implements double-checked locking for
    thread-safe lazy initialization.

    Args:
        app: Flask application instance
        world_logic_module: Optional world_logic module for direct calls

    Returns:
        Callable that returns the MCP client instance (thread-safe)

    Usage:
        get_mcp_client = create_thread_safe_mcp_getter(app, world_logic)
        client = get_mcp_client()  # Thread-safe, lazy initialization
    """
    # Initialize state on app object
    app._mcp_client = None
    app._mcp_client_lock = threading.Lock()

    def get_mcp_client():
        """
        Lazy initialization of MCP client with proper configuration.

        Thread-safe using double-checked locking pattern to prevent multiple
        client instances being created when using Gunicorn gthread workers.

        Returns:
            MCPClient: Singleton MCP client instance for this worker process
        """
        # Fast path: client already initialized (no lock needed for read)
        if app._mcp_client is None:
            # Acquire lock for initialization
            with app._mcp_client_lock:
                # Double-check after acquiring lock (another thread may have initialized)
                if app._mcp_client is None:
                    skip_http_mode = getattr(
                        app, "_skip_mcp_http", True
                    )  # Default: direct calls
                    mcp_server_url = getattr(
                        app,
                        "_mcp_server_url",
                        os.environ.get("MCP_SERVER_URL", "http://localhost:8000"),
                    )

                    # Use world_logic module for direct calls when skip_http=True
                    world_logic_to_use = None
                    if skip_http_mode:
                        world_logic_to_use = world_logic_module

                    app._mcp_client = MCPClient(
                        mcp_server_url,
                        timeout=300,
                        skip_http=skip_http_mode,
                        world_logic_module=world_logic_to_use,
                    )
        return app._mcp_client

    return get_mcp_client
