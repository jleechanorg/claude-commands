#!/usr/bin/env bash
# UserPromptSubmit hook - Session health monitoring
# Runs every time user sends a message to Claude
# Warns when session grows large to encourage /clear
#
# Thresholds:
# - 500 messages: ⚠️ Yellow warning
# - 1,000 messages: 🟠 Orange warning
# - 2,000 messages: 🔴 Red warning
#
# See: roadmap/2026-01-10-token-optimization-automation.md

set -uo pipefail
# NOTE: Do NOT use `set -e` (errexit) in hooks: hooks must be non-blocking.

find_conversation_file() {
  local repo_root
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1

  local dir_from_path
  dir_from_path="$(printf '%s' "$repo_root" | tr '/' '-')"

  local dir_dot_to_dash
  dir_dot_to_dash="$(printf '%s' "$dir_from_path" | tr '.' '-')"

  local candidate
  for candidate in "$HOME/.claude/projects/$dir_dot_to_dash" "$HOME/.claude/projects/$dir_from_path"; do
    if [ -d "$candidate" ]; then
      head -1 < <(ls -t "$candidate"/*.jsonl 2>/dev/null) || true
      return 0
    fi
  done

  return 1
}

# Find current conversation file (most recently modified .jsonl in THIS project)
# Session files are named with UUIDs like "3ac775c6-6ff9-40a1-a192-6319e0f34d1c.jsonl"
CONVERSATION_FILE="$(find_conversation_file 2>/dev/null || true)"

# Count messages (non-empty lines)
if [ -n "${CONVERSATION_FILE:-}" ] && [ -f "$CONVERSATION_FILE" ]; then
  MSG_COUNT="$(grep -c . "$CONVERSATION_FILE" 2>/dev/null || echo "0")"
else
  MSG_COUNT=0
fi

# Display warnings based on thresholds (only show highest threshold hit)
if [ "$MSG_COUNT" -ge 2000 ]; then
  echo "🔴 Very large session ($MSG_COUNT messages) - /clear strongly recommended" >&2
  THRESHOLD="2000"
elif [ "$MSG_COUNT" -ge 1000 ]; then
  echo "🟠 Large session ($MSG_COUNT messages) - recommend /clear" >&2
  THRESHOLD="1000"
elif [ "$MSG_COUNT" -ge 500 ]; then
  echo "⚠️  Session growing large ($MSG_COUNT messages) - consider /clear soon" >&2
  THRESHOLD="500"
else
  THRESHOLD="none"
fi

# Log warning display for tracking adherence
if [ "$MSG_COUNT" -ge 500 ]; then
  BRANCH_NAME="$(git branch --show-current 2>/dev/null || git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
  LOG_FILE="/tmp/your-project.com/${BRANCH_NAME}/session_warnings.log"
  mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
  echo "{\"timestamp\":\"$(date -Iseconds)\",\"messages\":$MSG_COUNT,\"threshold\":\"$THRESHOLD\"}" >> "$LOG_FILE" 2>/dev/null || true
fi

# Always exit 0 (non-blocking)
exit 0
