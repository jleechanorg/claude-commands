#!/bin/bash
# Test suite for fake code detection hook - TDD approach

set -euo pipefail

# Test configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK_SCRIPT="$PROJECT_ROOT/.claude/hooks/detect_speculation_and_fake_code.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 Testing fake code detection hook"
echo "Hook: $HOOK_SCRIPT"
echo ""

# Helper function to run a test
run_test() {
    local test_name="$1"
    local code_snippet="$2" 
    local expected_exit="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${YELLOW}Test $TESTS_RUN: $test_name${NC}"
    
    # Create temporary test directory
    local test_dir=$(mktemp -d)
    local current_dir=$(pwd)
    
    # Setup minimal git repo for hook
    cd "$test_dir"
    git init -q >/dev/null 2>&1
    echo "# Test Project" > CLAUDE.md
    mkdir -p .claude docs
    
    # Run hook with test code
    local actual_exit=0
    echo -e "$code_snippet" | bash "$HOOK_SCRIPT" >/dev/null 2>&1 || actual_exit=$?
    
    # Check result
    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo -e "${GREEN}✅ PASS${NC} (exit $actual_exit)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC} (expected exit $expected_exit, got $actual_exit)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Cleanup
    cd "$current_dir"
    rm -rf "$test_dir"
    echo
}

# Test 1: Clean code should pass
run_test "Clean code should pass" "def calculate(a, b): return a + b" 0

# Test 2: TODO pattern should be blocked
run_test "TODO pattern detection" "def func(): # TODO: implement real functionality here" 2

# Test 3: FIXME pattern should be blocked  
run_test "FIXME pattern detection" "def process(): # FIXME: Replace with actual processing" 2

# Test 4: Simulation pattern should be blocked
run_test "Simulation pattern detection" "def simulate_api_call(): return {'fake': 'data'}" 2

# Test 5: Production disclaimer should be blocked
run_test "Production disclaimer detection" "# In production, this would use real APIs" 2

# Test 6: Placeholder pattern should be blocked
run_test "Placeholder pattern detection" "def placeholder_function(): pass" 2

# Test 7: Multiple patterns should be blocked
run_test "Multiple patterns detection" "def placeholder(): # TODO: fix this later" 2

# Summary
echo "📊 Test Results:"
echo -e "Total: $TESTS_RUN | ${GREEN}Passed: $TESTS_PASSED${NC} | ${RED}Failed: $TESTS_FAILED${NC}"

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 $TESTS_FAILED test(s) failed!${NC}"
    exit 1
fi