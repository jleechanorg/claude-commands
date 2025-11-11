#!/bin/bash
# Test suite for git-header.sh hook

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Hook path
HOOK_SCRIPT="$(dirname "$0")/../git-header.sh"

echo "Testing git-header.sh hook..."
echo "================================="

# Test 1: Hook exists and is executable
if [ -x "$HOOK_SCRIPT" ]; then
    echo -e "${GREEN}✓${NC} Hook exists and is executable"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Hook not found or not executable"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Test 2: Hook produces output
output=$(bash "$HOOK_SCRIPT" 2>/dev/null || true)
if [ -n "$output" ]; then
    echo -e "${GREEN}✓${NC} Hook produces output"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Hook produces no output"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Test 3: Output contains branch information
if [[ "$output" == *"Local:"* ]]; then
    echo -e "${GREEN}✓${NC} Output contains local branch info"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Output missing local branch info"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Summary
echo "================================="
echo -e "Tests run: $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi