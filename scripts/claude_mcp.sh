#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Path to this launcher (used by mcp_common.sh for telemetry and logging)
MCP_LAUNCHER_PATH="${BASH_SOURCE[0]}"

MCP_PRODUCT_NAME="Claude"
MCP_CLI_BIN="claude"
# Export if downstream scripts rely on these in subshells
# export MCP_PRODUCT_NAME MCP_CLI_BIN MCP_LAUNCHER_PATH

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
