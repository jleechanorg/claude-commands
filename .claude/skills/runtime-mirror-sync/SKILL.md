---
name: runtime-mirror-sync
description: Why ~/.local/share/worldarchitect-runners/ is a runtime mirror, not the source — and how to sync changes correctly.
type: reference
---

# Runtime Mirror Sync

`launchd` runs scripts out of `~/.local/share/worldarchitect-runners/`. That
directory is a **runtime mirror** populated by
`self-hosted-oss/install.sh`'s `RUNTIME_SCRIPTS` array from
`self-hosted-oss/*.sh` in this repo.

## Why this matters

Editing the mirror directly is the "I edited the wrong file" anti-pattern.
It is silently clobbered on the next `install.sh` run, and other Macs never
see the change. The fix never propagates; the bug "magically comes back" on
reboot or on a teammate's machine.

## Enforcement

A user-scope PreToolUse hook
(`~/.claude/hooks/block-runtime-mirror-edits.sh`, Edit|Write|MultiEdit
matcher) blocks direct Edit/Write on
`~/.local/share/worldarchitect-runners/*.sh` and emits a diagnostic pointing
to the correct path. The hook deliberately allows:

- Edit/Write on `self-hosted-oss/*.sh` (any worktree)
- Edit/Write on `.jsonl` / `.log` / `.bak` / `.swp` in the mirror (state files)
- Bash `cp` / `rsync` to the mirror (the explicit sync shortcut below)

## Correct flow for self-hosted-oss changes

1. Edit `self-hosted-oss/<script>.sh` in the repo (this worktree).
2. Commit + push + open a PR (infra changes need a PR; host-only edits
   drift, get clobbered, and don't propagate).
3. After commit, sync the local mirror via Bash:
   ```bash
   cp self-hosted-oss/<script>.sh \
      ~/.local/share/worldarchitect-runners/<script>.sh
   ```
4. After the PR merges, re-run `bash self-hosted-oss/install.sh` on every
   other Mac so `RUNTIME_SCRIPTS` re-populates the mirror from the merged
   source.

## When the hook blocks — what to do

If you hit the hook, you almost certainly meant to edit
`self-hosted-oss/<script>.sh`. Re-open the file in the repo path and apply
the change there. The override `RUNTIME-MIRROR EDIT APPROVED` exists for
short-lived local experiments that will be reverted before the next install,
but is intentionally awkward to type.

## Related memory

- `feedback_2026-06-18_heal_runners_sigkill_session_conflict.md` — the
  episode that surfaced the wrong-file problem; documents the SIGKILL→SIGTERM
  fix at the recycle site, not in the mirror.
- `feedback_2026-06-09_runner_supervisor_and_ops.md` — the earlier
  "Stable install path sync" rule this skill extends.
