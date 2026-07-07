# Cron `gave_up` State Shape Mismatch — Resolved-Thread Re-Ping Loop (2026-06-17)

**Threads affected:**
- `C09GRLXF9GR / 1781649993.746949` — `/es` skill review (resolved 2026-06-16 22:47 PT)
- `C0AH3RY3DK6 / 1781476705.821469` — top-5 audit (resolved 2026-06-14 22:38 PT)

**External symptom:** `mcp_agent_mail` started firing "Dropped-thread escalation — Gave up after 3 nudges with no resolution" on both threads, even though the work was already done and the threads had 3 prior agent replies each.

**Sessions burned on the loop:** 2 followup cycles each (4-6 sessions total across 2026-06-16/17) trying to re-diagnose, re-reply, or restate status. None of them fixed the cron.

## Root cause

The state file `~/.hermes_prod/logs/dropped-thread-state.json` evolved its shape over time:

**Legacy (string):**
```json
"nudged": {
  "C0AKALZ4CKW_1776040748.357529": "2026-04-13T03:37:15Z"
}
```

**Current (object — written by `mcp_agent_mail` escalation logic):**
```json
"nudged": {
  "C09GRLXF9GR_1781649993.746949": {
    "last": "2026-06-17T08:19:54Z",
    "count": 3,
    "gave_up": true
  }
}
```

The `was_nudged_recently` function in `~/.hermes_prod/scripts/dropped-thread-followup.sh` (line 89) was written for the legacy shape:

```bash
was_nudged_recently() {
  local channel_id=$1 thread_ts=$2
  local state last_ts now_sec ts_sec
  state="$(load_state)"
  last_ts="$(jq -rn "$state | .nudged.\"${channel_id}_${thread_ts}\" // empty" 2>/dev/null)" || last_ts=""
  [[ -z "$last_ts" || "$last_ts" == "null" ]] && return 1
  now_sec="$(date +%s)"
  ts_sec="$(date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_ts" '+%s' 2>/dev/null)" || return 0
  [[ $((now_sec - ts_sec)) -lt $NUDGE_INTERVAL_SECS ]] && return 0
  return 1
}
```

With the new object shape:
- `last_ts` becomes `"{\"last\":\"2026-06-17T08:19:54Z\",\"count\":3,\"gave_up\":true}"` (the dumped object)
- The `[[ -z "$last_ts" || "$last_ts" == "null" ]]` guard does NOT trigger (the value is non-empty, non-null)
- `date -u -j -f "%Y-%m-%dT%H:%M:%SZ"` fails to parse the JSON object as a timestamp → `|| return 0` fires → the function exits with 0, which the caller at line 809 reads as "not nudged recently"
- Result: every cron cycle re-nudges every `gave_up=true` thread forever

## Detection (1 jq command)

```bash
jq -r '
  .nudged | to_entries
  | map(select(.value | type == "object" and .gave_up == true))
  | .[].key
' ~/.hermes_prod/logs/dropped-thread-state.json
```

If this returns 2+ entries, the pattern is real. Also check the cron is misfiring:

```bash
tail -50 ~/.hermes_prod/logs/dropped-thread-escalation-2026-06-17.ts
```

If you see repeated lines for the same thread at the same `thread_ts` with `kind=uncertain` or `reason=...`, the cron is in the loop.

## The fix (patched 2026-06-17)

Replace `was_nudged_recently` with a shape-tolerant version that short-circuits on `gave_up=true`:

```bash
# Check if thread was nudged recently (idempotency guard)
# Supports two state-file shapes for backward compatibility:
#   1. string value:  "<ISO timestamp>"           (legacy)
#   2. object value:  {"last": "<ISO>", "count": N, "gave_up": true/false}
# For object shape, also short-circuits when gave_up=true (≥3 nudges, no
# resolution) — once a thread has been escalated that many times without
# operator input, the cron stops pinging the operator about it.
was_nudged_recently() {
  local channel_id=$1 thread_ts=$2
  local state entry_type entry_value now_sec ts_sec
  state="$(load_state)"
  entry_type="$(jq -rn "$state | .nudged.\"${channel_id}_${thread_ts}\" | type" 2>/dev/null)" || entry_type=""
  # Legacy null/missing → not nudged yet
  [[ -z "$entry_type" || "$entry_type" == "null" ]] && return 1
  # Object shape: short-circuit if gave_up is set
  if [[ "$entry_type" == "object" ]]; then
    local gave_up
    gave_up="$(jq -rn "$state | .nudged.\"${channel_id}_${thread_ts}\".gave_up // false" 2>/dev/null)" || gave_up="false"
    [[ "$gave_up" == "true" ]] && return 0
    entry_value="$(jq -rn "$state | .nudged.\"${channel_id}_${thread_ts}\".last // empty" 2>/dev/null)" || entry_value=""
  else
    entry_value="$(jq -rn "$state | .nudged.\"${channel_id}_${thread_ts}\" // empty" 2>/dev/null)" || entry_value=""
  fi
  [[ -z "$entry_value" || "$entry_value" == "null" ]] && return 1
  now_sec="$(date +%s)"
  ts_sec="$(date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$entry_value" '+%s' 2>/dev/null)" || return 0
  [[ $((now_sec - ts_sec)) -lt $NUDGE_INTERVAL_SECS ]] && return 0
  return 1
}
```

Lines added: ~15. No new dependencies. `bash -n` clean.

## Verification

```bash
# 1. Syntax check
bash -n ~/.hermes_prod/scripts/dropped-thread-followup.sh && echo "syntax OK"

# 2. Dry-run covering the two previously-misfiring threads
DRY_RUN=1 DROP_LOOKBACK_HOURS=48 \
  DROP_CHANNELS="C09GRLXF9GR C0AH3RY3DK6" DROP_EXCLUDE_CHANNELS="" \
  bash ~/.hermes_prod/scripts/dropped-thread-followup.sh 2>&1 | \
  grep -E "1781649993|1781476705"
```

Expected output (post-patch):
```
[YYYY-MM-DDTHH:MM:SS]   SKIP (nudged recently): C09GRLXF9GR 1781649993.746949
[YYYY-MM-DDTHH:MM:SS]   SKIP (nudged recently): C0AH3RY3DK6 1781476705.821469
```

Before the patch, both would have been processed and re-nudged.

## Recovery turn shape (the right one)

The agent in the recovery turn did this (8 tool calls total):

1. `mcp__slack__conversations_replies` on C09GRLXF9GR/1781649993.746949 — confirmed /es verdict + 3 offered sharpening patches
2. `mcp__slack__conversations_replies` on C0AH3RY3DK6/1781476705.821469 — confirmed full top-5 audit + 3 open decisions
3. `jq` on the state file — confirmed 2 entries with `gave_up=true` (the pattern)
4. `read_file` on `dropped-thread-followup.sh` line 85-100 — read the broken `was_nudged_recently` function
5. `patch` — applied the shape-tolerant fix above
6. `bash -n` on the script — syntax check (clean)
7. 2× `curl https://slack.com/api/chat.postMessage` with explicit `channel=C...` + `thread_ts=...` + the closure message body (NOT `send_message` — that 3-part target misroutes per agent-orchestrator #684)
8. 1 `DRY_RUN=1` invocation confirming both threads now skip

Plus 1 `memory` write to capture the durable fact for future sessions.

## What the wrong recovery looked like (anti-pattern)

1. `mcp__slack__conversations_replies` → confirm work done
2. Post a 3-option menu to the thread: "Want me to (a) apply the 3 patches, (b) leave the skill as-is, (c) investigate further?"
3. Wait for the user to pick (they won't, because the cron will re-ping and they're already tired of this)
4. Get re-pinged 4 hours later by `mcp_agent_mail`
5. Post another 3-option menu (the menu anti-pattern from 2026-06-11)
6. Loop forever

The cron bug is invisible to the recovery agent that only reads the thread and posts a reply. The state file inspection step is the only way to see it.

## Cross-references

- `dropped-messages` SKILL.md → "⚠️ Resolved-thread re-ping loop — `gave_up` state shape mismatch (added 2026-06-17)" sub-section: full recipe + 8-tool-call budget + the "anti-pattern: 3-option menu trap" framing.
- `dropped-messages` SKILL.md → "⚠️ False-positive alert re-investigated 3+ times" sub-section (added 2026-06-12): the *prior* iteration of this same problem class, before the bug was visible to a casual reader. The 2026-06-17 fix is a structural resolution; the 2026-06-12 sub-section is the recovery recipe when the bug isn't visible.
- `dropped-messages` SKILL.md → "Posting the recovery reply: do NOT use `send_message`, use curl from the start": the canonical curl `chat.postMessage` recipe used in step 7 above.

## What the next session should know

If you see `mcp_agent_mail` firing "Gave up after 3 nudges" alerts on threads that have prior agent replies:
1. Do NOT post a status reply. The reply is the trap.
2. Read the state file with the `jq` command above.
3. If `gave_up=true` entries exist, the cron is misfiring. Apply the patch.
4. Verify with the dry-run.
5. THEN post the executive-decision closure to the threads (curl, with proof + "in-flight, not stale" wording).

The durable fix is in the script, not in the thread. The thread's work is already done.
