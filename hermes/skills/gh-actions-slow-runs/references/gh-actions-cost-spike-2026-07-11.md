# GH Actions Cost-Spike — 2026-07-11 per-(repo, workflow) histogram

**Provenance:** jleechanorg spend alert fired in Slack #worldai-alerts (channel C0BCVG4F560, thread `1783697404.378359`): "GitHub Actions daily Δ $36.37 > $10 (MTD $194.77)" / "GitHub Actions 7d sum $175.78 > $70". User reply: "Why is it costing so much? Let's investigate and fix."

## Outcome

Diagnosed in ~25 minutes using a NEW per-(repo, workflow) histogram from the `actions/runs` API. Root cause: `.github/workflows/skeptic-cron.yml` on 3 repos (`ai_universe`, `ai_universe_frontend`, `worldai_claw`) had three compounding bugs:

```yaml
on:
  schedule:
    - cron: '*/20 * * * *'           # every 20 min, 72 runs/day/repo
concurrency:
  cancel-in-progress: false          # runs stack, never cancel each other
runs-on: ${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS
            || '["self-hosted","Linux","ARM64","agent-orchestrator"]') }}
# ↑ no SELF_HOSTED_RUNNER_LABELS org var set → label mismatch
# → GitHub falls back to ubuntu-latest @ $0.008/min
```

Each run installed `agent-orchestrator`, posted triggers to all open PRs, sat ~30 min waiting. ~72 runs/day × 3 repos × ~30 min × $0.008 = **~$52/day**, **90.6% of the 7-day bill**.

The chore PRs that removed `skeptic-cron.yml` had ALREADY landed in all 42 jleechanorg repos on July 9-10 (per `search/commits?q=org:jleechanorg+remove+skeptic-cron+automation`) — the file is gone from `main` everywhere. But queued runs from before the deletion were still draining. The deletion commit SHA (`3f96d02e` on ai_universe_frontend) was the head SHA on every "Skeptic Cron" run, all marked `conclusion=cancelled`. Today's $0.45 spend is just routine PR/tag-listener noise — **no action needed beyond waiting for the queued runs to drain**.

## The recipe — per-(repo, workflow) histogram from actions/runs

### Step 1 — List all repos in the org

```bash
gh api 'orgs/jleechanorg/repos?per_page=100&type=private' --paginate \
  | jq -s 'map(.[]) | map(.full_name)'
```

Returns 42 repos. No `has_workflows` field on this endpoint — don't trust it.

### Step 2 — Per-repo run fetch (manual pagination)

```bash
# IMPORTANT: --paginate collides with the created=>= filter and returns null workflow_runs
# Use manual page=1..N with date-only filter instead.
since="2026-07-04"
gh api "repos/jleechanorg/${repo}/actions/runs?per_page=100&page=${page}&created=>=${since}" \
  | jq -c '.workflow_runs // [] | .[] | {id, name, event, run_started_at, updated_at, status, conclusion, path}'
```

**Pitfall — `created=>=ISO` URL form**: gh's `--paginate` strips URL query strings differently and returns `total_count: 0, workflow_runs: []`. Use date-only `created=YYYY-MM-DD` (no leading operator).

### Step 3 — Self-hosted runner detection (DO NOT trust run-object labels)

The `workflow_runs[].labels` field is `[]` for self-hosted runners (verified 2026-07-11 across 11 repos / 1402 runs). To classify runner type, fetch each unique workflow YAML and grep:

```bash
gh api "repos/${repo}/contents/${path}?ref=main" \
  | jq -r '.content // empty' | base64 -d 2>/dev/null \
  | grep -E 'self-hosted|SELF_HOSTED' || true
```

If the YAML contains `self-hosted` or `SELF_HOSTED`, classify as self-hosted; otherwise use `run_started_at`-derived heuristic from `labels` (will always be `linux-github-hosted` for self-hosted runs because labels is `[]`).

### Step 4 — Cost computation

Pricing map (verify against `usageItems[].pricePerUnit` for your org):

| Runner type | Effective rate | Source |
|---|---|---|
| GitHub-hosted Linux (`ubuntu-latest`) | $0.008/min | Standard rate; ~$0.006 effective after discount in some orgs |
| GitHub-hosted macOS 3-core | $0.08/min | Standard |
| GitHub-hosted Windows | $0.016/min | Standard |
| Self-hosted (any OS) | $0 (your host cost) | Does NOT appear in `usageItems` |
| Actions storage | $0.00033602/GB-hr | Storage GB-hours |

### Step 5 — Aggregation (the meat)

Group by `(repo, workflow_name, event, runner_type)` and sum `(updated_at - run_started_at) × rate`. Filter `status == "completed"` only (in-progress runs haven't billed yet but will when they finish).

Output format (top 25 from 2026-07-11):

```
   12049.2min  $ 96.39   184runs  jleechanorg/ai_universe_frontend     Skeptic Cron  schedule  linux-github-hosted
   11174.5min  $ 89.40   191runs  jleechanorg/ai_universe              Skeptic Cron  schedule  linux-github-hosted
    5334.8min  $ 42.68   115runs  jleechanorg/worldai_claw             Skeptic Cron  schedule  linux-github-hosted
    2550.4min  $ 20.40    92runs  jleechanorg/worldai_claw             Test          push      linux-github-hosted
    2387.4min  $ 19.10    92runs  jleechanorg/worldai_claw             CodeRabbit…   push      linux-github-hosted
    ...
```

The reusable script `scripts/per-repo-workflow-billing-histogram.py` does this in ~60s for 42 repos (10-worker ThreadPoolExecutor).

## The "deleted workflow draining" detection

When the histogram shows a workflow that no longer exists in `.github/workflows/` on `main`:

1. Check the run's `head_sha` — if every draining run points at the deletion-commit SHA, you've confirmed the drain
2. The `conclusion` will be `cancelled` (the deletion commit killed them)
3. Estimate drain time: `(max(updated_at) - deletion_commit_time)` typically 24-48h for ~30-min scheduled runs
4. **Do nothing** — the deletion already happened; just wait for the queue to drain

If you need to accelerate: there's no API to bulk-cancel-by-workflow-name. Use the Actions UI or `gh run cancel <id>` per-run (not worth it for $30-50 of one-time drain cost).

## Per-day breakdown (the smoke gun)

| Day | $ total | Skeptic Cron share | Pattern |
|---|---|---|---|
| Jul 4 | $0.34 | 64% | Baseline (Skeptic Cron on self-hosted — small minutes) |
| Jul 5 | $0.55 | 96% | Baseline |
| Jul 6 | **$71.39** | **94%** | Spike starts — Skeptic Cron on 3 repos × $22 each |
| Jul 7 | $76.68 | 92% | Sustained |
| Jul 8 | $47.80 | 89% | `worldai_claw` self-hosted matcher starts working (drops out of spike) |
| Jul 9 | $46.97 | 98% | Sustained |
| Jul 10 | $44.52 | 86% | Cancellation drain begins |
| Jul 11 | $3.65 | 0% | Back to baseline ✅ |

The day-by-day pattern is the smoking gun — when Skeptic Cron ran on self-hosted (Jul 4-5), cost was trivial. When it fell through to hosted (Jul 6 onwards), cost exploded. The fall-through was caused by the `vars.SELF_HOSTED_RUNNER_LABELS` fallback not matching any registered runner.

## Comparison to 2026-07-08 spike

The 2026-07-08 `your-project.com` spike (see `references/gh-actions-cost-spike-2026-07-08.md`) was a **different pattern**: workflows actively pinned to `runs-on: ubuntu-latest` in 3 PRs (#8172, #8141, #8142). The fix was to revert those PRs.

The 2026-07-11 spike was a **different pattern**: workflows that *looked like* self-hosted but fell through to hosted because the label matcher failed. The fix is already done (chore PRs removed the workflow); just waiting for the queue.

Same umbrella skill, two different root causes. C1-C6 (the 2026-07-08 path) handles "actively pinned to hosted". C7 (the 2026-07-11 path) handles "falling through to hosted via label mismatch or deleted-workflow drain".

## Prevention follow-up

Filed as bead `$USER-h9ik` (2026-07-11). Two durable fixes at the harness level:

1. **Per-(repo, workflow) daily-cost histogram cron** that alerts at >$5/day OR >$50/week per single workflow. The current `spend-alert-daily.sh` only fires on org MTD delta — too late to catch the spike in hour 1.

2. **`gh-actions-schedule-lint`** pre-commit/repo-scan that flags:
   - Any `cron:` denser than `0 */N * * *` (every-N-hours is OK, every-N-minutes is a footgun)
   - WITHOUT paired `concurrency.cancel-in-progress: true`
   - OR any `runs-on: ${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS || '...') }}` where the fallback contains labels — the fallback defeats the org-var contract

Both can ship as a single weekly `gh-actions-schedule-lint` cron + a `per-workflow-billing-alert` cron that calls the histogram script daily with a $5/workflow threshold.

## Cross-references

- `gh-actions-slow-runs/SKILL.md` § C7 — the histogram recipe
- `gh-actions-slow-runs/SKILL.md` Pitfalls P15, P16, P17 — the new gotchas
- `scripts/per-repo-workflow-billing-histogram.py` — the reusable histogram builder
- `~/.hermes/state/spend-alert-state.json` — rolling 7-day delta state (the alert source)
- `~/.hermes/scripts/spend-alert-daily.sh` — the cron that fired the alert
- `br create $USER-h9ik` — bead for the prevention work
