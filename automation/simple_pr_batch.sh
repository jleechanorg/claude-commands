#!/bin/bash

# Super simple PR automation using batchcopilot
# Processes PRs updated in last 24 hours that haven't been processed recently

PROCESSED_FILE="/tmp/pr_automation_processed.txt"
LOG_FILE="/tmp/pr_automation_simple.log"
MAX_BATCH_SIZE=5

# Create files if they don't exist
touch "$PROCESSED_FILE"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting simple PR batch processing"

# Get PRs updated in last 24 hours (GitHub CLI JSON format)
RECENT_PRS=$(gh pr list --state open --limit 20 --json number,updatedAt | \
    jq -r '.[] | select((.updatedAt | fromdateiso8601) > (now - 86400)) | .number')

if [ -z "$RECENT_PRS" ]; then
    log "No PRs updated in the last 24 hours"
    exit 0
fi

# Filter out recently processed PRs (within 4 hours)
BATCH_PRS=()
COUNT=0
CURRENT_TIME=$(date +%s)

for PR in $RECENT_PRS; do
    # Check if processed recently
    LAST_PROCESSED=$(grep "^$PR:" "$PROCESSED_FILE" 2>/dev/null | cut -d':' -f2)
    if [ -n "$LAST_PROCESSED" ]; then
        TIME_DIFF=$((CURRENT_TIME - LAST_PROCESSED))
        if [ $TIME_DIFF -lt 14400 ]; then  # 4 hours = 14400 seconds
            log "Skipping PR #$PR (processed $(($TIME_DIFF / 60)) minutes ago)"
            continue
        fi
    fi

    BATCH_PRS+=("$PR")
    COUNT=$((COUNT + 1))

    # Limit batch size
    if [ $COUNT -ge $MAX_BATCH_SIZE ]; then
        break
    fi
done

if [ ${#BATCH_PRS[@]} -eq 0 ]; then
    log "No eligible PRs to process"
    exit 0
fi

# Convert array to comma-separated string for batchcopilot
PR_LIST=$(IFS=','; echo "${BATCH_PRS[*]}")

log "Processing batch: ${BATCH_PRS[*]}"
echo "🤖 Running batchcopilot on PRs: $PR_LIST"

# Run batchcopilot with unprocessed PRs
cd ~/projects/worldarchitect.ai
if claude --dangerously-skip-permissions "/batchcopilot --prs $PR_LIST"; then
    # Mark PRs as processed with timestamp
    TIMESTAMP=$(date +%s)
    for PR in "${BATCH_PRS[@]}"; do
        # Remove old entry for this PR and add new one
        grep -v "^$PR:" "$PROCESSED_FILE" > "${PROCESSED_FILE}.tmp" 2>/dev/null || true
        echo "$PR:$TIMESTAMP" >> "${PROCESSED_FILE}.tmp"
        mv "${PROCESSED_FILE}.tmp" "$PROCESSED_FILE"
    done
    log "✅ Successfully processed PRs: ${BATCH_PRS[*]}"
else
    log "❌ Batch processing failed for PRs: ${BATCH_PRS[*]}"
    exit 1
fi

log "🏁 Simple PR batch processing complete"
