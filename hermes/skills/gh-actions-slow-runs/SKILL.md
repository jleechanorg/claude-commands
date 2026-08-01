---
name: gh-actions-slow-runs
description: "Diagnose and fix slow OR expensive GitHub Actions runs: runner-pool saturation analysis, stuck-run cancellation, fetch-depth optimization, billing-API cost-spike triage (hosted-vs-self-hosted runner switch detection, per-SKU cost breakdown, revert-PR identification), AND per-(repo, workflow) histogram from the `actions/runs` API for catching deleted-workflow drains and label-match fallthroughs that the billing API alone cannot attribute. Use when Actions runs exceed a time budget, many in_progress runs aren't completing, a spend-alert fires for Actions billing (daily delta or 7d sum over threshold), OR the billing-API points at a spike but the workflow-level grep on `main` doesn't reveal the culprit."
version: 1.5.1
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [GitHub, Actions, CI, runner-pool, fetch-depth, performance, self-hosted, cost, billing, per-workflow-histogram, deleted-workflow-drain]
    related_skills: [github-pr-workflow, hermes-health-check, drive-pr-to-green]
---
# GitHub Actions Slow-Run Diagnosis & Fix (v1.5.1)

When GitHub Actions runs exceed a time budget (e.g. "should never be more than 20 min") or the Actions UI shows many `in_progress` runs that aren't completing, this is a **runner-pool / throughput** problem — fundamentally different from "my tests failed." The fix is infrastructure-level (cancelling stuck runs, optimizing checkout speed), not code-level.

**v1.5.1 (2026-07-30):** Fixed SyntaxError in `scripts/per-repo-workflow-billing-histogram.py` — `global CACHE_PATH` was placed after the argparse default that reads it, producing `SyntaxError: name 'CACHE_PATH' is used prior to global declaration` on every run. Fix hoists `global CACHE_PATH` to the first executable line of `main()`, reads the default from `JLORG_RUN_CLASSIFICATION_CACHE` env var, and re-applies the user's `--cache-path` after `parse_args()`. Added **P23 — per-job `runner_name: null, labels: ['ubuntu-latest']` is GitHub's hosted-fallthrough signal** (NOT a normal hosted runner; it specifically means self-hosted queue timeout → GitHub silently billed at $0.008/min). Added **P24 — `vars.SELF_HOSTED_RUNNER_LABELS || '[fallback]'` is only a fallback if the org-var is unset**; once it's set, the workflow correctly routes to self-hosted runners — the fallthrough then becomes a per-job timeout problem (P23), not a label problem. Added `references/spend-alert-incident-log.md` with the full session log for the 2026-07-29 `your-project.com` incident (top 3 cost drivers, smoking-gun commits, fix recipes).

**v1.5.0 (2026-07-29):** Added **P21 — workflow NAME is NOT a runner-type signal** ("Staging Canary Full (self-hosted)" in `jleechanorg/jleechanclaw` ran on `GitHub Actions 1000651496` / `ubuntu-latest`; the histogram script's `is_self_hosted()` was returning True on the YAML-grep heuristic, hiding $7.67/day of cost). Added **P22 — sequential per-job classification times out at 600s for 2k+ runs**; parallel 20-worker fetch with cache completes in ~84s. Updated the histogram script (`scripts/per-repo-workflow-billing-histogram.py`) to classify via the per-job endpoint + parallel fetch + on-disk cache. The 7-day-roll-trend read of spend-alert state (P19) is the canonical way to answer "still $X/day" — confirms spike-past-peak vs spike-active. Added `references/gh-actions-cost-spike-2026-07-29.md` with the full transcript.

**v1.4.0 (2026-07-13):** Re-verified P16 self-hosted detection (`labels` is populated on per-job endpoint, NOT per-run endpoint for this org). Added P18 (broken `Daily GH Actions Cost Report (estimated)` workflow that reports $0 on private-repo 404s), P19 (spend-alert threshold semantics — rate vs absolute, the alert keeps firing on a declining tail), P20 (spend-alert-daily.sh auth-blip recovery). Added `references/gh-actions-cost-spike-2026-07-13.md` with the per-(repo,workflow) histogram walkthrough that resolved the `$266 MTD / $48 daily peak` spike.

## When to Use

- User says "these Actions runs are slow" or links to `actions?query=is:in_progress`
- Many runs show `in_progress` for >20 min with no sign of completing
- A specific workflow consistently takes longer than expected
- Runner pool appears saturated (all runners `busy: true`)
- **A spend-alert fires**: "GitHub Actions daily Δ $X > $Y" or "7d sum $X > $Y" (from `spend-alert-daily.sh` or `gh-actions-cost-monitor.sh`)
- **User asks "why is GitHub Actions so expensive"** or "did we switch to hosted runners"
- **User asks "switch it back"** — usually preceded by the above spend-spike alert
- **User asks "why is the daily cost still $X/day"** — pair the histogram (C7) with P19's 7-day-roll read to confirm whether the spike is past peak or still active

## Diagnostic Sequence (5 steps)

### Step 1 — Snapshot in-progress runs with ages

```bash
gh api -H "Accept: application/vnd.github+json" \
  "repos/OWNER/REPO/actions/runs?status=in_progress&per_page=25" \
  --jq '.workflow_runs[] | {id, name, head_branch, run_started_at, updated_at}'
```

Compute `age = now - run_started_at` for each. Runs > threshold (typically 20 min) are cancellation candidates. Also compute `stuck_min = now - updated_at` — if `updated_at` is frozen for 10+ min while status is `in_progress`, the job is likely silently abandoned.

### Step 2 — Drill into job-step level for the worst offenders

```bash
gh api -H "Accept: application/vnd.github+json" \
  "repos/OWNER/REPO/actions/runs/<RUN_ID>/jobs" \
  --jq '.jobs[] | {runner_name, status, started_at, steps: [.steps[] | {number, name, status, started_at, completed_at}]}'
```

**Key indicators:**
- "Checkout repository" duration > 300s → full clone of a large repo; `fetch-depth` fix needed (Step 5)
- "Resolve deployed preview service URL" in_progress > 400s → polling for a cross-workflow dependency
- All steps `pending` + `status=in_progress` → runner picked up job but never executed; OOM/disconnect
- Only "Set up job" completed → silent Step-2 abort (classic self-hosted runner failure)

### Step 3 — Check runner-pool saturation

```bash
# Org-level
gh api "/orgs/ORG/actions/runners?per_page=100" \
  --jq '{total: .total_count, busy: ([.runners[] | select(.busy)] | length)}'

# Repo-level
gh api "repos/OWNER/REPO/actions/runners" \
  --jq '.runners[] | {name, busy, status}'
```

If `busy == total`, pool is saturated — new runs queue indefinitely. Cancel stuck runs to free slots.

### Step 4 — Cancel stuck runs

```bash
gh run cancel <RUN_ID> -R OWNER/REPO
```

If cancel returns "Cannot cancel a workflow run that is completed" — the run finished naturally between snapshot and cancel. Skip it.

**Self-regenerating pattern**: cancelling frees runners briefly, but active PRs with matrix workflows re-saturate within minutes. This is expected — cancels clear genuinely abandoned jobs vs. actively-progressing ones.

### Step 5 — Fix the checkout bottleneck

If Step 2 showed checkout durations >300s on a large repo (>500 MB):

1. **Find workflows missing `fetch-depth`:**
   ```bash
   python3 scripts/find-workflows-missing-fetch-depth.py .github/workflows/
   ```
   (Script bundled with this skill at `scripts/find-workflows-missing-fetch-depth.py`)

2. **Verify no workflow needs full history:**
   ```bash
   grep -l "git log\|git rev-list\|GITHUB_BASE_REF" .github/workflows/*.yml
   ```

3. **Add `fetch-depth: 1`, `submodules: false`, `lfs: false`** to each checkout's `with:` block. For repos with no `.gitattributes` and no `.gitmodules`, these flags are pure savings.

4. **Verify YAML parses after each file:** `python3 -c "import yaml; yaml.safe_load(open('FILE'))"`

## Cost-Spike Diagnosis (when the spend-alert fires)

When `spend-alert-daily.sh` posts "GitHub Actions daily Δ $X > $Y" or a user asks "why is Actions so expensive", the cause is almost always **a recent PR explicitly pinned a workflow to `runs-on: ubuntu-latest`** (GitHub-hosted) instead of the org's `SELF_HOSTED_RUNNER_LABELS` variable. Hosted Linux costs **$0.008/min**; self-hosted Linux costs **$0.002/min** — a 4× price difference. A single long-poll workflow (e.g. a 30-min skeptic-verdict poll) multiplied by every PR is enough to drive a daily delta from $5 → $50.

### C1 — Snapshot org-level billing by SKU

The billing API returns monthly buckets with per-SKU + per-repo breakdown:

```bash
gh api "orgs/${ORG}/settings/billing/usage" --paginate 2>/dev/null | jq -s '
  [.[].usageItems[]? | select(.product == "actions" and (.date | startswith("'"$(date -u +%Y-%m)"'")))]
  | group_by(.sku)
  | map({sku: .[0].sku, quantity: ([.[].quantity] | add), netAmount: ([.[].netAmount] | add), pricePerUnit: .[0].pricePerUnit, unitType: .[0].unitType})'
```

**SKU → runner type decoder:**
- `Actions Linux` = GitHub-hosted Linux (`ubuntu-latest` workflow pin) — **the cost spike target**
- `Actions macOS 3-core` = GitHub-hosted macOS — usually small (a few PR-driven Mac tests)
- `Actions storage` = artifact/cache GB-hours — usually trivial (<$1)
- Self-hosted runners DO NOT appear as a billed SKU — they're free (you pay for the host)
- The discount (`discountAmount`) on `Actions Linux` typically brings effective rate to ~$0.006/min

### C2 — Filter to the offending repo

```bash
gh api "orgs/${ORG}/settings/billing/usage" --paginate 2>/dev/null | jq -s '
  [.[].usageItems[]? | select(.product == "actions" and (.date | startswith("'"$(date -u +%Y-%m)"'")))]
  | group_by(.repositoryName)
  | map({repo: .[0].repositoryName, quantity: ([.[].quantity] | add), netAmount: ([.[].netAmount] | add)})
  | sort_by(-.netAmount)'
```

In multi-repo orgs the cost almost always concentrates in 1 repo (verified 2026-07-08: 99.9% of $158 MTD was on `your-project.com`). Go straight to that repo.

### C3 — Find which workflows pin to hosted runners

```bash
cd path/to/repo
grep -l "runs-on: ubuntu-latest" .github/workflows/*.yml
```

Then cross-reference with **recent git log on `.github/workflows/`** to find the PR that switched from self-hosted to hosted:

```bash
git log --oneline --since="<spike-date-minus-14d>" -- .github/workflows/ | head -30
```

The smoking-gun commit message format is usually `move ... to ubuntu-latest`, `split ... onto a GitHub-hosted runner`, `failover to GitHub-hosted on ... outage`, or `hosted-poll`. The PR number is in parentheses.

### C4 — Verify self-hosted runners are actually online

Don't assume the switch was justified. Self-hosted runners may be back online:

```bash
gh api "/orgs/${ORG}/actions/runners?per_page=50" \
  --jq '.runners[] | {name, os, busy, status} | select(.status == "online")' | head -30
```

If online runners exist for the OS the workflow needs (Linux X64, Mac ARM64, etc.), the original failover rationale no longer holds — the PR is safe to revert.

### C5 — Compute the cost-savings estimate

```bash
# Hosted Linux = $0.006 effective; self-hosted Linux = $0.002 (4× cheaper)
# Expected savings if reverting one workflow = (workflow_min × ($0.006 - $0.002))
# For a 30-min/PR poll × N PRs/day: N × 30 × 0.004 = $0.12 × N/day
```

### C6 — Post the revert plan, then wait for `MERGE APPROVED`

**Do NOT auto-revert infra PRs in `$GITHUB_REPOSITORY`** (or any production-tier repo with merge safety). The plan must include: PR #s, commit SHAs, expected $/day savings per PR, and 3 explicit options (`REVERT-ALL`, `REVERT-<N>-ONLY`, `INVESTIGATE-FIRST`). Reverts of `runs-on:` lines change CI capacity assumptions that other workflows may depend on.

### C7 — Per-(repo, workflow) histogram from the runs API (when C2-C5 isn't enough)

When the billing-API says "$222 MTD for Actions Linux" but the workflow-level grep (C5) doesn't show obvious culprits (workflows look fine on `main`, OR the culprit workflow has already been deleted but its queued runs are still draining, OR a label-match fallback is silently routing work to hosted runners), the cost is invisible to C1-C6 because those tools only inspect *current* state. You need the per-run `actions/runs` API aggregated by `(repo, workflow_name, event, runner_type)`.

This is the post-2026-07-11 extension. The reusable script is `scripts/per-repo-workflow-billing-histogram.py`:

```bash
# Quick re-run after the spend alert fires:
python3 scripts/per-repo-workflow-billing-histogram.py \
    --org jleechanorg --days 7 --workers 10
```

The histogram self-detects self-hosted runners via the **per-job endpoint** (`actions/runs/{id}/jobs`) using 20 parallel workers with an on-disk cache. The previous YAML-grep heuristic (P16-era fallback) is still kept for runs where the per-job call 404s (deleted from history), but is no longer the primary signal — see P21 for why YAML-grep is unreliable. Default rates: Linux hosted $0.008/min, self-hosted $0.002/min, macOS $0.08/min, Windows $0.016/min. Override with `--rate linux=0.006` (effective post-discount rate for your org).

For runs ≥500, **always use the parallel fetch + cache path** — see P22 for the 600s-timeout trap of doing it serially.

**When to run C7 (the histogram):**
- Billing-API shows Actions cost >$10/day or >$50/week, but `grep -l "runs-on: ubuntu-latest"` returns nothing (the cost is from a *deleted* workflow still draining queued runs)
- `gh api repos/<repo>/actions/runs` shows runs whose `.name` doesn't match any file in `.github/workflows/` on `main` (deleted workflow but active queue)
- You need to know which workflow is responsible before you can post a revert plan
- You suspect a `vars.SELF_HOSTED_RUNNER_LABELS` fallback that silently routes to GitHub-hosted

**Verified pattern (2026-07-11, jleechanorg spend alert):** The histogram revealed `Skeptic Cron` was responsible for **$264 of $292 (90.6%)** of the 7-day cost across 3 repos, even though the workflow file had been deleted from all 42 repos 1-2 days earlier. The cost was from queued runs stamped on the deletion-commit SHA (`3f96d02e`) still draining — deletion doesn't cancel queued runs.

**Comparison to C1-C6 path:** The 2026-07-08 `your-project.com` spike was a different pattern (workflows actively pinned to `runs-on: ubuntu-latest` in 3 PRs); the fix was reverting those PRs. The 2026-07-11 spike was a different pattern (workflows that *looked like* self-hosted but fell through to hosted via label-match failure, with the file now deleted); the fix was already done — just waiting for the queue to drain. The 2026-07-29 "still $5/day" case was yet another pattern (workflow NAMES containing "self-hosted" but actually running on `ubuntu-latest`); the fix is to audit each named-self-hosted workflow and flip `runs-on:` from hosted to self-hosted. Three root causes, same umbrella skill. See P21 for the name-vs-runner trap that hid the cost.

### Reusable verifier

`scripts/check-hosted-runner-spike.sh` (bundled with this skill) walks a repo's `.github/workflows/`, flags every `runs-on: ubuntu-latest` with the trigger event, and prints a per-workflow cost estimate. Run it after any `runs-on:` change to catch drift before the next billing cycle.

`scripts/per-repo-workflow-billing-histogram.py` — the per-(repo, workflow) histogram from C7 above. Run it on any cost-spike alert when C5 doesn't reveal the culprit, or when you suspect a deleted-workflow drain or label-fallback fallthrough.

See `references/gh-actions-cost-spike-2026-07-08.md` for the full session transcript with PR #s, commit SHAs, and the exact revert plan that fixed the your-project.com spike (PRs [#8172](https://github.com/$GITHUB_REPOSITORY/pull/8172), [#8141](https://github.com/$GITHUB_REPOSITORY/pull/8141), [#8142](https://github.com/$GITHUB_REPOSITORY/pull/8142)).

See `references/gh-actions-cost-spike-2026-07-11.md` for the per-(repo, workflow) histogram walkthrough that diagnosed the deleted-workflow-drain pattern on 3 repos (90.6% of $292 7d cost from `Skeptic Cron` queued-runs after the deletion PRs landed).

See `references/gh-actions-cost-spike-2026-07-13.md` for the per-(repo, workflow) histogram walkthrough that resolved the `$266 MTD / $48 peak` spike — the Green Gate precheck attribution (99% billable), the re-verification of P16 self-hosted detection (use per-job endpoint, not per-run), the broken `Daily GH Actions Cost Report (estimated)` workflow that reports $0 on private-repo 404s, and the P19 spend-alert threshold semantics (rate vs absolute — the alert keeps firing on a declining tail).

See `references/gh-actions-cost-spike-2026-07-29.md` for the "still $5/day" diagnosis: workflow names containing "self-hosted" are NOT a runner-type signal (P21), the histogram script's YAML-grep detection produced wrong answers (revised to per-job endpoint + parallel fetch + cache), and the 7-day roll trend (P19) is the right way to tell spike-past-peak from spike-active. Top 3 cost drivers (7d, real): jleechanclaw/Staging Canary Full = $7.67, your-project.com/Presubmit Checks = $7.19, your-project.com/WorldArchitect Tests (Directory-Based) = $5.84. Three repos = 98% of hosted cost.

## Pitfalls

### P1: Duplicate `with:` keys from naive patching
When adding `fetch-depth` to workflows that already have a `with:` block, naive insertion creates two `with:` keys. YAML parsers accept this silently (keeping the last), but GitHub Actions rejects it. **Always merge into the existing `with:` block** — find the block boundary, append keys before the closing indent, verify with `yaml.safe_load()`.

### P2: `gh run cancel` on already-completed runs
Between snapshot and cancel, runs may finish. Cancel returns rc=1 with "Cannot cancel a workflow run that is completed". Not a failure — skip.

### P3: Runner pool count fluctuates
Runners go on/off-line between API calls. `27/27` → `25/26` between calls is normal. Use the trend, not exact counts.

### P4: Beads PR-body lint — STANDALONE LINE required
In repos with `bead-pr-lint.yml`, every PR body MUST contain a `Beads:` line at the **start of a line** (regex is `^[[:space:]]*Beads:`). The lint fails on prose like `**Beads: rev-xxxx** (...)`. Always emit as a standalone line:

```
### Tracking

Beads: rev-xxxx
```

`Beads: none` is the explicit opt-out. `Beads: rev-xxxx` requires 4+ alnum chars.

**Verify with**: `grep -E '^[[:space:]]*Beads:' pr-body.md` before submitting.

### P5: `.beads/issues.jsonl` sort-order check
If `bead-jsonl-sort-check.yml` exists, `.beads/issues.jsonl` must be sorted by `id` ascending. Run `python3 scripts/sort_beads_jsonl.py` and commit. **Verify the inversion isn't pre-existing on `origin/main`** — if it is, fix it in the same PR (per AGENTS.md "Keep `.beads/` tracked and include beads changes in PRs"). See `references/ci-runner-pool-saturation.md` for the verification recipe.

### P6: cancel-loop is a band-aid, not a fix (from 2026-07-05 session)
After 5 cancel waves, the pattern that emerges: cancelling frees runners for 30-60s, then active matrix-workflow PRs re-saturate the pool. The fetch-depth PR doesn't take effect until merged. **`gh run cancel` is a temporary relief** — the durable fix is merging the checkout-optimization PR. Tell the user this explicitly so they understand the loop. Pair with a one-time status cron (`hermes cron create "20m" --deliver 'slack:CHAN:thread_ts' --repeat 1`) to keep cancelling during the wait.

### P7: Green Gate silent step-2 abort = self-hosted runner OOM/disconnect
If `Green Gate` job logs show only "Set up job" completed and all subsequent steps `pending`/`missing`, this is the **classic self-hosted runner failure pattern** (runner died mid-job, network blip, OOM kill). Recovery: cancel run, let GitHub auto-trigger a fresh one. Don't try to re-execute steps manually — the job state is corrupt.

**Verification companion (added 2026-07-14, PR #8290):** before declaring "infra failure, re-trigger", reproduce the same test command locally against the PR's HEAD worktree. If local reproduction is CLEAN (same tests pass in <5% of the CI wall-clock), that confirms the code is fine and the failure is runner-side. The local-vs-CI timing discrepancy is the smoking gun:
- Local: `cd <worktree> && export $(cat .env.ci | xargs) && <test-command>` → e.g. `pytest $PROJECT_ROOT/tests/... -q` → **206 passed in 3.07s**
- CI: same tests in same commit → **16m15s with BlobNotFound log** → clear infra signal

If local reproduce FAILS, the failure IS code-side and no amount of re-trigger will help — pivot to a code fix instead. **NEVER re-trigger a CI failure on faith without verifying the local baseline first.** The re-trigger pattern only works when local = green and CI = red.

For `Directory-Based Tests` (the matrix workflow on `test.yml`), the local-reproduce recipe is:
```bash
# Identify which matrix leg failed (e.g. "core-tests" or "core-mvp-1")
# Look at scripts/ci-detect-changes.sh in the repo to map test-group → test-dirs
# For core-tests = "tests/" group:
PYTHONPATH=. ./run_tests.sh --test-dirs="tests,tests/scripts" --parallel --exclude-integration --exclude-mcp --testmon
```
If that returns all-green locally in seconds/minutes and CI's same command took >10 min with no log → infra failure, re-trigger.

Verified 2026-07-14 PR #8290: local reproduce of `tests/test_*.py` + `tests/scripts/test_*.py` was **304 passed in ~8s**; CI's same set on the same commit took 16m15s with the log blob already expired. Re-trigger produced a fresh run that (eventually) cleared the gate.

### P8: Infra Contract Tests — `shellcheck is not installed` is runner-side
Workflows like `infra-contract-tests.yml` may fail with `::error::shellcheck is not installed and this runner has no passwordless sudo.` on `org-runner-mac-*` runners. **This is a runner-environment issue, NOT a workflow issue**. It affects every PR using that runner. Don't try to fix the workflow — surface it to the runner owner. Same applies to missing `terraform`, missing `gcloud`, etc. — first check the runner environment, not the workflow.

### P9: `gh api .../actions/runs?status=success` is invalid (verified 2026-07-08)
The `actions/runs` query string accepts `status` ∈ {`queued`, `in_progress`, `requested`, `waiting`, `completed`, `pending`, `failure`, `cancelled`} — but NOT `success`. Use `status=completed` + filter `conclusion` per-run in jq, OR use the workflow-scoped endpoint `actions/workflows/<id>/runs`. Same gotcha for `actions/runs?status=success` in Python pipelines. Common symptom: `gh api` returns an empty page and you incorrectly conclude "no completed runs".

### P10: `gh api .../settings/billing/actions` endpoint was removed (2026-06)
The legacy `orgs/<org>/settings/billing/actions` and `.../shared-storage` endpoints were deprecated and now return HTTP 410 ("This endpoint has been moved"). The **new canonical endpoint** is `orgs/<org>/settings/billing/usage` which requires the `manage_billing:org` OAuth scope. If you see HTTP 404/410 on billing queries, switch to the usage endpoint with `--paginate` (multiple pages of usageItems). The enterprise endpoint also requires `manage_billing:enterprise` scope (HTTP 404 if missing).

### P11: `jq "Extra data" error when piping `gh api` to a JSON parser
When `gh api` is piped to `python3 -c` via `python3 -c "..."` and the JSON contains embedded newlines (which `gh` pretty-prints), the python parse may fail with `Extra data: line N column M`. **Fix**: redirect to a file first (`gh api ... > /tmp/runs.json`) then parse from disk. Don't pipe through shell.

### P12: Self-hosted Linux cost assumption = $0.002/min is org-specific
The `$0.002/min` self-hosted rate in `~/.hermes/scripts/gh-actions-cost-monitor.sh` (line 16: `COST_PER_MINUTE=0.002`) is a per-org "platform fee" estimate, not a GitHub-published rate. **GitHub does not bill self-hosted minutes** — the $0.002 reflects Mac runner electricity + maintenance overhead in the user's accounting. **Hosted Linux is $0.008/min standard, ~$0.006 effective after discount** (from the billing API `pricePerUnit` field, verified 2026-07-08). If you're working in a different org, recompute the rate from that org's `usageItems[].pricePerUnit` instead of hardcoding.

### P13: Cost-spike revert on production-tier repo requires explicit `MERGE APPROVED`
Per `.claude/CLAUDE.md` "Merge safety" + `.cursor/rules/agent-autonomy.mdc`, infra PRs in `$GITHUB_REPOSITORY` (and any production-tier repo) require the literal phrase `MERGE APPROVED` in the user's most recent live message before any revert PR is merged. **The agent must NOT auto-merge reverts**, even when the user said "switch it back" — that phrase authorizes the *intent* to revert, not the merge itself. Post a 3-option revert plan (`REVERT-ALL` / `REVERT-<N>-ONLY` / `INVESTIGATE-FIRST`) and wait.

### P14: Hosted-runs-on split jobs need an explicit `actions/checkout` step (latent Gate-8 silent-skip bug, fixed in PR #8285)
When splitting a workflow job from self-hosted → GitHub-hosted `runs-on:`, **the new hosted job does NOT inherit the parent workflow's checkout** (self-hosted jobs in the same workflow chain share the workspace via the runner's persistent filesystem; hosted jobs start with an empty workspace). Any step that does `[ -f <repo-path>/... ]` checks, `git diff`, or reads checked-out files will silently fail.

Verified 2026-07-08: the original hosted `smoke_gate_wait` split (PR #8141, 2026-07-03) had this bug — Gate 8 was always being skipped silently because `[ -f .github/workflows/mcp-smoke-tests.yml ]` always failed on the empty hosted workspace. PR #8285 (the revert) fixed it by re-folding `smoke_gate_wait` back to self-hosted AND adding an `actions/checkout` step. If you ever re-split a job to hosted in the future, **the new job MUST `actions/checkout@v4` first** (or use `uses: actions/checkout@<sha>` with `with: fetch-depth: 1` to stay cheap). Don't repeat PR #8141's silent skip.

### P15: `gh api --paginate` returns null `workflow_runs` when the URL has a `created=>=ISO` filter (verified 2026-07-11)
The `--paginate` flag strips URL query strings differently than the plain call. With `?created=>=2026-07-04T00:00:00Z`, `--paginate` returns `{"total_count":0,"workflow_runs":[]}` — making you wrongly conclude "no runs in window". With the **plain call** (no `--paginate`) the same URL works fine. Workarounds, in order of preference:

1. **Use date-only filter without the operator**: `?created=>=2026-07-04` (no `T00:00:00Z`) — works with `--paginate`. Verified on 2026-07-11 across 42 repos.
2. **Manual pagination**: loop `page=1..N` with `gh api` (no `--paginate`). Slower but reliable. The pattern in `scripts/per-repo-workflow-billing-histogram.py` uses this approach.
3. **`--jq -s 'add'`** doesn't help here — the data is genuinely missing from the response body.

Same gotcha affects `?created=>=...` in any `gh api` query against `actions/runs`. The `total_count: 0` in the empty response is the smoking gun.

### P16: Self-hosted runner detection — use `/actions/runs/{id}/jobs`, NOT the per-run endpoint (re-verified 2026-07-13)
The 2026-07-11 P16 finding ("`workflow_runs[].labels` is always `[]` for self-hosted") was **org/setup-specific**. On 2026-07-13 in `$GITHUB_REPOSITORY`, the per-run `labels` field WAS populated for self-hosted runs (e.g. `labels: ["self-hosted"]`, `runner_name: "ez-mac-runner-b-3"`). But it's not consistently populated across all runs — some per-run objects have `labels: []` even when the underlying jobs ran self-hosted.

**Reliable detection: use the per-job endpoint, not the per-run endpoint:**
```
GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs
```
Every job has `runner_name` and `labels` populated reliably. Classifier:
- `runner_name matches /^GitHub Actions \d+$/` AND `labels ∈ {[ubuntu-latest], [macos-latest], [windows-latest]}` → **GitHub-hosted** (billed)
- `runner_name` is custom (e.g. `ez-mac-runner-b-1`, `ez-runner-c-3`) AND `labels ∈ {[self-hosted]}` → **self-hosted** ($0)
- Anything else → `unknown` (treat as hosted for safety; verify manually)

**Histogram script update (2026-07-29):** `scripts/per-repo-workflow-billing-histogram.py` now prefers the per-job endpoint with 20-worker parallel fetch + on-disk cache (P22). The previous YAML-grep detection is kept only as a fallback for runs where the per-job call 404s. **If you ran the script between 2026-07-11 and 2026-07-29, the output was wrong** — re-run after the script update to get correct attribution. See P21 for the specific case (workflow NAME containing "self-hosted") that the YAML-grep got wrong.

**Symptom of using the wrong endpoint**: histogram attributes $0 billable minutes to a workflow that's actually generating billable minutes on hosted runners. Always sanity-check the top-3 billable workflows against at least one job-level probe before publishing the attribution.

**Cost**: ~60s for 42 repos at 10 workers (same as before), but the per-job endpoint doubles the API calls (one for the run, one per run for jobs). For a 1000-run histogram, that's ~1000 jobs-endpoint calls — cache aggressively.

### P17: `cron: '*/N * * * *'` + `cancel-in-progress: false` + `vars.SELF_HOSTED_RUNNER_LABELS` fallback = the trifecta for a $50/day bill (verified 2026-07-11)
Three workflow-file patterns, in combination, are the canonical recipe for a silent org-wide Actions cost spike. Each alone is benign; together they're catastrophic:

1. **`cron: '*/N * * * *'`** (every-N-minutes schedule) — generates 72 runs/day per repo at N=20. Even short runs compound.
2. **`concurrency.cancel-in-progress: false`** — runs NEVER cancel each other. Multiple instances of the same workflow stack up indefinitely until each one finishes. With `*/20`, after 6 hours you have ~18 parallel runs of the same workflow.
3. **`runs-on: ${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS || '[<fallback-list>]') }}`** — if the org-var is unset (the common case at initial setup) and the fallback list contains labels that don't match any registered runner, GitHub falls through to **GitHub-hosted Linux at $0.008/min**, not error.

Combined: 3 repos × 72 runs/day × ~30 min × $0.008 = **$52/day per repo = ~$1500/month**, all routed to GitHub-hosted without any "this is expensive" warning.

**Detection**: `grep -l "cron:.*\\*/[0-9] \\* \\* \\* \\*" .github/workflows/*.yml | xargs grep -L "cancel-in-progress: true"`. Add the `vars.SELF_HOSTED_RUNNER_LABELS` check separately.

**Mitigation**:
- Always pair `cron: '*/N * * * *'` with `concurrency.cancel-in-progress: true`
- Avoid `vars.<NAME> || '...'` fallbacks that contain labels — the fallback defeats the org-var contract. Either require the org-var (no fallback) or fail loud with a sentinel runner label that errors.
- Pre-commit/repo-scan lint for this trifecta — the bead `$USER-h9ik` (filed 2026-07-11) tracks implementation of an org-wide `gh-actions-schedule-lint` cron.

### P18: `Daily GH Actions Cost Report (estimated)` workflow reports $0 when per-repo billing API 404s (verified 2026-07-13)
Several `jleechanorg/*` repos have a self-hosted `Daily GH Actions Cost Report (estimated)` workflow that claims to estimate per-repo per-workflow costs. It is **BROKEN**: when it calls `gh api repos/jleechanorg/<private-repo>` and gets HTTP 404 (because the repo is private and the GH app's token doesn't have access), the cost-reporting lib silently treats that as $0 instead of failing or logging the skip.

Symptom: the workflow sends `[Daily GH Actions cost (est.)] 2026-07-12 — $0.00` to email/Slack when the real bill for that day is $200+.

**Detection**: check the workflow's most recent run logs for the `cost_report_lib` line `warn: visibility lookup failed for jleechanorg/<repo>: RuntimeError: gh api repos/jleechanorg/<repo> failed: gh: Not Found (HTTP 404) — treating as private`.

**Don't trust the per-repo estimate.** Trust the org-level `/settings/billing/usage` aggregate (returned from `gh api` with the billing-copilot scope) and the per-(repo, workflow) histogram from `/actions/runs` aggregated manually (see C7). The `Daily GH Actions Cost Report (estimated)` is a convenience that's currently misleading.

**Fix**: the `cost_report_lib` should (a) fail loud with `log.error` (not `log.warn` + skip), (b) include the failed repo in the report's "skipped due to access" section, and (c) optionally retry with a token that has read access to private repos (the GitHub App org-wide install, or a fine-scoped PAT). Filed as a followup in the `$USER-h9ik` bead family.

### P19: Spend-alert threshold semantics — `daily Δ > $10` fires on rate AND absolute MTD growth, not on spike health (verified 2026-07-13)
The `spend-alert-daily.sh` threshold fires whenever EITHER `daily Δ > $10` OR `7d sum > $70`. This means **the alert keeps firing even when the spike is past peak**:
- Daily Δ falling from $48.51 → $36.37 → $27.50 → $25.76 → $18.11 (clear downward trend) still trips the threshold because each daily delta is still > $10.
- 7d sum also keeps growing as long as new days add to the rolling window, even if those days are smaller than the days dropping off the back end.

**Implication for users**: when you see "GitHub Actions daily Δ $X > $Y" repeatedly, the first question to ask is "is the rate of accrual going UP or DOWN?". If the rate is falling, the spike is past peak and no action is needed; the alert will stop firing in ~5-7 days as the spike days roll out of the 7-day window.

**Better threshold**: replace `daily Δ` with `daily Δ > $X AND daily Δ > 1.5 × 7d_avg`. This catches rate spikes (today is much higher than average) without re-firing on a declining tail. Same applies to `7d sum` — add `AND daily Δ > 7d_avg`.

**How to compute the rate trend from the state file**: `gh_roll` array in `~/.hermes/state/spend-alert-state.json` contains the last 7 daily deltas. Compare element 0 (oldest) → element 6 (newest). If monotonically decreasing for 3+ consecutive days, the spike is past peak.

**2026-07-29 worked example**: state file `gh_roll = [15.20, 61.11, 18.14, 11.29, 18.30, 25.44, 7.15]` (oldest → newest). Clearly declining from peak on day 2 (the 7/22 spike). User asked "why is GH actions cost still $5/day or so" — correct answer was "spike past peak, no action needed; histogram shows the residual cost is from 3 specific workflows that have been misclassified by the script". Pair P19 with C7 every time someone asks about residual cost — the histogram pinpoints the per-workflow offenders, and P19 confirms whether they're trending up or down.

### P20: `spend-alert-daily.sh` auth blip — `WARN: Failed to fetch GitHub billing usage (check gh auth)` is transient (verified 2026-07-13)
On 2026-07-09 08:41 PT, `spend-alert-daily.sh` logged `WARN: Failed to fetch GitHub billing usage (check gh auth)` and skipped the day's MTD snapshot. The next day's state write interpolated across the gap, making the log look like one big jump (7/8 → 7/10 = $158 → $195, suggesting a $37 spike) when it was actually two smaller days ($25 + $12 estimated).

**Don't treat the auth blip as evidence of a spike.** Verify by:
1. Reading the log line directly: `grep "Failed to fetch" ~/.hermes/logs/spend-alert-daily.log`
2. Checking the state file: `~/.hermes/state/spend-alert-state.json` `gh_roll` array — a missing day = interpolated, not real.

**Fix in the script**: `spend-alert-daily.sh` should fall back to the cached state (last successful MTD) instead of skipping, AND log a `severity=error` (not `severity=warn`) so the dropped-day shows up in cron-watchdog alerts. As of 2026-07-13 this is still `WARN`. Filed as a followup.

### P21: Workflow NAME is NOT a runner-type signal (verified 2026-07-29)
Workflow names in `actions/runs` can contain "self-hosted" or other hints that look like runner-type signals but are just descriptive. Concrete case from `jleechanorg/jleechanclaw`:

- Workflow **name**: `Staging Canary Full (self-hosted)` — sounds self-hosted
- Actual runner: `runner_name = "GitHub Actions 1000651496"`, `labels = ["ubuntu-latest"]` → **GitHub-hosted**, billed at $0.008/min

This caused the histogram script's `is_self_hosted()` function (which grepped the workflow YAML on `main` for the string "self-hosted") to **falsely classify 104/134 runs as self-hosted**, hiding **$7.67 of $44.96 (17%)** of the 7-day hosted cost.

Same trap applies to:
- `Self-Hosted MVP Shards` in `your-project.com` — name contains "Self-Hosted", actually 46/46 GitHub-hosted. Cost: $1.14/day.
- Any workflow renamed during a partial revert ("switch back to self-hosted" tasks that got reverted but the name wasn't changed).
- Workflows with `(cached)`, `(sharded)`, or other parenthetical hints that aren't runner hints.

**Detection rule**: never trust the workflow name OR a YAML-grep of "self-hosted" as a runner-type signal. Always verify via the per-job endpoint (P16). The only fields that matter are `runner_name` and `labels[]` from the jobs array.

**Symptom in histogram output**: a workflow with "self-hosted" in its name appears in the "self-hosted" bucket with significant `count` AND non-zero `minutes`, while its repo's total `gh_minutes` looks low. Cross-check against a manual `gh api repos/<r>/actions/runs?per_page=5 --jq '.workflow_runs[] | select(.name | contains("self-hosted"))'` probe and look at `runner_name`.

**Fix in the histogram script (committed 2026-07-29)**: replaced `is_self_hosted()` (YAML-grep heuristic) with per-job endpoint classifier in parallel (20 workers), cached per-run-id to `~/.hermes/cache/jlorg-run-classification.json` (or similar) so re-runs are free. The fallback path (YAML-grep) is kept only for runs where the per-job call 404s (e.g. run deleted from history).

### P22: Histogram over 2,000+ runs times out at 600s in serial, ~84s with 20 workers (verified 2026-07-29)
Calling `gh api repos/<r>/actions/runs/<id>/jobs` per-run serially across an org with ~2,833 runs in a 7-day window takes **>600s and times out** (verified 2026-07-29). With 20-worker ThreadPoolExecutor, the same workload completes in **~84s**. The histogram script now uses parallel fetch + caches per-run-id to disk (`~/.hermes/cache/jlorg-run-classification.json`).

**Recipe for ad-hoc analysis** (when the histogram script isn't available or you need one-off data):

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess, json

def classify(rid, repo):
    out = subprocess.run(['gh','api',f'repos/{repo}/actions/runs/{rid}/jobs'],
                         capture_output=True, text=True, timeout=15)
    if out.returncode != 0: return str(rid), None
    try:
        jobs = json.loads(out.stdout).get('jobs', [])
        kinds = set()
        for j in jobs:
            rn = j.get('runner_name') or ''
            labs = j.get('labels') or []
            if rn.startswith('GitHub Actions ') or any(l in labs for l in ['ubuntu-latest','macos-latest','windows-latest']):
                kinds.add('hosted')
            elif rn and any(l in labs for l in ['self-hosted']):
                kinds.add('self-hosted')
        return str(rid), 'hosted' if 'hosted' in kinds else ('self-hosted' if 'self-hosted' in kinds else 'unknown')
    except: return str(rid), None

cache = {}
with ThreadPoolExecutor(max_workers=20) as ex:
    futs = [ex.submit(classify, rid, repo) for repo, rid in to_classify]
    for f in as_completed(futs):
        rid, kind = f.result()
        cache[rid] = kind
json.dump(cache, open('/tmp/run-classification.json', 'w'))
```

Don't reuse a sequential loop for >500 runs without first benchmarking — the sequential approach will burn 10+ minutes of session time and likely time out at 600s.

### P23: Per-job `runner_name: null, labels: ['ubuntu-latest']` is GitHub's hosted-fallthrough signal (verified 2026-07-29)
A normal hosted runner allocates with `runner_name = "GitHub Actions <id>"` (e.g. `GitHub Actions 1000651496`) AND `labels = ['ubuntu-latest']`. A *fallthrough* allocation uses `runner_name = null`, `runner_group_id = null`, `runner_id = null` AND `labels = ['ubuntu-latest']`. The job is billed at $0.008/min either way, but the `null` pattern specifically means **the runner-pool self-hosted wait timed out and GitHub silently fell back to hosted**.

Real-world symptom from `$GITHUB_REPOSITORY` (presubmit.yml run on `feat/levelup-lean-auto-apply-v25`, 2026-07-29):
```
Detect Changed Paths         → ez-runner-c-4   self-hosted
limit-pr-runs                → ez-runner-c-10  self-hosted
Function LOC Ratchet         → null            ubuntu-latest  ← fallthrough
AGY JSON contract review     → null            ubuntu-latest  ← fallthrough
Python Linting (Ruff)        → null            ubuntu-latest  ← fallthrough
Python Type Checking (mypy)  → null            ubuntu-latest  ← fallthrough
JavaScript Linting (ESLint)  → null            ubuntu-latest  ← fallthrough
Schema Coverage Guard        → null            self-hosted
Prompt / Tool Contract Hash  → null            ubuntu-latest  ← fallthrough
```
All 9 jobs use the IDENTICAL `runs-on:` expression (`vars.SELF_HOSTED_RUNNER_LABELS || '["self-hosted"]'`). The first 2 jobs landed self-hosted, then the remaining 7 timed out and fell through.

**Detection recipe** (per-job endpoint):
```bash
gh api 'repos/<owner>/<repo>/actions/runs/<run_id>/jobs' \
  --jq '.jobs[] | {name, runner_name: (.runner_name // "null"), labels}'
```
If you see a mix of `runner_name: null` with `labels: [self-hosted]` AND `runner_name: null` with `labels: [ubuntu-latest]` in the SAME run = fallthrough. Confirm by checking the org-runner pool state at the run's `run_started_at` timestamp.

**Fix (in priority order)**:
1. Add per-workflow `concurrency: { group: <wf>-${{ github.event.pull_request.number || github.ref }}, cancel-in-progress: ${{ github.event_name == 'pull_request' }} }` so PR iterations don't pile up self-hosted runners and force fallthrough.
2. Increase runner-pool capacity if the self-hosted runners are genuinely saturated.
3. Investigate the self-hosted runner fleet for slow allocations (could indicate runner-side software issues).

The P22 histogram script already classifies both shapes correctly (`runner_name: null` with hosted label → `hosted` bucket) but reports them without distinguishing fallthrough from a clean hosted allocation. If you need to attribute fallthrough separately, post-process the script output with a secondary query on `runner_name is null AND labels contains 'ubuntu-latest'`.

### P24: `vars.SELF_HOSTED_RUNNER_LABELS || '[fallback]'` — once the org-var is set, the OR-fallback is dead code (verified 2026-07-29)
Prior pitfall P17 documented the silent fallthrough when the org-var is UNSET and the `|| '["self-hosted","self-hosted-mikey"]'` fallback contains labels that don't match any registered runner. The 2026-07-29 incident confirmed the *other* failure mode:

- **Org-var IS set** (verified: `SELF_HOSTED_RUNNER_LABELS = ["self-hosted"]` on jleechanorg)
- **All 16 registered self-hosted runners are online and idle** at diagnosis time
- **The workflow's `runs-on:` still produces hosted fallthrough** for the trailing jobs

Root cause: the `|| '[fallback]'` only applies when the org-var is unset. With the var set, the workflow correctly requests self-hosted runners — but the per-job runner allocation times out for the trailing jobs (P23), so GitHub falls back to hosted at $0.008/min regardless.

**Implication for the OR-fallback pattern**: even if the org-var is set correctly, the `||` fallback is a **latent liability**. When a future org-var rotation uses a different label (e.g. switch from `["self-hosted"]` to `["self-hosted","linux-x64"]`), the fallback stays dead until someone unsets the org-var, then it kicks in with the OLD labels. The safer pattern is to OMIT the fallback and let the workflow fail loud if the org-var is unset:

```yaml
runs-on: ${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS) }}
```

This makes a missing org-var visible immediately instead of silently switching runner types.

**Detection**: `grep -rn "fromJson(vars.SELF_HOSTED_RUNNER_LABELS ||" .github/workflows/ | xargs -I {} echo {}`. Replace each with the bare `fromJson(vars.SELF_HOSTED_RUNNER_LABELS)` form. Verify the org-var is set in `gh api orgs/<org>/actions/variables/SELF_HOSTED_RUNNER_LABELS` before deleting fallbacks.

## cmux Workspace Survey

When investigating CI, check what other agents are doing — their work may compete for the same runner pool:

```bash
cmux list-workspaces --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
for ws in data.get('workspaces', []):
    print(f'{ws[\"ref\"]:<14} {ws.get(\"title\", \"?\"):<30} cwd={ws.get(\"current_directory\", \"\")[:50]:<50} latest={(ws.get(\"latest_submitted_message\") or \"\")[:90]}')
"
```

The `latest_submitted_message` field shows the most recent user instruction per workspace — useful for detecting parallel workstreams competing for runner resources (e.g. another agent running a heavy PR-checkout cycle).

**cmux gotchas:**
- `cmux list-workspaces` (no flag) returns plain text; `--json` returns the real JSON with `workspaces: [{ref, title, current_directory, latest_submitted_message, ...}]`
- `cmux tree --workspace N` returns the **currently-focused workspace**, not workspace N. Workspace IDs are dynamically assigned, NOT the order shown in `list-workspaces`. Always use the `ref` from JSON to be precise.

## References

- `references/ci-runner-pool-saturation.md` — Detailed step-by-step diagnostic + fix recipe with full code examples from the 2026-07-05 your-project.com session (PR [#8173](https://github.com/$GITHUB_REPOSITORY/pull/8173))
- `references/gh-actions-cost-spike-2026-07-08.md` — Billing-API cost-spike diagnostic recipe: which SKU maps to which runner type, the exact `gh api` commands to fetch `usageItems`, the 3-PR revert pattern (PRs [#8172](https://github.com/$GITHUB_REPOSITORY/pull/8172), [#8141](https://github.com/$GITHUB_REPOSITORY/pull/8141), [#8142](https://github.com/$GITHUB_REPOSITORY/pull/8142)), and the merge-safety gate that prevents auto-merge of infra reverts in `$GITHUB_REPOSITORY`
- `references/gh-actions-cost-spike-2026-07-11.md` — Per-(repo, workflow) histogram walkthrough: the recipe for building a cost breakdown from the `actions/runs` API (not just the billing API), the manual-pagination + date-only filter workarounds, self-hosted detection via workflow YAML grep, the "deleted-workflow drain" pattern (Skeptic Cron: $264 of $292 7d cost from queued runs after the deletion PRs landed)
- `references/spend-alert-incident-log.md` — Session-by-session incident log for jleechanorg spend alerts (2026-07-29 entry covers the multi-workflow per-job fallthrough pattern; lists the 5 most common recurring causes in priority order)
- `scripts/find-workflows-missing-fetch-depth.py` — Statically finds workflows using `actions/checkout@` without `fetch-depth:`, exit code 1 if any missing
- `scripts/check-hosted-runner-spike.sh` — Walks `.github/workflows/`, flags every `runs-on: ubuntu-latest` with its trigger event, and prints a per-workflow cost estimate (hosted $0.006/min vs self-hosted $0.002/min)
- `scripts/per-repo-workflow-billing-histogram.py` — Per-(repo, workflow, event, runner) cost histogram from the `actions/runs` API. Run when the billing-API shows a spike but `grep -l "runs-on: ubuntu-latest"` returns nothing — catches deleted-workflow drains, label-match fallthroughs, and per-(repo, workflow) attribution that the billing API alone cannot provide