# Deploy-failure investigation pitfalls (added 2026-07-05, c71322b / 1c9b9c0)

This reference covers the **investigation side** of "FAILED dev deploy" alerts. The push-side fix (Chainguard ENTRYPOINT ↔ CMD conflict) is the original content below.

---

## Investigation-side pitfalls

When a `FAILED: dev Deployment - <svc>` email arrives, the **commit named in the email subject is usually NOT the commit that actually failed**. Three concrete pitfalls observed on 2026-07-05.

### Pitfall 1 — the email is tagged with the push-event commit, not the build-time commit

The deploy workflow (`Auto-Deploy Dev` / `deploy-dev.yml` in `$GITHUB_REPOSITORY`) is triggered by a push to `main`, but it then runs `gcloud builds submit` against the current `main` HEAD at build time. By the time the workflow's build step actually executes, other PRs may have merged and `main` HEAD may have advanced several commits past the push event.

**Symptom (verified 2026-07-04→05, commits c71322b → 1c9b9c0):** An email arrived tagged `Branch: main | Commit: c71322b1d1c2…` ("docs: post-8005 cache tracker cleanup"). That commit only touched 3 `roadmap/*.md` files — it could not possibly break a container. The actual deployed-and-failed commit was `1c9b9c0ec9` ("[agento] feat(exportcommands): include ~/.hermes/skills"), 4 commits later.

**Recipe — verify the email commit matches the actual failed revision (3 commands, ~5 sec):**

```bash
# 1. List recent revisions with commit-sha-full + Ready condition
gcloud run revisions list --service=<svc> \
  --region=<region> --project=<project> --format=json --limit=10 \
  | jq -r '.[] | "\(.metadata.name)\t\(.metadata.labels."commit-sha-full" // "?")\t\([.status.conditions[] | select(.type=="Ready") | .status] | join(","))"'

# 2. Find the revision with Ready=False — its commit-sha-full is the real culprit
# 3. Compare to the commit in the email. If they differ, the email is a red herring.
```

If they differ, the email-triggering commit is a **red herring** — investigate the `latestCreatedRevisionName` (failed, has the actual broken commit) and verify the service is still serving traffic via `latestReadyRevisionName`.

### Pitfall 2 — the service is likely still UP

Cloud Run's revision lifecycle decouples "new revision created" from "new revision serving traffic." A failed revision never receives traffic; the *previous* `latestReadyRevisionName` keeps serving the previous commit.

**Recipe — confirm service health before panicking:**

```bash
# 1. What's currently serving?
gcloud run services describe <svc> --region=<region> --project=<project> \
  --format="value(status.latestReadyRevisionName,status.url)"

# 2. Is the URL responding?
curl -s -o /dev/null -w "HTTP %{http_code} | %{time_total}s\n" --max-time 10 <service-url>

# 3. What's the currently-serving commit?
gcloud run revisions describe <latest-ready-revision> \
  --region=<region> --project=<project> \
  --format="value(metadata.labels.commit-sha-full)"
```

A 200 on the service URL with `latestReadyRevisionName` ≠ `latestCreatedRevisionName` means the failure is **recoverable-from-HEAD-revert**, not user-impacting. The fix is to repair the Dockerfile (or the offending commit) and re-deploy — users are not affected in the meantime.

### Pitfall 3 — the build SHA ≠ the revision SHA ≠ the commit SHA

A single commit can produce multiple revisions (Cloud Run auto-creates revisions on each deploy; revisions are immutable). Three distinct identifiers to keep straight:

| Identifier | Format | Source |
|---|---|---|
| Image SHA (digest) | `sha256:8c6fd60a...` | `gcr.io/<proj>/<svc>@sha256:...` |
| Image tag | `dev-<short-sha>` | `gcr.io/<proj>/<svc>:dev-c71322b` |
| Revision name | `<svc>-NNNNN-xxx` | `mvp-site-app-dev-03642-ww4` |
| Source commit | 40-char hex | `gh api repos/<owner>/<repo>/commits/<sha>` |
| Revision label | `commit-sha-full` | `gcloud run revisions describe <rev>` |

**Recipe — match revision to image to commit:**

```bash
# 1. Get the failed revision's image SHA
gcloud run revisions describe <failed-revision> \
  --region=<region> --project=<project> \
  --format="value(spec.containers[0].image)"

# 2. Resolve image SHA -> source commit via gcb-build-id label
gcloud run revisions describe <failed-revision> \
  --region=<region> --project=<project> \
  --format="value(metadata.labels.gcb-build-id)"

# 3. Look up the build's source SHA
gcloud builds describe <gcb-build-id> --project=<project> \
  --format="value(source.repoSource.commitSha)"
```

That commit SHA is the one to investigate — *not* the one in the email. Cross-reference with `gh api repos/<owner>/<repo>/compare/<prev-commit>...<this-commit>` to see what changed.

### Anti-pattern: stopping at "the email says commit X failed, investigate X"

This was the actual first-reaction failure on 2026-07-05. The email subject's commit (`c71322b`, a docs-only PR) cannot possibly have broken a container; treating it as the investigation target would have sent the agent on a 30-minute wild goose chase through `roadmap/*.md` files. The 30-second `gcloud run revisions list` revealed `1c9b9c0` as the real culprit in 3 commands.

**Rule of thumb**: any time a `FAILED` deploy alert arrives, run the 3-command recipe above *before* reading the offending commit's diff. If the email commit ≠ the failed revision's commit, the email is a notification of the *triggering push*, not the failing code.

---

## Chainguard Python ENTRYPOINT — debug recipe for "deploy-preview fail: container won't start" (original content, added 2026-07-04, PR #8139)

**Symptom** (Cloud Run revision / deploy-preview job FAIL):
```
ERROR: (gcloud.run.deploy) The user-provided container failed to start and listen on the port
defined by the PORT=8080 environment variable within the allocated timeout.
Default STARTUP TCP probe failed 1 time consecutively for container "<svc>-1" on port 8080.
The instance was not started.
Connection failed with status CANCELLED.
Container called exit(2).
/usr/bin/python: can't open file '/app/<subdir>/gunicorn': [Errno 2] No such file or directory
```

The final line is the smoking gun: **the container runtime executed `python gunicorn …`**, which means `/usr/bin/python` was prepended to the Dockerfile `CMD`. Python then tried to interpret `gunicorn` as a script — and failed.

**Root cause** — Chainguard's hardened Python base image (`cgr.dev/chainguard/python:latest-dev`) sets:
```dockerfile
ENTRYPOINT ["/usr/bin/python"]
```

But when the project's `CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]` lands at container start, the runtime prepends ENTRYPOINT → final exec = `/usr/bin/python gunicorn -c …`. Python interprets `gunicorn` as a script filename to open. Since WORKDIR is `/app/<subdir>` and there is no `gunicorn` file there, the container exits 2 immediately and Cloud Run's health probe times out.

This is the opposite of `python:3.11-slim` (which has empty ENTRYPOINT and a CMD-only shell-style execution).

**Same-shape check — pull the image locally and inspect (authenticated via gcloud):**
```bash
gcloud auth configure-docker --quiet
docker pull gcr.io/<project>/<svc>:<sha>
docker inspect <image> --format '{{json .Config.Entrypoint}} | {{json .Config.Cmd}}'
# expected fault: Entrypoint ["/usr/bin/python"], Cmd ["gunicorn", ...]
```

Without local pull access (artifact registry auth often blocks), get the same info from the runtime Cloud Run logs:
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="<svc>"' \
  --project <project> --limit=10 --format=json
```
Look for the line `/usr/bin/python: can't open file '/app/...': [Errno 2]`.

**Same-name rule check** (per `qa-test-failure-dismissal-anti-pattern`): does any other PR against the same base branch show the same `deploy-preview` fail? If yes for ALL PRs that touch main, the root cause is in main, not in the PR you're driving.

**Why this is a deployment-prevention problem, not a workflow problem:**
- The PR under test typically does NOT touch the Dockerfile or the base image.
- The base-image swap (e.g. PR #8136 in this repo) shipped a Dockerfile change that itself merged with `deploy-preview=fail`. Every PR that lands after that picks up the same broken startup sequence.
- Per the `qa-test-failure-dismissal-anti-pattern` skill, treat this as **global infra**, NOT as a PR-specific blocker, when verifying with the same-name rule.

**Three fix paths (ranked by effort/risk):**

1. **Use exec form with absolute path** so ENTRYPOINT python is bypassed:
   ```dockerfile
   CMD ["/usr/local/bin/gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
   ```
   Caveat: Chainguard `:latest-dev` includes gunicorn only if the project's `requirements.txt` installs it. Verify the binary is at `/usr/local/bin/gunicorn` inside the image before fixing in this direction.

2. **Override ENTRYPOINT in the project's Dockerfile** to clear Chainguard's default:
   ```dockerfile
   ENTRYPOINT []
   CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
   ```
   This is cleaner — restores the `python:3.11-slim` semantics without changing the base image. Cheapest fix to ship.

3. **Pin a different base image** that doesn't override ENTRYPOINT, e.g. `python:3.11-slim` (the previous base) — but that gives up the CVE-reduction benefit the Chainguard swap was supposed to deliver.

**Decision rule for the gateway / drive-pr-to-green session**: do NOT patch the Dockerfile on the PR being driven, because that's scope-creep outside the user's actual change. Surface the root cause, cite the upstream PR (#8136 in this repo's case), list the three fix options as one of the final-reply options. The human picks the path; the agent does not edit Dockerfile mid-drive unless told.

---

## Reference (this investigation)

- Email ts 2026-07-05T00:07:14Z for `mvp-site-app-dev`, tagged commit `c71322b1d1c2…`
- Real failed revision: `mvp-site-app-dev-03642-ww4` (Ready=False, HealthCheckContainerError)
- Real failed commit: `1c9b9c0ec990348bf2ee40e2c7788966df9d41e5` (PR #8135)
- Real broken code path: PR #8136's Dockerfile (merged between `c71322b` and `1c9b9c0`)
- Service stayed healthy on `mvp-site-app-dev-03641-xhj` (commit `c71322b`) throughout
- 4 commits between trigger and failure: `cd29cb6`, `1c9b9c0`, `82b50f0`, `cfe9ad8`, `26f08d5` — the Chainguard base swap (`82b50f0` = PR #8136) is the source
- PR #8139 (the next driven PR after #8135) hit the same failure on every push until the Dockerfile gets fixed