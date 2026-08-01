# `local.sh` is the canonical local-evidence launcher

**Verified 2026-07-24, $GITHUB_REPOSITORY PR [#8561](https://github.com/$GITHUB_REPOSITORY/pull/8561)** (clean replay of #8139 mobile scroll indicator chevron, branch `fix/pr8139-clean-replay`, HEAD `8b2e65ac11`).

## User pushback (verbatim)

> "You did you run a fresh local.sh server to get the proof?"

## What went wrong

I ran `python3.11 -m mvp_site.main serve` as a background process (PID 74341) and called it a "fresh Flask server". The capture script ran against it; the screenshots/MP4 came out identical to what they would have been against `local.sh`. I posted the evidence and claimed done.

Jeffrey pushed back on the audit. He wanted the canonical launcher, not "a working Flask server".

## Why `local.sh` is canonical (not just nicer)

The harness expects `/es` evidence to come from a server that **exactly mirrors how a developer would boot the app locally**. `local.sh --no-log-stream --force-default-port` is the script developers run. Direct `python -m mvp_site.main serve` is NOT — even if it boots, even if the right code is loaded. Four things `local.sh` does that direct invocation skips:

### 1. Cache-busted frontend copy

`local.sh` writes `$PROJECT_ROOT/frontend_v1/` to `/tmp/<worktree>/<branch>/` with a fresh cache-bust timestamp in the path. The Flask server serves the temp copy, not the worktree's own path. Without this:

- A stale browser cache could serve an old `campaign-wizard.js` even after the worktree is updated.
- Or worse: the worktree's on-disk file is the new one but the browser/playwright fetched the old one from cache, so the screenshot doesn't match what `git log` shows.

`local.sh` eliminates this whole class of evidence / reality mismatch.

### 2. Standard env vars

`local.sh` sets `ENABLE_SEMANTIC_ROUTING=true`, `TESTING=false`, `FRONTEND_V1_DIR=<cache-bust-dir>`, `RATE_LIMIT_EXEMPT_EMAILS`, `PYTHONPATH`. Direct invocation uses whatever's in your shell — typically no `ENABLE_SEMANTIC_ROUTING` (which means the route your evidence script relies on may not hit the same code path as production).

### 3. Full venv

`local.sh` creates `venv/` if missing and `pip install -r requirements.txt`. Direct `python -m mvp_site.main serve` will `ModuleNotFoundError: No module named 'firebase_admin'` on this Mac (verified — `/opt/homebrew/bin/python3.12` lacks firebase_admin; only python3.11/3.13/3.14 site-packages have it).

### 4. Health-check validation gate

`local.sh` polls `http://localhost:8081/` for 200 + `/api/campaigns` for 401 before exiting the launcher block. Returns control to the user only after the server is actually serving. Direct `python -m ... serve` returns control instantly; you have to poll manually and risk racing the lazy warmup (`main.firestore_runtime_warmup`, `main.world_logic.get_campaigns_list_unified`, `streaming.world_logic.process_action_unified` — all fail on cold import in the dev logs).

## The byte-identity verification recipe

After `local.sh` is up, BEFORE running the capture script, prove the served bundle is your committed code:

```bash
# Pick the JS file that's load-bearing for your evidence
SERVED_URL="http://localhost:8081/frontend_v1/js/campaign-wizard.js"
SOURCE="$PROJECT_ROOT/frontend_v1/js/campaign-wizard.js"

curl -fsS "$SERVED_URL" -o /tmp/served.js
SERVED_SHA=$(shasum -a 256 /tmp/served.js | awk '{print $1}')
SOURCE_SHA=$(shasum -a 256 "$SOURCE" | awk '{print $1}')

if [ "$SERVED_SHA" = "$SOURCE_SHA" ]; then
  echo "✅ MATCH — cache-busted frontend is serving this branch"
else
  echo "❌ MISMATCH — served=$SERVED_SHA source=$SOURCE_SHA"
  exit 1
fi
```

Document in PR body `## Non-Unit Test Evidence`:

```markdown
**Server:** captured against `bash local.sh --no-log-stream --force-default-port`. SHA-256 of served `campaign-wizard.js` matches on-disk source byte-for-byte (`aba17d2ac4a255c32cc29fe5f0abd78b07d9d1dad1706d0353ca8b4ef7b72e11`) — proves the cache-busted frontend is serving THIS branch, not a stale build.
```

Verified output on PR #8561:

```
Served URL:  http://localhost:8081/frontend_v1/js/campaign-wizard.js
Served SHA:  aba17d2ac4a255c32cc29fe5f0abd78b07d9d1dad1706d0353ca8b4ef7b72e11
Source SHA:  aba17d2ac4a255c32cc29fe5f0abd78b07d9d1dad1706d0353ca8b4ef7b72e11
```

## Forbidden reply shapes (this pitfall class)

- **"I started a fresh Flask server"** without naming `local.sh` — leaves the cache-busted-frontend question open. Trigger for the user to ask "did you run local.sh?"
- **"8139 is frontend-only so the Flask server alone is enough"** — true on the React v2 axis (local.sh line 867 explicitly says React v2 is removed), but misses the cache-busted-frontend and standard-env-vars axes.
- **"served campaign-wizard.js contains 15 occurrences of `isMobileViewport|...`"** — proves the right code IS in the bundle, NOT that the served bundle IS the right code. Cache could serve a stale equal-content file.
- **"the server is on port 8081"** without showing the SHA match.

## Verified recovery recipe (what I did after the audit catch)

1. Killed the v1 standalone server: `pkill -f "mvp_site.main serve"`; `kill -9` stragglers; verified `lsof -nP -iTCP:8081 -sTCP:LISTEN` is empty.
2. Ran `bash local.sh --no-log-stream --force-default-port` (background process). It built `venv/`, pip-installed deps, wrote cache-busted frontend to `/tmp/wa-8139-clean/fix_pr8139-clean-replay/`, set env vars, validated health checks.
3. Computed byte-identity: SHA of served JS matched source SHA exactly (`aba17d2a...`).
4. Re-ran the Playwright capture script against the `local.sh` server. Same metrics as v1 (`indicatorVisible=True→False, scrollTop=0→337, windowScrollY=0`).
5. Re-rendered the captioned MP4 — caption now reads "PR #8561 | 8b2e65ac11 | 390x844 mobile viewport | local.sh server".
6. Backed up v1 evidence to `evidence/v1-standalone-server/` for diff.
7. Pushed v2 to the public gist (new SHA).
8. Re-uploaded v2 as new Slack attachments + posted a v2 summary explaining the deviation.
9. Updated PR #8561 description to explicitly state `bash local.sh` + the served-SHA match.
10. Posted a v2 PR comment with the byte-identity proof.

## Decision matrix — when each launcher is correct

| Situation | Correct launcher | Why |
|---|---|---|
| User asks for `/es` or "BEFORE/AFTER screenshot" against a `$GITHUB_REPOSITORY` PR | `bash local.sh --no-log-stream --force-default-port` | Canonical harness expectation. Cache-busted frontend + standard env vars. |
| Debugging a backend crash where you want a fresh stack trace | `python -m mvp_site.main serve` is acceptable | You're inspecting the crash, not producing harness-grade evidence. |
| Smoke-testing that the app still imports | `python -c "from mvp_site.main import create_app; create_app()"` | You don't need a server, you need import success. |
| Deploying to a real environment | `gcloud run services update ...` | Production deploy, not local evidence. |
| User explicitly says "just `python -m ... serve`, I don't need full local.sh" | `python -m mvp_site.main serve` | Explicit override; document the deviation in PR body anyway. |

## Verified output (PR #8561)

`local.sh` log (`/tmp/wa-8139-localsh.log`):

```
ℹ️ Server configuration loaded: Flask:8081, React:3002
[INFO] Virtual environment not found at $HOME/.worktrees/worldarchitect/wa-8139-clean/venv
[INFO] Creating virtual environment...
[INFO] Using python interpreter for venv: python3.12
[SUCCESS] Virtual environment created successfully
[INFO] Upgrading pip...
[INFO] Installing mvp_site requirements...
🔍 Validating server on port 8081...
Attempt 1/3: Testing http://127.0.0.1:8081/
✅ Server is responding correctly!
🚀 Server URL: http://127.0.0.1:8081/
🎯 Testing API connectivity...
✅ API endpoint responding correctly (authentication required)
✅ Health checks completed successfully!
ℹ️ Server URLs:
   - Flask Backend:  http://localhost:8081 (Serves V1 Frontend)
   - React Frontend: DISABLED (V2)
   - MCP Server:     http://localhost:8001 (Production mode)
```

PID file `flask_backend.pid` exists at `/tmp/wa-8139-clean/fix_pr8139-clean-replay/`. Cache-bust dir was created and populated.

## Related / companion lessons

- **`finish-the-job` skill changelog 1.7.3** — "UI change with `add X to settings and prove it works` → claimed X is in the dropdown but no captioned screenshot/video is attached" — same class of failure (proof-without-evidence), different surface.
- **`finish-the-job` skill changelog 1.7.6** — "Push a PR body edit and wait for the gates to re-evaluate without verifying the validator locally first" — same audit-first instinct: verify the proof matches reality BEFORE posting the claim.
- **`proof-before-claim`** (SOUL.md) — same root principle applied to local evidence: don't claim "fresh Flask server" without naming the launcher; don't claim "the served JS is the right code" without SHA proof.
