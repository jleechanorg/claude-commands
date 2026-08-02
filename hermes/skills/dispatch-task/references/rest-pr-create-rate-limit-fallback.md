# REST PR creation after GraphQL rate-limit or hang

Use this recipe after a branch is pushed when `gh pr create` or `gh pr list` uses the GraphQL path and fails, hangs, or returns only a rate-limit error.

## Preconditions

- The branch already exists on `origin`.
- You know the exact expected HEAD SHA.
- You have the final PR title and body in a file.
- The body has passed the outbound-secret gate.

## 1. Verify branch and search for an existing PR

```bash
OWNER_REPO=<owner>/<repo>
OWNER=${OWNER_REPO%%/*}
BRANCH=fix/<topic>
EXPECTED_SHA=<expected-head-sha>

git ls-remote origin "refs/heads/$BRANCH"
gh api "repos/$OWNER_REPO/pulls?state=all&head=$OWNER:$BRANCH&per_page=100" \
  --jq '.[] | {number,html_url,state,draft,head_sha:.head.sha}'
```

If an existing PR is returned, verify its head SHA before doing anything else. Do not create a duplicate.

## 2. Scan the exact outbound body

```bash
BODY_FILE=/tmp/pr-body.md
$HOME/.hermes/lib/outbound_secret_gate.py check --file "$BODY_FILE"
```

Use the canonical gate path for the active host if it differs. If blocked, redact the complete credential to `[REDACTED]` or a safe fingerprint, scan again, and only then continue.

## 3. Create a draft PR through REST

Use `-F draft=true` rather than `-f draft=true` so the field is a JSON boolean, not a string:

```bash
BODY=$(<"$BODY_FILE")
gh api -X POST "repos/$OWNER_REPO/pulls" \
  -H 'Accept: application/vnd.github+json' \
  -f title="$TITLE" \
  -f head="$OWNER:$BRANCH" \
  -f base="${BASE:-main}" \
  -f body="$BODY" \
  -F draft=true \
  --jq '{number,html_url,state,draft,head_sha:.head.sha}'
```

If the REST call returns `Problems parsing JSON`, inspect the typed flags first; do not retry blindly. In particular, check that `draft` was supplied with `-F`, and use `-f` for string fields.

## 4. Verify the side effect

```bash
gh api "repos/$OWNER_REPO/pulls?state=all&head=$OWNER:$BRANCH&per_page=100" \
  --jq '.[] | {number,html_url,state,draft,head_sha:.head.sha}'

gh api "repos/$OWNER_REPO/pulls/$NUMBER" \
  --jq '{number,html_url,state,draft,head:.head.ref,head_sha:.head.sha,mergeable,mergeable_state}'
```

Require all of:

- expected branch
- expected HEAD SHA
- `state=open`
- `draft=true` when requested
- a real `html_url`

A successful POST response or a pushed remote ref alone does not prove that a PR exists.

## 5. Report CI accurately

`mergeable=true` and `mergeable_state=clean` only describe Git ancestry/conflicts. They do not mean CI passed. Query the head commit's check runs and report counts separately:

```bash
gh api "repos/$OWNER_REPO/commits/$EXPECTED_SHA/check-runs?per_page=100" \
  --jq '[.check_runs[]] | {
    total:length,
    success:map(select(.conclusion=="success"))|length,
    failed:map(select(.conclusion=="failure" or .conclusion=="timed_out" or .conclusion=="action_required" or .conclusion=="startup_failure" or .conclusion=="cancelled"))|length,
    skipped:map(select(.conclusion=="skipped"))|length,
    pending:map(select(.status!="completed"))|length
  }'
```

If required checks are skipped because the PR is a draft, say `draft PR pushed; CI/evidence incomplete`, not `green` or `ready to merge`.

## Evidence

This fallback was exercised for a two-PR fanout after GraphQL PR creation hung/rate-limited. Both REST-created draft PRs were independently found through `pulls?state=all&head=...`, and both remote refs matched their expected SHAs.
