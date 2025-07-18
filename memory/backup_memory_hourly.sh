#!/bin/bash
# Memory MCP Hourly Backup Script - Updates Daily PR
# Version: 1.0.0

set -e

# Configuration
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_STAMP=$(date +"%Y-%m-%d")
BACKUP_BRANCH="memory-backup-${DATE_STAMP}"

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

# Check if today's backup branch exists
if ! git rev-parse --verify origin/${BACKUP_BRANCH} >/dev/null 2>&1; then
    log "No backup branch for today. Running full backup..."
    "$(dirname "$BASH_SOURCE")/backup_memory_pr.sh"
    exit 0
fi

# Quick update to existing branch
log "Updating existing backup branch: ${BACKUP_BRANCH}"
git checkout ${BACKUP_BRANCH} >/dev/null 2>&1
git pull origin ${BACKUP_BRANCH} >/dev/null 2>&1

# Count entities
OLD_COUNT=$(grep -c '^{' memory.json 2>/dev/null || echo "0")
NEW_COUNT=$(grep -c '^{' "$MEMORY_FILE" 2>/dev/null || echo "0")

# Copy memory file
cp "$MEMORY_FILE" memory.json

# Validate backup file
LAST_LINE=$(tail -1 memory.json)
if ! echo "$LAST_LINE" | jq . >/dev/null 2>&1; then
    log "ERROR - Backup file appears corrupted. Last line is not valid JSON:"
    log "$LAST_LINE"
    git checkout "$CURRENT_BRANCH" >/dev/null 2>&1
    exit 1
fi

# Check for changes
git add memory.json
if git diff --cached --quiet; then
    log "No changes since last backup"
    git checkout "$CURRENT_BRANCH" >/dev/null 2>&1
    exit 0
fi

# Commit and push
CHANGE=$((NEW_COUNT - OLD_COUNT))
git commit -m "Hourly update: ${TIMESTAMP} (${NEW_COUNT} entities, +${CHANGE})" >/dev/null 2>&1
git push origin ${BACKUP_BRANCH} >/dev/null 2>&1

log "Hourly backup complete: ${NEW_COUNT} entities (+${CHANGE})"

# Return to original branch
git checkout "$CURRENT_BRANCH" >/dev/null 2>&1