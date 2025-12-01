#!/usr/bin/env bash
set -euo pipefail

# Default to local MCP if not set
: "${MCP_SERVER_URL:=http://127.0.0.1:8001}"

# Default to real to mirror /smoke; fall back to mock if explicitly set
: "${MCP_TEST_MODE:=real}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
node "$SCRIPT_DIR/mcp-smoke-tests.mjs"
