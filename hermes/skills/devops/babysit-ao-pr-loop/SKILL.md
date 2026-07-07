---
name: babysit-ao-pr-loop
version: 1.2.0
description: Run a recurring cron-tick babysit loop that watches a single AO worker driving a PR — observe activity, post concise status updates to the originating Slack thread, suppress noise via [SILENT]/HEARTBEAT_OK when nothing changed, terminate the loop cleanly when the PR reaches a terminal state (merged, closed, abandoned) or the worker is gone. v1.2.0 (2026-07-05) adds the **executable self-cancel contract**: every babysit invocation MUST pass `--cron-job-id` to `babysit.py poll`/`babysit.py babysysit` so the script can issue `cronjob action=remove` itself on terminal PR detection. Without `--cron-job-id`, the prompt-level self-cancel clause is unreachable from the script and the cron leaks until the watchdog catches it (≤30 min). v1.1.0 (2026-07-05) added Phase 0.5 self-cancel discipline + the `babysit-stale-watchdog` companion. Triggered by any "babysit wa-NNNN" / "watch PR N" / "tick loop on PR N" instruction or any scheduled cron job that follows the pattern.
trigger:
  - babysit wa-
  - watch PR <num>
  - tick loop on PR <num>
  - cron job babysitting an AO worker
changelog:
  - "1.2.0 (2026-07-05): Add the executable self-cancel contract — every babysit prompt MUST invoke `babysit.py poll` (or `babysit.py babysit`) with `--cron-job-id $CRON_JOB_ID`. babysit.py gained a `cronjob_remove(job_id)` helper + `--cron-job-id` CLI arg + integration in the `is_pr_terminal` branch. Regression suite `skills/ao-babysit/scripts/test_babysit_self_cancel.py` (11 tests) enforces the contract. Bug-ref: 2026-07-05 thread C0AH3RY3DK6/p1783279995 — even after the v1.1.0 fix landed, babysit cron spam continued because the prompt-level self-cancel clause was unreachable: babysit.py had no way to know its own job_id."
  - "1.1.0 (2026-07-05): Add Phase 0.5 — terminal-state SELF-CANCEL via `cronjob action=remove job_id=$CRON_JOB_ID` (or `launchctl bootout` for launchd-managed babysits). Reference the `babysit-stale-watchdog` companion (every 30 min launchd watchdog at scripts/babysit_stale_watchdog.py) which catches stale babysits even if the in-script check is broken. Document the failure mode the 2026-07-05 babysit-wa-2403-PR7711 leak exposed: 251 polls over 9 days after PR #7711 merged because the original `babysit.py` only recognized 'PR created' as terminal, not 'PR MERGED on GitHub'. Bug-ref: thread C0AH3RY3DK6/p1783240445.370119."
  - "1.0.0 (2026-07-04): Initial authoring (existed on dirty staging branch dev1783194285; first landed on origin/main via cherry-pick of commit 7690435707 in PR replay b2ad00770d)."
---

# babysit-ao-pr-loop

A scheduled cron job ticks every N minutes on a single PR + AO worker pair. Each tick observes (does NOT modify or push) and posts a concise status update to a pre-known Slack thread. The loop is finite — it must terminate cleanly when the work is done, and stay quiet when nothing changed.

## When to load

- A scheduled cron job is targeting a single PR + worker session (e.g. `babysit wa-2403 on PR #7711`).
- A user asks you to "watch PR N", "tick loop on PR N", or "babysit worker wa-NNNN".
- You are inheriting an existing babysit loop mid-life and need to keep its cadence without re-creating its contract.

Do NOT load for: one-shot `agento_report` aggregations (use `agento_report`), PR bring-to-green interactive loops (use `drive-pr-to-green` / `finish-the-job`), full-time babysitting of a launched dev server or browser session (different domain).

## The contract (each tick)

Each tick has exactly five phases. Do them in this order, every tick:

### Phase 0 — Pre-flight (early-exit; run BEFORE composing any output)

Run these three checks. If ANY short-circuits the loop, do NOT post, do NOT nudge — produce the single suppression token or the single terminal message and exit.

1. **Is the work already done?**
   ```bash
   gh pr view <PR> --repo <OWNER>/<REPO> --json state,mergedAt,closedAt 2>&1
   ```
   - `state == "MERGED"` → terminal: post ONE single-line final message to the thread (e.g. `✅ PR <N> merged on <mergedAt>. Loop closing.`) and exit. Do not run subsequent ticks.
   - `state == "CLOSED"` (not merged) → terminal: post ONE escalation asking the user whether to keep the loop alive or stop it (your call: which is more useful here is up to the operator, but default to "stop, ask user"). Do not re-tick on your own.
2. **Is the worker session still alive?**
   ```bash
   ao session ls 2>&1 | grep -E "wa-<id>|<session_label>"
   ```
   - If the worker is gone AND the PR is not yet merged → terminal: post ONE final message noting the worker died, worker session no longer in `ao session ls`, and the loop is closing pending operator direction. Do not auto-respawn.
   - If the worker is gone AND the PR is already merged → terminal: post ONE final message acknowledging both ends and exit.
3. **Did anything actually change since the last tick?**
   - Compare current `git log origin/<base>..HEAD --since="<last_tick_ts>" --oneline` to the last-tick reading. If empty AND no new commit lands on `origin/<branch>` AND no new `ao` state change AND no CI rerun finished → suppress the full status update. Reply with the literal token `HEARTBEAT_OK` (the cron playbook contract) — do NOT post to Slack. If the cron also says "if absolutely nothing new, reply [SILENT]" and you have an empty commit delta AND no in-thread message is required → reply exactly `[SILENT]` per the cron playbook SILENT contract.

   ⚠️ **Pitfall — duplicate closeouts.** A common failure mode is two consecutive babysit ticks each independently noticing "work is done" and each posting a full closeout. After the FIRST tick posts the terminal message, every subsequent tick MUST short-circuit at Phase 0 step 1 even if `mergedAt` was already reported. Do not "refresh" a closeout. The first tick owns the close; subsequent ticks own silence.

### Phase 0.5 — SELF-CANCEL on terminal state (added 2026-07-05, v1.1.0)

After posting the terminal closeout in Phase 0 step 1 or step 2, the cron MUST also remove itself so no further ticks fire. The 2026-07-05 babysit-wa-2403-PR7711 incident exposed the failure mode: the cron reported MERGED every tick for 9+ days but never called `cronjob action=remove` on itself, producing 251 polls of duplicate closeouts to the same Slack thread.

**Mandatory self-cancel clause** — every babysit cron prompt MUST include this verbatim (the agent prompt, not just the skill):

```
After posting the Phase 0 terminal closeout, immediately call:

  cronjob action=remove job_id=$CRON_JOB_ID

If cronjob is unavailable (legacy launchd-managed babysit), fall back to:

  launchctl bootout gui/$(id -u)/<label>

If neither command is available, set Disabled=true in the plist template
and notify the operator to remove it manually. Then emit [SILENT] on
all subsequent ticks.
```

**Executable contract (added 2026-07-05, v1.2.0)** — the prompt-level clause above is necessary but not sufficient. The babysit MUST invoke `babysit.py poll` (or `babysit.py babysit`) with `--cron-job-id $CRON_JOB_ID` so the script can issue `cronjob action=remove` itself on terminal-PR detection. Without `--cron-job-id`, the prompt's "issue cronjob action=remove" instruction is unreachable from the script and the cron will leak past terminal-state until the watchdog catches it (up to 30 min).

Canonical prompt excerpt:

```bash
# Find this babysit's cron job_id once, then pass it to babysit.py on every tick
JOB_ID=$(cronjob list | jq -r '.jobs[] | select(.name=="<this babysit name>") | .id')
python3 ~/.hermes/skills/ao-babysit/scripts/babysit.py poll \
    --session "$SESSION_ID" \
    --slack-channel "$CHANNEL" \
    --slack-thread-ts "$THREAD_TS" \
    --task-summary "<task summary text including PR URL or PR #NNNN>" \
    --cron-job-id "$JOB_ID"
```

**Regression contract:** `skills/ao-babysit/scripts/test_babysit_self_cancel.py` enforces the executable side — that `babysit.py` defines `cronjob_remove()`, exposes `--cron-job-id` on both subcommands, and `poll()` invokes `cronjob_remove(cron_job_id)` in the terminal-PR branch. 11/11 tests pass; any future regression to babysit.py that drops the self-cancel plumbing fails the suite.

**Companion watchdog:** `~/.hermes/skills/babysit-stale-watchdog/SKILL.md`
ships a launchd plist (`ai.hermes.schedule.babysit-stale-watchdog`)
that runs every 30 min and disables any babysit cron whose referenced
PR is MERGED/CLOSED, even if the in-script Phase 0.5 self-cancel is
broken, missing, or running against an old prompt version. The
watchdog is the safety net; the in-script Phase 0.5 is the fast path.
Both layers are required.

**Audit recipe** for existing babysit crons that pre-date Phase 0.5
(the v1.0.0 babysit cron registry may have un-self-cancelled jobs):

```bash
cronjob list | jq '.jobs[] | select(.enabled and (.name|test("babysit|wa-[0-9]")))'
# For each match: gh pr view <PR-ref> --json state,mergedAt
# If MERGED or CLOSED, run: cronjob action=remove job_id=<id>
```

### Phase 1 — Observe (only if Phase 0 did NOT early-exit)

Run these and only these. Do NOT modify code; do NOT push; do NOT amend commits; do NOT call `ao send` or `git commit`.

1. **`git log origin/<base>..HEAD --oneline`** — what has the worker committed?
2. **`git status`** — any uncommitted work? (Untracked artifacts in the worktree like `.beads/.write.lock`, `specs/skeptic-report.json`, `ADVERSARIAL_REVIEW_*.md` are NORMAL residue from prior ticks, not new work. Do not flag them as "uncommitted work" unless they are fresh files on the fix-related paths.)
3. **`ao session ls | grep <session>`** — worker state (`working` / `pr_open` / `spawning` / `killed`).
4. **`gh pr view <PR> --repo <OWNER>/<REPO> --json headRefName,state,mergeable,commits,mergedAt`** — PR state.
5. **`gh pr checks <PR> --repo <OWNER>/<REPO>`** — CI state (only if Phase 0 didn't early-exit AND worker has pushed since last tick).
6. **`git log origin/<base>..HEAD --stat`** — only if there are new commits this tick.

Run these as a single parallel fan-out of `terminal` calls to keep ticks fast. NOT serial.

### Phase 2 — Decide nudges (only if Phase 0 didn't early-exit AND state has changed)

- If worker has NOT pushed in 30+ min AND state is still `spawning` or `working` → call `ao send <session> "STATUS?"` (the canonical nudge). Wait, do not inline-Enter; the manual Enter is the cron-playbook convention. After nudging, post a one-line note in the thread: `Nudged wa-NNNN at HH:MMZ — no push in N min.`
- If CI is red → summarize the failing check name + run URL in one line. Do not propose fixes; do not edit code. The babysit does not fix.
- If worker pushed new commits since last tick → summarize what landed (commit count + headline + one-line behavior delta), then run `gh pr checks` and post a 1-line green/red summary.
- If state == `pr_open` AND CI fully green AND reviewer-ready (no unresolved CodeRabbit CHANGES_REQUESTED, no Bugbot error-severity comments, mergeable=true) AND no skeptic request on the current head SHA yet → post `/skeptic` to the PR (NOT to the babysit thread) per the project's skeptic-cron contract. Verify with `gh pr comments` first.

### Phase 3 — Post the status update to the Slack thread (only if Phase 0 didn't early-exit)

Use the cron-deliverable template. Post ONE message per tick. Keep it under 12 lines.

```
:large_green_circle: _PR <N> babysit tick — HH:MMZ_
  • Worker state: <ao_session_state> | Branch: <branch> | HEAD: <short_sha>
  • Activity since last tick: <commit count> commits, headlines: <h1>; <h2>; ...
    OR "no new commits in <N> min"
  • CI: :white_check_mark: green OR :x: <failing check name> (<run_url>) OR :hourglass: pending
  • Reviewers: CodeRabbit <approve|request-changes|pending>; Bugbot <clean|errors|skipping>
  • Action taken this tick: <nudge / status-only / none>
  • Next checkpoint: <merge-ready / awaiting CI / awaiting CR / awaiting user>
```

If the worker has gone silent for a full 30 min window with no commits and no state change → reply `HEARTBEAT_OK` and DO NOT POST to Slack. This is the cron playbook's silence contract.

If the cron delivery instructions say "respond with exactly [SILENT]" AND there is genuinely nothing to report AND no nudge needed → reply exactly `[SILENT]` per that contract.

## Termination rules (loop closure)

When ANY of these are true, the loop is done:

1. PR state is `MERGED` (Phase 0 catches this).
2. PR state is `CLOSED` without merge, AND the operator has confirmed to stop.
3. Worker session is gone from `ao session ls`, AND the operator has confirmed to stop.
4. The cron schedule itself has been disabled (e.g. one-time cron fired + `--delete-after-run` completed).
5. The PR has been open > N days (configurable, default 14) with no movement AND no recent owner action → ask the operator.

When terminating:
- Post ONE final summary to the thread.
- Disable or self-delete the cron (one-time crons with `--delete-after-run` handle this automatically).
- If the cron is launchd-managed and meant to keep ticking, set `Disabled=true` in the plist template and `launchctl bootout gui/$(id -u)/<label>`.

## Anti-patterns (do NOT do)

- ❌ Reposting the same closeout message every tick after the work is done. **One tick owns the close; later ticks own silence.**
- ❌ Posting to Slack when nothing changed and the playbook says `HEARTBEAT_OK` / `[SILENT]`. Noise is worse than silence — the human inbox is the precious resource.
- ❌ Inlining `Enter` after `ao send "STATUS?"`. The cron-playbook convention is the literal newline-less stream; the worker ITSELF consumes the manual Enter as a session-input boundary.
- ❌ Editing code, even to fix a CI red. The babysit is observe-only. Drive-to-green goes to `drive-pr-to-green` or `finish-the-job`, which is a different loop.
- ❌ Auto-respawning the worker when it disappears. The operator decides.
- ❌ Treating untracked worktree files (`.beads/.write.lock`, `specs/*.json`, `ADVERSARIAL_REVIEW_*.md`) as "uncommitted work" — they are harness residue from prior ticks, not the fix's scope.
- ❌ Post-merge commits on the branch tip are NOT the babysit's problem. Drift accumulated after `mergedAt` belongs to a different audit; ignore it for status purposes.

## Tool usage notes

- Use `terminal` for `git`, `gh`, `ao` — fan-out parallel, not serial. A tick should not take more than 6 sequential tool calls.
- Use `mcp__slack__conversations_add_message` for thread replies. The cron invocation will pre-populate `channel_id` + `thread_ts`; verify before posting (per `slack-reply-inherit-thread-ts`).
- Use `mcp__slack__conversations_replies` once per tick if you need to confirm whether earlier ticks already posted a closeout.
- Do NOT use `mcp__slack__conversations_history` in full — paging through the channel is wasteful and may surface unrelated threads. The thread is the unit of work.

## Verification

Before posting the first tick of a new babysit loop, confirm:

- The cron is correctly delivering to the channel + thread configured by the operator. (The cron prompt usually specifies these.)
- The branch name + base branch + PR number are correct. (`gh pr view <N> --json headRefName,baseRefName`.)
- The worker session id is correct. (`ao session ls | grep <pattern>`.)
- If you inherit a mid-loop babysit, READ THE LAST 3 THREAD REPLIES before posting — if a recent tick already announced completion, post `[SILENT]` (do NOT duplicate the closeout).

## Support files

- `references/mid-loop-handoff.md` — pattern for inheriting a babysit loop from a previous session and confirming the thread state before posting.
- `references/cron-prompt-anatomy.md` — anatomy of a babysit cron task prompt (channel, thread_ts, branch, PR, worker session, beat) and how to extract them safely.
