#!/bin/bash
# Universal Command Composition Hook for Claude Code
# Multi-Player Intelligent Command Combination System
# Leverages Claude's natural language processing + nested command parsing for true universality

# Source timeout utilities for safe_read_stdin function
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/timeout-utils.sh"

# Read input from stdin (can be JSON or plain text)
# Handle both interactive and non-interactive modes without hanging
# CRITICAL: For claude -p mode, we need to handle the case where stdin may be provided
# but the parent process context is different
# FIXED: Use cross-platform safe_read_stdin function instead of timeout + cat,
#        while honoring CLI-provided fallbacks to avoid TTY hangs
# Prefer explicit inputs before attempting to read stdin
if [[ $# -gt 0 ]]; then
  raw_input="$*"
elif [[ -n "${CLAUDE_COMPOSE_INPUT:-}" ]]; then
  raw_input="$CLAUDE_COMPOSE_INPUT"
else
  raw_input=""
fi

# Read stdin with timeout-aware helper if we still have no content
if [[ -z "$raw_input" ]]; then
  raw_input=$(safe_read_stdin 5)
fi

# Optional logging for debugging (enable with COMPOSE_DEBUG=1)
if [[ -n "${COMPOSE_DEBUG:-}" ]]; then
  # Allow customizing log location; default to a secure temp file when unset
  if [[ -n "${COMPOSE_LOG_FILE:-}" ]]; then
    log_file="$COMPOSE_LOG_FILE"
  else
    if ! log_file="$(mktemp "${TMPDIR:-/tmp}/compose-commands.XXXXXX" 2>/dev/null)"; then
      log_file="${TMPDIR:-/tmp}/compose-commands-$$.log"
    fi
  fi
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  printf '[%s] INPUT: %s\n' "$timestamp" "$raw_input" >> "$log_file"
fi

# Try to parse as JSON first, fall back to plain text if that fails
# This maintains backward compatibility with plain text input
input=$(printf '%s' "$raw_input" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    # If it is valid JSON, extract the prompt field
    print(data.get("prompt", ""))
except (json.JSONDecodeError, ValueError):
    # Not JSON, treat as plain text
    sys.stdin.seek(0)
    print(sys.stdin.read())
' 2>/dev/null || echo "$raw_input")

# Detect if this is likely pasted content (like a GitHub PR page)
# Heuristics: GitHub UI patterns, PR formatting, commit stats
is_pasted_content=false
if echo "$input" | grep -qE '(Type / to search|Pull requests|Files changed|Navigation Menu|Skip to content|[0-9]+ commits?|Commits [0-9]+|[+−±-][0-9]+|wants to merge|#[0-9]+)' || \
   [[ $(echo "$input" | grep -o '/' | wc -l) -gt 20 ]]; then
    is_pasted_content=true
fi

# Multi-Player Command Detection: Extract potential slash commands + find nested commands
# Match slash followed by letters, numbers, underscores, and hyphens
raw_commands=$(echo "$input" | grep -oE '/[a-zA-Z][a-zA-Z0-9_-]*' | tr '\n' ' ')

# PERFORMANCE OPTIMIZATION: Cache git repository root to avoid repeated calls
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

# ── PR number resolution for template variable substitution ──────────────────
# Resolves {{pr_number}} from branch name (e.g. "fix/pr-123" → "123")
# so hooks that inject composed prompts can substitute the variable.
_resolve_pr_number() {
    local branch
    branch="$(git branch --show-current 2>/dev/null || git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
    if [[ -z "$branch" ]]; then
        echo ""
        return
    fi
    # session/* branches are AO session worktrees — never treated as PR-bearing
    if [[ "$branch" == session/* ]]; then
        echo ""
        return
    fi
    # Match patterns: pr-123, pr/123, ao-670, jc-123, wc-74, etc.
    # Anchor to prefix (not bare digits) to avoid session/wc-16 → PR #16
    local pr_num
    pr_num="$(echo "$branch" | grep -oE '(?:pr[-/]|ao-|jc-|wa-|cc-|ra-|wc-)([0-9]{2,4})' | tail -1 | grep -oE '[0-9]{2,4}' || echo "")"
    if [[ -z "$pr_num" ]]; then
        # Fallback: look up open PR by head branch via gh CLI
        pr_num="$(gh api "repos/$GITHUB_REPOSITORY/pulls" \
            --jq ".[] | select(.head.ref == \"$branch\" or .head.ref == \"${branch##*/}\") | .number" \
            2>/dev/null | head -1 || echo "")"
    fi
    echo "$pr_num"
}
PR_NUMBER="$(_resolve_pr_number)"

# ── No-PR context guard: skip composition entirely when no PR number resolved ────
# The green-gate workflow is PR-specific.  In worktrees with no associated PR
# (e.g. jleechanclaw main, jc-645), skip composition entirely so the prompt
# passes through unchanged — prevents idle-reminder loops from generating
# unresolvable template text every 15 minutes.
if [[ -z "$PR_NUMBER" ]]; then
    echo "$input"
    exit 0
fi

# ── PR Green Check Backoff Guard ───────────────────────────────────────────
# Check for ANY active skip file for this repo. If active, pass through without
# slash-command processing. Checks the skip file most recently modified.
_hook_remote=$(git remote get-url origin 2>/dev/null | sed 's/.git$//' | sed 's|.*github.com[:/]||' | tr '/' '_')
_now=$(python3 -c "import time; print(int(time.time()))")
# Find any skip file matching this repo that is still active
_skip_file=$(python3 -c "
import json, glob, os, time
now = int(time.time())
state_dir = '/tmp/pr_green_check'
owner = '$_hook_remote'
for pattern in [f'{state_dir}/.skip_{owner}_*', f'{state_dir}/.skip_*_{owner}_*']:
    for fp in glob.glob(pattern):
        try:
            d = json.load(open(fp))
            if d.get('until', 0) > now:
                print(fp)
                break
        except:
            pass
" 2>/dev/null)
if [[ -n "$_skip_file" && -f "$_skip_file" ]]; then
    echo "$input"
    exit 0
fi

# CORRECTNESS FIX: Standardize pasted content threshold
PASTE_COMMAND_THRESHOLD=2

# MULTI-PLAYER ENHANCEMENT: Parse command markdown files for nested commands
function find_nested_commands() {
    local cmd="$1"
    local cmd_file="$REPO_ROOT/.claude/commands/${cmd#/}.md"

    if [[ -f "$cmd_file" ]]; then
        # READABILITY IMPROVEMENT: Use simpler, more maintainable patterns
        # Look for "combines the functionality of" patterns
        combines_pattern=$(grep -E 'combines? the functionality of' "$cmd_file" 2>/dev/null | \
                          grep -oE '/[a-zA-Z][a-zA-Z0-9_-]*' | tr '\n' ' ' || echo "")

        # Look for direct action patterns (calls, executes, runs, uses, invokes)
        action_pattern=$(grep -E '(calls?|executes?|runs?|uses?|invokes?)' "$cmd_file" 2>/dev/null | \
                        grep -oE '/[a-zA-Z][a-zA-Z0-9_-]*' | tr '\n' ' ' || echo "")

        nested="$combines_pattern $action_pattern"

        # Also look for direct command references in workflow descriptions
        workflow_nested=$(grep -oE '(Phase [0-9]+|Step [0-9]+)[^/]*(/[a-zA-Z][a-zA-Z0-9_-]*)' "$cmd_file" 2>/dev/null | \
                         grep -oE '/[a-zA-Z][a-zA-Z0-9_-]*' | tr '\n' ' ' || echo "")

        echo "$nested $workflow_nested" | tr ' ' '\n' | sort -u | tr '\n' ' '
    fi
}

# Normalize whitespace across aggregated command strings in a consistent way
normalize_whitespace() {
    local input
    input=$(cat)
    printf '%s' "$input" | tr '\n' ' ' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/[[:space:]][[:space:]]*/ /g'
}

# Count valid commands first to inform filtering decision
valid_cmd_count=0
for cmd in $raw_commands; do
    escaped_cmd=$(printf '%s' "$cmd" | sed 's/[][().^$*+?{}|\\]/\\&/g')
    if echo "$input" | grep -qE "(^|[[:space:]])$escaped_cmd([[:space:]]|[[:punct:]]|$)" && \
       ! echo "$input" | grep -qE "$escaped_cmd/"; then
        valid_cmd_count=$((valid_cmd_count + 1))
    fi
done

# Multi-Player Command Analysis: Filter commands + detect nested commands
commands=""
nested_commands=""
actual_cmd_count=0
# COMPATIBILITY FIX: Use optimized string approach (bash version doesn't support associative arrays)
seen_commands=" "  # Track commands to avoid duplicates (space-padded for exact matching)

for cmd in $raw_commands; do
    # Escape command for safe regex usage (properly escape all regex special chars)
    escaped_cmd=$(printf '%s' "$cmd" | sed 's/[][().^$*+?{}|\\]/\\&/g')
    # Check if this appears to be a standalone command (not part of a path)
    if echo "$input" | grep -qE "(^|[[:space:]])$escaped_cmd([[:space:]]|[[:punct:]]|$)" && \
       ! echo "$input" | grep -qE "$escaped_cmd/"; then

        # If this looks like pasted content, apply stricter filtering
        if [[ "$is_pasted_content" == "true" ]]; then
            # Accept all commands if there are 2 or fewer (likely intentional)
            # Otherwise, only accept commands at boundaries
            if [[ $valid_cmd_count -le $PASTE_COMMAND_THRESHOLD ]]; then
                if [[ "$seen_commands" != *" $cmd "* ]]; then
                    commands="$commands$cmd "
                    actual_cmd_count=$((actual_cmd_count + 1))
                    seen_commands="$seen_commands$cmd "
                fi

                # BUG FIX: Add nested command analysis for pasted content too
                nested=$(find_nested_commands "$cmd")
                if [[ -n "$nested" ]]; then
                    nested_commands="$nested_commands$nested"
                fi
            else
                # Check if command is in first or last 200 characters using escaped pattern
                input_start="${input:0:200}"
                input_end="${input: -200}"
                if echo "$input_start" | grep -qF "$cmd" || echo "$input_end" | grep -qF "$cmd"; then
                    if [[ "$seen_commands" != *" $cmd "* ]]; then
                        commands="$commands$cmd "
                        actual_cmd_count=$((actual_cmd_count + 1))
                        seen_commands="$seen_commands$cmd "
                    fi

                    # BUG FIX: Add nested command analysis for boundary pasted content too
                    nested=$(find_nested_commands "$cmd")
                    if [[ -n "$nested" ]]; then
                        nested_commands="$nested_commands$nested"
                    fi
                fi
            fi
        else
            # Normal processing for typed content
            if [[ "$seen_commands" != *" $cmd "* ]]; then
                commands="$commands$cmd "
                actual_cmd_count=$((actual_cmd_count + 1))
                seen_commands="$seen_commands$cmd "
            fi

            # MULTI-PLAYER: Find nested commands for this command
            nested=$(find_nested_commands "$cmd")
            if [[ -n "$nested" ]]; then
                nested_commands="$nested_commands$nested"
            fi
        fi
    fi
done

# Normalize whitespace for aggregated command strings before further processing
commands=$(printf '%s' "$commands" | normalize_whitespace)
nested_commands=$(printf '%s' "$nested_commands" | normalize_whitespace)

# Exit early if no real slash commands found
if [[ -z "$commands" ]]; then
    echo "$input"
    exit 0
fi
# Remove only the commands that were actually detected using safer approach
text="$input"
for cmd in $commands; do
    # Use Python for safer word-boundary aware replacement
    text=$(echo "$text" | python3 -c "
import sys
import re
text = sys.stdin.read()
cmd = '$cmd'
# Escape regex special characters
escaped_cmd = re.escape(cmd)
# Remove command with word boundaries
pattern = r'(^|\s)' + escaped_cmd + r'(\s|$)'
text = re.sub(pattern, r'\1\2', text)
print(text, end='')
")
done
# Clean up extra whitespace
text=$(echo "$text" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | sed 's/[[:space:]][[:space:]]*/ /g')

# Use actual command count from filtering loop
command_count=$actual_cmd_count

# MULTI-PLAYER OUTPUT: Combine detected + nested commands intelligently
# Clean and deduplicate nested commands
if [[ -n "$nested_commands" ]]; then
    nested_commands=$(printf '%s' "$nested_commands" | tr ' ' '\n' | sed '/^$/d' | sort -u | normalize_whitespace)
fi

# ENHANCED: Check if we have any valid commands to process
# Process single commands with composition potential OR multiple commands
# Pattern-based approach: Check if command file exists OR is conceptual command
should_process_single_command() {
    local cmd="$1"

    # Input validation: ensure non-empty and properly formatted
    if [[ -z "$cmd" ]]; then
        return 1  # Empty input - should not process
    fi

    # Strip leading/trailing spaces for robust comparison and extract first word
    cmd="${cmd# }"     # Remove leading spaces
    cmd="${cmd% }"     # Remove trailing spaces
    cmd="${cmd%% *}"   # Extract first word (everything before first space)

    # Security validation: prevent path traversal attacks (defense-in-depth)
    if [[ "$cmd" =~ \.\./|/\.\.|^\.\.$|// ]]; then
        return 1  # Path traversal attempt - should not process
    fi

    # Validate basic command pattern first
    if [[ ! "$cmd" =~ ^/[a-zA-Z][a-zA-Z0-9_-]*$ ]]; then
        return 1  # Invalid command format - should not process
    fi

    # Remove leading slash for file lookup
    local cmd_file="${cmd#/}"

    # Validate cmd_file: only allow alphanumeric, underscores, and hyphens
    if [[ ! "$cmd_file" =~ ^[A-Za-z0-9_-]+$ ]]; then
        return 1  # Invalid command file name
    fi

    # Configurable extension support (md by default, extensible)
    local extensions=("md")  # Future: could be configurable
    local cmd_path=""
    local found_file=false

    # Only check filesystem if we have a valid REPO_ROOT
    if [[ -n "$REPO_ROOT" && -d "$REPO_ROOT/.claude/commands" ]]; then
        for ext in "${extensions[@]}"; do
            cmd_path="$REPO_ROOT/.claude/commands/${cmd_file}.${ext}"
            # Additional security: ensure resolved path stays within commands directory
            local resolved_path=""
            if dir="$(cd "$(dirname "$cmd_path")" 2>/dev/null && pwd)"; then
                resolved_path="$dir/$(basename "$cmd_path")"
            fi
            if [[ -n "$resolved_path" && "$resolved_path" == "$REPO_ROOT/.claude/commands/"* && -f "$cmd_path" ]]; then
                found_file=true
                break
            fi
        done

        if [[ "$found_file" == true ]]; then
            return 0  # Should process - command file exists and is secure
        fi
    fi

    # Process conceptual commands (slash followed by word pattern)
    # Exclude common false positives like system paths AND simple commands without composition potential
    if [[ ! "$cmd" =~ ^/(usr|var|etc|home|bin|lib|opt|tmp|dev|proc|sys|root|mnt|media|help)$ ]]; then
        return 0  # Should process - valid conceptual command
    fi

    return 1  # Should not process - neither file nor valid conceptual command
}

# Prepare intelligent multi-player output
# Trigger for multiple commands OR single commands with composition potential
if [[ $command_count -gt 1 ]] || ( [[ $command_count -eq 1 ]] && should_process_single_command "${commands%% *}" ); then
    # Build comprehensive command list (detected + nested)
    all_commands="$commands"
    if [[ -n "$nested_commands" ]]; then
        # CORRECTNESS FIX: Use printf for proper deduplication across merged sources
        all_commands=$(printf '%s\n%s' "$commands" "$nested_commands" | tr ' ' '\n' | sed '/^$/d' | sort -u | tr '\n' ' ')
    fi

    # Ensure combined command list has clean whitespace for user-facing output
    all_commands=$(printf '%s' "$all_commands" | normalize_whitespace)

    # Add context awareness to the output
    if [[ "$is_pasted_content" == "true" && $command_count -le $PASTE_COMMAND_THRESHOLD ]]; then
        # Likely intentional commands at beginning/end of pasted content
        if [[ -n "$nested_commands" ]]; then
            output="🔍 Detected slash commands:$commands
🎯 Multi-Player Intelligence: Found nested commands:$nested_commands

Use these approaches in combination:$all_commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$commands and will combine them intelligently.\""
        else
            output="🔍 Detected slash commands:$commands

Use these approaches in combination:$commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$commands and will combine them intelligently.\""
        fi
    elif [[ "$is_pasted_content" == "true" ]]; then
        # Too many commands detected in pasted content, likely false positives
        # Just pass through the original input
        output="$input"
    else
        # Normal multi-command composition with multi-player intelligence
        if [[ -n "$nested_commands" ]]; then
            output="🔍 Detected slash commands:$commands
🎯 Multi-Player Intelligence: Found nested commands:$nested_commands

Use these approaches in combination:$all_commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$commands and will combine them intelligently.\""
        else
            output="🔍 Detected slash commands:$commands

Use these approaches in combination:$commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$commands and will combine them intelligently.\""
        fi
    fi
else
    # MULTI-PLAYER: Single commands only trigger multi-player intelligence for composition commands
    # Simple commands like /think, /help, etc. should pass through unchanged
    if [[ $command_count -eq 1 ]]; then
        # For single commands, only trigger multi-player intelligence when meaningful nested commands exist
        single_command="${commands%% *}"

        if [[ -n "$single_command" && -n "$nested_commands" ]]; then
            # Filter out self-references and extract meaningful nested commands
            filtered_nested=$(echo "$nested_commands" | tr ' ' '\n' | grep -v "^${single_command}$" | grep -v '^$' | sort -u | tr '\n' ' ' | sed 's/[[:space:]]*$//')

            if [[ -n "$filtered_nested" ]]; then
                all_commands=$(printf '%s\n%s' "$single_command" "$filtered_nested" | tr ' ' '\n' | sort -u | grep -v '^$' | tr '\n' ' ' | sed 's/[[:space:]]*$//')
                output="🔍 Detected slash command:$single_command
🎯 Multi-Player Intelligence: Found nested commands:$filtered_nested

Use these approaches in combination:$all_commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$single_command and will combine them intelligently.\""
            else
                # No meaningful nested commands, pass through unchanged
                output="$input"
            fi
        else
            # Single command without nested intelligence - preserve for backward compatibility
            # Fixed: Don't strip command prefix to maintain compatibility with existing workflows
            output="$input"
        fi
    else
        # No commands detected, pass through unchanged
        output="$input"
    fi
fi

# Multi-Player Debug Logging
if [[ -n "${COMPOSE_DEBUG:-}" ]]; then
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  printf '[%s] DETECTED: %s\n' "$timestamp" "$commands" >> "$log_file"
  printf '[%s] NESTED: %s\n' "$timestamp" "$nested_commands" >> "$log_file"
  printf '[%s] OUTPUT: %s\n' "$timestamp" "$output" >> "$log_file"
  printf '[%s] ---\n' "$timestamp" >> "$log_file"
fi

# ── Substitute {{pr_number}} template variable ─────────────────────────────────
# If PR_NUMBER was resolved from branch context, replace the placeholder in the
# composed output. If not resolved (no PR context), leave placeholder as-is so
# the session can report it as a hook setup issue rather than silently failing.
if [[ -n "$PR_NUMBER" ]]; then
    output="${output//\{\{pr_number\}\}/$PR_NUMBER}"
else
    # No PR context: strip the full green-gate workflow block to prevent
    # injecting an unresolvable template into the LLM prompt.  The block starts
    # at "(STEP -1" and ends at the "📋 Automatically" marker.
    output=$(echo "$output" | python3 -c "
import sys, re
text = sys.stdin.read()
# Remove green-gate workflow block: from (STEP -1 to 📋 marker (exclusive)
text = re.sub(r'\(STEP -1.*?\)(?=📋|\Z)', '', text, flags=re.DOTALL)
# Also remove any remaining unresolved template variables
text = re.sub(r'\{\{[^}]+\}\}', '', text)
print(text.strip())
")
fi

# Return the output
echo "$output"
