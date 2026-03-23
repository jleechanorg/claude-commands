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
PROJECT_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || cd "$SCRIPT_DIR/../.." && pwd)"
MCP_SERVER_HOST="localhost"
MCP_SERVER_PORT="8000"
SERVER_URL="http://${MCP_SERVER_HOST}:${MCP_SERVER_PORT}"
SERVER_PID=""
LOG_DIR="${LOG_DIR:-/tmp/your-project.com/test}"
SERVER_LOG="${LOG_DIR}/mcp-server-smoke.log"
TEST_LOG="${LOG_DIR}/mcp-test-output.log"
RESULTS_FILE="${LOG_DIR}/smoke-test-results.json"
REQUEST_RESPONSE_LOG="${LOG_DIR}/mcp-requests-responses.json"
MAX_STARTUP_WAIT=30  # seconds

# Ensure log directory exists
mkdir -p "$LOG_DIR"
: > "$SERVER_LOG"
: > "$TEST_LOG"

# Default to real services/local server unless explicitly overridden
export TESTING=${TESTING:-true}
export FLASK_ENV=${FLASK_ENV:-development}
export TEST_MODE=${TEST_MODE:-real}
export MCP_TEST_MODE=${TEST_MODE}  # Propagate to Python test suite
# Align MOCK_SERVICES_MODE with TEST_MODE: mock mode should enable mock services
if [ "$TEST_MODE" = "mock" ]; then
    export MOCK_SERVICES_MODE=${MOCK_SERVICES_MODE:-true}
else
    export MOCK_SERVICES_MODE=${MOCK_SERVICES_MODE:-false}
fi
export WORLDAI_DEV_MODE=${WORLDAI_DEV_MODE:-true}
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
# Default to vpython if venv exists, otherwise use python3 for CI compatibility
# Prefer project venv Python when available so required packages (e.g. mcp) are found locally.
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ -x "${PROJECT_ROOT}/venv/bin/python" ]; then
    PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
fi

# Prefer project venv Python when available so required packages (e.g. mcp) are found locally.
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ -x "${PROJECT_ROOT}/venv/bin/python" ]; then
    PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
fi

# Wire PYTHON_BIN into execution path
if [ -z "${PYTHON_EXEC:-}" ]; then
    PYTHON_EXEC="$PYTHON_BIN"
fi
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
    TESTING="$TESTING" "$PYTHON_EXEC" $PROJECT_ROOT/mcp_api.py \
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

    # Run canonical testing_mcp smoke suite against the local server
    local work_name="github-mcp-smoke-${TEST_MODE:-mock}"
    if "$PYTHON_EXEC" testing_mcp/test_smoke.py \
        --server "$SERVER_URL" \
        --work-name "$work_name" \
        --no-download 2>&1 | tee "$TEST_LOG"; then
        echo -e "\n${GREEN}✓ All smoke tests passed${NC}"

        # Parse test log to extract detailed results
        local test_details=""
        test_details=$(cat "$TEST_LOG" | python3 -c "
import sys, json, re

# Track scenarios found and their status
scenarios = {}
current_scenario = None

for line in sys.stdin:
    line = line.strip()

    # Track which scenario we're in
    if line.startswith('SCENARIO'):
        match = re.search(r'SCENARIO \d+: (.+)', line)
        if match:
            current_scenario = match.group(1)
            # Initialize as 'in_progress' until we know the result
            scenarios[current_scenario] = 'in_progress'

    # Success markers
    if current_scenario:
        if 'Campaign created' in line:
            scenarios['Campaign Creation'] = 'passed'
        elif 'Character creation completed' in line:
            scenarios['Character Creation Completion'] = 'passed'
        elif 'story actions completed successfully' in line:
            scenarios[current_scenario] = 'passed'
        elif 'Dice roll action completed' in line:
            scenarios['Dice Roll Action'] = 'passed'
        elif 'God mode action completed' in line:
            scenarios['God Mode Action'] = 'passed'
        elif 'Thinking mode action completed' in line:
            scenarios['Thinking Mode Action'] = 'passed'

        # Failure markers
        elif '❌' in line and current_scenario in scenarios:
            if scenarios[current_scenario] != 'passed':
                scenarios[current_scenario] = 'failed'

# Convert to list format
tests = [{'name': name, 'status': status if status != 'in_progress' else 'failed'}
         for name, status in scenarios.items()]

print(json.dumps(tests))
" 2>&1)
        if [ $? -ne 0 ] || [ -z "$test_details" ]; then
            echo -e "${YELLOW}⚠️  Warning: Failed to parse test details from log, defaulting to empty array${NC}" >&2
            test_details="[]"
        fi

        # Create detailed results JSON
        cat > "$RESULTS_FILE" <<EOF
{
  "status": "success",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "server_url": "$SERVER_URL",
  "tests_passed": true,
  "test_details": $test_details
}
EOF
        local latest_bundle=""
        latest_bundle="$(ls -dt /tmp/your-project.com/*/$work_name/iteration_* 2>/dev/null | head -n 1 || true)"
        if [ -n "$latest_bundle" ] && [ -f "$latest_bundle/llm_request_responses.jsonl" ]; then
            cp "$latest_bundle/llm_request_responses.jsonl" "$REQUEST_RESPONSE_LOG"
        else
            echo "# No canonical request/response bundle found yet" > "$REQUEST_RESPONSE_LOG"
        fi
        return 0
    else
        echo -e "\n${RED}✗ Smoke tests failed${NC}"
        echo -e "${YELLOW}Server log (${SERVER_LOG}) and test log (${TEST_LOG}) saved for debugging.${NC}"

        # Parse test log to extract what passed before failure (same logic as success case)
        local test_details=""
        test_details=$(cat "$TEST_LOG" 2>/dev/null | python3 -c "
import sys, json, re

scenarios = {}
current_scenario = None

for line in sys.stdin:
    line = line.strip()

    if line.startswith('SCENARIO'):
        match = re.search(r'SCENARIO \d+: (.+)', line)
        if match:
            current_scenario = match.group(1)
            scenarios[current_scenario] = 'in_progress'

    if current_scenario:
        if 'Campaign created' in line:
            scenarios['Campaign Creation'] = 'passed'
        elif 'Character creation completed' in line:
            scenarios['Character Creation Completion'] = 'passed'
        elif 'story actions completed successfully' in line:
            scenarios[current_scenario] = 'passed'
        elif 'Dice roll action completed' in line:
            scenarios['Dice Roll Action'] = 'passed'
        elif 'God mode action completed' in line:
            scenarios['God Mode Action'] = 'passed'
        elif 'Thinking mode action completed' in line:
            scenarios['Thinking Mode Action'] = 'passed'
        elif '❌' in line and current_scenario in scenarios:
            if scenarios[current_scenario] != 'passed':
                scenarios[current_scenario] = 'failed'

tests = [{'name': name, 'status': status if status != 'in_progress' else 'failed'}
         for name, status in scenarios.items()]

print(json.dumps(tests))
" 2>&1)
        if [ $? -ne 0 ] || [ -z "$test_details" ]; then
            echo -e "${YELLOW}⚠️  Warning: Failed to parse test details from failure log, defaulting to empty array${NC}" >&2
            test_details="[]"
        fi

        # Create results JSON with partial results
        cat > "$RESULTS_FILE" <<EOF
{
  "status": "failure",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "server_url": "$SERVER_URL",
  "tests_passed": false,
  "test_details": $test_details
}
EOF
        # Always write fallback to avoid stale logs from previous runs
        echo "# Smoke test failed before request/response capture was produced" > "$REQUEST_RESPONSE_LOG"
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
    echo "Python interpreter: $PYTHON_EXEC"
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
