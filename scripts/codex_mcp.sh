#!/bin/bash

set -euo pipefail

TEST_MODE=false
if [[ "${1:-}" == "--test" ]]; then
    TEST_MODE=true
fi

MCP_PRODUCT_NAME="Codex"
MCP_CLI_BIN="codex"
MCP_SCOPE="user"
MCP_STATS_LOCK_FILE="/tmp/codex_mcp_stats.lock"
MCP_LOG_FILE_PREFIX="/tmp/codex_mcp"
MCP_BACKUP_PREFIX="codex"
MCP_REQUIRE_CLI=true

DEFAULT_MCP_ENV_FLAGS=(
    --env "MCP_CODEX_DEBUG=false"
    --env "MCP_VERBOSE_TOOLS=false"
    --env "MCP_AUTO_DISCOVER=false"
)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/mcp_common.sh"
exit $?
