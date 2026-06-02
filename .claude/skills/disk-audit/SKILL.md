---
name: disk-audit
description: Run disk usage analysis and cleanup preview on the local Mac. Always validate snapshot coverage before quoting. Never delete without user approval.
metadata:
  type: skill
  runtime: claude
---

# Disk Audit — Skill

Analyze local disk usage, validate snapshot completeness, identify cleanup candidates, and optionally clean safe targets. **Always defaults to dry-run preview.** Never deletes anything without explicit user approval.

## Contract

- **Command alias:** `/disk-audit` (points here)
- **Snapshot script:** `~/projects_other/user_scope/scripts/disk_snapshot.sh` — emits JSON with `snapshot_coverage_pct` + `timeout_keys`
- **Audit script:** `~/projects_other/user_scope/scripts/disk_audit.sh`
- **Default invocation:** `--clean --dry-run` (preview only)
- **Never-delete list:** `~/.codex/sessions`, `~/.codex/sessions_archive/`, `~/.codex/state*.sqlite`, `~/.codex/log`, `~/.claude/projects`
- **Mtime caution:** Worktrees and AO sessions with mtime <14 days require explicit `WORKTREE APPROVED` per CLAUDE.md

## When to Use

- User wants to check disk usage
- User wants to see cleanup candidates before approving
- Disk alert fires (≥80% used)
- User wants to know "why did my disk grow so much"

## Phases

### Phase 0: SNAPSHOT VALIDATION (mandatory before quoting numbers)

**Before quoting any size from `disk_snapshot.json`, validate it:**

```bash
python3 -c "
import json
s = json.load(open('backup/Mac/disk_snapshot.json'))
print(f'coverage: {s.get(\"snapshot_coverage_pct\", \"missing\")}%')
print(f'warning:  {s.get(\"snapshot_warning\", \"none\")}')
print(f'timeouts: {s.get(\"timeout_keys\", [])}')
"
```

**Rules:**
- If `snapshot_coverage_pct` is missing → snapshot is from an old script version; do not quote it. Regenerate with current `disk_snapshot.sh`.
- If `snapshot_coverage_pct < 70` or `snapshot_warning == "low_coverage"` → snapshot is incomplete. Use raw `du -sh ~/.[!.]* ~/*` instead.
- If `timeout_keys` is non-empty → those entries are `null` in the JSON (NOT zero). Re-measure them directly: `du -sh ~/.gemini` etc.
- Any entry reading `null` ≠ empty dir. It means `du` timed out. Re-measure.

### Phase 1: DISCOVERY (catch new blind spots)

Run `./scripts/disk_snapshot.sh --discover` to scan `~/.[!.]*` and `~/*` for dirs >5 GB not currently in `MONITORED_DIRS`. If new entries appear, add them to the script.

### Phase 2: AUDIT (default)

Run `./scripts/disk_audit.sh --clean --dry-run` to show cleanup candidates without deleting.

### Phase 3: CLEAN (with approval)

After user approves dry-run output:
```bash
./scripts/disk_audit.sh --clean
```

### Phase 4: CLEAN-ALL (aggressive, with approval)

Includes Docker system prune candidates:
```bash
./scripts/disk_audit.sh --clean-all
```

## Sparse-file trap (Docker.raw, *.qcow2, *.img)

VM disk images on macOS are **sparse files** with two sizes:
- **Apparent** (`stat -f%z`): logical max — can be 926 GB even when nearly empty
- **Allocated** (`du -sk`): actual blocks on disk

**Always use `du -sk` for these.** Never `stat`. The `disk_snapshot.sh` script (post 2026-05-24) already uses `du -sk` exclusively. To verify a sparse file's real size manually:
```bash
du -h ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw   # allocated
docker system df                                                          # itemized
```

## Known disk-bloat patterns (from 2026-05-24 audit)

| Pattern | Where | Typical size | Notes |
|---------|-------|-------------:|-------|
| IDE worktrees with full project copies | `~/.gemini/antigravity/worktrees/`, `~/.ao-sessions/<sid>/.gemini/antigravity/worktrees/` | 50–150 GB | **Two-level nesting pattern:** AO sessions that used Antigravity as their agent store a full `.gemini/antigravity/` subtree *inside* the session dir. That subtree contains a `worktrees/worktree_<project>/` dir with one sub-worktree per PR task — each sub-worktree is a complete project clone + venv (~1 GB). Example: `ao-5847/.gemini/antigravity/worktrees/worktree_worldarchitect/` held 79 sub-worktrees = 43.7 GB. Don't delete while Antigravity IDE is running (`ps aux \| grep -i antigravity`). Check mtime <14d → needs `WORKTREE APPROVED`. |
| SQLite repair backups | `~/.codex/*.codex-repair-*.bak` | 1–10 GB | Created during state DB repair. Safe to delete if >5 days old AND original DB is healthy. |
| Single runaway logs | `~/Library/Logs/cmux-focus.log`, `~/Library/Logs/com.openai.codex/*` | 100–800 MB | Truncate with `: > path` to keep inode open for active writer. |
| Old Python venvs in abandoned projects | `~/projects/*/venv`, `~/projects_other/*/.venv` | 50–700 MB each | Find with `find ~/projects -name '.venv' -mtime +90`. Always check `git log -1` in parent dir first — only prune from projects with no commits in 90+ days. |
| Updater app caches | `~/Library/Caches/*-updater` | 200–700 MB | Safe — apps re-download. |
| `__pycache__` accumulation | Across projects | 1–2 GB | Always safe to delete (`find ~/projects -name __pycache__ -mtime +30 -exec rm -rf {} +`). |

## Output Format

1. Overall disk status (`df -h /`)
2. **Snapshot validation result** (coverage %, warnings, timeout_keys)
3. Top cleanup candidates with sizes
4. Total reclaimable space
5. Next step: "Run `disk_audit.sh --clean` to proceed"

## Allowed Tools

- Bash (run scripts, `du`, `df`, `lsof` for in-use check)
- Read (inspect scripts/snapshots)
- Do NOT use `rm -rf` directly — go through `disk_audit.sh`

## Common pitfalls

1. **Quoting snapshot numbers without checking coverage** — always run Phase 0 first.
2. **Assuming a tracked dir reading 0 KB is empty** — it may have timed out (pre-Coverage_pct era) or be `null` (post-update). Cross-check.
3. **Quoting Docker.raw apparent size as real usage** — always use `du -sk` or `docker system df`.
4. **Deleting AO/IDE worktrees while IDE is running** — check `ps aux | grep -i antigravity` and `lsof +D ~/.gemini` first.
5. **Deleting venvs in recently-active projects** — gate on `git log -1 --format=%ai` ≥90 days old.
6. **Recommending cleanup of `~/.codex/sessions*`** — these are PROTECTED per repo CLAUDE.md.

## Context

- Script paths: `~/projects_other/user_scope/scripts/disk_{snapshot,audit,usage_alert}.sh`
- Launchd alert: `com.$USER.disk-usage-alert.plist` (threshold default 787 GB)
- Snapshot cron: runs from `backup-home.sh` every 30 min, commits JSON to git
- Tests: `~/projects_other/user_scope/tests/test_disk_snapshot.py` (10 tests covering sparse files, timeout sentinel, coverage_pct, discover mode)

## Triggers

disk audit, disk cleanup, clean disk, disk space, reclaim disk, disk usage, snapshot coverage, what's eating my disk
