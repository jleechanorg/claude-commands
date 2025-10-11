#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export MCP_PRODUCT_NAME="Claude"
export MCP_CLI_BIN="claude"

# Location-aware sourcing: works from both root and scripts/ directory
if [[ -f "$SCRIPT_DIR/mcp_common.sh" ]]; then
    source "$SCRIPT_DIR/mcp_common.sh" "$@"
elif [[ -f "$SCRIPT_DIR/scripts/mcp_common.sh" ]]; then
    source "$SCRIPT_DIR/scripts/mcp_common.sh" "$@"
else
    echo "❌ Error: Cannot find mcp_common.sh" >&2
    exit 1
fi
exit $?
