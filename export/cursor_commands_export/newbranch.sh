#!/bin/bash
# Newbranch command - Create new branch from latest main
# Usage: ./newbranch.sh [branch-name]
# Alias: nb.sh

# Initialize security and configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/security_utils.sh"
source "$SCRIPT_DIR/config.sh"

# Initialize security utilities
init_security_utils || handle_error "Failed to initialize security utilities"
init_config || handle_error "Failed to initialize configuration"

# Check for uncommitted changes
if [ -n "$(secure_git_command status --porcelain)" ]; then
    echo "❌ Uncommitted changes detected. Please commit or stash them first."
    secure_git_command status --short
    exit 1
fi

# Parse branch name
branch_name="$1"
if [ -z "$branch_name" ]; then
    # Generate timestamp-based branch name
    timestamp=$(date +%s)
    branch_name="dev$timestamp"
fi

# Validate branch name
validate_branch_name "$branch_name" || handle_error "Invalid branch name: $branch_name"

# Check if branch already exists
if secure_git_command rev-parse --verify "$branch_name" >/dev/null 2>&1; then
    echo "❌ Branch '$branch_name' already exists locally"
    echo "Use 'git branch -D $branch_name' to delete it first, or choose a different name"
    exit 1
fi

# Check if branch exists on remote
if secure_git_command ls-remote --heads origin "$branch_name" | grep -q "$branch_name"; then
    echo "❌ Branch '$branch_name' already exists on remote"
    echo "Choose a different branch name"
    exit 1
fi

log_message "INFO" "Creating new branch: $branch_name"
echo "=== Creating New Branch ==="

# Fetch latest from origin
echo "Fetching latest changes from origin..."
log_message "INFO" "Fetching latest changes from origin/$DEFAULT_BRANCH"
secure_git_command fetch origin "$DEFAULT_BRANCH" || handle_error "Failed to fetch from origin. Check your network connection."

# Create and checkout new branch from origin/main
echo "Creating branch '$branch_name' from origin/$DEFAULT_BRANCH..."
log_message "INFO" "Creating and checking out new branch from origin/$DEFAULT_BRANCH"
secure_git_command checkout -b "$branch_name" "origin/$DEFAULT_BRANCH" || handle_error "Failed to create branch. It may already exist."

echo ""
echo "✅ Successfully created and switched to branch: $branch_name"
echo "✅ Tracking: origin/$DEFAULT_BRANCH"
echo ""
echo "Next steps:"
echo "1. Make your changes"
echo "2. Commit your work"
echo "3. Use ./push.sh to push and create PR"

log_message "INFO" "Branch creation completed successfully"