#!/bin/bash
# Test command - Run full test suite and check GitHub CI status
# Usage: ./test.sh

# Initialize security and configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/security_utils.sh"
source "$SCRIPT_DIR/config.sh"

# Initialize security utilities
init_security_utils || handle_error "Failed to initialize security utilities"
init_config || handle_error "Failed to initialize configuration"

log_message "INFO" "Starting test suite execution"

echo "=== Running Local Tests ==="
if [ -f "$TEST_SCRIPT" ]; then
    "$TEST_SCRIPT" || handle_error "Local tests failed - please fix before proceeding"
else
    handle_error "Test script not found: $TEST_SCRIPT"
fi

echo "✅ Local tests passed"

echo ""
echo "=== Checking GitHub CI Status ==="

# Get current branch
branch=$(get_current_branch)
validate_branch_name "$branch" || handle_error "Invalid branch name: $branch"

# Try to find PR for current branch
pr_number=$(secure_gh_command pr list --head "$branch" --json number --jq '.[0].number' 2>/dev/null)

if [ -n "$pr_number" ]; then
    echo "Found PR #$pr_number for branch $branch"
    echo "Checking CI status..."
    
    log_message "INFO" "Checking CI status for PR #$pr_number"
    secure_gh_command pr checks "$pr_number"
    
    # Check if all checks passed
    failed_checks=$(secure_gh_command pr checks "$pr_number" --json name,status --jq '.[] | select(.status != "COMPLETED" or .conclusion != "SUCCESS") | .name' 2>/dev/null)
    
    if [ -z "$failed_checks" ]; then
        echo "✅ All GitHub CI checks passed"
        log_message "INFO" "All CI checks passed for PR #$pr_number"
    else
        echo "❌ Some GitHub CI checks failed:"
        echo "$failed_checks"
        echo ""
        echo "To view failed logs:"
        echo "gh run view --log-failed"
        log_message "WARN" "Some CI checks failed for PR #$pr_number"
    fi
else
    echo "No PR found for current branch"
    echo "GitHub CI status check skipped"
    log_message "INFO" "No PR found for branch $branch, skipping CI check"
fi

echo ""
echo "=== Test Summary ==="
echo "Local tests: PASSED"
if [ -n "$pr_number" ] && [ -z "$failed_checks" ]; then
    echo "GitHub CI: PASSED"
else
    echo "GitHub CI: Check required"
fi

log_message "INFO" "Test execution completed"