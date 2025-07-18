#!/bin/bash
# Memory MCP Backup Script - Fixed for NDJSON format
# Version: 2.0.0

set -e

# Configuration
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_VERSION="2.0.0"

# Logging
log() {
    echo "$(date): $1"
}

# Check if memory file exists
if [ ! -f "$MEMORY_FILE" ]; then
    log "ERROR - Memory file not found: $MEMORY_FILE"
    exit 1
fi

# Save current branch
CURRENT_BRANCH=$(git branch --show-current)
log "Current branch: $CURRENT_BRANCH"

# Switch to main and pull latest
log "Switching to main branch and pulling latest..."
git checkout main
git pull origin main

# Count entities in the files for comparison (NDJSON format)
if [ -f "memory.json" ]; then
    OLD_COUNT=$(grep -c '^{' memory.json 2>/dev/null || echo "0")
    NEW_COUNT=$(grep -c '^{' "$MEMORY_FILE" 2>/dev/null || echo "0")
    
    log "Entity count - Old: $OLD_COUNT, New: $NEW_COUNT"
    
    # Warning if significant data loss (more than 10% reduction)
    if [ "$NEW_COUNT" -lt "$OLD_COUNT" ]; then
        LOSS_PERCENT=$(( (OLD_COUNT - NEW_COUNT) * 100 / OLD_COUNT ))
        if [ "$LOSS_PERCENT" -gt 10 ]; then
            log "WARNING - Significant data reduction detected: $LOSS_PERCENT% fewer entities"
            log "Proceeding anyway as Memory MCP may have consolidated data"
        fi
    fi
fi

# Copy memory file
cp "$MEMORY_FILE" memory.json
log "Memory file copied successfully"

# Check for changes
git add memory.json
if git diff --cached --quiet; then
    log "No changes detected in memory data"
    git checkout "$CURRENT_BRANCH"
    exit 0
fi

# Commit and push to main
ENTITY_COUNT=$(grep -c '^{' memory.json 2>/dev/null || echo "0")
git commit -m "Memory backup: ${TIMESTAMP} ($ENTITY_COUNT entities)"

# Handle conflicts by pulling and resolving
if ! git push origin main; then
    log "Push failed, pulling and resolving conflicts..."
    git pull origin main
    
    # If there's a merge conflict, use theirs (remote) and merge our changes
    if [ -f memory.json.orig ]; then
        log "Memory conflict detected - merging data..."
        
        # Create merged file by combining unique entries
        python3 << 'EOF' "$MEMORY_FILE"
import json
import sys

seen = set()
output = []

# Read all JSON objects from both files
for line in open('memory.json.orig'):
    try:
        obj = json.loads(line.strip())
        key = json.dumps(obj, sort_keys=True)
        if key not in seen:
            seen.add(key)
            output.append(obj)
    except:
        pass

# Read from memory file passed as argument
memory_file = sys.argv[1]
for line in open(memory_file):
    try:
        obj = json.loads(line.strip())
        key = json.dumps(obj, sort_keys=True)
        if key not in seen:
            seen.add(key)
            output.append(obj)
    except:
        pass

# Write merged output
with open('memory.json', 'w') as f:
    for obj in output:
        f.write(json.dumps(obj) + '\n')

print(f'Merged {len(output)} unique entries')
EOF
        
        rm -f memory.json.orig
        git add memory.json
        git commit -m "Memory backup: ${TIMESTAMP} (merged)"
    fi
    
    # Try pushing again
    git push origin main
fi

# Return to original branch
git checkout "$CURRENT_BRANCH"

log "Memory backup completed successfully"