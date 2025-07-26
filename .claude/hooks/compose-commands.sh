#!/bin/bash
# Universal Command Composition Hook for Claude Code
# Leverages Claude's natural language processing for true universality

input="$1"

# Exit early if no slash commands found
if [[ ! "$input" =~ /[a-zA-Z] ]]; then
    echo "$input"
    exit 0
fi

# Extract all slash commands and remaining text
commands=$(echo "$input" | grep -oE '\/[a-zA-Z]+' | tr '\n' ' ')
text=$(echo "$input" | sed 's/\/[a-zA-Z]\+//g' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

# Count commands
command_count=$(echo "$commands" | wc -w)

# If multiple commands, create meta-prompt for Claude's NLP with explicit detection
if [[ $command_count -gt 1 ]]; then
    echo "🔍 Detected slash commands:$commands

Use these approaches in combination:$commands. Apply this to: $text

📋 Automatically tell the user: \"I detected these commands:$commands and will combine them intelligently.\""
else
    # Single command or no commands pass through unchanged
    echo "$input"
fi
