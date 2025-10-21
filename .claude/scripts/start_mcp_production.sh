#!/bin/bash
# Start WorldArchitect MCP Server in Production Mode (for Claude Code integration)
# This script provides stdio MCP server for AI assistant integration
# Fail fast and surface errors
set -Eeuo pipefail
trap 'echo "ERROR: start_mcp_production.sh failed at line $LINENO" >&2' ERR

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

SETUP_SCRIPT="$PROJECT_ROOT/scripts/setup_production_env.sh"
if [[ -f "$SETUP_SCRIPT" ]]; then
    # Use shared production environment setup if available
    source "$SETUP_SCRIPT"
else
    # Fallback: define minimal setup to preserve behaviour when the helper is missing
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

# Validate Python executable
PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
if [ ! -x "$PYTHON_EXEC" ]; then
    echo "ERROR: Python executable not found at $PYTHON_EXEC" >&2
    echo "Please ensure virtual environment is set up: python3 -m venv venv" >&2
    exit 1
fi

# Validate MCP server exists
MCP_SERVER_PATH="$PROJECT_ROOT/mvp_site/mcp_api.py"
if [ ! -f "$MCP_SERVER_PATH" ]; then
    echo "ERROR: MCP server not found at $MCP_SERVER_PATH" >&2
    echo "Please ensure you're running from project root" >&2
    exit 1
fi

exec "$PYTHON_EXEC" "$MCP_SERVER_PATH" --dual "$@"
