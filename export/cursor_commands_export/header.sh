#!/bin/bash
# Header command - Generate mandatory branch header
# Usage: ./header.sh

# Initialize security and configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/security_utils.sh"
source "$SCRIPT_DIR/config.sh"

# Initialize security utilities
init_security_utils || handle_error "Failed to initialize security utilities"
init_config || handle_error "Failed to initialize configuration"

# Function to find project root by searching for CLAUDE.md
find_project_root() {
    local current_dir="$SCRIPT_DIR"
    local max_depth=20
    local depth=0
    
    while [ "$depth" -lt "$max_depth" ]; do
        if [ -f "$current_dir/CLAUDE.md" ]; then
            echo "$current_dir"
            return 0
        fi
        
        if [ "$current_dir" = "/" ] || [ "$current_dir" = "" ]; then
            return 1
        fi
        
        current_dir=$(dirname "$current_dir")
        ((depth++))
    done
    
    return 1
}

# Try to find and use the git-header script
if project_root=$(find_project_root) && [ -f "$project_root/claude_command_scripts/git-header.sh" ]; then
    log_message "INFO" "Using git-header.sh from project root"
    "$project_root/claude_command_scripts/git-header.sh"
else
    # Fallback implementation using secure functions
    local_branch=$(get_current_branch)
    validate_branch_name "$local_branch" || handle_error "Invalid current branch name: $local_branch"
    
    remote=$(get_upstream_branch)
    
    # Get PR info using secure gh command
    pr_info=$(get_pr_info "$local_branch")
    
    # Generate header using config function
    header=$(generate_header)
    echo "$header"
    
    log_message "INFO" "Generated header: $header"
fi