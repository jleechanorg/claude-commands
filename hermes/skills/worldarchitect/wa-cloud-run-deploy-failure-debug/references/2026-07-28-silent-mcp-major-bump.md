---
title: Silent major-version bump in an unbounded pip pin — pip resolves to a breaking major at image-build time and no gate catches it
verified-on: $GITHUB_REPOSITORY PR #8657 (band-aid) / $GITHUB_REPOSITORY issue 8657-thread / Slack C0BDEAJH8PK/p1785267392.104109
failure-class: Mode 9 (image-build-time dependency resolution regression — the build is green, the revision is Ready, but every worker crashes at boot)
---

## TL;DR

`mcp 2.0.0` released and silently removed `Server.list_tools` + `Server.call_tool` from the v1 API. `$PROJECT_ROOT/requirements.txt:35` pinned `mcp>=1.0.0` — NO upper bound. When the next image built for the dev deploy, `pip install -r requirements.txt` resolved to `mcp 2.0.0`. The image built fine, the revision was reported Ready, every smoke-test SKIPPED (the `concurrency: cancel-in-progress` killed the smoke-tests job before it ran), and the user only found out because `https://mvp-site-app-dev.../health` returned 503.

**The fatal chain:** (1) unbounded upper bound + (2) upstream major release + (3) tests don't see the new dep resolution + (4) build just produces a layer with the resolved deps + (5) Cloud Run reports Ready even when workers are in a death loop + (6) Green Gate has no smoke-test gate that runs AFTER revision is Ready. Every individual step is "fine"; the chain is not.

**End-state:** PR #8657 pinned `mcp<2.0.0` (band-aid). Dev returned to 200 once the rebuild shipped. Three follow-ups dispatched via `claude_minimax` (not AO) at 2026-07-28: PR #xxxx (the v2 port), PR #yyyy (the CI dep-resolution major-bump gate), PR #zzzz (the weekly dep-major-version audit cron). All three target the same bug class.

## Timeline (UTC, 2026-07-27 → 2026-07-28)

| Time | Event |
|---|---|
| 2026-07-27 evening PT | `mcp 2.0.0` released on PyPI (silently; `pip index versions mcp` would have shown it the next morning) |
| 2026-07-28 19:08 | PR #8504 (commit `3d231766643559b3b9b7b60c8b62265b34075fcb`) merged to `main` — changes $PROJECT_ROOT/prompts only, no requirement changes |
| 2026-07-28 19:21:34 | Auto-Deploy Dev run #30391590978 triggers from the main-branch push |
| 2026-07-28 19:24:54 | Composite action installs `fastembed numpy google-cloud-storage jsonschema pydantic cachetools flask` (precompute deps only — does NOT install `mcp`) |
| 2026-07-28 19:25:06 | `Successfully installed ... mcp-...` not in the install log — mcp is installed by the **Dockerfile build step** (later), not by the precompute composite action |
| 2026-07-28 19:30ish | `gcloud builds submit` succeeds (the image built). `mcp>=1.0.0` resolved to `mcp 2.0.0` at THIS step, baked into the image layer |
| 2026-07-28 19:31:45 | Deploy step exits failure: `gcloud run services describe` shows `latestReadyRevisionName=mvp-site-app-dev-04114-vkv` (so Cloud Run sees the new revision as Ready) — but every worker is in a death loop |
| 2026-07-28 19:31:45 | `smoke-tests` job SKIPPED (concurrency: cancel-in-progress) — no `/health` check verified on the new revision |
| 2026-07-28 19:31:45 | `Notify on failure` + `Send failure email` fire (`❌ FAILED: dev Deployment - mvp-site-app-dev`) |
| 2026-07-28 19:37ish | User reports "Seems like dev is down investigate it" in Slack `C0BDEAJH8PK` |
| 2026-07-28 19:37:46 | `curl https://mvp-site-app-dev.../health` → HTTP 503 ("Service Unavailable", 19 bytes) |
| 2026-07-28 19:37:46 | `gcloud run services describe mvp-site-app-dev` → `latestReadyRevisionName == latestCreatedRevisionName == mvp-site-app-dev-04114-vkv` (Ready=True, traffic 100%) — but the app is broken |
| 2026-07-28 19:38ish | `gcloud logging read ... severity>=ERROR` → recurring gunicorn worker death loop with `AttributeError: 'Server' object has no attribute 'list_tools'` at `$PROJECT_ROOT/mcp_api.py:69` |
| 2026-07-28 19:42ish | Local repro: `pip install 'mcp>=1.0.0'` → `mcp 2.0.0`; `hasattr(Server('x'), 'list_tools')` → `False` |
| 2026-07-28 19:44ish | Local repro: `pip install 'mcp==1.29.0'` → `hasattr(Server('x'), 'list_tools')` → `True` (confirmed the API still exists in 1.x) |
| 2026-07-28 19:46ish | `docker build -t wa-fix-mcp-pin -f $PROJECT_ROOT/Dockerfile .` succeeded with the pin |
| 2026-07-28 19:47:17 | `docker run ... /health` → HTTP 200; `pip show mcp` inside container → `1.29.0`; `grep -c AttributeError /tmp/wa_fix_mcp_pin.log` → 0 |
| 2026-07-28 19:54ish | Branch `fix/mcp-pin-below-v2` (off `origin/main` `1a2e3130ad`), committed `fb3d65d3b0` (one-line pin), pushed, PR #8657 opened |
| 2026-07-28 20:04:03 | User authorizes merge (`mergedBy.login == jleechan2015`); merge commit `7f9792420b69241084adee8d0c5c9589ec66e4b6` |
| 2026-07-28 20:36ish | Auto-Deploy Dev ships new revision `mvp-site-app-dev-04128-x25` (SHA `258075d765`); `curl /health` → HTTP 200; `mcp_client.initialized: true` |
| 2026-07-28 22:36 | Dev still healthy (verified) |

## Root cause (the diagnostic chain)

### Step 1 — Confirm the surface
Every gunicorn worker died at boot with the same traceback:
```
File "/app/$PROJECT_ROOT/main.py", line 165, in <module>
    from mvp_site.mcp_api import handle_jsonrpc
File "/app/$PROJECT_ROOT/mcp_api.py", line 69, in <module>
    @server.list_tools()
     ^^^^^^^^^^^^^^^^^
AttributeError: 'Server' object has no attribute 'list_tools'
```
This is NOT Mode 1-6 (none of the symptoms match — no `can't open`, no `SIGKILL`, no `OOM`, no env-var missing, no `protobuf` metaclass). It's NOT Mode 7 (the deploy step succeeded enough to create a revision; the script probe didn't fire). It's something new.

### Step 2 — Confirm the version
The container's `pip show mcp` returned `2.0.0`. The test environment's pip cache had `mcp 1.x` (it was cached from a previous build). The test suite ran against the old venv. The build step invoked `pip install -r requirements.txt` which resolved `mcp>=1.0.0` → `2.0.0` (the new latest). The image layer was built with mcp 2.0.0 baked in. The deployed container ran `mcp 2.0.0`.

### Step 3 — Confirm the API contract change
`mcp 2.0.0` removed `Server.list_tools` and `Server.call_tool`. The decorators `@server.list_tools()` and `@server.call_tool()` in `mcp_api.py` no longer exist in 2.0.0:
- Verified in a fresh venv: `pip install mcp==2.0.0 && python -c "from mcp.server import Server; print(hasattr(Server('x'), 'list_tools'))"` → `False`
- Verified the 1.x replacement: `pip install mcp==1.29.0 && python -c "from mcp.server import Server; print(hasattr(Server('x'), 'list_tools'))"` → `True`
- 4 v1 decorators are used in `$PROJECT_ROOT/mcp_api.py`: `list_tools` (line 69), `call_tool` (line 300), `list_resources` (line 536), `read_resource` (line 561). All four are gone in 2.0.0.

### Step 4 — Why no gate caught it
Walk the chain backwards:
1. **Test suite** ran against the test venv (cached `mcp 1.x`). Tests passed — but the tests don't import `mcp_api.py` at module level, so even if they had run against 2.0.0, the AttributeError wouldn't surface because `mcp_api.py` is only imported by `main.py`, not by the tests directly.
2. **pip install in the test step** — there isn't one for the production deps. The Dockerfile's `pip install -r requirements.txt` runs ONCE at image-build time, not at test time.
3. **Build step** — `gcloud builds submit` succeeded. Cloud Build just packages the resolved deps; it doesn't run the code.
4. **gcloud run deploy** — revision created, reported Ready. Cloud Run's "Ready" check is the container binding :8080 — which our container did (gunicorn master binds the port, then the workers die, then the master restarts them, then they die again, forever). The startup probe succeeded (TCP probe to :8080 succeeded) so Cloud Run marked the revision Ready and routed 100% traffic to it.
5. **smoke-tests** — SKIPPED. The `concurrency: cancel-in-progress` setting in the workflow killed the smoke-tests job before it ran (verified in the run timeline: `smoke-tests | skipped | 0 steps`). The smoke-tests job is supposed to be the gate that catches "ready but broken", but in this case it never ran.
6. **Green Gate** — passed. Green Gate runs `pytest`, which doesn't import `mcp_api.py` at module level.

### Step 5 — The Iron Law #3 statement
```
THE BUILD IS GREEN BUT THE APP IS BROKEN.
THE TRANSITIVE DEP RESOLVED TO A NEW MAJOR AT BUILD TIME.
NO GATE AT TEST TIME OR DEPLOY TIME FIRES.
```

This is the missing Iron Law. Iron Law #1: "the build log lies; the revision log tells the truth." Iron Law #2: "the pip install can succeed while the script probe fails." Iron Law #3: "the build is green; the resolved deps changed silently; the revision is Ready; the workers crash on first import."

## Why this is a NEW failure class (not just another Mode 7 sibling)

| Question | Mode 7 (PRECOMPUTE_FAILED) | Mode 9 (silent major bump) |
|---|---|---|
| Where does it fail? | `deploy.sh` step, before `gcloud run deploy` | AFTER `gcloud run deploy` — the revision IS Ready, AND traffic IS routed, AND the workers ARE dying |
| What's the symptom? | `PRECOMPUTE_FAILED` in step stdout; no new revision created | `503 Service Unavailable` from `/health`; revision logs show recurring gunicorn worker death loop |
| Why didn't the test suite catch it? | N/A (it was at the deploy step) | Tests ran against a cached venv with the OLD major; the build resolved the NEW major at image-build time |
| Why didn't the build step catch it? | N/A (build succeeded) | Build just packages the resolved deps; it doesn't run the code |
| Why didn't Cloud Run's Ready check catch it? | N/A (no revision was created) | TCP-probe to `:8080` succeeded because gunicorn master binds the port before workers die |
| Why didn't Green Gate's smoke-tests catch it? | N/A (smoke-tests were for the deploy step, not the revision) | `concurrency: cancel-in-progress` SKIPPED the smoke-tests job |
| First-place fix | Composite-action env-export contract (PR #8380) | (1) Pin to a fixed major for code that uses old API, (2) Add CI gate that fails PR on transitive major-version bump, (3) Weekly audit cron |

## Verification recipe (the Step 5.5 adaptation for Mode 9)

The standard Step 5.5 ("is the deploy actually live despite the failure?") WORKS for Mode 9 — but the answer is the OPPOSITE of the Mode 7 case. For Mode 9, the live revision IS the broken one:

```bash
# 1. Confirm the live revision did deploy (vs. failed pre-deploy)
gcloud run services describe mvp-site-app-dev \
  --region=us-central1 --project=worldarchitecture-ai \
  --format='value(status.latestReadyRevisionName, status.latestCreatedRevisionName, metadata.labels.commit-sha-full)'

# 2. Probe /health — expect 503 if Mode 9 is active
curl -sS -o /tmp/h.txt -w "HTTP=%{http_code} TIME=%{time_total}\n" \
  --max-time 30 "https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/health"

# 3. Confirm worker death loop in revision logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=mvp-site-app-dev AND severity>=ERROR AND timestamp>"<30 min ago>"' \
  --project=worldarchitecture-ai --limit=100 --format='value(timestamp,severity,textPayload)' \
  | grep -E "Worker (pid:|exited)|AttributeError|Reason: Worker failed"

# 4. Determine the failing package version
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=mvp-site-app-dev AND timestamp>"<30 min ago>"' \
  --project=worldarchitecture-ai --limit=200 --format='value(timestamp,severity,textPayload)' \
  | grep -iE "Successfully installed|Requirement already satisfied" | tail -20
# Look for the package versions that the IMAGE built with — these are the resolved transitive deps

# 5. Local repro recipe (the load-bearing diagnostic)
python3 -m venv /tmp/mode9-repro
/tmp/mode9-repro/bin/pip install --quiet 'mcp>=1.0.0'  # unbounded, matches the broken pin
/tmp/mode9-repro/bin/pip show mcp | head -3             # if Version: 2.0.0, you've reproduced the upstream major
/tmp/mode9-repro/bin/python -c "from mcp.server import Server; s=Server('x'); print('list_tools:', hasattr(s, 'list_tools'))"  # if False, the API is gone
# Now pin and re-test:
/tmp/mode9-repro/bin/pip install --quiet 'mcp==1.29.0'
/tmp/mode9-repro/bin/python -c "from mcp.server import Server; s=Server('x'); print('list_tools:', hasattr(s, 'list_tools'))"  # should be True
```

If the unbounded-pin resolves to a major that broke the API, you've found the bug class. The fix is one of three: pin to a known-good major, port the code to the new major, or add a CI gate that catches it at PR time.

## Local-rebuild / `/es` evidence recipe (for the PR that fixes Mode 9)

```bash
# 1. Branch from origin/main (this is mandatory — see .cursor/rules/pr-branch-from-main.mdc)
git worktree add -b fix/<short-name> .worktrees/<short-name> origin/main
cd .worktrees/<short-name>

# 2. Apply the fix (in this case: pin)
# Edit $PROJECT_ROOT/requirements.txt to add the upper bound

# 3. Build the image locally — Cloud Run literally builds the same Dockerfile
docker build -t wa-mode9-fix -f $PROJECT_ROOT/Dockerfile .

# 4. Run the container with the same env vars as Cloud Run
docker run --rm -p 8094:8080 -e PORT=8080 -e TESTING_AUTH_BYPASS=true \
  --name wa-mode9-fix --memory 2g --cpus 2 wa-mode9-fix:latest > /tmp/wa_mode9.log 2>&1 &
DOCKER_PID=$!

# 5. Wait for container to bind, then probe
sleep 18
for i in 1 2 3 4 5 6 7 8; do
  out=$(curl -sS -o /tmp/wa_mode9_h.txt -w "HTTP=%{http_code}" --max-time 30 "http://127.0.0.1:8094/health" 2>&1)
  echo "try $i: $out"
  if echo "$out" | grep -q "HTTP=2"; then break; fi
  sleep 4
done
cat /tmp/wa_mode9_h.txt

# 6. Confirm the resolved version inside the container
docker run --rm wa-mode9-fix:latest pip show mcp | head -3
# Expected: Version: <pinned version, e.g. 1.29.0>

# 7. Confirm zero of the failure-class signature in the boot log
grep -c "AttributeError" /tmp/wa_mode9.log
# Expected: 0 (vs. 1 per worker on the broken image)

# 8. Confirm gunicorn master spun up a single worker, no death loop
grep -c "Booting worker" /tmp/wa_mode9.log
# Expected: 1 (vs. infinite restarts on the broken image)

# 9. Save the log to the worktree's evidence/ directory (will be gitignored)
mkdir -p evidence && cp /tmp/wa_mode9.log evidence/local_boot_after_pin.log

# 10. Stop the container
docker kill wa-mode9-fix 2>/dev/null || kill $DOCKER_PID 2>/dev/null
```

This is the `/es` evidence recipe for `$PROJECT_ROOT/` production changes. The PR body MUST link the self-contained bundle (the log file in `evidence/`), raw command output, and the post-build `pip show` result.

## The three-leg prevention chain (the durable fix)

The PR #8657 band-aid is the right immediate fix. The three legs of prevention are:

1. **Pin to a known-good major** (PR #8657) — smallest fix. Required for code that hasn't been ported yet. Ages out; needs follow-up.
2. **Port the code to the new major** (PR #xxxx — claudem-minimax dispatched) — proper fix. Drops the pin. Has its own scope (4 decorators + tests).
3. **CI gate that fails PR on transitive major-version jump** (PR #yyyy — claudem-minimax dispatched) — catches the next instance at PR time. The cheapest durable prevention.
4. **Weekly dep-major-version audit cron** (PR #zzzz — claudem-minimax dispatched) — catches the case when no PR is in flight and the upstream major drops silently. Posts to `#ai-general` only when there's an actionable bump.

The three are complementary. Leg 3 alone would catch the next instance at PR time, but the operator might miss the Slack ping if they're not actively reading PRs. Leg 4 alone would catch the drift weekly, but only if someone refactors the pin to drop the upper bound. Legs 1+2 are the immediate fix + the proper migration. Legs 3+4 are the durable prevention.

## Common pitfalls when investigating Mode 9

### Don't trust `gcloud run services describe` showing `Ready=True`
For Mode 9, `latestReadyRevisionName == latestCreatedRevisionName` AND the revision IS Ready. But the app inside is broken. The "Ready" check is a TCP probe to the container's port — it doesn't run the code. Always ALSO probe `/health` from the live URL.

### Don't trust "Green Gate passed"
For Mode 9, Green Gate ran and passed. The tests didn't import `mvp_site.mcp_api` at module level — the AttributeError only fires when `main.py` imports `mcp_api.py` at boot. The test suite is not a substitute for a real boot-time smoke test.

### Don't trust "build succeeded"
For Mode 9, `gcloud builds submit` succeeded. The build just packages the resolved deps; it doesn't run the code. The `mcp 2.0.0` was baked into the image layer and only surfaced when gunicorn forked the workers.

### Don't assume the prod image is also broken
For Mode 9, prod is fine because the prod image was built before `mcp 2.0.0` released. The new image only ships on the next deploy. Always check `gcloud run services describe mvp-site-app-stable` and probe its `/health` to confirm the failure is scoped to dev (or not).

### Don't propose a fix without local repro
The fix is `mcp<2.0.0`, but the EVIDENCE is the local venv probe: `pip install 'mcp>=1.0.0' → 2.0.0; hasattr(Server('x'), 'list_tools') → False`. Without that probe, "the fix is to pin" is a guess. With the probe, it's a verified case.

### Don't ship the PR body with file paths or commit SHAs that get shell-substituted
The first draft of PR #8657's body had backticks interpreted by the shell as command substitution, eating `mcp-site-app-dev` and `2.0.0` from the visible text. Use `gh pr edit --body-file <path>` with a heredoc to a write_file'd file, NOT inline backticks. Verified 2026-07-28 — the regenerated body was clean.

### Don't skip the smoke-tests job because "Concurrency: cancel-in-progress" did it
The smoke-tests job is the gate that catches "Ready but broken". Skipping it (via concurrency cancellation) is a bug in the workflow configuration, not a feature. The fix is to make smoke-tests non-cancellable, OR to add a deploy-preview check that runs OUTSIDE the concurrency group.

## Why this should be a new Iron Law (not just another pitfall)

This is structurally different from any pitfall in the current SKILL.md. The pitfall section describes "things you might do wrong when fixing the failure"; the Iron Law describes "the failure mode the operator has to recognize". Mode 9 IS a new failure mode — the diagnostic question is different, the verification recipe is different, the user-facing answer is different. The other Modes answer "what went wrong with the container". Mode 9 answers "what went wrong with the dep — the container is fine, the code is fine, the deps just silently changed".

## Related to other failures in this codebase

- Mode 7 (PR #8380) — composite action installs deps, deploy script can't find them. Different surface (deploy step vs. runtime), same archetype (silent dep-resolution failure).
- Mode 6 (Python 3.14 + protobuf metaclass) — base image changed (Chainguard → python:3.11-slim), compatibility broken. Different surface (base image vs. transitive dep), same archetype (silent upstream change breaking the build).
- The `pip-review` / `pip-check-outdated` / `dependabot` family of tools — all designed to catch this kind of drift, but none of them integrated into the PR check workflow. The weekly audit cron (PR #zzzz) is the in-house equivalent.

## PR + reference links

- Band-aid fix: [PR #8657](https://github.com/$GITHUB_REPOSITORY/pull/8657) (`fix/mcp-pin-below-v2`, commit `fb3d65d3b0` → merge `7f9792420b`)
- v2 port (proper fix): PR #xxxx (claudem-minimax dispatched, branch `feat/port-mcp-api-to-v2`)
- CI gate (PR-time prevention): PR #yyyy (claudem-minimax dispatched, branch `feat/dep-resolution-major-bump-gate`)
- Weekly audit cron (drift detection): PR #zzzz (claudem-minimax dispatched, branch `chore/dep-major-version-weekly-audit`)
- Originating Auto-Deploy Dev run: [#30391590978](https://github.com/$GITHUB_REPOSITORY/actions/runs/30391590978)
- Originating bot failure email: `Your Project Deploy Bot <$USER@gmail.com>` at 2026-07-28 12:31 PT, subject `❌ FAILED: dev Deployment - mvp-site-app-dev`
- Slack thread: `C0BDEAJH8PK/p1785267392.104109`
- Local boot log (post-pin, 121 lines): `/tmp/wa_fix_mcp_pin.log` (also in worktree at `evidence/local_boot_after_pin.log`, gitignored)
- Production verify: `mvp-site-app-stable` revision `mvp-site-app-stable-00176-jhs` (SHA `4bde5a8527573912c1dfaf162b1ef0c0d91f9940`) — unaffected, 200 OK
