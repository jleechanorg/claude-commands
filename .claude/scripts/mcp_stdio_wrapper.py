#!/usr/bin/env python3
"""
Wrapper script to run WorldArchitect MCP server in stdio-only mode for Claude Code.
This script provides stdio transport for MCP protocol communication.
"""
import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the actual MCP server (go up one level from scripts directory)
mcp_server_path = os.path.join(os.path.dirname(script_dir), "mvp_site", "mcp_api.py")

# Run the MCP server in stdio-only mode for Claude Code
cmd = [sys.executable, mcp_server_path, "--stdio"]
os.execv(sys.executable, [sys.executable] + cmd[1:])
