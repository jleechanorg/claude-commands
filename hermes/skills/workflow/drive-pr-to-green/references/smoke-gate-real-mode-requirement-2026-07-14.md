# Smoke Gate (Gate 8) — REAL-mode requirement + dispatch recipe

**Date:** 2026-07-14
**Affected PR:** [$GITHUB_REPOSITORY#8290](https://github.com/$GITHUB_REPOSITORY/pull/8290)
**Affected workflow:** `.github/workflows/green-gate.yml` → `smoke_gate_wait` job; `.github/workflows/mcp-smoke-tests.yml`
**Bead:** wa-8290-green

## Symptom

After all other gates pass (Evidence Gate, Directory Tests, Green Gate Precheck, Bugbot, CodeRabbit commit-status fallback), `smoke_gate_wait` times out at its 25-minute budget and Green Gate fails on **Gate 8: Smoke**:

```
GATE-8 FAIL: timed out waiting for a REAL-mode mcp-smoke-tests pass for SHA <head_sha> —
the default smoke runs in MOCK mode and does not satisfy the gate;
run /smoke on the PR for real-service coverage
```

The misleading signal: `pr-dev-preview.yml` (the auto-deployed PR preview) runs MCP smoke tests in **MOCK mode by default**, and the resulting "✅ MCP Smoke Tests Passed" PR comment does **NOT** satisfy Gate 8.

## Root cause

The Green Gate aggregator's `smoke_gate_wait` job (in `green-gate.yml`, Gate-8 block) polls for a **REAL-mode `mcp-smoke-tests` pass for the exact PR head SHA**. It accepts only REAL-mode PASS results tagged with the head SHA in the PR comment.

`pr-dev-preview.yml` (workflow id 208357918, "Deploy PR Preview (Rotating Pool)") dispatches MCP smoke tests with the default `test_mode=mock`. So even though the deployment completes successfully and posts a "✅ Deployment Complete!" comment + a "MCP Smoke Tests Passed" MOCK-mode comment, Gate 8 will time out after 25 minutes of polling.

## Detection recipe

```bash
# Read the smoke_gate_wait job log for the explicit fail message
gh run view <green-gate-run-id> --job <smoke_gate_wait-job-id> \
  --repo <owner>/<repo> --log | grep -E 'GATE-8|REAL-mode'

# Check the latest MCP smoke tests workflow run mode
gh api /repos/<owner>/<repo>/actions/runs?event=workflow_dispatch\&per_page=5 \
  | jq -r '.workflow_runs[] | "\(.created_at[11:19])  \(.name)  head=\(.head_sha[0:12])  concl=\(.conclusion)"' \
  | grep -i smoke
```

If the latest MCP smoke test run shows `concl=success` but the `smoke_gate_wait` job logs the REAL-mode fail message, the default MOCK-mode dispatch is the cause.

## Fix recipe — manual `workflow_dispatch` with `test_mode=real`

```bash
GH_TOK="$(gh auth token)"

gh workflow run mcp-smoke-tests.yml \
  --repo <owner>/<repo> \
  -f pr_number=<N> \
  -f test_mode=real
```

Then:

1. Wait for the smoke run to complete (REAL mode takes 20-30 minutes — significantly longer than MOCK).
2. Verify the PR head SHA matches the smoke run's `head_sha` (see "Head-resolution gotcha" below).
3. Re-trigger Green Gate:
   ```bash
   gh workflow run green-gate.yml \
     --repo <owner>/<repo> \
     -f pr_number=<N> \
     -f head_sha=<head_sha>
   ```
4. The `smoke_gate_wait` job polls every ~20s, finds the REAL-mode pass comment with the SHA tag, and Green Gate clears Gate 8.

## The `test_mode` input is real|mock (not just mock|real)

`mcp-smoke-tests.yml` accepts a `test_mode` choice input:

```yaml
workflow_dispatch:
  inputs:
    pr_number:
      required: true
      type: string
    test_mode:
      required: false
      type: choice
      default: 'mock'
      options:
        - mock
        - real
```

Do NOT pass `head_sha` — that returns `422: Unexpected inputs provided: ["head_sha"]`. The head SHA is auto-resolved from the `pr_number` input via the workflow's `pr_ref` step.

## Head-resolution gotcha (informational, not a bug)

When dispatched via `workflow_dispatch`, the workflow run summary's `head_sha` field shows the **runner checkout SHA** (origin/main, because `workflow_dispatch` runs against the repo default branch unless `--ref` is specified). This is **misleading** but not a bug — the `pr_ref` step inside the job correctly resolves `pr.data.head.sha` via the GitHub REST API and uses that for the actual smoke test target.

To verify the smoke ran against the right SHA, check:
1. The PR comment posted by the smoke workflow (it includes `**Commit SHA**: <sha>` and `**PR**: #N @ <sha_short>`).
2. The `pr_ref` step's outputs in the run log.

## The `/smoke` slash-command path has its own head-resolution issue

Posting `/smoke` as a PR comment triggers `comment-router.yml` which dispatches `mcp-smoke-tests.yml` via `workflow_dispatch`. But in some `jleechanorg/*` repos, the comment-router has been observed to:

1. Fail with `403: Resource not accessible by integration` when posting the "dispatched" acknowledgement comment (token permission scope issue on the dispatch workflow).
2. Dispatch the smoke test against `origin/main` (the default branch) instead of the PR head, when the router's `pr_number` resolution is broken.

When the comment-router path misfires, fall back to **manual `workflow_dispatch` with `pr_number=<N>` and `test_mode=real`** (above). The direct dispatch path has a more reliable head-resolution story.

## Why local reproduce doesn't catch this

Local test reproduce (e.g. `./run_tests.sh` or pytest against the worktree) does not exercise Gate 8 because Gate 8 only fires inside the Green Gate CI aggregator. The local-reproduce-green signal is necessary but not sufficient for "as-green-as-CI-allows." A 304/304 local pass + Green Gate Gate 8 FAIL = REAL-mode dispatch is required.

## Companion fixes (track separately)

- **Extend Gate 8 to fall back to MOCK-mode smoke when no REAL-mode has been requested.** Currently Gate 8 strictly polls for `test_mode=real`, which forces every /green through the 20-30 min REAL-mode dispatch. Some PRs (docs-only, chore-only) shouldn't need REAL-mode coverage. Track as `wa-green-gate-gate8-mock-fallback`.
- **Add `test_mode` parameter to `pr-dev-preview.yml`.** Currently the auto-deployed preview always runs MOCK, leading to the misleading "MCP Smoke Tests Passed" comment that the user thinks should clear Gate 8. A `test_mode=real` default for PRs that touch `$PROJECT_ROOT/prompts/` or `$PROJECT_ROOT/**/*.py` would close the gap. Track as `wa-pr-dev-preview-real-mode-default`.

## Verified provenance

- **2026-07-14 PR #8290** (`$GITHUB_REPOSITORY`, head `c8dbb46928825c0de095c18cb60918b22d2df639`):
  - `smoke_gate_wait` job (run 29372329939) timed out at 22:40:46Z after 45 polls × 20s = 15 min polling budget. The 25-min `timeout-minutes` is the job-level bound.
  - Log message at fail: `GATE-8 FAIL: timed out waiting for a REAL-mode mcp-smoke-tests pass for SHA c8dbb46 — the default smoke runs in MOCK mode and does not satisfy the gate; run /smoke on the PR for real-service coverage`.
  - `pr-dev-preview.yml` ran at 22:14:07Z on `c8dbb46` and posted a "MCP Smoke Tests Passed" comment at 22:19:15Z — but in MOCK mode.
  - Manual `workflow_dispatch` with `pr_number=8290 test_mode=real` dispatched at 22:42:57Z; smoke run id 29373887935 in progress at the time of this reference.
  - `/smoke` comment at 22:41:48Z triggered `comment-router.yml` (id 202218184) which dispatched MCP smoke against `head=69282e011d2b` (origin/main, wrong head) and the acknowledged-dispatch comment failed with `403: Resource not accessible by integration`.

## Cross-references

- `references/smoke-gate-pool-exhaustion-2026-07-07.md` — sibling reference covering pool-exhaustion failure mode (different from REAL-mode requirement, but both block Gate 8).
- `references/coderabbit-commit-id-gate3-stale-review-2026-07-14.md` — sibling gap on Gate 3 (same drive, same PR).
- `~/.hermes/skills/workflow/drive-pr-to-green/SKILL.md` — the drive-to-green flow this reference slots into (Gate-8 stage).
- PR #8290 thread `C0AH3RY3DK6/1784030452.318509` — originating incident. Ts `1784068963.759179` documents the Gate-8 root-cause analysis.