---
name: wa-cloud-run-deploy-failure-debug
description: "Diagnose silent Cloud Run deployment failures for YourProject (and any python-based Cloud Run service). Trigger when the Auto-Deploy Dev workflow shows a red deploy step, when a dev Deployment Failed email arrives, when a new revision is created but receives 0% traffic, when health checks never pass, when gcloud run services describe reports a NotReady revision, or when the user reports 'prod is fine but dev is broken'. Encodes the systematic-debugging Phase 1 discipline applied to deploy pipelines (the visible CI/build signal is a false green — the real failure surfaces in Cloud Run revision startup logs, not in workflow status). Covers the full Chainguard-python-ENTRYPOINT failure family — broken in two distinct ways: a bare CMD gunicorn AND CMD [python -m gunicorn]. Both need an ENTRYPOINT override. v2.0.0 (2026-07-06) adds the v1 to v2 patch lesson plus the /advice re-review requirement when a PR's fix surface evolves after advisory approval."
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [worldarchitect, deploy, cloud-run, devops, gcp, debugging]
    related_skills: [systematic-debugging, drive-pr-to-green, always-pr-never-local-edit, evidence-standards, advice]
---

# WA Cloud Run Deploy Failure Debug

## When to use this skill

Load first when ANY of these fire in the `$GITHUB_REPOSITORY` repo (or any python-on-Cloud-Run project with a similar shape):

- **Email: "❌ FAILED: dev Deployment - mvp-site-app-dev"** sent via the `send-deploy-notification` action (`dawidd6/action-send-mail`).
- **Auto-Deploy Dev workflow** (or any Cloud Run deploy workflow) shows a red gcloud step with output like:
  ```
  ERROR: (gcloud.run.deploy) The user-provided container failed to start
  and listen on the port defined provided by the PORT=8080 environment variable
  within the allocated timeout.
  ```
- **New Cloud Run revision** shows `Ready=False` and `0% traffic` in `gcloud run services describe <service>`.
- **`gh pr checks` shows the deploy step failed** but earlier steps (build, push) passed.
- **User reports "the deploy says it succeeded but the service is broken"** — the visible green hides the real failure.

## The Iron Law of Cloud Run deploy debugging

```
THE BUILD/IMAGE IS NOT THE DEPLOY.
THE REVISION STARTUP LOGS ARE.
```

`gcloud builds submit` exiting 0 only proves the image built and pushed. Cloud Run then pulls that image, creates a NEW revision, runs its `CMD`, and starts probing TCP port 8080 — ANY of those four steps can fail independently of the build. The `Auto-Deploy` workflow only checks the gcloud exit code; a deployment that quietly rolls back the failed revision still counts as "Auto-Deploy Dev ✅" on the commit. Operators reading PR status see green and stop. The failure ships to production quietly the next time someone redeploys from this base.

## Six failure modes (ordered by observed frequency)

| # | Failure | Symptom in revision logs | First-place fix |
|---|---------|--------------------------|----------------|
| 1a | **`CMD ["gunicorn", ...]` against ENTRYPOINT=python (e.g. Chainguard)** | `/usr/bin/python: can't open file '/app/your_app/gunicorn': [Errno 2]` | `ENTRYPOINT []` + `CMD ["python", "-m", "gunicorn", ...]` |
| 1b | **`CMD ["python", "-m", ...]` against ENTRYPOINT=python (the v1 fix trap)** | `/usr/bin/python: can't open file '/app/your_app/python': [Errno 2]` | Same: `ENTRYPOINT []` is mandatory to drop the inherited python prefix |
| 2 | **Container exits fast / uncaught exception in `main:create_app()`** | `Container called exit(2)` followed by repeated STARTUP TCP probe failures | Run `python -c "from main import create_app; create_app()"` locally against the same venv |
| 3 | **Health check timeout** | `Default STARTUP TCP probe failed 1 time consecutively` looping for 4+ minutes | Reduce warmup time or extend Cloud Run `--timeout`/`--startup-probe-timeout` |
| 4 | **OOM during init** | `Worker (pid:NNN) was sent SIGKILL! Perhaps out of memory?` | Reduce `--memory` per-instance, or ship a smaller embed cache |
| 5 | **Missing env var / secret** | Container exits before listening; stderr shows `KeyError: ...` or `Missing required env var` | Diff the env-var contract in `deploy.sh` (`ENV_VARS=...`) against what the app actually reads |
| 6 | **Python 3.14 + protobuf C-extension incompatibility** (Chainguard `:latest-dev` ships 3.14) | `TypeError: Metaclasses with custom tp_new are not supported.` in `google._upb._message` during `firebase_admin` → `google.cloud.firestore` import chain | Pin `protobuf>=5.27.0` in `requirements.txt`, OR use `python:3.11-slim`/`python:3.12-slim` base instead of Chainguard `:latest-dev` |

**Mode 1a and 1b are the SAME root cause broken in two distinct ways.** A bare `CMD ["gunicorn", ...]` fails immediately because Docker prepends `python` and tries to open `gunicorn` as a file. The "obvious" fix — `CMD ["python", "-m", "gunicorn", ...]` — ALSO fails because Docker still prepends the inherited `python` entrypoint, giving `python python -m gunicorn ...`, and Python tries to open the first arg `python` as a script file. The only correct fix is `ENTRYPOINT [] + CMD ["python", "-m", ...]`. See `references/2026-07-06-entrypoint-override-mandatory.md`.

## The Phase 1 loop (run these in order; don't skip)

### Step 1 — Find the failing revision name

```bash
gh api "repos/$GITHUB_REPOSITORY/actions/runs/<RUN_ID>/jobs" \
  --jq '.jobs[] | select(.conclusion=="failure") | "\(.name) | \(.id)"'
# Note: <RUN_ID> = the `Auto-Deploy Dev` run from the email body or
#   gh run list --workflow="Auto-Deploy Dev" --limit=1
```

The failing job's log URL is in the email and `gh run view <id> --web`.

### Step 2 — Pull the revision logs (not the build logs)

```bash
gcloud logging read \
  'resource.type=cloud_run_revision
   AND resource.labels.service_name=mvp-site-app-dev
   AND timestamp>="<30 min before failure>Z"
   AND timestamp<="<30 min after failure>Z"' \
  --project=worldarchitecture-ai \
  --limit=100 \
  --format=json
```

The build log (in `deploy / deploy` job output) shows the IMAGE BUILD succeeded. The REVISION LOGS (in Cloud Logging, queried above) show the actual container start failure. **Most operators stop at the build log. Don't.**

Filter the JSON for: `can't open`, `ModuleNotFoundError`, `ImportError`, `KeyError`, `SIGKILL`, `exit(2)`, `Traceback`, `ERROR:`.

### Step 3 — Sanity-check "what does the current prod run?"

```bash
gcloud run services describe mvp-site-app-stable \
  --region=us-central1 --project=worldarchitecture-ai --format=json
```

If prod was last deployed BEFORE the breaking change, prod still runs the old image and is not the regression source — dev failed only because it recently redeployed from the same base. This is what happened 2026-07-05: prod's revision was 2026-06-28, base swap was 2026-07-02, dev failed every push since.

### Step 4 — Find the Dockerfile base + diff the base change

```bash
git log --oneline -10 -- your_app/Dockerfile
# Then read the commit that last touched your_app/Dockerfile
git show <SHA> --stat
```

Look for `FROM ... python ...` line. Chainguard's `:latest-dev` has `ENTRYPOINT=["python"]` (verified). `python:3.11-slim` does NOT have any ENTRYPOINT.

### Step 5 — Verify the fix locally

```bash
# Reproduce the EXACT CMD the Dockerfile ships:
docker build -t wa-debug -f your_app/Dockerfile .
docker run --rm -p 8093:8080 -e PORT=8080 -e TESTING_AUTH_BYPASS=true wa-debug

# OR without docker (works in the repo venv):
cd mvp_site && python -m gunicorn -c gunicorn.conf.py main:create_app() \
  --bind 127.0.0.1:8093 --workers 1 --preload
# Then:
curl http://127.0.0.1:8093/health
# Expected: HTTP 200, body JSON {"status":"healthy","service":"worldarchitect-ai",...}
```

**The macOS fork+objc gotcha:** `--preload` is local-mac-only. Production Linux / Cloud Run doesn't see the `objc[pid]: +[NSMutableString initialize] may have been in progress in another thread when fork()` crash; the production `gunicorn.conf.py` defaults (`gthread`, no `--preload`) are unchanged. Use `--preload` for the smoke test ONLY on macOS; document the reason in the PR.

## The Phase 2 fix recipe (for ENTRYPOINT/CMD mismatches)

**Container CMD before (broken):**
```dockerfile
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
```

**Container CMD after (correct, against ENTRYPOINT=python base):**
```dockerfile
ENTRYPOINT []
CMD ["python", "-m", "gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
```

**Why `ENTRYPOINT []` AND not just `CMD ["python", "-m", ...]`:**

Docker's exec form runs `<ENTRYPOINT> <CMD-as-args>`. If the parent image sets `ENTRYPOINT=["python"]` (Chainguard `cgr.dev/chainguard/python:latest-dev` does), then:

| Dockerfile | What runs in container | Result |
|---|---|---|
| `CMD ["gunicorn", ...]` | `python /app/your_app/gunicorn` | `can't open file '/app/your_app/gunicorn'` |
| `CMD ["python", "-m", "gunicorn", ...]` | `python python -m gunicorn ...` | `can't open file '/app/your_app/python'` (the first arg is interpreted as a script, not as `-m`'s module) |
| `ENTRYPOINT []` + `CMD ["python", "-m", ...]` | `python -m gunicorn ...` | ✅ gunicorn module found via Python's import system, listens on PORT=8080 |

The "obvious" fix in the row 2 — `CMD ["python", "-m", ...]` without ENTRYPOINT override — DOES NOT WORK. This was the trap that PR #8180 (this session's first attempt) fell into. The advisor who reviewed v1 missed the ENTRYPOINT detail. Only the Phase 1 revision-log inspection AFTER merge revealed the same-family failure with a different `can't open file` path. Always set `ENTRYPOINT []` first, THEN exec-form CMD.

**Why this works in the third row:** `ENTRYPOINT []` clears the inherited entrypoint, so the exec-form CMD runs as written. `python -m gunicorn` resolves the module via Python's import system — no `$PATH` lookup, no `/app/your_app/<tool>` file interpretation. Portable across `python:3.11-slim` (no ENTRYPOINT — the `[]` is a no-op there), Chainguard, distroless, and any future base.

**Shell form as alternative (NOT preferred):** `CMD python -m gunicorn ...` (no JSON list) also works because shell-form CMD bypasses the ENTRYPOINT wrap. But shell form loses PID 1 signal handling that some bases rely on. Stick with `ENTRYPOINT [] + CMD ["exec-form", ...]`.

**Generalize:** Any time a Dockerfile `CMD` references a tool, ask "what ENTRYPOINT does the parent image set?" If the answer is "python" (Chainguard, many minimal bases), BOTH `CMD ["tool", ...]` AND `CMD ["python", "-m", ...]` break — only `ENTRYPOINT []` + `CMD ["python", "-m", ...]` survives. The fix surface is one line longer than the obvious fix. Don't stop at the obvious fix; ship the override.

## Pitfalls — DO NOT do these

1. **Don't trust "gcloud builds submit exit 0" as deploy success.** The image built, but the revision may still fail to start. Always pull the Cloud Run revision logs.
2. **Don't compare revisions to a previous deployment's logs** if the Docker base changed between then and now — the ENTRYPOINT may have changed too.
3. **Don't assume "it works locally" means "it works in Cloud Run".** The reverse is also true: a local failure that's macOS-specific (objc fork) does NOT mean Cloud Run will fail. Pin down the actual root cause in the revision logs, then test the FIX not the build.
4. **Don't silently merge the fix.** Per the your-project.com repo rule (`~/.cursor/rules/pr-hyperlink.mdc` + `MERGE APPROVED` gate), always open a PR and wait for explicit `MERGE APPROVED` before merging. The user reviews.
5. **Don't bundle "while I'm here" refactors into the deploy-fix PR.** Per `simplify-code` and `requesting-code-review` skills, the PR must be one logical change — the Dockerfile CMD. No formatting-only edits, no opportunistic test additions, no doc-string rewrites. Pure root-cause fix.
6. **Don't ignore `evidence/gunicorn_es_evidence.log`** if you produce a smoke-test log during Phase 1 — commit it to the PR branch so the failure → fix → proof chain is auditable. Evidence Staleness Tolerance (`~/.claude/skills/evidence-standards`) applies, but a 60-line gunicorn log for a Dockerfile CMD fix is permanent evidence.
7. **Don't ship `CMD ["python", "-m", ...]` as the ENTRYPOINT-mismatch fix.** The "obvious" fix breaks because Docker still prepends the inherited `python` entrypoint, giving `python python -m gunicorn ...` and the same `can't open file` family of errors with `python` instead of `gunicorn` in the path. ONLY `ENTRYPOINT [] + CMD ["python", "-m", ...]` works against an ENTRYPOINT=python base. This is the #1 reason the v1 fix in this session's PR #8180 had to be followed by a v2 fix in PR #8182.
8. **Don't accept an `/advice` approval from the start of a PR as binding once the PR's fix surface has evolved.** When a follow-up commit changes the actual change-set materially (different Dockerfile lines, different config keys, different module), the original review's reasoning may no longer match what's being merged. This session: `/advice` returned "Approve and merge as-is, confidence high" against v1, and v2 turned out to be insufficient for the same root cause — the reviewer's "Verify Chainguard python base has ENTRYPOINT=python" claim was correct but the "use python -m gunicorn instead" recommendation was incomplete. Re-run advisory review on the actual FINAL form of the fix before merging, especially when two+ approaches were considered and one was rejected post-review. See the related `advice` skill.
9. **Don't assume fixing one failure layer exhausts the root cause.** A single base-image swap (e.g. `python:3.11-slim` → `cgr.dev/chainguard/python:latest-dev`) can introduce MULTIPLE independent failure layers that only surface sequentially as you fix each one: (Layer 1) ENTRYPOINT mismatch → `can't open file '/app/.../gunicorn'`, (Layer 2) ENTRYPOINT mismatch with `python -m` → `can't open file '/app/.../python'`, (Layer 3) Python 3.14 + protobuf metaclass → `TypeError: Metaclasses with custom tp_new are not supported.` Each layer masks the next — you can't see Layer 3 until Layers 1+2 are fixed because gunicorn never boots far enough to import `firebase_admin`. After fixing the visible failure, re-pull the revision logs for the NEW revision deployed from your fix and check for the next layer. Don't claim "fixed" until `latestReadyRevisionName == latestCreatedRevisionName` AND `/health` returns 200 from the new revision.
10. **Don't assume `Auto-Deploy Dev` actually deployed just because a run was created.** The workflow uses `concurrency: cancel-in-progress: ${{ github.event_name != 'release' }}` — rapid successive pushes to main cancel earlier deploy runs before the `deploy` job (reusable workflow call) starts. A cancelled run shows only `smoke-tests (skipped)` in its job list and has 0 log lines. To actually deploy after a merge, trigger manually: `gh workflow run deploy-dev.yml --repo $GITHUB_REPOSITORY --ref main`, then watch with `gh run list --workflow=deploy-dev.yml --limit=1`.

## Verification before claiming "fixed"

| Gate | How to verify | Block if red |
|------|---------------|--------------|
| Local smoke test | `curl http://127.0.0.1:8093/health` returns 200 with the JSON body | Don't push |
| Docker build (if you have docker) | `docker build -t wa-debug -f your_app/Dockerfile .` finishes successfully | Fix Dockerfile before pushing |
| PR CI passes | `gh pr checks <N>` all green (or at least no relevant-to-this-PR failures) | Don't merge |
| **Cloud Run revision actually serving** | `gcloud run revisions list --service=<name>` shows the new SHA as `latestReadyRevisionName` (not just `latestCreatedRevisionName`); `gcloud run services describe <name>` shows 100% traffic on it | Don't close the bead — re-investigate (see Pitfall 7) |
| Post-merge: next dev deploy succeeds | Watch `gh run list --workflow="Auto-Deploy Dev" --limit=1` after the next push | Don't close the bead |

The fourth row is new and is the one that caught this skill's first version. `latestCreatedRevisionName` ≠ `latestReadyRevisionName`. The created-but-not-ready state is exactly what happens when the v1 fix shipped but the v1-only change still failed the startup probe.

## Cross-references

- `references/2026-07-05-chainguard-entrypoint.md` — full session evidence: failing revision `mvp-site-app-dev-03646-k8w`, gcloud logging query, PR #8180, the silent 4-day outage pattern. **(Note: this reference documents the v1 fix. The v1 fix was incomplete — see the addendum below. Read both files together for the complete story.)**
- `references/2026-07-06-entrypoint-override-mandatory.md` — the v1→v2 patch lesson: `CMD ["python", "-m", ...]` is NOT sufficient when the base image sets `ENTRYPOINT=["python"]`. Documents the failing revision from PR #8180's merge (`mvp-site-app-dev-03647-68m`), the second-stage `can't open file '/app/your_app/python'` error, and the canonical fix `ENTRYPOINT [] + CMD ["python", "-m", ...]`. **MUST READ** before advising anyone on a Chainguard ENTRYPOINT/CMD fix.
- `~/.claude/skills/systematic-debugging/SKILL.md` — the umbrella Phase 1 protocol this skill is a domain-specific instance of.
- `~/.hermes/skills/skills/workflow/drive-pr-to-green/SKILL.md` — for driving the resulting PR through to merge.
- `~/.claude/skills/evidence-standards/SKILL.md` — for `/es` evidence requirements and Staleness Tolerance.
- `~/.claude/skills/advice/SKILL.md` — the `/advice` second-opinion slash skill; relevant here because advisor approval was scoped to the v1 fix surface, not to the eventual v2 (Pitfall 8 captures the lesson).
- `~/.cursor/rules/pr-hyperlink.mdc` — for the PR-hyperlink rule when reporting status to the user.
- The repo's `CLAUDE.md` "Merge safety" section — for the `MERGE APPROVED` gate on your-project.com PRs.

## One-line summary

**The build log lies. The revision log tells the truth. Pull the Cloud Run `cloud_run_revision` resource logs for the failing revision, find the actual container-startup error, fix that, smoke-test locally, then open a PR — don't merge without `MERGE APPROVED`.**
