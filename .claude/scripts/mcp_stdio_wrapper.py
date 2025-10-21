#!/usr/bin/env python3
"""
Wrapper script to run WorldArchitect MCP server in stdio-only mode for Claude Code.
This script provides stdio transport for MCP protocol communication.
"""
import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the actual MCP server (go up two levels: .claude/scripts -> .claude -> project root)
project_root = os.path.dirname(os.path.dirname(script_dir))
mcp_server_path = os.path.join(project_root, "mvp_site", "mcp_api.py")

# Validate that the MCP server exists
if not os.path.isfile(mcp_server_path):
    print(f"ERROR: MCP server not found at {mcp_server_path}", file=sys.stderr)
    sys.exit(1)

# Run the MCP server in stdio-only mode for Claude Code
cmd = [sys.executable, mcp_server_path, "--stdio"]
os.execv(sys.executable, [sys.executable] + cmd[1:])
