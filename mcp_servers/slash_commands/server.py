#!/usr/bin/env python3
"""
Consolidated MCP Server for Slash Commands
Unified router pattern replacing 29 individual tool files
Routes MCP calls to actual slash commands via unified_router.py
"""
import asyncio
import sys
from pathlib import Path

# Dynamic import logic to handle both direct execution and package import
if __name__ == "__main__":
    # Direct execution: use absolute imports and add path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from unified_router import main as router_main
else:
    # Package import: use relative imports
    from .unified_router import main as router_main

async def async_main():
    """
    Async server entry point - delegates to unified router.
    All 29 tools now consolidated into single router pattern.
    """
    print("🚀 Starting consolidated MCP server with unified router...", file=sys.stderr)
    print("📋 29 individual tool files → 1 unified router", file=sys.stderr)
    await router_main()

def main():
    """
    Synchronous entry point for pip-installed command
    """
    asyncio.run(async_main())

if __name__ == "__main__":
    # Start the unified router server
    main()
