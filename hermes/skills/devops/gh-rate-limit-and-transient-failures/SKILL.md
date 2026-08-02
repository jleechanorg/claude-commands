---
name: gh-rate-limit-and-transient-failures
description: When gh pr view / gh pr checks / gh run view / gh api returns GraphQL rate-limited, 401 Bad credentials, or 503 No-server-available, this is the diagnostic-and-recovery playbook. Encodes the resolution matrix that distinguishes the three failure modes by their first-word signature and gives the working REST-endpoint recipe that bypasses GraphQL rate-limits.
version: 1.4.0
author: hermes (learned during PR #8467 gate-6b debug, $GITHUB_REPOSITORY, 2026-07-20; PR #8462 dispatch, 2026-07-20; /repro #8501 on q04GfOEl4SWnEQrFUVST, 2026-07-21; PR #8548 `$PROJECT_ROOT/prompts/injection/` extraction, $GITHUB_REPOSITORY, 2026-07-23; 20m inbox-triage cron, 2026-07-24)
changelog:
  - "1.4.0 (2026-07-24) Added cron-defaults section (REST over GraphQL) plus gh-pr-view-json field-name footgun. Verified during the 20m inbox-triage follow-up cron — a 4-PR state sweep with gh pr view --json hit GraphQL rate-limit on the first call. Field-name footgun also surfaced: changed_files does NOT exist in gh pr view --json output; the field is changedFiles. CLI is CamelCase, REST is snake_case. New dedicated section plus a field-name footgun subsection. Cron sessions are single-shot with no interactive budget recovery, so defaulting to gh api REST preserves the operator GraphQL budget for interactive PR-debug sessions."
  - "1.3.0 (2026-07-23) Added gh-pr-create GraphQL-rate-limited section. The existing recipe covered gh pr view / gh pr checks / gh run view / gh api, but NOT gh pr create — which also uses a GraphQL mutation (createPullRequest) and 422s when the bucket is empty. The fix is POST /repos/{owner}/{repo}/pulls via REST with --input <payload.json> (handles the maintainer_can_modify boolean type-coercion that bare -f flags get wrong). Verified 2026-07-23 on $GITHUB_REPOSITORY PR #8548 where the push was already durable on origin/fix/companion-quest-cadence-mirror-8526-clean and the only missing piece was the PR-creation metadata. New matrix row + dedicated section + the working REST recipe + anti-pattern list (don't loop on gh pr create, don't use -f flags, don't try updatePullRequest to rename). Distinct from the existing 1.2.0 gh-safe-publish-wrapper-broken bypass — that one was about the wrapper script itself failing, this one is about GraphQL budget exhaustion."
  - "1.2.0 (2026-07-21) Added gh-safe-publish wrapper broken bypass via REST section. The ~/.hermes/scripts/gh-safe-publish wrapper has a bash parse bug at line 14 (case ... in ... ;; esac mismatched bracket — verified 2026-07-21, hit while filing issue #8501). Symptom is a Python SyntaxError: closing parenthesis does not match opening parenthesis. When the wrapper is broken, the secret-redaction gate can't run via the wrapper; bypass by POSTing directly to REST with urllib.request while still calling outbound_secret_gate.py check manually. New matrix row + dedicated section + the working urllib.request POST recipe."
  - "1.1.0 (2026-07-20) Initial recipe set."
triggers:
  - gh is rate limited
  - GraphQL API rate limit exceeded
  - gh returns 401
  - GitHub 503
  - no server is currently available
  - curl returns Bad credentials from gh auth token
  - read CI logs when gh is broken
  - how to inspect a failed check when pr checks stalls
  - Bad credentials on api.github.com
---

# GitHub CLI / API — Rate-Limit, 401, and 503 Failure Playbook

When `gh` breaks under load, you still need to debug failed CI checks. This skill gives you the resolution matrix and the working REST recipe.

## Why this skill exists

Three failures look identical on the surface — `gh` returns an error, no data — but each has a different fix. Burning 5-10 minutes on the wrong branch of the decision tree is the failure mode. The matrix below is verified against PR #8467 ($GITHUB_REPOSITORY, 2026-07-20) where all three fired in sequence within 90 seconds.

## Symptom → fix matrix (FIRST WORD test)

| First word(s) of error                                              | Failure class                  | Fix                                                        |
|---------------------------------------------------------------------|--------------------------------|------------------------------------------------------------|
| `GraphQL: API rate limit already exceeded`                          | GraphQL rate limit (5000/h, primary budget) | Switch to REST endpoints via `gh api`                    |
| `No server is currently available to service your request` (503)    | Transient 503 (load shedding)  | Retry with 30-60s backoff; usually clears in <2 min         |
| `Bad credentials` (401) from raw `curl` with `gh auth token`       | Token format mismatch           | Use `gh api` wrapper, NOT raw `Authorization: Bearer ...`  |
| `missing_scope: ...`                                                | Token scope gap                 | Re-auth: `gh auth login --scopes "repo,workflow,read:org"` |
| `Not Found` (404) on `/actions/jobs/<id>/logs`                      | Wrong endpoint / archived job  | Try `gh api repos/<o>/<r>/actions/runs/<id>/logs` instead         |
| `gh-safe-publish` wrapper bash syntax error (`closing parenthesis ')' does not match opening parenthesis '['`) | Wrapper script has a shell parse bug (verified 2026-07-21, `~/.hermes/scripts/gh-safe-publish:14`) | Bypass the wrapper and POST directly to REST `https://api.github.com/repos/<owner>/<repo>/issues` (or `/pulls`) via urllib/httpx with `gh auth token`. See "gh-safe-publish wrapper broken" section below. |
| `gh pr create` returns `GraphQL: API rate limit already exceeded for user ID <n>` | GraphQL rate limit hits the `createPullRequest` mutation while the push is already durable on `origin/<branch>` | Switch to REST `POST /repos/<owner}/{<repo>}/pulls` with `--input <payload.json>`. The push is the durable state; the PR creation is a thin REST call that does NOT consume GraphQL budget. Verified 2026-07-23 on $GITHUB_REPOSITORY PR #8548 after the existing skill's recipe for `gh pr checks`/`gh api` did not cover `gh pr create`. |
| `unable to determine default branch for <repo>: GraphQL: API rate limit already exceeded for user ID <n>` from `gh workflow run` | GraphQL rate limit (5000/h, primary bucket) hits the resolver that picks the default branch before `--ref` is applied | Add `--ref <branch>` AND/OR switch to REST `/actions/workflows/<file>/dispatches` (which doesn't need the default branch) |

**Test:** look at the FIRST word(s) of stderr before reading the rest. `'GraphQL'` → use REST. `'No server'` → wait + retry. `'Bad credentials'` → wrap in `gh api`. Don't guess — each fix is wrong for the other two failure classes.

## The working recipe — REST via `gh api`

`gh api` (without `--method`) hits REST endpoints and is **not subject to the GraphQL rate-limit bucket**. When `gh pr checks` returns `GraphQL: API rate limit already exceeded`, the same data is available via:

```bash
# PR metadata (state, mergeable, head SHA, body)
gh api \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  repos/<owner>/<repo>/pulls/<pr_number>

# Check runs (replaces `gh pr checks`)
gh api \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  repos/<owner>/<repo>/pulls/<pr_number>/check-runs

# Job logs (the load-bearing recipe for failed-CI debug)
gh api \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  repos/<owner>/<repo>/actions/jobs/<job_id>/logs > /tmp/job.log 2>&1

# Workflow run jobs + conclusions (replaces `gh run view`)
gh api \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  repos/<owner>/<repo>/actions/runs/<run_id>/jobs \
  --jq '.jobs[] | {name, conclusion, html_url}'
```

Saved ~6 minutes during PR #8467 debug (the Green Gate Precheck GATE-6b failure was hidden behind a GraphQL rate-limit at the moment of inspection).

## Why direct `curl` with `gh auth token` returns 401

`gh auth token` resolves to a short-lived/refreshable token whose format (`ghs_...` or already-rotated) rejects static `Authorization: Bearer` headers in `curl`. The `gh api` wrapper handles the refresh transparently — that's why `gh api` keeps working even when bare curl with the same token value gets 401.

**Symptom:** you read `gh auth token` and get something like `ghp_tP...rzoJ***` (note the trailing `***` — that's the masked portion). When you pass that string as `Authorization: Bearer $TOKEN` in curl, GitHub returns 401.

**Fix:** don't use raw curl. Use `gh api`. The wrapper refreshes the token on each call.

## Don't try these (they waste time)

- `curl https://api.github.com/.../actions/runs/<id>/logs` — endpoint returns 302 to Azure blob storage; urllib / curl-without-follow-redirect fails on the redirect.
- `httpx.post("https://api.github.com/...", headers={"Authorization": f"Bearer {gh_token}"})` — same 401.
- Reading `~/.config/gh/hosts.yml` for the token and exporting it — same refresh token problem.
- Importing Python's `urllib` and following redirects manually — fragile, error-prone, and unnecessary because `gh api` already handles it.
- **`gh workflow run <wf>.yml -f pr_number=N -f test_mode=real`** when GraphQL is rate-limited, *even with `--ref <branch>`* — the CLI hits GraphQL to resolve the default branch before applying `--ref`, so the GraphQL bucket still bites. Use the REST `/actions/workflows/<wf>/dispatches` endpoint instead (no default-branch lookup, no GraphQL). Verified 2026-07-20 on PR #8462 / `mcp-smoke-tests.yml` dispatch.

## Rate-limit reset check (without burning GraphQL budget)

To check remaining GraphQL budget without consuming it (which would worsen the rate-limit), use the REST `/rate_limit` endpoint:

```bash
gh api rate_limit --jq '.resources.graphql'
# Returns: {"limit":5000,"used":5058,"remaining":0,"reset":1784510958}
```

This is REST-not-GraphQL so it stays available even when GraphQL budget is exhausted.

## Anti-patterns to avoid

1. **Don't import `httpx` / `requests` to write a "fixed" GitHub client.** Use `gh api`. The CLI exists for this.
2. **Don't pipe `gh auth token` to `curl -H "Authorization: Bearer $(cat)"`** — passes the masked value with `***` suffix → guaranteed 401.
3. **Don't retry the GraphQL endpoint when it's rate-limited.** Each retry burns the rolling-window budget further. Switch to REST.
4. **Don't wait for the 5000/h budget reset before doing useful work.** A 30-60s exponential backoff on REST clears most 503s.
5. **Don't try `--paginate` or `--limit 1000` on `gh pr checks`** during a rate-limit window — that's a GraphQL endpoint, you'll exhaust the budget for nothing.

## Verification

After fixing a failed check, run the working REST recipe to confirm:

```bash
# 1. PR is still open and mergeable
gh api repos/<owner>/<repo>/pulls/<pr_number> \
  --jq '{state: .state, mergeable: .mergeable, head_sha: .head.sha}'

# 2. Latest check-run conclusions
gh api repos/<owner>/<repo>/commits/<head_sha>/check-runs \
  --jq '.check_runs[] | {name, conclusion, html_url}'

# 3. (If failure persists) re-fetch the failed job's logs via the REST recipe.
```

If all three return data without `GraphQL: API rate limit` or 503 errors, your workflow is unstuck.

## Reference files

- `references/pr-8467-recovery-transcript.md` — the verified transcript showing all 5 failure modes firing in sequence within 90 seconds during PR #8467 green-gate debug (2026-07-20), with the working `gh api` recipe that recovered in ~30 seconds.
- The REST-vs-GraphQL choice is the canonical workaround in SOUL.md `gh-actions-stuck-self-hosted-runner-recovery` skill (different failure class — runner queue stuck, not API rate-limit).
- The 8-section PR-body template (the OTHER class of failure that hides behind gate validators) lives at `wa-green-gate-pr-shape/templates/pr-body-8-section.md`.

## `gh-safe-publish` wrapper broken — bypass via REST (verified 2026-07-21)

The `~/.hermes/scripts/gh-safe-publish` wrapper around `gh issue create` / `gh pr create` is meant to scan the body file with `lib/outbound_secret_gate.py` before publishing. **But the wrapper itself can be broken** (e.g. line-14 bash parse error: `closing parenthesis ')' does not match opening parenthesis '['`). When that fires, the wrapper is unusable for ALL publishing, not just for one call.

**Symptom:**
```
$ gh-safe-publish issue create --repo X --body-file Y
File "$HOME/.hermes/scripts/gh-safe-publish", line 14, in <module>
    "issue create"|"issue comment"|"pr create"|"pr comment"|"gist create") ;;
                                                                         ^
SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' on line 8
```

**Bypass recipe — POST directly to the REST API while still running the gate first:**

```python
import json, subprocess, urllib.request, urllib.error

# 1. Run the gate manually (same check the wrapper would have run)
subprocess.check_call(["python3", "$HOME/.hermes/lib/outbound_secret_gate.py",
                       "check", "--file", body_file_path])

# 2. Read the token (NOTE: per the 401 pitfall above, this approach to token-fetching
#    works for `gh api`-style flows. For bare REST POST you may need a different mechanism
#    — see "Token-format pitfall" below.)
tok = subprocess.check_output(["gh", "auth", "token"], text=True).strip()

# 3. POST to GitHub REST API
payload = {"title": "...", "body": open(body_file_path).read(), "labels": [...]}
req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/issues",
    method="POST",
    headers={
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    data=json.dumps(payload).encode(),
)
with urllib.request.urlopen(req, timeout=30) as resp:
    print(json.load(resp)["html_url"])
```

**Token-format pitfall (this is the second failure mode the bare-curl approach can hit).** `gh auth token` may return a **masked** token ending in `***` (or a value that 401s when used raw in `Authorization: Bearer`). If your POST returns 401, switch to `gh api`:

```bash
# Let gh write the JSON body and POST it (uses gh's token-refresh wrapper)
cat > /tmp/issue.json <<EOF
{"title": "...", "body": "...", "labels": ["..."]}
EOF
gh api -X POST repos/<owner>/<repo>/issues --input /tmp/issue.json
```

**Important caveat about the gate.** The gate still runs at step 1 — `outbound_secret_gate.py check` works even when the wrapper is broken. **Never skip the gate** to "save time" — that's how PATs end up in published issues (see the `outbound-secret-redaction-gate` security skill for the verified incident).

**Fix the wrapper separately.** The bash parse error is a 30-second fix once you spot it (`case "..." in ... ;; esac` mismatched bracket) but don't block on fixing the wrapper — bypass it via REST and file a follow-up to patch the script.

## `gh pr create` GraphQL rate-limited — switch to REST `POST /repos/{owner}/{repo}/pulls` (verified 2026-07-23, PR #8548)

The skill's existing recipe covered `gh pr view`, `gh pr checks`, `gh run view`, and `gh api`. The gap that bit during PR #8548: `gh pr create` ALSO uses GraphQL under the hood (the `createPullRequest` mutation), and when the GraphQL bucket is exhausted, `gh pr create` returns `GraphQL: API rate limit already exceeded for user ID <n>`. The branch is already pushed (the push is durable state per SOUL.md `push-pr-donot-stop-halfway`), so the only thing missing is the PR-creation thin call.

**Don't waste cycles retrying `gh pr create`.** Each retry burns GraphQL budget. The fix is to bypass the GraphQL mutation entirely via REST.

**Working recipe (verified 2026-07-23, $GITHUB_REPOSITORY PR #8548):**

```bash
# 1. The push is already durable (DONE in the prior turn).
git -C <repo> rev-parse origin/<branch>
# Verify the SHA matches what you intended to push.

# 2. Confirm the PR does NOT already exist via REST (NOT GraphQL — would burn budget):
gh api repos/<owner>/<repo>/pulls?head=<owner>:<branch>&state=all \
  -q '.[].number' | grep -v '^$' || echo "PR does not exist yet"

# 3. Build the PR payload as JSON (avoid `gh api -f` here — `maintainer_can_modify`
#    type-coerces badly with -f flags; --input is the clean path):
cat > /tmp/pr-payload.json <<EOF
{
  "title": "<pr title>",
  "head": "<branch>",
  "base": "main",
  "body": "<full PR body — multiline JSON string>",
  "maintainer_can_modify": true,
  "draft": false
}
EOF

# 4. POST to REST (no GraphQL consumption):
gh api -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  repos/<owner>/<repo>/pulls \
  --input /tmp/pr-payload.json

# 5. Verify the PR was created (still REST, no GraphQL):
gh api repos/<owner>/<repo>/pulls \
  -q '.[] | select(.head.ref=="<branch>") | {number, html_url, state}' \
  | head -5
```

**Why this works:**

- `POST /repos/{owner}/{repo}/pulls` is a REST endpoint, NOT a GraphQL mutation. It draws from the REST rate-limit bucket (separate budget; not affected by `createPullRequest` GraphQL exhaustion).
- The push is durable on `origin/<branch>` BEFORE you attempt PR creation. The PR-creation call is just metadata — nothing about the underlying work is at risk if the PR call fails.
- The recipe handles the type-coercion pitfall with `gh api -f`: the `maintainer_can_modify` field must be a JSON boolean (not the string `"true"`). Using `--input <payload.json>` with explicit JSON gets the type right; `-f` flags string-coerce everything.

**Anti-patterns:**

- ❌ Loop on `gh pr create` with `sleep 30 && gh pr create ...` waiting for the GraphQL bucket to refresh. Burns budget and can take 8+ hours to reset (the reset window is the rolling 5000/h bucket).
- ❌ Try `gh pr create --head <branch>` with no other flags — same GraphQL path, same failure.
- ❌ Open the PR via the GitHub web UI from the terminal session — the agent doesn't have a browser here.
- ❌ Pre-create the PR via a placeholder title (`"WIP: PR <N>"`) and rename later — that ALSO consumes GraphQL budget on `updatePullRequest`.

**`gh pr view --json` field-name footgun.** The field names returned by `gh pr view --json` are CamelCase and don't match REST field names one-to-one. The field that bites is `changedFiles` (NOT `changed_files`). Easy way to get the exact list without guessing:

```bash
gh pr view --help | grep -A1 '\-\-json' | head -10
# OR just call gh pr view with one bogus field to get the available-fields error:
gh pr view 123 --json bogus --repo foo/bar
# Error: Unknown JSON field: "bogus"
# Available fields:
#   additions
#   assignees
#   author
#   ...
#   changedFiles
#   closed
#   ...
```

Field name → REST mapping that bit me (2026-07-24 cron): `changedFiles` (CLI) ↔ `changed_files` (REST), `mergedAt` (CLI) ↔ `merged_at` (REST). The CLI uses CamelCase, the REST API uses snake_case. When in doubt, default to `gh api repos/<owner>/<repo>/pulls/<N>` and `--jq` your way to the shape you need — the REST field names are stable and self-documenting.

## Cron jobs / scheduled follow-ups: prefer REST `gh api` over GraphQL `gh pr view` by default (verified 2026-07-24)

A scheduled 20m inbox-triage follow-up fired in this session and hit `GraphQL: API rate limit already exceeded for user ID 13840161` immediately on the first `gh pr view --json number,title,state,mergedAt,updatedAt,headRefName,author,additions,changed_files ...` call across 4 PRs. Recovery was a one-line swap to REST (`gh api repos/<owner>/<repo>/pulls/<n> --jq "{number, title, state, merged, merged_at, updated_at, head: .head.ref, base: .base.ref, additions, changed_files}"`), but the operator's GraphQL budget was already spent.

**The lesson:** cron jobs and other low-stakes scheduled state-checks should default to `gh api` REST from the start, not `gh pr view` GraphQL. Rationale:

1. **Cron sessions have no interactive context to recover from a rate-limit.** When an interactive session hits the limit, the operator can wait 30-60s and pick a different approach. A cron session is a single-shot — once the GraphQL bucket is empty, every subsequent `gh pr view`/`gh pr list`/`gh pr checks` in the same job will fail.
2. **Cron state-checks are routine and well-served by REST.** The fields you actually need for "did PR X change state?" — `state`, `merged`, `merged_at`, `updated_at`, `head.sha`, `additions`, `changed_files` — are all available via REST with stable field names. The CLI's CamelCase reshuffling adds friction, not value.
3. **Preserve the operator's GraphQL budget for interactive sessions.** A heavy 20m-tick cron that polls 4-8 PRs with `gh pr view` every tick burns 5000/h of budget that the operator's interactive PR-debug sessions also need. REST `/repos/.../pulls/<n>` does NOT consume the GraphQL bucket.

**Working cron-friendly recipe (verified 2026-07-24):**

```bash
# Quick "did it change?" state-check for one PR — REST, no GraphQL
gh api repos/<owner>/<repo>/pulls/<N> \
  --jq '{state: .state, merged: .merged, merged_at: .merged_at, updated_at: .updated_at, head_sha: .head.sha, additions: .additions, changed_files: .changed_files}'

# Multi-PR sweep (loop, not parallel GraphQL):
for pr in 8551 8559 8561 8564; do
  echo "=== PR #$pr ==="
  gh api "repos/$GITHUB_REPOSITORY/pulls/$pr" \
    --jq '{number, title, state, merged, merged_at, updated_at, head: .head.ref, base: .base.ref, additions, changed_files}'
done
```

**When GraphQL is still appropriate in a cron:** never. If you find yourself reaching for `gh pr list --search` or `gh pr view --json` from a cron, stop and use `gh api` with explicit `--jq` filters instead. The CLI conveniences don't pay off when the budget is the binding constraint.

**Edge case — the GraphQL bucket is truly exhausted for hours:** this happens when an earlier session burned the bucket via heavy `gh pr list --search` polling. The reset window is the rolling 5000/h bucket; check via REST:

```bash
gh api rate_limit --jq '.resources.graphql'
# Returns: {"limit":5000,"used":5058,"remaining":0,"reset":1784860131}
# If `remaining: 0` AND the `reset` epoch is hours away, REST creation is the only option.
```

**Edge case — `gh api` itself 401s:** the existing skill already covers this (`gh auth token` returns a masked/rotated value that 401s on bare `Authorization: Bearer`). `gh api` wraps the token refresh, so it stays working. If `gh api` 401s, re-auth with `gh auth login --scopes "repo,workflow,read:org"`.

## Recipes for the three sibling failures

| Failure                              | Skill to load                                |
|--------------------------------------|----------------------------------------------|
| Self-hosted runner stuck / unhealthy | `gh-actions-stuck-self-hosted-runner-recovery` |
| Action job log shows specific error  | `wa-cloud-run-deploy-failure-debug` (Cloud Run) or `gh-actions-slow-runs` (general perf) |
| PR-description validator rejects body | `wa-green-gate-pr-shape` (GATE-6b 8-section scaffold) |
