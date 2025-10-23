#!/bin/bash
# MCP Dual Transport Background Wrapper
# Purpose: Run MCP (stdio + HTTP) in background with persistent stdin.
# Usage: scripts/mcp_dual_background.sh --host 127.0.0.1 --port 8001 [--other flags]
set -Eeuo pipefail
trap 'echo "ERROR: mcp_dual_background.sh failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use shared production environment setup
if [[ -f "$SCRIPT_DIR/setup_production_env.sh" ]]; then
  source "$SCRIPT_DIR/setup_production_env.sh"
  setup_mcp_production_env
else
  echo "❌ Missing $SCRIPT_DIR/setup_production_env.sh" >&2
  exit 1
fi

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

# Create a named pipe for persistent stdin
branch="${GITHUB_REF_NAME:-local}"
PIPE_FILE="$(mktemp -u "/tmp/mcp_stdin_${branch}_XXXX")"
umask 077
mkfifo "$PIPE_FILE"

# Keep the pipe open in the background
exec 3<>"$PIPE_FILE"

# Start MCP server with stdin from named pipe
: "${PROJECT_ROOT:="$REPO_ROOT"}"

"$REPO_ROOT/venv/bin/python" "$PROJECT_ROOT/mcp_api.py" --dual "$@" <"$PIPE_FILE" &
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
