#!/usr/bin/env python3
"""
Entry point for the slash commands MCP server.
This module provides the entry point when the package is run with python -m.
"""

from .server import main

if __name__ == "__main__":
    raise SystemExit(main())
