#!/bin/bash
# Context command - Show current context and project state
# Usage: ./context.sh

# Initialize security and configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/security_utils.sh"
source "$SCRIPT_DIR/config.sh"

# Initialize security utilities
init_security_utils || handle_error "Failed to initialize security utilities"
init_config || handle_error "Failed to initialize configuration"

log_message "INFO" "Displaying current context"

echo "=== Current Context ==="
echo ""

# Git context
echo "Git Status:"
current_branch=$(get_current_branch)
validate_branch_name "$current_branch" || handle_error "Invalid branch name: $current_branch"

echo "Branch: $current_branch"
echo "Remote: $(get_upstream_branch)"

# Check for PR
pr_info=$(get_pr_info "$current_branch")
echo "PR: $pr_info"

# Working directory status
echo ""
echo "Working Directory:"
modified=$(secure_git_command status --porcelain | wc -l)
echo "Modified files: $modified"

if [ $modified -gt 0 ]; then
    echo "Changes:"
    secure_git_command status --short
fi

# Recent commits
echo ""
echo "Recent Commits:"
secure_git_command log --oneline -5

# Test status
echo ""
echo "Test Status:"
if [ -f "$TEST_SCRIPT" ]; then
    echo "Run ./test.sh to check test status"
else
    echo "No test runner found at: $TEST_SCRIPT"
fi

# Server status
echo ""
echo "Development Server:"
pid_file=$(get_safe_pid_path "$current_branch")
if [ -f "$pid_file" ]; then
    pid=$(safe_file_operation "read" "$pid_file")
    if validate_pid "$pid" && kill -0 "$pid" 2>/dev/null; then
        echo "Server running (PID: $pid)"
        port=$(calculate_port "$current_branch")
        echo "URL: http://localhost:$port"
        
        # Show log file location
        log_file=$(get_safe_log_path "$current_branch")
        echo "Logs: $log_file"
    else
        echo "Stale PID file found, server not running"
        log_message "WARN" "Stale PID file found for branch $current_branch"
    fi
else
    echo "No server running for current branch"
fi

echo ""
echo "=== End Context ==="

log_message "INFO" "Context display completed"