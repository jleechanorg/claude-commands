# PR #8467 CI-Log Recovery — Raw Transcript

Verified 2026-07-20 against `$GITHUB_REPOSITORY` PR #8467 with PR HEAD SHA `ec74ca2dda043facb8f68ae7a272466244c77fa1`, run ID `29710203094`, failed job `88252978820` (Green Gate Precheck Gates 1-6).

## Failure chain observed (in order)

```
1. gh pr checks 8467 --repo $GITHUB_REPOSITORY
   → returns CheckRun table including "Green Gate Precheck (Gates 1-6)  fail  1m11s"
   (this works because gh pr checks uses GraphQL; rate-limited from earlier loops)

2. gh run view 29710203094 --repo $GITHUB_REPOSITORY --job 88252978820 --log-failed
   → failed to get job: HTTP 503: No server is currently available to service your request.
   (transient; retry after backoff succeeds)

3. Sleep 60s + retry:
   → run 29710203094 is still in progress; logs will be available when it is complete
   (job actually completed at 00:58:20Z, but gh cached status stale; try gh api instead)

4. gh api -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' \
     repos/$GITHUB_REPOSITORY/actions/jobs/88252978820/logs > /tmp/log.txt
   → SUCCESS, 9456 lines, 1.2 MB
```

## Key finding from the log

The Green Gate Precheck log shows the gates ran in this order:

```
GATE-1 PASS: CI=success
GATE-2 PASS: no conflicts
GATE-3 PASS: CR=APPROVED(status-only)
GATE-5 PASS: all comments resolved
GATE-6 PASS: evidence present
GATE-6b FAIL: PR description gate rejected PR body (validator output below)
```

GATE-6b failed because the PR body (well-written prose with `## Summary`, `## Real LLM Evidence`, `## Known Limitations`, `## Verification`) was missing 5 canonical sections:
- `## Production Code Changes`
- `## Test Changes`
- `## Unit Test Evidence`
- `## Non-Unit Test Evidence`
- `## Evidence`

The agent author had crafted 4 sections of beautiful prose and missed the entire 8-section scaffold. Re-running Green Gate after fixing the body should be the only remaining step.

## What didn't work (negative results)

1. `curl -fsS -L https://api.github.com/repos/$GITHUB_REPOSITORY/actions/jobs/88252978820/logs`
   → `404 Not Found` (the base endpoint doesn't exist; the working endpoint is `/actions/jobs/<id>/logs` only when properly authenticated).

2. `python3 urllib.urlopen("https://api.github.com/repos/$GITHUB_REPOSITORY/actions/jobs/88252978820/logs", headers={"Authorization": f"Bearer {token}"})`
   → `HTTP 401 Bad credentials` (token from `gh auth token` returns masked value with `***` suffix).

3. `gh auth token 2>&1` then use the raw string
   → output is `ghp_tP...rzoJ***` literally — passing that as `Authorization: Bearer` produces 401.

4. `gh pr view 8467 --repo $GITHUB_REPOSITORY --json body`
   → `GraphQL: API rate limit already exceeded for user ID 13840161`
   (couldn't get the PR body via GraphQL during the rate-limit window; had to use `gh api ... /pulls/8467` REST instead).

5. Waiting for 5000/h GraphQL budget to reset (which was ~3500s away)
   → too slow; burning an extra hour was unacceptable. Switched to REST.

## What worked (positive results)

1. **`gh api -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' repos/$GITHUB_REPOSITORY/actions/jobs/88252978820/logs`**
   → 200 OK, 1.2 MB plain-text log; greppable for `GATE-` markers.

2. **`gh api repos/$GITHUB_REPOSITORY/actions/runs/29710203094/jobs --jq '.jobs[] | {name, conclusion, html_url}'`**
   → returned all 4 jobs from the run (precheck fail, gate4 skip, gate skip, green gate queued).

3. **`gh api repos/$GITHUB_REPOSITORY/pulls/8467 --jq '.state, .merged'`**
   → `open\nfalse` — PR is open, not merged. (Used as a sanity check.)

4. The `gh api` form with REST headers works EVEN when GraphQL is rate-limited. That's the load-bearing insight.

## Failure recovery recipe that worked end-to-end

```bash
# Step 1: Get the PR state via REST (always works)
gh api -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' \
  repos/$GITHUB_REPOSITORY/pulls/8467 \
  --jq '{state: .state, mergeable: .mergeable, head_sha: .head.sha}'

# Step 2: Get the run's jobs
gh api -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' \
  repos/$GITHUB_REPOSITORY/actions/runs/29710203094/jobs \
  --jq '.jobs[] | {name, conclusion, html_url}'

# Step 3: Get the failed job's log
gh api -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' \
  repos/$GITHUB_REPOSITORY/actions/jobs/88252978820/logs > /tmp/job.log

# Step 4: Grep the gate failures
grep -nE 'GATE-[0-9]+ (PASS|FAIL|SKIP|ERROR)' /tmp/job.log
```

Time spent: ~5 minutes from initial `gh pr checks` to having the actual gate failure in plain text. Could have been ~30 seconds with the right recipe up front.

## Carry-forward rules

- Whenever `gh pr checks`, `gh pr view --json`, or `gh run view --log-failed` returns GraphQL/503, immediately pivot to `gh api -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' ...`.
- The two -H header flags are load-bearing for the 2022 API version; without them, gh api may default to v3 and route some endpoints through GraphQL.
- After fixing a failing PR gate, the local `pr_description_gate.py` validator (see `wa-green-gate-pr-shape` skill) catches the GATE-6b shape errors before any CI cycle.
