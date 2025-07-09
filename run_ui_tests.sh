#!/bin/bash

# run_ui_tests.sh - Complete UI/Browser Test Runner for WorldArchitect.AI
# This script handles all the setup and execution for browser tests
# Usage: ./run_ui_tests.sh [mock]
#   mock: Use mock APIs (Firebase/Gemini) instead of real APIs

set -e  # Exit on any error

# Check for mock mode
MOCK_MODE=false
if [[ "$1" == "mock" ]]; then
    MOCK_MODE=true
    echo "🚀 WorldArchitect.AI UI Test Runner (MOCK MODE)"
    echo "=============================================="
else
    echo "🚀 WorldArchitect.AI UI Test Runner (REAL APIs)"
    echo "=============================================="
fi

# 1. Activate virtual environment
echo "🔧 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
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
echo "🌐 Verifying browser dependencies..."
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

# 4. Create screenshot directory
echo "📸 Setting up screenshot directory..."
SCREENSHOT_DIR="/tmp/worldarchitectai/browser"
mkdir -p "$SCREENSHOT_DIR"
echo "✅ Screenshots will be saved to: $SCREENSHOT_DIR"

# 5. Start test server in background
if $MOCK_MODE; then
    echo "🏃 Starting test server with MOCK APIs..."
    export USE_MOCKS=true
else
    echo "🏃 Starting test server with REAL APIs..."
    export USE_MOCKS=false
fi

TEST_PORT=6006
export TESTING=true
export PORT=$TEST_PORT

# Kill any existing server on the port
lsof -ti:$TEST_PORT | xargs kill -9 2>/dev/null || true
sleep 1

# Start the server
python3 mvp_site/main.py serve &
SERVER_PID=$!

if $MOCK_MODE; then
    echo "📍 Test server started (PID: $SERVER_PID) on port $TEST_PORT with MOCK APIs"
else
    echo "📍 Test server started (PID: $SERVER_PID) on port $TEST_PORT with REAL APIs"
fi

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
trap cleanup EXIT

# 7. Run the tests in parallel
echo "🧪 Running browser tests in parallel..."
echo "======================================="

# Automatically discover all test files in testing_ui/ directory
BROWSER_TESTS=()
if [ -d "testing_ui" ]; then
    echo "🔍 Discovering test files in testing_ui/ directory..."
    while IFS= read -r -d '' test_file; do
        BROWSER_TESTS+=("$test_file")
    done < <(find testing_ui -name "test_*.py" -type f -print0 | sort -z)
    echo "✅ Found ${#BROWSER_TESTS[@]} test files"
else
    echo "❌ testing_ui/ directory not found"
    exit 1
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