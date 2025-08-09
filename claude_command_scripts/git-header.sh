#!/usr/bin/env bash
# Git header generator script (ENHANCED VERSION WITH GIT STATUS)
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

# Get sync status between local and remote
local_status=""
if [ "$remote" != "no upstream" ]; then
    # Count commits ahead and behind
    ahead_count=$(git rev-list --count "$remote"..HEAD 2>/dev/null || echo "0")
    behind_count=$(git rev-list --count HEAD.."$remote" 2>/dev/null || echo "0")

    if [ "$ahead_count" -eq 0 ] && [ "$behind_count" -eq 0 ]; then
        local_status=" (synced)"
    elif [ "$ahead_count" -gt 0 ] && [ "$behind_count" -eq 0 ]; then
        local_status=" (ahead $ahead_count)"
    elif [ "$ahead_count" -eq 0 ] && [ "$behind_count" -gt 0 ]; then
        local_status=" (behind $behind_count)"
    else
        local_status=" (diverged +$ahead_count -$behind_count)"
    fi
else
    local_status=" (no remote)"
fi

# Get git status for PR inference
git_status_short=$(git status --short 2>/dev/null)

# Find PR for current branch first
pr_info=$(gh pr list --head "$local_branch" --json number,url 2>/dev/null || echo "[]")

# If no PR found for current branch, try to infer from git status and recent commits
if [ "$pr_info" = "[]" ]; then
    # Check if we have uncommitted changes that might be related to a PR
    if [ -n "$git_status_short" ]; then
        # Look for PRs that might be related to the current working directory state
        # Check for recent PRs that might match the work being done
        recent_prs=$(gh pr list --state open --limit 5 --json number,url 2>/dev/null || echo "[]")
        
        # If there are recent PRs, suggest the most recent open PR as context
        if [ "$(echo "$recent_prs" | jq "length" 2>/dev/null)" -gt 0 ] 2>/dev/null || [ "$recent_prs" != "[]" ]; then
            recent_pr_num=$(echo "$recent_prs" | jq -r ".[0].number // \"none\"" 2>/dev/null || echo "none")
            recent_pr_url=$(echo "$recent_prs" | jq -r ".[0].url // \"\"" 2>/dev/null || echo "")
            if [ "$recent_pr_num" != "none" ] && [ "$recent_pr_num" != "null" ]; then
                pr_text="(related to #$recent_pr_num $recent_pr_url)"
            else
                pr_text="none"
            fi
        else
            pr_text="none"
        fi
    else
        pr_text="none"
    fi
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
Add-Type -AssemblyName System.Windows.Forms;
\$balloon = New-Object System.Windows.Forms.NotifyIcon;
\$balloon.Icon = [System.Drawing.SystemIcons]::Warning;
\$balloon.BalloonTipTitle = \$('$title');
\$balloon.BalloonTipText = \$('$message');
\$balloon.Visible = \$true;
\$balloon.ShowBalloonTip(5000);
Start-Sleep -Seconds 1;
\$balloon.Dispose()
" >/dev/null 2>&1 &
}

# Function to show popup alert
show_popup() {
    local message="$1"
    powershell.exe -Command "[System.Windows.Forms.MessageBox]::Show(\$('$message'), \$('Claude API Critical Alert'), \$('OK'), \$('Warning'))" >/dev/null 2>&1 &
}

# Check for bashrc alias setup
check_bashrc_alias() {
    local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
    local script_path="$git_root/claude_command_scripts/git-header.sh"

    # Check if alias exists in bashrc
    if ! grep -q "alias.*git-header" ~/.bashrc 2>/dev/null; then
        echo "⚠️  WARNING: git-header alias not found in ~/.bashrc"
        echo "   Add this line to your ~/.bashrc for reliable access:"
        echo "   alias git-header='bash $script_path'"
        echo "   Then run: source ~/.bashrc"
        echo ""
    fi
}

# Run bashrc check on every execution
check_bashrc_alias

# Always show git status first for complete context
echo "=== Git Status ==="
git status
echo

# Get Claude API rate limit info if requested
if [ "$1" = "--with-api" ] || [ "$1" = "--monitor" ]; then
    # Check for API key in environment
    if [ -z "$CLAUDE_API_KEY" ]; then
        echo "[Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]"
        echo "[API: Error - CLAUDE_API_KEY environment variable not set]"
        exit 0
    fi

    response=$(curl -s -D /tmp/claude_headers.tmp https://api.anthropic.com/v1/messages \
      --header "x-api-key: $CLAUDE_API_KEY" \
      --header "anthropic-version: 2023-06-01" \
      --header "content-type: application/json" \
      --data '{
        "model": "claude-3-opus-20240229",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "test"}]
      }' 2>/dev/null)

    # Check for authentication errors
    if echo "$response" | grep -q "authentication_error"; then
        echo "[Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]"
        echo "[API: Authentication failed - Get valid API key from console.anthropic.com]"
        rm -f /tmp/claude_headers.tmp
        exit 0
    fi

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
