#!/bin/bash
# Start WorldArchitect MCP Server in Production Mode (for Claude Code integration)
# This script provides stdio MCP server for AI assistant integration
# Fail fast and surface errors
set -Eeuo pipefail
trap 'echo "ERROR: start_mcp_production.sh failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

exec "$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/mcp_api.py" --dual "$@"
