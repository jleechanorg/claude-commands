#!/usr/bin/env bash
# Git header generator script (ENHANCED VERSION WITH GIT STATUS)
# Usage: ./git-header.sh or git header (if aliased)
# Works from any directory within a git repository or worktree

# Find the git directory (works in worktrees and submodules)
git_dir=$(git rev-parse --git-dir 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Not in a git repository]"
    exit 0
fi

# Get the root of the working tree
git_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Unable to find git root]"
    exit 0
fi

# Find the git root and change to it
script_dir="$git_root"
cd "$git_root" || { echo "[Unable to change to git root]"; exit 0; }

# Get working directory for context
working_dir="$(basename "$git_root")"

local_branch=$(git branch --show-current)
remote=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "no upstream")

# Get sync status and unpushed changes
local_status=""

# Check for uncommitted changes (always check, regardless of remote)
# Check both modified tracked files AND untracked files
if ! git diff-index --quiet HEAD -- 2>/dev/null || [ -n "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
    uncommitted=" +uncommitted"
else
    uncommitted=""
fi

if [ "$remote" != "no upstream" ]; then
    # Count commits ahead and behind
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

# Smart PR detection with fast-first fallback strategy
# 1. Branch name patterns (instant)
# 2. Cached network lookup (fast)
# 3. Real-time network lookup with timeout (fallback)

# Fast detection from branch naming patterns
pr_text="none"
if [[ "$local_branch" =~ pr-([0-9]+) ]]; then
    pr_text="#${BASH_REMATCH[1]} (inferred)"
elif [[ "$local_branch" =~ /pr-([0-9]+) ]]; then
    pr_text="#${BASH_REMATCH[1]} (inferred)"
else
    # Always try network lookup with fast timeout for PR detection
    current_commit=$(git rev-parse HEAD 2>/dev/null)
    if [ -n "$current_commit" ]; then
        pr_number=$(timeout 1 git ls-remote origin 'refs/pull/*/head' 2>/dev/null | \
                   grep "$current_commit" | \
                   sed 's/.*refs\/pull\/\([0-9]*\)\/head.*/\1/' | \
                   head -1 2>/dev/null)
        if [ -n "$pr_number" ]; then
            pr_text="#$pr_number"
        fi
    fi
fi





# Skip git status output for statusline mode
if [ "$1" != "--status-only" ]; then
    echo "=== Git Status ==="
    git status
    echo
fi



# Simple output - just the essential info
echo -e "\033[1;36m[Dir: $working_dir | Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]\033[0m"
