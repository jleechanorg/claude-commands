#!/bin/bash

# run_ui_tests.sh - Complete UI/Browser Test Runner for WorldArchitect.AI
# This script handles all the setup and execution for browser tests
# Usage: ./run_ui_tests.sh [mode] [--playwright|--puppeteer]
#   mode:
#     mock        - Use mock implementations for BOTH Firebase and Gemini
#     mock-gemini - Use mock Gemini but REAL Firebase (default for cost savings)
#     real        - Use REAL implementations for both services (costs money!)
#
#   --playwright  - Use Playwright MCP (default, AI-optimized)
#   --puppeteer   - Use Puppeteer MCP for Chrome-specific testing (requires Claude Code CLI)
#
# Default (no argument): mock-gemini mode

set -e  # Exit on any error

# Parse arguments
MODE=""
USE_PUPPETEER=false
USE_PLAYWRIGHT=false

# Refactored argument parsing for correctness
while [[ $# -gt 0 ]]; do
    case "$1" in
        --playwright)
            USE_PLAYWRIGHT=true
            USE_PUPPETEER=false
            shift
            ;;
        --puppeteer)
            USE_PUPPETEER=true
            USE_PLAYWRIGHT=false
            shift
            ;;
        *)
            if [[ -z "$MODE" ]]; then
                MODE="$1"
            fi
            shift
            ;;
    esac
done

# Set default mode if not specified
MODE="${MODE:-mock-gemini}"

case "$MODE" in
    "mock")
        echo "🚀 WorldArchitect.AI UI Test Runner (FULL MOCK MODE)"
        echo "=============================================="
        echo "📌 Both Firebase and Gemini will be mocked - no API costs!"
        export USE_MOCK_FIREBASE=true
        export USE_MOCK_GEMINI=true
        export MOCK_SERVICES_MODE=true
        export TEST_MODE="${TEST_MODE:-mock}"
        ;;
    "mock-gemini")
        echo "🚀 WorldArchitect.AI UI Test Runner (MOCK GEMINI + REAL FIREBASE)"
        echo "=============================================="
        echo "📌 Gemini will be mocked (no AI costs)"
        echo "🔥 Firebase will be REAL (database operations will persist)"
        export USE_MOCK_FIREBASE=false
        export USE_MOCK_GEMINI=true
        export MOCK_SERVICES_MODE=true
        export TEST_MODE="${TEST_MODE:-mock}"
        ;;
    "real")
        echo "🚀 WorldArchitect.AI UI Test Runner (REAL APIs)"
        echo "=============================================="
        echo "⚠️  WARNING: Real APIs will be used - this costs money!"
        echo "🔥 Firebase: REAL"
        echo "🤖 Gemini: REAL (costs per API call)"
        export USE_MOCK_FIREBASE=false
        export USE_MOCK_GEMINI=false
        export MOCK_SERVICES_MODE=false
        export TEST_MODE="${TEST_MODE:-real}"
        ;;
    *)
        echo "❌ Invalid mode: $MODE"
        echo "Usage: $0 [mock|mock-gemini|real] [--playwright|--puppeteer]"
        echo "  mock        - Mock both Firebase and Gemini"
        echo "  mock-gemini - Mock Gemini, use real Firebase (default)"
        echo "  real        - Use real APIs for everything"
        echo "  --playwright - Use Playwright MCP (default)"
        echo "  --puppeteer - Use Puppeteer MCP for Chrome-specific testing"
        exit 1
        ;;
esac

# 1. Activate virtual environment
echo "🔧 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    echo "🧪 Real-Mode Testing Framework: TEST_MODE=$TEST_MODE"
else
    echo "❌ Virtual environment not found at venv/bin/activate"
    exit 1
fi

# 2. Verify Playwright installation
echo "🔍 Verifying Playwright installation..."
python3 -c "import playwright; print('✅ Playwright module found')" || {
    echo "❌ Playwright not installed. Installing..."
    pip install playwright
    playwright install chromium
}

# 3. Verify browser dependencies
if [[ "$USE_PUPPETEER" == "true" ]]; then
    echo "🤖 Using Puppeteer MCP - skipping Playwright dependencies"
    echo "   Note: Puppeteer MCP requires Claude Code CLI environment"
else
    echo "🌐 Verifying Playwright browser dependencies..."
    python3 -c "
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        browser.close()
    print('✅ Chromium browser ready')
except Exception as e:
    print(f'❌ Browser test failed: {e}')
    exit(1)
" || {
    echo "❌ Browser dependencies missing. Installing..."
    playwright install chromium
}
fi

# 4. Create screenshot directory
echo "📸 Setting up screenshot directory..."
SCREENSHOT_DIR="/tmp/worldarchitectai/browser"
mkdir -p "$SCREENSHOT_DIR"
echo "✅ Screenshots will be saved to: $SCREENSHOT_DIR"

# 5. Start MCP server and Flask app in background
echo "🏃 Starting MCP server and Flask app..."
echo "   Configuration:"
if [[ "$USE_MOCK_FIREBASE" == "true" ]]; then
    echo "   ✓ Firebase: Using in-memory mock"
else
    echo "   ⚠️  Firebase: Using REAL database"
fi
if [[ "$USE_MOCK_GEMINI" == "true" ]]; then
    echo "   ✓ Gemini: Using predefined mock responses"
else
    echo "   ⚠️  Gemini: Using REAL API (incurs API charges)"
fi

TEST_PORT=8088
MCP_PORT=8000
export TESTING=true
export PORT=$TEST_PORT
export MCP_SERVER_URL="http://localhost:$MCP_PORT"

# Kill any existing servers on the ports
lsof -ti:$TEST_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$MCP_PORT | xargs kill -9 2>/dev/null || true
sleep 1

# Start MCP server first
echo "🔧 Starting MCP server on port $MCP_PORT..."
cd mvp_site && python3 mcp_api.py --port $MCP_PORT --host 0.0.0.0 &
MCP_PID=$!
cd ..

# Wait for MCP server to be ready
echo "⏳ Waiting for MCP server to be ready..."
for i in {1..15}; do
    if curl -s "http://localhost:$MCP_PORT" > /dev/null 2>&1; then
        echo "✅ MCP server is ready"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ MCP server failed to start within 15 seconds"
        kill $MCP_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Start Flask app after MCP server is ready
echo "🌐 Starting Flask app on port $TEST_PORT..."
# Use absolute path and execute from correct directory
FLASK_SCRIPT="/home/jleechan/projects/worldarchitect.ai/worktree_human/mvp_site/start_flask.py"
cd /home/jleechan/projects/worldarchitect.ai/worktree_human/mvp_site
TESTING=true PORT=$TEST_PORT MCP_SERVER_URL="http://localhost:$MCP_PORT" SKIP_MCP_HTTP=true FLASK_DEBUG=False python3 start_flask.py &
SERVER_PID=$!
cd /home/jleechan/projects/worldarchitect.ai/worktree_human

echo "📍 Both servers started:"
echo "   📊 MCP server: http://localhost:$MCP_PORT (PID: $MCP_PID)"
echo "   🌐 Flask app: http://localhost:$TEST_PORT (PID: $SERVER_PID)"
echo "   Mode: $MODE"

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s "http://localhost:$TEST_PORT" > /dev/null 2>&1; then
        echo "✅ Server is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Server failed to start within 30 seconds"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 6. Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up..."
    kill $SERVER_PID 2>/dev/null || true
    kill $MCP_PID 2>/dev/null || true
    echo "✅ Cleanup complete"
}
# trap cleanup EXIT

# 7. Run the tests
if [[ "$USE_PUPPETEER" == "true" ]]; then
    echo "🤖 Puppeteer MCP Mode - Manual Execution Required"
    echo "================================================="
    echo ""
    echo "🔧 Server running on: http://localhost:$PORT"
    echo "🧪 Test URL: http://localhost:$PORT?test_mode=true&test_user_id=test-user-123"
    echo ""
    echo "Available Puppeteer tests:"
    echo "• testing_ui/test_structured_fields_puppeteer.py"
    echo ""
    echo "💡 To run Puppeteer tests, use Claude Code CLI with MCP tools:"
    echo "   1. Navigate to test URL"
    echo "   2. Execute test steps via Puppeteer MCP functions"
    echo "   3. Capture screenshots for validation"
    echo ""
    echo "⏳ Server will remain running... Press Ctrl+C to stop"

    # Keep server running for manual testing
    wait $SERVER_PID
    exit 0
else
    echo "🧪 Running comprehensive UI and MCP tests..."
    echo "=================================================="

    # Automatically discover all test files in testing_ui/ directory
    BROWSER_TESTS=()
    if [ -d "testing_ui/core_tests/" ]; then
        echo "🔍 Discovering browser test files in testing_ui/core_tests/ directory..."
        while IFS= read -r -d '' test_file; do
            BROWSER_TESTS+=("$test_file")
        done < <(find testing_ui/core_tests -name "test_*.py" -type f -print0 | sort -z)
        echo "✅ Found ${#BROWSER_TESTS[@]} browser test files"
    else
        echo "❌ testing_ui/core_tests/ directory not found"
        exit 1
    fi

    # Add comprehensive MCP end2end test
    MCP_END2END_TEST="mvp_site/tests/test_end2end/test_mcp_integration_comprehensive.py"
    if [ -f "$MCP_END2END_TEST" ]; then
        echo "🔍 Adding comprehensive MCP integration test..."
        BROWSER_TESTS+=("$MCP_END2END_TEST")
        echo "✅ Added MCP integration test"
    else
        echo "⚠️  MCP integration test not found: $MCP_END2END_TEST"
    fi

    # Add dedicated MCP architecture tests if available
    if [ -d "testing_mcp/" ] && [ -f "testing_mcp/run_mcp_tests.sh" ]; then
        echo "🔍 Discovering dedicated MCP architecture tests..."
        MCP_INTEGRATION_TESTS=()
        while IFS= read -r -d '' test_file; do
            MCP_INTEGRATION_TESTS+=("$test_file")
        done < <(find testing_mcp/integration -name "test_*.py" -type f -print0 2>/dev/null | sort -z)

        if [ ${#MCP_INTEGRATION_TESTS[@]} -gt 0 ]; then
            echo "✅ Found ${#MCP_INTEGRATION_TESTS[@]} dedicated MCP tests"
            BROWSER_TESTS+=("${MCP_INTEGRATION_TESTS[@]}")
        else
            echo "ℹ️  No dedicated MCP integration tests found"
        fi
    else
        echo "ℹ️  Dedicated MCP test directory not available"
    fi

    echo "📊 Total tests to run: ${#BROWSER_TESTS[@]} (Browser + MCP Integration)"
fi

# Create parallel execution with limited concurrency
PASSED=0
FAILED=0
FAILED_TESTS=()
PIDS=()
TEST_RESULTS=()
MAX_PARALLEL=1

echo "🚀 Starting ${#BROWSER_TESTS[@]} tests with max $MAX_PARALLEL concurrent..."

# Function to wait for any background job to complete
wait_for_slot() {
    while [ ${#PIDS[@]} -ge $MAX_PARALLEL ]; do
        for i in "${!PIDS[@]}"; do
            if ! kill -0 "${PIDS[$i]}" 2>/dev/null; then
                wait "${PIDS[$i]}"
                unset PIDS[$i]
                PIDS=("${PIDS[@]}")  # Re-index array
                break
            fi
        done
        sleep 0.1
    done
}

# Start tests with limited parallelism
for i in "${!BROWSER_TESTS[@]}"; do
    test_file="${BROWSER_TESTS[$i]}"
    if [ -f "$test_file" ]; then
        # Wait for a slot to become available
        wait_for_slot

        echo "   📋 Starting: $test_file (${#PIDS[@]}/$MAX_PARALLEL active)"

        # Run test in background, capture output to temp file
        temp_file="/tmp/test_result_$i.log"
        (
            echo "🔍 Running: $test_file" > "$temp_file"
            echo "----------------------------------------" >> "$temp_file"
            if TESTING=true python3 "$test_file" >> "$temp_file" 2>&1; then
                echo "✅ PASSED: $test_file" >> "$temp_file"
                echo "PASSED" > "/tmp/test_status_$i"
            else
                echo "❌ FAILED: $test_file" >> "$temp_file"
                echo "FAILED" > "/tmp/test_status_$i"
            fi
        ) &

        PIDS+=($!)
        TEST_RESULTS+=("$temp_file")
    else
        echo "⚠️  Test file not found: $test_file"
        ((FAILED++))
        FAILED_TESTS+=("$test_file (not found)")
    fi
done

# Wait for all tests to complete
echo "⏳ Waiting for ${#PIDS[@]} parallel tests to complete..."
for i in "${!PIDS[@]}"; do
    pid="${PIDS[$i]}"
    test_file="${BROWSER_TESTS[$i]}"

    echo "   ⏳ Waiting for: $test_file (PID: $pid)"
    wait $pid

    # Check result
    if [ -f "/tmp/test_status_$i" ]; then
        status=$(cat "/tmp/test_status_$i")
        if [ "$status" = "PASSED" ]; then
            ((PASSED++))
            echo "   ✅ COMPLETED: $test_file"
        else
            ((FAILED++))
            FAILED_TESTS+=("$test_file")
            echo "   ❌ FAILED: $test_file"
        fi
    else
        ((FAILED++))
        FAILED_TESTS+=("$test_file (no status)")
        echo "   ❓ UNKNOWN: $test_file"
    fi
done

# Show all test outputs
echo ""
echo "📋 Individual Test Results:"
echo "=========================="
for i in "${!TEST_RESULTS[@]}"; do
    temp_file="${TEST_RESULTS[$i]}"
    if [ -f "$temp_file" ]; then
        echo ""
        cat "$temp_file"
        rm -f "$temp_file" "/tmp/test_status_$i"
    fi
done

# 8. Results summary
echo ""
echo "📊 Test Results Summary"
echo "======================="
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "📸 Screenshots: $SCREENSHOT_DIR"

# List all screenshot files with full paths
echo ""
echo "📸 Generated Screenshots (Full Paths):"
echo "======================================"
if [ -d "$SCREENSHOT_DIR" ]; then
    screenshot_count=0
    while IFS= read -r -d '' screenshot; do
        echo "   📄 $screenshot"
        ((screenshot_count++))
    done < <(find "$SCREENSHOT_DIR" -name "*.png" -type f -printf '%p\0' 2>/dev/null | sort -z)

    if [ $screenshot_count -eq 0 ]; then
        echo "   ⚠️  No PNG screenshots found in $SCREENSHOT_DIR"
    else
        echo "   📊 Total screenshots: $screenshot_count files"
    fi
else
    echo "   ❌ Screenshot directory not found: $SCREENSHOT_DIR"
fi

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed tests:"
    for failed_test in "${FAILED_TESTS[@]}"; do
        echo "   - $failed_test"
    done
fi

echo "\n📸 All screenshots saved in: $SCREENSHOT_DIR"

# 9. Exit with appropriate code
if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 All browser tests passed!"
    exit 0
else
    echo ""
    echo "💥 Some tests failed. Check the output above."
    exit 1
fi
