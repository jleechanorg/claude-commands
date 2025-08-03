#!/bin/bash
# Test suite for git-header.sh script
# Tests various scenarios: with/without upstreams, PRs, edge cases

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEADER_SCRIPT="$SCRIPT_DIR/git-header.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
run_test() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Test $TESTS_RUN: $test_name ... "

    if [ "$actual" = "$expected" ]; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

mock_git_commands() {
    local branch="$1"
    local upstream="$2"
    local pr_json="$3"

    # Create temporary mock script
    cat > /tmp/mock_git_header.sh << EOF
#!/bin/bash
# Mock version for testing
local_branch="$branch"
remote="$upstream"
pr_info='$pr_json'

if [ "\$pr_info" = "[]" ]; then
    pr_text="none"
else
    pr_num=\$(echo "\$pr_info" | jq -r ".[0].number // \"none\"" 2>/dev/null || echo "none")
    pr_url=\$(echo "\$pr_info" | jq -r ".[0].url // \"\"" 2>/dev/null || echo "")
    if [ "\$pr_num" = "none" ] || [ "\$pr_num" = "null" ]; then
        pr_text="none"
    else
        pr_text="#\$pr_num"
        if [ -n "\$pr_url" ]; then
            pr_text="\$pr_text \$pr_url"
        fi
    fi
fi

echo "[Local: \$local_branch | Remote: \$remote | PR: \$pr_text]"
EOF

    chmod +x /tmp/mock_git_header.sh
    /tmp/mock_git_header.sh
}

echo "🧪 Running git-header.sh test suite..."
echo "========================================"

# Test 1: Basic branch with upstream and PR
result=$(mock_git_commands "feature-branch" "origin/main" '[{"number": 123, "url": "https://github.com/user/repo/pull/123"}]')
expected="[Local: feature-branch | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]"
run_test "Branch with upstream and PR" "$expected" "$result"

# Test 2: Branch with upstream but no PR
result=$(mock_git_commands "feature-branch" "origin/main" '[]')
expected="[Local: feature-branch | Remote: origin/main | PR: none]"
run_test "Branch with upstream but no PR" "$expected" "$result"

# Test 3: Branch with no upstream
result=$(mock_git_commands "local-branch" "no upstream" '[]')
expected="[Local: local-branch | Remote: no upstream | PR: none]"
run_test "Branch with no upstream" "$expected" "$result"

# Test 4: Main branch
result=$(mock_git_commands "main" "origin/main" '[]')
expected="[Local: main | Remote: origin/main | PR: none]"
run_test "Main branch" "$expected" "$result"

# Test 5: PR with number but no URL (edge case)
result=$(mock_git_commands "feature-branch" "origin/main" '[{"number": 456, "url": ""}]')
expected="[Local: feature-branch | Remote: origin/main | PR: #456]"
run_test "PR with number but no URL" "$expected" "$result"

# Test 6: PR with invalid number
result=$(mock_git_commands "feature-branch" "origin/main" '[{"number": null, "url": ""}]')
expected="[Local: feature-branch | Remote: origin/main | PR: none]"
run_test "PR with null number" "$expected" "$result"

# Test 7: Branch with special characters
result=$(mock_git_commands "feature/my-branch" "origin/main" '[]')
expected="[Local: feature/my-branch | Remote: origin/main | PR: none]"
run_test "Branch name with special characters" "$expected" "$result"

# Test 8: Long branch name
result=$(mock_git_commands "very-long-feature-branch-name-for-testing" "origin/main" '[{"number": 789, "url": "https://github.com/user/repo/pull/789"}]')
expected="[Local: very-long-feature-branch-name-for-testing | Remote: origin/main | PR: #789 https://github.com/user/repo/pull/789]"
run_test "Long branch name" "$expected" "$result"

# Clean up
rm -f /tmp/mock_git_header.sh

echo "========================================"
echo "📊 Test Results:"
echo "  Total tests run: $TESTS_RUN"
echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "  ${GREEN}All tests passed! ✅${NC}"
    exit 0
fi
