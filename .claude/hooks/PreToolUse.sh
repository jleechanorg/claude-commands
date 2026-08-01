#!/usr/bin/env bash
# PreToolUse hook - Wafer/GLM-5.1 defense-in-depth
# Only active when CLAUDEW_MODE=1 (claudew sessions)
#
# Layer 1a: Hard-block oversized Read calls (>2000 lines or >100KB)
# Layer 1b: Hard-block Bash bulk-read (cat/head/tail/awk) on large files
# In non-wafer mode, passes everything through unchanged.

set -euo pipefail

# Fast exit if not wafer mode
if [ "${CLAUDEW_MODE:-}" != "1" ]; then
  cat
  exit 0
fi

# Guard: ensure jq is available
if ! command -v jq >/dev/null 2>&1; then
  cat
  exit 0
fi

TOOL_REQUEST=$(cat)
TOOL_NAME=$(echo "$TOOL_REQUEST" | jq -r '.tool_name' 2>/dev/null || echo "unknown")

# Logging setup
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "/tmp")
PROJECT_NAME=$(basename "$PROJECT_ROOT" 2>/dev/null || echo "unknown-project")
BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo 'unknown')
LOG_FILE="/tmp/${PROJECT_NAME}/${BRANCH_NAME}/hook_modifications.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

CONVERSATION_FILE=$(head -1 < <(ls -t ~/.claude/projects/*/*.jsonl 2>/dev/null) || true)
SESSION_ID=$(basename "$CONVERSATION_FILE" .jsonl 2>/dev/null || echo "unknown")

WAFER_LINE_LIMIT=2000
WAFER_BYTE_LIMIT=100000

case "$TOOL_NAME" in
  Read)
    FILE_PATH=$(echo "$TOOL_REQUEST" | jq -r '.tool_input.file_path' 2>/dev/null || echo "")

    if [ -f "$FILE_PATH" ]; then
      LINE_COUNT=$(wc -l < "$FILE_PATH" 2>/dev/null || echo "0")
      FILE_SIZE=$(stat -f%z "$FILE_PATH" 2>/dev/null || stat -c%s "$FILE_PATH" 2>/dev/null || echo "0")
      HAS_OFFSET=$(echo "$TOOL_REQUEST" | jq -r '.tool_input.offset // "null"' 2>/dev/null || echo "null")
      HAS_LIMIT=$(echo "$TOOL_REQUEST" | jq -r '.tool_input.limit // "null"' 2>/dev/null || echo "null")

      # Compute effective read range
      if [ "$HAS_LIMIT" != "null" ]; then
        EFFECTIVE_LINES=$HAS_LIMIT
      else
        if [ "$HAS_OFFSET" != "null" ]; then
          EFFECTIVE_LINES=$((LINE_COUNT - HAS_OFFSET))
        else
          EFFECTIVE_LINES=$LINE_COUNT
        fi
      fi
      if [ "$EFFECTIVE_LINES" -lt 0 ]; then
        EFFECTIVE_LINES=0
      fi

      if [ "$EFFECTIVE_LINES" -gt "$WAFER_LINE_LIMIT" ] || [ "$FILE_SIZE" -gt "$WAFER_BYTE_LIMIT" -a "$EFFECTIVE_LINES" -gt "$WAFER_LINE_LIMIT" ]; then
        jq -n \
          --arg lines "$LINE_COUNT" \
          --arg bytes "$FILE_SIZE" \
          --arg effective "$EFFECTIVE_LINES" \
          --arg file "$(basename "$FILE_PATH")" \
          '{decision:"block",reason:("Blocked oversized read in wafer mode: "+$file+" is "+$lines+" lines / "+$bytes+" bytes (requested "+$effective+" lines). Use offset/limit (max limit:2000) or grep -n to locate the section you need first.")}'
        jq -n \
          --arg timestamp "$(date -Iseconds)" \
          --arg session_id "$SESSION_ID" \
          --arg tool "Read" \
          --arg file "$FILE_PATH" \
          --argjson lines "$LINE_COUNT" \
          --argjson bytes "$FILE_SIZE" \
          --argjson effective_lines "$EFFECTIVE_LINES" \
          --arg action "blocked_wafer" \
          '{timestamp:$timestamp, session_id:$session_id, tool:$tool, file:$file, lines:$lines, bytes:$bytes, effective_lines:$effective_lines, action:$action}' \
          >> "$LOG_FILE" 2>/dev/null || true
        exit 0
      fi
    fi
    ;;

  Bash)
    COMMAND=$(echo "$TOOL_REQUEST" | jq -r '.tool_input.command' 2>/dev/null || echo "")

    # Block bulk file readers (cat, head, tail, awk) — allow grep/sed (targeted search)
    IS_BULK_READER=false
    if echo "$COMMAND" | grep -qE '(^|[|;&]|&&|\|\|)[[:space:]]*(cat|head|tail|awk)[[:space:]]'; then
      IS_BULK_READER=true
    fi

    if [ "$IS_BULK_READER" = true ]; then
      BASH_TARGET_FILE=""
      for ARG in $COMMAND; do
        CLEAN_ARG="${ARG#\"}"
        CLEAN_ARG="${CLEAN_ARG%\"}"
        CLEAN_ARG="${CLEAN_ARG%\'}"
        CLEAN_ARG="${CLEAN_ARG%%[;|&]*}"
        [[ "$CLEAN_ARG" == -* ]] && continue
        if [ -f "$CLEAN_ARG" ]; then
          BASH_TARGET_FILE="$CLEAN_ARG"
        fi
      done

      if [ -n "$BASH_TARGET_FILE" ]; then
        BASH_FILE_SIZE=$(stat -f%z "$BASH_TARGET_FILE" 2>/dev/null || stat -c%s "$BASH_TARGET_FILE" 2>/dev/null || echo "0")
        BASH_FILE_LINES=$(wc -l < "$BASH_TARGET_FILE" 2>/dev/null || echo "0")

        if [ "$BASH_FILE_SIZE" -gt "$WAFER_BYTE_LIMIT" ] || [ "$BASH_FILE_LINES" -gt "$WAFER_LINE_LIMIT" ]; then
          jq -n \
            --arg lines "$BASH_FILE_LINES" \
            --arg bytes "$BASH_FILE_SIZE" \
            --arg file "$(basename "$BASH_TARGET_FILE")" \
            --arg cmd "$(echo "$COMMAND" | head -c 200)" \
            '{decision:"block",reason:("Blocked Bash bulk-read in wafer mode: "+$file+" is "+$lines+" lines / "+$bytes+" bytes. Command: "+$cmd+". Use grep -n to locate the section, then Read with offset/limit (max limit:2000) to read only what you need.")}'
          jq -n \
            --arg timestamp "$(date -Iseconds)" \
            --arg session_id "$SESSION_ID" \
            --arg tool "Bash" \
            --arg file "$BASH_TARGET_FILE" \
            --argjson lines "$BASH_FILE_LINES" \
            --argjson bytes "$BASH_FILE_SIZE" \
            --arg action "blocked_wafer_bash" \
            '{timestamp:$timestamp, session_id:$session_id, tool:$tool, file:$file, lines:$lines, bytes:$bytes, action:$action}' \
            >> "$LOG_FILE" 2>/dev/null || true
          exit 0
        fi
      fi
    fi
    ;;
esac

# Output modified request (or original if no changes)
echo "$TOOL_REQUEST"
