# No-Agent Hermes Cron PR Watchdog

**Verified 2026-07-20, $GITHUB_REPOSITORY PR #8466.**

A pattern for watching a single PR's CI state without spinning up an AO worker or burning LLM tokens on every poll. Uses `hermes cron create --no-agent --script` to run a bash script on a fixed cadence; the script exits silently except when the PR's state actually changes (or transitions to terminal).

## Why this exists

The companion `babysit-stale-watchdog` skill covers babysits that spawn AO workers. Not every PR needs a worker — for small, well-understood PRs that just need CI to clear, the `no-agent` watchdog pattern is cheaper, simpler, and doesn't depend on AO lifecycle plumbing.

## When to use

- Single PR is open on a real branch (you control the branch)
- CI is the only blocker (no review iteration, no scope changes needed)
- You want a Slack-thread ping on state transitions only
- You don't need LLM judgment on each poll — pure state machine

## Recipe

```bash
# 1. Author the script in ~/.hermes/scripts/<short-name>.sh (hermes cron
#    requires relative paths under that dir). Self-chmod at the top.

cat > ~/.hermes/scripts/wa-pr-<N>-watch.sh <<'SCRIPT'
#!/bin/bash
set -u
PR_NUM=<N>
CHANNEL="<CHAN_ID>"            # e.g. C09GRLXF9GR
THREAD_TS="<THREAD_TS>"        # e.g. 1784235989.925899
REPO="<OWNER>/<REPO>"          # e.g. $GITHUB_REPOSITORY
STATE_DIR="/tmp/wa-pr-${PR_NUM}"
STATE_FILE="${STATE_DIR}/state.txt"
mkdir -p "$STATE_DIR"

LAST_STATE=""
[ -f "$STATE_FILE" ] && LAST_STATE=$(cat "$STATE_FILE")

# Use gh CLI (it goes through its own auth — works under cron with no env)
PR_JSON=$(gh pr view "$PR_NUM" --repo "$REPO" --json state,mergeable,statusCheckRollup 2>/dev/null)
if [ -z "$PR_JSON" ]; then
    # Silent on rate-limit (cron watchdog pattern)
    exit 0
fi

CURRENT_STATE=$(echo "$PR_JSON" | jq -r '.state')
FAILING=$(echo "$PR_JSON" | jq -r '[.statusCheckRollup[]? | select(.state=="FAILURE") | .name] | join(", ")')
PENDING=$(echo "$PR_JSON" | jq -r '[.statusCheckRollup[]? | select(.state=="PENDING" or .state=="QUEUED") | .name] | length')

post_to_slack() {
    local msg="$1"
    local token="${HERMES_SLACK_BOT_TOKEN:-${SLACK_MCP_XOXB_TOKEN:-${SLACK_USER_TOKEN:-}}}"
    [ -z "$token" ] && { echo "$msg"; return; }
    local payload=$(jq -nc --arg ch "$CHANNEL" --arg ts "$THREAD_TS" --arg text "$msg" \
        '{channel:$ch, thread_ts:$ts, text:$text}')
    curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json; charset=utf-8" \
        -d "$payload" > /dev/null 2>&1
}

if [ "$LAST_STATE" != "$CURRENT_STATE" ]; then
    case "$CURRENT_STATE" in
        OPEN)
            if [ -z "$FAILING" ] && [ "${PENDING:-0}" = "0" ]; then
                post_to_slack "✅ PR #${PR_NUM} CI fully green — mergeable=$(echo "$PR_JSON" | jq -r '.mergeable'). Ready for merge review."
            else
                post_to_slack "⏳ PR #${PR_NUM} state=$CURRENT_STATE, mergeable=$(echo "$PR_JSON" | jq -r '.mergeable'), pending=${PENDING}, failing=[$FAILING]."
            fi
            ;;
        MERGED)
            post_to_slack "🎉 PR #${PR_NUM} MERGED. Closing loop."
            echo "$CURRENT_STATE" > "$STATE_FILE"
            exit 0  # terminal
            ;;
        CLOSED)
            post_to_slack "🚫 PR #${PR_NUM} CLOSED (not merged). Closing loop."
            echo "$CURRENT_STATE" > "$STATE_FILE"
            exit 0
            ;;
    esac
    echo "$CURRENT_STATE" > "$STATE_FILE"
fi

exit 0
SCRIPT
chmod +x ~/.hermes/scripts/wa-pr-<N>-watch.sh

# 2. Create the cron. CRITICAL: --script takes just the FILENAME, not the
#    absolute path. --no-agent skips the LLM entirely.

hermes cron create 'every 6m' \
  --name "wa-pr-<N>-watch" \
  --deliver "slack:<CHAN>:<THREAD_TS>" \
  --script "wa-pr-<N>-watch.sh" \
  --no-agent
```

The cron job ID lands in `hermes cron list` output. Pass it back to the user in the originating Slack thread so they can find/replay/remove it.

## What this catches that AO-worker babysits do not

- **Rate-limit silent exits**: when `gh` is rate-limited, `PR_JSON` is empty, and the script exits 0 without posting. This is the watchdog pattern — silently skip and try next tick.
- **State-machine transitions only**: no chatty "still running" pings. One message per state change.
- **No LLM cost**: `no-agent` means the script IS the job. Zero tokens burned.

## Pitfalls

- **`--script` requires relative filename** under `~/.hermes/scripts/`. Absolute or `~/...` paths fail with `Failed to create job: Script path must be relative to ~/.hermes/scripts/`.
- **`gh` rate-limit fallback to silent exit** is the watchdog pattern — do NOT replace it with a noisy "could not fetch PR" Slack message, that floods the thread on every tick during a 503 storm.
- **`gh pr view --json` returns stale data on rate-limit**: if it errors, the script exits silently. Do not fall back to REST API inside the script — the cron will recover on the next tick once the rate-limit window closes.
- **Slack token resolution order matters**: prefer `$HERMES_SLACK_BOT_TOKEN` (most common), then `$SLACK_MCP_XOXB_TOKEN`, then `$SLACK_USER_TOKEN` (xoxp). If none are set, the script prints to stdout only — useful for local debugging, useless for production.
- **Self-cancel on terminal state is in-script, not in cron-jobs**: the script writes `MERGED`/`CLOSED` to its state file and exits 0. The `babysit-stale-watchdog` companion script (`~/.hermes/scripts/babysit_stale_watchdog.py`, run by launchd every 30 min) is what actually disables a stale cron once the PR is terminal for ≥30 min. Both layers are needed — the in-script exit is fast-feedback, the watchdog is the safety net.
- **Cadence**: 6 min is a good default for "PR CI should clear in 30-60 min" workflows. Faster cadences (1m, 2m) burn Slack API quota on no-op ticks; slower (15m, 30m) miss the green→merged window.

## Worked example

Verified 2026-07-20 for PR #8466:

1. Pushed empty commit `7041776da1` to retrigger CI after transient GitHub 503
2. `gh pr view 8466 --json state,...` confirmed `state=OPEN` and 7 queued check-runs
3. Created `~/.hermes/scripts/wa-pr-8466-babysit.sh` with the recipe above
4. `hermes cron create 'every 6m' --name 'wa-pr-8466-babysit' --deliver 'slack:C09GRLXF9GR:1784235989.925899' --script 'wa-pr-8466-babysit.sh' --no-agent` → job `124ad03896f5`
5. Cron self-disables within 30 min of PR transition to MERGED via the companion `babysit-stale-watchdog` script

Final delivery to user included the cron job ID `124ad03896f5` in the Slack thread reply so they could find/remove/replay it later.

## Pair with

- `~/.hermes/scripts/babysit_stale_watchdog.py` (launchd, every 30 min) — disables the cron when the PR is terminal
- `drive-pr-to-green` v2.5.6 — the empty-commit retrigger pattern that typically precedes a watchdog cron
- `gh-actions-transient-failure-diagnosis` — the diagnostic that determines "is this a real CI failure or a flake?"