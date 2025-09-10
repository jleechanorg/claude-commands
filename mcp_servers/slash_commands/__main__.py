#!/usr/bin/env python3
"""
Entry point for the slash commands MCP server.
This module provides the entry point when the package is run with python -m.
"""

import asyncio
from .server import main as async_main

def main():
    """Main entry point for the installed package"""
    return asyncio.run(async_main())

if __name__ == "__main__":
    raise SystemExit(main())
