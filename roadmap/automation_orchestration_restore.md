# Restore orchestrated Claude automation for PR fixing
Status: ✅ COMPLETED

## Goal
- ✅ Reinstate cron-friendly PR automation that uses the orchestration system and Claude agents to run `/fixpr` or `/copilot` in isolated workspaces under `/tmp/{repo}/{branch}`.

## Approach
- ✅ Add a batch runner that:
  - Discovers recent PRs (last 24h) across `jleechanorg`.
  - Ensures a clean base clone per repo under `/tmp/pr-orch-bases/{repo}`.
  - Spawns orchestration agents with worktrees at `/tmp/{repo}/{branch}` to run `/fixpr` then `/copilot` on the PR branch.
  - Uses TaskDispatcher/tmux sessions for execution and reuses the Claude CLI profile.
- ✅ Wire a cron entry to invoke the runner on a cadence (default 15 minutes) and log to `$HOME/Library/Logs/worldarchitect-automation/orchestrated_pr_runner.log`.
- ✅ Validation pass (smoke/dry-run) and monitoring instructions.

## Risks / mitigations
- **Worktree collisions**: remove stale `/tmp/{repo}/{branch}` before agent creation.
- **Repo drift**: hard reset the base clone to `origin/main` per run.
- **Capacity**: limit processed PRs per run (configurable flag).
- **Permissions**: rely on existing GH auth and Claude CLI; exit early with clear errors if missing.
