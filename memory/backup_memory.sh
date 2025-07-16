#!/usr/bin/env bash
# Memory MCP Backup Script - Direct to main worldarchitect.ai repo with conflict resolution
# STRICT APPEND-ONLY: Never edit existing memory data, only append new entries
# VERSION: 1.3.0
#
# DEPLOYMENT REMINDER: After updating this script in the repo, copy to stable location:
# cp memory/backup_memory.sh $HOME/backup_memory.sh
# 
# Then update crontab to use stable path:
# 0 * * * * $HOME/backup_memory.sh >> $HOME/.cache/mcp-memory/backup.log 2>&1

set -euo pipefail

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

MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
# Auto-detect repo directory with fallback options
REPO_DIR="${REPO_DIR:-$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null || true)}"
REPO_DIR="${REPO_DIR:-$(find "$HOME" -path '*/worldarchitect.ai/.git' -type d -exec dirname {} \; | head -1)}"
if [ -z "$REPO_DIR" ]; then
    echo "$(date): ERROR - Cannot find worldarchitect.ai repository"
    exit 1
fi
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Check if memory.json exists
if [ ! -f "$MEMORY_FILE" ]; then
    echo "$(date): No memory.json file found"
    exit 1
fi

# Go to main repo
cd "$REPO_DIR" || exit 1

# Check script version consistency
check_script_version || echo "$(date): Proceeding despite version mismatch"

# Save current branch and set up trap for restoration
CURRENT_BRANCH=$(git branch --show-current)
trap 'git checkout -q "$CURRENT_BRANCH" 2>/dev/null || true' EXIT
echo "$(date): Current branch: $CURRENT_BRANCH"

# Ensure clean working directory before switching branches
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "$(date): ERROR - Uncommitted changes present, aborting backup"
    exit 1
fi

# Switch to main and pull latest
git checkout main
git pull origin main

# STRICT APPEND-ONLY GUARDRAIL
if [ -f "memory/memory.json" ]; then
    # Check if new file is larger (append-only check)
    OLD_SIZE=$(wc -c < memory/memory.json)
    NEW_SIZE=$(wc -c < "$MEMORY_FILE")
    
    if [ "$NEW_SIZE" -lt "$OLD_SIZE" ]; then
        echo "$(date): ERROR - Memory file shrunk! This violates append-only constraint."
        echo "$(date): Old size: $OLD_SIZE, New size: $NEW_SIZE"
        # Return to original branch
        git checkout "$CURRENT_BRANCH"
        exit 1
    fi
    
    # Additional content validation - ensure no existing data was modified
    if ! head -c "$OLD_SIZE" "$MEMORY_FILE" | cmp -s - memory/memory.json; then
        echo "$(date): ERROR - Existing memory data was modified! This violates append-only constraint."
        # Return to original branch
        git checkout "$CURRENT_BRANCH"
        exit 1
    fi
    
    echo "$(date): Append-only validation passed. Old: $OLD_SIZE bytes, New: $NEW_SIZE bytes"
fi

# Copy memory file (append-only verified)
cp "$MEMORY_FILE" memory/memory.json

# Check for changes
git add memory/memory.json
if git diff --cached --quiet; then
    echo "$(date): No changes to commit"
    # Return to original branch
    git checkout "$CURRENT_BRANCH"
    exit 0
fi

# Commit and push to main
git commit -m "Memory backup: ${TIMESTAMP} (append-only)"

# Handle conflicts by pulling and resolving
if ! git push origin main; then
    echo "$(date): Push failed, pulling and resolving conflicts..."
    git pull origin main
    
    # If there are conflicts in memory.json, validate before resolving
    if git status --porcelain | grep -q "UU memory/memory.json"; then
        echo "$(date): Memory conflict detected - validating data integrity..."
        
        # Get the remote version for comparison
        git show HEAD:memory/memory.json > /tmp/remote_memory.json
        
        # Re-validate append-only constraint against remote version
        REMOTE_SIZE=$(wc -c < /tmp/remote_memory.json)
        LOCAL_SIZE=$(wc -c < "$MEMORY_FILE")
        
        if [ "$LOCAL_SIZE" -lt "$REMOTE_SIZE" ]; then
            echo "$(date): CRITICAL ERROR - Remote has newer data! Local: $LOCAL_SIZE, Remote: $REMOTE_SIZE"
            echo "$(date): This indicates a sync issue - aborting to prevent data loss"
            rm -f /tmp/remote_memory.json
            exit 1
        fi
        
        # Verify local file contains all remote data (is superset)
        if ! head -c "$REMOTE_SIZE" "$MEMORY_FILE" | cmp -s - /tmp/remote_memory.json; then
            echo "$(date): CRITICAL ERROR - Local file is not a superset of remote data"
            echo "$(date): This indicates data corruption or sync issue - aborting"
            rm -f /tmp/remote_memory.json
            exit 1
        fi
        
        echo "$(date): Validation passed - local file is strict superset of remote"
        echo "$(date): Resolving conflict by keeping local version (contains all remote data plus new additions)"
        git checkout --ours memory/memory.json
        git add memory/memory.json
        git commit -m "Resolve memory.json conflict - keep superset version (Local: $LOCAL_SIZE, Remote: $REMOTE_SIZE)"
        
        rm -f /tmp/remote_memory.json
    fi
    
    # Try push again
    git push origin main
fi

# Return to original branch
git checkout "$CURRENT_BRANCH"

echo "$(date): Memory backup completed successfully - append-only validated"
