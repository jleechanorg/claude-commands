#!/bin/bash
# MCP Dual Transport Background Wrapper
# Purpose: Run MCP (stdio + HTTP) in background with persistent stdin.
# Usage: scripts/mcp_dual_background.sh --host 127.0.0.1 --port 8001 [--other flags]
set -Eeuo pipefail
trap 'echo "ERROR: mcp_dual_background.sh failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve the project root so the script works from both repo .claude/ and ~/.claude/
resolve_project_root() {
    local search_dir="$SCRIPT_DIR"
    while [[ "$search_dir" != "/" ]]; do
        if [[ -f "$search_dir/scripts/setup_production_env.sh" && -f "$search_dir/mvp_site/mcp_api.py" ]]; then
            echo "$search_dir"
            return 0
        fi
        search_dir="$(dirname "$search_dir")"
    done

    if [[ -n "${WORLDARCHITECT_PROJECT_ROOT:-}" ]] && \
       [[ -f "${WORLDARCHITECT_PROJECT_ROOT}/scripts/setup_production_env.sh" && \
          -f "${WORLDARCHITECT_PROJECT_ROOT}/mvp_site/mcp_api.py" ]]; then
        echo "${WORLDARCHITECT_PROJECT_ROOT}"
        return 0
    fi

    return 1
}

PROJECT_ROOT="$(resolve_project_root)" || {
    echo "ERROR: Unable to locate project root containing scripts/setup_production_env.sh" >&2
    exit 1
}

cd "$PROJECT_ROOT"

# Use shared production environment setup
SETUP_SCRIPT="$PROJECT_ROOT/scripts/setup_production_env.sh"
if [[ -f "$SETUP_SCRIPT" ]]; then
    source "$SETUP_SCRIPT"
else
    setup_mcp_production_env() {
        unset TESTING
        unset MOCK_SERVICES_MODE
        unset MOCK_MODE
        export PRODUCTION_MODE="true"
        echo "🔧 Production environment configured (fallback)" >&2
        echo "  TESTING=${TESTING:-unset}" >&2
        echo "  MOCK_SERVICES_MODE=${MOCK_SERVICES_MODE:-unset}" >&2
        echo "  PRODUCTION_MODE=${PRODUCTION_MODE}" >&2
    }
fi

setup_mcp_production_env

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

# Ensure Python can import the local mvp_site package without requiring editable installs
if [[ -z "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$PROJECT_ROOT"
else
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
fi

# Create a named pipe for persistent stdin (secure: no TOCTOU vulnerability)
branch="${GITHUB_REF_NAME:-local}"
PIPE_DIR="$(mktemp -d "/tmp/mcp_stdin_${branch}_XXXX")"
umask 077
PIPE_FILE="$PIPE_DIR/pipe"
mkfifo "$PIPE_FILE"

# Keep the pipe open in the background
exec 3<>"$PIPE_FILE"

# Start MCP server with stdin from named pipe
"$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/mvp_site/mcp_api.py" --dual "$@" <"$PIPE_FILE" &
MCP_PID=$!

# Function to cleanup on exit
cleanup() {
    if [ -n "$MCP_PID" ] && kill -0 "$MCP_PID" 2>/dev/null; then
        kill "$MCP_PID" 2>/dev/null
    fi
    if [ -p "$PIPE_FILE" ]; then
        rm -f "$PIPE_FILE" 2>/dev/null
    fi
    if [ -d "$PIPE_DIR" ]; then
        rmdir "$PIPE_DIR" 2>/dev/null
    fi
    exec 3>&-
}

trap cleanup EXIT INT TERM

# Wait for MCP server to exit (or forever in background)
wait "$MCP_PID" 2>/dev/null
