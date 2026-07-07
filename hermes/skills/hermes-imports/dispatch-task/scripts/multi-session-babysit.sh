#!/bin/bash
# Multi-session babysit for a fanout of N AO workers spawned for one issue.
# Verified 2026-06-20 (issue #7722 fanout: wa-2420 + wa-2422).
#
# Behavior:
#   - Polls `ao status` every 5 min for all listed sessions.
#   - Posts ONE Slack thread reply every ~15 min with status for ALL sessions.
#   - Posts a Slack thread reply immediately if any session hits terminal state.
#   - Exits when all sessions have reached terminal state OR after MAX_POLLS * SLEEP_SEC.
#
# Required env (caller must export):
#   HERMES_SLACK_BOT_TOKEN — Slack bot token for chat.postMessage
#
# Args:
#   $1 = Slack channel (e.g. C0B9W8D609M)
#   $2 = Slack thread ts (the originating user message)
#   $3 = space-separated AO session IDs (e.g. "wa-2420 wa-2422")
#
# Log: /tmp/<phenotype>-babysit.log
# Done marker: /tmp/<phenotype>-babysit-done
#
# Usage:
#   HERMES_SLACK_BOT_TOKEN="xoxb-..." \
#     ./multi-session-babysit.sh C0B9W8D609M 1781987827.564519 "wa-2420 wa-2422"
#
# PITFALL (verified 2026-06-20, $USER-c2kv dispatch):
#   The shipped scripts are NOT executable by default (-rw-r--r-- in the skill
#   bundle). Calling them via `bash <script>` works, but invoking via `path`
#   fails with "Permission denied" and exits silently after 4 min. Symptom: no
#   "Babysit armed" ack in the Slack thread, ao status confirms workers are
#   healthy, but no status updates ever appear. Three defensive layers below:
#     1. Self-chmod at startup if not executable.
#     2. Bail loudly (NOT silent) if the file still can't run.
#     3. Treat any non-zero startup exit as a hard failure that posts to Slack.

set -u

# Defensive layer 1: self-chmod if the script isn't executable.
if [ ! -x "$0" ]; then
  chmod +x "$0" 2>/dev/null || {
    echo "[$(date -u +%H:%M:%S)] FATAL: $0 is not executable and chmod failed" >&2
    exit 126
  }
fi

CHANNEL="${1:?usage: $0 <channel> <thread_ts> '<session-id> [session-id ...]'}"
THREAD_TS="${2:?usage: $0 <channel> <thread_ts> '<session-id> [session-id ...>'}"
SESSIONS="${3:?usage: $0 <channel> <thread_ts> '<session-id> [session-id ...>'}"

# Validate the Slack token UP FRONT. Under `set -u`, a missing token would
# otherwise blow up on the first post with "unbound variable" rather than a
# clean diagnostic; binding to a sentinel and checking is the safe pattern.
if [[ -z "${HERMES_SLACK_BOT_TOKEN:-}" ]]; then
  echo "[$(date -u +%H:%M:%S)] FATAL: HERMES_SLACK_BOT_TOKEN not set — babysit cannot post" >&2
  exit 3
fi

PHENOTYPE="${PHENOTYPE:-wa-fanout}"
LOG="/tmp/${PHENOTYPE}-babysit.log"
DONE_MARKER="/tmp/${PHENOTYPE}-babysit-done"
MAX_POLLS="${MAX_POLLS:-48}"      # 48 × 5min = 4h
SLEEP_SEC="${SLEEP_SEC:-300}"

post_thread() {
  local msg="$1"
  # Bound the call so a Slack/network stall cannot block the loop. Capture
  # the response so we can surface Slack API errors (ok=false) to the log.
  local resp
  resp=$(curl -sS --connect-timeout 10 --max-time 30 \
    -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer ${HERMES_SLACK_BOT_TOKEN}" \
    -H "Content-type: application/json; charset=utf-8" \
    --data-binary @<(python3 -c "import json,sys; print(json.dumps({'channel':'$CHANNEL','thread_ts':'$THREAD_TS','text':sys.stdin.read()}))" <<<"$msg") 2>&1)
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "[$(date -u +%H:%M:%S)] slack post curl failed rc=$rc" >> "$LOG"
    return 1
  fi
  if ! echo "$resp" | python3 -c 'import sys,json; sys.exit(0 if json.loads(sys.stdin.read()).get("ok") else 1)' 2>/dev/null; then
    echo "[$(date -u +%H:%M:%S)] slack post rejected: $(echo "$resp" | head -c 300)" >> "$LOG"
    return 1
  fi
}

# Track terminal state per session in the marker file
declare_terminal() {
  local sid="$1"
  grep -qE "^${sid}$" "$DONE_MARKER" 2>/dev/null || echo "$sid" >> "$DONE_MARKER"
}

all_done() {
  for sid in $SESSIONS; do
    grep -qE "^${sid}$" "$DONE_MARKER" 2>/dev/null || return 1
  done
  return 0
}

echo "[$(date -u +%H:%M:%S)] babysit starting: sessions=$SESSIONS channel=$CHANNEL thread=$THREAD_TS" > "$LOG"

# Initial ack
post_thread "🔭 Babysit armed for $(echo $SESSIONS | wc -w | tr -d ' ') session(s). Will poll every 5min, summary every 15min."

for i in $(seq 1 $MAX_POLLS); do
  echo "[$(date -u +%H:%M:%S)] poll #$i" >> "$LOG"

  STATUS_OUT=$(cd ~/.openclaw && ~/bin/ao status 2>&1 | grep -E "$(echo $SESSIONS | tr ' ' '|')" | head -20)
  echo "$STATUS_OUT" >> "$LOG"

  for SID in $SESSIONS; do
    LINE=$(echo "$STATUS_OUT" | grep "$SID" || true)
    # NOTE: do NOT include `pr_open` here — opening a PR is a mid-stream
    # milestone, NOT a terminal state. Workers continue through CI/review/green
    # iterations and we want progress updates until they reach merged/closed/
    # done/errored. Listing `pr_open` caused the fanout babysit to stop on the
    # first PR open and miss the rest of the green-loop iterations.
    # Match the single-session babysit terminal set: merged|done|killed|
    # errored|closed|exited|failed. The first poll after terminal detection
    # posts the notice; subsequent polls are silent (declare_terminal gate).
    if echo "$LINE" | grep -qiE "merged|done|killed|errored|closed|exited|failed"; then
      if ! grep -qE "^${SID}$" "$DONE_MARKER" 2>/dev/null; then
        echo "TERMINAL: $SID" >> "$LOG"
        post_thread "🔔 *$SID* terminal: \`\`\`\n$LINE\n\`\`\`"
        declare_terminal "$SID"
      fi
    fi
    if [ -z "$LINE" ]; then
      if ! grep -qE "^${SID}$" "$DONE_MARKER" 2>/dev/null; then
        echo "GONE: $SID" >> "$LOG"
        post_thread "⚠️ *$SID* not in ao status — likely killed or session ended."
        declare_terminal "$SID"
      fi
    fi
  done

  if all_done; then
    echo "all terminal — exiting" >> "$LOG"
    post_thread "✅ All sessions terminal. Final reply coming in next message."
    break
  fi

  # Every 3rd poll (~15 min), post a combined status summary
  if [ $((i % 3)) -eq 0 ]; then
    # Use $'...' so the embedded \n in each segment expands to a real newline
    # at assignment time. Plain "$SUMMARY=..." leaves \n as literal text.
    SUMMARY=$'⏱️ *Status @ poll #'"$i"$'*\n'
    for SID in $SESSIONS; do
      LINE=$(echo "$STATUS_OUT" | grep "$SID" || echo "_missing from ao status_")
      SUMMARY+=$'\n*'"$SID"$'*\n```\n'"$LINE"$'\n```\n'
    done
    post_thread "$SUMMARY"
  fi

  sleep "$SLEEP_SEC"
done

echo "[$(date -u +%H:%M:%S)] babysit loop ended" >> "$LOG"

# If we exited the loop because MAX_POLLS was reached WITHOUT all sessions
# reaching terminal state, the thread would otherwise have no follow-up signal.
# Post a timeout notice so the operator sees the babysit expired.
if [ -f "$LOG" ] && ! grep -q "all terminal — exiting" "$LOG"; then
  REMAINING=""
  for SID in $SESSIONS; do
    grep -qE "^${SID}$" "$DONE_MARKER" 2>/dev/null || REMAINING="$REMAINING $SID"
  done
  REMAINING="${REMAINING# }"
  post_thread "⏰ *Babysit timed out after $((MAX_POLLS*SLEEP_SEC/60))min* without all sessions reaching terminal state. Still non-terminal:$REMAINING. Check \`cd ~/.openclaw && ~/bin/ao status\` for current state."
fi
