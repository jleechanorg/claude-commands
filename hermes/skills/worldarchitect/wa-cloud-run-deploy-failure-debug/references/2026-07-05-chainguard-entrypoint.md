# Reference — 2026-07-05 Chainguard ENTRYPOINT silent dev deploy failure

This is the canonical evidence file for the ENTRYPOINT/CMD incompatibility failure mode in this skill. Future agents should treat this as the canonical pattern, not as a one-off bug.

**READ BOTH THIS FILE AND `references/2026-07-06-entrypoint-override-mandatory.md` TOGETHER.** The v1 fix documented in this file was incomplete; PR #8182 documents the corrected v2 form. Skipping the second file means you'll reproduce the v1 trap.

## Timeline

| UTC | Event |
|-----|-------|
| 2026-07-02 13:34 PT | Commit `4a8500a860210bd5916d822b0cf25ba2b4e4c91b` lands on main: `[security] swap mvp_site Dockerfile base to Chainguard python:latest-dev`. **No test gate verifies container runtime behavior after the swap.** |
| 2026-07-04 23:58 | `Auto-Deploy Dev` workflow for `fix/restore-git-exec-perms-directory-tests` merge: build OK, deploy FAIL. Nobody investigates Cloud Run revision logs. |
| 2026-07-05 00:04 | Production `mvp-site-app-stable-00168-m4t` last deployed — **2026-06-28**, BEFORE the Chainguard swap. Production still runs `python:3.11-slim`. No user-visible impact. |
| 2026-07-05 22:21 | PR #8176 `[antig] feat(beads): canonicalize .beads/issues.jsonl` merged. Auto-deploy fires. Build OK. Deploy FAIL with `can't open file '/app/$PROJECT_ROOT/gunicorn'`. |
| 2026-07-05 22:40 | Send-deploy-notification action sends email `❌ FAILED: dev Deployment - mvp-site-app-dev` to Jeffrey. |
| 2026-07-05 23:29 | Jeffrey posts "Investigate and fix" in Slack thread `C0AH3RY3DK6/p1783294201.582369`. |
| 2026-07-05 23:39 | Hermes (this session) opens PR #8180 `fix(deploy): invoke gunicorn via python -m so Chainguard image entrypoint does not crash` — the **v1 fix**. |
| 2026-07-05 23:41 | Slack status reply posted to thread with root cause + fix + proof + `MERGE APPROVED` request. |
| 2026-07-06 00:00ish | Jeffrey replies "Merge approved*". |
| 2026-07-06 00:22 | PR #8180 squashed and merged into main (`1b32e6b2`). Auto-Deploy Dev fires. Image built and pushed as `sha256:46f36ebf...`. New revision `mvp-site-app-dev-03647-68m` created at 00:26Z. **But the revision fails startup TCP probe** — see the v2 addendum. |
| 2026-07-06 00:30 | Hermes inspects the new failing revision's logs via `gcloud logging read`, sees the second-stage `can't open file '/app/$PROJECT_ROOT/python'`, opens PR #8182 with the **v2 fix** (`ENTRYPOINT []` added). |

**Total silent failure window: still ongoing as of 2026-07-06 00:30 UTC** until PR #8182 lands. v1 fix closed the gunicorn-can't-be-opened symptom but introduced the python-can't-be-opened symptom; the v2 fix closes both.

## The two commands that diagnosed the v0 failure

### 1. Pull the failing revision's startup logs (NOT the build log)

```bash
gcloud logging read \
  'resource.type=cloud_run_revision
   AND resource.labels.service_name=mvp-site-app-dev
   AND resource.labels.revision_name=mvp-site-app-dev-03646-k8w' \
  --project=worldarchitecture-ai \
  --limit=100 --format=json --freshness=24h
```

Critical log entries from `mvp-site-app-dev-03646-k8w`:

```
[2026-07-05T22:42:06.298992Z] /usr/bin/python: can't open file
                              '/app/$PROJECT_ROOT/gunicorn':
                              [Errno 2] No such file or directory
[2026-07-05T22:42:07.258004470Z] WARNING: Container called exit(2).
[2026-07-05T22:42:07.429592Z] ERROR: Default STARTUP TCP probe failed
                              1 time consecutively for container
                              "mvp-site-app-1" on port 8080.
                              The instance was not started.
                              Connection failed with status CANCELLED.
```

The loop repeats every ~5s for the full 4-minute Cloud Run startup probe window. ~50 probe failures per revision. Operator-visible signal: the email; absent the email, nothing.

### 2. Confirm the base-image swap

```bash
git log --oneline -10 -- $PROJECT_ROOT/Dockerfile
# 4a8500a860 [security] swap mvp_site Dockerfile base to Chainguard python:latest-dev
# e49d7fbb14 fix(prompts): show both dice on advantage/disadvantage narration (#7539)

git show 4a8500a860 --stat
# $PROJECT_ROOT/Dockerfile  | 26 ++++++++---
# ...security-scan-results/...
```

The commit message explicitly says "Build proof: `docker build ...` succeeded locally in 1m45s, final image 2.24GB." — but **a successful `docker build` does not exercise the CMD**. The CMD was never run before the merge.

## Why the failure stayed invisible

| Layer | Signal | Actual state |
|-------|--------|--------------|
| `gcloud builds submit` | exit 0 | Image built ✅ |
| `Auto-Deploy Dev` gcloud step | exit 1 | Deploy failed ❌ |
| GHA workflow status | red on the `deploy / deploy` job | Operator-visible failure ✅ |
| Slack mrkdwn status | not configured | No alert ❌ |
| `gh pr checks` (PR #8176) | bead-jsonl-sort ✅, all other gates ✅ | PR looks green ✅ |
| Cloud Run revision startup | 50× probe failures, then auto-rollback | Operationally broken ❌ |
| Operator review | "deploy said ok-ish, build was green" | Net: nothing wrong, file PR #8175 instead ❌ |
| Production | still serving from old `python:3.11-slim` revision | User impact: ZERO ❌ |

**The misdirection:** the PR's check suite gates are bead-jsonl-sort, linting, type-checking, directory tests — they all pass. The Cloud Run revision startup is a separate operational surface that the existing CI does not probe. The dev deployment workflow's red status was drowned by the green PR status.

## Why production was never affected (yet)

```bash
gcloud run revisions describe mvp-site-app-stable-00168-m4t \
  --region=us-central1 --project=worldarchitecture-ai --format=json
# Image: gcr.io/worldarchitecture-ai/mvp-site-app@sha256:0b84e88a...
# Deploy time: 2026-06-28T09:23:21Z
```

The 2026-06-28 stable revision pre-dates the Chainguard swap (2026-07-02). Production's been frozen on `python:3.11-slim` and only refreshes when a stable deploy runs. The next stable deploy would have hit users — but no stable deploys ran during the 4-day window.

## The v1 fix (in PR #8180) — INCOMPLETE

```diff
# $PROJECT_ROOT/Dockerfile, line 73
-CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
+CMD ["python", "-m", "gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
```

**Correction (2026-07-06):** This fix was insufficient. After PR #8180 merged and an auto-deploy fired on the merge commit `1b32e6b2`, the new revision `mvp-site-app-dev-03647-68m` failed with a different symptom: `/usr/bin/python: can't open file '/app/$PROJECT_ROOT/python'`. The reason: Docker still prepends the inherited Chainguard `ENTRYPOINT=["python"]` to the exec-form CMD, so `CMD ["python", "-m", ...]` runs as `python python -m ...`, and Python tries to open `python` (the first arg after the entrypoint-injected `python`) as a script.

The **v2 fix** (PR #8182) is:

```diff
 # $PROJECT_ROOT/Dockerfile
+ENTRYPOINT []
 CMD ["python", "-m", "gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
```

The companion reference `references/2026-07-06-entrypoint-override-mandatory.md` documents the second-stage trap in full.

## Verification (local smoke test, real-server `/es`)

The same `python -m gunicorn ...` invocation was used to verify both v1 and v2 — both local smoke tests pass, because local venv doesn't use Docker's entrypoint wrapping. This is one reason the v1 fix was missed locally: only the post-merge Cloud Run revision log catches it.

```bash
cd mvp_site
python -m gunicorn -c gunicorn.conf.py main:create_app() \
  --bind 127.0.0.1:8093 --workers 1 --preload
```

```
[2026-07-05 16:39:44 -0700] [51447] [INFO] Starting gunicorn 23.0.0
[2026-07-05 16:39:44 -0700] [51447] [INFO] Listening at: http://127.0.0.1:8093
$ curl http://127.0.0.1:8093/
HTTP 200, body=23764 bytes
$ curl http://127.0.0.1:8093/health
HTTP 200, body={"mcp_client":{"initialized":false},"service":"worldarchitect-ai","status":"healthy","timestamp":"2026-07-05T23:39:44.106043+00:00"}
```

`--preload` is **macOS-only** (local). On Cloud Run (Linux) `gthread` workers do not see the objc fork-thread-safety crash, so production uses `gunicorn.conf.py` defaults unchanged.

Full evidence log committed to PR branch at `evidence/gunicorn_es_evidence.log` for v1 and `evidence/gunicorn_es_evidence_v2.log` for v2.

## What this session still owed after the v1 merge

This session shipped the v1 PR, merged it on `MERGE APPROVED`, then detected the v1 insufficiency via Phase 1 revision-log inspection and shipped v2 (PR #8182). It did NOT:

- Land v2 (still awaiting `MERGE APPROVED` for #8182).
- Verify the v2 merged form actually serves traffic in Cloud Run (will be verified on the next push to main post-merge).
- Add a CI gate that probes the new revision's `/health` after deploy and fails the workflow if it doesn't return 200 within 30s (proposed follow-up in PR #8180 body).
- Add a post-deploy smoke-test step (proposed follow-up in PR #8180 body).
- Add a CI step that diffs `latestReadyRevisionName` vs `latestCreatedRevisionName` after deploy and fails the workflow if they're not equal — would have caught v1's silent runtime break. (Pitfall 7 in the parent SKILL.md captures this.)

Any future agent debugging a recurrence should:
1. Check whether the proposed follow-ups landed (PR template, deploy-dev.yml, worldarchitect repo).
2. If not, open a new bead with provenance to this reference (per `beads-cli.mdc` proactive bead-creation rule).
3. Read `references/2026-07-06-entrypoint-override-mandatory.md` FIRST — it documents the second-stage trap that the v1 fix fell into.

## Cross-references for future agents

- **PR #8180** — v1 fix attempt; MERGED at `1b32e6b2`, REVISION FAILS at runtime (see v2 below).
- **PR #8182** — v2 fix (adds `ENTRYPOINT []`); OPEN, MERGEABLE.
- **PR #8176** — the original triggering merge (`fix(beads): canonicalize .beads/issues.jsonl`).
- **Commit `4a8500a860`** — the Chainguard swap that introduced the bug.
- **Slack thread `C0AH3RY3DK6/p1783294201.582369`** — the originating "Investigate and fix" request and the live v1→v2 discussion.
- **gcloud run deploy run id `28757055505`** — the first concrete failing `Auto-Deploy Dev` run after the swap.
- **Cloud Run revisions to inspect**:
  - `mvp-site-app-dev-03646-k8w` — the v0 failing revision (can't open gunicorn).
  - `mvp-site-app-dev-03647-68m` — the v1-still-failing revision (can't open python). The proof that v1 was insufficient; found via this skill's Phase 1 Step 2 protocol.
- **`references/2026-07-06-entrypoint-override-mandatory.md`** — the v2 addendum (full trap documentation).
