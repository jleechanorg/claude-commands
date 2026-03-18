#!/usr/bin/env bash
# Codex Git Header Hook - Mirrors Claude Code git-header.sh status output
# This script provides git status information for Codex sessions
# Usage: Run manually or integrate via Codex automation

# Find the git directory
git_dir=$(git rev-parse --git-dir 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Not in a git repository]"
    exit 0
fi

# Get git root
git_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Unable to find git root]"
    exit 0
fi

cd "$git_root" || exit 1

working_dir="$(basename "$git_root")"
local_branch=$(git branch --show-current 2>/dev/null || echo "HEAD")
remote=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "no upstream")

# Get repo info
get_repo_from_remote() {
    local url
    parse_repo_from_url() {
        local parsed_url="$1"
        if [[ "$parsed_url" =~ https?://([^@/]+@)?([^/]+)/([^/]+)/([^/]+)(\.git)?/?$ ]]; then
            local domain="${BASH_REMATCH[2]}"
            local owner="${BASH_REMATCH[3]}"
            local repo="${BASH_REMATCH[4]}"
            repo="${repo%.git}"
            echo "${domain}/${owner}/${repo}"
            return 0
        fi
        if [[ "$parsed_url" =~ git@([^:]+):([^/]+)/([^/]+)(\.git)?/?$ ]]; then
            local domain="${BASH_REMATCH[1]}"
            local owner="${BASH_REMATCH[2]}"
            local repo="${BASH_REMATCH[3]}"
            repo="${repo%.git}"
            echo "${domain}/${owner}/${repo}"
            return 0
        fi
        return 1
    }
    if url=$(git remote get-url upstream 2>/dev/null); then
        parse_repo_from_url "$url" && return 0
    fi
    local remote_count
    remote_count=$(git remote 2>/dev/null | wc -l | tr -d '[:space:]')
    if [ "$remote_count" = "1" ]; then
        local remote_name
        remote_name=$(git remote 2>/dev/null | head -n 1)
        if [ -n "$remote_name" ] && url=$(git remote get-url "$remote_name" 2>/dev/null); then
            parse_repo_from_url "$url" && return 0
        fi
    fi
    return 1
}

repo_name=$(get_repo_from_remote)

# Check for uncommitted changes
if git diff-index --quiet HEAD -- 2>/dev/null; then
    uncommitted=""
else
    uncommitted=" +uncommitted"
fi

# Get sync status
if [ "$remote" != "no upstream" ]; then
    ahead_count=$(git rev-list --count "$remote"..HEAD 2>/dev/null || echo "0")
    behind_count=$(git rev-list --count HEAD.."$remote" 2>/dev/null || echo "0")

    if [ "$ahead_count" -eq 0 ] && [ "$behind_count" -eq 0 ]; then
        local_status=" (synced$uncommitted)"
    elif [ "$ahead_count" -gt 0 ] && [ "$behind_count" -eq 0 ]; then
        local_status=" (ahead $ahead_count$uncommitted)"
    elif [ "$ahead_count" -eq 0 ] && [ "$behind_count" -gt 0 ]; then
        local_status=" (behind $behind_count$uncommitted)"
    else
        local_status=" (diverged +$ahead_count -$behind_count$uncommitted)"
    fi
else
    local_status=" (no remote$uncommitted)"
fi

# Find PR number
pr_text="none"
if command -v gh >/dev/null 2>&1 && [ -n "$local_branch" ]; then
    if [ -n "$repo_name" ]; then
        pr_info=$(gh pr view --repo "$repo_name" --json number,url --template '{{.number}} {{.url}}' "$local_branch" 2>/dev/null)
    else
        pr_info=$(gh pr view --json number,url --template '{{.number}} {{.url}}' "$local_branch" 2>/dev/null)
    fi
    if [ -n "$pr_info" ]; then
        pr_number="${pr_info%% *}"
        pr_url="${pr_info#* }"
        if [ "$pr_number" != "$pr_url" ] && [ -n "$pr_number" ]; then
            pr_text="#$pr_number"
        fi
    fi
fi

# Output header
short_remote=$(echo "$remote" | sed 's|origin/||;s|upstream/||')
echo "[Dir: $working_dir | Local: $local_branch$local_status | Remote: $short_remote | PR: $pr_text]"
