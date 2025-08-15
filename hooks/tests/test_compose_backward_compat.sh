#!/bin/bash
# Test backward compatibility of compose-commands.sh
# Tests that it handles both JSON and plain text input

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local input="$2"
    local expected_contains="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    echo -n "Testing $test_name... "
    
    # Run the hook with the input
    result=$(echo "$input" | bash ../compose-commands.sh 2>/dev/null)
    
    if echo "$result" | grep -q "$expected_contains"; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Expected to contain: '$expected_contains'"
        echo "  Got: '$result'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo "Testing compose-commands.sh backward compatibility..."
echo "=================================================="

# Test 1: Plain text input (backward compatibility)
run_test "plain text with single command" \
    "/test this is a test" \
    "/test"

# Test 2: Plain text with multiple commands
run_test "plain text with multiple commands" \
    "/test and /execute something" \
    "/test /execute"

# Test 3: JSON input (new format)
run_test "JSON input with prompt field" \
    '{"prompt": "/test this is a test"}' \
    "/test"

# Test 4: JSON input with multiple commands
run_test "JSON input with multiple commands" \
    '{"prompt": "/test and /execute something"}' \
    "/test /execute"

# Test 5: Empty plain text
run_test "empty plain text" \
    "" \
    ""

# Test 6: Empty JSON
run_test "empty JSON" \
    '{"prompt": ""}' \
    ""

# Test 7: Plain text without commands
run_test "plain text without commands" \
    "no commands here" \
    ""

# Test 8: Malformed JSON (should handle gracefully)
run_test "malformed JSON falls back gracefully" \
    '{"broken json' \
    ""

# Summary
echo "=================================================="
echo "Test Results:"
echo "  Tests run:    $TESTS_RUN"
echo "  Tests passed: $TESTS_PASSED"
echo "  Tests failed: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi