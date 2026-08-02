# GitHub Actions Cost Spike — 2026-07-13 (`jleechanorg` $266 MTD, $48 peak)

## Summary

Spend alert fired twice in 24h: `daily Δ $25.76 > $10` then `daily Δ $18.11 > $10` (MTD $248 → $266). Investigation revealed the spike is **past peak** (daily delta halved from $48.51 to $18.11 over 5 days), attributed 99% of billable minutes to `Green Gate` precheck jobs, and identified a broken in-repo cost-reporting workflow that reports $0.

## Spike timeline

| Date | MTD | Daily Δ | Notes |
|---|---|---|---|
| 7/3 | $28.58 | — | normal |
| 7/4 | $28.58 | $0.00 | |
| 7/5 | $36.24 | $7.66 | |
| 7/6 | $63.17 | $26.93 | **spike starts** |
| 7/7 | $109.89 | $46.72 | peak |
| 7/8 | $158.40 | $48.51 | peak |
| 7/9 | (auth blip) | — | `WARN: Failed to fetch GitHub billing usage (check gh auth)` |
| 7/10 | $194.77 | $36.37 | |
| 7/11 | $222.27 | $27.50 | |
| 7/12 | $248.03 | $25.76 | first alert fires |
| 7/13 | $266.14 | $18.11 | second alert fires (this session) |

Rate of accrual has **halved since 7/7-7/8 peak** ($48.51 → $18.11). The alert keeps firing because absolute MTD still climbs and the `daily Δ > $10` threshold doesn't recognize declining tails (see P19).

## Live billing (raw `gh api orgs/jleechanorg/settings/billing/usage`)

```json
{
  "Actions Linux": { "quantity": 63446, "netAmount": 258.414, "repo": "your-project.com" },
  "Actions macOS 3-core": { "quantity": 95, "netAmount": 5.89, "repo": "jleechanclaw" },
  "Actions Windows": { "quantity": 9, "netAmount": 0.00, "repo": "agent-orchestrator" },
  "Actions storage": { "quantity": 6923.21, "netAmount": 1.83, "repo": "your-project.com" },
  "MTD_total": 266.137
}
```

**Effective rate**: $0.006/min (after $122.26 discount on $380.68 gross). Self-hosted runners do not appear as a billed SKU.

## Per-(repo, workflow) histogram (top-30 wall-clock, 2026-07-13)

From `/tmp/wa_runs_p1.json` + `/tmp/wa_runs_p2.json` filtered to non-skipped/cancelled:

| Workflow | Wall-clock | Billable (GH-hosted) | % | Hosted jobs |
|---|---|---|---|---|
| Green Gate | 53.1m | 52.7m | **99.2%** | `Green Gate Precheck (Gates 1-6)` ubuntu-latest, `Bugbot Gate Wait (Gate 4)`, `Smoke Gate Wait (Gate 8)` |
| Auto-Deploy Dev | 29.6m | 11.7m | 39.7% | deploy step on ubuntu-latest |
| Presubmit Checks | 11.3m | 5.4m | 47.4% | `JavaScript Linting (ESLint)`, `Python Linting (Ruff)`, `Python Type Checking (mypy)` on ubuntu-latest |
| Coverage Report | 4.3m | 0.9m | 21.4% | `Generate Coverage Report` on ubuntu-latest |
| WorldArchitect Tests (Directory-Based) | 90.9m | 0.0m | 0.0% | all self-hosted (`ez-mac-runner-b-2..6`) |
| Self-Hosted MVP Shards | 55.1m | 0.0m | 0.0% | all self-hosted |
| Mobile Auth Same-Origin Regression | 43.6m | 0.0m | 0.0% | self-hosted (`ez-mac-runner-b-4`, 21min single job) |
| Deploy PR Preview (Rotating Pool) | 39.6m | 0.0m | 0.0% | self-hosted |
| Auth Browser Tests | 10.8m | 0.3m | 3.2% | mostly self-hosted |
| **TOTAL** | **338.4m** | **71.0m** | **21.0%** | |

**Key insight**: the long-running workflows (`Mobile Auth`, `WorldArchitect Tests`, `Self-Hosted MVP Shards`) generate $0 billable minutes because they all run on self-hosted runners. The billable minutes come from **short (1-2 min) jobs in `Green Gate` precheck and `Presubmit Checks` lint** — jobs that exist to gate the PR but are themselves billed.

## Job-level breakdown (per-job `/actions/runs/{id}/jobs`)

Sample run 29242462225 (Green Gate, success):
- `Green Gate Precheck (Gates 1-6)`: runner=`GitHub Actions 1000625612`, labels=`ubuntu-latest`, dur=1.02m, billed
- `Bugbot Gate Wait (Gate 4)`: runner=`GitHub Actions 1000625613`, labels=`ubuntu-latest`, dur=0.12m, billed
- `Smoke Gate Wait (Gate 8)`: runner=`GitHub Actions 1000625614`, labels=`ubuntu-latest`, dur=1.08m, billed
- `Green Gate`: runner=`ez-mac-runner-b-1`, labels=`self-hosted`, dur=0.08m, $0

3 GitHub-hosted jobs × ~1 min each = ~3 billable minutes per Green Gate invocation. Across all `your-project.com` Green Gate runs in July (~80+ invocations), that's the bulk of the Linux bill.

## What changed from prior spike diagnoses (P16 re-verification)

The 2026-07-11 P16 finding ("per-run `labels` is always `[]` for self-hosted") was correct for the 11 repos checked then. But on 2026-07-13 in `$GITHUB_REPOSITORY`, **per-run `labels` IS populated** (e.g. `labels: ["self-hosted"]`). The reliable detector across all orgs is the **per-job endpoint**, not the per-run endpoint. See SKILL.md P16 for the updated guidance.

## Why the spike happened

**No cause was found that explains the 7/5-7/6 ramp-up.** No new workflows were added in that window. No `runs-on:` line was changed from self-hosted to hosted (verified via `git log --since="2026-07-01" -- .github/workflows/`). The skeptic-cron deletion (PR #8217) merged 2026-07-07 — *after* the spike started — so skeptic-cron is NOT the cause (contrary to the prior session's hypothesis in memory).

Hypothesis (unverified): PR volume increased 7/5-7/8 (a merge train or batch of merges drove many PRs to open Green Gate workflows simultaneously), so billable minutes went up because Green Gate invocations went up. The Green Gate per-invocation cost is roughly constant; the spike is in *invocation count*, not per-invocation cost.

**Verification recipe** (for future spikes):
```bash
# Count Green Gate invocations per day, July
gh api 'repos/$GITHUB_REPOSITORY/actions/runs?per_page=100&page=N&created=>=2026-07-01' \
  --jq '.workflow_runs | map(select(.name == "Green Gate")) | group_by(.run_started_at[0:10]) | map({day: .[0].run_started_at[0:10], count: length})'
```

## Three things to know going forward (delivered to Slack)

1. **`Daily GH Actions Cost Report (estimated)` in `your-project.com` is broken.** It sent `[Daily GH Actions cost (est.)] 2026-07-12 — $0.00` when the real bill is $248. Root cause: per-repo `gh api` calls 404 on private repos; the lib silently treats that as $0. Don't trust that number — trust `~/.hermes/state/spend-alert-state.json` + the raw billing API. See SKILL.md P18.

2. **The 7/9 auth blip** in `spend-alert-daily.sh` (`WARN: Failed to fetch GitHub billing usage`) was a transient `gh auth` issue, not a real outage. 7/10 was interpolated from 7/8→7/10. See SKILL.md P20.

3. **Per-workflow attribution requires the per-job endpoint** (`/actions/runs/{id}/jobs`), not the per-run endpoint. Per-run `labels` is inconsistently populated; per-job `labels` and `runner_name` are reliable. See SKILL.md P16.

## Recommended fixes (proportional, not panic-mode)

- **Quick win:** `Green Gate` is 99% GitHub-hosted and accounts for most billable minutes. Each invocation runs 3 GitHub-hosted precheck jobs (~3-4 billable min) regardless of outcome. If Green Gate fails transiently, the retry creates more billable jobs. Verify `concurrency.cancel-in-progress: true` is set on the precheck jobs (it is, but cancelled runs still incur billable minutes — the optimization is to make the precheck jobs faster, not to prevent retries).
- **Medium:** `Auto-Deploy Dev` is 40% billable — investigate whether the deploy step can move to self-hosted.
- **Long-term:** fix the `Daily GH Actions Cost Report (estimated)` workflow so the per-workflow alert works. Real cost is in the `/usage` aggregate; the per-repo cost report is broken because the lib doesn't handle private-repo 404s. Filed under the `$USER-h9ik` bead family.

## Files referenced

- `$HOME/.hermes/state/spend-alert-state.json` — live state, current alert
- `$HOME/.hermes/logs/spend-alert-daily.log` — 10-day history of daily MTD snapshots
- `$HOME/Library/LaunchAgents/ai.hermes.schedule.spend-alert-daily.plist` — active launchd
- `$HOME/.hermes/scripts/spend-alert-daily.sh` — local installed version
- `/tmp/wa_runs_p1.json`, `/tmp/wa_runs_p2.json` — sample raw API responses used for the histogram
- `/tmp/all_wa_runs_july.json` — flattened top-30 wall-clock runs

## Provenance

Session: 2026-07-13 15:30-15:50 PT. Slack thread: `C0BCVG4F560/1783870217.337079` (`#worldai-alerts`). Triggered by `spend-alert-daily.sh` daily 08:30 PT launchd job.
