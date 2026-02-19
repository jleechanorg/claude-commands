#!/bin/bash
# Simple cleanup script for completed agent worktrees and old results

set -e

echo "🧹 Orchestration Agent Cleanup Script"
echo "====================================="

# Configuration
RESULT_DIR="/tmp/orchestration_results"
MAX_AGE_HOURS=24

# Function to check if worktree is safe to remove
is_worktree_safe_to_remove() {
    local worktree_path="$1"
    local branch_name=$(git -C "$worktree_path" branch --show-current 2>/dev/null || echo "")

    # Check if PR exists and is merged
    if [ -n "$branch_name" ]; then
        pr_state=$(gh pr view "$branch_name" --json state -q .state 2>/dev/null || echo "")
        if [ "$pr_state" = "MERGED" ]; then
            return 0  # Safe to remove
        fi
    fi

    # Check if .done file exists (agent completed)
    if [ -f "$RESULT_DIR/${worktree_path##*/}_results.json.done" ]; then
        return 0  # Safe to remove
    fi

    return 1  # Not safe
}

# Clean up agent worktrees
echo "🔍 Checking agent worktrees..."
for worktree in agent_workspace_*; do
    if [ -d "$worktree" ]; then
        if is_worktree_safe_to_remove "$worktree"; then
            echo "  ✅ Removing completed worktree: $worktree"
            git worktree remove "$worktree" --force 2>/dev/null || rm -rf "$worktree"
        else
            echo "  ⏳ Keeping active worktree: $worktree"
        fi
    fi
done

# Clean up old result files
echo ""
echo "🔍 Checking result files..."
if [ -d "$RESULT_DIR" ]; then
    find "$RESULT_DIR" -type f -name "*.json*" -mtime +1 -exec rm -v {} \; | sed 's/^/  ✅ /'
fi

# Clean up orphaned tmux sessions
echo ""
echo "🔍 Checking tmux sessions..."
for session in $(tmux ls 2>/dev/null | grep -E '^(dev|security|test|script|agent)-' | cut -d: -f1); do
    # Check if corresponding worktree exists
    worktree="agent_workspace_${session}"
    if [ ! -d "$worktree" ]; then
        echo "  ✅ Killing orphaned session: $session"
        tmux kill-session -t "$session" 2>/dev/null || true
    fi
done

# Summary
echo ""
echo "✨ Cleanup complete!"
echo ""
echo "Active agents:"
tmux ls 2>/dev/null | grep -E '^(dev|security|test|script|agent)-' | sed 's/^/  - /' || echo "  None"
