#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_LAUNCHER_PATH="$0"

MCP_PRODUCT_NAME="Claude"
MCP_CLI_BIN="claude"

source "$SCRIPT_DIR/mcp_common.sh" "$@"
exit $?
