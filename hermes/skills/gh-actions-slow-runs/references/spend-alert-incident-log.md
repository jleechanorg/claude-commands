# Spend Alert Investigation — Reference Log

Session-by-session record of `jleechanorg` spend-alert investigations and their
root causes. Use this when a spend alert fires on `jleechanorg` and the
attribution doesn't match an obvious single-workflow burn — the recurring
patterns below are usually the cause.

Each entry: date, alert shape, root cause, fix, verification.

---

## 2026-07-29 — Multi-workflow per-job fallthrough on `your-project.com`

**Alert shape**: `GitHub Actions daily Δ $14.15 > $10` and `7d sum $155.59 > $70`.
MTD = $514.43. 7-day rolling delta trace `[61.11, 18.14, 11.29, 18.30, 25.44, 7.15, 14.15]`
(spike past peak on 7/22, currently declining tail — alert will keep firing until
the spike days roll out, per P19).

**Org var**: `SELF_HOSTED_RUNNER_LABELS=["self-hosted"]` is SET.
**Runners online**: 16 self-hosted (6 macOS `ez-mac-runner-b-*`, 10 Linux
`ez-runner-c-*`), all idle at diagnosis time.

**Root cause** (per-job classification via `actions/runs/{id}/jobs`,
parallel fetch over 1000 recent runs, ~37s):

| Workflow | Hosted min | Cost | Root cause |
|---|---|---|---|
| `Presubmit Checks` | 12,169m | $97.36 | Job-level fallthrough: first 2 jobs land self-hosted, remaining 7 jobs resolve to `runner_name=null, labels=['ubuntu-latest']` |
| `Coverage Report` | 6,550m | $52.40 | `coverage.yml:212` has hardcoded `runs-on: ubuntu-latest` for the post-test comment job |
| `Auth Browser Tests` | 1,096m | $8.77 | Same fallthrough as Presubmit Checks |

**Smoking-gun commits** (all `[codex/GPT-5]` author):

- `c2d7a53324` (2026-07-28 23:51) — pinned dep-major-bump-gate in `presubmit.yml` to `["self-hosted","ez-runner-c"]`
- `ce6f88d4e7` (2026-07-29 02:48) — added `Linux,X64` to the label set
- `746d3525c7` (2026-07-29 04:49) — rolled back to `vars.SELF_HOSTED_RUNNER_LABELS || '["self-hosted"]'`

The rollback was the right idea but didn't fix the recurring hosted bill because:

1. **`Coverage Report` line 212** (`runs-on: ubuntu-latest`) is hardcoded and the
   rollback didn't touch it. Single-line fix: replace with
   `runs-on: ${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS || '["self-hosted"]') }}`.
   Estimated savings: ~$52/day.
2. **`Presubmit Checks` and `Auth Browser Tests`** continue to fall through to
   hosted for trailing jobs even with the org-var set, because the first 2 jobs
   in each workflow consume the available self-hosted runners. The remaining
   jobs wait too long and GitHub assigns them to hosted `ubuntu-latest`
   (`runner_name=null`, `runner_group_id=null`). Fix is per-workflow concurrency:
   ```yaml
   concurrency:
     group: presubmit-${{ github.event.pull_request.number || github.ref }}
     cancel-in-progress: ${{ github.event_name == 'pull_request' }}
   ```

**Verification probe** (per-job on one cancelled hosted Presubmit run):

```
Detect Changed Paths         → ez-runner-c-4   (self-hosted)
limit-pr-runs                → ez-runner-c-10  (self-hosted)
Function LOC Ratchet         → null            ubuntu-latest (hosted)
AGY JSON contract review     → null            ubuntu-latest (hosted)
Python Linting (Ruff)        → null            ubuntu-latest (hosted)
Python Type Checking (mypy)  → null            ubuntu-latest (hosted)
JavaScript Linting (ESLint)  → null            ubuntu-latest (hosted)
Schema Coverage Guard        → null            self-hosted
Prompt / Tool Contract Hash  → null            ubuntu-latest (hosted)
```

Same `runs-on:` expression, mixed runner types within one run = per-job runner
selection timed out for the trailing jobs.

**New pitfall** (added to SKILL.md P23): **per-job `runner_name: null,
labels: ['ubuntu-latest']` is GitHub's hosted-fallthrough signal** — it is NOT
the same as `runner_name: "GitHub Actions N"` (a normal hosted runner that
successfully allocated). Both produce billable minutes, but the `null` pattern
specifically means self-hosted queue timeout. See P23 in `SKILL.md` for the
full diagnostic recipe.

**Per-(repo, workflow) histogram script bugfix** (v1.5.1, 2026-07-30): the
`global CACHE_PATH` declaration inside `main()` was placed AFTER the
`--cache-path` argparse default that reads the module-level constant,
producing a `SyntaxError: name 'CACHE_PATH' is used prior to global declaration`.
Fix: hoist `global CACHE_PATH` to the first executable line of `main()`, compute
the default from an env var before the argparse default is materialised, and
re-apply the user's `--cache-path` after `parse_args()`. See script docstring
and P24 in `SKILL.md`.

---

## Pattern summary (most common jleechanorg spend-alert causes, in priority order)

1. **Per-job hosted fallthrough** (this incident, 2026-07-29) — first N jobs
   consume self-hosted runners, trailing jobs time out and bill hosted. Symptom:
   same `runs-on:` across jobs in one run, mixed runner types in job-level data.
   Fix: per-workflow `concurrency.cancel-in-progress: true` so PR iterations
   don't pile up.

2. **Hardcoded `runs-on: ubuntu-latest` in a workflow that should be self-hosted**
   (Coverage Report line 212 in this incident, plus prior 2026-07-08
   `your-project.com` spike with 3 PRs that switched to hosted). Symptom: 100%
   of jobs in that workflow land hosted. Fix: replace with
   `runs-on: ${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS || '["self-hosted"]') }}`.

3. **`vars.SELF_HOSTED_RUNNER_LABELS || '[fallback]'` + missing label match**
   (P17 from prior sessions) — the fallback contains labels that don't match
   any registered runner, GitHub falls through to hosted silently. Symptom: ALL
   jobs in that workflow land hosted across many repos.

4. **Deleted-workflow drain** (2026-07-11, Skeptic Cron) — workflow file deleted
   but queued runs stamped on the deletion-commit SHA still drain for days.
   Symptom: workflow name in `actions/runs` doesn't match any file in
   `.github/workflows/` on `main`. Fix: nothing to do, wait for queue to drain.

5. **Workflow NAME contains "self-hosted" but actually runs hosted** (P21 from
   prior sessions) — partial-revert renaming trap. Symptom: histogram attributes
   $0 billable minutes to a workflow with "self-hosted" in its name, but
   `runner_name` is `null` or starts with `GitHub Actions`. Fix: rename the
   workflow back to its actual runner type, OR flip `runs-on:` from hosted to
   self-hosted.

When a new spend alert fires on `jleechanorg`, check this list FIRST. Each
pattern has a known fix recipe — don't re-derive from scratch.