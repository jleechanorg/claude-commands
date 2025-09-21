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
else
    BRANCH="N/A"
    REPO=$(basename "$(pwd)")
fi

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Construct full message with context
FULL_MESSAGE="$MESSAGE

📁 Repository: $REPO
🌿 Branch: $BRANCH
⏰ Time: $TIMESTAMP"

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
