#!/usr/bin/env bash
# Production-Ready Multi-Machine Memory Backup with File-Based Distributed Locking
# VERSION: 5.0.0 - Final solution with distributed coordination

set -euo pipefail

# Configuration
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE_STAMP=$(date '+%Y-%m-%d')
HOSTNAME=$(hostname -s)
REPO_URL="${BACKUP_REPO_URL:-}"
# Validate repository URL is set
if [ -z "$REPO_URL" ]; then
    echo "❌ Error: BACKUP_REPO_URL environment variable is not set" >&2
    echo "Please set BACKUP_REPO_URL to your GitHub memory backup repository URL" >&2
    exit 1
fi
REPO_DIR="$HOME/.cache/memory-backup-repo"
LOCK_FILE=".backup_lock"
LOCK_TIMEOUT=60
MAX_RETRIES=30

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$HOSTNAME:$$]: $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Setup repository if needed
setup_repository() {
    if [ ! -d "$REPO_DIR" ]; then
        log "Cloning repository..."
        git clone "$REPO_URL" "$REPO_DIR" || error_exit "Failed to clone"
    fi

    cd "$REPO_DIR" || error_exit "Cannot access repository"
    git config user.name "$HOSTNAME-backup"
    git config user.email "backup@$HOSTNAME.local"
}

# Try to acquire distributed lock
acquire_distributed_lock() {
    local lock_id="$HOSTNAME:$$:$(date +%s)"
    local attempts=0

    log "Attempting to acquire distributed lock..."

    while [ $attempts -lt $MAX_RETRIES ]; do
        # Fetch latest state
        git fetch origin main >/dev/null 2>&1
        git reset --hard origin/main >/dev/null 2>&1

        # Check if lock exists and is valid
        if [ -f "$LOCK_FILE" ]; then
            local lock_time=$(git log -1 --format=%ct -- "$LOCK_FILE" 2>/dev/null || echo "0")
            local current_time=$(date +%s)
            local lock_age=$((current_time - lock_time))

            if [ $lock_age -lt $LOCK_TIMEOUT ]; then
                local lock_owner=$(cat "$LOCK_FILE" | head -1)
                log "Lock held by $lock_owner (${lock_age}s old), waiting..."
                sleep 2
                attempts=$((attempts + 1))
                continue
            else
                log "Found stale lock (${lock_age}s old), breaking it..."
            fi
        fi

        # Try to acquire lock
        echo "$lock_id" > "$LOCK_FILE"
        echo "Host: $HOSTNAME" >> "$LOCK_FILE"
        echo "PID: $$" >> "$LOCK_FILE"
        echo "Acquired: $TIMESTAMP" >> "$LOCK_FILE"

        git add "$LOCK_FILE"
        git commit -m "Lock acquired by $HOSTNAME (PID: $$)" >/dev/null 2>&1

        # Try to push (this is the atomic operation)
        if git push origin main >/dev/null 2>&1; then
            log "Distributed lock acquired successfully!"
            return 0
        fi

        # We lost the race, reset and try again
        git reset --hard origin/main >/dev/null 2>&1
        attempts=$((attempts + 1))
        sleep 1
    done

    error_exit "Failed to acquire lock after $MAX_RETRIES attempts"
}

# Release the distributed lock
release_distributed_lock() {
    log "Releasing distributed lock..."

    cd "$REPO_DIR" || return

    # Only delete if we own it
    if [ -f "$LOCK_FILE" ]; then
        local lock_owner=$(cat "$LOCK_FILE" | head -1)
        local my_id="$HOSTNAME:$$"

        if [[ "$lock_owner" == *"$my_id"* ]]; then
            rm -f "$LOCK_FILE"
            git add "$LOCK_FILE"
            git commit -m "Lock released by $HOSTNAME (PID: $$)" >/dev/null 2>&1
            git push origin main >/dev/null 2>&1 || true
            log "Lock released"
        fi
    fi
}

# Validate environment
validate_environment() {
    if [ ! -f "$MEMORY_FILE" ]; then
        error_exit "Memory file not found: $MEMORY_FILE"
    fi

    if ! command -v jq >/dev/null 2>&1; then
        error_exit "jq is required but not installed"
    fi

    if ! jq empty "$MEMORY_FILE" 2>/dev/null; then
        error_exit "Invalid JSON in memory file"
    fi
}

# Update hostname-specific file
update_hostname_file() {
    local hostname_file="memory-${HOSTNAME}.json"

    cp "$MEMORY_FILE" "$hostname_file"

    local count=$(jq 'length' "$hostname_file" 2>/dev/null || echo "0")
    log "Updated $hostname_file with $count entities"

    git add "$hostname_file"
    git commit -m "Update from $HOSTNAME: $count entities" >/dev/null 2>&1 || true
}

# Create unified memory file (must be called while holding lock)
create_unified_memory() {
    log "Creating unified memory file..."

    local temp_file=$(mktemp)
    local total=0

    echo "[" > "$temp_file"

    local first=true
    for mem_file in memory-*.json; do
        if [ -f "$mem_file" ] && [[ "$mem_file" =~ ^memory-[^.]+\.json$ ]]; then
            if [ "$first" = false ]; then
                echo "," >> "$temp_file"
            fi
            first=false

            # Extract just the JSON array contents
            jq -r '.[]' "$mem_file" | while IFS= read -r line; do
                echo "$line" >> "$temp_file"
                total=$((total + 1))
            done
        fi
    done

    echo "]" >> "$temp_file"

    # Validate unified file
    if jq empty "$temp_file" 2>/dev/null; then
        mv "$temp_file" "memory.json"
        local final_count=$(jq length "memory.json")
        log "Created unified memory.json with $final_count total entities"

        git add "memory.json"
        git commit -m "Unified memory updated by $HOSTNAME" >/dev/null 2>&1 || true
    else
        rm -f "$temp_file"
        error_exit "Failed to create valid unified JSON"
    fi
}

# Main backup process
perform_backup() {
    log "Starting distributed backup process..."

    # Setup
    validate_environment
    setup_repository

    # Acquire distributed lock
    acquire_distributed_lock

    # Ensure we release lock on exit
    trap 'release_distributed_lock' EXIT INT TERM

    # Pull latest while holding lock
    git pull origin main --no-edit >/dev/null 2>&1 || true

    # Update our hostname-specific file
    update_hostname_file

    # Create unified file
    create_unified_memory

    # Push all changes
    if git push origin main; then
        log "Successfully pushed all changes"
    else
        error_exit "Failed to push changes"
    fi

    # Lock will be released by trap
    log "Backup completed successfully!"
}

# Run with basic error handling
if perform_backup; then
    exit 0
else
    log "Backup failed"
    exit 1
fi
