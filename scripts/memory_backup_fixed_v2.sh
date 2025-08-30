#!/usr/bin/env bash
# Multi-Environment Safe Memory Backup Script with Proper Locking
# VERSION: 2.1.0 - Fixes race conditions identified in v2.0.0

set -euo pipefail

# Configuration
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE_STAMP=$(date '+%Y-%m-%d')
HOSTNAME=$(hostname -s)
REPO_URL="https://github.com/jleechanorg/worldarchitect-memory-backups.git"
REPO_DIR="$HOME/.cache/memory-backup-repo"
LOCK_DIR="/var/lock"
LOCK_FILE="$LOCK_DIR/memory-backup.lock"
LOCK_TIMEOUT=30

# Ensure lock directory exists
mkdir -p "$LOCK_DIR" 2>/dev/null || true

# Logging with process ID for debugging parallel execution
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$$]: $1"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Acquire lock with timeout
acquire_lock() {
    local lock_acquired=false
    local elapsed=0

    log "Attempting to acquire lock..."

    while [ $elapsed -lt $LOCK_TIMEOUT ]; do
        if mkdir "$LOCK_FILE" 2>/dev/null; then
            lock_acquired=true
            log "Lock acquired successfully"
            # Store PID in lock for debugging
            echo $$ > "$LOCK_FILE/pid"
            echo "$HOSTNAME" > "$LOCK_FILE/hostname"
            echo "$(date)" > "$LOCK_FILE/acquired_at"
            break
        fi

        # Check if lock is stale (older than timeout)
        if [ -f "$LOCK_FILE/pid" ]; then
            local lock_pid=$(cat "$LOCK_FILE/pid" 2>/dev/null || echo "0")
            if ! kill -0 "$lock_pid" 2>/dev/null; then
                log "Removing stale lock from PID $lock_pid"
                release_lock
                continue
            fi
        fi

        sleep 1
        elapsed=$((elapsed + 1))
    done

    if [ "$lock_acquired" = false ]; then
        error_exit "Failed to acquire lock after $LOCK_TIMEOUT seconds"
    fi
}

# Release lock
release_lock() {
    if [ -d "$LOCK_FILE" ]; then
        rm -rf "$LOCK_FILE"
        log "Lock released"
    fi
}

# Unified cleanup to ensure resources are released and message logged
cleanup() {
    # Log if interrupted (INT/TERM) or on normal exit (EXIT)
    log "Cleaning up before exit (signal or normal termination)"
    release_lock
}

# Register a single cleanup trap for EXIT, INT and TERM.
# This replaces any existing traps for these signals (does not append).
# shellcheck disable=SC2064 # Variables in single quotes expand at trap definition time
trap 'cleanup' EXIT INT TERM

# Validate prerequisites
validate_environment() {
    if [ ! -f "$MEMORY_FILE" ]; then
        error_exit "Memory file not found: $MEMORY_FILE"
    fi

    if ! jq empty "$MEMORY_FILE" 2>/dev/null; then
        error_exit "Memory file is not valid JSON: $MEMORY_FILE"
    fi

    for tool in git jq flock; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            error_exit "Required tool not found: $tool"
        fi
    done

    log "Environment validation passed"
}

# Setup or update repository
setup_repository() {
    if [ ! -d "$REPO_DIR" ]; then
        # Clone needs to be outside of the repo lock
        log "Cloning memory backup repository..."
        git clone "$REPO_URL" "$REPO_DIR" || error_exit "Failed to clone repository"
    fi

    cd "$REPO_DIR" || error_exit "Cannot access repository directory"

    # Use flock for git operations to prevent conflicts
    (
        flock -x 200

        git checkout main || error_exit "Failed to checkout main branch"
        git pull origin main || error_exit "Failed to pull latest changes"

        mkdir -p historical

    ) 200>"$REPO_DIR/.git/backup.lock"

    log "Repository setup complete"
}

# Create historical snapshot with verification
create_historical_snapshot() {
    local snapshot_file="historical/memory-${HOSTNAME}-${DATE_STAMP}.json"

    if [ -f "$snapshot_file" ]; then
        log "Historical snapshot already exists for today: $snapshot_file"
        return 0
    fi

    cp "$MEMORY_FILE" "$snapshot_file" || error_exit "Failed to create historical snapshot"

    # Verify snapshot integrity
    local source_count=$(jq -s length "$MEMORY_FILE" 2>/dev/null || echo "0")
    local snapshot_count=$(jq -s length "$snapshot_file" 2>/dev/null || echo "0")

    if [ "$source_count" -ne "$snapshot_count" ]; then
        error_exit "Snapshot verification failed: counts don't match ($source_count vs $snapshot_count)"
    fi

    # Add metadata header
    local temp_file=$(mktemp "${TMPDIR:-/tmp}/memory_backup.XXXXXX")
    {
        echo "# Memory MCP Backup Snapshot"
        echo "# Date: $TIMESTAMP"
        echo "# Host: $HOSTNAME"
        echo "# Source: $MEMORY_FILE"
        echo "# Entities: $snapshot_count"
        echo "# Checksum: $(sha256sum "$snapshot_file" | cut -d' ' -f1)"
        echo ""
        cat "$snapshot_file"
    } > "$temp_file"

    mv "$temp_file" "$snapshot_file"

    log "Created historical snapshot: $snapshot_file (entities: $snapshot_count)"
}

# Update hostname-specific memory file
update_current_memory() {
    local hostname_file="memory-${HOSTNAME}.json"
    local old_count=0

    if [ -f "$hostname_file" ]; then
        old_count=$(jq -s length "$hostname_file" 2>/dev/null || echo "0")
    fi

    cp "$MEMORY_FILE" "$hostname_file" || error_exit "Failed to update $hostname_file"

    local new_count=$(jq -s length "$hostname_file" 2>/dev/null || echo "0")
    local change=$((new_count - old_count))

    log "Updated $hostname_file: $old_count → $new_count entities (change: $change)"

    echo "$change" # Return change count
}

# Create unified memory.json with proper locking and verification
create_unified_memory() {
    log "Creating unified memory file with lock protection..."

    # Acquire exclusive lock for unified file creation
    acquire_lock

    local temp_unified=$(mktemp "${TMPDIR:-/tmp}/memory_unified.XXXXXX")
    local total_entities=0
    local env_count=0
    local entity_checksums=""

    {
        echo "# Unified Memory MCP Backup"
        echo "# Generated: $TIMESTAMP"
        echo "# Process: $$"
        echo "# Combined from all environment memory files"
        echo ""
    } > "$temp_unified"

    # Read current state of all memory files
    for mem_file in memory-*.json; do
        if [ -f "$mem_file" ] && [[ "$mem_file" =~ ^memory-[^.]+\.json$ ]]; then
            local env_name=$(basename "$mem_file" .json | sed 's/memory-//')
            local env_entities=$(jq -s length "$mem_file" 2>/dev/null || echo "0")
            local env_checksum=$(sha256sum "$mem_file" | cut -d' ' -f1)

            echo "# Environment: $env_name ($env_entities entities, checksum: ${env_checksum:0:8})" >> "$temp_unified"

            # Extract JSON entities with verification
            if jq -r '.[] | tostring' "$mem_file" >> "$temp_unified" 2>/dev/null; then
                total_entities=$((total_entities + env_entities))
                env_count=$((env_count + 1))
                entity_checksums="${entity_checksums}${env_checksum}"
                log "Added $env_entities entities from $env_name environment"
            else
                log "Warning: Failed to parse $mem_file, using fallback"
                grep '^{' "$mem_file" >> "$temp_unified" 2>/dev/null || true
            fi
        fi
    done

    # Calculate unified checksum for verification
    local unified_checksum=$(echo "$entity_checksums" | sha256sum | cut -d' ' -f1)
    echo "# Unified checksum: ${unified_checksum:0:16}" >> "$temp_unified"

    # Atomic move with verification
    local pre_move_size=$(stat -f%z "$temp_unified" 2>/dev/null || stat -c%s "$temp_unified" 2>/dev/null || echo "0")
    mv "$temp_unified" "memory.json"
    local post_move_size=$(stat -f%z "memory.json" 2>/dev/null || stat -c%s "memory.json" 2>/dev/null || echo "0")

    if [ "$pre_move_size" -ne "$post_move_size" ]; then
        error_exit "File corruption detected during unified file creation"
    fi

    log "Created unified memory.json: $total_entities entities from $env_count environments"

    # Store metadata for verification
    echo "$total_entities" > ".unified_count"
    echo "$unified_checksum" > ".unified_checksum"

    # Release lock after successful creation
    release_lock
}

# Enhanced commit and push with verification
commit_and_push() {
    local change_count=$1

    # Use flock for git operations
    (
        flock -x 200

        git add memory*.json historical/ .unified_* || error_exit "Failed to stage changes"

        if git diff --cached --quiet; then
            log "No changes to commit"
            return 0
        fi

        # Get counts for commit message
        local unified_count=$(cat .unified_count 2>/dev/null || echo "0")
        local hostname_file="memory-${HOSTNAME}.json"
        local host_count=$(jq -s length "$hostname_file" 2>/dev/null || echo "0")

        local commit_msg="Memory backup from ${HOSTNAME}: ${TIMESTAMP}

- Environment: ${HOSTNAME} (${host_count} entities, change: ${change_count})
- Unified total: ${unified_count} entities across all environments
- Process ID: $$
- Lock protection: enabled
- Historical snapshot: historical/memory-${HOSTNAME}-${DATE_STAMP}.json

Multi-environment safe backup v2.1.0 with race condition fixes"

        git commit -m "$commit_msg" || error_exit "Failed to commit changes"

    ) 200>"$REPO_DIR/.git/backup.lock"

    # Push with enhanced retry logic
    push_with_retry

    log "Successfully committed and pushed changes"
}

# Enhanced push with retry and verification
push_with_retry() {
    local max_retries=5
    local retry_delay=2

    for i in $(seq 1 $max_retries); do
        log "Push attempt $i/$max_retries..."

        if git push origin main 2>&1 | tee /tmp/push_$$.log; then
            log "Push successful on attempt $i"
            rm -f /tmp/push_$$.log
            return 0
        fi

        if [ $i -eq $max_retries ]; then
            cat /tmp/push_$$.log
            error_exit "Failed to push after $max_retries attempts"
        fi

        log "Push failed, analyzing conflict..."

        # Check for specific conflict types
        if grep -q "non-fast-forward" /tmp/push_$$.log; then
            log "Non-fast-forward detected, pulling and retrying..."

            # Stash local changes to prevent data loss
            local stash_name="backup-$(date +%s)-$$"
            git stash save "$stash_name"

            # Pull with rebase
            if ! git pull --rebase origin main; then
                log "Rebase failed, attempting merge strategy..."
                git rebase --abort 2>/dev/null || true
                git stash pop

                if ! git pull origin main --no-edit; then
                    error_exit "Unable to resolve conflicts automatically"
                fi

                # Re-create unified file after merge
                log "Recreating unified memory.json after merge..."
                create_unified_memory

                # Re-commit if needed
                if ! git diff --quiet memory.json; then
                    git add memory.json .unified_*
                    git commit --amend --no-edit || error_exit "Failed to amend commit"
                fi
            else
                git stash pop
            fi
        fi

        # Exponential backoff
        local delay=$((retry_delay * (2 ** (i-1))))
        log "Waiting ${delay}s before retry..."
        sleep $delay
    done

    rm -f /tmp/push_$$.log
}

# Main execution with enhanced error handling
main() {
    log "Starting multi-environment safe memory backup v2.1.0"
    log "Target repository: $REPO_URL"
    log "Memory file: $MEMORY_FILE"
    log "Environment: $HOSTNAME"
    log "Process ID: $$"

    validate_environment
    setup_repository
    create_historical_snapshot

    local change_count
    change_count=$(update_current_memory)

    # Create unified file with lock protection
    create_unified_memory

    commit_and_push "$change_count"

    log "Memory backup completed successfully"
    log "Repository location: $REPO_DIR"
}

# Previous signal-specific trap is no longer necessary because the unified
# cleanup trap above handles both normal exits and interruptions.

# Run main function
main "$@"
