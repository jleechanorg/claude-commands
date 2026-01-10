#!/usr/bin/env bash
#
# MCP Smoke Test Script
# Runs basic smoke tests against the MCP server to verify core functionality
#

set -euo pipefail  # Exit on error, undefined vars, and pipeline failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_SERVER_HOST="127.0.0.1"
MCP_SERVER_PORT="8000"
SERVER_URL="http://${MCP_SERVER_HOST}:${MCP_SERVER_PORT}"
SERVER_PID=""
LOG_DIR="${PROJECT_ROOT}/tmp/worldarchitect.ai/test"
SERVER_LOG="${LOG_DIR}/mcp-server-smoke.log"
TEST_LOG="${LOG_DIR}/mcp-test-output.log"
RESULTS_FILE="${LOG_DIR}/smoke-test-results.json"
REQUEST_RESPONSE_LOG="${LOG_DIR}/mcp-requests-responses.json"
MAX_STARTUP_WAIT=30  # seconds

# Ensure log directory exists
mkdir -p "$LOG_DIR"
: > "$SERVER_LOG"
: > "$TEST_LOG"

# Default to mock/test-friendly environment when not provided
export TESTING=${TESTING:-true}
export FLASK_ENV=${FLASK_ENV:-testing}
export TEST_MODE=${TEST_MODE:-mock}
export MOCK_SERVICES_MODE=${MOCK_SERVICES_MODE:-true}
export WORLDAI_DEV_MODE=${WORLDAI_DEV_MODE:-true}
export GEMINI_API_KEY=${GEMINI_API_KEY:-dummy_key_for_mock_mode}
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

# Cleanup function
cleanup() {
    local exit_code=$?
    echo -e "\n${YELLOW}Cleaning up...${NC}"

    if [ -n "$SERVER_PID" ] && ps -p "$SERVER_PID" > /dev/null 2>&1; then
        echo "Stopping MCP server (PID: $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi

    # Kill any remaining processes on the port
    if command -v lsof > /dev/null 2>&1; then
        lsof -ti:$MCP_SERVER_PORT | xargs kill -9 2>/dev/null || true
    elif command -v fuser > /dev/null 2>&1; then
        fuser -k ${MCP_SERVER_PORT}/tcp 2>/dev/null || true
    fi

    exit $exit_code
}

trap cleanup EXIT INT TERM

# Start MCP server
start_server() {
    echo -e "${YELLOW}Starting MCP server on ${SERVER_URL}...${NC}"

    cd "$PROJECT_ROOT"

    # Start server in background
    TESTING="$TESTING" python3 mvp_site/mcp_api.py \
        --host "$MCP_SERVER_HOST" \
        --port "$MCP_SERVER_PORT" \
        --http-only \
        > "$SERVER_LOG" 2>&1 &

    SERVER_PID=$!
    echo "Server PID: $SERVER_PID"

    # Wait for server to be ready
    echo "Waiting for server to start (max ${MAX_STARTUP_WAIT}s)..."
    local count=0
    while [ $count -lt $MAX_STARTUP_WAIT ]; do
        if curl -sf "${SERVER_URL}/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Server is ready${NC}"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        if ! ps -p "$SERVER_PID" > /dev/null 2>&1; then
            echo -e "${RED}✗ Server process died during startup${NC}"
            echo "Server log:"
            cat "$SERVER_LOG"
            return 1
        fi
    done

    echo -e "${RED}✗ Server failed to start within ${MAX_STARTUP_WAIT}s${NC}"
    echo "Server log:"
    cat "$SERVER_LOG"
    return 1
}

# Run smoke tests
run_smoke_tests() {
    echo -e "\n${YELLOW}Running MCP smoke tests...${NC}"
    echo "========================================"

    cd "$PROJECT_ROOT"

    # Run the test client with all tests
    if python3 mvp_site/tests/mcp_test_client.py \
        --server "$SERVER_URL" \
        --test all \
        --log-file "$REQUEST_RESPONSE_LOG" 2>&1 | tee "$TEST_LOG"; then
        echo -e "\n${GREEN}✓ All smoke tests passed${NC}"

        # Create results JSON
        cat > "$RESULTS_FILE" <<EOF
{
  "status": "success",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "server_url": "$SERVER_URL",
  "tests_passed": true
}
EOF
        return 0
    else
        echo -e "\n${RED}✗ Smoke tests failed${NC}"
        echo -e "${YELLOW}Server log (${SERVER_LOG}) and test log (${TEST_LOG}) saved for debugging.${NC}"

        # Create results JSON
        cat > "$RESULTS_FILE" <<EOF
{
  "status": "failure",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "server_url": "$SERVER_URL",
  "tests_passed": false
}
EOF
        return 1
    fi
}

# Main execution
main() {
    echo "========================================"
    echo "MCP Smoke Test Suite"
    echo "========================================"
    echo "Project root: $PROJECT_ROOT"
    echo "Server URL: $SERVER_URL"
    echo "Log directory: $LOG_DIR"
    echo "Request/Response log: $REQUEST_RESPONSE_LOG"
    echo ""
    echo "Test Mode Configuration:"
    echo "  TESTING: $TESTING"
    echo "  FLASK_ENV: $FLASK_ENV"
    echo "  TEST_MODE: $TEST_MODE"
    echo "  MOCK_SERVICES_MODE: $MOCK_SERVICES_MODE"
    if [ "$MOCK_SERVICES_MODE" = "false" ] || [ "$TESTING" = "false" ]; then
        echo -e "${YELLOW}  ⚠️  RUNNING AGAINST REAL APIs${NC}"
    else
        echo -e "${GREEN}  ✓  Running in mock mode (safe for CI)${NC}"
    fi
    echo "========================================"

    # Start the server
    if ! start_server; then
        echo -e "${RED}✗ Failed to start MCP server${NC}"
        exit 1
    fi

    # Run the tests
    if run_smoke_tests; then
        echo -e "\n${GREEN}✓ MCP smoke tests completed successfully${NC}"
        exit 0
    else
        echo -e "\n${RED}✗ MCP smoke tests failed${NC}"
        exit 1
    fi
}

# Run main function
main
