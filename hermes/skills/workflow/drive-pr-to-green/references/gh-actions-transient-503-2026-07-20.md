# GitHub Actions `actions/github-script` HTTP 503 Transient Failure

**Verified 2026-07-20, $GITHUB_REPOSITORY PR #8466.**

## Symptom

A check-run on a PR fails. The PR's code is fine. The only failed step is `actions/github-script@<sha>` calling `github.rest.<resource>.<verb>(...)` against the GitHub API. The log inside that step shows:

```
status: 503,
response: {
  url: 'https://api.github.com/repos/<OWNER>/<REPO>/<resource>',
  status: 503,
  headers: { ... x-ratelimit-remaining: 4990 ... },
  data: { message: 'No server is currently available to service your request. Sorry about that. Please try resubmitting your request and contact us if the problem persists.' }
},
request: { method: 'GET', url: '...<resource>' }
```

This is GitHub's own API returning 503 to the workflow runner. The PR's code is **not** the cause. The action framework cannot distinguish "the step's API call hit a 503" from "the step's code threw" — both surface as `conclusion: failure` on the check-run.

## Why this is a trap

1. The PR's `statusCheckRollup` shows red → the natural response is "investigate the PR."
2. The named commit is the headline → the agent looks at the code, finds nothing wrong.
3. The actual cause is GitHub infrastructure → the investigation burns budget on a phantom.

The CI dashboard is **not** the source of truth for transient failures. The job log is.

## Diagnostic recipe (30-90 seconds)

### Step 1 — grab the failing check-run id

```bash
TOKEN="$(gh auth token)"
# Pick from gh pr view --json statusCheckRollup or directly:
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/commits/<HEAD_SHA>/check-runs?per_page=20" \
  | jq '.check_runs[] | select(.conclusion=="failure") | {id, name, details_url}'
```

### Step 2 — get the workflow run's jobs (use databaseId, NOT run_number)

The run's `id` field in the workflow_runs API is the **databaseId** (`29709994853`), distinct from the human-readable `run_number` (`#14728`). The `actions/jobs/{id}/logs` and `actions/runs/{id}/jobs` endpoints expect the databaseId.

```bash
RUN_DB_ID=29709994853  # NOT 14728
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/runs/${RUN_DB_ID}/jobs" \
  | jq '.jobs[] | {id, name, conclusion, failed_steps: [.steps[] | select(.conclusion=="failure") | {name, number}]}'
```

Note the `job.id` (e.g. `88252983872`) and the failed step's `number` (e.g. `2`).

### Step 3 — fetch the failed step's log

```bash
curl -fsS -L -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/jobs/${JOB_ID}/logs" \
  -o /tmp/job-log.bin
```

The endpoint returns a 302 redirect to a Microsoft Azure S3-signed URL (`productionresultssa2.blob.core.windows.net/actions-results/<guid>/workflow-job-run-.../job-logs.txt?rsct=text%2Fplain&se=...&sig=...`). Follow the redirect with `curl -L`; the body is plain text wrapped in a UTF-8 BOM (some content-types reported by `file` will say "Zip archive data" but it's actually a single text file).

If `api.github.com` itself is rate-limiting your curl call, retry after `sleep 30` — the GitHub rate-limit window is per-token and short.

### Step 4 — grep for the transient-failure signature

```bash
python3 -c "
data = open('/tmp/job-log.bin', 'rb').read()
text = data.decode('utf-8', 'replace')
# Strip BOM
if text.startswith('\ufeff'):
    text = text[1:]
# Show last 100 lines
for line in text.split('\n')[-100:]:
    print(line)
"
```

Look for these signatures:

| Pattern | Meaning |
|---------|---------|
| `status: 503` + `message: 'No server is currently available'` | Transient GitHub API degradation — this is the **most common** |
| `status: 429` + `x-ratelimit-remaining: 0` | Per-token rate limit hit inside the workflow |
| `status: 502` / `Bad Gateway` | GitHub infrastructure blip |
| `Conflict: Another merge in progress` | Race against a concurrent operation |
| Empty `output.title` + empty `output.text` + `conclusion: failure` on the check-run | Workflow job died before writing any output — almost always transient infra |
| `Failed to start the runner` / `Failed to create worktree` | Self-hosted runner hiccup |

If you see any of these inside an `actions/github-script` step, the PR is innocent.

### Step 5 — verify locally before retriggering

Before pushing, sanity-check the PR body / commit / branch against the local validator script that the failed workflow uses. For `design-doc-gate.yml`:

```bash
RE='^[[:space:]]*##[[:space:]]+(design[[:space:]]+decision|governing[[:space:]]+design[[:space:]]+doc[[:space:]]*&[[:space:]]+tracking|tenets)([[:space:]]|$)'
gh pr view <N> --repo <OWNER>/<REPO> --json body | jq -r '.body' | grep -iP "$RE" || echo "FAIL"
```

If the local validator PASSES on the same head SHA but CI FAILED with the same content check, the CI failure is **stale-run** or **transient-503-induced-early-exit**, not a real gate violation. Safe to retrigger.

## The fix — empty-commit retrigger

```bash
# From inside the PR's worktree (or a clean clone on the PR's branch)
git -c user.name="<github-username>" \
    -c user.email="<github-username>@users.noreply.github.com" \
    commit --allow-empty -m "ci: retrigger after transient github 503 in <step-name> (job <job-id>)"
git push origin HEAD
```

This creates a new commit SHA on the PR's `headRefName`, fires the `pull_request` event with the correct SHA, and all `pull_request`-triggered workflows re-evaluate. The new run gets a fresh runner allocation; the transient API issue usually clears within minutes.

**Why not `gh workflow run <workflow>.yml`?** Per v2.5.6 of this skill, `gh workflow run` lands on `head_branch=main`, not the PR branch. The dispatch evaluates against `origin/main`'s HEAD, not the PR's. The resulting run is useless for refreshing PR status. **Empty commit is the canonical fix.**

**Why not `@dependabot rebase`?** That works for dependabot PRs only. For first-party branches, use empty commit.

## Verification — proving the retrigger worked

```bash
NEW_SHA="$(git -C <worktree> rev-parse HEAD)"
curl -fsS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/commits/${NEW_SHA}/check-runs?per_page=20" \
  | jq '.check_runs[] | {name, status, conclusion, details_url}'
```

Expected: the previously-failing check shows `status: in_progress` or `conclusion: success` on the NEW SHA, distinct from the prior SHA's red state. If the same check fails again with the same `status: 503` log → escalate to "GitHub is having a bad day" and pause the drive until the incident clears.

## What the user sees when this happens

A Slack thread message like:
> ❌ PR #8466 has failing check(s): Auth Browser Tests (job 88252983872)

That's the headline. The user might reply "is this real?" The correct reply is: "No — log shows `status: 503` from inside `actions/github-script` against `api.github.com/repos/.../pulls/8466`. Transient GitHub API issue. Pushing empty commit on the PR branch to retrigger. Should clear in 1-2 min."

## Anti-patterns

- ❌ Chasing the named PR/commit without reading the log
- ❌ Adding `--retry` flags to the failing step (the action already retries once; a third retry will not help; the underlying API availability issue is on GitHub's side)
- ❌ Reverting a real PR change because of a transient CI failure
- ❌ Trusting `gh pr view --json statusCheckRollup` alone for "is CI green?" — always fetch `/commits/{sha}/check-runs?per_page=50` for the modern GH Actions API
- ❌ Filing a bug report against the PR's code when the log says `status: 503`

## Pair with

- Class-level skill: `gh-actions-transient-failure-diagnosis` — the umbrella for all transient-failure patterns (not just `actions/github-script`)
- `drive-pr-to-green` v2.5.6 — the empty-commit retrigger recipe and the `gh workflow run head_branch` trap
- `gh-actions-slow-runs` — when the failure is "slow" not "red"
- `gh-actions-stuck-self-hosted-runner-recovery` — when the failure is "no log retrievable"