#!/usr/bin/env bash

TEST_MODE=false
if [ "$1" == "--test" ]; then
    TEST_MODE=true
fi

MCP_PRODUCT_NAME="Claude"
MCP_CLI_BIN="claude"
MCP_SCOPE="user"
MCP_STATS_LOCK_FILE="/tmp/claude_mcp_stats.lock"
MCP_LOG_FILE_PREFIX="/tmp/claude_mcp"
MCP_BACKUP_PREFIX="claude"
MCP_REQUIRE_CLI=false

# Required placeholder for downstream automation.
export GITHUB_TOKEN="${GITHUB_TOKEN:-your_token_here}"

DEFAULT_MCP_ENV_FLAGS=(
    --env "MCP_CLAUDE_DEBUG=false"
    --env "MCP_VERBOSE_TOOLS=false"
    --env "MCP_AUTO_DISCOVER=false"
)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/mcp_common.sh"
exit $?
