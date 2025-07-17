#!/usr/bin/env bash
# Memory MCP Backup Script - Portable version with fork support and branch safety
# STRICT APPEND-ONLY: Never edit existing memory data, only append new entries
# VERSION: 2.0.0
#
# SETUP: Run memory/setup.sh to configure for your environment
# MANUAL: Copy this script to $HOME/backup_memory.sh and configure paths

set -euo pipefail

# Configuration - can be overridden by environment variables
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
REPO_DIR="${REPO_DIR:-$HOME/worldarchitect-backup}"
CONFIG_FILE="${CONFIG_FILE:-$HOME/.config/mcp-memory/config.json}"
MAX_RETRIES="${MAX_RETRIES:-3}"
LOG_FILE="${LOG_FILE:-$HOME/.cache/mcp-memory/backup.log}"

# Load configuration if available
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        # Extract values from JSON config (simple bash parsing)
        if command -v jq &> /dev/null; then
            MEMORY_FILE=$(jq -r '.memory_file // empty' "$CONFIG_FILE" 2>/dev/null || echo "$MEMORY_FILE")
            REPO_DIR=$(jq -r '.backup_worktree // empty' "$CONFIG_FILE" 2>/dev/null || echo "$REPO_DIR")
            MAX_RETRIES=$(jq -r '.max_backup_retries // empty' "$CONFIG_FILE" 2>/dev/null || echo "$MAX_RETRIES")
            LOG_FILE=$(jq -r '.log_file // empty' "$CONFIG_FILE" 2>/dev/null || echo "$LOG_FILE")
            
            # Check if backup is enabled
            local backup_enabled=$(jq -r '.backup_enabled // empty' "$CONFIG_FILE" 2>/dev/null || echo "true")
            if [ "$backup_enabled" = "false" ]; then
                echo "$(date): Backup disabled in configuration"
                exit 0
            fi
            
            # Check if this is a fork (local-only mode)
            local is_fork=$(jq -r '.is_fork // empty' "$CONFIG_FILE" 2>/dev/null || echo "false")
            local backup_to_remote=$(jq -r '.backup_to_remote // empty' "$CONFIG_FILE" 2>/dev/null || echo "true")
            
            if [ "$is_fork" = "true" ] && [ "$backup_to_remote" = "false" ]; then
                echo "$(date): Fork detected - using local-only backup mode"
                FORK_MODE="true"
            else
                FORK_MODE="false"
            fi
        else
            echo "$(date): jq not available, using default configuration"
            FORK_MODE="false"
        fi
    else
        echo "$(date): No config file found, using defaults"
        FORK_MODE="false"
    fi
}

# Auto-detect repository directory
detect_repo_dir() {
    if [ -d "$REPO_DIR" ]; then
        return 0
    fi
    
    # Try to find backup worktree
    local backup_worktree="$HOME/worldarchitect-backup"
    if [ -d "$backup_worktree" ]; then
        REPO_DIR="$backup_worktree"
        return 0
    fi
    
    # Try to find main repository
    local main_repo
    main_repo=$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null || true)
    if [ -n "$main_repo" ]; then
        REPO_DIR="$main_repo"
        return 0
    fi
    
    # Search for repository in home directory
    main_repo=$(find "$HOME" -name ".git" -type d -path "*/worldarchitect.ai/.git" -exec dirname {} \; | head -1)
    if [ -n "$main_repo" ]; then
        REPO_DIR="$main_repo"
        return 0
    fi
    
    return 1
}

# Version check function
check_script_version() {
    local repo_script="$REPO_DIR/memory/backup_memory.sh"
    local deployed_script="$HOME/backup_memory.sh"
    
    if [ -f "$repo_script" ] && [ -f "$deployed_script" ]; then
        local repo_version=$(grep "# VERSION:" "$repo_script" | cut -d' ' -f3)
        local deployed_version=$(grep "# VERSION:" "$deployed_script" | cut -d' ' -f3)
        
        if [ "$repo_version" != "$deployed_version" ]; then
            echo "$(date): WARNING - Script version mismatch!"
            echo "$(date): Repo version: $repo_version, Deployed version: $deployed_version"
            echo "$(date): Consider updating deployed script: cp $repo_script $deployed_script"
            return 1
        else
            echo "$(date): Script versions match: $repo_version"
            return 0
        fi
    else
        echo "$(date): Cannot check versions - missing script files"
        return 1
    fi
}

# Create backup worktree if it doesn't exist
create_backup_worktree() {
    if [ ! -d "$REPO_DIR" ]; then
        echo "$(date): Creating backup worktree: $REPO_DIR"
        
        # Find the main repository
        local main_repo
        main_repo=$(find "$HOME" -name ".git" -type d -path "*/worldarchitect.ai/.git" -exec dirname {} \; | head -1)
        
        if [ -z "$main_repo" ]; then
            echo "$(date): ERROR - Cannot find main worldarchitect.ai repository"
            exit 1
        fi
        
        # Create worktree
        cd "$main_repo"
        if ! git worktree add "$REPO_DIR" main; then
            echo "$(date): ERROR - Failed to create backup worktree"
            exit 1
        fi
        
        echo "$(date): Backup worktree created successfully"
    fi
}

# Main backup function
perform_backup() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check if memory.json exists
    if [ ! -f "$MEMORY_FILE" ]; then
        echo "$(date): No memory.json file found at $MEMORY_FILE"
        exit 1
    fi
    
    # Ensure backup directory exists
    if ! detect_repo_dir; then
        echo "$(date): Backup directory not found, attempting to create..."
        create_backup_worktree
    fi
    
    # Go to backup directory
    cd "$REPO_DIR" || exit 1
    
    # Check script version if possible
    check_script_version || echo "$(date): Proceeding despite version check issues"
    
    # Save current branch and set up trap for restoration
    local current_branch=$(git branch --show-current)
    
    # If we're already on main in backup worktree, switch to a different branch temporarily
    if [ "$current_branch" = "main" ]; then
        echo "$(date): Already on main branch, switching to backup branch temporarily"
        git checkout -b "backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || git checkout backup_temp 2>/dev/null || true
        current_branch=$(git branch --show-current)
        echo "$(date): Switched to temporary branch: $current_branch"
    fi
    
    # Set up trap for restoration
    trap 'git checkout -q "$current_branch" 2>/dev/null || true' EXIT
    echo "$(date): Current branch: $current_branch"
    
    # Clean worktree should always be clean, but verify anyway
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "$(date): WARNING - Worktree has uncommitted changes, cleaning up"
        git reset --hard HEAD
        git clean -fd
    fi
    
    # Switch to main and pull latest (skip if fork mode)
    git checkout main
    if [ "$FORK_MODE" = "false" ]; then
        git pull origin main
    else
        echo "$(date): Fork mode - skipping pull from origin"
    fi
    
    # STRICT APPEND-ONLY GUARDRAIL
    if [ -f "memory/memory.json" ]; then
        # Check if new file is larger (append-only check)
        local old_size=$(wc -c < memory/memory.json)
        local new_size=$(wc -c < "$MEMORY_FILE")
        
        if [ "$new_size" -lt "$old_size" ]; then
            echo "$(date): ERROR - Memory file shrunk! This violates append-only constraint."
            echo "$(date): Old size: $old_size, New size: $new_size"
            git checkout "$current_branch"
            exit 1
        fi
        
        # Additional content validation - ensure no existing data was modified
        if ! head -c "$old_size" "$MEMORY_FILE" | cmp -s - memory/memory.json; then
            echo "$(date): ERROR - Existing memory data was modified! This violates append-only constraint."
            git checkout "$current_branch"
            exit 1
        fi
        
        echo "$(date): Append-only validation passed. Old: $old_size bytes, New: $new_size bytes"
    fi
    
    # Copy memory file (append-only verified)
    cp "$MEMORY_FILE" memory/memory.json
    
    # Check for changes
    git add memory/memory.json
    if git diff --cached --quiet; then
        echo "$(date): No changes to commit"
        git checkout "$current_branch"
        exit 0
    fi
    
    # Commit changes
    git commit -m "Memory backup: ${timestamp} (append-only)"
    
    # Push to remote (skip if fork mode)
    if [ "$FORK_MODE" = "false" ]; then
        # Handle conflicts by pulling and resolving
        if ! git push origin main; then
            echo "$(date): Push failed, pulling and resolving conflicts..."
            git pull origin main
            
            # Handle memory.json conflicts with validation
            if git status --porcelain | grep -q "UU memory/memory.json"; then
                echo "$(date): Memory conflict detected - validating data integrity..."
                
                # Get the remote version for comparison
                git show HEAD:memory/memory.json > /tmp/remote_memory.json
                
                # Re-validate append-only constraint against remote version
                local remote_size=$(wc -c < /tmp/remote_memory.json)
                local local_size=$(wc -c < "$MEMORY_FILE")
                
                if [ "$local_size" -lt "$remote_size" ]; then
                    echo "$(date): CRITICAL ERROR - Remote has newer data! Local: $local_size, Remote: $remote_size"
                    echo "$(date): This indicates a sync issue - aborting to prevent data loss"
                    rm -f /tmp/remote_memory.json
                    exit 1
                fi
                
                # Verify local file contains all remote data (is superset)
                if ! head -c "$remote_size" "$MEMORY_FILE" | cmp -s - /tmp/remote_memory.json; then
                    echo "$(date): CRITICAL ERROR - Local file is not a superset of remote data"
                    echo "$(date): This indicates data corruption or sync issue - aborting"
                    rm -f /tmp/remote_memory.json
                    exit 1
                fi
                
                echo "$(date): Validation passed - local file is strict superset of remote"
                echo "$(date): Resolving conflict by keeping local version (contains all remote data plus new additions)"
                git checkout --ours memory/memory.json
                git add memory/memory.json
                git commit -m "Resolve memory.json conflict - keep superset version (Local: $local_size, Remote: $remote_size)"
                
                rm -f /tmp/remote_memory.json
            fi
            
            # Try push again
            git push origin main
        fi
    else
        echo "$(date): Fork mode - skipping push to origin (local backup only)"
    fi
    
    # Return to original branch (or create a safe backup branch if original was main)
    if [ "$current_branch" = "main" ] || [ "$current_branch" = "backup_temp" ]; then
        # Don't stay on main, create a safe backup branch
        local backup_branch="backup_$(date +%Y%m%d)"
        git checkout -b "$backup_branch" 2>/dev/null || git checkout "$backup_branch" 2>/dev/null
        echo "$(date): Switched to backup branch: $backup_branch (avoiding main checkout)"
    else
        git checkout "$current_branch"
        echo "$(date): Returned to original branch: $current_branch"
    fi
    
    echo "$(date): Memory backup completed successfully - append-only validated"
}

# Retry wrapper
backup_with_retry() {
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        echo "$(date): Backup attempt $attempt of $MAX_RETRIES"
        
        if perform_backup; then
            echo "$(date): Backup successful on attempt $attempt"
            return 0
        else
            echo "$(date): Backup failed on attempt $attempt"
            if [ $attempt -lt $MAX_RETRIES ]; then
                echo "$(date): Retrying in 10 seconds..."
                sleep 10
            fi
        fi
        
        ((attempt++))
    done
    
    echo "$(date): All backup attempts failed"
    return 1
}

# Main execution
main() {
    echo "$(date): Starting Memory MCP backup (portable version 2.0.0)"
    
    # Load configuration
    load_config
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Run backup with retry
    backup_with_retry
}

# Run main function
main "$@"