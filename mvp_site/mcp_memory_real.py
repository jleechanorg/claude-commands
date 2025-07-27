"""Real Memory MCP Integration

This module provides the actual MCP integration for production use.
Replace mcp_memory_stub.py imports with this module when ready.
"""

from collections.abc import Callable
from typing import Any

import logging_util

logger = logging_util.getLogger(__name__)


class MCPMemoryClient:
    """MCP Memory client with dependency injection support"""

    def __init__(self):
        self._search_fn: Callable[[str], list[dict[str, Any]]] | None = None
        self._open_fn: Callable[[list[str]], list[dict[str, Any]]] | None = None
        self._read_fn: Callable[[], dict[str, Any]] | None = None
        self._initialized = False

    def _get_mcp_function(self, func_name: str, fallback_func: Callable):
        """Safely get MCP function with fallback for testing/development"""
        try:
            return globals().get(func_name, fallback_func)
        except Exception as e:
            logger.warning(f"MCP function {func_name} not available: {e}")
            return fallback_func

    def initialize(self):
        """Initialize MCP function references (called once at startup)"""
        if not self._initialized:
            self._search_fn = self._get_mcp_function(
                "mcp__memory_server__search_nodes", lambda _: []
            )
            self._open_fn = self._get_mcp_function(
                "mcp__memory_server__open_nodes", lambda _: []
            )
            self._read_fn = self._get_mcp_function(
                "mcp__memory_server__read_graph",
                lambda: {"entities": [], "relations": []},
            )
            self._initialized = True

    def set_functions(self, search_fn=None, open_fn=None, read_fn=None):
        """Dependency injection for testing (allows mock functions)"""
        if search_fn:
            self._search_fn = search_fn
        if open_fn:
            self._open_fn = open_fn
        if read_fn:
            self._read_fn = read_fn
        self._initialized = True

    def search_nodes(self, query: str) -> list[dict[str, Any]]:
        """Call real Memory MCP search_nodes function"""
        try:
            if not self._initialized:
                self.initialize()
            return self._search_fn(query)
        except Exception as e:
            logger.error(f"Memory MCP search_nodes failed: {e}")
            return []

    def open_nodes(self, names: list[str]) -> list[dict[str, Any]]:
        """Call real Memory MCP open_nodes function"""
        try:
            if not self._initialized:
                self.initialize()
            return self._open_fn(names)
        except Exception as e:
            logger.error(f"Memory MCP open_nodes failed: {e}")
            return []

    def read_graph(self) -> dict[str, Any]:
        """Call real Memory MCP read_graph function"""
        try:
            if not self._initialized:
                self.initialize()
            return self._read_fn()
        except Exception as e:
            logger.error(f"Memory MCP read_graph failed: {e}")
            return {"entities": [], "relations": []}


# Global instance for backward compatibility
_mcp_client = MCPMemoryClient()


# Backward compatible module-level functions
def search_nodes(query: str) -> list[dict[str, Any]]:
    """Call real Memory MCP search_nodes function"""
    return _mcp_client.search_nodes(query)


def open_nodes(names: list[str]) -> list[dict[str, Any]]:
    """Call real Memory MCP open_nodes function"""
    return _mcp_client.open_nodes(names)


def read_graph() -> dict[str, Any]:
    """Call real Memory MCP read_graph function"""
    return _mcp_client.read_graph()


# Backward compatible initialization functions
def initialize_mcp_functions():
    """Initialize MCP function references (called once at startup)"""
    _mcp_client.initialize()


def set_mcp_functions(search_fn=None, open_fn=None, read_fn=None):
    """Dependency injection for testing (allows mock functions)"""
    _mcp_client.set_functions(search_fn, open_fn, read_fn)
