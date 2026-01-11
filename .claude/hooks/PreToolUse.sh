#!/usr/bin/env bash
# PreToolUse hook - Token optimization via tool input modification
# Receives JSON tool request on stdin, outputs modified JSON to stdout
#
# Optimizations:
# 1. Read tool: Add offset/limit for files >500 lines (40-50% reduction)
# 2. Bash tool: Inject --minimal --unified=0 for git diff (30-40% reduction)
#
# See: roadmap/2026-01-10-token-optimization-automation.md

set -euo pipefail

# Read incoming tool request JSON
TOOL_REQUEST=$(cat)
TOOL_NAME=$(echo "$TOOL_REQUEST" | jq -r '.name' 2>/dev/null || echo "unknown")

# Setup logging
LOG_FILE="/tmp/worldarchitect.ai/$(git branch --show-current 2>/dev/null || echo 'unknown')/hook_modifications.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

# Identify Session ID (best effort)
# Use process substitution to avoid SIGPIPE with pipefail
CONVERSATION_FILE=$(head -1 < <(ls -t ~/.claude/projects/*/*.jsonl 2>/dev/null) || true)
SESSION_ID=$(basename "$CONVERSATION_FILE" .jsonl 2>/dev/null || echo "unknown")

case "$TOOL_NAME" in
  Read)
    FILE_PATH=$(echo "$TOOL_REQUEST" | jq -r '.input.file_path' 2>/dev/null || echo "")

    # Only process if file exists and doesn't already have offset/limit
    if [ -f "$FILE_PATH" ]; then
      HAS_OFFSET=$(echo "$TOOL_REQUEST" | jq -r '.input.offset // "null"' 2>/dev/null || echo "null")

      if [ "$HAS_OFFSET" == "null" ]; then
        LINE_COUNT=$(wc -l < "$FILE_PATH" 2>/dev/null || echo "0")

        # Files >500 lines: read middle 500 lines
        if [ "$LINE_COUNT" -gt 500 ]; then
          MIDDLE=$((LINE_COUNT / 2))
          START=$((MIDDLE - 250))
          # First check for negative start (handling small files or near-start windows)
          if [ "$START" -lt 0 ]; then
            START=0
          fi
          
          # Adjust if window goes past end of file
          if [ $((START + 500)) -gt "$LINE_COUNT" ]; then
            START=$((LINE_COUNT - 500))
          fi
          
          # Final safety check (in case LINE_COUNT < 500 despite outer check)
          if [ "$START" -lt 0 ]; then
            START=0
          fi

          # Modify JSON to add offset/limit
          TOOL_REQUEST=$(echo "$TOOL_REQUEST" | jq \
            --arg offset "$START" \
            --arg limit "500" \
            '.input.offset = ($offset | tonumber) | .input.limit = ($limit | tonumber)' 2>/dev/null || echo "$TOOL_REQUEST")

          # Log modification safely using jq
          REDUCTION_PCT=$((100 - (500 * 100 / LINE_COUNT)))
          jq -n \
            --arg timestamp "$(date -Iseconds)" \
            --arg session_id "$SESSION_ID" \
            --arg tool "Read" \
            --arg file "$FILE_PATH" \
            --argjson original_lines "$LINE_COUNT" \
            --argjson modified_lines 500 \
            --argjson reduction_pct "$REDUCTION_PCT" \
            '{timestamp:$timestamp, session_id:$session_id, tool:$tool, file:$file, original_lines:$original_lines, modified_lines:$modified_lines, reduction_pct:$reduction_pct}' \
            >> "$LOG_FILE" 2>/dev/null || true
        fi
      fi
    fi
    ;;

  Bash)
    COMMAND=$(echo "$TOOL_REQUEST" | jq -r '.input.command' 2>/dev/null || echo "")

    # Intercept git diff commands - add --minimal --unified=0 if not present
    # Use sed with word boundaries to match actual git commands, not string literals
    # Handle both "git diff" and "git --no-pager diff"
    if [[ "$COMMAND" != *"--minimal"* ]]; then
      MODIFIED_COMMAND="$COMMAND"
      WAS_MODIFIED=false

      # Use sed to match "git diff" or "git --no-pager diff" as actual commands
      # Pattern matches git commands at start of line or after command separators (|, ;, &, &&, ||)
      # This avoids matching string literals like grep "git diff" or echo "run git diff"
      # Note: This is a heuristic - perfect quote detection in bash commands is complex
      if echo "$COMMAND" | grep -qE '(^|[|;&]|&&|\|\|)[[:space:]]*git[[:space:]]+--no-pager[[:space:]]+diff([[:space:]]|$)'; then
        # Match "git --no-pager diff" as a command (not in quotes)
        MODIFIED_COMMAND=$(echo "$COMMAND" | sed -E 's/(^|[|;&]|&&|\|\|)([[:space:]]*)(git[[:space:]]+--no-pager[[:space:]]+diff)([[:space:]]|$)/\1\2\3 --minimal --unified=0\4/')
        WAS_MODIFIED=true
      elif echo "$COMMAND" | grep -qE '(^|[|;&]|&&|\|\|)[[:space:]]*git[[:space:]]+diff([[:space:]]|$)'; then
        # Match "git diff" as a command (not in quotes)
        MODIFIED_COMMAND=$(echo "$COMMAND" | sed -E 's/(^|[|;&]|&&|\|\|)([[:space:]]*)(git[[:space:]]+diff)([[:space:]]|$)/\1\2\3 --minimal --unified=0\4/')
        WAS_MODIFIED=true
      fi

      if [ "$WAS_MODIFIED" = true ]; then
        TOOL_REQUEST=$(echo "$TOOL_REQUEST" | jq \
          --arg cmd "$MODIFIED_COMMAND" \
          '.input.command = $cmd' 2>/dev/null || echo "$TOOL_REQUEST")

        # Log modification safely
        jq -n \
          --arg timestamp "$(date -Iseconds)" \
          --arg session_id "$SESSION_ID" \
          --arg tool "Bash" \
          --arg optimization "git_diff_minimal" \
          --arg original "git diff" \
          --arg modified "git diff --minimal --unified=0" \
          '{timestamp:$timestamp, session_id:$session_id, tool:$tool, optimization:$optimization, original:$original, modified:$modified}' \
          >> "$LOG_FILE" 2>/dev/null || true
      fi
    fi
    ;;
esac

# Output modified request (or original if no changes or errors)
echo "$TOOL_REQUEST"
