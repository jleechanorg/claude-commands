#!/bin/bash
# Single-session babysit loop — polls `ao status` for one session and posts
# progress to a Slack thread every ~5 min until the session reaches terminal
# state (exited/killed/done/merged/closed/errored/failed) or hits MAX_POLLS * SLEEP_SEC.
#
# Usage:
#   ./babysit-one-session.sh <session-id> <bead-id> <slack-channel> <slack-thread-ts> [max_polls=24] [sleep_sec=300]
#
# Example:
#   ./babysit-one-session.sh wa-2428 $USER-ny4j C0AH3RY3DK6 1782000034.157059
#
# Writes:
#   /tmp/<session>-babysit.log   - per-poll status output
#   /tmp/<session>-done          - "TERMINAL" / "GONE" / "TIMEOUT" marker
#   /tmp/<session>-pr-url        - PR URL if found via `gh pr list`
#
# Slack token resolution order:
#   $OPENCLAW_SLACK_BOT_TOKEN -> $SLACK_MCP_XOXB_TOKEN -> $HERMES_SLACK_BOT_TOKEN
#   If none of those are set, posts are skipped (logs still write to /tmp).
#
# PITFALL (verified 2026-06-20, $USER-c2kv dispatch):
#   The shipped scripts are NOT executable by default (-rw-r--r-- in the skill
#   bundle). Calling them via `bash <script>` works, but invoking via `path`
#   fails with "Permission denied" and exits silently after 4 min. Defensive
#   layer below: self-chmod at startup. See multi-session-babysit.sh for the
#   full incident write-up.

set -u

# Defensive layer 1: self-chmod if the script isn't executable.
if [ ! -x "$0" ]; then
  chmod +x "$0" 2>/dev/null || {
    echo "[$(date -u +%H:%M:%S)] FATAL: $0 is not executable and chmod failed" >&2
    exit 126
  }
fi

SESSION="${1:-}"
BEAD="${2:-}"
CHANNEL="${3:-}"
THREAD_TS="${4:-}"
MAX_POLLS="${5:-24}"
SLEEP_SEC="${6:-300}"

if [ -z "$SESSION" ] || [ -z "$BEAD" ] || [ -z "$CHANNEL" ] || [ -z "$THREAD_TS" ]; then
  echo "Usage: $0 <session-id> <bead-id> <slack-channel> <slack-thread-ts> [max_polls] [sleep_sec]"
  exit 2
fi

# Infer project, repo, and worktree from session ID prefix FIRST, then allow
# AO_* env vars to override individual fields. Without this ordering, setting
# only AO_PROJECT would skip prefix inference and leave REPO/WT_PARENT empty,
# causing PR detection to fall back to "/$SESSION" and `gh --repo ""`.
# Options: wa-* -> worldarchitect, jc-* -> jleechanclaw, ao-* -> agent-orchestrator
if [[ "$SESSION" =~ ^wa- ]]; then
  PROJECT="worldarchitect"
  REPO="$GITHUB_REPOSITORY"
  WT_PARENT="$HOME/.worktrees/worldarchitect"
elif [[ "$SESSION" =~ ^jc- ]]; then
  PROJECT="jleechanclaw"
  REPO="jleechanorg/jleechanclaw"
  WT_PARENT="$HOME/.worktrees/jleechanclaw"
elif [[ "$SESSION" =~ ^ao- ]]; then
  PROJECT="agent-orchestrator"
  REPO="jleechanorg/agent-orchestrator"
  WT_PARENT="$HOME/.worktrees/agent-orchestrator"
else
  # Default fallback for unknown prefixes
  PROJECT="worldarchitect"
  REPO="$GITHUB_REPOSITORY"
  WT_PARENT="$HOME/.worktrees/worldarchitect"
fi

# Allow AO_* env vars to override individual fields AFTER prefix inference
PROJECT="${AO_PROJECT:-$PROJECT}"
REPO="${AO_REPO:-$REPO}"
WT_PARENT="${AO_WT_PARENT:-$WT_PARENT}"

LOG="/tmp/${SESSION}-babysit.log"
DONE="/tmp/${SESSION}-done"
PR_URL="/tmp/${SESSION}-pr-url"
TOKEN="${OPENCLAW_SLACK_BOT_TOKEN:-${SLACK_MCP_XOXB_TOKEN:-${HERMES_SLACK_BOT_TOKEN:-}}}"

post_to_thread() {
  local text="$1"
  [ -z "$TOKEN" ] && return 0
  local resp
  resp=$(curl -sS --connect-timeout 10 --max-time 30 \
    -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "$(python3 -c "import json,sys; print(json.dumps({'channel':'$CHANNEL','thread_ts':'$THREAD_TS','text':sys.argv[1]}))" "$text")" 2>&1)
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "[$(date -u +%H:%M:%S)] slack post curl failed rc=$rc" >> "$LOG"
    return 1
  fi
  # Surface Slack API errors (ok=false) to the log so /tmp/<session>-babysit.log
  # shows the rejection reason instead of swallowing it via >/dev/null.
  if ! echo "$resp" | python3 -c 'import sys,json; sys.exit(0 if json.loads(sys.stdin.read()).get("ok") else 1)' 2>/dev/null; then
    echo "[$(date -u +%H:%M:%S)] slack post rejected: $(echo "$resp" | head -c 300)" >> "$LOG"
    return 1
  fi
}

echo "[$(date -u +%H:%M:%S)] babysit starting for $SESSION (poll every ${SLEEP_SEC}s, max $MAX_POLLS polls)" > "$LOG"
post_to_thread ":hourglass: *${BEAD}* / \`${SESSION}\` babysit started (${SLEEP_SEC}s polling, $((MAX_POLLS*SLEEP_SEC/60))min budget)."

for i in $(seq 1 $MAX_POLLS); do
  STATUS_OUT=$(cd ~/.openclaw && ~/bin/ao status --project "$PROJECT" 2>&1 | grep -A 2 "$SESSION" | head -8)
  echo "[$(date -u +%H:%M:%S)] poll #$i" >> "$LOG"
  echo "$STATUS_OUT" >> "$LOG"

  WT="$WT_PARENT/$SESSION"
  PR=""
  if [ -d "$WT" ]; then
    cd "$WT"
    BR=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    LOG_LINES=$(git log --oneline -3 2>/dev/null)
    echo "branch=$BR" >> "$LOG"
    echo "$LOG_LINES" >> "$LOG"
    PR=$(gh pr list --repo "$REPO" --head "$BR" --state all --json number,url --jq '.[0].url // empty' 2>/dev/null)
    [ -n "$PR" ] && echo "$PR" > "$PR_URL"
  fi

  if echo "$STATUS_OUT" | grep -qiE "exited|killed|done|merged|closed|errored|failed"; then
    echo "TERMINAL" > "$DONE"
    echo "[$(date -u +%H:%M:%S)] terminal state detected" >> "$LOG"
    FINAL_MSG=":*${BEAD} done* — \`${SESSION}\` exited. PR: ${PR:-none yet}. Proof will follow up in thread if not already."
    post_to_thread "$FINAL_MSG"
    break
  fi

  PROGRESS=":mag: *${BEAD}* poll #${i} — \`${SESSION}\` status: $(echo "$STATUS_OUT" | head -1 | xargs)"
  [ -n "$PR" ] && PROGRESS="$PROGRESS — PR: $PR"
  post_to_thread "$PROGRESS"

  sleep "$SLEEP_SEC"
done

if [ ! -f "$DONE" ]; then
  echo "TIMEOUT" > "$DONE"
  post_to_thread ":warning: *${BEAD}* babysit hit $((MAX_POLLS*SLEEP_SEC/60))min timeout without terminal state. Check \`${SESSION}\` directly with: \`cd ~/.openclaw && ao status --project $PROJECT\`"
fi
