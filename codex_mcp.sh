#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_LAUNCHER_PATH="$0"

MCP_PRODUCT_NAME="Codex"
MCP_CLI_BIN="codex"

source "$SCRIPT_DIR/scripts/mcp_common.sh" "$@"
exit $?
