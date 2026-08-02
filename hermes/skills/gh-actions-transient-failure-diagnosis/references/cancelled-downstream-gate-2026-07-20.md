# Cancelled downstream gate (Green Gate aggregator case)

**Verified 2026-07-20 on $GITHUB_REPOSITORY PR #8466 head `7041776da1`.**

## Symptom

A Green Gate (or similar N-green aggregator) check-run fails, but inspecting its job log reveals:

```
GATE-X FAIL: <gate_name>_wait job did not complete successfully (result=cancelled, <gate_name>_gate=unset) — see that job's log for the detailed GATE-X WAIT/FAIL trace
```

Other aggregator gates pass. Example log lines from the same Green Gate aggregator job:

```
PRECHECK_RESULT: success          # Gates 1-6 PASS
BUGBOT_GATE: PASS                  # Gate 4 PASS
SMOKE_RESULT: cancelled            # Gate 8 CANCELLED — aggregator propagates as FAIL
SMOKE_GATE:                        # unset because the cancelled job never wrote its output
```

## Root cause

The downstream gate job (e.g. `smoke_gate_wait`) was **cancelled** before it could write its output. The aggregator's `if [ "$SMOKE_RESULT" != "success" ]; then ... exit 1` is correct fail-closed behavior on missing input — the aggregator is innocent. The cancelled job is also typically innocent: cancellations are usually caused by runner-pool pressure, sibling-job failures that propagate cancellation, or self-hosted runner preemption. Almost never the cancelled workflow's own code.

## Recovery (priority order)

1. **`gh run rerun <aggregator_run_db_id> --failed`** — re-runs only the failed jobs in the same workflow. Works for `workflow_dispatch` runs. For `pull_request`-triggered workflows, this may re-cancel because the sibling runners are still under pressure.
2. **Empty-commit retrigger** (preferred for `pull_request` workflows) — pushes a new SHA, fires `pull_request` event for all dependent workflows. Use the recipe from `references/gh-actions-transient-503-2026-07-20.md` (same shape: `git -c user.name=<u> -c user.email=<u>@users.noreply.github.com commit --allow-empty -m 'ci: retrigger after <gate> cancel in aggregator run <id>' && git push origin HEAD`). The cancelled sibling usually re-runs clean because runner-pool pressure has cleared.
3. **Re-dispatch the cancelled job's workflow** (not Green Gate itself) via `gh workflow run <gate_workflow>.yml -f pr_number=<N>`. Verify `headBranch` after dispatch — `gh workflow run` lands on `head_branch=main` per `drive-pr-to-green` v2.5.6.
4. **Wait and retry** — if (1)–(3) all re-cancel, runner pool is genuinely saturated. Wait 15-30 min and retry; do not loop rapidly.

## Diagnostic commands

```bash
TOKEN="$(gh auth token)"

# Find the aggregator check_run_id from statusCheckRollup
gh pr view <N> --repo <OWNER>/<REPO> --json statusCheckRollup

# Resolve the aggregator's run databaseId (NOT the human-readable run_number)
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/check-runs/<aggregator_id>" \
  | jq '.check_suite'
# → aggregator run db_id (long numeric, NOT #N style)

# Find the cancelled downstream job
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/runs/<aggregator_run_db_id>/jobs" \
  | jq '.jobs[] | {id, name, conclusion}' | grep -i cancelled

# Read the aggregator log (always unzip the result)
curl -fsS -L -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/jobs/<aggregator_job_id>/logs" \
  -o /tmp/agg-job.zip
python3 -c "
import zipfile
with zipfile.ZipFile('/tmp/agg-job.zip') as zf:
    for name in zf.namelist():
        print(f'=== {name} ===')
        print(zf.read(name).decode('utf-8', 'replace'))
"

# Look for: PRECHECK_RESULT, BUGBOT_GATE, SMOKE_RESULT lines.
# The cancelled gate will show SMOKE_RESULT=cancelled and SMOKE_GATE=unset.
```

## Anti-patterns

- ❌ **Investigating the cancelled job's code/config.** Cancellations with no log output are almost never caused by the workflow's own logic. Read the aggregator's gate-trace line first; if it says `result=cancelled`, the gate code is fine.
- ❌ **Re-running via `gh workflow run` on the aggregator itself.** Green Gate aggregator is `pull_request`-triggered — `gh workflow run` lands on `head_branch=main` and is useless per `drive-pr-to-green` v2.5.6.
- ❌ **Rapid retry loops.** If `gh run rerun --failed` and empty-commit retrigger both re-cancel, runner pool is saturated. Pause 15-30 min before retrying.
- ❌ **Trusting `statusCheckRollup` alone.** The aggregator's `conclusion: failure` shows in `statusCheckRollup` but the *cause* (which gate cancelled) only shows in the aggregator's job log.

## Why this trap is subtle

A Green Gate `failure` looks like a real CI failure. The natural response is "find the failing gate" and start chasing the named gate's code. But when the named gate is `cancelled` (not `failed`), the gate code is innocent — the runner system killed it. This is the symmetric trap to the `actions/github-script` 503 case in v1.0.0: same failure headline ("Green Gate failed"), but the root cause is *runner pool* not *GitHub API* or *workflow code*.

The aggregator's `exit 1` on `result=cancelled` is correct fail-closed behavior — without that, a cancelled gate would silently pass. The bug is in the runner pool, not the aggregator logic.

## Cross-reference

- Verified reproduction: PR #8466 head `7041776da1` / aggregator job #88254838835 / run #29710376992
- Aggregator log: `GATE-8 FAIL: smoke_gate_wait job did not complete successfully (result=cancelled, smoke_gate=unset) — see that job's log for the detailed GATE-8 WAIT/FAIL trace` at 02:15:01.9548046Z
- Same PR also exhibited the v1.0.0 transient-503 case on a separate workflow (Auth Browser Tests job #88252983872, run #29709994853). Different root cause, same aggregator failure shape — both fixable via empty-commit retrigger.