#!/bin/bash

# run_ui_tests.sh - Complete UI/Browser Test Runner for WorldArchitect.AI
# This script handles all the setup and execution for browser tests
# Usage: ./run_ui_tests.sh [mode] [--puppeteer]
#   mode:
#     mock        - Use mock implementations for BOTH Firebase and Gemini
#     mock-gemini - Use mock Gemini but REAL Firebase (default for cost savings)
#     real        - Use REAL implementations for both services (costs money!)
#   
#   --puppeteer   - Use Puppeteer MCP instead of Playwright (requires Claude Code CLI)
#   
# Default (no argument): mock-gemini mode

set -e  # Exit on any error

# Parse arguments
MODE=""
USE_PUPPETEER=false

# Refactored argument parsing for correctness
while [[ $# -gt 0 ]]; do
    case "$1" in
        --puppeteer)
            USE_PUPPETEER=true
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
        export TEST_MODE="${TEST_MODE:-mock}"
        ;;
    "mock-gemini")
        echo "🚀 WorldArchitect.AI UI Test Runner (MOCK GEMINI + REAL FIREBASE)"
        echo "==============================================" 
        echo "📌 Gemini will be mocked (no AI costs)"
        echo "🔥 Firebase will be REAL (database operations will persist)"
        export USE_MOCK_FIREBASE=false
        export USE_MOCK_GEMINI=true
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
        export TEST_MODE="${TEST_MODE:-real}"
        ;;
    *)
        echo "❌ Invalid mode: $MODE"
        echo "Usage: $0 [mock|mock-gemini|real] [--puppeteer]"
        echo "  mock        - Mock both Firebase and Gemini"
        echo "  mock-gemini - Mock Gemini, use real Firebase (default)"
        echo "  real        - Use real APIs for everything"
        echo "  --puppeteer - Use Puppeteer MCP instead of Playwright"
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

# 5. Start test server in background
echo "🏃 Starting test server..."
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
export TESTING=true
export PORT=$TEST_PORT

# Kill any existing server on the port
lsof -ti:$TEST_PORT | xargs kill -9 2>/dev/null || true
sleep 1

# Start the server
python3 mvp_site/main.py serve &
SERVER_PID=$!

echo "📍 Test server started (PID: $SERVER_PID) on port $TEST_PORT"
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
    echo "🧪 Running Playwright browser tests in parallel..."
    echo "=================================================="
    
    # Automatically discover all test files in testing_ui/ directory
    BROWSER_TESTS=()
    if [ -d "testing_ui/core_tests/" ]; then
        echo "🔍 Discovering test files in testing_ui/core_tests/ directory..."
        while IFS= read -r -d '' test_file; do
            BROWSER_TESTS+=("$test_file")
        done < <(find testing_ui/core_tests -name "test_*.py" -type f -print0 | sort -z)
        echo "✅ Found ${#BROWSER_TESTS[@]} test files"
    else
        echo "❌ testing_ui/core_tests/ directory not found"
        exit 1
    fi
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