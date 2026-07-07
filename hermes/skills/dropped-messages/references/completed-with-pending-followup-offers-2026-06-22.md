---
name: dropped-messages/completed-with-pending-followup-offers
description: New false-positive class for the dropped-thread cron (2026-06-22) — agent posts answer + "Want me to (a)/(b)/(c)?" follow-up offers, then goes idle. Cron sees no user pick → flags as dropped. Verified on thread 1781981458.208669 (wa-user-activity-report top-10 drilldown).
type: reference
last_verified: 2026-06-22
---

## The failure mode (verified 2026-06-22)

`scripts/dropped-thread-followup.sh` reads `.nudged` state and a thread's last-message author. When the user asks for an analysis and the agent delivers the analysis **plus three offered drilldowns** (a/b/c), the agent then goes idle. The cron ticks 4h later:

1. Sees the thread's last assistant message is the offered-choices post (no PR URL, no "merged", no completion proof).
2. `dropped-thread-auto-resolve.sh` (per `references/session-2026-06-20-auto-resolve-stale-pending.md`) doesn't resolve it because `PROOF_PAT` requires a GitHub URL or `merged`/`landed`/`complete ✓` — none of which appear in "Want me to (a)/(b)/(c)?" posts.
3. Cron posts a "Dropped-thread followup" asking the agent to redo or explain the blocker.

The work is already done. The cron is misclassifying "waiting for user to pick from N offered next steps" as "work dropped."

## Verified example: thread 1781981458.208669

- Jeffrey 2026-06-20 18:53 UTC: "Drill into the top 10 what's your theory on why they stopped playing and what was their campaigns about"
- Agent 2026-06-20 18:56 UTC (ts=1781981760.052879): full drilldown, 5 confidence-tagged theories, **3 offered follow-ups** (a) dump last Gemini scene for akey445 + me@ecor.me, (b) read Dragon Knight prompt to verify prefab-only theory, (c) grep repo for re-engagement cron.
- No user reply. Agent went idle.
- Cron 2026-06-22 02:07 UTC (ts=1782094052.727999): `[Dropped-thread followup]` posted by `mcp_agent_mail`.
- Redrive reply posted 2026-06-22 02:08 UTC (ts=1782094081.599789) as MCP mail bot confirming COMPLETED.

## The pattern (regex form)

Agent message matches **any** of these → thread is "pending user pick", not "dropped":

```regex
Want me to\s+(?:dump|read|grep|check|run|open|fetch|pull|show|tell|verify|test)
(?:\s+\w+){0,30}
\?\s*$
```

Or has the structural "lettered options" pattern:

```regex
\([a-z]\)\s+\S.{10,200}\n\([a-z]\)\s+\S
```

Or contains the literal "Should I" / "Would you like" / "Pick one" lead-in.

## Durable fix candidates (apply to whichever makes sense)

1. **`dropped-thread-auto-resolve.sh` `PROOF_PAT`** — add an "offered follow-up" pattern:
   ```bash
   OFFERED_FOLLOWUP_PAT='Want me to|Should I|Would you like|Pick one|\([a-z]\) [a-z]'
   ```
   Threads where the latest assistant message matches this should be marked `gave_up=true` with `state=pending-user-choice` rather than `pending` — they'll only re-fire if the user explicitly says "stop, redo this."

2. **`mcp-mail-ack` COMMIT** — add a new `State:` value `pending-user-choice` for ack-log entries where work landed but the agent offered N drilldowns. The cron can read the ack-log for this state and skip the nudge (verify on read).

3. **`wa-user-activity-report` SKILL.md** — add a "post-report checklist" requiring the agent to either:
   - pick a recommended next action and run it inline, OR
   - explicitly ask "Want me to drill into (a)/(b)/(c)? Reply with the letter or say 'done' to close this thread", OR
   - tag the offer as `pending-user-choice` in the in-thread post (e.g. add a `:hourglass_flowing_sand:` reaction) so the cron's heuristic can pick it up.

4. **`wa-user-activity-report` skill ack discipline** — after posting the report, immediately write a `pending-user-choice` entry to `mcp-mail-ack-log.md`. The cron reads the log; the entry short-circuits the nudge.

## Why this is class-level (not one-off)

Every analytical skill that delivers a summary + offers drilldowns hits this trap: `dogfood`, `wa-user-activity-report`, `executive-digest`, `wa-finish-intent-structured-bypass`, and any skill that ends with "Want me to..." rather than a definitive close. The fix belongs in the cron heuristic (option 1) because that catches the whole class; the other fixes are defense-in-depth.

## How to spot this in the wild (triage checklist)

When the dropped-thread cron flags a thread and you suspect false-positive:

1. Read the **last 2–3 messages** in the thread (not just the latest).
2. Did the agent post a full answer **with offered follow-ups** ("Want me to (a)/(b)/(c)?")?
3. If yes → this is the "completed-with-pending-followup-offers" class. Reply with a redrive recap (3-article recipe) and the offered follow-ups are still available if the user wants one.

Don't try to re-run the analysis. Don't expand the answer. The user already saw it.

## Related

- `references/session-2026-06-20-auto-resolve-stale-pending.md` — the auto-resolve script that already handles "PR URL posted" but **not** "follow-ups offered." This class is the missing case.
- `references/2026-06-21-redrive-reply-mcp-mail-bot.md` — the 3-article redrive recipe (post as MCP mail bot, log to ack-log, patch gotcha). The Article-3 patch from this thread is THIS document.
- `~/.hermes/scripts/dropped-thread-auto-resolve.sh` — where option 1 above would land (add `OFFERED_FOLLOWUP_PAT` to the proof-pattern set).
- `~/.hermes/scripts/dropped-thread-followup.sh` — the cron itself; its `.nudged` state would gain a new `pending-user-choice` value under option 2.

## Sibling false-positive class — "PR_OPEN_MERGEABLE_BUT_PICKUP_NEEDED" (verified 2026-06-22 23:42 UTC, thread 1782028360.785129)

The "completed-with-pending-followup-offers" class above covers analytical offers. There's a **sibling class** for /repro workflows where:

1. The /repro work landed cleanly in a prior session (twin copy + issue + draft PR).
2. The PR was promoted from draft → ready, ran the full Green Gate suite, and is `state=OPEN + mergeStateStatus=CLEAN`.
3. The agent went idle waiting for `MERGE APPROVED`.
4. The dropped-thread cron sees no fresh "user pickup" message and fires a followup.

**Verified 2026-06-22 23:42 UTC on `btF3Nu4mqQRTVLG6F7tu` / Zalia execution:**

| Stage | State |
|-------|-------|
| Repro twin copy | ✅ exists (campaign `3DU4t5ibUPIDtchVeDxS`) |
| Issue filed | ✅ [#7761](https://github.com/$GITHUB_REPOSITORY/issues/7761) OPEN |
| PR opened + promoted | ✅ [#7762](https://github.com/$GITHUB_REPOSITORY/pull/7762) OPEN, non-draft |
| CI 7-green | ✅ 19/19 PASS at 2026-06-22T21:08:51Z (after one transient FAILURE retry at 21:06Z) |
| `mergeStateStatus` | ✅ `CLEAN` |
| Awaiting | ⏸ `MERGE APPROVED` from Jeffrey |

**Why the cron misfires:** the cron treats "no fresh user message" as "work dropped." But the durable artifact is **a PR in CLEAN state**, not "no message." The agent has finished the work and is in a stateful waiting pattern (`MERGE APPROVED` gate per `~/.claude/CLAUDE.md` "Merge safety" for your-project.com PRs).

**Triage checklist (extends the one above):**

5. Read the **last 3 messages** in the thread (not just the latest).
6. Did the agent post a /repro / fix-flow with: `gh issue create` body + `gh pr create --draft` body + a promotion-to-ready message?
7. Did the PR transition to `state=OPEN + mergeStateStatus=CLEAN`?
8. If yes → this is the `PR_OPEN_MERGEABLE_BUT_PICKUP_NEEDED` class. Reply with a redrive recap + the "awaiting `MERGE APPROVED`" line. **Do NOT re-run the repro.** The twin, issue, and PR are all on disk.

**Durable fix candidate (extends option 1 above):**

- **`dropped-thread-auto-resolve.sh`** — add a GitHub-API-driven short-circuit:
  ```bash
  # New check: any open PR on the originating repo whose body or comments
  # reference the originating campaign ID and is in CLEAN mergeStateStatus?
  gh pr list --state open --json number,mergeStateStatus,body \
    --search "btF3Nu4mqQRTVLG6F7tu in:body" \
    | jq -e '.[] | select(.mergeStateStatus=="CLEAN") | .number' > /dev/null \
    && state=closed-loop-pickup-needed && exit 0
  ```
  Threads where the originating campaign is referenced by a CLEAN PR skip the cron nudge.

**Cross-references:**

- This is the **third** cron-misfire false-positive class logged today: (1) completed-with-pending-followup-offers at 02:08Z, (2) stale 5b-leak alert at 11:42Z, (3) PR_OPEN_MERGEABLE_BUT_PICKUP_NEEDED at 23:42Z. All three suggest a unified cron refactor: read the durable artifact state (PR status, issue status, ack-log entry, mcp-mail-ack-log.md `State:` value) BEFORE firing the followup nudge.
- `references/2026-06-21-redrive-reply-mcp-mail-bot.md` v2 — the "Post the redrive to the channel where the dropped-thread followup landed" gotcha is verified again here (alert channel `C0AH3RY3DK6` ≠ alert source channel; MCP mail bot is a member of `C0AH3RY3DK6`, post landed at `ts=1782196673.810309`).
