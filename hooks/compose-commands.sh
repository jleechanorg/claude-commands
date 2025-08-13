#!/bin/bash
# Universal Command Composition Hook for Claude Code
# Leverages Claude's natural language processing for true universality

# Read JSON from stdin
json_input=$(cat)

# Optional logging for debugging (enable with COMPOSE_DEBUG=1)
if [[ -n "${COMPOSE_DEBUG:-}" ]]; then
  # Allow customizing log location; include PID for uniqueness
  log_file="${COMPOSE_LOG_FILE:-/tmp/compose-commands-$$.log}"
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  printf '[%s] INPUT: %s\n' "$timestamp" "$json_input" >> "$log_file"
fi

# Extract the prompt field from JSON using Python (always available in Claude Code)
# Python handles all edge cases including escaped quotes, Unicode, etc.
input=$(printf '%s' "$json_input" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("prompt", ""))' 2>/dev/null || echo "")

# Detect if this is likely pasted content (like a GitHub PR page)
# Heuristics: GitHub UI patterns, PR formatting, commit stats
is_pasted_content=false
if echo "$input" | grep -qE '(Type / to search|Pull requests|Files changed|Navigation Menu|Skip to content|[0-9]+ commits?|Commits [0-9]+|[+−±-][0-9]+|wants to merge|#[0-9]+)' || \
   [[ $(echo "$input" | grep -o '/' | wc -l) -gt 20 ]]; then
    is_pasted_content=true
fi

# Extract potential slash commands
# Match slash followed by letters, numbers, underscores, and hyphens
raw_commands=$(echo "$input" | grep -oE '/[a-zA-Z][a-zA-Z0-9_-]*' | tr '\n' ' ')

# Count total valid commands first to inform filtering decision
cmd_count_in_input=0
for cmd in $raw_commands; do
    # Escape command for safe regex usage
    escaped_cmd=$(printf '%s' "$cmd" | sed 's/[]\[\(\)\{\}\*\+\?\^\$\|\\]/\\&/g')
    if echo "$input" | grep -qE "(^|[[:space:]])$escaped_cmd([[:space:]]|[[:punct:]]|$)" && \
       ! echo "$input" | grep -qE "$escaped_cmd/"; then
        cmd_count_in_input=$((cmd_count_in_input + 1))
    fi
done

# Filter commands based on context
commands=""
actual_cmd_count=0
for cmd in $raw_commands; do
    # Escape command for safe regex usage
    escaped_cmd=$(printf '%s' "$cmd" | sed 's/[]\[\(\)\{\}\*\+\?\^\$\|\\]/\\&/g')
    # Check if this appears to be a standalone command (not part of a path)
    if echo "$input" | grep -qE "(^|[[:space:]])$escaped_cmd([[:space:]]|[[:punct:]]|$)" && \
       ! echo "$input" | grep -qE "$escaped_cmd/"; then
        
        # If this looks like pasted content, apply stricter filtering
        if [[ "$is_pasted_content" == "true" ]]; then
            # Accept all commands if there are 2 or fewer (likely intentional)
            # Otherwise, only accept commands at boundaries
            if [[ $cmd_count_in_input -le 2 ]]; then
                commands="$commands$cmd "
                actual_cmd_count=$((actual_cmd_count + 1))
            else
                # Check if command is in first or last 200 characters using escaped pattern
                input_start="${input:0:200}"
                input_end="${input: -200}"
                if echo "$input_start" | grep -qF "$cmd" || echo "$input_end" | grep -qF "$cmd"; then
                    commands="$commands$cmd "
                    actual_cmd_count=$((actual_cmd_count + 1))
                fi
            fi
        else
            # Normal processing for typed content
            commands="$commands$cmd "
            actual_cmd_count=$((actual_cmd_count + 1))
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
    # Use literal string replacement with awk to avoid sed escaping issues
    text=$(echo "$text" | awk -v pattern="$cmd" '{gsub(pattern,""); print}')
done
# Clean up extra whitespace
text=$(echo "$text" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

# Use actual command count from filtering loop
command_count=$actual_cmd_count

# Prepare output
if [[ $command_count -gt 1 ]]; then
    # Add context awareness to the output
    if [[ "$is_pasted_content" == "true" && $command_count -le 3 ]]; then
        # Likely intentional commands at beginning/end of pasted content
        output="🔍 Detected slash commands:$commands

Use these approaches in combination:$commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$commands and will combine them intelligently.\""
    elif [[ "$is_pasted_content" == "true" ]]; then
        # Too many commands detected in pasted content, likely false positives
        # Just pass through the original input
        output="$input"
    else
        # Normal multi-command composition
        output="🔍 Detected slash commands:$commands

Use these approaches in combination:$commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$commands and will combine them intelligently.\""
    fi
else
    # Single command or no commands pass through unchanged
    output="$input"
fi

# Log the output
if [[ -n "${COMPOSE_DEBUG:-}" ]]; then
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  printf '[%s] OUTPUT: %s\n' "$timestamp" "$output" >> "$log_file"
  printf '[%s] ---\n' "$timestamp" >> "$log_file"
fi

# Return the output
echo "$output"
