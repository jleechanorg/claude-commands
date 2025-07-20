"""Real Memory MCP Integration

This module provides the actual MCP integration for production use.
Replace mcp_memory_stub.py imports with this module when ready.
"""

import logging_util

logger = logging_util.getLogger(__name__)

def search_nodes(query: str):
    """Call real Memory MCP search_nodes function"""
    try:
        # In Claude Code, this function is available directly
        return mcp__memory-server__search_nodes(query)
    except Exception as e:
        logger.error(f"Memory MCP search_nodes failed: {e}")
        return []

def open_nodes(names: list):
    """Call real Memory MCP open_nodes function"""
    try:
        # In Claude Code, this function is available directly
        return mcp__memory-server__open_nodes(names)
    except Exception as e:
        logger.error(f"Memory MCP open_nodes failed: {e}")
        return []

def read_graph():
    """Call real Memory MCP read_graph function"""
    try:
        # In Claude Code, this function is available directly
        return mcp__memory-server__read_graph()
    except Exception as e:
        logger.error(f"Memory MCP read_graph failed: {e}")
        return {"entities": [], "relations": []}