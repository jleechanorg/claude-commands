---
name: self-hosted-runner-preflight
description: Pre-flight checklist for self-hosted runner failures. Use when investigating low disk, missing runner, or stuck Green Gate on the $GITHUB_REPOSITORY fleet. Always verifies host-level container state, not just GitHub API.
---

# Self-Hosted Runner Pre-Flight

## When to use this skill
- User says "runner is offline", "runner missing", "CI failed low_disk_space", "Green Gate stuck"
- `gh api orgs/jleechanorg/actions/runners` shows fewer than 22 runners
- A workflow run has been "in_progress" on Green Gate >30 minutes

## The 5-questions pre-flight (MANDATORY before any fix)

For each failure class, answer BEFORE proposing a fix:

1. **What does GitHub say?**
   `gh api orgs/jleechanorg/actions/runners?per_page=100 --jq '.runners[] | {name,status,busy}'`
2. **What does the host actually have?**
   - mac: `docker ps --format "{{.Names}}\t{{.Status}}" | grep org-runner-mac-`
   - jeff-ubuntu: `ssh jeff-ubuntu "DOCKER_HOST=unix:///home/$USER/.lima/colima/sock/docker.sock docker ps --format '{{.Names}}\t{{.Status}}' | grep org-runner-"`
3. **What does the disk look like inside the container?**
   `docker exec <name> df -Pk /` — needs >=1GB free for preflight to pass.
4. **Is the runner in restart loop?**
   - `docker ps -a --format "{{.Names}}\t{{.Status}}" | grep Restarting`
   - If yes, check logs: `docker logs --tail 30 <name>` for 403/registration errors.
5. **Is Green Gate stuck?**
   Check the run step "Check smoke gate (gate 8)" — if IN_PROGRESS >30min with no smoke runs on the branch, see Class C re-dispatch.

## Failure-class fixes

### Class A: low_disk_space (>=1 runner has <1GB free inside container)
- ROOT FIX: edit `self-hosted-oss/pre-job-hook.sh` to add disk cleanup (fires on EVERY job, not periodic).
- Pattern:
  ```bash
  AVAIL_KB="$(df -Pk "${RUNNER_WORKDIR}" 2>/dev/null | awk 'NR==2 {print $4}')"
  if [[ "$AVAIL_KB" -lt "$DISK_MIN_KB" ]]; then
    rm -rf /root/.cache/pip
    rm -rf "${RUNNER_WORKDIR}/<repo>"
  fi
  ```
- Set `DISK_MIN_KB=5242880` (5GB, 5x the preflight threshold).
- Belt-and-suspenders: add a periodic launchd script (`mac-runner-disk-cleanup.sh` style).
- Deploy: `bash self-hosted-oss/install.sh` syncs to `~/.local/share/worldarchitect-runners/pre-job-hook.sh` (bind-mounted live — no restart needed).
- VERIFY: `docker exec <runner> bash -c 'pgrep Runner.Worker'` returns empty (idle), then `df -Pk /` shows >=5GB.

### Class B: missing runner (compose defines N but only N-1 containers exist)
- mac (ARM64): `RUNNER_COUNT=<N> bash ~/.local/share/worldarchitect-runners/start-runner.sh start`
- jeff-ubuntu (X64):
  `ssh jeff-ubuntu "cd ~/projects/worktree_runner/self-hosted-colima && DOCKER_HOST=unix:///home/$USER/.lima/colima/sock/docker.sock docker compose up -d runner-<N>"`
- Then verify: `docker ps | grep runner-<N>` and `gh api orgs/jleechanorg/actions/runners --jq '.runners[].name' | grep runner-<N>`

### Class C: Green Gate stuck on gate 8 (smoke)
- Compare `SKEPTIC_GATE_TRIGGER` SHA pinned in PR comments to `gh pr view <N> --json headRefOid`.
- If mismatched, re-dispatch in order:
  ```bash
  gh workflow run "MCP Smoke Tests" --ref <branch> -f pr_number=<N>
  gh workflow run "Skeptic Self-Verify" --ref <branch> -f pr_number=<N>
  gh workflow run green-gate.yml --ref <branch> -f pr_number=<N> -f head_sha=<sha>
  ```
- All 3 require `pr_number`; green-gate.yml ALSO requires `head_sha`.

### Class D: token returns 403 from inside container
- Confirm token length: `docker exec <name> bash -c 'echo ${#ACCESS_TOKEN}'` (should be ~40).
- Test directly:
  `docker exec <name> curl -X POST -H "Authorization: token $ACCESS_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/orgs/jleechanorg/actions/runners/registration-token`
- 201 → token fine, timing issue (config.sh ran before API ready), re-run start-runner.
- 401/403 → token bad/expired, rotate `gh auth token` and re-deploy.

## Anti-patterns
- Trusting GitHub UI as ground truth for runner health.
- Proposing "schedule a cron to clean up" as the primary fix (use per-job hook).
- Re-dispatching Green Gate without first dispatching smoke (gate 8 polls forever).
- Restarting the container while a job is running (always check `pgrep Runner.Worker` first).
- Editing the runtime mirror directly (`~/.local/share/worldarchitect-runners/`) — edit `self-hosted-oss/`, then `bash install.sh` to sync.
