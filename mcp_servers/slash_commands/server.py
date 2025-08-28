#!/usr/bin/env python3
"""
Consolidated MCP Server for Slash Commands
Unified router pattern replacing 29 individual tool files
Routes MCP calls to actual slash commands via unified_router.py
"""
import asyncio
import sys
from pathlib import Path

# Fix relative import issue - use absolute import when run as main script
if __name__ == "__main__":
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from mcp_servers.slash_commands.unified_router import main as router_main
else:
    from .unified_router import main as router_main

async def main():
    """
    Main server entry point - delegates to unified router.
    All 29 tools now consolidated into single router pattern.
    """
    print("🚀 Starting consolidated MCP server with unified router...", file=sys.stderr)
    print("📋 29 individual tool files → 1 unified router", file=sys.stderr)
    await router_main()

if __name__ == "__main__":
    # Start the unified router server
    asyncio.run(main())