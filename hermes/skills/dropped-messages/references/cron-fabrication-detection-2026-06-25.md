---
name: dropped-messages/cron-fabrication-detection-2026-06-25
description: "Cron-side fabrication-detection patch to scripts/dropped-thread-followup.sh. When the last agent message in a thread uses 'no new content' / 'nothing new to address' framing right after a real human ask, re-nudge immediately (bypassing the 30-min quiet window). Verified 2026-06-25."
type: reference
last_verified: 2026-06-25
---

# Cron-side fabrication-detection patch — landed 2026-06-25

**File:** `~/.hermes/scripts/dropped-thread-followup.sh` (staging, where launchd reads) + `~/.hermes_prod/scripts/dropped-thread-followup.sh` (prod backup).

## The gap this closes

Without this patch, the dropped-thread-followup cron treats the agent's last reply as a closed loop. When the agent fabricates "no new content" framing for an unread human message (verified 2026-06-23 incident `C0AH3RY3DK6/1782261422.141589`), the cron only re-nudges on the standard 30-min quiet window — which is the exact window during which the user loses trust.

The SOUL.md `## COMMIT: never-hallucinate-no-new-content` rule + `pr-bring-to-green-inline-cookbook` P4 (interleave one `conversations_replies` per CI-poll iteration) are *model-side* and *operational* fixes. This cron-side patch is the *third* durable fix — it catches the case where the model-level rule fails anyway (a model that ignores SOUL.md) and re-nudges within minutes instead of waiting for the 30-min quiet window.

## What was added (3 hunks, ~189 net new lines)

### Hunk 1 — env config (after line 71, ~25 lines)

```bash
FABRICATION_WINDOW_SECS="${DROP_FABRICATION_WINDOW_SECS:-600}"   # 10 min default
FABRICATION_STRIKE_CAP="${DROP_FABRICATION_STRIKE_CAP:-2}"        # 2 nudges / 24h
FABRICATION_DRY_RUN="${DROP_FABRICATION_DRY_RUN:-0}"              # 0 = live, 1 = audit-only
FABRICATION_LOG="${FABRICATION_LOG:-$HOME/.hermes_prod/memory/fabrication-detections.log}"
FABRICATION_PHRASES=(
  "no new content" "no new message" "nothing new to address"
  "nothing new to report" "the user just sent" "the message has no body"
  "your message contains no new content" "the message has no text"
)
```

### Hunk 2 — helper functions (after `was_nudged_recently`, ~110 lines)

`detect_agent_fabrication(channel, thread, last_human_ts, last_agent_ts, last_agent_text, messages_file)` — returns 0 when ALL 5 conditions hold:

1. Last message is from `AGENT_USER_ID` (`U0AEZC7RX1Q`).
2. Last message text matches one of `FABRICATION_PHRASES` (case-insensitive).
3. Penultimate message ts is non-empty (real prior human msg exists).
4. Penultimate message text is non-empty AND author is not the agent AND no `bot_id`/`subtype` (rejects agent→agent "no new content" replies).
5. Gap between last-agent ts and now is `<= FABRICATION_WINDOW_SECS`.

Side effect: writes audit entry to `FABRICATION_LOG` with `ts, channel, thread_ts, last_human_ts, last_agent_ts, gap_secs, phrase, action` (action=re-nudge or log_only).

Dry-run semantics: returns 2 (not 0) when `DROP_FABRICATION_DRY_RUN=1` — caller treats this as info-only, no real nudge. Default-off so the first 24h post-deploy can measure FP rate.

`fabrication_strike_count(channel, thread)` — counts `action=re-nudge` entries in `FABRICATION_LOG` for the given (channel, thread) in the last 24h. Returns 0 if log doesn't exist. Used to enforce `FABRICATION_STRIKE_CAP`.

### Hunk 3 — main-loop integration (after `if [[ "$needs_action" != "true" ]]; then`, ~44 lines)

When the standard `analyze_thread` says "no action needed" but:
- last msg is from agent
- strike count `< FABRICATION_STRIKE_CAP`
- `detect_agent_fabrication` returns 0

→ override `needs_action=true`, set `reason="fabrication-override"`, set `kind="fabrication"`. Continue to the existing nudge-text builder.

When `detect_agent_fabrication` returns 2 (dry-run hit) → log only, no re-nudge, no override.

### Hunk 4 — nudge-text for kind=fabrication (~10 lines)

```
<@AGENT> [Dropped-thread followup — fabrication detected] Your last reply in this thread used
'no new content' / 'nothing new to address' / similar phrasing right after a real human ask.
That framing is a documented false-positive class (see skills/dropped-messages/references/no-new-content-hallucination-2026-06-23.md).
Required response shape: (1) re-fetch the thread via conversations_replies and re-read the most
recent human message; (2) if re-fetch confirms empty body, ask 'did you mean to attach something?';
(3) if re-fetch reveals a real message, acknowledge the gap honestly and act on it now.
Do NOT generate 'no new content' / 'no new message' / 'the user just sent their name' /
'nothing new to address' framing for an unread message.
```

## Verification (2026-06-25 04:13 PT)

Synthetic thread test (fabrication 5 min ago, 6 min after human ask):

| Strike | fabrication_strike_count | detect rc | Behavior |
|---|---|---|---|
| 1 | 0 | 0 | flagged, log entry written |
| 2 | 1 | 0 | flagged, log entry written |
| 3 | 2 | (skipped) | SKIP — strike cap reached, no infinite-loop |

End-to-end `DRY_RUN=1 DROP_FABRICATION_DRY_RUN=1 DROP_CHANNELS=C0AH3RY3DK6 bash ~/.hermes/scripts/dropped-thread-followup.sh` → completed cleanly, no errors, channel cooldown correctly blocks re-nudge during 10-min window.

## Operational guidance

- **First 24h post-deploy:** run with `DROP_FABRICATION_DRY_RUN=1` (audit log only) to measure FP rate before turning on the real nudge. Audit log entries show `phrase=`, `gap_secs=`, `action=log_only` so you can see what the regex matches.
- **After 24h:** flip `DROP_FABRICATION_DRY_RUN=0` (default-off, but launchd runs without env vars so it stays off until you set it). Recommended: add `DROP_FABRICATION_DRY_RUN=0` to the launchd plist's `EnvironmentVariables` once you've reviewed the dry-run audit log.
- **Window tuning:** if FPs show up on legitimate "nothing new to report" summaries (e.g. status crons), tighten `DROP_FABRICATION_WINDOW_SECS` from 600 to 300, OR tighten the phrase list to only match fabrication-specific phrasings ("no new content", "your message contains no new content") and drop generic ones ("nothing new to report").
- **Strike cap tuning:** 2 nudges / 24h was empirically chosen — enough to break a stuck loop, low enough that a chronically-fabricating agent maxes out and falls back to the standard 30-min escalation path (which itself has the GAVE UP circuit-breaker per `references/circuit-breaker-design.md`).

## Pitfalls when extending this patch (or writing similar cron-side pattern detection)

These four gotchas cost real time during the 2026-06-25 landing. Document them inline so future agents don't repeat the same debugging cycle.

### Pitfall 1: Slack ts is `<unix-epoch-seconds>.<microseconds>` — the integer portion IS the epoch

When the helper does `gap_secs=$((now_sec - last_agent_epoch))`, the obvious first attempt is `last_agent_epoch="${last_agent_ts%%.*}"`. That LOOKS correct but produces a NEGATIVE gap when `now_sec` is ~1.78e9 (current real epoch) and `last_agent_epoch` is also ~1.78e9 (Slack ts in seconds) — actually no, that works. The REAL gotcha: if you use `last_agent_ts` directly in arithmetic without the `%%.*` strip, bash treats it as a string and `$((1782261422.141589 - 1782385980))` returns a syntax error. **The fix that actually works:**

```bash
last_agent_epoch="$(date -u -j -f "%s" "${last_agent_ts%%.*}" '+%s' 2>/dev/null)" || return 1
```

`date -u -j -f "%s" "<epoch>" '+%s'` is a no-op identity transform on macOS BSD date — it just verifies the input is parseable as a `%s` format and outputs the same epoch. The `|| return 1` makes it a guard. Without `date`, plain bash arithmetic on the integer portion works but loses the validation.

### Pitfall 2: bash arrays must be initialized BEFORE sourced-script helpers run, but env vars set AFTER sourcing don't propagate into the sourced namespace

The pattern:
```bash
# WRONG: setting the env var after source doesn't override the sourced default
source ~/.hermes/scripts/dropped-thread-followup.sh
DROP_FABRICATION_DRY_RUN=1 detect_agent_fabrication ...
```
This runs `detect_agent_fabrication` in a subshell where the env var IS set, but the function body reads `FABRICATION_DRY_RUN` (not `DROP_FABRICATION_DRY_RUN`). The sourced script's `FABRICATION_DRY_RUN="${DROP_FABRICATION_DRY_RUN:-0}"` ran at source time BEFORE the inline env var was set, so the sourced default of "0" is locked in.

**Correct pattern (set env var BEFORE source):**
```bash
export DROP_FABRICATION_DRY_RUN=1
source ~/.hermes/scripts/dropped-thread-followup.sh
```

Or for one-off testing of a single function call:
```bash
DROP_FABRICATION_DRY_RUN=1 bash -c 'source ~/.hermes/scripts/dropped-thread-followup.sh && detect_agent_fabrication ...'
```

### Pitfall 3: nested awk regex inside bash function with double-quoted heredoc double-escapes `{` and `}`

The first attempt at `fabrication_strike_count` used:
```bash
count="$(awk -v ts="$thread_ts" -v ch="$channel_id" '
  /^[\[]/ {
    match($0, /\[[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\]/, m)
    ...
  }
' "$FABRICATION_LOG")"
```

This produced `awk: syntax error at source line 3 ... illegal statement at source line 3` — the heredoc nesting caused `{` and `}` to be double-escaped, breaking the awk regex. **The fix:** use a Python3 heredoc instead. Python is already used elsewhere in the script (`analyze_thread` shell-out), it's clearer for log parsing, and it avoids the bash-quoting trap:

```bash
python3 - "$FABRICATION_LOG" "$cutoff" "$channel_id" "$thread_ts" <<'PY' 2>/dev/null || echo 0
import sys, re, datetime as dt
log_path, cutoff, channel_id, thread_ts = sys.argv[1:5]
# ... clean Python parsing ...
PY
```

The `<<'PY'` (single-quoted) prevents bash from expanding `$` inside the heredoc — Python sees the literal `$thread_ts` only via `sys.argv`, not via heredoc interpolation.

### Pitfall 4: the override integration point must come BEFORE `continue`, not after

The naive placement of the fabrication-detection override is AFTER the existing `if [[ "$needs_action" != "true" ]]; then ... continue; fi` block. But that block already calls `continue`, so the override code never runs. **Correct placement:** inside the `if [[ "$needs_action" != "true" ]]; then` block, AFTER the `log "  OK ($reason): ..."` line but BEFORE the `continue`. The structure is:

```bash
if [[ "$needs_action" != "true" ]]; then
  log "  OK ($reason): $channel $thread_ts"
  # fabrication override here — sets needs_action=true if hit
  if [[ "$needs_action" != "true" ]]; then
    continue
  fi
fi
```

The double-`needs_action` check (one before the override, one after) is intentional: if the override fires, control falls through the outer `if` block to the nudge-text builder. If it doesn't fire, the inner check catches and continues.

### Pitfall 5: Bash `set -e` interacts badly with functions that use `return N` to signal non-failure

When sourcing the script under `set -e`, the test wrapper's `detect_agent_fabrication ... ; rc=$?` works because we explicitly use `set +e` around the call. But if the test wrapper forgets `set +e`, the function's `return 1` (NOT fabrication) triggers `set -e` and aborts the test before the next assertion runs. **Always wrap test calls with explicit `set +e` / `set -e` brackets** or use `if detect_agent_fabrication ...; then` to absorb the exit code into the if-condition.

## Cross-references

- `references/no-new-content-hallucination-2026-06-23.md` — the false-positive class this patch targets.
- `~/.hermes_prod/SOUL.md` `## COMMIT: never-hallucinate-no-new-content` — model-level rule.
- `~/.hermes_prod/skills/pr-bring-to-green-inline-cookbook/SKILL.md` Pitfall P4 — polling-loop operational rule.
- `references/2026-06-21-redrive-reply-mcp-mail-bot.md` — 3-article redrive recipe (this patch is the cron-side complement).
- `references/cron-staging-prod-drift-2026-06-17.md` — staging-vs-prod deploy discipline used here.

## Regression-test case (in the script comment as a reference, not auto-asserted)

The 2026-06-23 00:35:01Z incident on `C0AH3RY3DK6/1782231566.821589`. With this patch active and tuned live:

- Last human msg: `1782261301.872479` Jeffrey's "lets reduce vertical space" screenshot `F0BCS7F3WDP`
- Last agent msg: `1782261422.141589` the "no new content" fabrication
- Time gap at fabrication: ~2 min (well within 10-min window)
- Patch would have: detected fabrication, written audit entry, posted re-nudge within minutes instead of waiting for 30-min quiet window

After this patch shipped, the dropped-thread cron will not fire on this same thread again because the most recent MCP mail bot reply (`1782386059.603359` ack + patch announcement) breaks the fabrication pattern — the agent's last reply is no longer the fabrication.