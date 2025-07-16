#!/bin/bash
# Integration command - Create fresh branch from main and cleanup
# Usage: ./integrate.sh [branch-name] [--force]

# Initialize security and configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/security_utils.sh"
source "$SCRIPT_DIR/config.sh"

# Initialize security utilities
init_security_utils || handle_error "Failed to initialize security utilities"
init_config || handle_error "Failed to initialize configuration"

# Parse arguments
branch_name=""
force_flag=""
for arg in "$@"; do
    if [ "$arg" = "--force" ]; then
        force_flag="--force"
    else
        branch_name="$arg"
    fi
done

log_message "INFO" "Starting integration process"
echo "=== Integration Process Starting ==="

# Get current branch for cleanup
current_branch=$(get_current_branch)
validate_branch_name "$current_branch" || handle_error "Invalid current branch name: $current_branch"

# Stop test server if running (check for PID file)
pid_file=$(get_safe_pid_path "$current_branch")
if [ -f "$pid_file" ]; then
    pid=$(safe_file_operation "read" "$pid_file")
    if validate_pid "$pid" && kill -0 "$pid" 2>/dev/null; then
        echo "Stopping test server for branch $current_branch (PID: $pid)..."
        log_message "INFO" "Stopping test server with PID: $pid"
        kill "$pid" || log_message "WARN" "Failed to stop process $pid"
        safe_file_operation "delete" "$pid_file"
    else
        log_message "WARN" "Invalid or dead PID in file: $pid_file"
        safe_file_operation "delete" "$pid_file"
    fi
fi

# Check for uncommitted changes unless forced
if [ -z "$force_flag" ]; then
    if [ -n "$(secure_git_command status --porcelain)" ]; then
        echo "❌ Uncommitted changes detected. Commit or stash them first."
        echo "   Use --force to override this check."
        exit 1
    fi
fi

# Run the integrate script if it exists
if [ -f "./integrate.sh" ] && [ "$0" != "./integrate.sh" ]; then
    echo "Running project integrate.sh..."
    log_message "INFO" "Running project-specific integrate.sh"
    ./integrate.sh "$branch_name" || handle_error "Project integrate.sh failed"
else
    # Fallback implementation
    echo "Switching to $DEFAULT_BRANCH branch..."
    log_message "INFO" "Switching to $DEFAULT_BRANCH branch"
    secure_git_command checkout "$DEFAULT_BRANCH" || handle_error "Failed to checkout $DEFAULT_BRANCH"
    
    echo "Pulling latest changes..."
    log_message "INFO" "Pulling latest changes from origin/$DEFAULT_BRANCH"
    secure_git_command pull origin "$DEFAULT_BRANCH" || handle_error "Failed to pull latest changes"
    
    # Create new branch
    if [ -z "$branch_name" ]; then
        # Generate timestamp-based branch name
        timestamp=$(date +%s)
        branch_name="dev$timestamp"
    fi
    
    # Validate the branch name
    validate_branch_name "$branch_name" || handle_error "Invalid branch name: $branch_name"
    
    echo "Creating new branch: $branch_name"
    log_message "INFO" "Creating new branch: $branch_name"
    secure_git_command checkout -b "$branch_name" || handle_error "Failed to create branch: $branch_name"
fi

# Clean up old branch resources
echo ""
echo "=== Cleanup Complete ==="
echo "✅ Now on branch: $(get_current_branch)"
echo "✅ Test server stopped and resources cleaned"
echo ""
echo "Next steps:"
echo "1. Start working on your new feature"
echo "2. Use ./push.sh when ready to push changes"
echo "3. Test server will start automatically on push"

log_message "INFO" "Integration process completed successfully"