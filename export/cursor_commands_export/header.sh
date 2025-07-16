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

# Check if the original script exists
if [ -f "./claude_command_scripts/git-header.sh" ]; then
    log_message "INFO" "Using project-specific git-header.sh"
    ./claude_command_scripts/git-header.sh
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