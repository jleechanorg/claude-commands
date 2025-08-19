#!/bin/bash
# Universal Command Composition Hook for Claude Code  
# Multi-Player Intelligent Command Combination System
# Leverages Claude's natural language processing + nested command parsing for true universality

# Read input from stdin (can be JSON or plain text)
raw_input=$(cat)

# Optional logging for debugging (enable with COMPOSE_DEBUG=1)
if [[ -n "${COMPOSE_DEBUG:-}" ]]; then
  # Allow customizing log location; include PID for uniqueness
  log_file="${COMPOSE_LOG_FILE:-/tmp/compose-commands-$$.log}"
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

# Count total valid commands first to inform filtering decision
cmd_count_in_input=0
for cmd in $raw_commands; do
    # Escape command for safe regex usage (properly escape all regex special chars)
    escaped_cmd=$(printf '%s' "$cmd" | sed 's/[][().^$*+?{}|\\]/\\&/g')
    if echo "$input" | grep -qE "(^|[[:space:]])$escaped_cmd([[:space:]]|[[:punct:]]|$)" && \
       ! echo "$input" | grep -qE "$escaped_cmd/"; then
        cmd_count_in_input=$((cmd_count_in_input + 1))
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
            if [[ $cmd_count_in_input -le $PASTE_COMMAND_THRESHOLD ]]; then
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
nested_commands=$(echo "$nested_commands" | tr ' ' '\n' | sort -u | grep -v '^$' | tr '\n' ' ')

# Prepare intelligent multi-player output
# Only trigger for multiple commands OR single composition commands with meaningful nested commands
if [[ $command_count -gt 1 ]] || ( [[ $command_count -eq 1 ]] && [[ "$commands" == "/pr " || "$commands" == "/execute " || "$commands" == "/copilot " || "$commands" == "/orchestrate " ]] && [[ -n "$nested_commands" ]] ); then
    # Build comprehensive command list (detected + nested)
    all_commands="$commands"
    if [[ -n "$nested_commands" ]]; then
        # CORRECTNESS FIX: Use printf for proper deduplication across merged sources
        all_commands=$(printf '%s\n%s' "$commands" "$nested_commands" | tr ' ' '\n' | sort -u | grep -v '^$' | tr '\n' ' ')
    fi
    
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
        # Check if this is a known composition command that should trigger multi-player intelligence
        if [[ "$commands" == "/pr " || "$commands" == "/execute " || "$commands" == "/copilot " || "$commands" == "/orchestrate " ]] && [[ -n "$nested_commands" ]]; then
            # Filter out self-references and extract meaningful nested commands
            filtered_nested=$(echo "$nested_commands" | tr ' ' '\n' | grep -v "^${commands% }$" | grep -v '^$' | tr '\n' ' ')
            
            if [[ -n "$filtered_nested" ]]; then
                all_commands=$(printf '%s\n%s' "$commands" "$filtered_nested" | tr ' ' '\n' | sort -u | grep -v '^$' | tr '\n' ' ')
                output="🔍 Detected slash command:$commands
🎯 Multi-Player Intelligence: Found nested commands:$filtered_nested

Use these approaches in combination:$all_commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$commands and will combine them intelligently.\""
            else
                # No meaningful nested commands, pass through unchanged
                output="$input"
            fi
        else
            # Single command that's not a composition command passes through unchanged
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

# Return the output
echo "$output"
