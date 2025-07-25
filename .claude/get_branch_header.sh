#!/bin/bash
# Get branch header for CLAUDE.md compliance
# Used by Claude hooks to generate consistent branch information

branch=$(git branch --show-current 2>/dev/null || echo "unknown")
upstream=$(git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream")
pr_data=$(gh pr list --head "$branch" --json number,url 2>/dev/null)

if [ -n "$pr_data" ] && [ "$pr_data" != "[]" ]; then
    pr=$(echo "$pr_data" | grep -o "\"number\":[0-9]*" | cut -d: -f2 | head -1)
    url=$(echo "$pr_data" | grep -o "\"url\":\"[^\"]*\"" | cut -d\" -f4 | head -1)
    if [ -n "$pr" ]; then
        pr="#$pr $url"
    else
        pr="none"
    fi
else
    pr="none"
fi

echo "[Local: $branch | Remote: $upstream | PR: $pr]"