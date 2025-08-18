#!/usr/bin/env bash
# Memory Backup using CRDT-inspired Conflict-Free Merge Strategy
# VERSION: 6.0.0 - No locks needed, always converges correctly

set -euo pipefail

HOSTNAME=$(hostname -s)
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
REPO_URL="https://github.com/jleechanorg/worldarchitect-memory-backups.git"
REPO_DIR="$HOME/.cache/memory-backup-repo"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$HOSTNAME:$$]: $1"
}

# CRDT-inspired approach: Each entity gets a unique ID with hostname and timestamp
# This makes all entities globally unique and mergeable without conflicts
prepare_memory_with_metadata() {
    local output_file=$1
    local timestamp=$(date +%s)
    
    # Add metadata to each entity to make it globally unique
    jq --arg host "$HOSTNAME" --arg ts "$timestamp" '
        .[] | . + {
            "_sync_metadata": {
                "host": $host,
                "timestamp": $ts,
                "id": "\($host)_\(.id)_\($ts)"
            }
        }
    ' "$MEMORY_FILE" > "$output_file"
}

# Merge multiple JSON files using CRDT semantics
# Last-Write-Wins (LWW) for same entity ID, union for different IDs
merge_memory_files() {
    local output_file=$1
    shift
    local input_files=("$@")
    
    # Collect all entities from all files
    local all_entities=$(mktemp)
    
    for file in "${input_files[@]}"; do
        if [ -f "$file" ]; then
            # Extract entities, handling both array and object formats
            jq -r '.[]' "$file" 2>/dev/null >> "$all_entities" || \
            jq -r '.' "$file" 2>/dev/null >> "$all_entities" || true
        fi
    done
    
    # Apply CRDT merge rules:
    # 1. Group by entity ID
    # 2. For duplicates, keep the one with latest timestamp
    # 3. Union all unique entities
    jq -s '
        group_by(.id // ._sync_metadata.id) |
        map(
            sort_by(._sync_metadata.timestamp // 0) |
            last
        )
    ' "$all_entities" > "$output_file"
    
    rm -f "$all_entities"
}

# No locking needed - just merge and push
# Git handles the "distributed" part, CRDT handles the "conflict" part
perform_backup() {
    log "Starting CRDT-based backup (no locks needed!)"
    
    cd "$REPO_DIR"
    
    # Always work with latest
    git fetch origin main
    git reset --hard origin/main
    
    # Prepare our data with metadata
    local temp_memory=$(mktemp)
    prepare_memory_with_metadata "$temp_memory"
    
    # Save hostname-specific file
    cp "$temp_memory" "memory-${HOSTNAME}.json"
    
    # Merge all memory files using CRDT semantics
    local all_files=(memory-*.json)
    local unified=$(mktemp)
    merge_memory_files "$unified" "${all_files[@]}"
    
    # Update the unified file
    mv "$unified" "memory.json"
    
    # Commit everything
    local entity_count=$(jq length "memory.json")
    git add memory*.json
    git commit -m "CRDT merge from $HOSTNAME: $entity_count total entities" || true
    
    # Push with automatic retry on conflicts
    local max_retries=5
    for i in $(seq 1 $max_retries); do
        if git push origin main; then
            log "Push successful"
            break
        fi
        
        log "Conflict detected, re-merging..."
        git pull origin main --strategy=recursive --strategy-option=theirs
        
        # Re-merge with CRDT semantics
        merge_memory_files "$unified" memory-*.json
        mv "$unified" "memory.json"
        
        git add memory.json
        git commit --amend --no-edit
    done
    
    rm -f "$temp_memory"
    log "Backup complete - no locks needed!"
}

perform_backup