#!/bin/bash
# Git header generator script
# Usage: ./git-header.sh or git header (if aliased)
# Works from any directory within a git repository or worktree

# Find the git directory (works in worktrees and submodules)
git_dir=$(git rev-parse --git-dir 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Not in a git repository]"
    exit 1
fi

# Get the root of the working tree
git_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Unable to find git root]"
    exit 1
fi

# Change to git root to ensure commands work properly
cd "$git_root" || exit 1

local_branch=$(git branch --show-current)
remote=$(git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream")
pr_info=$(gh pr list --head "$local_branch" --json number,url 2>/dev/null || echo "[]")

if [ "$pr_info" = "[]" ]; then
    pr_text="none"
else
    pr_num=$(echo "$pr_info" | jq -r ".[0].number // \"none\"" 2>/dev/null || echo "none")
    pr_url=$(echo "$pr_info" | jq -r ".[0].url // \"\"" 2>/dev/null || echo "")
    if [ "$pr_num" = "none" ] || [ "$pr_num" = "null" ]; then
        pr_text="none"
    else
        pr_text="#$pr_num"
        if [ -n "$pr_url" ]; then
            pr_text="$pr_text $pr_url"
        fi
    fi
fi

echo "[Local: $local_branch | Remote: $remote | PR: $pr_text]"