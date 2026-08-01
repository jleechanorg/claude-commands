---
title: GraphQL rate-limit wedges `gh pr create` — fall back to REST POST `/repos/.../pulls`
date: 2026-07-12
verified-on: $GITHUB_REPOSITORY PR #8337 (fix/state-update-warnings)
---

## Symptom

`gh pr create --repo <owner>/<repo> --base main --head <branch> --title "..." --body-file <path>` returns:

```
GraphQL: API rate limit already exceeded for user ID 13840161.
```

But `gh api rate_limit --jq '.resources | {core: .core.remaining, graphql: .graphql.remaining}'` shows:

```json
{"core": 4486, "graphql": 0}
```

The token's GraphQL bucket is exhausted (often from prior `gh pr list` / `gh pr view` / `ao spawn` activity that all hit GraphQL) but the REST Core bucket still has plenty. `gh pr create` uses GraphQL internally, so it wedges; REST POST to the same endpoint bypasses the wedge.

## Why this happens

- The shared `jleechan2015` GitHub token is used by `gh auth`, `ao spawn`, the orchestrator, and the gateway session.
- GraphQL quota is 5000 points per hour; each `gh pr list --json ...` / `gh pr view --json ...` / `ao spawn ...` consumes 1-50 points depending on depth.
- REST Core is a separate 5000/hour bucket that `gh api` and `curl https://api.github.com/repos/...` share.

The token's GraphQL bucket can hit zero while REST Core still has 4000+. `gh pr create` wedges; `curl -X POST .../repos/.../pulls` works.

## Fix: REST POST for PR creation

```python
import json, subprocess, urllib.request

# 1. Source the GH token (works from execute_code which doesn't auto-source bashrc)
token_proc = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
gh_token = token_proc.stdout.strip()

# 2. Write the body to a file FIRST (avoids shell-quoting parens in --title / --body)
#    See companion reference "PR body shell-quoting trap" below.
title = open("/tmp/pr-title.txt").read().strip()
body = open("/tmp/pr-body.md").read()

# 3. POST JSON directly
payload = {
    "title": title,
    "head": "fix/<branch>",
    "base": "main",
    "body": body,
    "draft": False,
}
req = urllib.request.Request(
    "https://api.github.com/repos/<owner>/<repo>/pulls",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "hermes-agent",
    },
    method="POST",
)
resp = urllib.request.urlopen(req, timeout=60)
pr_data = json.loads(resp.read())
print(f"PR #{pr_data['number']} created: {pr_data['html_url']}")
```

This bypasses GraphQL entirely — REST POST `/repos/.../pulls` is the same operation, just on a different endpoint.

## Fix: REST PATCH for PR body updates

```python
req = urllib.request.Request(
    f"https://api.github.com/repos/<owner>/<repo>/pulls/<N>",
    data=json.dumps({"body": new_body}).encode(),
    headers={"Authorization": f"Bearer {gh_token}", ...},
    method="PATCH",
)
```

Same trick. Used for `gh pr edit <N> --body-file ...` when that wedges.

## Companion fix: PR body shell-quoting trap

When passing the body inline via `bash -c "..."` or `gh pr create --body "..."`, **parens in the title break the bash heredoc**:

```
/opt/homebrew/bin/bash: eval: line 6: syntax error near unexpected token `('
```

Verified on PR #8337 — title was `fix(schema): hide state-update schema-gate warnings (Slack C0AH3RY3DK6/1783845865.692919, 2026-07-12)`. Fix: write title + body to files, then either pass them via `--title "$(cat /tmp/title.txt)" --body-file /tmp/body.md` OR skip the shell entirely and use the REST POST above with `json.dumps(...)`.

## When to apply this recipe

1. `gh pr create` / `gh pr edit` returns GraphQL rate-limit error.
2. The driver skill (`drive-pr-to-green` Step 7c) only documents the REST fallback for `gh pr merge` — NOT for PR creation. That's a gap; this reference fills it.

The `drive-pr-to-green` skill's Step 7c quotes `gh api -X POST` for the merge endpoint but the recipe for `gh pr create` is new in this reference.

## Verification

After REST POST:

```python
import subprocess
r = subprocess.run(["gh", "pr", "view", "<N>", "--repo", "<owner>/<repo>",
                    "--json", "number,state,mergeable,headRefName,baseRefName"],
                   capture_output=True, text=True, timeout=10)
print(json.loads(r.stdout))
```

`gh pr view` may ALSO use GraphQL internally, so if it wedges too, fall back to REST:

```bash
curl -fsS "https://api.github.com/repos/<owner>/<repo>/pulls/<N>" \
    -H "Authorization: Bearer $(gh auth token)" \
    | python3 -m json.tool | head -30
```

## Why `drive-pr-to-green` Step 7c didn't cover this

The skill was authored before PR #8337; its Step 7c covers the GH rate-limit fallback for `gh pr merge` only (REST `PUT /repos/.../pulls/<N>/merge`). PR creation wasn't a common failure mode because most agents hit the merge rate-limit, not the create rate-limit. PR #8337 broke this assumption because the agent ran `ao spawn` 3 times (each one consumed GraphQL points), exhausted the bucket, then tried to create a PR — and `gh pr create` is on the same GraphQL bucket.

Update the upstream skill's Step 7c to include the `gh pr create` REST POST fallback. Until that's done, this reference is the canonical recipe.

## Cost

~3 tool calls: source token, write title/body to files, POST. Compare to ~30+ minute wait for the GraphQL bucket to reset (GraphQL quota resets hourly per `gh api rate_limit` `reset_graphql` epoch).
