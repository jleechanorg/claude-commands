# GitHub GraphQL rate-limit REST fallback (verified #8390, #8443, #8451)

When `gh issue create` / `gh pr create` hit `GraphQL: API rate limit already
exceeded for user ID 13840161.`, do NOT retry — the budget won't refill for
an hour. Both `gh issue create` and `gh pr create` use GraphQL for the
underlying mutation. `gh-safe-publish` (which gates these calls through the
outbound-secret-publication-gate) does NOT bypass the GraphQL rate limit —
it fails identically when `resources.graphql.remaining == 0`.

**Verified 2026-07-14, 2026-07-18:** the rate-limit signal can flip
mid-session. Always check immediately before the gate call:

```bash
gh api rate_limit --jq '{graphql: .resources.graphql.remaining, graphql_reset: .resources.graphql.reset, core: .resources.core.remaining}'
```

| `graphql.remaining` | `core.remaining` | Action |
|---|---|---|
| `> 500` | any | proceed normally with `gh-safe-publish issue create` |
| `1..500` | any | proceed but expect at most 1 retry — if first gate fails, jump straight to REST |
| `0` | `> 0` | **REST fallback immediately** — REST quota is separate from GraphQL |
| `0` | `0` | wait for reset (both APIs exhausted) |

## REST fallback: `urllib.request` recipe (no extra deps)

The token returned by `gh auth token` works for BOTH GraphQL (`gh` CLI) and
REST (`api.github.com`) — same `Authorization: Bearer <token>` header.

### File an issue (verified #8451)

```python
import json
import subprocess
import urllib.request
import urllib.error

OWNER = "jleechanorg"
REPO = "your-project.com"

def file_issue(token: str, title: str, body: str, labels: list[str]) -> dict:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
    payload = {"title": title, "body": body, "labels": labels}
    body_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body_bytes,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "hermes-repro-fallback/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            parsed = json.loads(err_body)
        except json.JSONDecodeError:
            parsed = {"raw": err_body}
        print(json.dumps({"error": True, "status": e.code, "data": parsed}, indent=2))
        raise

# Source the token the same way `gh` does
token = subprocess.run(["gh", "auth", "token"],
                      capture_output=True, text=True).stdout.strip()
result = file_issue(token, "My title", "My body", ["bug", "repro"])
print(f"Issue #{result['number']}: {result['html_url']}")
```

Returns `{"issue_number": <int>, "url": <str>, "state": "open"}` on success.

### Create a draft PR (verified #8452)

Same pattern but POST to `/pulls`. **Hard prerequisite:** the head branch
MUST already exist on origin before the REST call, otherwise the API
returns `422 head ref does not exist`. The verified sequence:

1. Create a worktree: `git worktree add /path/wt-<topic> -b fix/<branch> origin/main`
2. Commit your changes in the worktree.
3. Push the branch: `git push origin HEAD:refs/heads/fix/<branch>` (or
   `--force-with-lease` if amending).
4. Call the REST PR endpoint with `head: "refs/heads/fix/<branch>"` and
   `base: "main"` and `draft: True`.

```python
def create_draft_pr(token: str, head_branch: str, base_branch: str,
                    title: str, body: str) -> dict:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
    payload = {
        "title": title,
        "head": f"refs/heads/{head_branch}",
        "base": base_branch,
        "body": body,
        "draft": True,
        "maintainer_can_modify": True,
    }
    # ... same urllib.request.Request POST as above ...
```

### Update PR body (PATCH, verified #8452)

```python
def update_pr_body(token: str, pr_number: int, new_body: str) -> dict:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}"
    payload = {"body": new_body}
    body_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body_bytes,
        method="PATCH",  # PATCH for partial update
        headers={"Authorization": f"Bearer {token}", ...},
    )
    # ... same urllib.request.urlopen(req) ...
```

**Curl one-liner alternative (verified #8460):** when you don't want to write a Python script for a single PATCH, the same call works with `curl`:

```bash
curl -fsS -X PATCH \
  -H "Authorization: token $(gh auth token)" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json; print(json.dumps({'body': open('/tmp/pr-body.md').read()}))")" \
  "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<N>" \
  | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'PR #{d[\"number\"]} body len={len(d[\"body\"])}')"
```

The `python3 -c` is needed because `curl -d` does NOT expand `$()` from files; it sends the literal string. For issues the same PATCH pattern works against `/issues/<N>/comments` to post a follow-up comment:

```bash
curl -fsS -X POST \
  -H "Authorization: token $(gh auth token)" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json, sys; print(json.dumps({'body': sys.argv[1]}))" '<comment text>')" \
  "https://api.github.com/repos/<OWNER>/<REPO>/issues/<N>/comments" \
  | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'Comment id={d[\"id\"]} url={d[\"html_url\"]}')"
```

Verified 2026-07-19, draft PR #8460: `gh pr edit 8460 --body-file /tmp/pr-body.md` returned `GraphQL: API rate limit already exceeded for user ID 13840161.` → fell straight to the curl-PATCH above → success (5,104-byte body landed).

## Pitfalls

1. **Don't retry `gh-safe-publish` after first GraphQL `0`.** Each retry
   consumes more of the exhausted budget. Go REST on the first sign of
   rate limit.
2. **Head ref must exist on origin BEFORE the PR create.** The REST API
   doesn't auto-create the branch like `gh pr create` does — it returns
   422. Sequence: worktree → commit → push → REST PR create.
3. **Use PATCH for body updates, not POST.** POST creates a NEW PR; PATCH
   updates the existing one. If you POST by mistake, you end up with two
   PRs and have to close one.
4. **Don't include `maintainer_can_modify: True` unless you genuinely need
   it.** Some orgs reject the field silently; the default (`false`) is
   safer for first-party contributors.
5. **Token source.** `gh auth token` returns the same token that
   `gh-safe-publish` uses internally. NEVER hardcode — pull at runtime
   via `subprocess.run(["gh", "auth", "token"], ...)`.
6. **`User-Agent` header is required.** GitHub's API returns 403 if the
   UA is missing or empty. `"hermes-repro-fallback/1.0"` works; an empty
   string does not.
7. **`X-GitHub-Api-Version: 2022-11-28`** is recommended but not strictly
   required; pinned version prevents surprise behavior changes.

## Verifying the REST fallback worked

After `POST /issues` returns, immediately verify by hitting
`GET /repos/<OWNER>/<REPO>/issues/<N>` — if it returns `state: "open"`
and the correct title, the file is durable. Don't trust the POST
response alone — GitHub has been known to return 202 with delayed
processing under load.

```bash
curl -fsS "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/<N>" \
  -H "Authorization: Bearer $(gh auth token)" \
  -H "Accept: application/vnd.github+json"
```

Same pattern for PRs: `GET /repos/<OWNER>/<REPO>/pulls/<N>` should show
`state: "open"`, `draft: true`, and the correct `head.sha`.

## Outbound-secret-publication-gate interaction

The REST fallback bypasses `gh-safe-publish`'s gate wrapper. **You MUST
still run the body through `lib/outbound_secret_gate.py` BEFORE the POST**
to scan for GitHub PATs, Slack tokens, or HTTPS credentials. The gate
works on the body string, not on the transport — so you can gate locally
then REST-post.

Sequence:
1. Build the body in memory.
2. **Write the body to a path that survives across `execute_code` calls.**
   `/tmp/...` is sandbox-scoped per `execute_code` invocation — a body
   written there in one call is gone by the next call. Use
   `os.path.expanduser("~/.hermes/wa-repro-<issue-no>/issue-body.md")`
   (or similar under `~/.hermes/`), which persists across calls. Verified
   trap: writing to `/tmp/wa-repro-8468/issue-body.md` followed by a second
   `execute_code` call → `FileNotFoundError: [Errno 2] No such file or directory`.
3. **Invoke the gate with the correct CLI shape.** The gate is a positional-
   `mode` + `--file` flag CLI — `--body` is NOT a valid flag. Verified working
   invocation (verified 2026-07-20, issue #8468):
   ```bash
   python3 ~/.hermes/lib/outbound_secret_gate.py check \
     --file ~/.hermes/wa-repro-<issue-no>/issue-body.md
   ```
   The mode is one of `check | redact | fingerprints`. Exit code 0 = clean,
   non-zero = flagged (the script prints what matched). Always run `check`
   before `redact` so you can review what would be redacted.
4. If clean → POST via urllib.
5. If flagged → redact (the script can write a redacted copy), re-scan,
   re-POST. **Do NOT paste the matched string back into your tool calls**
   until you've redacted — copy it into a private scratch file first.

### Common gate-invocation mistakes (verified 2026-07-20, #8468)

| Mistake | Symptom | Fix |
|---|---|---|
| `--body "$BODY"` passed as flag | `error: argument mode: invalid choice: '<body text>'` | Use positional `check` + `--file <path>` |
| Omitting the positional `mode` arg | `error: argument mode: invalid choice: 'check'`-adjacent trace | Always pass `check | redact | fingerprints` as the FIRST positional |
| Body passed inline (no `--file`) | Script reads stdin or errors | Write the body to disk first; use `--file` |
| Looking for the gate in `~/.hermes/scripts/` | `FileNotFoundError` | The gate lives at `~/.hermes/lib/outbound_secret_gate.py` (NOT `scripts/`). The `gh-safe-publish` wrapper IS in `scripts/`, but the standalone gate is in `lib/`. |

