#!/bin/bash
# Comprehensive test runner for all Claude Code hooks
# Follows TDD/BDD best practices

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test directory
TEST_DIR="$(dirname "$0")"
HOOKS_DIR="$(dirname "$TEST_DIR")"

# Counters
TOTAL_TESTS=0
TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_TESTS=()

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Claude Code Hooks Test Suite          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to run individual test files
run_test_file() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .sh)
    
    echo -e "${YELLOW}Running: ${NC}$test_name"
    echo "----------------------------------------"
    
    if bash "$test_file"; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
        TOTAL_PASSED=$((TOTAL_PASSED + 1))
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        FAILED_TESTS+=("$test_name")
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
}

# Discover and run all test files
for test_file in "$TEST_DIR"/test_*.sh; do
    if [ -f "$test_file" ] && [ -x "$test_file" ]; then
        run_test_file "$test_file"
    fi
done

# Final summary
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Test Summary                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total test files run: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$TOTAL_PASSED${NC}"
echo -e "Failed: ${RED}$TOTAL_FAILED${NC}"

if [ $TOTAL_FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed tests:${NC}"
    for failed in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}• $failed${NC}"
    done
    exit 1
else
    echo ""
    echo -e "${GREEN}🎉 All hook tests passed!${NC}"
    exit 0
fi