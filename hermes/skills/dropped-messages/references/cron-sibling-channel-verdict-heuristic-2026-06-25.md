---
name: dropped-messages/cron-sibling-channel-verdict-heuristic
description: Cron design note for the dropped-thread-followup script — when an agent verdict lands in a sibling channel (not the originating thread) due to a misroute-blocked `send_message`, the cron's "thread contains agent reply" heuristic sees nothing and keeps nudging past `gave_up=true`. Class-level lesson from 2026-06-25 `C0AH3RY3DK6/1782032160.683689` daily-escalation audit. Pair with `cross-channel-post-unreachable-workspace-2026-06-25.md` (the runtime-side recovery) and `narration-mirror-cleanup-2026-06-25.md` (the post-path cleanup).
type: reference
last_verified: 2026-06-25
---

# Cron heuristic gap — verdict delivered to sibling channel ≠ thread resolved

**Verified 2026-06-25, dropped-thread followup
`C0AH3RY3DK6/1782032160.683689` (planning-block-leak on `ZlkhIbuvQwOyROOQPQAb`) + daily escalation thread `C09GRLXF9GR/1782429092.004159`.**

The dropped-thread-followup cron in `~/.hermes/scripts/dropped-thread-followup.sh`
fires when an originating thread has gone cold. The cron's existing
heuristics:

1. **was_nudged_recently** — skip if the thread got a nudge in the last N min
2. **gave_up short-circuit** — once `gave_up=true`, never re-nudge
3. **"thread contains agent reply"** — implicit (the cron stops nudging
   once the user marks the question resolved)

**The gap:** none of these heuristics recognize "the agent posted a
complete, accurate verdict in a SIBLING channel because the originating
thread is in a workspace the runtime can't reach." The verdict is durable
(it's in `C09GRLXF9GR/1782429092.004159`, an internal daily-escalation
thread) but the originating `C0AH3RY3DK6/1782032160.683689` thread
remains empty of agent replies. The cron nudges → escalates → `gave_up`
→ fires the daily escalation thread. **Cycle continues.**

Verified incident shape:

| Field | Value |
|---|---|
| Originating thread | `C0AH3RY3DK6/1782032160.683689` ("Run /repro seems like planning block leaked future event") |
| Workspace of originating | `T09FXQ4LCQP` ($USER AI) |
| Sibling verdict channel | `C09GRLXF9GR` (daily escalation thread `1782429092.004159`) |
| Workspace of sibling | `T09FXQ4LCQP` (same workspace, but helper's misroute-guard false-positives it — see `cross-channel-post-unreachable-workspace-2026-06-25.md`) |
| Verdict content | Complete triage + 4 proposed fixes (full PR #7764 + #7766 evidence) |
| Cron state at daily-summary post | `gave_up=true` after 3 nudges |
| Outcome | Daily-escalation thread captured the verdict; cron stopped escalating only because of `gave_up=true`, NOT because it recognized the sibling-channel verdict |

## Why the cron's existing heuristics don't catch this

1. **was_nudged_recently** is about the originating thread's own message history. It looks at the thread it nudges, not at sibling channels.
2. **gave_up=true** is a one-way ratchet — it stops the cron from doing more work, but it doesn't tell the user "this was a sibling-channel verdict."
3. **"thread contains agent reply"** is implicit in the nudging logic — it counts nudges as "is this thread still cold?" but doesn't recognize "did the agent post a verdict anywhere?"

## Proposed heuristic: `verdict_delivered_to_sibling_chat`

Add a new check in the `was_nudged_recently` block (or alongside it):

```bash
# Pseudo-bash
function has_sibling_verdict() {
  local thread_ts="$1"
  local lookback_min="${SIBLING_VERDICT_LOOKBACK_MIN:-60}"

  # Search the last $lookback_min min of agent posts across all channels
  # the agent has access to (via mcp__slack__conversations_search or
  # equivalent). If any agent post quotes the same thread_ts and contains
  # verdict markers (PR link, "verdict:", "fix:", "status:", "complete.",
  # etc.), treat as resolved.

  local query="in:#all-$USER-ai after:<now-$lookback_min>m <@U0AEZC7RX1Q> OR <@U0A4G7LDJ4R> $thread_ts"
  local hits
  hits=$(mcp__slack__conversations_search query="$query" limit=5 2>/dev/null \
    | jq '[.messages[] | select(.text | test("PR #[0-9]+|verdict|status:|complete\\."))] | length')

  [ "${hits:-0}" -gt 0 ]
}
```

Then in the main cron loop:

```bash
if has_sibling_verdict "$thread_ts"; then
  log "SIBLING_VERDICT: thread=$thread_ts has verdict in sibling channel, skipping nudge"
  continue
fi
```

## Why this works

- The cron already reads `mcp__slack__conversations_*` (it pulls thread
  history before nudging). One additional `conversations_search` per
  candidate thread is cheap.
- The heuristic is **post-path agnostic** — works whether the agent
  posted via `send_message`, direct `curl chat.postMessage`, MCP, or
  even a Slack block kit interaction.
- It doesn't try to verify the verdict is *correct* — that's a separate
  concern. It just recognizes that "the agent said something
  substantive elsewhere about this thread" means "the user has
  somewhere to read the verdict."

## Anti-patterns (verified 2026-06-25)

- ❌ **Mark the originating thread as resolved in the script** when a
  sibling-channel verdict exists, but **don't post any reply to the
  originating thread.** This leaves the thread's user-facing state in
  "dropped" forever — if the user later opens it expecting a reply,
  they'll see nothing. The verdict must reach the originating thread
  SOMEHOW: (a) via direct API curl, (b) via MCP mail bot ack-log
  entry, or (c) via a brief in-thread ack pointing at the
  sibling-channel verdict. Pick one.
- ❌ **Disable the cron on `T09FXQ4LCQP` because of the misroute-guard
  false positive.** The misroute-guard is a helper-side problem with a
  separate fix (add the workspace to `~/.hermes/slack_tokens.json`,
  per `cross-channel-post-unreachable-workspace-2026-06-25.md`).
  Disabling the cron would lose visibility on real drops.
- ❌ **Reduce `gave_up` from 3 nudges to 1 nudge.** This makes the
  cron less persistent on real drops without solving the
  sibling-channel verdict recognition problem. The `gave_up=true`
  short-circuit is doing its job; the missing piece is the
  recognition heuristic.

## Pair with these references

- `cross-channel-post-unreachable-workspace-2026-06-25.md` —
  explains the runtime-side `send_message` misroute-guard false
  positive for `T09FXQ4LCQP` and the direct-API curl fallback.
- `narration-mirror-cleanup-2026-06-25.md` — the bulk-delete recipe
  for the 5-10 narration mirrors that auto-appear when posting via
  `terminal`-executed curl.
- `daily-escalation-thread-reply-2026-06-20.md` — the daily-summary
  shape that catches sibling-channel verdicts and asks the user to
  ack them. Pair with the new heuristic so future daily summaries
  don't have to mention this gap.

## What this is NOT

- **Not a fix for the misroute-guard.** That's a separate problem
  (helper registry + token wiring) with a separate fix path.
- **Not a replacement for `gave_up`.** The `gave_up=true` ratchet is
  correct; it prevents infinite escalation loops on genuinely-stuck
  threads. The new heuristic runs BEFORE the nudge count advances.
- **Not a verdict-correctness check.** This heuristic only recognizes
  that *something* was posted; it doesn't verify the content. That's
  the user's job (they read the sibling-channel verdict and decide
  whether to ack).