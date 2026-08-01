# GitHub GraphQL rate-limit → REST fallback (verified 2026-07-23)

The `gh` CLI hides a non-obvious dual-bucket rate-limit architecture. This
reference captures the symptom, the fall-back recipe, and the dual-bucket
rule so a future session doesn't waste 90 seconds on a sleep-retry loop
that cannot help.

## Symptom

`gh pr view --json`, `gh pr create`, `gh pr list --json`, `gh pr edit`, and
`gh pr merge --auto` all use the GitHub GraphQL API under the hood. When
GraphQL is exhausted, you see:

```
GraphQL: API rate limit already exceeded for user ID <N>.
```

The REST API has its own 5000/hr per-account bucket. The two are
**separate** and **drain independently**.

## The dual-bucket rule

> REST (core) and GraphQL are SEPARATE per-account 5000/hr buckets that
> drain independently. `gh api rate_limit` is quota-EXEMPT — check it
> FIRST to see which bucket is live. Fall back across buckets
> (GraphQL→REST or REST→GraphQL) for the SAME data; only report
> "rate-limited" when BOTH are at/near 0.

In practice this means: the moment a `gh` command errors with
"API rate limit already exceeded", switch to `gh api` (or `curl`) REST
for the SAME operation. **Do NOT sleep-retry GraphQL** — that just
extends the rate-limit window and burns the bucket for OTHER queries.

## REST fallbacks for the common `gh pr` operations

| `gh` command (GraphQL) | REST fallback (`gh api` / `curl`) |
|---|---|
| `gh pr view <N> --json state,headRefName` | `gh api /repos/<OWNER>/<REPO>/pulls/<N>` |
| `gh pr list --state open` | `gh api /repos/<OWNER>/<REPO>/pulls?state=open` |
| `gh pr list --search <q>` | `gh api "/repos/<OWNER>/<REPO>/pulls?state=all&per_page=100"` + `python3` filter |
| `gh pr create --title ... --body ...` | `gh api /repos/<OWNER>/<REPO>/pulls --method POST -f title="..." -f head="..." -f base="main" -f body="..."` |
| `gh pr edit <N> --add-reviewer <u>` | `gh api /repos/<OWNER>/<REPO>/pulls/<N>/requested_reviewers --method POST -f "reviewers[]=<u>"` |
| `gh pr close <N>` | `gh api /repos/<OWNER>/<REPO>/pulls/<N> --method PATCH -f state=closed` |
| `gh pr comment <N> --body "..."` | `gh api /repos/<OWNER>/<REPO>/issues/<N>/comments --method POST -f body="..."` |

For status checks, the REST endpoint is `/repos/<OWNER>/<REPO>/commits/<SHA>/check-runs`
(check-runs) and `/repos/<OWNER>/<REPO>/commits/<SHA>/status` (legacy
statuses). Both are REST — never hit by GraphQL.

## Verified 2026-07-23 (your-project.com PR review session)

In a single ~15-minute turn, the agent hit "GraphQL: API rate limit
already exceeded for user ID 13840161" on 5 consecutive `gh pr view
--json` / `gh pr create` calls. The mitigation:

1. **Switched all data fetches to `gh api /repos/.../pulls/<N>` REST.**
   Worked every time. Pulled `state`, `additions`, `changedFiles`,
   `mergeable`, `reviewDecision`, `latestReviews`, `headRefOid`,
   `createdAt`, `updatedAt` via REST + `python3 -c` JSON extraction.
2. **For check-runs / statuses:** `gh api /repos/.../commits/<SHA>/check-runs`
   REST worked; used `python3 -c` to print the (name, conclusion) tuple
   for each check, then sorted by timestamp to surface the latest
   Green Gate / Bugbot / Smoke Gate verdict.
3. **`gh pr create` is the hardest hit:** it ALWAYS uses GraphQL.
   After ~90s the GraphQL bucket recovered enough to call `gh pr
   create` once (created a clean-replay branch), then it locked out
   again on the next attempt. **The 90s wait did NOT re-free other
   endpoints** (the bucket drains as a single quota even when only one
   endpoint is being used).

The fix is the dual-bucket rule, not patience. In a follow-up the
`pr-cleanup-replay` skill's Phase 3.7 (value-retune) explicitly pauses
BEFORE auto-opening the new PR, so the user gets a chance to decide on
the value before the GraphQL bucket gets drained by an auto-`pr create`.

## Why this matters for `pr-cleanup-replay` Phases 3 / 3.5 / 3.7

Every Phase 3+ recipe in `pr-cleanup-replay` needs to:

- `gh pr view <N> --json headRefOid,files` to confirm Phase 3.5 replay
  preserved only the intended files.
- `gh pr list --head <branch>` to verify the close-and-reopen invariant.
- `gh pr create` for Phase 3 / 3.7 / 5 new-PR opens.

When GraphQL is locked, the recipes still complete via REST — but
inspect every REST response with a `python3 -c` filter because
`gh api`'s default output is the raw JSON dump. The recipes in
`pr-cleanup-replay` should be read as "REST-first if GraphQL is locked".

## Recipe: REST equivalent of `gh pr view --json <N>`

```bash
# When GraphQL is rate-limited, pull PR data via REST:
gh api /repos/<OWNER>/<REPO>/pulls/<N> | python3 -c "
import json,sys
d = json.loads(sys.stdin.read())
print(f'#{d[\"number\"]} [{d[\"state\"]}] mergeable={d.get(\"mergeable\",\"?\")} '
      f'additions={d[\"additions\"]} deletions={d[\"deletions\"]} '
      f'changedFiles={d[\"changed_files\"]} base={d[\"base\"][\"ref\"]} '
      f'head={d[\"head\"][\"ref\"]} sha={d[\"head\"][\"sha\"][:10]}')
"
```

## Recipe: REST equivalent of `gh pr list --json headRefName,state,additions,changedFiles`

```bash
gh api "/repos/<OWNER>/<REPO>/pulls?state=open&per_page=100" | python3 -c "
import json,sys
d = json.loads(sys.stdin.read())
for p in d:
    print(f'#{p[\"number\"]:>4} [{p[\"state\"]}] +{p[\"additions\"]:>5}/-{p[\"deletions\"]:>4} '
          f'{p[\"changed_files\"]:>2}f | {p[\"title\"][:80]}')
"
```

## Recipe: REST equivalent of `gh pr create`

```bash
gh api /repos/<OWNER>/<REPO>/pulls --method POST \
  -f title='<title>' \
  -f head='<branch>' \
  -f base='main' \
  -F body='<body>'
# `-F` (capital) for body preserves newlines; `-f` would URL-encode them.
```

## When both buckets are exhausted

If `gh api rate_limit` shows BOTH buckets near 0, the recovery is
**wait for `X-RateLimit-Reset`** (epoch seconds returned in the
`X-RateLimit-Reset` header). For a typical `jleechan2015` account
this is 30-60 minutes. In the meantime:

1. **Do NOT issue any more `gh` calls** — each call burns a few extra
   minutes off the reset window even if it returns 403.
2. **Use `git` + `git ls-remote` + `git log --oneline origin/<branch>`**
   for any data the agent needs from the remote.
3. **For full PR diff data:** `git fetch origin` + `git diff origin/main...origin/<branch>`
   gives you the local-side diff with no rate-limit cost.

## See also

- `pr-cleanup-replay` Phase 3 (close-and-reopen), Phase 3.5 (in-place
  force-push), Phase 3.7 (value retune) — all assume the dual-bucket
  rule and pivot to REST when GraphQL is locked.
- SOUL.md `## COMMIT: pr-clean-branch-from-main-no-history-bloat` —
  the SOUL-level rule this reference operationalizes.
- `claude-code` AGENTS.md § "GitHub CLI — REST API fallback" — mirrors
  the dual-bucket rule for the Codex/Codex-CLI runtime.
