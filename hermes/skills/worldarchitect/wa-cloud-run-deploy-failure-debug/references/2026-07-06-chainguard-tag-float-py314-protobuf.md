# Chainguard `:latest-dev` Tag Float — Python 3.14 Breaks Protobuf

**Date:** 2026-07-06
**PRs:** [#8136](https://github.com/$GITHUB_REPOSITORY/pull/8136) (Chainguard swap, merged 2026-07-02), [#8187](https://github.com/$GITHUB_REPOSITORY/pull/8187) (revert to python:3.11-slim)
**Affected:** ALL PR deploy-preview workflows from 2026-07-02 to 2026-07-06

## Root Cause

PR #8136 swapped `$PROJECT_ROOT/Dockerfile` `FROM python:3.11-slim` to `FROM cgr.dev/chainguard/python:latest-dev`. The Chainguard free tier publishes only `:latest` and `:latest-dev` tags — no pinned 3.x version tags. The `:latest-dev` tag silently floated from Python 3.11 to **Python 3.14** sometime between 2026-07-02 and 2026-07-06.

## Failure Mechanism

1. Docker build succeeds (pip installs fine, image pushes to GCR).
2. Cloud Run creates a new revision from the image.
3. Container starts, gunicorn boots, imports `firebase_admin` → `google.cloud.firestore` → `google.protobuf.descriptor_pb2`.
4. Protobuf's C-extension (`google._upb._message`) is incompatible with Python 3.14's metaclass changes.
5. Container crashes with `TypeError: Metaclasses with custom tp_new are not supported.` before binding PORT=8080.
6. Cloud Run STARTUP TCP probe fails → `Deployment failed`.

## Cloud Run Revision Log Evidence

```
Default STARTUP TCP probe failed 1 time consecutively for container "mvp-site-app-s1-1" on port 8080.
TypeError: Metaclasses with custom tp_new are not supported.
Container called exit(1).
  File "/usr/lib/python3.14/importlib/__init__.py", line 88, in import_module
  File "google/protobuf/internal/api_implementation.py", line 41, in _CanImport
  File "google/protobuf/descriptor.py", line 17, in <module>
  File "google/protobuf/descriptor_pb2.py", line 6, in <module>
```

Note the `/usr/lib/python3.14/` path — confirms Chainguard `:latest-dev` shipped Python 3.14, not 3.11.

## gcloud logging query used

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="mvp-site-app-s1" AND timestamp>="2026-07-06T07:12:00Z" AND timestamp<="2026-07-06T07:13:00Z"' \
  --project=worldarchitecture-ai --limit=20 --format="value(textPayload)"
```

## The Fix

**Revert to `python:3.11-slim`** — the stable, well-tested base that matches CI and local dev. This also drops ALL Chainguard-specific workarounds from PRs #8180/#8182:
- `USER root/nonroot` switching (python:3.11-slim runs as root by default)
- `--chown=nonroot:nonroot` on COPY commands (not needed for root user)
- `ENTRYPOINT []` override (python:3.11-slim has no python entrypoint injection)
- `python -m gunicorn` invocation (direct `gunicorn` CMD works on standard base)

## Why not pin Chainguard to a digest?

Chainguard's free tier publishes `:latest` and `:latest-dev` only — no `:3.11` or `:3.12` tags. You CAN pin via digest (`FROM cgr.dev/chainguard/python@sha256:...`), but:
1. The digest must be manually maintained (pull + update on every base bump).
2. The Chainguard team rotates digests for security patches, breaking old pins.
3. `python:3.11-slim` is maintained by Docker Hub with stable `3.11` tags — no float risk.

For a production Cloud Run service, `python:3.11-slim` is the safer choice until Chainguard publishes stable version tags.

## How this relates to modes 1a/1b

The ENTRYPOINT fixes from PRs #8180/#8182 were CORRECT for the ENTRYPOINT problem but MOOT once the base image floated to Python 3.14 — the container never got far enough to hit the ENTRYPOINT issue because protobuf crashed first. This is Pitfall 9 in action: each fix layer reveals the next failure, and a base-image float can invalidate all per-layer fixes simultaneously.

## Affected PRs (systemic)

| PR | deploy-preview status | Notes |
|----|----------------------|-------|
| [#8186](https://github.com/$GITHUB_REPOSITORY/pull/8186) | ❌ fail → ✅ pass after fix | Original PR Jeffrey asked about |
| [#8185](https://github.com/$GITHUB_REPOSITORY/pull/8185) | ❌ fail | Same root cause |
| [#8182](https://github.com/$GITHUB_REPOSITORY/pull/8182) | ❌ fail (merged, but deploy was broken) | Merged before float detected |
| [#8177](https://github.com/$GITHUB_REPOSITORY/pull/8177) | ✅ pass | Lucky timing — deployed before tag float |