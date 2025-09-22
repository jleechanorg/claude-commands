#!/bin/bash

# Test script for Slack notification setup
# Usage: ./test_slack_notification.sh

set -euo pipefail

echo "🧪 Testing Slack notification setup..."

# Check if SLACK_WEBHOOK_URL is set
if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
    echo "❌ SLACK_WEBHOOK_URL environment variable not set"
    echo "📖 Please see scripts/slack_setup_guide.md for setup instructions"
    exit 1
fi

echo "✅ SLACK_WEBHOOK_URL is configured"

# Get repository root and check if slack_notify.sh exists and is executable
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)
if [ ! -x "$ROOT/scripts/slack_notify.sh" ]; then
    echo "❌ scripts/slack_notify.sh not found or not executable"
    echo "Run: chmod +x $ROOT/scripts/slack_notify.sh"
    exit 1
fi

echo "✅ scripts/slack_notify.sh is executable"

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "❌ jq command not found (required for JSON processing)"
    echo "Install with: brew install jq (macOS) or sudo apt install jq (Ubuntu)"
    exit 1
fi

echo "✅ jq is available for JSON processing"

# Test the webhook with a simple message
echo "🚀 Sending test notification..."
"$ROOT/scripts/slack_notify.sh" "🧪 Test notification from Claude Code setup verification"

echo ""
echo "✅ Test completed! Check your Slack channel for the notification."
echo "📖 For more information, see scripts/slack_setup_guide.md"
