#!/bin/bash
# PR command - Create pull request from current branch
# Usage: ./pr.sh [task-description]

# Initialize security and configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/security_utils.sh"
source "$SCRIPT_DIR/config.sh"

# Initialize security utilities
init_security_utils || handle_error "Failed to initialize security utilities"
init_config || handle_error "Failed to initialize configuration"

if [ -z "$1" ]; then
    echo "Usage: ./pr.sh 'task description'"
    echo "Example: ./pr.sh 'Add dark mode toggle to settings'"
    exit 1
fi

task_description="$*"
validate_pr_title "$task_description" || handle_error "Invalid task description"

log_message "INFO" "Creating PR for: $task_description"
echo "=== Creating PR for: $task_description ==="

# Get current branch
current_branch=$(get_current_branch)
validate_branch_name "$current_branch" || handle_error "Invalid branch name: $current_branch"

# Check if on main branch or other protected branches
for protected_branch in "${PROTECTED_BRANCHES[@]}"; do
    if [ "$current_branch" = "$protected_branch" ]; then
        echo "❌ Cannot create PR from protected branch: $protected_branch"
        echo "Create a feature branch first with ./newbranch.sh"
        exit 1
    fi
done

# Check for existing PR
existing_pr=$(secure_gh_command pr list --head "$current_branch" --json number --jq '.[0].number' 2>/dev/null)
if [ -n "$existing_pr" ]; then
    echo "❌ PR #$existing_pr already exists for this branch"
    pr_url=$(secure_gh_command pr view "$existing_pr" --json url --jq '.url')
    echo "View at: $pr_url"
    exit 1
fi

echo ""
echo "=== Pre-PR Checklist ==="

# Run tests
echo "Running tests..."
log_message "INFO" "Running test suite for PR creation"
if [ -f "$TEST_SCRIPT" ]; then
    "$TEST_SCRIPT" || handle_error "Tests failed. Fix them before creating PR."
else
    handle_error "Test script not found: $TEST_SCRIPT"
fi
echo "✅ Tests passed"

# Check for uncommitted changes
if [ -n "$(secure_git_command status --porcelain)" ]; then
    echo "❌ Uncommitted changes found. Commit them first."
    exit 1
fi
echo "✅ Working directory clean"

# Push latest changes
echo ""
echo "Pushing latest changes..."
log_message "INFO" "Pushing latest changes to remote"
secure_git_command push origin HEAD || handle_error "Failed to push. Resolve issues first."

# Generate PR body
echo ""
echo "=== Creating PR ==="

pr_title="$task_description"
validate_pr_title "$pr_title" || handle_error "Invalid PR title"

# Generate commit list safely
commit_list=$(secure_git_command log origin/main..HEAD --oneline | sed 's/^/- /' | head -20)
file_changes=$(secure_git_command diff origin/main..HEAD --name-status | head -20)
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Use the PR template from config
pr_body="$PR_TEMPLATE"
pr_body="${pr_body//TASK_DESCRIPTION/$task_description}"
pr_body="${pr_body//BRANCH_NAME/$current_branch}"
pr_body="${pr_body//COMMIT_LIST/$commit_list}"
pr_body="${pr_body//TIMESTAMP/$timestamp}"
pr_body="${pr_body//FILE_CHANGES/$file_changes}"

validate_pr_description "$pr_body" || handle_error "Generated PR description is invalid"

# Create the PR
log_message "INFO" "Creating PR with title: $pr_title"
secure_gh_command pr create --title "$pr_title" --body "$pr_body" --head "$current_branch" || handle_error "Failed to create PR"

echo ""
echo "✅ PR created successfully!"
new_pr=$(secure_gh_command pr list --head "$current_branch" --json number,url --jq '.[0] | "#\(.number) - \(.url)"')
echo "PR: $new_pr"

log_message "INFO" "PR creation completed successfully"