#!/bin/bash
# Push command - Pre-push review, validation, PR update
# Usage: ./push.sh

# Initialize security and configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/security_utils.sh"
source "$SCRIPT_DIR/config.sh"

# Initialize security utilities
init_security_utils || handle_error "Failed to initialize security utilities"
init_config || handle_error "Failed to initialize configuration"

log_message "INFO" "Starting pre-push review process"

echo "=== Pre-Push Review ==="

# Check for untracked files
untracked=$(secure_git_command ls-files --others --exclude-standard)
if [ -n "$untracked" ]; then
    echo "Found untracked files:"
    echo "$untracked"
    echo ""
    
    # Only prompt if in interactive mode
    if [ "$(get_env_setting interactive)" = "true" ]; then
        echo "Would you like to add any of these files? (y/n)"
        read -r response
        if [ "$response" = "y" ]; then
            echo "Enter files to add (space-separated, or 'all' for all files):"
            read -r files_to_add
            
            if [ "$files_to_add" = "all" ]; then
                secure_git_command add . || handle_error "Failed to add all files"
            else
                # Validate each file path before adding
                for file in $files_to_add; do
                    if validate_file_path "$file"; then
                        secure_git_command add "$file" || handle_error "Failed to add file: $file"
                    else
                        handle_error "Invalid file path: $file"
                    fi
                done
            fi
            secure_git_command status
        fi
    else
        log_message "INFO" "Non-interactive mode: skipping file addition prompt"
    fi
fi

# Check if there are changes to commit
if [ -n "$(secure_git_command status --porcelain)" ]; then
    echo "Uncommitted changes detected. Commit them first."
    exit 1
fi

# Run tests
echo ""
echo "=== Running Tests ==="
log_message "INFO" "Running test suite"
if [ -f "$TEST_SCRIPT" ]; then
    "$TEST_SCRIPT" || handle_error "Tests failed. Fix before pushing."
else
    handle_error "Test script not found: $TEST_SCRIPT"
fi

# Get current branch
branch=$(get_current_branch)
validate_branch_name "$branch" || handle_error "Invalid branch name: $branch"

# Review changes
echo ""
echo "=== Reviewing Changes ==="
echo "Changes to be pushed:"
secure_git_command log origin/"$branch"..HEAD --oneline 2>/dev/null || secure_git_command log origin/main..HEAD --oneline

echo ""
echo "Files changed:"
secure_git_command diff origin/"$branch"..HEAD --name-status 2>/dev/null || secure_git_command diff origin/main..HEAD --name-status

echo ""
if [ "$(get_env_setting interactive)" = "true" ]; then
    echo "Continue with push? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        echo "Push cancelled"
        exit 0
    fi
else
    log_message "INFO" "Non-interactive mode: proceeding with push"
fi

# Push to remote
echo ""
echo "=== Pushing to Remote ==="
log_message "INFO" "Pushing to remote repository"
secure_git_command push origin HEAD || handle_error "Push failed"

# Check for existing PR
pr_number=$(secure_gh_command pr list --head "$branch" --json number --jq '.[0].number' 2>/dev/null)

if [ -z "$pr_number" ]; then
    echo ""
    if [ "$(get_env_setting interactive)" = "true" ]; then
        echo "No PR exists for this branch. Create one? (y/n)"
        read -r response
        if [ "$response" = "y" ]; then
            echo "Enter PR title:"
            read -r pr_title
            validate_pr_title "$pr_title" || handle_error "Invalid PR title"
            
            echo "Enter PR description (press Enter twice when done):"
            pr_desc=""
            while IFS= read -r line; do
                [ -z "$line" ] && break
                pr_desc+="$line"$'\n'
            done
            validate_pr_description "$pr_desc" || handle_error "Invalid PR description"
            
            secure_gh_command pr create --title "$pr_title" --body "$pr_desc" || handle_error "Failed to create PR"
        fi
    else
        log_message "INFO" "Non-interactive mode: skipping PR creation"
    fi
else
    echo "✅ PR #$pr_number already exists"
    pr_url=$(secure_gh_command pr view "$pr_number" --json url --jq '.url')
    echo "View at: $pr_url"
fi

# Start test server
echo ""
echo "=== Starting Test Server ==="
port=$(calculate_port "$branch")
safe_port=$(get_available_port "$port")

if [ -n "$safe_port" ]; then
    echo "Starting server on port $safe_port for branch $branch..."
    echo "Server will be available at: http://localhost:$safe_port"
    
    # Use safe log path
    log_file=$(get_safe_log_path "$branch")
    echo "Logs: $log_file"
    
    # Note: Actual server start would depend on project setup
    echo "(In Cursor, manually start your development server)"
else
    log_message "WARN" "Could not find available port for test server"
fi

log_message "INFO" "Push process completed successfully"
echo ""
echo "✅ Push complete!"