#!/bin/bash
# Start WorldArchitect MCP Server in Production Mode (for Claude Code integration)
# This script provides stdio MCP server for AI assistant integration
# Fail fast and surface errors
set -Eeuo pipefail
trap 'echo "ERROR: start_mcp_production.sh failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use shared production environment setup if available
if [[ -f "$SCRIPT_DIR/setup_production_env.sh" ]]; then
  source "$SCRIPT_DIR/setup_production_env.sh"
  setup_mcp_production_env
else
  echo "❌ Missing $SCRIPT_DIR/setup_production_env.sh" >&2
  exit 1
fi

echo "Starting MCP server in production mode (dual transport: stdio + HTTP)..." >&2

: "${PROJECT_ROOT:="$REPO_ROOT"}"

exec "$REPO_ROOT/venv/bin/python" "$PROJECT_ROOT/mcp_api.py" --dual "$@"
