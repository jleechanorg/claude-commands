#!/bin/bash

# RED PHASE: Tests that should FAIL with branch-header-only responses
# These tests would have caught the Claude CLI bug

set -e

echo "🔴 RED PHASE: Response Quality Tests (Should Fail)"
echo "================================================"

CLAUDE_ENDPOINT="http://127.0.0.1:5001/claude"

# Test 1: Hello prompt should contain greeting words
test_hello_response() {
    echo "Testing hello response quality..."

    response=$(curl -s --data-urlencode "prompt=hello!" "$CLAUDE_ENDPOINT")
    echo "Response: '$response'"

    # RED: This should FAIL with branch-header-only response
    if [[ "$response" == *"Hello"* ]] || [[ "$response" == *"hi"* ]] || [[ "$response" == *"help"* ]]; then
        echo "✅ Response contains greeting content"
        return 0
    else
        echo "❌ Response lacks meaningful greeting content"
        echo "❌ Got: '$response'"
        echo "❌ Expected: Response containing greeting words"
        return 1
    fi
}

# Test 2: Math prompt should contain actual calculation
test_math_response() {
    echo "Testing math response quality..."

    response=$(curl -s --data-urlencode "prompt=what is 2+2?" "$CLAUDE_ENDPOINT")
    echo "Response: '$response'"

    # RED: This should FAIL with branch-header-only response
    if [[ "$response" == *"4"* ]] || [[ "$response" == *"four"* ]]; then
        echo "✅ Response contains mathematical answer"
        return 0
    else
        echo "❌ Response lacks mathematical content"
        echo "❌ Got: '$response'"
        echo "❌ Expected: Response containing '4' or 'four'"
        return 1
    fi
}

# Test 3: Response should not be ONLY metadata
test_not_just_metadata() {
    echo "Testing response is not just metadata..."

    response=$(curl -s --data-urlencode "prompt=help me debug" "$CLAUDE_ENDPOINT")
    echo "Response: '$response'"

    # RED: This should FAIL with branch-header-only response
    if [[ "$response" =~ ^\[Local:.*\]$ ]]; then
        echo "❌ Response is ONLY branch metadata"
        echo "❌ Got: '$response'"
        echo "❌ Expected: Actual content beyond metadata"
        return 1
    else
        echo "✅ Response contains content beyond metadata"
        return 0
    fi
}

# Test 4: Response length should be reasonable
test_response_length() {
    echo "Testing response has reasonable length..."

    response=$(curl -s --data-urlencode "prompt=explain something" "$CLAUDE_ENDPOINT")
    echo "Response: '$response'"

    # RED: This should FAIL with short branch-header-only response
    if [ ${#response} -gt 100 ]; then
        echo "✅ Response has reasonable length (${#response} chars)"
        return 0
    else
        echo "❌ Response too short for meaningful content"
        echo "❌ Got: ${#response} characters"
        echo "❌ Expected: >100 characters for explanation"
        return 1
    fi
}

# Run all quality tests
main() {
    echo "Running response quality validation tests..."

    failed_tests=()

    if ! test_hello_response; then
        failed_tests+=("hello_response")
    fi

    if ! test_math_response; then
        failed_tests+=("math_response")
    fi

    if ! test_not_just_metadata; then
        failed_tests+=("not_just_metadata")
    fi

    if ! test_response_length; then
        failed_tests+=("response_length")
    fi

    if [ ${#failed_tests[@]} -gt 0 ]; then
        echo ""
        echo "❌ QUALITY TESTS FAILED: ${failed_tests[*]}"
        echo "❌ These tests would have caught the Claude CLI bug!"
        return 1
    else
        echo ""
        echo "✅ All quality tests passed"
        return 0
    fi
}

main "$@"
