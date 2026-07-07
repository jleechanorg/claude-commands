# Anatomy of a Babysit Cron Task Prompt

A babysit cron prompt (the `hermes cron create "20m" ...` body that gets delivered on every tick) has a contract you must honor — every prompt that follows this pattern is a tick on an existing loop, even if it looks fresh.

## Canonical prompt shape

```
You are babysitting AO worker wa-<id> working on PR <url> (issue #<n> — <short summary>).

Worktree: <absolute path to worktree> (branch <branch_name>)
Bead: <bead_id>
Campaign evidence: <optional log path>

Steps each tick:
1. <observation step 1>
2. <observation step 2>
... (typically 6-7 steps)
N. Post a concise status update to the Slack thread (channel <C...>, thread <ts>) every tick: <list of required post sections>

If nothing changed since last tick AND no commits in 30 min, reply HEARTBEAT_OK instead of posting.

Tools available: terminal, file, gh CLI, ao CLI. Do NOT modify code. Do NOT push. You only observe and report.
```

## Required fields to extract (every tick, before doing anything)

- `PR number` — from "PR <url>" or "PR #<n>"
- `Repo` — `jleechanorg/<repo>` (default, check PR JSON)
- `Worktree absolute path` — required for `git log ... --oneline`
- `Branch` — required for `git log origin/<base>..HEAD`
- `Base branch` — usually `main` or `master`; verify with `gh pr view <N> --json baseRefName`
- `Worker session id` — `wa-<id>` or `<session_label>`; grep target for `ao session ls`
- `Slack channel` — `C...` (10-char ID)
- `Slack thread_ts` — `<ts>` (Unix timestamp `1234567890.123456`)
- `Cron cadence hints` — "every tick" / "20m" / "5 min" — tells you the silence window
- **`[SILENT]` vs `HEARTBEAT_OK` contract** — read the prompt's tail carefully; if it says "respond with exactly [SILENT]" you MUST use the literal token, not `HEARTBEAT_OK`, when nothing has changed

## How to extract safely

Do NOT regex-extract these from the prompt in a serial fashion. Run the four observation commands (see Phase 1 in SKILL.md) and verify the extracted fields against actual repo state — a stale prompt can have a wrong branch name, wrong thread_ts, or right thread with a different parent message.

```bash
# Verify the prompt's PR number resolves to a real PR
gh pr view <N> --repo jleechanorg/<repo> --json headRefName,baseRefName,state,mergedAt

# Verify the thread_ts is still active (not orphaned by a channel rename)
mcp__slack__conversations_replies --channel_id <chan> --thread_ts <ts> --limit 1

# Verify the worktree path is reachable
cd <worktree> && git rev-parse --abbrev-ref HEAD
```

If any of the three fails:
- PR doesn't exist → produce exactly `[SILENT]` and exit (the prompt is stale).
- thread_ts returns empty → post `[SILENT]`, and also log a structured note that the cron prompt's thread_ts is stale and needs to be refreshed by the operator.
- worktree path doesn't exist → post a one-liner asking the operator to re-baseline the cron; the loop cannot continue.

## Variations you may see

- **One-time cron with `--delete-after-run`**: the prompt may explicitly say "this is a one-shot followup, deliver the result and the cron self-deletes". In that case there is no observe-loop, just one delivery — treat it as a `finish-the-job` micro-task instead.
- **Multi-PR sweep**: the prompt may list multiple `(PR, worker, thread_ts)` triples. Run the phases per-triple, write one consolidated section in the message.
- **`/skeptic` invocation request** baked into the prompt: that is a separate signal that the operator wants auto-skeptic. Honor it in Phase 2 only if the PR is green, reviewer-ready, and the current head SHA has no existing skeptic request (verified via `gh pr comments | grep -i skeptic`).

## Anti-pattern

- ❌ Treating the cron prompt as a fresh user task. The user did not write this prompt for you; the operator (cron itself) did, and the contract is "tick the loop", not "redesign the workflow".
- ❌ Re-extracting PR number / branch / thread_ts from the prompt on every tick without verifying them against actual repo/thread state. A stale cron with a real recent failure is the most expensive miss (you'd post nothing while work has rotted).
