# Reference — 2026-07-06 ENTRYPOINT override mandatory (v1→v2 patch)

This is the canonical evidence file for the **second-stage** trap in the Chainguard python ENTRYPOINT family of Cloud Run failures. Treat as a sibling to `references/2026-07-05-chainguard-entrypoint.md` — both are required reading for any future agent debugging a Dockerfile-CMD / ENTRYPOINT-mismatch symptom on a Python-on-Cloud-Run service.

## The two-line trap

A Dockerfile on a base image that sets `ENTRYPOINT=["python"]` (Chainguard `cgr.dev/chainguard/python:latest-dev` does) can produce **two different `can't open file` errors** depending on what the CMD looks like. The fix is the same for both, but the "obvious" fix only fixes the first and silently breaks the second.

| Dockerfile `CMD` | What runs in container | Symptom |
|---|---|---|
| `CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]` | `python /app/$PROJECT_ROOT/gunicorn` | `/usr/bin/python: can't open file '/app/$PROJECT_ROOT/gunicorn'` |
| `CMD ["python", "-m", "gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]` | `python python -m gunicorn ...` | `/usr/bin/python: can't open file '/app/$PROJECT_ROOT/python'` (first arg `python` is interpreted as a script, not `-m`'s module) |
| `ENTRYPOINT []` + `CMD ["python", "-m", "gunicorn", ...]` | `python -m gunicorn ...` | ✅ gunicorn module resolved via Python's import system |

The middle row is the trap. It LOOKS right: `python -m gunicorn` "resolves via Python's import system" — but Docker still prepends the inherited `python` ENTRYPOINT before the exec-form CMD, so `python` becomes the first positional arg to Python instead of `-m`, and Python tries to open a file named `python`.

## Timeline (this skill's v1→v2 evolution)

| UTC | Event |
|-----|-------|
| 2026-07-05 23:29 | Jeffrey posts "Investigate and fix" |
| 2026-07-05 23:39 | Hermes opens PR #8180 with the **v1 fix**: `CMD ["python", "-m", "gunicorn", ...]`. Local smoke test passes. `/advice` reviewer returns "Approve and merge as-is, confidence high" — does NOT catch the ENTRYPOINT detail. |
| 2026-07-06 00:22 | PR #8180 merged (after Jeffrey's `Merge approved*`). Main HEAD = `1b32e6b2`. |
| 2026-07-06 00:24 | `Auto-Deploy Dev` fires on the merge commit; new image tagged `1b32e6b2ab...`; new revision `mvp-site-app-dev-03647-68m` created. |
| 2026-07-06 00:27 | New revision fails startup TCP probe — but with the **second-stage error**: `/usr/bin/python: can't open file '/app/$PROJECT_ROOT/python'`. |
| 2026-07-06 00:30 | Hermes inspects the revision logs (per this skill's Phase 1 Step 2), discovers the v1 fix was insufficient, opens **PR #8182** with the **v2 fix**: `ENTRYPOINT []` + `CMD ["python", "-m", "gunicorn", ...]`. Local smoke test on the new form also passes. |

**Status as of 2026-07-06 00:30 UTC:** v1 merged into main but is broken at runtime. v2 PR #8182 open, MERGEABLE, awaiting `MERGE APPROVED`. Production `mvp-site-app-stable-00168-m4t` unaffected (still runs pre-Chainguard `python:3.11-slim`, deployed 2026-06-28).

## How to detect you've hit the second-stage error

Symptoms that distinguish v1's trap from the original failure:

1. **The base image sets an ENTRYPOINT** — verify with `docker inspect <image> --format '{{.Config.Entrypoint}}'` or by reading the base image's docs (Chainguard's published images all set `ENTRYPOINT=["python"]`).
2. **The error pattern is identical up to the last path component.** Both v0 and v1 produce `can't open file '/app/$PROJECT_ROOT/<token>'` where `<token>` is whatever CMD's first arg was (after prepending the inherited `python`). The path *changes* (`gunicorn` → `python`), the failure mode does not.
3. **Local `python -m gunicorn ...` works fine** but Cloud Run fails. Local venv doesn't use Docker's entrypoint wrapping, so the local path doesn't reproduce. The only way to surface this is via the actual revision logs in Cloud Run after deploy.

## The correct fix (the v2 form)

```dockerfile
# Validated against cgr.dev/chainguard/python:latest-dev (ENTRYPOINT=["python"])
# and equivalent minimal bases. Also a no-op against python:3.11-slim
# (no ENTRYPOINT to override), so it's portable.
ENTRYPOINT []
CMD ["python", "-m", "gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
```

`ENTRYPOINT []` is the canonical Docker idiom for "clear the inherited entrypoint." Per the Docker reference, `ENTRYPOINT` in exec form replaces the inherited value with an empty list, which makes the exec-form `CMD` run as written — no implicit `python` prefix, no implicit `/bin/sh -c` for the shell form.

## What the `/advice` review missed

The v1 advisor (delegate_task → MiniMax-M3) verified three claims:

1. Chainguard's python base image sets `ENTRYPOINT=["python"]` ✅
2. The fix `python -m gunicorn` is the canonical pattern recommended by Chainguard's own Flask+gunicorn migration guide ✅
3. `gunicorn==23.0.0` is in `$PROJECT_ROOT/requirements.txt` ✅

But the reviewer missed the implication of claim 1 for the CMD being exec-form. The Chainguard migration guide applies to shell-form invocations like `CMD gunicorn ...` or `ENTRYPOINT ["gunicorn"]`. The exec-form `CMD ["python", "-m", ...]` plus inherited `ENTRYPOINT=["python"]` is a different beast: Docker still prepends.

**Future `/advice` use case for this lesson:** when the `/advice` reviewer's approval is bound to a specific change-set, any post-approval material change to the change-set re-opens the review. Pitfall 8 in the parent skill captures this in operator form.

## Source artifacts for cross-reference

- **PR #8180** — v1 fix attempt (`CMD ["python", "-m", ...]` only); MERGED at `1b32e6b2`, REVISION FAILS at runtime.
- **PR #8182** — v2 fix (adds `ENTRYPOINT []`); OPEN, MERGEABLE @ `8b87472a8f` at the time of writing.
- **Failing revision from PR #8180 merge**: `mvp-site-app-dev-03647-68m` — `gcloud logging read 'resource.labels.revision_name=mvp-site-app-dev-03647-68m'` shows the second-stage `can't open file '/app/$PROJECT_ROOT/python'` symptom.
- **Original failing revision from PR #8176**: `mvp-site-app-dev-03646-k8w` — captures the v0 `can't open file '/app/$PROJECT_ROOT/gunicorn'` symptom (see `references/2026-07-05-chainguard-entrypoint.md`).
- **Slack thread** `C0AH3RY3DK6/p1783294201.582369` — originated "Investigate and fix" and contains the live session discussion.

## Future-agent checklist

Before you ship any "use python -m X" fix for a Cloud Run startup failure on a Chainguard (or any python-ENTRYPOINT) base image, walk this list:

1. `docker inspect <base> | jq .Config.Entrypoint` (or `gcr.io/<repo>/<image>:latest` revision history) — confirm or deny the inherited entrypoint.
2. If `ENTRYPOINT` is set, your fix MUST include `ENTRYPOINT []` (or explicit `ENTRYPOINT ["<your-runner>"]` that wraps everything). Don't rely on `CMD` alone.
3. Local smoke test with `python -m gunicorn ...` is necessary but NOT sufficient — only the Cloud Run revision log after deploy catches the inherited-entrypoint trap.
4. After merging, verify via `gcloud run services describe <service> --format='value(status.latestReadyRevisionName)'` — must equal `status.latestCreatedRevisionName` AND have `Ready=True`. If only `latestCreatedRevisionName` advanced and the new revision is `Ready=Unknown`, you hit the trap. Pull the revision logs and add `ENTRYPOINT []`.
