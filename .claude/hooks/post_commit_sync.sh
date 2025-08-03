#!/bin/bash
# post_commit_sync.sh - Post-Commit Sync Check Hook
#
# Purpose: Automatically run sync check after commits to ensure changes are pushed
#
# Integration: Add to .claude/settings.json hooks section for PostCommit events
#
# Features:
#   - Triggers automatically after successful commits
#   - Uses portable project root detection
#   - Integrates with existing sync_check system
#   - Respects user's git workflow preferences

set -euo pipefail

# Auto-detect project root (works from any directory)
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [[ -z "$PROJECT_ROOT" ]]; then
    echo "⚠️  Not in a git repository - skipping post-commit sync check" >&2
    exit 0
fi

# Check if sync_check exists
SYNC_SCRIPT="$PROJECT_ROOT/scripts/sync_check.sh"
if [[ ! -f "$SYNC_SCRIPT" ]]; then
    echo "⚠️  Sync check script not found at $SYNC_SCRIPT - skipping" >&2
    exit 0
fi

echo ""
echo "🔄 Post-Commit Hook: Running sync check..."
echo "============================================"

# Execute sync check
if "$SYNC_SCRIPT"; then
    echo "✅ Post-commit sync check completed successfully"
else
    echo "⚠️  Post-commit sync check encountered issues"
    echo "💡 You may need to manually push changes: git push"
fi

echo ""
