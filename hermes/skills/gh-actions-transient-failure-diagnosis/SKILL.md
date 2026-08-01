---
name: gh-actions-transient-failure-diagnosis
version: 1.2.0
changelog:
  - "1.2.0 (2026-07-20) CodeRabbit rate-limit chain failure (PR #8462 head 68df3793d8). When Green Gate Precheck fails with GATE-1 CI=failure AND GATE-3 CR=FAIL AND the CodeRabbit status description is exactly `Review rate limited`, the root cause is a single upstream rate-limit — the aggregator's CI=failure is a chained propagation through Gate-3, not a real test failure. Recovery is passive (poll `pulls/N/reviews` while waiting for the rate-limit to clear per env-preferences.mdc 2026-07-16). DO NOT @-mention CodeRabbit or retry the review — that just extends the ETA."
description: "Diagnose GitHub Actions failures that look like real CI failures but are actually transient infrastructure (HTTP 503 from `actions/github-script`, GitHub API rate-limit surfaced inside workflow steps, cancelled downstream gate propagated as aggregator failure, or webhook-trigger races). Verified 2026-07-20 on PR #8466: Auth Browser Tests job 88252983872 hit 503, and Green Gate aggregator job 88254838835 failed because downstream `smoke_gate_wait` was cancelled -- push empty commit or `gh run rerun`, do NOT chase the named PR or investigate the cancelled job's code."
triggers:
  - "actions/github-script 503"
  - "Resolve PR context failure transient"
  - "CI failing but no code change"
  - "same commit two different results"
  - "transient github api failure"
  - "rate limit inside github action"
  - "Green Gate cancelled"
  - "GATE-X FAIL result=cancelled"
  - "aggregator gate downstream cancelled"
  - "smoke_gate_wait cancelled"
changelog:
  - "1.1.0 (2026-07-20) Cancelled downstream gate (Green Gate aggregator case). PR #8466 head 7041776da1 aggregator job 88254838835 failed at `GATE-8 FAIL: smoke_gate_wait job did not complete successfully (result=cancelled, smoke_gate=unset)` while Gates 1-6 (`PRECHECK_RESULT: success`) and Gate 4 (`BUGBOT_GATE: PASS`) passed. Recovery: `gh run rerun <run-db-id> --failed` for workflow_dispatch, empty-commit retrigger for `pull_request`-triggered workflows, wait-and-retry if both re-cancel."
  - "1.0.0 (2026-07-20) Initial. PR #8466 Auth Browser Tests job 88252983872 hit 503 on `GET /repos/$GITHUB_REPOSITORY/pulls/8466`. Empty commit retrigger cleared the same step. Recipe includes the `actions/jobs/{id}/logs` S3-redirect ZIP-fetch path."
related_skills:
  - drive-pr-to-green
  - gh-actions-slow-runs
  - gh-actions-stuck-self-hosted-runner-recovery
  - superpowers-cloud-build
---

# gh-actions-transient-failure-diagnosis

## Why

GitHub Actions runs occasionally fail for reasons that have nothing to do with the PR's code. The most common shape is **transient GitHub infrastructure** surfacing inside workflow steps: HTTP 503 from `actions/github-script` calls to `api.github.com`, rate-limit hits, or webhook-trigger races. The failure gets attributed to the workflow / PR / commit anyway because that's how `check-runs.conclusion` works — the action framework doesn't distinguish "the step's API call hit a 503" from "the step's code threw."

**The trap:** the natural response is to investigate the named PR/commit. The user gets a red CI report, the agent looks at the named commit, finds nothing wrong, and the investigation burns budget chasing a phantom. The actual root cause is GitHub's API availability, not the code.

**Verified case (2026-07-20, $GITHUB_REPOSITORY PR #8466):**

- **Symptom:** Auth Browser Tests run #14728 failed at step 2 (`Resolve PR number + head SHA`, job 88252983872). First impression: "PR #8466 is broken."
- **Actual log:** The step's `actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea` issue` called `github.rest.pulls.get({owner, repo, pull_number: 8466})`. The server returned `status: 503, response: { url: 'https://api.github.com/repos/$GITHUB_REPOSITORY/pulls/8466', data: { message: 'No server is currently available to service your request. Sorry about that. Please try resubmitting your request and contact us if the problem persists.' } }`.
- **Root cause:** GitHub's own API was temporarily unavailable. The PR's code was fine — the failed step never even touched it.
- **Fix:** Push an empty commit on the PR branch to retrigger the `pull_request` event. The new run started clean and Design Doc Gate passed on the first attempt.

## When to load this skill

- A check-run fails with **only generic** output ("Process completed with exit code 1") and no actionable error
- The only failed step is `actions/github-script` or a step whose primary action is to call `github.rest.*` or `api.github.com`
- The same commit produces **different results** on consecutive runs (one green, one red, with no code change between)
- `gh api` or `curl` against `api.github.com` returns 503 / 502 / secondary rate-limit errors within minutes of the CI failure
- `gh pr view --json statusCheckRollup` shows an inconsistent picture (e.g. `success` from one workflow but `failure` from a different one for the same SHA)
- User asks "is this a real CI failure or just a flake?"
- **Green Gate Precheck shows `GATE-1 FAIL: CI=failure` AND `GATE-3 FAIL: CR=FAIL(status=failure comment=none)` AND `CodeRabbit` status context has description `Review rate limited`** — see "CodeRabbit rate-limit chain failure" below.

## Diagnostic recipe (30-90 seconds)

### Step 1: Identify the failed check-run and its parent workflow run

```bash
TOKEN="$(gh auth token)"
# Pick the failing check_run_id from `gh pr view --json statusCheckRollup` or
# `gh api repos/<OWNER>/<REPO>/commits/<HEAD_SHA>/check-runs?per_page=20`
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/check-runs/<ID>" | jq .
```

The response includes `check_suite.workflow_id`, `check_suite.id` (= the workflow run's databaseId), and `details_url` (the run's HTML page).

### Step 2: Find the failed step inside the workflow run

```bash
# Get the workflow run's jobs (use the run databaseId from step 1, NOT the run_number)
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/runs/<RUN_DATABASE_ID>/jobs" | jq '.jobs[] | {id, name, conclusion, steps: [.steps[] | select(.conclusion=="failure") | {name, number}]}'
```

Note the `job.id` and the failing step's `number`. **Pitfall:** `gh pr view --json statusCheckRollup` gives `run_number` (human-readable like `#14728`), but `actions/jobs/<id>/logs` requires the **run's databaseId** (long numeric like `29709994853`). Always use databaseId for `actions/runs/<id>/jobs`.

### Step 3: Fetch the failing step's log

```bash
# actions/jobs/<job_id>/logs returns a 302 → S3-signed-URL ZIP archive
# The follow-the-redirect with -L pulls the actual log bytes
curl -fsS -L -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/jobs/<JOB_ID>/logs" \
  -o /tmp/job-log.bin
# The response is a ZIP archive
python3 -c "
import zipfile, io
with zipfile.ZipFile('/tmp/job-log.bin') as zf:
    for name in zf.namelist():
        print(f'=== {name} ===')
        print(zf.read(name).decode('utf-8', 'replace'))
"
```

### Step 4: Look for the transient-failure signature

Search the log for these patterns (any one is a strong "this is transient" signal):

| Signature | Meaning |
|-----------|---------|
| `status: 503` + `message: 'No server is currently available to service your request'` | GitHub API degraded |
| `status: 429` + `x-ratelimit-remaining: 0` | Per-token rate limit hit inside the workflow |
| `status: 502` + `Bad Gateway` | GitHub infrastructure blip |
| `Failed to start the runner` / `Failed to create worktree` | Self-hosted runner hiccup, not code |
| `Conflict: Another merge in progress` | Race against a concurrent merge / push |
| `The operation was canceled.` mid-step | Runner preempted or spot-killed |
| Empty `output.title` + empty `output.text` + `conclusion: failure` on a check-run | Workflow job died before writing any output — almost always transient infra |
| Aggregator job (`Green Gate`, `N-green`, etc.) fails with `<GATE-X> FAIL: <gate_name> job did not complete successfully (result=cancelled, …)` | Downstream gate job was **cancelled** (not failed). Aggregator propagates cancel as fail. See "Cancelled downstream gate" recipe below. |

If you see `status: 503` from an `actions/github-script` step calling `github.rest.pulls.get`, `github.rest.issues.*`, `github.rest.repos.*`, etc. → **it is transient. Push an empty commit to retrigger.**

### Step 4b: Cancelled downstream gate (Green Gate aggregator case)

When the failing check is an aggregator like `Green Gate` and its log shows:
```
GATE-X FAIL: <gate_name>_wait job did not complete successfully (result=cancelled, <gate_name>_gate=unset)
```

…the aggregator propagated a `cancelled` from a downstream gate. This is **almost always transient** — typically caused by a parallel job's runner pool exhaustion, a self-hosted runner preemption, or an upstream merge conflict that cancelled sibling jobs. The aggregator's `exit 1` is correct behavior (it's fail-closed on missing input), but the underlying gate is innocent.

**Verified case (2026-07-20, $GITHUB_REPOSITORY PR #8466 head `7041776da1`):**

- Aggregator job #88254838835 (`Green Gate`) failed at the `GATE-8 FAIL` step.
- The aggregator's log line was: `GATE-8 FAIL: smoke_gate_wait job did not complete successfully (result=cancelled, smoke_gate=unset) — see that job's log for the detailed GATE-8 WAIT/FAIL trace`
- All other aggregator gates passed: `PRECHECK_RESULT: success` (Gates 1-6), `BUGBOT_GATE: PASS` (Gate 4).
- The cancelled `smoke_gate_wait` (Gate 8) had no log of its own — it was cancelled before producing output.

**Recipe** (in priority order — try the cheapest first):

1. **`gh run rerun <run-databaseId> --failed` on the aggregator** — re-runs only the failed jobs in the same workflow. CAVEAT: this only works for `workflow_dispatch` runs and same-workflow cancellations; for `pull_request`-triggered runs (Green Gate is one), the rerun reuses the cancelled sibling's state and may cancel again.
2. **Empty-commit retrigger** (preferred for `pull_request`-triggered workflows) — pushes a new SHA that re-fires the `pull_request` event for all dependent workflows. Use the same recipe from Step 5 below; the cancelled sibling usually re-runs clean because the runner-pool pressure has cleared.
3. **Re-dispatch the cancelled job directly via `gh workflow run <workflow>.yml -f pr_number=<N>`** — but ONLY for the cancelled job's workflow, not Green Gate itself. The dispatcher lands on `head_branch=main` per `drive-pr-to-green` v2.5.6, so verify `headBranch` after dispatch.
4. **Wait and retry** — if (1)–(3) all re-cancel, the runner pool is genuinely saturated. Wait 15-30 min and re-trigger; do not loop rapidly.

**Diagnostic commands:**

```bash
# Find the aggregator run + its cancelled downstream
TOKEN="$(gh auth token)"
gh pr view <N> --repo <OWNER>/<REPO> --json statusCheckRollup
# → aggregator check_run_id (e.g., Green Gate)
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/check-runs/<aggregator_id>" \
  | jq '.check_suite'
# → aggregator run databaseId

curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/runs/<aggregator_run_db_id>/jobs" \
  | jq '.jobs[] | {id, name, conclusion}' | grep -i cancelled
# → the cancelled downstream's job_id

# Try (1) first
gh run rerun <aggregator_run_db_id> --failed
# If the rerun also cancels, drop to (2): empty commit
git -c user.name="<u>" -c user.email="<u>@users.noreply.github.com" \
    commit --allow-empty -m "ci: retrigger after Gate-8 cancel in aggregator run <id>"
git push origin HEAD
```

**Anti-pattern:** investigating the cancelled job's *code* (e.g., reading the smoke test config) before checking whether the cancel was a runner-pool issue. Cancellations with no log output are almost never caused by the workflow's own logic — they're caused by the runner allocation system or by a sibling job's failure cascading. Read the aggregator's gate-trace line first; if it says `result=cancelled`, the gate code is fine.

### Step 4c: CodeRabbit rate-limit chain failure (NEW v1.2.0)

When the Green Gate Precheck fails with this exact pattern in its log:

```
GATE-1 FAIL: CI=failure
GATE-2 PASS: no conflicts
GATE-3 FAIL: CR=FAIL(status=failure comment=none)
GATE-5 PASS: all comments resolved
```

…and `gh api repos/<o>/<r>/commits/<sha>/status` shows a `CodeRabbit` StatusContext with `state: failure` and `description: "Review rate limited"`, the failure class is **CodeRabbit rate-limit chain-failure**, NOT a real CI failure.

**What's happening**: CodeRabbit is throttled by its org/account-level "Fair Usage Limits Policy" (per env-preferences.mdc 2026-07-16). Its status_context reports `state=failure` because it couldn't even submit a review. Green Gate Precheck's GATE-3 check reads that `state=failure` and reports `GATE-3 FAIL`. Because all gates must pass for `eligible=true` (any FAIL → `ELIGIBLE=false`), and the precheck also rolls up `GATE-1` from any non-success check_run in the head SHA, **GATE-1 FAILS as a downstream propagation of GATE-3**. The actual CI tests are green (`Directory tests core-mvp-1/2/3`, `Directory tests core-tests`, `Coverage Report`, all PASS).

**Recipe** (in priority order):

1. **Verify the chain** by reading the aggregator's gate-trace (NOT the failed check_runs — the chain hides in the rolled-up state). The pattern `GATE-3 FAIL: CR=FAIL(status=failure comment=none)` followed by `GATE-1 FAIL: CI=failure` is the signature; `failure` in the CR tuple is from the StatusContext, not from a missing review.

2. **Check `.coderabbit.yaml` at repo root** to confirm the ceiling:
   ```bash
   gh api repos/<o>/<r>/contents/.coderabbit.yaml -H "Accept: application/vnd.github.v3.raw" | grep -A2 "^reviews:"
   # `approve: true` → CodeRabbit CAN post APPROVED when not rate-limited
   # `approve` absent → CodeRabbit can only post COMMENTED (no merit to waiting longer)
   ```

3. **Do NOT retry CodeRabbit via PR comment** (`@coderabbitai full review`). Per env-preferences.mdc 2026-07-16: "once rate-limited, stop retrying that PR; poll `pulls/N/reviews` passively instead. Retrying `@coderabbitai full review` while still rate-limited re-extends the ETA instead of resetting it (observed 18min→57min→58min)."

4. **Poll `pulls/N/reviews` every 5-10 min** via REST (GraphQL is the same rate-limited bucket as the SDK):
   ```bash
   gh api repos/<o>/<r>/pulls/<N>/reviews --paginate \
     | jq -r --arg head "<HEAD_SHA>" \
       '.[] | select(.user.login == "coderabbitai[bot]" and .commit_id == $head) | "\(.state) \(.submitted_at)"'
   ```

5. **When a new review appears with `state: APPROVED`** (or `state: COMMENTED` if `.coderabbit.yaml` lacks `approve: true`), the chain resolves on its own — GATE-3 transitions to PASS, the aggregator re-reads and GATE-1 also PASSes. No further action needed; Green Gate's precheck re-runs on the next `pull_request` event or via `gh workflow run green-gate.yml --ref <branch>`.

**Anti-pattern:** the chain-failure pattern looks identical to "the PR has bad code". An agent that doesn't read the aggregator's gate-trace will:
- read the named PR's diff looking for the bug
- find nothing
- propose editing bq_logging.py
- push a fix commit
- retrigger CI
- now there's a polluted commit + the rate-limit is still happening + nothing got better

Read the gate log FIRST. The shape `GATE-3 FAIL: CR=FAIL(status=failure comment=none)` + `CodeRabbit description: "Review rate limited"` is the entire signal.

**Verified case (2026-07-20, $GITHUB_REPOSITORY PR #8462 head 68df3793d8):**

- Aggregator log showed `GATE-1 FAIL: CI=failure` and `GATE-3 FAIL: CR=FAIL(status=failure comment=none)`.
- 17 check_runs succeeded (`Directory tests core-mvp-1/2/3`, `Directory tests core-tests`, `Coverage Report`, `Import Validation`, `Schema Coverage Guard`, etc.); 2 failed (`Green Gate`, `Green Gate Precheck (Gates 1-6)`); 6 skipped (`Bugbot Gate Wait (Gate 4)`, `Smoke Gate Wait (Gate 8)`, `Cursor Bugbot`); 1 in-progress at the snapshot (`MCP Smoke Tests [Preview E2E]`).
- CodeRabbit status (REST `commits/<sha>/status`): `CodeRabbit state=failure desc=Review rate limited`.
- Resolution: passive wait, no further action from agent. The CR rate-limit clears org-wide on its own schedule; once it does, a new review is posted on the next push/auto-retrigger.

### Step 5: Verify with local validator (before retriggering)

Before pushing, double-check the PR body / commit / branch actually pass the gate that failed. For design-doc-gate-style regex checks, run the local validator script from the workflow's source:

```bash
# Example: design-doc-gate regex from .github/workflows/design-doc-gate.yml
RE='^[[:space:]]*##[[:space:]]+(design[[:space:]]+decision|governing[[:space:]]+design[[:space:]]+doc[[:space:]]*&[[:space:]]+tracking|tenets)([[:space:]]|$)'
gh pr view <N> --repo <OWNER>/<REPO> --json body | jq -r '.body' | grep -iP "$RE" || echo "FAIL"
```

If the local validator PASSES on the same head SHA but CI FAILED with the same content check, the CI failure is transient (a stale run against an older commit, or a 503-induced early-exit). Safe to retrigger.

## The fix — empty-commit retrigger

```bash
# From inside the PR's worktree (or a clean clone on the PR's branch)
git -c user.name="<github-username>" \
    -c user.email="<github-username>@users.noreply.github.com" \
    commit --allow-empty -m "ci: retrigger after transient github 503 in <step-name> (job <job-id>)"
git push origin HEAD
```

This creates a new commit SHA on the PR's `headRefName`, which fires the `pull_request` event with the correct SHA. All workflows that watch `pull_request` will re-evaluate. The new run starts fresh, gets a new runner allocation, and the transient API issue usually clears within minutes.

**Risk:** this modifies the PR's branch with an empty commit. For dependabot/external-author PRs where you don't have write access, use `@dependabot rebase` instead, or `gh run rerun` if the original was a `workflow_dispatch` (note: `pull_request`-triggered runs cannot be rerun — they must be re-triggered by a push).

**Note on `gh workflow run`:** `gh workflow run <workflow>.yml -f pr_number=N -f head_sha=X` lands on `head_branch=main`, NOT the PR branch. The dispatch evaluates against `origin/main`'s HEAD, not the PR's. The resulting run is useless for refreshing PR status. See `drive-pr-to-green` v2.5.6 for the full trap. **Empty commit is the canonical fix.**

## Anti-patterns

- ❌ **Chasing the named PR/commit without reading the log.** If the only failed step is `actions/github-script` and the log shows `status: 503`, the named PR has nothing to do with it. Verify the log before opening an investigation.
- ❌ **`gh workflow run` to "refresh" PR status.** It does not — see `drive-pr-to-green` v2.5.6 for why the dispatch evaluates against `origin/main`.
- ❌ **Adding `--retry` flags to the failing step.** `actions/github-script` already retries once. A third retry will not help; the underlying API availability issue is on GitHub's side.
- ❌ **Reverting a real PR change because of a transient CI failure.** The code is fine; the CI is flaky. Push empty commit, let CI re-run, merge.
- ❌ **Trusting `gh pr view --json statusCheckRollup` alone for "is CI green?"** It only shows the latest, deduplicated view. Always fetch `/commits/{sha}/check-runs?per_page=50` for the modern GH Actions API and look at `check_runs[].conclusion` directly. A `statusCheckRollup: success` from a single `CodeRabbit` legacy status_context can coexist with multiple GH Actions failures.

## Verification — proving the empty-commit retrigger worked

After pushing the empty commit:

```bash
# Wait ~30s for CI to queue, then check the new head's check-runs
NEW_SHA=$(git -C <worktree> rev-parse HEAD)
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/commits/$NEW_SHA/check-runs?per_page=20" \
  | jq '.check_runs[] | {name, status, conclusion, details_url}'
```

Expected: `Design Doc Gate` and any previously-failing check should show `status: in_progress` or `conclusion: success` on the NEW SHA, distinct from the prior SHA's red state. If the same check fails again with the same `status: 503` log → escalate to "GitHub is having a bad day" and pause the drive until the incident clears.

## Pair with

- `drive-pr-to-green` v2.5.6 — empty-commit retrigger + `gh workflow run` `head_branch` trap (this skill's empty-commit section is the detailed recipe; the drive skill is the lifecycle context)
- `gh-actions-slow-runs` — when the failure is "slow" not "red" (runner pool saturation, billing spikes, label-match fallthrough)
- `gh-actions-stuck-self-hosted-runner-recovery` — when the failure is "no log retrievable" (runner died, `BlobNotFound` on the log endpoint)
- `superpowers-cloud-build` Step 0 hello-world — same "don't trust the headline, fetch the log" discipline applied to cloud-build runs (verify `Cloud Build <supervisor@cloud-build.local>` actually committed before reporting success)

## Reference

- Verified reproduction: PR #8466 / job #88252983872 / run #29709994853, 2026-07-20
  - Failed step log excerpt: `status: 503, response: { url: 'https://api.github.com/repos/$GITHUB_REPOSITORY/pulls/8466', data: { message: 'No server is currently available to service your request.' } }, request: { method: 'GET', url: 'https://api.github.com/repos/$GITHUB_REPOSITORY/pulls/8466' }`
  - Fix: `git -c user.name=jleechan2015 -c user.email=jleechan2015@users.noreply.github.com commit --allow-empty -m 'ci: retrigger after transient github 503 in Resolve PR context (job 88252983872)' && git push origin HEAD`
  - Result: `60c050a48b..7041776da1  HEAD -> fix/8353-cloudbuild-json-sanitize`. New run #29710376998 (Design Doc Gate) passed on the new head; subsequent queued runs started against `7041776da1`.

- **Cancelled downstream gate (Green Gate aggregator)**: PR #8466 / aggregator job #88254838835 / run #29710376992 on head `7041776da1`, 2026-07-20
  - Aggregator log: `GATE-8 FAIL: smoke_gate_wait job did not complete successfully (result=cancelled, smoke_gate=unset) — see that job's log for the detailed GATE-8 WAIT/FAIL trace` at 02:15:01.9548046Z
  - Aggregator passed Gates 1-6 (`PRECHECK_RESULT: success`) and Gate 4 (`BUGBOT_GATE: PASS`). Only Gate 8 was cancelled.
  - Recovery: `gh run rerun <aggregator_run_db_id> --failed` or empty-commit retrigger per Step 4b above.
  - Full recipe: `references/cancelled-downstream-gate-2026-07-20.md`.

- **Sibling transient case (different root cause, same PR)**: PR #8466 / Auth Browser Tests job #88252983872 / run #29709994853 hit the v1.0.0 transient-503 trap on `actions/github-script` step. Empty commit to `7041776da1` cleared it. Both transient-failure shapes occurred on the same PR within minutes — verify the aggregator's gate-trace line AND the failed step's log before deciding the root cause class.