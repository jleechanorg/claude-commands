#!/bin/bash
# Memory MCP Backup Script with Daily PR Creation
# Version: 3.0.0

set -euo pipefail

# Configuration
MEMORY_FILE="${MEMORY_FILE:-$HOME/.cache/mcp-memory/memory.json}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_STAMP=$(date +"%Y-%m-%d")
SCRIPT_VERSION="3.0.0"
BACKUP_BRANCH="memory-backup-${DATE_STAMP}"
PR_TITLE="Memory backup: ${DATE_STAMP}"

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

# Fetch latest from remote
log "Fetching latest from remote..."
git fetch origin main

# Check if backup branch already exists for today
if git rev-parse --verify origin/${BACKUP_BRANCH} >/dev/null 2>&1; then
    log "Backup branch for today already exists: ${BACKUP_BRANCH}"
    # Check if PR already exists
    EXISTING_PR=$(gh pr list --head ${BACKUP_BRANCH} --json number --jq '.[0].number' 2>/dev/null || echo "")
    if [ -n "$EXISTING_PR" ]; then
        log "PR #${EXISTING_PR} already exists for today's backup. Updating it..."
        # Checkout existing branch
        git checkout ${BACKUP_BRANCH}
        git pull origin ${BACKUP_BRANCH}
    else
        log "Branch exists but no PR. Will create PR after update."
        git checkout ${BACKUP_BRANCH}
        git pull origin ${BACKUP_BRANCH}
    fi
else
    log "Creating new backup branch: ${BACKUP_BRANCH}"
    # Create new branch from main
    git checkout -b ${BACKUP_BRANCH} origin/main
fi

# Count entities for logging
OLD_COUNT=0
if [ -f "memory.json" ]; then
    OLD_COUNT=$(grep -c '^{' memory.json 2>/dev/null || echo "0")
fi
NEW_COUNT=$(grep -c '^{' "$MEMORY_FILE" 2>/dev/null || echo "0")

log "Entity count - Old: $OLD_COUNT, New: $NEW_COUNT"

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

# Verify jq is available
if ! command -v jq >/dev/null 2>&1; then
    log "ERROR - jq not found; install it before running backups"
    exit 1
fi

# Validate backup file before committing
ENTITY_COUNT=$(grep -c '^{' memory.json 2>/dev/null || echo "0")
LAST_LINE=$(tail -1 memory.json)
if ! echo "$LAST_LINE" | jq . >/dev/null 2>&1; then
    log "ERROR - Backup file appears corrupted. Last line is not valid JSON:"
    log "$LAST_LINE"
    git checkout "$CURRENT_BRANCH"
    exit 1
fi

# Verify file integrity
while IFS= read -r line; do
    if ! echo "$line" | jq . >/dev/null 2>&1; then
        log "ERROR - Invalid JSON line detected in backup"
        log "$line"
        git checkout "$CURRENT_BRANCH"
        exit 1
    fi
done < memory.json

# Commit changes
COMMIT_MSG="Memory backup: ${TIMESTAMP} (${ENTITY_COUNT} entities)

- Previous count: ${OLD_COUNT} entities
- Current count: ${ENTITY_COUNT} entities
- Change: $((ENTITY_COUNT - OLD_COUNT)) entities"

git commit -m "$COMMIT_MSG"

# Push to remote
log "Pushing to remote branch ${BACKUP_BRANCH}..."
git push -u origin ${BACKUP_BRANCH}

# Create or update PR
if [ -n "$EXISTING_PR" ]; then
    log "Updating existing PR #${EXISTING_PR}..."
    # Update PR description with latest stats
    gh pr edit ${EXISTING_PR} --body "# Daily Memory Backup

## Summary
Automated backup of Memory MCP data for ${DATE_STAMP}

## Current Status
- **Total Entities**: ${ENTITY_COUNT}
- **Change from Previous**: $((ENTITY_COUNT - OLD_COUNT)) entities
- **Last Updated**: $(date)

## Backup Details
- Memory file location: \`~/.cache/mcp-memory/memory.json\`
- Backup branch: \`${BACKUP_BRANCH}\`
- Format: NDJSON (newline-delimited JSON)

## Recent Changes
This PR contains the latest memory backup with all learnings, patterns, and relations stored by the Memory MCP server.

---
*This is an automated daily backup. The PR will be updated throughout the day as new memories are added.*"
else
    log "Creating new PR for today's backup..."
    # Create new PR
    PR_URL=$(gh pr create \
        --title "$PR_TITLE" \
        --body "# Daily Memory Backup

## Summary
Automated backup of Memory MCP data for ${DATE_STAMP}

## Current Status
- **Total Entities**: ${ENTITY_COUNT}
- **Starting Count**: ${OLD_COUNT} entities
- **Change**: $((ENTITY_COUNT - OLD_COUNT)) entities added

## Backup Details
- Memory file location: \`~/.cache/mcp-memory/memory.json\`
- Backup branch: \`${BACKUP_BRANCH}\`
- Format: NDJSON (newline-delimited JSON)

## Recent Changes
This PR contains the latest memory backup with all learnings, patterns, and relations stored by the Memory MCP server.

---
*This is an automated daily backup. The PR will be updated throughout the day as new memories are added.*" \
        --base main \
        --head ${BACKUP_BRANCH})
    
    log "Created PR: ${PR_URL}"
fi

# Return to original branch
git checkout "$CURRENT_BRANCH"

log "Memory backup completed successfully"

# Set up cron job if not already set
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_ENTRY="0 2 * * * cd $SCRIPT_DIR && ./backup_memory_pr.sh >> backup.log 2>&1"
if ! crontab -l 2>/dev/null | grep -q "backup_memory_pr.sh"; then
    log "Setting up daily cron job at 2 AM..."
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    log "Cron job installed successfully"
fi