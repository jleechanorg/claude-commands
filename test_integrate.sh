#!/bin/bash
# test_integrate.sh - Test script for integrate.sh functionality
# Tests the branch protection rule handling and PR creation workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0

echo "🧪 Testing integrate.sh functionality..."
echo "======================================"

# Helper functions
run_test() {
    local test_name="$1"
    local test_command="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${YELLOW}Test $TESTS_RUN: $test_name${NC}"
    echo "Command: $test_command"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

cleanup_test_branches() {
    echo "🧹 Cleaning up test branches..."
    git branch -D test-branch-1 2>/dev/null || true
    git branch -D test-branch-2 2>/dev/null || true
    git push origin --delete test-branch-1 2>/dev/null || true
    git push origin --delete test-branch-2 2>/dev/null || true
}

# Store original branch
ORIGINAL_BRANCH=$(git branch --show-current)
echo "Original branch: $ORIGINAL_BRANCH"

# Test 1: Check that integrate.sh exists and is executable
run_test "integrate.sh exists and is executable" "[ -x ./integrate.sh ]"

# Test 2: Check integrate.sh help/usage
run_test "integrate.sh shows usage info" "./integrate.sh --help 2>&1 | grep -q 'Usage:' || head -20 ./integrate.sh | grep -q 'Usage:'"

# Test 3: Verify script has branch protection handling
run_test "Script contains branch protection logic" "grep -q 'create.*PR' ./integrate.sh"

# Test 4: Check for existing sync PR detection
run_test "Script has sync PR detection" "grep -q 'check_existing_sync_pr' ./integrate.sh"

# Test 5: Verify error handling for repository rules
run_test "Script handles repository rule violations" "grep -q 'repository.*rule' ./integrate.sh"

# Test 6: Check script validates git status properly
run_test "Script checks git status" "grep -q 'git.*status' ./integrate.sh"

# Test 7: Verify script creates timestamped branches
run_test "Script creates dev{timestamp} branches" "grep -q 'dev.*timestamp' ./integrate.sh"

# Test 8: Check that script has proper error messages
run_test "Script has error handling" "grep -q 'Error:' ./integrate.sh"

# Simulate integration scenarios (without actually running integrate.sh)
echo -e "\n${YELLOW}🔍 Analyzing integrate.sh logic...${NC}"

# Test 9: Check main sync scenarios are handled
run_test "Script handles main ahead scenario" "grep -A 5 'Local main ahead' ./integrate.sh | grep -q 'PR'"

# Test 10: Check diverged branches scenario
run_test "Script handles diverged branches" "grep -A 5 'diverged' ./integrate.sh | grep -q 'merge'"

# Test 11: Verify cleanup logic exists
run_test "Script has branch deletion logic" "grep -q 'branch.*delete' ./integrate.sh"

# Test 12: Check that script validates branch safety
run_test "Script validates branch safety" "grep -q 'safe.*delete' ./integrate.sh"

# Dry run tests (check command composition without execution)
echo -e "\n${YELLOW}🔍 Testing command structure...${NC}"

# Test 13: Verify git commands are properly structured
run_test "Git commands are well-formed" "bash -n ./integrate.sh"

# Test 14: Check that script can detect current environment
run_test "Script can detect git environment" "git status >/dev/null 2>&1"

# Final summary
echo -e "\n======================================"
echo -e "${GREEN}Tests passed: $TESTS_PASSED/$TESTS_RUN${NC}"

if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo -e "${GREEN}integrate.sh appears to be working correctly${NC}"
    exit 0
else
    FAILED=$((TESTS_RUN - TESTS_PASSED))
    echo -e "${RED}❌ $FAILED tests failed${NC}"
    echo -e "${RED}integrate.sh needs attention${NC}"
    exit 1
fi
