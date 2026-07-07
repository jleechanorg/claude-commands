# Manual babysit template (when the canonical script is broken)

Use this template when `scripts/babysit-one-session.sh` is misbehaving
(known bug as of 2026-07-06 — its `post_to_thread` produces
Python syntax errors). The recommended modern alternative is a
`cronjob` whose prompt polls state and posts via
`mcp__slack__conversations_add_message` — but if you need a bash
loop instead, copy this template and adapt.

## When to use

- The canonical script's Slack posts silently fail
- You need a one-shot babysit that can be inspected via plain shell
- You're babysitting a session that needs custom polling logic
  (e.g. reading a worktree-local evidence bundle)

## Template

```bash
#!/bin/bash
# Manual babysit template — adapt SESSION/BEAD/CHANNEL/THREAD_TS/PR_URL_TEMPLATE
set -u
SESSION=wa-NNNN
BEAD=rev-XXXX
CHANNEL=C0XXXXXXXXX
THREAD_TS=1234567890.123456
REPO=jleechanorg/<repo>
WT=$HOME/.worktrees/<project>/$SESSION
LOG=/tmp/${SESSION}-babysit.log
DONE=/tmp/${SESSION}-done
MAX_POLLS=24
SLEEP_SEC=300
AO=$HOME/.nvm/versions/node/v22.22.0/bin/ao  # see dispatch-task SKILL.md §"Broken ~/bin/ao symlink"

# Helper: build JSON payload as a string so curl receives a valid body.
# The inline $'\n' bash quoting in the original script's `post_to_thread`
# is what breaks — keep Python source on stdin, not in a -c arg.
mkjson() {
  python3 <<PYEOF
import json, sys
text = sys.argv[1]
print(json.dumps({"channel": "$CHANNEL", "thread_ts": "$THREAD_TS", "text": text}, ensure_ascii=False))
PYEOF
  "$1"
}

# IMPORTANT: direct curl with $HERMES_SLACK_BOT_TOKEN returns invalid_auth
# (verified 2026-07-06). Only mcp__slack__conversations_add_message works.
# This bash-side post_to_thread will SILENTLY FAIL. Use the cronjob pattern
# from SKILL.md §"Env Slack tokens return `invalid_auth`" instead.
post_to_thread() {
  local text="$1"
  local payload
  payload=$(mkjson "$text")
  local resp
  resp=$(curl -sS --connect-timeout 10 --max-time 30 \
    -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer ***" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "$payload" 2>&1)
  echo "[$(date -u +%H:%M:%S)] post: $text" >> "$LOG"
  echo "[$(date -u +%H:%M:%S)] resp: $(echo "$resp" | head -c 200)" >> "$LOG"
  if echo "$resp" | grep -q '"error":"invalid_auth"'; then
    echo "[$(date -u +%H:%M:%S)] WARN: token invalid, posts will fail. Use cronjob pattern instead." >> "$LOG"
  fi
}

echo "[$(date -u +%H:%M:%S)] babysit starting for $SESSION" > "$LOG"

for i in $(seq 1 $MAX_POLLS); do
  STATUS_OUT=$($AO status -p $(echo "$SESSION" | sed 's/-[0-9]*$//' | sed 's/^wa$/worldarchitect/; s/^jc$/jleechanclaw/; s/^ao$/agent-orchestrator/') 2>&1 | grep -A 2 "$SESSION" | head -8)
  echo "--- poll #$i at $(date -u +%H:%M:%S) ---" >> "$LOG"
  echo "$STATUS_OUT" >> "$LOG"

  PR=""
  BR=""
  if [ -d "$WT" ]; then
    BR=$(git -C "$WT" rev-parse --abbrev-ref HEAD 2>/dev/null)
    PR=$(gh pr list --repo "$REPO" --head "$BR" --state all --json number,url --jq '.[0].url // empty' 2>/dev/null)
    [ -n "$PR" ] && echo "$PR" > "/tmp/${SESSION}-pr-url"
  fi

  if echo "$STATUS_OUT" | grep -qiE "exited|killed|done|merged|closed|errored|failed"; then
    echo "TERMINAL" > "$DONE"
    post_to_thread "✅ *${BEAD}* — \`${SESSION}\` reached terminal state. Branch \`${BR}\`. PR: ${PR:-none yet}."
    break
  fi

  PROGRESS="🔍 *${BEAD}* poll #${i} — \`${SESSION}\`: $(echo "$STATUS_OUT" | head -1 | xargs)"
  [ -n "$PR" ] && PROGRESS="$PROGRESS | PR: $PR"
  [ -n "$BR" ] && PROGRESS="$PROGRESS | branch: \`${BR}\`"
  post_to_thread "$PROGRESS"

  sleep "$SLEEP_SEC"
done

if [ ! -f "$DONE" ]; then
  echo "TIMEOUT" > "$DONE"
  post_to_thread "⚠️ *${BEAD}* babysit hit $((MAX_POLLS*SLEEP_SEC/60))min timeout without terminal state."
fi
```

## Recommended modern alternative (cronjob-based)

Instead of the bash babysit, use the canonical cron-driven pattern
that posts via the working `mcp__slack__conversations_add_message`
tool. See SKILL.md §"Env Slack tokens return `invalid_auth`" for why
this is preferred over curl-based posting.

```bash
# Create a polling cron that posts via the gateway's mcp__slack tool
# (the bash token will fail, but the cron job's prompt can use mcp__slack).
hermes cron create \
  --schedule "5m" \
  --repeat 60 \
  --name "babysit $SESSION" \
  --prompt 'Check $AO status for session $SESSION on project <project>.
  If PR is MERGED/CLOSED, post a final closeout to channel C0BDAMWQQJK thread 1783368232.020759
  using mcp__slack__conversations_add_message, then `cronjob action=remove job_id=$CRON_JOB_ID`.
  Otherwise post a brief status ping with colored icon (🟢/🟡/🔴/🔵).'
```

Provenance: written 2026-07-06 after wa-3157 dispatch (PR #8063,
issue #8062 story choice text leak repro) hit the broken canonical
babysit + invalid-auth tokens. The cronjob path is what we actually
used in production.