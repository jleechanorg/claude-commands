#!/bin/bash
# MCP Dual Transport Background Wrapper
# Purpose: Run MCP (stdio + HTTP) in background with persistent stdin.
# Usage: scripts/mcp_dual_background.sh --host 127.0.0.1 --port 8001 [--other flags]
set -Eeuo pipefail
trap 'echo "ERROR: mcp_dual_background.sh failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Use shared production environment setup
source "$SCRIPT_DIR/setup_production_env.sh"
setup_mcp_production_env

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

# If the requested HTTP port is already serving our MCP health endpoint, treat it as
# "already running" and exit successfully (common during dev when a prior server is
# still active).
HOST="127.0.0.1"
PORT="8001"
ARGS=("$@")
for ((i=0; i<${#ARGS[@]}; i++)); do
    case "${ARGS[$i]}" in
        --host)
            HOST="${ARGS[$((i+1))]:-$HOST}"
            i=$((i+1))
            ;;
        --port)
            PORT="${ARGS[$((i+1))]:-$PORT}"
            i=$((i+1))
            ;;
    esac
done

CHECK_HOST="$HOST"
if [[ "$CHECK_HOST" == "0.0.0.0" ]]; then
    CHECK_HOST="127.0.0.1"
fi

if command -v curl >/dev/null 2>&1; then
    if HEALTH_JSON="$(curl -fsS --max-time 1 "http://${CHECK_HOST}:${PORT}/health" 2>/dev/null)"; then
        if echo "$HEALTH_JSON" | grep -Eq '"server"[[:space:]]*:[[:space:]]*"world-logic"'; then
            echo "MCP server already running on http://${CHECK_HOST}:${PORT} (health OK); skipping new start." >&2
            exit 0
        fi
    fi
fi

# If the port is bound but it's not our MCP server, fail with a clear message.
if command -v lsof >/dev/null 2>&1; then
    if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "ERROR: Port ${PORT} is already in use and does not appear to be our MCP server." >&2
        lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2 || true
        exit 1
    fi
fi

# Create a named pipe for persistent stdin
branch="${GITHUB_REF_NAME:-local}"
PIPE_FILE="$(mktemp -u "/tmp/mcp_stdin_${branch}_XXXX")"
umask 077
mkfifo "$PIPE_FILE"

# Keep the pipe open in the background
exec 3<>"$PIPE_FILE"

# Start MCP server with stdin from named pipe
PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}" venv/bin/python -m mvp_site.mcp_api --dual "$@" <"$PIPE_FILE" &
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
