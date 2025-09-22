#!/bin/bash

# Slack notification script for Claude Code hooks
# Usage: ./slack_notify.sh "message"

set -euo pipefail

# Default message if none provided
MESSAGE="${1:-"🤖 Claude Code: Task completed - awaiting next instruction"}"

# Check if SLACK_WEBHOOK_URL is set
if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
    echo "⚠️  SLACK_WEBHOOK_URL environment variable not set. Skipping notification."
    exit 0
fi

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
    echo "⚠️  jq not found; skipping Slack notification"
    exit 0
fi

# Get current branch and timestamp
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
    REPO=$(basename "$(git rev-parse --show-toplevel)")

    # Get remote info
    REMOTE=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/\.git$//' || echo "N/A")

    # Get PR info if available
    PR_INFO="N/A"
    if command -v gh >/dev/null 2>&1; then
        PR_NUMBER=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "")
        if [ -n "$PR_NUMBER" ]; then
            PR_URL=$(gh pr view --json url --jq '.url' 2>/dev/null || echo "")
            if [ -n "$PR_URL" ]; then
                PR_INFO="$PR_NUMBER $PR_URL"
            fi
        fi
    fi
else
    BRANCH="N/A"
    REPO=$(basename "$(pwd)")
    REMOTE="N/A"
    PR_INFO="N/A"
fi

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Construct full message with simplified worktree:branch format
# Truncate branch to first 8 characters for readability
BRANCH_SHORT=$(echo "$BRANCH" | cut -c1-8)
FULL_MESSAGE="[$REPO:$BRANCH_SHORT...]
$MESSAGE
⏰ $TIMESTAMP"

# Send notification to Slack
echo "📤 Sending Slack notification..."
curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":$(printf '%s' "$FULL_MESSAGE" | jq -Rs .)}" \
    --silent --show-error --fail-with-body \
    "$SLACK_WEBHOOK_URL" || {
    echo "❌ Failed to send Slack notification"
    exit 1
}

echo "✅ Slack notification sent successfully"
