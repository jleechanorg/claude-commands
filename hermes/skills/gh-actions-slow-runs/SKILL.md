---
name: gh-actions-slow-runs
description: "Diagnose and fix slow GitHub Actions runs: runner-pool saturation analysis, stuck-run cancellation, fetch-depth optimization. Use when Actions runs exceed a time budget or many in_progress runs aren't completing."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [GitHub, Actions, CI, runner-pool, fetch-depth, performance, self-hosted]
    related_skills: [github-pr-workflow, hermes-health-check, drive-pr-to-green]
---

# GitHub Actions Slow-Run Diagnosis & Fix

When GitHub Actions runs exceed a time budget (e.g. "should never be more than 20 min") or the Actions UI shows many `in_progress` runs that aren't completing, this is a **runner-pool / throughput** problem — fundamentally different from "my tests failed." The fix is infrastructure-level (cancelling stuck runs, optimizing checkout speed), not code-level.

## When to Use

- User says "these Actions runs are slow" or links to `actions?query=is:in_progress`
- Many runs show `in_progress` for >20 min with no sign of completing
- A specific workflow consistently takes longer than expected
- Runner pool appears saturated (all runners `busy: true`)

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

### P8: Infra Contract Tests — `shellcheck is not installed` is runner-side
Workflows like `infra-contract-tests.yml` may fail with `::error::shellcheck is not installed and this runner has no passwordless sudo.` on `org-runner-mac-*` runners. **This is a runner-environment issue, NOT a workflow issue**. It affects every PR using that runner. Don't try to fix the workflow — surface it to the runner owner. Same applies to missing `terraform`, missing `gcloud`, etc. — first check the runner environment, not the workflow.

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
- `scripts/find-workflows-missing-fetch-depth.py` — Statically finds workflows using `actions/checkout@` without `fetch-depth:`, exit code 1 if any missing