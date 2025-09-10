#!/usr/bin/env python3
"""
Entry point for claude-slash-commands-mcp package
"""
import asyncio
from .server import main as server_main

def main():
    """Main entry point for the installed package"""
    asyncio.run(server_main())

if __name__ == "__main__":
    main()
