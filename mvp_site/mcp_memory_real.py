"""Real Memory MCP Integration

This module provides the actual MCP integration for production use.
Replace mcp_memory_stub.py imports with this module when ready.

FAIL-FAST DESIGN: If MCP functions are not available or fail, errors propagate
to the caller rather than silently returning empty data.
"""

from collections.abc import Callable
from typing import Any

from mvp_site import logging_util

logger = logging_util.getLogger(__name__)


class MCPMemoryError(Exception):
    """Raised when MCP memory operations fail."""


class MCPMemoryClient:
    """MCP Memory client with dependency injection support.

    FAIL-FAST: All operations raise MCPMemoryError on failure instead of
    returning empty data. Callers must handle errors explicitly.
    """

    def __init__(self):
        self._search_fn: Callable[[str], list[dict[str, Any]]] | None = None
        self._open_fn: Callable[[list[str]], list[dict[str, Any]]] | None = None
        self._read_fn: Callable[[], dict[str, Any]] | None = None
        self._initialized = False

    def _get_mcp_function(self, func_name: str) -> Callable | None:
        """Get MCP function from globals - returns None if not found or not callable."""
        fn = globals().get(func_name)
        return fn if callable(fn) else None

    def initialize(self):
        """Initialize MCP function references (called once at startup).

        Raises:
            MCPMemoryError: If NO MCP functions are available.
        """
        if self._initialized:
            return

        self._search_fn = self._get_mcp_function("mcp__memory_server__search_nodes")
        self._open_fn = self._get_mcp_function("mcp__memory_server__open_nodes")
        self._read_fn = self._get_mcp_function("mcp__memory_server__read_graph")

        if self._search_fn is None and self._open_fn is None and self._read_fn is None:
            raise MCPMemoryError(
                "No MCP memory functions available. Ensure MCP server is running "
                "and functions are registered in globals."
            )

        self._initialized = True

    def set_functions(
        self,
        search_fn: Callable[[str], list[dict[str, Any]]] | None = None,
        open_fn: Callable[[list[str]], list[dict[str, Any]]] | None = None,
        read_fn: Callable[[], dict[str, Any]] | None = None,
    ):
        """Dependency injection for testing (allows partial overrides).

        At least one MCP function must be provided. Any provided functions
        replace the existing references; omitted functions keep their current
        values. After injection, `_initialized` is marked True to bypass
        globals-based initialization.
        """
        if search_fn is None and open_fn is None and read_fn is None:
            raise MCPMemoryError(
                "At least one MCP function must be provided when injecting dependencies."
            )

        if search_fn is not None:
            self._search_fn = search_fn
        if open_fn is not None:
            self._open_fn = open_fn
        if read_fn is not None:
            self._read_fn = read_fn
        self._initialized = True

    def search_nodes(self, query: str) -> list[dict[str, Any]]:
        """Call real Memory MCP search_nodes function.

        Raises:
            MCPMemoryError: If MCP not initialized or search function unavailable.
        """
        if not self._initialized:
            self.initialize()

        if self._search_fn is None:
            raise MCPMemoryError(
                "MCP search_nodes function not available. "
                "Initialize MCP or use set_functions() for testing."
            )

        # Let exceptions propagate - caller should handle failures
        return self._search_fn(query)

    def open_nodes(self, names: list[str]) -> list[dict[str, Any]]:
        """Call real Memory MCP open_nodes function.

        Raises:
            MCPMemoryError: If MCP not initialized or open function unavailable.
        """
        if not self._initialized:
            self.initialize()

        if self._open_fn is None:
            raise MCPMemoryError(
                "MCP open_nodes function not available. "
                "Initialize MCP or use set_functions() for testing."
            )

        # Let exceptions propagate - caller should handle failures
        return self._open_fn(names)

    def read_graph(self) -> dict[str, Any]:
        """Call real Memory MCP read_graph function.

        Raises:
            MCPMemoryError: If MCP not initialized or read function unavailable.
        """
        if not self._initialized:
            self.initialize()

        if self._read_fn is None:
            raise MCPMemoryError(
                "MCP read_graph function not available. "
                "Initialize MCP or use set_functions() for testing."
            )

        # Let exceptions propagate - caller should handle failures
        return self._read_fn()


# Global instance for backward compatibility
_mcp_client = MCPMemoryClient()


# Backward compatible module-level functions
def search_nodes(query: str) -> list[dict[str, Any]]:
    """Call real Memory MCP search_nodes function.

    Raises:
        MCPMemoryError: If MCP not available or operation fails.
    """
    return _mcp_client.search_nodes(query)


def open_nodes(names: list[str]) -> list[dict[str, Any]]:
    """Call real Memory MCP open_nodes function.

    Raises:
        MCPMemoryError: If MCP not available or operation fails.
    """
    return _mcp_client.open_nodes(names)


def read_graph() -> dict[str, Any]:
    """Call real Memory MCP read_graph function.

    Raises:
        MCPMemoryError: If MCP not available or operation fails.
    """
    return _mcp_client.read_graph()


# Backward compatible initialization functions
def initialize_mcp_functions():
    """Initialize MCP function references (called once at startup).

    Raises:
        MCPMemoryError: If required MCP functions are not available.
    """
    _mcp_client.initialize()


def set_mcp_functions(
    search_fn: Callable[[str], list[dict[str, Any]]] | None = None,
    open_fn: Callable[[list[str]], list[dict[str, Any]]] | None = None,
    read_fn: Callable[[], dict[str, Any]] | None = None,
):
    """Dependency injection for testing (allows partial overrides).

    At least one MCP function must be provided; omitted functions keep their
    existing values.
    """
    _mcp_client.set_functions(search_fn, open_fn, read_fn)
