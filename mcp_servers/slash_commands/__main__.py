#!/usr/bin/env python3
"""
Entry point for claude-slash-commands-mcp package
"""
from .server import main as server_main

def main():
    """Main entry point for the installed package"""
    server_main()

if __name__ == "__main__":
    main()
