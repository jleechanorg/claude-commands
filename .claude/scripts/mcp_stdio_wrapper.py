#!/usr/bin/env python3
"""
Wrapper script to run WorldArchitect MCP server in stdio-only mode for Claude Code.
This script provides stdio transport for MCP protocol communication.
"""
import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Compute repo root (parent of .claude/) and resolve PROJECT_ROOT override
repo_root = os.path.dirname(os.path.dirname(script_dir))
project_root = os.environ.get("PROJECT_ROOT", repo_root)
mcp_server_path = os.path.join(project_root, "mcp_api.py")

if not os.path.isfile(mcp_server_path):
    sys.stderr.write(f"ERROR: MCP server not found at {mcp_server_path}\n")
    sys.exit(1)

os.execv(sys.executable, [sys.executable, mcp_server_path, "--stdio"])
