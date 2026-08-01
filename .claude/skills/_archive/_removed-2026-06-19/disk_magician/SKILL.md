---
name: disk-magician-claude
description: Run disk usage diagnostics, growth history logs, and automated cache/temp cleanup on development machines.
metadata:
  type: skill
  runtime: claude
---

# Disk Magician — Claude Skill

This skill teaches Claude how to use `disk_magician` to audit disk space, identify growth regressions, and perform cleanups.

## Skill Integration & Commands

* **Snapshot Validation (Phase 0)**: Check the coverage and timeouts of the snapshot file located in your backup repository:
  ```bash
  ./disk_magician.sh audit --dry-run
  ```
  Check the output to make sure coverage is >= 70% and there are no warnings.
* **Scan / Discover (Phase 1)**: Scan for directories > 5 GB not currently in the monitored configuration:
  ```bash
  ./disk_magician.sh discover
  ```
* **Audit Candidates (Phase 2)**: View cleanup candidates and regressions:
  ```bash
  ./disk_magician.sh audit
  ```
* **Safe Cleanup (Phase 3)**: Execute safe cache and temp cleanups (which deletes stale temporary PR clones, dev caches, and orphaned worktrees):
  ```bash
  ./disk_magician.sh clean
  ```
* **Destructive Cleanup (Phase 4)**: Interactively clear Docker VM disk images, Colima VMs, and old agent session folders:
  ```bash
  ./disk_magician.sh clean-all
  ```

## Safety Constraints & Guardrails
- **Mtime Caution:** Worktrees and agent sessions with modification time < 14 days require explicit `WORKTREE APPROVED` confirmation from the user before deletion.
- **Never-delete list:** Do not delete `~/.codex/sessions`, `~/.codex/sessions_archive/`, `~/.codex/state*.sqlite`, `~/.codex/log`, or `~/.claude/projects` directly. Always run cleanups through `disk_magician.sh` to ensure safety filters are respected.
