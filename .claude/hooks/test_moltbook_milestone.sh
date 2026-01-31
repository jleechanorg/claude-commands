#!/bin/bash
# Tests for Moltbook Milestone Hook - TDD Approach
set -euo pipefail

# Test utilities
TEST_STATE_FILE="/tmp/moltbook_test_state.json"
TEST_CREDENTIALS_FILE="/tmp/moltbook_test_credentials.json"
HOOK_SCRIPT=".claude/hooks/moltbook-milestone.sh"

# Setup test credentials
echo '{"api_key": "test_key_123"}' > "$TEST_CREDENTIALS_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Setup/Teardown
setup() {
  echo '{"last_post_time": 0, "posts_today": 0, "milestones_tracked": [], "last_reset_date": "1970-01-01"}' > "$TEST_STATE_FILE"
}

teardown() {
  rm -f "$TEST_STATE_FILE"
}

# Test assertion helpers
assert_true() {
  local condition="$1"
  local description="$2"
  TESTS_RUN=$((TESTS_RUN + 1))

  if [ "$condition" = "true" ]; then
    echo -e "${GREEN}✓${NC} $description"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $description"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

assert_equals() {
  local expected="$1"
  local actual="$2"
  local description="$3"
  TESTS_RUN=$((TESTS_RUN + 1))

  if [ "$expected" = "$actual" ]; then
    echo -e "${GREEN}✓${NC} $description"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $description"
    echo "  Expected: $expected"
    echo "  Actual: $actual"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# RED Phase: Test for deferred posting
echo -e "${YELLOW}RED PHASE: Writing Failing Tests${NC}"
echo "========================================"
echo ""

echo "Test Suite: Deferred Posting"
echo "-----------------------------"

# Test 1: Rate-limited milestone should be marked as deferred
setup
echo "Test 1: Rate-limited milestone marks as deferred"
# Simulate recent post (within 2 hours)
RECENT_POST=$(($(date +%s) - 3600))  # 1 hour ago
jq --arg ts "$RECENT_POST" '.last_post_time = ($ts | tonumber)' "$TEST_STATE_FILE" > "${TEST_STATE_FILE}.tmp"
mv "${TEST_STATE_FILE}.tmp" "$TEST_STATE_FILE"

# Run hook with PR merge (should be rate-limited)
export STATE_FILE="$TEST_STATE_FILE"
export CREDENTIALS_FILE="$TEST_CREDENTIALS_FILE"
export MOLTBOOK_DRY_RUN=true
OUTPUT=$(echo '{"tool_input":{"command":"gh pr merge 4268"}}' | "$HOOK_SCRIPT" 2>&1 || true)
unset STATE_FILE
unset CREDENTIALS_FILE
unset MOLTBOOK_DRY_RUN

# Check if deferred_post field exists
HAS_DEFERRED=$(jq -r '.deferred_post // "none"' "$TEST_STATE_FILE")
assert_true "$([ "$HAS_DEFERRED" != "none" ] && echo true || echo false)" "Should have deferred_post in state"
teardown

# Test 2: Deferred post should include milestone details
setup
RECENT_POST=$(($(date +%s) - 3600))
jq --arg ts "$RECENT_POST" '.last_post_time = ($ts | tonumber)' "$TEST_STATE_FILE" > "${TEST_STATE_FILE}.tmp"
mv "${TEST_STATE_FILE}.tmp" "$TEST_STATE_FILE"

export STATE_FILE="$TEST_STATE_FILE"
export CREDENTIALS_FILE="$TEST_CREDENTIALS_FILE"
export MOLTBOOK_DRY_RUN=true
echo '{"tool_input":{"command":"gh pr merge 4268"}}' | "$HOOK_SCRIPT" >/dev/null 2>&1 || true
unset STATE_FILE
unset CREDENTIALS_FILE
unset MOLTBOOK_DRY_RUN

DEFERRED_TYPE=$(jq -r '.deferred_post.type // "missing"' "$TEST_STATE_FILE")
assert_equals "pr_merge" "$DEFERRED_TYPE" "Deferred post should have type 'pr_merge'"
teardown

# Test 3: When rate limit clears, deferred post should be posted
setup
# Old post (3 hours ago - rate limit should be clear)
OLD_POST=$(($(date +%s) - 10800))
jq --arg ts "$OLD_POST" '.last_post_time = ($ts | tonumber)' "$TEST_STATE_FILE" > "${TEST_STATE_FILE}.tmp"
mv "${TEST_STATE_FILE}.tmp" "$TEST_STATE_FILE"

# Add a deferred post
jq '.deferred_post = {
  "type": "pr_merge",
  "details": "PR #4268 merged",
  "pr_num": "4268",
  "deferred_at": '"$OLD_POST"'
}' "$TEST_STATE_FILE" > "${TEST_STATE_FILE}.tmp"
mv "${TEST_STATE_FILE}.tmp" "$TEST_STATE_FILE"

export STATE_FILE="$TEST_STATE_FILE"
export CREDENTIALS_FILE="$TEST_CREDENTIALS_FILE"
export MOLTBOOK_DRY_RUN=true
OUTPUT=$(echo '{"tool_input":{"command":"ls -la"}}' | "$HOOK_SCRIPT" 2>&1 || true)
unset STATE_FILE
unset CREDENTIALS_FILE
unset MOLTBOOK_DRY_RUN

# Should see posting of deferred content
POSTED_DEFERRED=$(echo "$OUTPUT" | grep -c "Shipped: PR #4268" || echo "0")
assert_true "$([ "$POSTED_DEFERRED" -gt 0 ] && echo true || echo false)" "Should post deferred PR #4268 when rate limit clears"
teardown

# Test 4: After posting deferred, deferred_post should be cleared
setup
OLD_POST=$(($(date +%s) - 10800))
jq --arg ts "$OLD_POST" '.last_post_time = ($ts | tonumber) | .deferred_post = {
  "type": "pr_merge",
  "details": "PR #4268 merged",
  "pr_num": "4268"
}' "$TEST_STATE_FILE" > "${TEST_STATE_FILE}.tmp"
mv "${TEST_STATE_FILE}.tmp" "$TEST_STATE_FILE"

export STATE_FILE="$TEST_STATE_FILE"
export CREDENTIALS_FILE="$TEST_CREDENTIALS_FILE"
export MOLTBOOK_DRY_RUN=true
echo '{"tool_input":{"command":"ls -la"}}' | "$HOOK_SCRIPT" >/dev/null 2>&1 || true
unset STATE_FILE
unset CREDENTIALS_FILE
unset MOLTBOOK_DRY_RUN

DEFERRED_AFTER=$(jq -r '.deferred_post // "none"' "$TEST_STATE_FILE")
assert_equals "none" "$DEFERRED_AFTER" "Deferred post should be cleared after posting"
teardown

echo ""
echo -e "${YELLOW}Summary${NC}"
echo "======="
echo "Tests Run: $TESTS_RUN"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -gt 0 ]; then
  echo -e "${RED}RED PHASE: Tests failing as expected${NC}"
  echo "Next: Implement deferred posting logic"
  exit 1
else
  echo -e "${GREEN}GREEN PHASE: All tests passing${NC}"
  exit 0
fi
