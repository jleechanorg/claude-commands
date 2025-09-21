#!/bin/bash

# fix_backup_repository.sh - Fix backup repository initialization issues

set -euo pipefail

# Configuration
REPO_DIR="$HOME/.cache/memory-backup-repo"
HISTORICAL_DIR="$REPO_DIR/historical"
LOG_FILE="/tmp/fix_backup_repo.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check if directory exists and is accessible
check_directory() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        log "Directory $dir does not exist"
        return 1
    fi

    if [[ ! -r "$dir" ]] || [[ ! -w "$dir" ]]; then
        log "Directory $dir lacks proper read/write permissions"
        return 1
    fi

    log "Directory $dir exists with proper permissions"
    return 0
}

# Create directory with secure permissions
create_directory() {
    local dir="$1"
    local parent_dir
    parent_dir=$(dirname "$dir")

    # Create parent directories if needed
    if [[ ! -d "$parent_dir" ]]; then
        log "Creating parent directory: $parent_dir"
        mkdir -p "$parent_dir" || error_exit "Failed to create parent directory $parent_dir"
    fi

    # Create directory with secure permissions (700 = rwx------)
    log "Creating directory: $dir"
    mkdir -m 700 -p "$dir" || error_exit "Failed to create directory $dir"

    # Verify creation
    check_directory "$dir" || error_exit "Directory verification failed for $dir"
}

# Initialize git repository
init_git_repo() {
    local repo_dir="$1"

    if [[ -d "$repo_dir/.git" ]]; then
        log "Git repository already initialized in $repo_dir"
        return 0
    fi

    log "Initializing git repository in $repo_dir"
    cd "$repo_dir"
    git init || error_exit "Failed to initialize git repository"

    # Create initial commit
    echo "# Memory Backup Repository" > README.md
    git add README.md || error_exit "Failed to add README.md"
    git commit -m "Initial commit" || error_exit "Failed to create initial commit"

    log "Git repository initialized successfully"
}

# Set up historical directory structure
setup_historical_dir() {
    local hist_dir="$1"

    log "Setting up historical directory structure"
    create_directory "$hist_dir"

    # Create subdirectories for organization
    create_directory "$hist_dir/conversations"
    create_directory "$hist_dir/data"
    create_directory "$hist_dir/metadata"

    log "Historical directory structure created"
}

# Validate repository health
validate_repo() {
    local repo_dir="$1"
    local issues_found=0

    log "Validating repository health..."

    # Check repository directory
    if ! check_directory "$repo_dir"; then
        log "Issue: Backup repository directory missing or inaccessible"
        ((issues_found++))
    fi

    # Check git repository
    if [[ ! -d "$repo_dir/.git" ]]; then
        log "Issue: Git repository not initialized"
        ((issues_found++))
    else
        cd "$repo_dir"
        if ! git status >/dev/null 2>&1; then
            log "Issue: Git repository corrupted"
            ((issues_found++))
        fi
    fi

    # Check historical directory
    if ! check_directory "$HISTORICAL_DIR"; then
        log "Issue: Historical directory missing or inaccessible"
        ((issues_found++))
    fi

    # Check historical subdirectories
    for subdir in conversations data metadata; do
        if ! check_directory "$HISTORICAL_DIR/$subdir"; then
            log "Issue: Historical subdirectory $subdir missing"
            ((issues_found++))
        fi
    done

    if [[ $issues_found -eq 0 ]]; then
        log "All repository components are healthy"
        return 0
    else
        log "Found $issues_found issues that need fixing"
        return 1
    fi
}

# Main execution
main() {
    log "Starting backup repository fix process"

    # Validate repository health first
    if validate_repo "$REPO_DIR"; then
        log "Repository is already healthy. No action needed."
        exit 0
    fi

    # Create repository directory if missing
    if [[ ! -d "$REPO_DIR" ]]; then
        create_directory "$REPO_DIR"
    else
        # Ensure proper permissions if directory exists
        chmod 700 "$REPO_DIR" || error_exit "Failed to set permissions on $REPO_DIR"
        check_directory "$REPO_DIR" || error_exit "Repository directory access issue"
    fi

    # Initialize git repository
    init_git_repo "$REPO_DIR"

    # Set up historical directory structure
    setup_historical_dir "$HISTORICAL_DIR"

    # Final validation
    log "Performing final validation..."
    if validate_repo "$REPO_DIR"; then
        log "Repository fix completed successfully"
        exit 0
    else
        error_exit "Repository validation failed after fix attempt"
    fi
}

# Run main function
main "$@"
