# Worked Example: Iter-Budget Exhausted Mid-Work — Crash-Capture BQ Recovery (2026-06-15)

**Thread:** `C0AH3RY3DK6 / 1781315111.023479` (jleechanorg your-project.com)
**Drop signal:** MCP Agent Mail followup at `ts=1781491197.425849` (2026-06-15 02:39:57Z, ~48h after root)
**User root (2026-06-13 01:45:11Z):** *"I wanna intercept all crashes and log to Bq and all user facing errors"*
**Dropped-thread followup quote:** *"Centralize code and use /fs and /f to drive this with real user BQ evidence generated from real server at the end and spawn AO worker after you get all requirements from me. Can use /superpowers brainstorm as needed but just give me recommended options all at once to review in bulk"*

## What the prior session actually did (the 60-iter-cap-cutoff state)

The prior session implemented the crash-capture feature end-to-end across 4 commits on `feat/crash-capture-to-bq`, all pushed to origin:

| SHA | Message | LOC | What it did |
|---|---|---|---|
| `1e5c6845d2` | feat(bq): add error_events table + log_error_event() sink | 178 | BQ table schema + sink in `$PROJECT_ROOT/bq_logging.py` |
| `8eef986e45` | feat(logging): auto-promote ERROR/CRITICAL/exception to error_events | 118/-6 | `bq_silent` opt-out in `$PROJECT_ROOT/logging_util.py` |
| `03eccacc8c` | feat(crash_capture): process-level + Flask error event interceptors | 520 | New `$PROJECT_ROOT/crash_capture.py` (incl. real bug fix) |
| `7b443f1adb` | test(crash_capture): 30 tests covering sink, interceptor, Flask, auto-promote | 620 | `$PROJECT_ROOT/tests/test_crash_capture.py` |

Total: 1450 insertions across 5 files. All 30 new tests + 33 related tests passed (63/63 verified by the prior session's terminal status).

The session's terminal Slack message at `ts=1781322001.845249` (2026-06-13 03:40:01Z):
> `:warning: Iteration budget exhausted 60/60 asking model to summarise`

The session's final status at `ts=1781322032.805219` (2026-06-13 03:40:32Z) listed the next 3 steps:
1. `gh gist create` for the test output (GATE-6 evidence)
2. `gh pr create` with the 8-section body
3. Spawn the AO worker for bring-to-green

## What the prior session did NOT do

- Did NOT run `gh pr create` — the branch was pushed but no PR was opened
- Did NOT run `/fs` (factory-spec) — the dark-factory spec generation step from the original meta-request was never started
- Did NOT run `/f` (full dark-factory loop) — the implementation was direct, not through `pipelines/factory/gates.dot`
- Did NOT produce a `/es` real-server bundle — only 63/63 unit/integration tests against mocked BQ sink

## How the recovery detected the state (4 verification calls)

The recovery turn that handled this thread ran the exact recipe from the parent SKILL.md:

```bash
# 1. Read the prior session's terminal Slack messages
mcp__slack__conversations_replies --channel_id=C0AH3RY3DK6 --thread_ts=1781315111.023479
# → Confirmed ":warning: Iteration budget exhausted 60/60" + 3-step "next actions" list

# 2. Verify no PR was opened
gh pr list --state all --search "crash capture to bq"
# → No results; `gh pr list --head feat/crash-capture-to-bq` would also be empty

# 3. Confirm the commits are clean and on-topic
git log origin/feat/crash-capture-to-bq --oneline -10
# → 4 commits (1e5c6845d2 → 8eef986e45 → 03eccacc8c → 7b443f1adb) on top of e08437e011
git diff origin/main...origin/feat/crash-capture-to-bq --stat
# → 5 files, 1450 insertions, no unrelated contamination

# 4. Confirm the test claim reconciles to the diff
git show 7b443f1adb --stat
# → test_crash_capture.py is in the diff at 620 insertions, matching the prior session's 30/30 claim
```

4 tool calls. No re-run of the test suite. No `gh pr view`. No `git worktree add`.

## The recovery reply shape (the right one)

The recovery turn posted a single Slack reply with the standard `colored-icons-in-status-reports` sections (Healthy / Risky / Blocked / Next actions) AND a single yes/no decision:

```
🟢 Healthy
- `feat/crash-capture-to-bq` exists at origin with 4 clean commits, 1450 LOC
- All 30 new + 33 related tests pass (63/63)
- Issue #7512 is open with a locked design

🟡 Risky
- No PR has been opened yet. Prior session pushed the branch and ran out at PR-open.
- The "centralize code with /fs and /f" meta-request was never started as a dark-factory loop.

🔴 Blocked
- Need your decision on the original meta-request. Two interpretations:
  1. Crash-capture was a one-off, just open the PR for it. ~10 min.
  2. You really want the dark-factory loop. /fs first, then /f with --feature. ~1-2 hours.

🔵 Next actions
- Awaiting your pick between (1) ship-the-PR-now and (2) re-run-through-dark-factory.
- Branch reference: origin/feat/crash-capture-to-bq @ 7b443f1adb
```

8 lines of section content + a single binary decision. No re-investigation. No 4-option menu. No "let me check X" narration.

## Why the recovery did NOT open the PR in the same turn

The user's original meta-request was explicit: "Centralize code and use `/fs` and `/f` to drive this." The prior session's diff does not satisfy that meta-request — it shipped the crash-capture directly, not through dark-factory. The recovery turn surfaced the meta-decision as the explicit single yes/no question (path 1 = ship direct PR; path 2 = re-run through /f + /fs), with path 1 as the safe default.

If the recovery had pre-emptively opened the PR, it would have:
- Made path 2 impossible without closing the just-opened PR (waste of a PR number, beacon to the next user who searches "crash-capture")
- Bypassed the explicit meta-decision the user baked into the request
- Set the precedent that the dropped-thread recovery ignores meta-requests in favor of literal "ship the work" — which is the wrong policy when the user has signaled process discipline

The 4-call verification is enough to make the binary decision concrete. The user can pick A or B in one reply.

## What the wrong recovery would have looked like

### Anti-pattern 1: The 4-option menu (the standard "menu" anti-pattern)

> "Status: branch pushed, tests pass, no PR. Want me to:
> (a) Open the PR with the 8-section body and spawn AO for bring-to-green
> (b) Re-run /fs to generate the spec, then /f with --feature for the holdout
> (c) Just open the PR without the dark-factory gates
> (d) Wait for more requirements?"

This is the menu trap. The user already didn't pick the original 3-option menu (that's why the dropped-thread followup arrived). A second 4-option menu will also not be picked. Worse: option (c) is a stealth re-skinning of option (a), so the menu is effectively 3 options with extra noise.

### Anti-pattern 2: Pre-emptively open the PR

> `gh pr create --base main --head feat/crash-capture-to-bq ...`

Wrong: ignores the explicit `/fs` + `/f` meta-request. Even if the user later says "yes, ship direct," the PR is already open and the meta-decision was bypassed. The user has to either close-and-reopen (waste) or accept the bypass (loss of process control).

### Anti-pattern 3: Re-investigate the test results

> "Let me re-run the test suite to verify 63/63 before recommending next steps."

Wrong: the prior session's Slack messages are the source of truth. The 4-command verification is enough to confirm the state. Re-running the full test suite is the iter-budget trap the prior session fell into — burning 5+ iters on `pytest` for a result already in Slack history. The recovery turn should not repeat the same trap.

### Anti-pattern 4: Just file a status report and stop

> "Here's the status: branch at <SHA>, 4 commits, 63/63 tests. No PR. Awaiting your decision."

Wrong: the user did not ask for a status report. The user asked for the work to be done (interception of crashes to BQ). The status report is necessary but not sufficient — the recovery must also surface the actionable next step (single yes/no decision), not just state the gap.

## Lessons captured (cross-references)

- **`dropped-messages` SKILL.md new pitfall:** "Prior session ran out of tool-iterations mid-work" — the full recipe + anti-patterns + cross-references.
- **`always-pr-never-local-edit` SKILL.md new pitfall:** "Cross-reference: when YOU are the iter-cap-cutoff session, leave clean recovery state" — the forward-looking version (push the branch, name the 3 next steps, state the meta-decision).
- **Future `dispatch-task` reference:** when the user asks to "spawn AO worker after you get all requirements from me" (as the dropped-thread quote did), the recovery turn must surface the AO-spawn *as one of the recovery options*, not as an action to take pre-emptively. The 3-option menu in the prior session's terminal message listed "spawn AO worker" as step 3 — that step is *in the original session's last status*, not in the recovery turn's autonomous actions.

## What the next session should do after the user picks

### If user picks path 1 (ship PR now)

```bash
# In the recovery turn after the user's reply:

# 1. Create the GATE-6 evidence gist
gh gist create --public --desc "crash-capture: 30+33 tests, 63/63 PASS, pytest output" /tmp/test_output.log
# → returns https://gist.github.com/<user>/<id>

# 2. Open the PR with the 8-section body
gh pr create --base main --head feat/crash-capture-to-bq \
  --title "[antig] feat: intercept all crashes + user-facing errors to BigQuery error_events" \
  --body-file /tmp/pr_body.md
# → returns https://github.com/$GITHUB_REPOSITORY/pull/<N>

# 3. Spawn the AO worker for bring-to-green
ao spawn -p jleechanorg__your-project.com <bead-id>
# → returns ao-<id>; steer with ao send to use the existing branch

# 4. Echo PR URL + AO worker session in the Slack reply (the "verified merge-readiness" shape)
```

### If user picks path 2 (re-run through /f + /fs)

```bash
# 1. /fs crash-capture-to-bq (factory-spec generates spec.md + attractor_spec.md)
dark-factory --pipeline pipelines/slim/spec_gen.dot --goal "crash-capture BQ error_events" --backend claude

# 2. /f with the gates pipeline and the existing branch as the implementing agent's diff
dark-factory --pipeline pipelines/factory/gates.dot --goal "crash-capture BQ error_events" \
  --backend claude --feature crash-capture --cxdb ~/.dark-factory/cxdb.sqlite

# 3. The holdout grader runs end-to-end on the existing 4-commit branch
# 4. Green Gate verdict arrives; report in thread
```

Path 2 takes 1-2 hours and requires the `dark-factory` install + a sealed holdout feature at `~/projects/dark-factory-holdouts/holdouts/crash-capture/`. Neither is currently present on this host, so path 2 is the larger commitment.

## Summary

The iter-budget-exhausted-mid-work pattern is the most common cause of "user waited 48h for a PR that was 1 step away from being opened." The recovery recipe is short (4 verification calls) and the right reply shape is single-decision (path 1 vs path 2), not multi-option menu. The forward-looking rule (for the agent that IS the burning-iter session) is to push the branch + name the 3 next steps + state the meta-decision before the cap hits. Both halves of the loop are now in the skill library.
