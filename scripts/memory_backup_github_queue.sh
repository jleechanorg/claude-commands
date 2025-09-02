#!/usr/bin/env bash
# Memory Backup with GitHub-based Queue System
# Simple, reliable, no extra infrastructure needed
# VERSION: 4.0.0

set -euo pipefail

HOSTNAME=$(hostname -s)
REPO_URL="${BACKUP_REPO_URL:-}"
REPO_DIR="$HOME/.cache/memory-backup-repo"
QUEUE_BRANCH_PREFIX="queue"
PROCESSING_BRANCH="processing"
MAX_WAIT=120

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$HOSTNAME:$$]: $1"
}

# Add ourselves to the queue
join_queue() {
    local queue_id="$HOSTNAME-$$-$(date +%s)"
    local queue_branch="$QUEUE_BRANCH_PREFIX-$queue_id"

    log "Joining backup queue as: $queue_id"

    cd "$REPO_DIR"
    git fetch origin

    # Create our queue entry branch
    git checkout -b "$queue_branch"
    echo "$queue_id" > ".queue_entry"
    echo "Host: $HOSTNAME" >> ".queue_entry"
    echo "Time: $(date -Iseconds)" >> ".queue_entry"

    git add .queue_entry
    git commit -m "Queue entry: $queue_id"

    # Push our queue branch
    if git push origin "$queue_branch"; then
        log "Successfully joined queue"
        echo "$queue_branch"
    else
        log "Failed to join queue"
        return 1
    fi
}

# Wait for our turn in the queue
wait_for_turn() {
    local my_branch=$1
    local my_id=$(echo "$my_branch" | sed "s/$QUEUE_BRANCH_PREFIX-//")
    local waited=0

    log "Waiting for our turn in queue..."

    while [ $waited -lt $MAX_WAIT ]; do
        git fetch origin

        # Get all queue branches sorted by creation time
        local queue_branches=$(git for-each-ref --sort=committerdate \
            --format='%(refname:short)' "refs/remotes/origin/$QUEUE_BRANCH_PREFIX-*" | \
            sed 's|origin/||')

        # Check if we're first in queue
        local first_in_queue=$(echo "$queue_branches" | head -1)

        if [ "$first_in_queue" = "$my_branch" ]; then
            # Try to acquire processing lock
            if acquire_processing_lock "$my_id"; then
                log "Our turn! Processing lock acquired"
                return 0
            fi
        fi

        # Show queue position
        local position=$(echo "$queue_branches" | grep -n "$my_branch" | cut -d: -f1)
        log "Queue position: $position, waiting..."

        sleep 5
        waited=$((waited + 5))
    done

    log "Timeout waiting in queue"
    return 1
}

# Acquire processing lock
acquire_processing_lock() {
    local lock_id=$1

    # Try to create processing branch
    git checkout main
    git checkout -b "$PROCESSING_BRANCH"
    echo "$lock_id" > ".processing"
    git add .processing
    git commit -m "Processing: $lock_id"

    if git push origin "$PROCESSING_BRANCH" 2>/dev/null; then
        log "Processing lock acquired"
        return 0
    else
        # Someone else is processing
        git checkout main
        git branch -D "$PROCESSING_BRANCH"
        return 1
    fi
}

# Leave queue and release processing lock
leave_queue() {
    local my_branch=$1

    log "Leaving queue and releasing locks..."

    cd "$REPO_DIR"

    # Delete our queue branch
    git push origin --delete "$my_branch" 2>/dev/null || true

    # Delete processing branch
    git push origin --delete "$PROCESSING_BRANCH" 2>/dev/null || true

    git checkout main
}

# Process with queue protection
process_with_queue() {
    local queue_branch=""

    # Join queue
    queue_branch=$(join_queue) || return 1

    # Ensure cleanup on exit
    trap "leave_queue '$queue_branch'" EXIT INT TERM

    # Wait for our turn
    if wait_for_turn "$queue_branch"; then
        log "Starting protected backup process..."

        # Pull latest while we have the lock
        git checkout main
        git pull origin main

        # Do the actual backup work here
        # ... update memory files ...
        # ... create unified memory ...

        log "Backup complete"
    else
        log "Failed to acquire processing turn"
        return 1
    fi
}

# Main remains similar, just uses queue
main() {
    log "Starting queue-based distributed backup"

    # Setup repository
    # ... standard setup ...

    # Process with queue protection
    process_with_queue

    log "Distributed backup complete"
}

main "$@"
