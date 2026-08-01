# GraphQL Rate-Limit REST Fallback

**Added 2026-07-11** after the PR-review-status babysit cron (`1a2566453473`) hit `GraphQL: API rate limit already exceeded for user ID 13840161.` on every `gh pr view --json ...` call while the REST core counter still had 4965/5000 remaining. The babysit was one tick away from posting a misleading "no progress" status when PRs were already merged — the Phase 0 read was silently returning 403 instead of `state=MERGED`.

## Why this happens

GitHub enforces per-user hourly rate limits on multiple endpoints, each with its own counter:

| Counter | Used by | Reset window |
|---|---|---|
| `core` (5000/hr) | REST `/repos/.../pulls/...`, `/contents/...`, `/issues/.../comments`, `/rate_limit` itself | Independent |
| `graphql` (5000/hr) | `gh pr view --json ...`, `gh api graphql`, CodeRabbit-style queries | Independent |
| `search` (30/min) | `gh search ...`, code search | Independent |
| `integration_manifest`, `source_import` | rare | Independent |

When `gh pr view` returns `rate limit already exceeded`, it is the **graphql** counter that's exhausted. The REST `core` counter is usually still near-full and can be used immediately. Waiting an hour for GraphQL to reset when REST still works is a self-inflicted babysit outage.

## Detect which counter is exhausted

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" "https://api.github.com/rate_limit" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)['resources']
for k in ('core', 'graphql', 'search'):
    r = d[k]
    print(f\"{k:8s}: used={r['used']}/{r['limit']} reset={r['reset']}\")"
```

If `core.remaining > 0` AND `graphql.remaining == 0` → use REST recipes below. If both are at 0 → wait for the reset timestamp shown in the response.

## Recipe 1 — Read PR metadata (state, merged_at, mergeable)

This replaces `gh pr view <N> --json state,mergedAt,mergeable,mergedBy`.

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"state: {d['state']}\")
print(f\"merged: {d['merged']}\")
print(f\"merged_at: {d['merged_at']}\")
print(f\"mergeable: {d['mergeable']}\")
print(f\"merged_by: {(d.get('merged_by') or {}).get('login')}\")"
```

Works even when `gh auth status` shows the secondary-account keyring warning — `gh auth token` returns the active account's token, not the keyring fallback.

## Recipe 2 — Read PR issue comments

This replaces `gh api repos/$OWNER/$REPO/issues/$PR_NUMBER/comments`.

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues/$PR_NUMBER/comments?per_page=100" \
  | python3 -c "
import sys, json
for c in json.load(sys.stdin):
    print(f\"{c['created_at']} {c['user']['login']}: {c['body'][:180].replace(chr(10),' ')}\")"
```

## Recipe 3 — Read inline review comments

This replaces `gh api .../pulls/$PR_NUMBER/comments`.

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments?per_page=100"
```

Note: REST returns a flat list of inline review comments without the **thread** nesting GraphQL provides. For nested review-thread state (resolved/unresolved threads per file+line), GraphQL is the only option — wait for the reset.

## Recipe 4 — Read a file from the repo (`.beads/issues.jsonl` etc.)

This is the recipe that unblocked the 2026-07-11 babysit. `jleechanorg/dark-factory`'s `.beads/issues.jsonl` was on GitHub but unreachable in any local clone on the operator's machine. The `contents` API returns the file as base64-encoded content; decode it inline.

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/contents/$PATH" \
  | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
if 'content' in d:
    raw = base64.b64decode(d['content']).decode('utf-8','replace')
    sys.stdout.write(raw)
elif 'message' in d:
    print('API error:', d['message'], file=sys.stderr)"
```

Notes:
- `$PATH` defaults to the **default branch** (usually `main`). To target a specific ref, append `?ref=<branch-or-sha>`.
- Files larger than ~1 MB hit the `contents` API size limit. Switch to `git/blobs/{sha}` for arbitrary size, or use `https://raw.githubusercontent.com/$OWNER/$REPO/<ref>/$PATH` for direct download (no auth header needed for public repos).
- For directories: `contents/<dir>/` returns the directory listing as JSON.

## Recipe 5 — Read repo issues (cross-repo bead sweep)

This replaces `gh issue list --repo ... --json ...`.

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=all&per_page=100&sort=updated&direction=desc" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin):
    if 'pull_request' in i: continue   # skip PRs (issues endpoint returns both)
    print(f\"#{i['number']} [{i['state']}] {i['title']}\")"
```

## Pitfalls

- **`gh auth status` warnings vs `gh auth token` success.** If multiple `gh` accounts are configured (the operator's `jleechan2015` keyring + a separate `$USER-af` for Agnt-F), `gh auth status` may print a red "Failed to log in" line for the secondary account while `gh auth token` still returns the active account's token. Use `gh auth token` for REST fallback. Do NOT refresh auth on the warning alone.
- **Per-PR-per-account vs per-account counter.** Rate limits are per-user, not per-PR or per-repo. A babysit sweeping 10 PRs burns 10 from the counter (one `pr view` each).
- **Secondary rate limits.** REST has its own unlisted secondary rate-limit on burst traffic. If you get HTTP 403 with `Retry-After` header and no JSON body, you're hitting the secondary limit — slow down with `sleep 1` between requests. The 2026-07-11 babysit observed this when sweeping multiple PRs in a single tick.
- **Pagination.** REST endpoints default to 30 items, max 100 per page via `?per_page=100`. For PRs with >100 comments, loop with `?page=N&per_page=100` or use `Link: rel="next"` header parsing.
- **REST returns PRs under `/issues/<N>` for comments.** PRs are technically issues in GitHub's data model — `gh api repos/.../issues/<N>/comments` returns PR conversation comments, while `gh api repos/.../pulls/<N>/comments` returns inline review comments. Use both for a full audit.
- **Files >1 MB.** The `contents` API errors at ~1 MB. For larger files (a fat `issues.jsonl` after 1000+ beads, a generated bundle, etc.), use the `git/blobs/{sha}` API: `GET /repos/$OWNER/$REPO/git/blobs/$SHA` returns base64-encoded content with no size limit (though response time grows).

## When NOT to use this fallback

- You genuinely need GraphQL features (nested review-thread state, `gh pr view --json reviews,reviewThreads`, label aggregation with `--json labels`). REST has no equivalent for these — wait for the GraphQL reset.
- You need to write (post comments, push commits, merge PRs). REST can do all of these but the recipe is out of scope for this reference. Use the standard `github-pr-workflow` skill for write paths.

## Verification

Before relying on REST fallback in production, run this 30-second smoke test from any session that would normally hit GraphQL:

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" "https://api.github.com/rate_limit" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['resources']; \
      assert d['core']['remaining'] > 0, 'REST core exhausted — fallback unavailable'; \
      print('REST fallback ready: core=', d['core']['remaining'])"
```

If the assertion passes, the fallback recipes above will work for the remainder of the hour.
