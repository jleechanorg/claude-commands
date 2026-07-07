# Inheriting a Mid-Loop Babysit

When a babysit loop has been ticking for a while and you take over mid-stream (handoff across sessions, restart of the agent runtime, etc.), the **first tick of your run MUST verify the loop is still authoritative before posting anything**.

## Why this matters

Concrete failure observed 2026-07-04 on PR #7711 / bead rev-w98fd / thread `C0AH3RY3DK6/1781868745.233079`:

The original PR had merged on 2026-06-23 (~11 days earlier). The babysit cron was still configured to tick on that PR number. Two prior babysit ticks in the same series had already independently noticed the merge and each posted a closing summary — one at 2026-07-05T05:02:40Z ("SILENT: PR 7711 already MERGED ... Ending cron loop"), one at 2026-07-05T05:14:56Z (full closeout with bullet list), one at 2026-07-05T06:07:51Z (full closeout again with "babysit DONE closeout"). Each new tick that did a fresh `gh pr view` saw `state: MERGED` and produced its own slightly different summary, because none of them read the prior-tick messages first.

## The 4-step handoff pre-flight (do these every time you inherit a tick)

1. **`gh pr view <PR> --repo <OWNER>/<REPO> --json state,mergedAt,closedAt`** — Is the work already done?
2. **`mcp__slack__conversations_replies --channel_id <chan> --thread_ts <ts> --limit 5`** — What did the last 1-2 ticks already post? Sort by `ts DESC`. Look for:
   - "Ending cron loop."
   - "babysit DONE"
   - "PR <N> merged"
   - "Loop closing."
   - ":white_check_mark:" + "closed" / "merged"
3. **If step 1 says merged AND step 2 shows a recent closeout (within the last 60 min)** → suppress. Reply `[SILENT]`. Do not post anything.
4. **If step 1 says merged AND step 2 has NO recent closeout (e.g. handoff happened AFTER all prior ticks ran)** → it is YOUR job to be the closing tick. Post ONE final summary, then disable the cron.

## Anti-pattern

- ❌ Assuming "this tick owns the close" without checking. Multiple ticks each posting a slightly different closeout is the failure mode.
- ❌ Trusting the SKILL.md contract ("Phase 0 step 1 catches this") without verifying what prior ticks already did. The contract says *one* tick posts the close — the contract does NOT exempt subsequent ticks from checking the thread before posting.

## Detection heuristic

If the cron prompt text contains any of:
- "ending cron loop"
- "babysit DONE"
- "babysit COMPLETE"
- "Loop closing"
- "mergedAt <date in the past>"

…in the last 5 thread replies, the loop is already closed. Suppress. The cron should self-disable shortly; if it does not, file a follow-up to disable it.
