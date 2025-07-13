#!/bin/bash
# Git header generator script
# Usage: ./git-header.sh or git header (if aliased)

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

echo "[Hook: $local_branch | Remote: $remote | PR: $pr_text]"