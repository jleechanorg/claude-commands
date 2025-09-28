#!/bin/bash
# post_commit_sync.sh - Post-Tool-Use Sync and PR Push Hook
#
# Purpose: Automatically run sync check, add automation prefix, and push to PR after git commit operations
#
# Integration: Add to .claude/settings.json hooks section for PostToolUse events with git commit matcher
#
# Features:
#   - Triggers automatically after successful commits
#   - Adds [AI automation] prefix to commit messages in automation context
#   - Uses portable project root detection
#   - Integrates with existing sync_check system
#   - Automatically pushes to PR if in automation context
#   - Respects user's git workflow preferences

set -euo pipefail

# AUTOMATION DISABLED FLAG - Check immediately before any git operations
AUTOMATION_DISABLED=${AUTOMATION_DISABLED:-0}

if [[ "$AUTOMATION_DISABLED" == "1" ]]; then
    echo "🚫 Automation is disabled - skipping post-commit sync"
    exit 0
fi

# Auto-detect project root (works from any directory) - only after disable check
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [[ -z "$PROJECT_ROOT" ]]; then
    echo "⚠️  Not in a git repository - skipping post-commit sync check" >&2
    exit 0
fi

# Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# Source shared automation context logic when available
AUTOMATION_HELPER="$(dirname "$0")/lib/automation.sh"
if [[ -r "$AUTOMATION_HELPER" ]]; then
    # shellcheck source=/dev/null
    source "$AUTOMATION_HELPER"
else
    echo "ℹ️  Automation helper not found at $AUTOMATION_HELPER - using fallback context detection" >&2
    is_automation_context() {
        [[ "${AUTOMATION_CONTEXT:-}" == "1" ]]
    }
fi

# Function to add automation prefix to the last commit if needed
add_automation_prefix_if_needed() {
    # Check if this is an automation context
    if ! is_automation_context; then
        return 0
    fi

    # Get the last commit message
    local last_msg
    last_msg=$(git log -1 --pretty=format:'%s')

    # Skip if message already has [AI automation] prefix
    if [[ "$last_msg" =~ ^\[AI\ automation\] ]]; then
        echo "✅ Commit message already has [AI automation] prefix"
        return 0
    fi

    # Skip if this is a merge commit
    if [[ $(git cat-file -p HEAD | grep '^parent ' | wc -l) -gt 1 ]]; then
        echo "ℹ️  Merge commit detected - skipping automation prefix"
        return 0
    fi

    # Add [AI automation] prefix using git commit --amend (safe from injection)
    local new_msg="[AI automation] $last_msg"
    # --no-verify is used here intentionally in automation context to avoid recursive hook invocation
    # and redundant validation, since this script is triggered by a commit hook itself.
    if git commit --amend --no-verify --file=- >/dev/null 2>&1 <<< "$new_msg"; then
        echo "✅ Added [AI automation] prefix to commit message"
    else
        echo "❌ Failed to add automation prefix - aborting automation to maintain consistency"
        return 1
    fi
}

# Check if sync_check exists
SYNC_SCRIPT="$PROJECT_ROOT/scripts/sync_check.sh"
if [[ ! -f "$SYNC_SCRIPT" ]]; then
    echo "⚠️  Sync check script not found at $SYNC_SCRIPT - skipping" >&2
    exit 0
fi

echo ""
echo "🔄 Post-Tool-Use Hook: Processing commit..."
echo "============================================"

# First, add automation prefix if this is an automation context
add_automation_prefix_if_needed

echo "🔄 Running sync check..."
echo "============================================"

# Execute sync check
if "$SYNC_SCRIPT"; then
    echo "✅ Post-commit sync check completed successfully"

    # If this is an automation context, automatically push to PR
    if is_automation_context; then
        echo "🤖 Detected automation context - pushing to PR..."

        # Push to origin with force-with-lease protection (safe after amend)
        if git push --force-with-lease origin HEAD 2>/dev/null; then
            echo "✅ Successfully pushed automation commit to PR"
        else
            echo "⚠️  Failed to push to PR - you may need to push manually"
            echo "    (Possible conflict with remote changes - manual intervention needed)"
        fi
    else
        echo "ℹ️  Not automation context - manual push may be needed"
    fi
else
    echo "⚠️  Post-commit sync check encountered issues"
    echo "💡 You may need to manually push changes: git push"
fi

echo ""
