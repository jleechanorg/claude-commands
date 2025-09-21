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

# Function to format timestamp (cross-platform compatible)
format_time() {
    local timestamp="$1"
    if [ -n "$timestamp" ]; then
        # Check if we have GNU date (Linux) or BSD date (macOS)
        if date --version >/dev/null 2>&1; then
            # GNU date (Linux) - supports -d flag
            date -d "$timestamp" '+%H:%M:%S' 2>/dev/null || echo "??:??:??"
        else
            # BSD date (macOS) - use -j flag with different format
            # Handle different timestamp formats that might come from HTTP headers
            case "$timestamp" in
                *T*Z|*T*+*|*T*-*)
                    # ISO 8601 format (e.g., "2024-01-15T14:30:00Z" or with timezone)
                    local converted_timestamp
                    converted_timestamp=$(echo "$timestamp" | sed 's/T/ /' | sed 's/Z$//' | sed 's/\+.*$//' | sed 's/-[0-9][0-9]:*[0-9][0-9]$//')
                    date -j -f "%Y-%m-%d %H:%M:%S" "$converted_timestamp" '+%H:%M:%S' 2>/dev/null || echo "??:??:??"
                    ;;
                *[0-9][0-9]:[0-9][0-9]:[0-9][0-9]*)
                    # Already has time format - try various date formats
                    date -j -f "%Y-%m-%d %H:%M:%S" "$timestamp" '+%H:%M:%S' 2>/dev/null || \
                    date -j -f "%m/%d/%Y %H:%M:%S" "$timestamp" '+%H:%M:%S' 2>/dev/null || \
                    date -j -f "%d/%m/%Y %H:%M:%S" "$timestamp" '+%H:%M:%S' 2>/dev/null || \
                    echo "??:??:??"
                    ;;
                *[0-9]*)
                    # Unix timestamp or other numeric format
                    if [ ${#timestamp} -eq 10 ] && [ "$timestamp" -eq "$timestamp" ] 2>/dev/null; then
                        # Unix timestamp (10 digits)
                        date -r "$timestamp" '+%H:%M:%S' 2>/dev/null || echo "??:??:??"
                    else
                        # Try as regular date
                        date -j -f "%Y-%m-%d" "$timestamp" '+%H:%M:%S' 2>/dev/null || echo "??:??:??"
                    fi
                    ;;
                *)
                    # Fallback to simple format attempts
                    echo "??:??:??"
                    ;;
            esac
        fi
    fi
}

# Function to parse Claude Code transcript and get token metrics
# Based on ccstatusline token parsing logic
get_token_metrics() {
    local transcript_path="$1"

    # Initialize variables
    local input_tokens=0
    local output_tokens=0
    local cached_tokens=0
    local context_length=0
    local most_recent_timestamp=""
    local most_recent_usage=""

    # Check if transcript file exists
    if [ ! -f "$transcript_path" ]; then
        echo "0,0,0,0"
        return
    fi

    # Parse JSONL file line by line
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines
        [ -z "$line" ] && continue

        # Extract token usage from JSON (using grep and sed for bash compatibility)
        local line_input_tokens line_output_tokens line_cache_read line_cache_creation line_timestamp line_sidechain

        # Extract usage data using grep and sed
        line_input_tokens=$(echo "$line" | grep -o '"input_tokens":[0-9]*' | sed 's/"input_tokens"://' || echo "0")
        line_output_tokens=$(echo "$line" | grep -o '"output_tokens":[0-9]*' | sed 's/"output_tokens"://' || echo "0")
        line_cache_read=$(echo "$line" | grep -o '"cache_read_input_tokens":[0-9]*' | sed 's/"cache_read_input_tokens"://' || echo "0")
        line_cache_creation=$(echo "$line" | grep -o '"cache_creation_input_tokens":[0-9]*' | sed 's/"cache_creation_input_tokens"://' || echo "0")
        line_timestamp=$(echo "$line" | grep -o '"timestamp":"[^"]*"' | sed 's/"timestamp":"//; s/"//' || echo "")
        line_sidechain=$(echo "$line" | grep -o '"isSidechain":true' || echo "")

        # Only process lines with usage data
        if [ -n "$line_input_tokens" ] && [ "$line_input_tokens" != "0" ] || [ -n "$line_output_tokens" ] && [ "$line_output_tokens" != "0" ]; then
            # Add to totals
            input_tokens=$((input_tokens + ${line_input_tokens:-0}))
            output_tokens=$((output_tokens + ${line_output_tokens:-0}))
            cached_tokens=$((cached_tokens + ${line_cache_read:-0} + ${line_cache_creation:-0}))

            # Track most recent main chain entry (not sidechain and has timestamp)
            if [ -z "$line_sidechain" ] && [ -n "$line_timestamp" ]; then
                # Simple timestamp comparison (assuming ISO format)
                if [ -z "$most_recent_timestamp" ] || [ "$line_timestamp" \> "$most_recent_timestamp" ]; then
                    most_recent_timestamp="$line_timestamp"
                    most_recent_usage="$line_input_tokens,${line_cache_read:-0},${line_cache_creation:-0}"
                fi
            fi
        fi
    done < "$transcript_path"

    # Calculate context length from most recent main chain entry
    if [ -n "$most_recent_usage" ]; then
        local recent_input recent_cache_read recent_cache_creation
        recent_input=$(echo "$most_recent_usage" | cut -d',' -f1)
        recent_cache_read=$(echo "$most_recent_usage" | cut -d',' -f2)
        recent_cache_creation=$(echo "$most_recent_usage" | cut -d',' -f3)
        context_length=$((${recent_input:-0} + ${recent_cache_read:-0} + ${recent_cache_creation:-0}))
    fi

    local total_tokens=$((input_tokens + output_tokens + cached_tokens))

    # Return comma-separated values: input,output,cached,total,context
    echo "$input_tokens,$output_tokens,$cached_tokens,$total_tokens,$context_length"
}

# Function to format token count (similar to ccstatusline's formatTokens)
format_tokens() {
    local tokens="$1"
    if [ "$tokens" -ge 1000000 ]; then
        # Round to 1 decimal place for millions
        local millions=$((tokens / 1000000))
        local decimal=$(((tokens % 1000000 + 50000) / 100000))
        if [ "$decimal" -eq 10 ]; then
            millions=$((millions + 1))
            decimal=0
        fi
        echo "${millions}.${decimal}M"
    elif [ "$tokens" -ge 1000 ]; then
        # Round to 1 decimal place for thousands, check for rollover to millions
        local thousands=$((tokens / 1000))
        local decimal=$(((tokens % 1000 + 50) / 100))
        if [ "$decimal" -eq 10 ]; then
            thousands=$((thousands + 1))
            decimal=0
        fi
        # Check if we've rolled over to 1000k (should be 1.0M)
        if [ "$thousands" -eq 1000 ] && [ "$decimal" -eq 0 ]; then
            echo "1.0M"
        else
            echo "${thousands}.${decimal}k"
        fi
    else
        echo "$tokens"
    fi
}

# Check for bashrc alias setup
check_bashrc_alias() {
    local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
    local script_path="$git_root/.claude/hooks/git-header.sh"

    # Check if alias exists in bashrc
    if ! grep -q "alias.*git-header" ~/.bashrc 2>/dev/null; then
        echo "⚠️  WARNING: git-header alias not found in ~/.bashrc"
        echo "   Add this line to your ~/.bashrc for reliable access:"
        echo "   alias git-header='bash $script_path'"
        echo "   Then run: source ~/.bashrc"
        echo ""
    fi
}

# Check for --status-only flag to skip git status and context info
if [ "$1" = "--status-only" ]; then
    status_only=true
else
    status_only=false
    # Run bashrc check on every execution
    check_bashrc_alias

    # Always show git status first for complete context
    echo "=== Git Status ==="
    git status
    echo
fi

# Function to find Claude Code transcript file
find_transcript_file() {
    # Look for most recent transcript file in .claude/projects
    local claude_dir=~/.claude/projects
    if [ -d "$claude_dir" ]; then
        # Find most recent .jsonl file, portable across macOS and Linux
        case "$(uname)" in
            Darwin)
                # macOS/BSD: stat -f
                find "$claude_dir" -name "*.jsonl" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-
                ;;
            Linux)
                # Linux: stat -c
                find "$claude_dir" -name "*.jsonl" -type f -exec stat -c "%Y %n" {} \; 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-
                ;;
            *)
                # Fallback: try find -printf (GNU find)
                find "$claude_dir" -name "*.jsonl" -type f -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-
                ;;
        esac
    fi
}

# Function to show context information (now always displayed)
show_context_info() {
    # Try to find and parse Claude Code transcript
    transcript_file=$(find_transcript_file)
    if [ -n "$transcript_file" ] && [ -f "$transcript_file" ]; then
        metrics=$(get_token_metrics "$transcript_file")
        IFS=',' read -r input_tokens output_tokens cached_tokens total_tokens context_length <<< "$metrics"

        # Calculate context percentage (using ccstatusline's 200k limit for compatibility)
        if [ "$context_length" -gt 0 ]; then
            # Add system overhead offset to match Claude Code's /context command
            # System overhead includes: system prompt, tools, memory files, etc.
            # Calibrated to match /context command output (103k total - 96k session = 7k overhead)
            system_overhead=7000
            adjusted_context=$((context_length + system_overhead))

            context_percent_used=$(( (adjusted_context * 100) / 160000 ))
            echo -e "\033[1;33m[Context: ${context_percent_used}% tokens used]\033[0m"
        else
            echo -e "\033[1;31m[Context: No active session found]\033[0m"
        fi
    else
        echo -e "\033[1;31m[Context: No transcript file found]\033[0m"
    fi
}

# Maintain compatibility when legacy flags are provided but omit API usage stats
if [ "$1" = "--with-api" ] || [ "$1" = "--monitor" ]; then
    echo -e "\033[1;36m[Dir: $working_dir | Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]\033[0m"
    show_context_info
elif [ "$status_only" = true ]; then
    # Only output the header lines for statusLine - no git status or other output
    echo -e "\033[1;36m[Dir: $working_dir | Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]\033[0m"
    show_context_info
else
    # Full output for normal usage
    echo -e "\033[1;36m[Dir: $working_dir | Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]\033[0m"
    show_context_info
fi
