#!/bin/bash
# MCP Dual Transport Background Wrapper
# Provides persistent stdin for dual-mode MCP server in background execution

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Use shared production environment setup
source "$SCRIPT_DIR/setup_production_env.sh"
setup_mcp_production_env

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

# Create a named pipe for persistent stdin
PIPE_FILE="/tmp/mcp_stdin_$$"
mkfifo "$PIPE_FILE"

# Keep the pipe open in the background
exec 3<>"$PIPE_FILE"

# Start MCP server with stdin from named pipe
venv/bin/python mvp_site/mcp_api.py --dual "$@" <"$PIPE_FILE" &
MCP_PID=$!

# Function to cleanup on exit
cleanup() {
    if [ -n "$MCP_PID" ] && kill -0 "$MCP_PID" 2>/dev/null; then
        kill "$MCP_PID" 2>/dev/null
    fi
    if [ -p "$PIPE_FILE" ]; then
        rm -f "$PIPE_FILE" 2>/dev/null
    fi
    exec 3>&-
}

trap cleanup EXIT INT TERM

# Wait for MCP server to exit (or forever in background)
wait "$MCP_PID" 2>/dev/null
