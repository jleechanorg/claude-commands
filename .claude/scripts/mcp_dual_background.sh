#!/bin/bash
# MCP Dual Transport Background Wrapper
# Purpose: Run MCP (stdio + HTTP) in background with persistent stdin.
# Usage: scripts/mcp_dual_background.sh --host 127.0.0.1 --port 8001 [--other flags]
set -Eeuo pipefail
trap 'echo "ERROR: mcp_dual_background.sh failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT_DEFAULT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$PROJECT_ROOT_DEFAULT}"

# Use shared production environment setup when available
SETUP_SCRIPT="$SCRIPT_DIR/setup_production_env.sh"
if [ -r "$SETUP_SCRIPT" ]; then
    # shellcheck source=/dev/null
    source "$SETUP_SCRIPT"
    if declare -f setup_mcp_production_env >/dev/null 2>&1; then
        setup_mcp_production_env
    fi
else
    echo "WARNING: setup_production_env.sh not found. Using fallback environment." >&2
fi

cd "$PROJECT_ROOT"

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

# Create a named pipe for persistent stdin
branch="${GITHUB_REF_NAME:-local}"
PIPE_DIR="$(mktemp -d -p "${TMPDIR:-/tmp}" "mcp_stdin_${branch}_XXXXXX")"
PIPE_FILE="${PIPE_DIR}/stdin"
mkfifo -m 600 "$PIPE_FILE"

# Keep the pipe open in the background
exec 3<>"$PIPE_FILE"

# Start MCP server with stdin from named pipe
PYTHON_BIN="${VENV_PYTHON:-$PROJECT_ROOT/venv/bin/python}"
"$PYTHON_BIN" "$PROJECT_ROOT/mcp_api.py" --dual "$@" <"$PIPE_FILE" &
MCP_PID=$!

# Function to cleanup on exit
cleanup() {
    if [ -n "$MCP_PID" ] && kill -0 "$MCP_PID" 2>/dev/null; then
        kill "$MCP_PID" 2>/dev/null
    fi
    exec 3>&-
    if [ -d "$PIPE_DIR" ]; then
        rm -rf "$PIPE_DIR" 2>/dev/null
    fi
}

trap cleanup EXIT INT TERM

# Wait for MCP server to exit (or forever in background)
wait "$MCP_PID" 2>/dev/null
