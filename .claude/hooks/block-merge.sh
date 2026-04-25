#!/usr/bin/env bash
# block-merge.sh — Repo-level PreToolUse hook for your-project.com
#
# Hard-blocks any agent from executing merge commands without explicit
# human "MERGE APPROVED" in the conversation.
#
# Incidents:
#   PR #6161 — merged without human approval (question ≠ directive)
#   PR #6240 — polish agent auto-merged despite CLAUDE.md prohibition
#
# This hook travels with the repo — any agent in any worktree/clone
# is protected automatically.
#
# Wired in .claude/settings.json PreToolUse:Bash hooks array.

set -euo pipefail

INPUT=$(cat)

# Guard: if jq is unavailable or JSON is malformed, pass through (non-blocking)
if ! command -v jq >/dev/null 2>&1; then
  printf '%s\n' "$INPUT"
  exit 0
fi

TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)

# Only intercept Bash tool calls
[[ "$TOOL_NAME" != "Bash" ]] && { printf '%s\n' "$INPUT"; exit 0; }

COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

# Detect merge commands anywhere in the string (covers chaining: &&, ;, bash -c, eval).
#   gh pr merge ...
#   gh api repos/.../pulls/N/merge  (including $VAR PR numbers)
#   curl/wget to GitHub merge REST endpoint
#
# Allow-list: commands that start with common inspection/doc tools may embed the
# merge substring (e.g. grep/git log --grep) without executing a merge.
MERGE_ANYWHERE='gh[[:space:]]+pr[[:space:]]+merge|gh[[:space:]]+api[[:space:]].*pulls/[^[:space:]/]+/merge|(curl|wget)[[:space:]].*pulls/[^[:space:]/]+/merge'
DOC_SAFE_PREFIX='^[[:space:]]*(#|echo|printf|grep|cat|sed|awk|jq|git[[:space:]]+(log|show|diff|grep|rev-parse|config|blame)|gh[[:space:]]+pr[[:space:]]+(view|diff|status|checks|list))'
if printf '%s' "$COMMAND" | grep -qE "$MERGE_ANYWHERE"; then
  # Doc-safe allow-list applies per shell segment. Applying it to the full string
  # would bypass: `grep ... && gh pr merge` (whole line starts with grep).
  # Pipeline: `echo x | gh pr merge` must not pass just because the left side is echo.
  PIPE_MERGE='.*\|[[:space:]]*(gh[[:space:]]+pr[[:space:]]+merge|gh[[:space:]]+api[[:space:]].*pulls/[^[:space:]/]+/merge|(curl|wget)[[:space:]].*pulls/[^[:space:]/]+/merge)'
  MERGE_UNSAFE=0
  # Newlines can hide a merge after a doc-looking first line; flatten for pipe detection.
  CMD_FLAT=$(printf '%s' "$COMMAND" | tr '\n' ' ')
  if printf '%s' "$CMD_FLAT" | grep -qE "$PIPE_MERGE"; then
    MERGE_UNSAFE=1
  else
    US=$(printf '\037')
    _split=$(printf '%s' "$COMMAND" | sed "s/[[:space:]]*||[[:space:]]*/${US}/g; s/[[:space:]]*&&[[:space:]]*/${US}/g; s/[[:space:]]*;[[:space:]]*/${US}/g")
    _oldifs=$IFS
    set -f
    IFS="$US"
    # shellcheck disable=SC2206
    _segments=(${_split})
    set +f
    IFS=$_oldifs
    for seg in "${_segments[@]}"; do
      seg_trim=$(printf '%s' "$seg" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      [[ -z "$seg_trim" ]] && continue
      if ! printf '%s' "$seg_trim" | grep -qE "$MERGE_ANYWHERE"; then
        continue
      fi
      while IFS= read -r _line || [[ -n "${_line:-}" ]]; do
        _line_trim=$(printf '%s' "$_line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        [[ -z "$_line_trim" ]] && continue
        if printf '%s' "$_line_trim" | grep -qE "$MERGE_ANYWHERE"; then
          if ! printf '%s' "$_line_trim" | grep -qE "$DOC_SAFE_PREFIX"; then
            MERGE_UNSAFE=1
            break 2
          fi
        fi
      done <<< "$(printf '%s' "$seg_trim")"
    done
  fi
  if [[ "$MERGE_UNSAFE" -eq 0 ]]; then
    printf '%s\n' "$INPUT"
    exit 0
  fi
  echo "========================================" >&2
  echo "BLOCKED: Merge command in your-project.com" >&2
  echo "" >&2
  echo "  $COMMAND" >&2
  echo "" >&2
  echo "This repo requires explicit human 'MERGE APPROVED'" >&2
  echo "before any merge. Report readiness and STOP." >&2
  echo "" >&2
  echo "To merge, ask the human to run:" >&2
  echo "  ! gh pr merge <N> --squash" >&2
  echo "========================================" >&2
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"BLOCKED: Merge command in your-project.com requires explicit human MERGE APPROVED. Report readiness and STOP. To merge, ask the human to run: ! gh pr merge <N> --squash"}}'
  exit 0
fi

printf '%s\n' "$INPUT"
