#!/usr/bin/env bash
# Multi-Environment Memory Backup with Git-Based Distributed Locking
# VERSION: 3.0.0 - True distributed locking for multiple machines

set -euo pipefail

# Configuration
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE_STAMP=$(date '+%Y-%m-%d')
HOSTNAME=$(hostname -s)
REPO_URL="https://github.com/jleechanorg/worldarchitect-memory-backups.git"
REPO_DIR="$HOME/.cache/memory-backup-repo"
LOCK_BRANCH="backup-lock"
LOCK_TIMEOUT=60
LOCK_RETRY_DELAY=2

# Logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$HOSTNAME:$$]: $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Acquire distributed lock using Git branch
acquire_distributed_lock() {
    local lock_acquired=false
    local elapsed=0
    local lock_id="$HOSTNAME-$$-$(date +%s)"

    log "Attempting to acquire distributed lock (ID: $lock_id)..."

    cd "$REPO_DIR" || error_exit "Cannot access repository"

    while [ $elapsed -lt $LOCK_TIMEOUT ]; do
        # Fetch latest state
        git fetch origin >/dev/null 2>&1

        # Check if lock branch exists
        if git show-ref --verify --quiet "refs/remotes/origin/$LOCK_BRANCH"; then
            # Lock exists, check if it's stale
            local lock_age=$(git log -1 --format=%ct "origin/$LOCK_BRANCH" 2>/dev/null || echo "0")
            local current_time=$(date +%s)
            local age_seconds=$((current_time - lock_age))

            if [ $age_seconds -gt $LOCK_TIMEOUT ]; then
                log "Found stale lock (${age_seconds}s old), attempting to break it..."
                # Try to delete stale lock
                if git push origin --delete "$LOCK_BRANCH" 2>/dev/null; then
                    log "Stale lock removed"
                fi
            else
                log "Lock held by another process (${age_seconds}s old), waiting..."
                sleep $LOCK_RETRY_DELAY
                elapsed=$((elapsed + LOCK_RETRY_DELAY))
                continue
            fi
        fi

        # Try to create lock branch
        echo "$lock_id" > .lock_info
        echo "Host: $HOSTNAME" >> .lock_info
        echo "PID: $$" >> .lock_info
        echo "Time: $TIMESTAMP" >> .lock_info

        git add .lock_info
        git commit -m "Lock acquired by $HOSTNAME (PID: $$)" >/dev/null 2>&1 || true

        # Try to push lock branch (atomic operation)
        if git push origin "HEAD:refs/heads/$LOCK_BRANCH" 2>/dev/null; then
            lock_acquired=true
            log "Distributed lock acquired successfully"
            break
        fi

        # Failed to acquire, another process got it first
        git reset --hard HEAD~1 >/dev/null 2>&1 || true
        sleep $LOCK_RETRY_DELAY
        elapsed=$((elapsed + LOCK_RETRY_DELAY))
    done

    if [ "$lock_acquired" = false ]; then
        error_exit "Failed to acquire distributed lock after $LOCK_TIMEOUT seconds"
    fi

    # Return to main branch
    git checkout main >/dev/null 2>&1
}

# Release distributed lock
release_distributed_lock() {
    log "Releasing distributed lock..."

    cd "$REPO_DIR" || return

    # Delete lock branch
    if git push origin --delete "$LOCK_BRANCH" 2>/dev/null; then
        log "Distributed lock released"
    else
        log "Warning: Could not release lock (may have been released already)"
    fi
}

# Ensure lock is released on exit
trap 'release_distributed_lock' EXIT INT TERM

# Create unified memory with distributed locking
create_unified_memory_safe() {
    log "Creating unified memory with distributed lock protection..."

    # Acquire distributed lock
    acquire_distributed_lock

    # Pull latest changes while holding lock
    git pull origin main --no-edit >/dev/null 2>&1 || true

    local temp_unified=$(mktemp)
    local total_entities=0
    local env_count=0

    {
        echo "# Unified Memory MCP Backup"
        echo "# Generated: $TIMESTAMP"
        echo "# Host: $HOSTNAME"
        echo "# Process: $$"
        echo "# Lock: Distributed (Git-based)"
        echo ""
    } > "$temp_unified"

    # Process all environment-specific memory files
    for mem_file in memory-*.json; do
        if [ -f "$mem_file" ] && [[ "$mem_file" =~ ^memory-[^.]+\.json$ ]]; then
            local env_name=$(basename "$mem_file" .json | sed 's/memory-//')
            local env_entities=$(jq 'length' "$mem_file" 2>/dev/null || echo "0")

            echo "# Environment: $env_name ($env_entities entities)" >> "$temp_unified"

            jq -r '.[] | tostring' "$mem_file" >> "$temp_unified" 2>/dev/null || {
                grep '^{' "$mem_file" >> "$temp_unified" 2>/dev/null || true
            }

            total_entities=$((total_entities + env_entities))
            env_count=$((env_count + 1))
            log "Added $env_entities entities from $env_name environment"
        fi
    done

    # Atomic move
    mv "$temp_unified" "memory.json"

    log "Created unified memory.json: $total_entities entities from $env_count environments"

    # Commit and push while still holding lock
    git add memory.json
    git commit -m "Updated unified memory (locked by $HOSTNAME)" >/dev/null 2>&1 || true
    git push origin main

    # Lock will be released by trap on exit
}

# Alternative implementation using lock files in the repository
create_lock_file_based() {
    local lock_file=".memory_lock"
    local my_lock_id="$HOSTNAME-$$-$(date +%s)"

    # Try to create lock file
    echo "$my_lock_id" > "$lock_file"
    git add "$lock_file"
    git commit -m "Lock: $my_lock_id" >/dev/null 2>&1

    # Push and see if we win the race
    if git push origin main 2>/dev/null; then
        log "Lock acquired via lock file"
        return 0
    fi

    # We lost the race, pull and check who has the lock
    git pull origin main --no-edit
    local current_lock=$(cat "$lock_file")

    if [ "$current_lock" = "$my_lock_id" ]; then
        # We got it after merge
        return 0
    else
        # Someone else has it
        return 1
    fi
}

# Main execution remains similar
main() {
    log "Starting distributed memory backup v3.0.0"
    log "Repository: $REPO_URL"
    log "Memory file: $MEMORY_FILE"
    log "Host: $HOSTNAME"

    # Standard setup...
    # ... (validation, repository setup, etc.)

    # Create unified file with distributed locking
    create_unified_memory_safe

    log "Backup completed successfully"
}

main "$@"
