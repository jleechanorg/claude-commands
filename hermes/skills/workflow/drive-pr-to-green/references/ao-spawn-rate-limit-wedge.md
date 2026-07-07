# AO spawn wedged on GH rate-limit (added 2026-07-05, PR #8070 dispatch)

Distinct failure mode from the zombie-cap recipe in `references/ao-spawn-cap-zombie-recovery.md`. Same symptom (`ao spawn` doesn't complete), different cause, different fix.

## Symptoms

- `ao spawn --claim-pr N` cold-starts (90-180s), gateway times out at the standard cold-start window
- A worktree stub appears at `/private/tmp/<repo>/pr-<N>-*` with a broken `.git` pointer — the worktree dir exists but the gitdir target does not
- `ao status` shows `GitHub rate limit detected, retrying in 1000ms … Gh CLI rate limit retries exhausted, trying REST API fallback … Gh CLI rate limit retries exhausted, no REST fallback available` in a tight loop
- The orchestrator daemon (`/tmp/ao_daemon.log`) is wedged and not progressing
- `gh api graphql …` and `gh pr comment …` both fail with `"API rate limit already exceeded for user ID 13840161"` (jleechan2015 token)

## Root cause

The GH user-token (`jleechan2015` per `gh auth status`) hit BOTH the GraphQL bucket (0/5000) AND the Core REST bucket (~5000/5000). `ao` tries GraphQL first (orchestrator's preferred path for repo/PR status), exhausts, falls back to REST, exhausts, retries — never recovers until the bucket resets.

REST and GraphQL are **separate** per-account 5000/hr buckets that drain independently (per `gh dual-bucket fallback` in `~/.cursor/rules/env-preferences.mdc`). One bucket can be at 0 while the other has headroom; both at 0 means total API unavailability for the token. Single-account setups (no alt token) cannot escape this until the bucket resets.

## Verification recipe

```bash
# 1. Confirm both buckets are exhausted (not just one)
gh api rate_limit --jq '.resources | {core: .core, graphql: .graphql}'

# Convert epoch resets to local-readable time:
date -r <epoch> "+%Y-%m-%d %H:%M:%S %Z"

# 2. Check the orchestrator daemon log is actually wedged (not just slow)
tail -50 /tmp/ao_daemon.log | grep -E "rate limit" | tail -5

# 3. Confirm worktree stub is broken (not just slow to attach)
ls /private/tmp/<repo>/pr-<N>-*/.git 2>/dev/null && \
  cat /private/tmp/<repo>/pr-<N>-*/.git
# If .git is a file pointing to a non-existent dir, the worktree is broken.
```

## Recovery — DO NOT keep retrying `ao spawn`

1. **Bail on the AO dispatch path.** The orchestrator cannot create sessions until the rate-limit resets. Each retry just adds to the daemon's retry-loop noise.
2. **Drive inline.** Create a fresh worktree at the PR head via `git worktree add -B <branch> /private/tmp/wa-pr<N>-drive origin/<branch>`, apply fixes, force-push with Form A lease. Only `git` operations are needed during the fix-apply phase; no GraphQL/REST API calls required.
3. **Schedule a one-shot cron** to handle the rate-limit-blocked steps after the bucket resets:

   ```bash
   hermes cron create "15m" \
     --name "wa-pr<N>-rate-limit-retry" \
     --deliver "slack:<channel_id>:<thread_ts>" \
     --repeat 1
   ```

   The cron body MUST include the exact sequence to run:
   - `bash ~/.hermes/lib/resolve_review_threads.sh <N> --owner <owner> --repo <repo>` (resolveReviewThread × N)
   - `gh pr comment <N> --repo <owner>/<repo> --body "@coderabbitai all good? …"` (fresh re-review ping)
   - Trigger Skeptic Self-Verify (workflow id via `gh workflow list …`)
   - Poll for `VERDICT: PASS` (max 10-15 min)
   - Re-run failed Green Gate via `gh api -X POST …/rerun-failed-jobs`
   - Post completion summary in-thread (channel + thread_ts)
   - **Explicit "DO NOT spawn new AO workers"** in the cron body — orchestrator still wedged until reset

4. **Post the in-thread Slack status now** with cron job_id and PROVISIONAL end-state per `incident-proposal-current-evidence-gate`. Format:

   ```
   :hammer_and_wrench: Drive PR #N progress — applied the N still-valid
   CodeRabbit fixes; pushed; wedged on GH rate limit.

   What landed at `<NEW_SHA>` (force-pushed to `<branch>`):
   • <fix 1>
   • <fix 2>

   Already-resolved (stale CodeRabbit threads on old head):
   • <thread 1>

   Wedged:
   • `gh api rate_limit`: GraphQL 0/5000 (exhausted), Core REST <n>/5000 (used). Reset at <HH:MM UTC> (~<n> min).
   • `ao` daemon in retry-loop wedged on GraphQL. Spawning a fresh AO worker blocked until reset.
   • Could not run `resolve_review_threads.sh` (GraphQL) nor post `@coderabbitai` re-review ping (REST exhausted). Both retry at <HH:MM UTC>.

   Cron scheduled: <job_id> (`<cron-name> (15m)`) at +15m.
   ```

5. **Final reply declares PROVISIONAL end-state** — fix code shipped on the remote (`push-pr-donot-stop-halfway` satisfied), but green-CI / skeptic-VERDICT / thread-resolution are pending the cron. Do NOT claim "done" until the cron reports back.

## Why this is correct

- The durable state (push to `origin/<branch>`) is on the remote — `push-pr-donot-stop-halfway` is satisfied.
- The cron is the watcher that picks up the rate-limit-blocked steps.
- Per `followup-promise-requires-cron` (SOUL.md), every "will retry after X" promise MUST be paired with a one-shot cron in the same turn.
- Per `one-time-status-cron-after-every-task` (SOUL.md), the cron job_id MUST be cited in the in-thread status.

## Why this is different from the zombie-cap recipe

| Dimension | Zombie-cap (cap-zombie-recovery.md) | Rate-limit wedge (this file) |
|---|---|---|
| Cause | Orchestrator's session table full of `[spawning]` zombies | GH user-token's GraphQL/REST API buckets exhausted |
| Detection | `ao session ls` shows many stale rows; spawn rejects with `>= cap (30)` | `gh api rate_limit` shows 0 remaining on both buckets; `ao_daemon.log` shows retry loop |
| Fix | Kill zombies + raise `AO_MAX_CONCURRENT_SESSIONS` env | Drive inline + schedule post-reset cron |
| Re-applicable after fix | Yes (spawn succeeds) | No (need to wait for bucket reset) |
| Skill touchpoint | `dispatch-task` umbrella | `drive-pr-to-green` Step 7c |

## Bug-ref 2026-07-05 PR #8070 dispatch

- Attempted `ao spawn --claim-pr 8070` at 18:55 UTC, gateway timed out at 180s.
- Worktree stub appeared at `/private/tmp/your-project.com/pr-8070-fix-bq-is-test-null-migration.` with broken `.git` pointer.
- `ao_daemon.log` showed ~30 retry-loop lines per second.
- Verified both buckets exhausted via `gh api rate_limit` (GraphQL 0/5000 reset 19:14 UTC, Core 1221/5000 reset 19:01 UTC).
- Pivoted to inline worktree at `/private/tmp/wa-pr8070-drive`, force-pushed commit `3dc87246b2` covering the 2 still-valid reviewer threads (jobComplete check + --apply SQL gate).
- Cron `23657868e035` (`wa-8070-rate-limit-retry (15m)`) scheduled at +15m to handle resolveReviewThread × 5, `@coderabbitai` re-review, Skeptic Self-Verify, poll for VERDICT, re-run Green Gate, post completion summary in channel `C0BCVG4F560` thread `1783269016.979119`.

## Long-term prevention (out of scope here, track as separate bead)

- Add a second GH token (`$USER-af` or similar) to the orchestrator config so a rate-limit wedge on one token doesn't kill both `ao` and inline `gh api` calls.
- Add a launchd/ cron pre-check that runs `gh api rate_limit` before `ao spawn` and refuses to spawn when both buckets are <100 remaining.
- Add a `resolve_rate_limit_wedge.sh` script that monitors `ao_daemon.log` for retry-loop patterns and triggers the cron-recovery recipe automatically.