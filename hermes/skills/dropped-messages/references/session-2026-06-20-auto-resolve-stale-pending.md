# Auto-resolve stale "pending" dropped threads — added 2026-06-20

## The problem

`dropped-thread-followup.sh` only marks a thread `gave_up=true` after `MAX_NUDGES=3`
(default). But agents often answer within the **first** nudge — posting a status
reply with proof (PR URL, "merged", `:white_check_mark:`, etc.) — and the
`.nudged` state still shows it as pending because the script doesn't inspect
the thread's content post-nudge.

Effect: state accumulates 6+ "pending" entries that are actually resolved. Every
4h the launchd cron sees them, re-flags them, and the roadmap report
(`slack-thread-roadmap-report.sh`) shows them as "actionable" even though they
aren't.

## The fix — `dropped-thread-auto-resolve.sh`

A small companion script that runs **before** the main dropped-thread script
and pre-cleans state. Bakes in the auto-resolve pattern so future cron ticks
don't re-accumulate stale "pending" entries.

**File:** `~/.hermes/scripts/dropped-thread-auto-resolve.sh` (committed
2026-06-20, PR via `jleechanorg/jleechanclaw`).

**Trigger to add inside `slack-thread-roadmap-report.sh`** (or any other
consumer of `.nudged` state):

```bash
AUTO_RESOLVE_SCRIPT="${AUTO_RESOLVE_SCRIPT:-$HERMES_HOME/scripts/dropped-thread-auto-resolve.sh}"
if [[ -x "$AUTO_RESOLVE_SCRIPT" ]]; then
  log "  running dropped-thread-auto-resolve.sh (pre-cleanup)"
  bash "$AUTO_RESOLVE_SCRIPT" >> "$LOG_FILE" 2>&1 || log "  auto-resolve: exited non-zero (continuing)"
fi
```

## Resolution criteria (PROOF_PAT + QUESTION_PAT)

The script marks `gave_up=true` for any pending (last_nudge < 24h) thread where
**all three** are true:

1. The **latest** message in the thread is from the agent (`U0AEZC7RX1Q` or
   any `bot_id`)
2. The latest agent message **contains proof** — matches the regex:
   ```
   https://github\.com/[^\s)]+  |  merged  |  shipped  |  landed
   |  :white_check_mark:  |  \*Status  |  \*PR #  |  complete ✓
   |  self-improvement review  |  skill .* created
   ```
3. **No user follow-up after the agent's reply** — i.e. no human message with
   `ts > agent.ts`

`is_question` is a separate guard (matches `?`, `<@U…>`, "could you", "please",
"do you", "would you") — a question reply is **not** treated as proof of
resolution.

## Verified 2026-06-20

- 6 stale pending threads → 6 marked `gave_up=true` on first run
- Idempotent: second run examined=0 resolved=0 (no double-work)
- Roadmap cron then went from 0-actionable-with-noise to clean all-clear
  reports

## Why this is class-level (not one-off)

Any future consumer of `.nudged` state (`dropped-thread-followup.sh`,
`slack-thread-roadmap-report.sh`, third-party dashboards, ad-hoc recovery
queries) will hit the same stale-pending noise. The auto-resolve pattern is
the canonical "is this thread actually still pending?" classifier and should
be reused, not re-implemented.

## Pitfall: don't conflate "agent status reply" with "PR merged"

`PROOF_PAT` includes the literal string "merged" because that's how agents
typically report completion. But it also matches a self-improvement review
like `:floppy_disk: Self-improvement review: Skill 'gateway-safety-guard'
created.` — that's the **agent describing what IT did**, not the user
approving. The classifier treats both as resolution. If a thread needs explicit
user sign-off, the user follow-up check (`has_user_after`) catches it.

## Pitfall: agent "partial-state reply" pattern

`finish-the-job` skill (per `~/.codex/AGENTS.md`) ends with a "partial-state
reply" that includes the PR URL but no `merged` claim — the agent delivered a
PR but hasn't confirmed the user approved/merged it. The classifier marks
these as resolved because the PR URL is in `PROOF_PAT`. **This is correct**
because:

- The dropped-thread script's purpose is "find unanswered work"
- An agent that opened a PR has *answered* the work request, even if merge is
  pending
- The merge-state is a separate concern (tracked elsewhere, e.g. via the
  /skeptic gate for AO PRs)

## Related

- `~/.hermes/scripts/dropped-thread-auto-resolve.sh` — the script
- `~/.hermes/scripts/slack-thread-roadmap-report.sh` — primary consumer
- `slack-thread-roadmap-report.sh` Step 1 — pre-cleanup hook point
- `dropped-thread-followup.sh` line 60 — `MAX_NUDGES=3` cap (the reason
  this auto-resolve is needed in the first place)
