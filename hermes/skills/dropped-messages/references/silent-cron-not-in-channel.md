# Silent cron blindness — bot removed from channel

**Class:** recurring, silent, multi-hour crash. NOT a routing bug. NOT a token bug. The cron runs perfectly; the Slack API returns `not_in_channel`; the script swallows the error and reports `actioned=0 skipped=0`.

**Bug-ref:** Slack C09GRLXF9GR ts 1784196782.877209, 2026-07-16. ~4h+ window where `dropped-thread-followup.sh` ran every 1800s producing zero action, no Slack alert, and the companion `dropped-thread-watcher-of-watchers.sh` happily reported `ok launchd=loaded log_age=739s` because the launchd job WAS running.

## Symptom fingerprint (any 3+ → suspect this)

```
log: "[YYYY-MM-DDThh:mm:ss]   Failed to fetch threads for $channel"
log: "Done — actioned=0 skipped=0"  every tick
launchctl print: state=not running, last exit code=0, runs=N (plenty)
watcher log: ok launchd=loaded log_age=NNNNs (silent green)
DRY_RUN=1 + manual run: zero nudges (correct behavior of broken script, NOT a bug-fix signal)
```

## Root cause (always Slack-side, never launchd-side)

The bot used by the script (`mcp_agent_mail` U0A4G7LDJ4R by default for `dropped-thread-followup.sh`) lost membership in 1+ of the SCAN_CHANNELS. `conversations.history` returns:

```json
{"ok":false,"error":"not_in_channel","warning":"missing_charset"}
```

`auth.test` still succeeds (bot token is valid); `conversations.info` still returns metadata for public channels regardless of membership. Only `conversations.history` / `conversations.replies` / `conversations.list` (for full visibility) reveal the lost-membership state.

## Why the script hides this (the recurring pattern)

Three layers of error-swallowing, each individually defensible but lethal in combination:

1. **curl stderr → /dev/null** — `-s` + `2>/dev/null` hides network errors
2. **jq parse failure** — `response | jq -r '.foo'` on a `{"ok":false}` body returns empty/null, doesn't throw
3. **`|| return 1` + caller-side `log "  Failed to fetch threads for $channel"`** — caller has no access to the actual error string; the most specific signal `jq -r .error` is one layer up, not propagated

The bare channel-id log line is **operationally indistinguishable** from a "no dropped threads this tick" success — both look like `actioned=0 skipped=0`.

## Diagnostic recipe (30 seconds)

```bash
TOK=$(awk -F'"' '/^export SLACK_BOT_TOKEN=/{print $2}' ~/.bashrc)

# 1. Auth check — proves token is valid (almost always green)
curl -sf -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $TOK" | jq -r '.user_id, .bot_id'

# 2. Membership audit — the smoking gun
curl -sf "https://slack.com/api/conversations.list?types=public_channel,private_channel&exclude_archived=true&limit=200" \
  -H "Authorization: Bearer $TOK" \
  | jq -r '.channels[] | select(.is_member==true) | "\(.id) \(.name)"'

# 3. Per-channel probe — exposes not_in_channel explicitly
for ch in C09GRLXF9GR C0AH3RY3DK6 C0AJ3SD5C79; do
  curl -sf -X POST https://slack.com/api/conversations.history \
    -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
    -d "{\"channel\":\"$ch\",\"limit\":1}" \
    | jq -r "\"$ch \(.ok) \(.error // \"no_err\")\""
done
```

Expected smoking-gun line: `<CHANNEL_ID> false not_in_channel`.

## In-flight remediation (apply now)

```bash
TOK=$(awk -F'"' '/^export SLACK_BOT_TOKEN=/{print $2}' ~/.bashrc)
for ch in C09GRLXF9GR C0AH3RY3DK6 C0ALSKLU9KM C0AKALZ4CKW; do
  curl -sf -X POST https://slack.com/api/conversations.join \
    -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
    -d "{\"channel\":\"$ch\"}" | jq -r "\"$ch \(.ok) \(.error // \"no_err\")\""
done
```

DMs (`D...` channel IDs) cannot be `join`-ed via bot token; they're handled separately and the script's `SKIP standalone (DM channel)` branch already covers that.

## Durable fix (3 layers — required for class-level fix)

### Layer 1: surface the actual Slack error in the log

```bash
# In fetch_recent_threads, replace:
#   response="$(curl ...)" || return 1
# with:
response="$(curl ...)" || return 1
local _slack_err
_slack_err="$(echo "$response" | jq -r '.error // empty' 2>/dev/null)"
if [[ -n "$_slack_err" ]]; then
  echo "$_slack_err" >&2  # caller can pick up via 2>&1
  return 2                 # distinct exit code = "Slack rejected"
fi
```

### Layer 2: auto-rejoin on `not_in_channel`, alert on hard failure

In the main loop, distinguish exit codes:

```bash
threads=$(fetch_recent_threads "$channel" 2>/tmp/_fetch_err.$$)
case $? in
  2) local _err=$(cat /tmp/_fetch_err.$$)
     if [[ "$_err" == "not_in_channel" ]]; then
       log "  bot not in $channel — auto-rejoining"
       curl -sf -X POST https://slack.com/api/conversations.join \
         -H "Authorization: Bearer $SLACK_TOKEN" \
         -H "Content-Type: application/json" \
         -d "{\"channel\":\"$channel\"}" > /dev/null
       threads=$(fetch_recent_threads "$channel") || { log "  rejoin failed"; continue; }
     else
       log "  Slack error $_err on $channel"
       # post ops alert to HERMES_OPS_SLACK_CHANNEL with the channel+error
     fi ;;
  *) log "  Failed to fetch threads for $channel"; continue ;;
esac
```

### Layer 3: watcher-of-watchers must assert progress, not just liveness

`~/.hermes/scripts/dropped-thread-watcher-of-watchers.sh` currently only checks `launchctl state=loaded` + `log_age < 1.5×StartInterval`. Both green even when the script is silently broken. Add a third gate:

```bash
# Pseudocode — adapt to actual script's grep pattern
local _recent_done_count
_recent_done_count=$(grep -c "Done — actioned=" "$log_file" | tail -50)
if [[ "$_recent_done_count" -ge 3 ]]; then
  # Last 3 ticks all reported actioned=0 — could be legit (no drops) OR broken bot
  local _recent_fail_count
  _recent_fail_count=$(grep -c "Failed to fetch threads" "$log_file" | tail -50)
  if [[ "$_recent_fail_count" -ge 3 ]]; then
    post_alert "$WATCH_TARGET_LABEL silent — last 3 ticks failed to fetch"
  fi
fi
```

## Anti-patterns to avoid

- **Don't blame launchd.** `state=not running last exit code=0` is the symptom of `KeepAlive{SuccessfulExit=false}` working correctly for a script that exits 0 immediately. The script IS running; its Slack calls are failing.
- **Don't trust `auth.test` alone.** It proves token validity, not membership.
- **Don't add a `Dry-Run` workaround.** `DRY_RUN=1` runs the same broken fetch path and reports zero nudges — indistinguishable from "no drops in lookback window."
- **Don't change the SCAN_CHANNELS list.** Removing the missing channels hides the symptom, doesn't fix the membership rot.
- **Don't assume a token rotation.** Run `auth.test` first; if green, the problem is downstream (membership, scope, channel-archived).

## Files affected (durable fix)

- `~/.hermes/scripts/dropped-thread-followup.sh` lines ~1303-1352 (`fetch_thread_messages`, `fetch_recent_threads`), ~1357 (`fetch_standalone_user_messages`), ~1578-1582 (main loop error swallowing)
- `~/.hermes/scripts/dropped-thread-watcher-of-watchers.sh` — add progress gate
- `~/.hermes/launchd/ai.hermes.schedule.dropped-thread-followup.plist` — no change
- `~/.hermes/launchd/ai.hermes.schedule.dropped-thread-watcher.plist` — possibly tighten `WATCH_LOG_MAX_AGE` from 5400 to 1800

## Companion checklist for next incident

- [ ] `auth.test` ok?
- [ ] `conversations.list` shows `is_member=true` for each SCAN_CHANNEL?
- [ ] Per-channel `conversations.history limit=1` returns ok?
- [ ] Recent log has any "Done — actioned > 0 OR skipped > 0" line? If neither for 3+ ticks → broken
- [ ] Did the bot get removed by workspace admin? (User removed from app, OAuth re-prompt, scope change)
- [ ] Is there a Slack workspace re-org / new install event in the last 24h?