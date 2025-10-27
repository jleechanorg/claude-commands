#!/bin/bash
# Start WorldArchitect MCP Server in Production Mode (for Claude Code integration)
# This script provides stdio MCP server for AI assistant integration
# Fail fast and surface errors
set -Eeuo pipefail
trap 'echo "ERROR: start_mcp_production.sh failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORLDARCHITECT_MODULE_DIR_DEFAULT="${WORLDARCHITECT_MODULE_DIR:-}"
if [[ -z "$WORLDARCHITECT_MODULE_DIR_DEFAULT" && -n "${PROJECT_ROOT:-}" ]]; then
    WORLDARCHITECT_MODULE_DIR_DEFAULT="${PROJECT_ROOT}"
fi
WORLDARCHITECT_MODULE_DIR="${WORLDARCHITECT_MODULE_DIR_DEFAULT:-orchestration}"

resolve_project_root() {
    local search_dir="$SCRIPT_DIR"

    while [[ "$search_dir" != "/" ]]; do
        if [[ -f "$search_dir/scripts/setup_production_env.sh" && -f "$search_dir/${WORLDARCHITECT_MODULE_DIR}/mcp_api.py" ]]; then
            echo "$search_dir"
            return 0
        fi
        search_dir="$(dirname "$search_dir")"
    done

    if [[ -n "${WORLDARCHITECT_PROJECT_ROOT:-}" ]] && \
       [[ -f "${WORLDARCHITECT_PROJECT_ROOT}/scripts/setup_production_env.sh" && \
          -f "${WORLDARCHITECT_PROJECT_ROOT}/${WORLDARCHITECT_MODULE_DIR}/mcp_api.py" ]]; then
        echo "${WORLDARCHITECT_PROJECT_ROOT}"
        return 0
    fi

    return 1
}

REPO_ROOT="$(resolve_project_root)" || {
    echo "ERROR: Unable to locate project root containing scripts/setup_production_env.sh and ${WORLDARCHITECT_MODULE_DIR}/mcp_api.py" >&2
    exit 1
}

SETUP_SCRIPT="$REPO_ROOT/scripts/setup_production_env.sh"
if [[ -f "$SETUP_SCRIPT" ]]; then
    # shellcheck disable=SC1090
    source "$SETUP_SCRIPT"
    if declare -F setup_mcp_production_env >/dev/null 2>&1; then
        setup_mcp_production_env
    fi
else
    echo "⚠️ Warning: $SETUP_SCRIPT not found; continuing without production env setup" >&2
fi

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

PYTHON_BIN="$REPO_ROOT/venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="${PYTHON_EXEC:-python3}"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
    echo "ERROR: Python executable '$PYTHON_BIN' not found" >&2
    exit 1
fi

MCP_SERVER_PATH=""
for candidate in \
    "$REPO_ROOT/${WORLDARCHITECT_MODULE_DIR}/mcp_api.py" \
    "$REPO_ROOT/src/mcp_api.py" \
    "$REPO_ROOT/mcp_api.py"
do
    if [[ -f "$candidate" ]]; then
        MCP_SERVER_PATH="$candidate"
        break
    fi
done

if [[ -z "$MCP_SERVER_PATH" ]]; then
    echo "ERROR: Unable to locate mcp_api.py under $REPO_ROOT" >&2
    exit 1
fi

if [[ -z "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$REPO_ROOT"
else
    export PYTHONPATH="$REPO_ROOT:$PYTHONPATH"
fi

exec "$PYTHON_BIN" "$MCP_SERVER_PATH" --dual "$@"
