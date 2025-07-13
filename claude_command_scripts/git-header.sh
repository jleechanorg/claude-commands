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

# Find the script's actual location relative to git root
script_dir="$git_root"
if [ -d "$git_root/claude_command_scripts" ]; then
    script_dir="$git_root"
elif [ -d "$git_root/worktree_roadmap/claude_command_scripts" ]; then
    script_dir="$git_root/worktree_roadmap"
else
    # Search for the script in any subdirectory
    found_script=$(find "$git_root" -name "git-header.sh" -type f 2>/dev/null | head -1)
    if [ -n "$found_script" ]; then
        script_dir=$(dirname "$(dirname "$found_script")")
    fi
fi

# Change to the directory containing claude_command_scripts
cd "$script_dir" || cd "$git_root" || exit 1

local_branch=$(git branch --show-current)
remote=$(git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream")

# Get local changes status
modified_count=$(git status --porcelain | grep -E "^ M|^MM|^AM" | wc -l)
staged_count=$(git status --porcelain | grep -E "^M |^A |^D |^R |^C " | wc -l)
untracked_count=$(git status --porcelain | grep "^??" | wc -l)

# Build local status string
local_status=""
if [ "$modified_count" -gt 0 ] || [ "$staged_count" -gt 0 ] || [ "$untracked_count" -gt 0 ]; then
    status_parts=()
    [ "$staged_count" -gt 0 ] && status_parts+=("${staged_count}S")
    [ "$modified_count" -gt 0 ] && status_parts+=("${modified_count}M")
    [ "$untracked_count" -gt 0 ] && status_parts+=("${untracked_count}U")
    local_status=" ($(IFS=, ; echo "${status_parts[*]}"))"
else
    local_status=" (clean)"
fi

# Get unpushed commits count
unpushed_count=0
if [ "$remote" != "no upstream" ]; then
    unpushed_count=$(git rev-list --count HEAD..."$remote" 2>/dev/null || echo "0")
    if [ "$unpushed_count" -gt 0 ]; then
        remote="$remote (+$unpushed_count)"
    fi
fi

# Try to find PR for current branch first
pr_info=$(gh pr list --head "$local_branch" --json number,url 2>/dev/null || echo "[]")

# If no PR found for current branch, try to find related PRs
if [ "$pr_info" = "[]" ]; then
    # Look for PRs that might be related to commits from this branch
    # Get recent commits and search for PRs containing those commits
    recent_commits=$(git log --format="%H" -10 2>/dev/null || echo "")
    if [ -n "$recent_commits" ]; then
        # Search all open PRs for any that might contain our commits
        all_prs=$(gh pr list --state open --json number,url,headRefName 2>/dev/null || echo "[]")
        if [ "$all_prs" != "[]" ]; then
            # Look for PRs where we might have pushed commits
            for commit in $recent_commits; do
                for pr_branch in $(echo "$all_prs" | jq -r '.[].headRefName' 2>/dev/null); do
                    if git merge-base --is-ancestor "$commit" "origin/$pr_branch" 2>/dev/null; then
                        pr_info=$(echo "$all_prs" | jq "[.[] | select(.headRefName == \"$pr_branch\")]" 2>/dev/null)
                        break 2
                    fi
                done
            done
        fi
    fi
fi

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

# Function to format timestamp
format_time() {
    local timestamp="$1"
    if [ -n "$timestamp" ]; then
        date -d "$timestamp" '+%H:%M:%S'
    fi
}

# Function to show balloon notification
show_balloon() {
    local title="$1"
    local message="$2"
    powershell.exe -Command "
Add-Type -AssemblyName System.Windows.Forms
\$balloon = New-Object System.Windows.Forms.NotifyIcon
\$balloon.Icon = [System.Drawing.SystemIcons]::Warning
\$balloon.BalloonTipTitle = '$title'
\$balloon.BalloonTipText = '$message'
\$balloon.Visible = \$true
\$balloon.ShowBalloonTip(5000)
Start-Sleep -Seconds 1
\$balloon.Dispose()
" >/dev/null 2>&1 &
}

# Function to show popup alert
show_popup() {
    local message="$1"
    powershell.exe -Command "[System.Windows.Forms.MessageBox]::Show('$message', 'Claude API Critical Alert', 'OK', 'Warning')" >/dev/null 2>&1 &
}

# Get Claude API rate limit info if requested
if [ "$1" = "--with-api" ] || [ "$1" = "--monitor" ]; then
    response=$(curl -s -D /tmp/claude_headers.tmp https://api.anthropic.com/v1/messages \
      --header "x-api-key: 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" \
      --header "anthropic-version: 2023-06-01" \
      --header "content-type: application/json" \
      --data '{
        "model": "claude-opus-4-20250514",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "ping"}]
      }' 2>/dev/null)
    
    if [ -f /tmp/claude_headers.tmp ]; then
        requests_reset=$(grep -i 'anthropic-ratelimit-requests-reset:' /tmp/claude_headers.tmp | cut -d' ' -f2- | tr -d '\r')
        requests_remaining=$(grep -i 'anthropic-ratelimit-requests-remaining:' /tmp/claude_headers.tmp | cut -d' ' -f2- | tr -d '\r')
        requests_limit=$(grep -i 'anthropic-ratelimit-requests-limit:' /tmp/claude_headers.tmp | cut -d' ' -f2- | tr -d '\r')
        
        # Calculate usage percentage
        if [ -n "$requests_remaining" ] && [ -n "$requests_limit" ]; then
            requests_used=$((requests_limit - requests_remaining))
            usage_percent=$((requests_used * 100 / requests_limit))
            remaining_percent=$((requests_remaining * 100 / requests_limit))
            
            # Show alerts based on remaining percentage
            if [ "$1" = "--monitor" ] && [ "$remaining_percent" -le 25 ]; then
                show_popup "CRITICAL: Only $remaining_percent% API quota remaining ($requests_remaining/$requests_limit requests)"
            elif [ "$1" = "--monitor" ] && [ "$remaining_percent" -le 50 ]; then
                show_balloon "Claude API Alert" "Warning: Only $remaining_percent% quota remaining ($requests_remaining/$requests_limit)"
            elif [ "$1" = "--monitor" ] && [ "$remaining_percent" -le 75 ]; then
                show_balloon "Claude API Notice" "Info: $remaining_percent% quota remaining ($requests_remaining/$requests_limit)"
            fi
        fi
        
        echo "[Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]"
        echo "[API: ${requests_remaining:-?}/${requests_limit:-50} requests (${remaining_percent:-?}% remaining) | Reset: $(format_time "$requests_reset")]"
        
        rm -f /tmp/claude_headers.tmp
    else
        echo "[Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]"
        echo "[API: Error getting rate limits]"
    fi
else
    echo "[Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]"
fi