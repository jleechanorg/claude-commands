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

# ---------------------------------------------------------------------------
# find_conversation_file — locate the current session's .jsonl transcript
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# PR merge-state guard: suppress hook fires for merged/closed PRs
# Two layers:
#   1. Sentinel file: ~/.tmp/HOOK_cr_done_<PR> — agent writes this after
#      confirming CR APPROVED on a merged PR.
#   2. Conversation marker: "PR #N MERGED/CLOSED" in recent transcript.
#
# CR's LLM-context compaction re-embeds stale CHANGES_REQUESTED instructions
# every ~15 min. Sentinel + conversation markers prevent re-delivery by the
# hook itself, but /clear is required to break the agent's internal loop.
# ---------------------------------------------------------------------------

# Short-circuit: if no git repo (no PR context), exit fast without any I/O
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  # No repo — session is not PR-bound, let other hooks run
  :
else
  CONVERSATION_FILE="$(find_conversation_file 2>/dev/null || true)"
fi

if [ -n "${CONVERSATION_FILE:-}" ] && [ -f "$CONVERSATION_FILE" ]; then

  # Layer 1: Check sentinel files for any PR mentioned in full conversation.
  # Use while/read to avoid word-splitting "PR #N" into "PR" + "#N".
  # grep -oh outputs each match on its own line; sort -u deduplicates.
  while IFS= read -r pr_ref; do
    pr_num="${pr_ref#PR #}"
    # Sentinel files have .json suffix: HOOK_cr_done_<pr>.json
    if [ -n "$pr_num" ] && [ -f "$HOME/.tmp/HOOK_cr_done_${pr_num}.json" ]; then
      echo "[UserPromptSubmit] PR #${pr_num} — hook suppressed by sentinel (merged/closed)" >&2
      exit 0
    fi
  done <<< "$(grep -ohE 'PR #[0-9]+' "$CONVERSATION_FILE" 2>/dev/null | sort -u || true)"

  # Layer 2: Conversation marker — suppress if "PR #N MERGED/CLOSED" found
  LAST20="$(tail -n 20 "$CONVERSATION_FILE" 2>/dev/null || true)"
  if echo "$LAST20" | grep -qiE 'PR #[0-9]+ (MERGED|CLOSED)'; then
    PR_STATE="$(echo "$LAST20" | grep -oiE 'PR #[0-9]+ (MERGED|CLOSED)' | tail -1 || true)"
    echo "[UserPromptSubmit] $PR_STATE — hook suppressed by conversation marker" >&2
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# Session health: count messages and warn on large sessions
# ---------------------------------------------------------------------------

# Count non-empty lines in conversation file
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
