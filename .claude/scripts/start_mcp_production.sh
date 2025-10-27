#!/bin/bash
# Start WorldArchitect MCP Server in Production Mode (for Claude Code integration)
# This script provides stdio MCP server for AI assistant integration
# Fail fast and surface errors
set -Eeuo pipefail
trap 'echo "ERROR: start_mcp_production.sh failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

resolve_project_root() {
    local search_dir="$SCRIPT_DIR"

    while [[ "$search_dir" != "/" ]]; do
        if [[ -f "$search_dir/scripts/setup_production_env.sh" && -f "$search_dir/$PROJECT_ROOT/mcp_api.py" ]]; then
            echo "$search_dir"
            return 0
        fi
        search_dir="$(dirname "$search_dir")"
    done

    if [[ -n "${WORLDARCHITECT_PROJECT_ROOT:-}" ]] && \
       [[ -f "${WORLDARCHITECT_PROJECT_ROOT}/scripts/setup_production_env.sh" && \
          -f "${WORLDARCHITECT_PROJECT_ROOT}/$PROJECT_ROOT/mcp_api.py" ]]; then
        echo "${WORLDARCHITECT_PROJECT_ROOT}"
        return 0
    fi

    return 1
}

PROJECT_ROOT="$(resolve_project_root)" || {
    echo "ERROR: Unable to locate project root containing scripts/setup_production_env.sh and $PROJECT_ROOT/mcp_api.py" >&2
    exit 1
}

SETUP_SCRIPT="$PROJECT_ROOT/scripts/setup_production_env.sh"
if [[ -f "$SETUP_SCRIPT" ]]; then
    # shellcheck disable=SC1090
    source "$SETUP_SCRIPT"
    if declare -F setup_mcp_production_env >/dev/null 2>&1; then
        setup_mcp_production_env
    fi
else
    # Fallback: ensure production mode even when setup script is missing
    echo "⚠️ Warning: $SETUP_SCRIPT not found; using fallback production config" >&2
    unset TESTING
    unset MOCK_SERVICES_MODE
    unset MOCK_MODE
    export PRODUCTION_MODE="true"
fi

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="${PYTHON_EXEC:-python3}"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
    echo "ERROR: Python executable '$PYTHON_BIN' not found" >&2
    exit 1
fi

MCP_SERVER_PATH=""
for candidate in \
    "$PROJECT_ROOT/$PROJECT_ROOT/mcp_api.py" \
    "$PROJECT_ROOT/src/mcp_api.py" \
    "$PROJECT_ROOT/mcp_api.py"
do
    if [[ -f "$candidate" ]]; then
        MCP_SERVER_PATH="$candidate"
        break
    fi
done

if [[ -z "$MCP_SERVER_PATH" ]]; then
    echo "ERROR: Unable to locate mcp_api.py under $PROJECT_ROOT" >&2
    exit 1
fi

if [[ -z "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$PROJECT_ROOT"
else
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
fi

exec "$PYTHON_BIN" "$MCP_SERVER_PATH" --dual "$@"
