#!/usr/bin/env python3
"""
Wrapper script to run WorldArchitect MCP server in stdio-only mode for Claude Code.
This script provides stdio transport for MCP protocol communication.
"""
import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the actual MCP server (prefer PROJECT_ROOT, fallback to sanitized default)
project_root_hint = os.environ.get("PROJECT_ROOT", "mvp_site")

if os.path.isabs(project_root_hint):
    candidate_path = os.path.join(project_root_hint, "mcp_api.py")
else:
    repo_root = os.path.dirname(script_dir)
    candidate_path = os.path.join(repo_root, project_root_hint, "mcp_api.py")

if not os.path.exists(candidate_path):
    alt_candidate = os.path.join(os.path.dirname(script_dir), "mcp_api.py")
    if os.path.exists(alt_candidate):
        candidate_path = alt_candidate
    else:
        sys.stderr.write(f"Error: MCP server not found at {candidate_path}\n")
        sys.exit(1)

# Run the MCP server in stdio-only mode for Claude Code
os.execv(sys.executable, [sys.executable, candidate_path, "--stdio"])
