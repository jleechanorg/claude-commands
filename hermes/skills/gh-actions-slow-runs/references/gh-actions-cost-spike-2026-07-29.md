# GH Actions cost-spike reference: "still $5/day" diagnosis (2026-07-29)

## Trigger
Jeffrey asked: *"why is gh actions cost still $5 a day or so"* — daily billed amount on the org billing page (https://github.com/organizations/jleechanorg/settings/billing/usage?period=3&group=0&customer=36837722&query=product:actions) showed $5.96 / $5.82 / $7.16 / $5.96 / $22.52 / $21.92 etc.

## What the spend-alert state file said
`~/.hermes/state/spend-alert-state.json`:
```json
{
  "month": "2026-07",
  "gh_mtd": 500.27,
  "gh_delta": 7.15,
  "gh_roll": [15.20, 61.11, 18.14, 11.29, 18.30, 25.44, 7.15]
}
```
gh_roll oldest → newest. Peak was day 2 (7/22 = $61.11). Today = $7.15. Clear declining trend. Per P19: spike is past peak, no action needed — but the user asked, so we still ran the histogram to identify what's actually costing the residual $5-7/day.

## What the billing API said
`gh api orgs/jleechanorg/settings/billing/usage --paginate` for July 2026:
- `Actions Linux` (your-project.com): 110,664 min, gross $663.98, discount $176.44, **net $487.54**
- `Actions macOS 3-core` (jleechanclaw): 325 min, **net $20.15**
- `Actions storage` (your-project.com): 11,653 GB-hours, **net $3.42**
- `Actions Windows` (agent-orchestrator): 49 min, **net $0.00** (100% discount)
- LFS misc: <$0.05
- **July MTD total: ~$511**

Pricing per SKU from the billing API:
- Linux: $0.006/min (after discount; gross $0.008)
- macOS 3-core: $0.062/min
- Windows: $0.01/min

## What the histogram (first attempt) said — WRONG
Ran the existing `scripts/per-repo-workflow-billing-histogram.py` (v1.4.0's YAML-grep classifier):
- Total 7d hosted cost: $97.58 = $13.94/day (much higher than reality)
- Top offender: `your-project.com/Test` at $11.85 (45-min runs from `ez-mac-runner-b-*` — actually self-hosted)

The classifier called everything "hosted" because the per-run `runner_name` field was empty for self-hosted runs. P16 was documented in SKILL.md but the script hadn't been updated.

## What the manual per-job probe revealed
Spot-checked `actions/runs/{id}/jobs` on the top 8 runs in `your-project.com` and `worldai_claw`:
- All 8 had `runner_name = "ez-mac-runner-b-{1-6}"`, `labels = ["self-hosted", "self-hosted-macos"]`
- These were SELF-HOSTED, not hosted. The per-run object was missing the runner field; only the per-job object had it.

## What the histogram (with corrected classifier) said — RIGHT
Re-classified all 2,833 runs using the per-job endpoint with 20-worker parallel fetch + on-disk cache (84s total). Final results:

| Runner | Runs |
|---|---:|
| Hosted | 2,405 |
| Self-hosted | 295 |
| Unknown (no labels) | 133 |

**7-day hosted cost: $44.96 = $6.42/day**

| Repo×Workflow (top 5) | 7d cost | Daily | Reality |
|---|---:|---:|---|
| jleechanclaw / Staging Canary Full (self-hosted) | $7.67 | $1.10 | **Misnamed**: actual runner is `GitHub Actions 1000651496` / `ubuntu-latest` |
| your-project.com / Presubmit Checks | $7.19 | $1.03 | `runs-on: ubuntu-latest` |
| your-project.com / WorldArchitect Tests (Directory-Based) | $5.84 | $0.83 | `runs-on: ubuntu-latest` |
| your-project.com / Coverage Report | $4.44 | $0.63 | `runs-on: ubuntu-latest` |
| worldai_claw / Green Gate | $3.71 | $0.53 | `runs-on: ubuntu-latest` (100/128 hosted) |

**Top 3 repos** = 98% of hosted cost:
- `your-project.com` $26.02
- `worldai_claw` $9.35
- `jleechanclaw` $8.97

## Two real bugs found
1. **P21 — workflow NAME is not a runner-type signal.** "Staging Canary Full (self-hosted)" was 104/134 GitHub-hosted despite the name. The YAML-grep `is_self_hosted()` heuristic in the script returned True for any workflow whose YAML or name contained "self-hosted", silently misclassifying 104 runs and hiding $7.67/day of cost.

2. **P22 — per-job endpoint with parallel fetch is required.** Sequential `gh api` calls for 2,833 runs took >600s and timed out. 20-worker ThreadPoolExecutor completed in 84s. The previous script was silently timing out and producing incomplete histograms on this workload size.

## Script changes
`scripts/per-repo-workflow-billing-histogram.py`:
- Replaced `is_self_hosted()` (YAML-grep) with per-job endpoint classifier
- Added `classify_run(rid, repo)` function called via `ThreadPoolExecutor(max_workers=20)`
- Cache results to `~/.hermes/cache/jlorg-run-classification.json` so re-runs skip the API
- YAML-grep kept as fallback for runs where per-job call 404s (deleted from history)

## What the user was told
- $5-7/day is real — matches the histogram's $6.42/day average
- The 7-day roll is clearly declining from peak (P19: spike past peak)
- Top 8-12 workflows actually pin to `runs-on: ubuntu-latest` despite having "(self-hosted)" or "Self-Hosted" in their names
- 3 repos = 98% of hosted cost
- Three options posted: A) auto-generate per-workflow PRs (needs `MERGE APPROVED`), B) inline 1-2 cheap wins + queue rest, C) just audit memo no infra touch
- (User has not yet replied at the time of this reference write-up)

## Lessons captured
- **P21 added to SKILL.md**: never trust workflow name or YAML-grep of "self-hosted" as runner-type signal. Per-job endpoint (`actions/runs/{id}/jobs`) is the only reliable source.
- **P22 added to SKILL.md**: per-job classification needs parallel fetch + cache for orgs with >500 runs in window. Sequential burns 10+ minutes.
- **P19 reinforced**: 7-day-roll read of `gh_roll` array is the right first step when someone asks "still $X/day" — confirms spike-past-peak before drilling in.
- **Script gap closed**: P16 was documented in v1.4.0 but the script wasn't updated. v1.5.0 closes the gap. **Any histogram output from 2026-07-11 through 2026-07-29 should be considered wrong** — re-run after the script update.