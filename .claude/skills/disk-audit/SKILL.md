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
- **Snapshot generator:** `disk-magician snapshot --output <snap>` — emits JSON with `snapshot_coverage_pct` + `timeout_keys`. Config via `DISK_MAGICIAN_CONFIG=~/projects_other/user_scope/scripts/disk_magician_config.json` (user_scope's monitored-dir set). `backup-home.sh` runs this every 30 min and writes `backup/<host>/disk_snapshot.json`. The local `disk_snapshot.sh` generator was removed in favor of the shared `disk-magician` CLI. **Audit/history read user_scope's committed `backup/<host>/` tree via the reader scripts below — NOT `disk-magician audit`/`history`, which read a separate single-host `~/.disk_magician_backup` tree.**
- **Audit script:** `~/projects_other/user_scope/scripts/disk_audit.sh` — **snapshot-first**: reads pre-measured sizes from the committed snapshot, ranks the top 20 dirs, shows 7-day regressions, and bounds any live `du` at 60s. Runs in ~6s instead of timing out.
- **History script:** `~/projects_other/user_scope/scripts/disk_history.sh` — trends/regressions from 700+ git-committed snapshots
- **Host selection:** `~/projects_other/user_scope/scripts/snapshot_lib.sh` → `resolve_snapshot_path` picks the **current host's** snapshot (newest `timestamp`), not the first alphabetical `backup/<host>/` dir. Both audit + history source it so they agree. On this Mac it resolves to `backup/Mac/disk_snapshot.json`.
- **Default invocation:** `disk_audit.sh` (snapshot-ranked preview) → `--clean --dry-run` for delete candidates
- **Re-measure live:** pass `--live` to force `du` instead of the snapshot (slow); `--no-history` to skip the regression section
- **Never-delete list:** `~/.codex/sessions`, `~/.codex/sessions_archive/`, `~/.codex/state*.sqlite`, `~/.codex/log`, `~/.claude/projects`
- **Mtime caution:** Worktrees and AO sessions with mtime <14 days require explicit `WORKTREE APPROVED` per CLAUDE.md

## When to Use

- User wants to check disk usage
- User wants to see cleanup candidates before approving
- Disk alert fires (≥80% used)
- User wants to know "why did my disk grow so much"

## Phases

### Phase 0: SNAPSHOT VALIDATION (mandatory before quoting numbers)

**Resolve the current host's snapshot first** — do NOT hardcode a `backup/<host>/` path or glob the first match (that picks a stale wrong-host file). Use the shared resolver, then validate:

```bash
cd ~/projects_other/user_scope
SNAP="$(bash -c 'source scripts/snapshot_lib.sh; resolve_snapshot_path "$(pwd)"')"
python3 -c "
import json,sys
s = json.load(open(sys.argv[1]))
print('file:', sys.argv[1])
print('host:', s.get('hostname'), '| ts:', s.get('timestamp'))
print(f'coverage: {s.get(\"snapshot_coverage_pct\", \"missing\")}%')
print(f'warning:  {s.get(\"snapshot_warning\", \"none\")}')
print(f'timeouts: {s.get(\"timeout_keys\", [])}')
" "$SNAP"
```

**Rules:**
- If the resolved file's `hostname`/`timestamp` is not the current machine's latest → the resolver fell back; check `backup/*/` for a fresher file or run `DISK_MAGICIAN_CONFIG=~/projects_other/user_scope/scripts/disk_magician_config.json disk-magician snapshot --output backup/<host>/disk_snapshot.json` to regenerate.
- If `snapshot_coverage_pct` is missing → snapshot is from an old script version; do not quote it. Regenerate with `disk-magician snapshot`.
- If `snapshot_coverage_pct < 70` or `snapshot_warning == "low_coverage"` → snapshot is incomplete. Use raw `du -sh ~/.[!.]* ~/*` instead (or `disk_audit.sh --live`).
- If `timeout_keys` is non-empty → those entries are `null` in the JSON (NOT zero). Re-measure them directly: `du -sh ~/.gemini` etc.
- Any entry reading `null` ≠ empty dir. It means `du` timed out. Re-measure.

### Phase 1: DISCOVERY (catch new blind spots)

Run `DISK_MAGICIAN_CONFIG=~/projects_other/user_scope/scripts/disk_magician_config.json disk-magician snapshot --discover` to scan `~/.[!.]*` and `~/*` for dirs >5 GB not currently in the monitored config. If new entries appear, add them to `~/projects_other/user_scope/scripts/disk_magician_config.json`.

### Phase 2: AUDIT (default — snapshot-ranked, ~6s)

Run `./scripts/disk_audit.sh`. It auto-resolves the current host's snapshot and prints, with no live `du` over big home dirs:
1. **Largest directories (top 20)** ranked from the snapshot, with `Source`/`Coverage`/`Age` header so you can see staleness at a glance.
2. **Recent growth (last 7 days, regressions only)** via `disk_history.sh --days 7 --regressions` — this is how you answer "why did my disk grow?" (e.g. it surfaces Docker.raw creeping +2–4 GB/snapshot).
3. **Actionable findings** — specific delete/prune targets with sizes.

This replaces the old slow "du over ~/Library and ~/projects" path. Only reach for live measurement to verify a specific delete candidate:
- `./scripts/disk_audit.sh --live` → re-measure everything with `du` (slow; use when coverage <70% or snapshot is stale)
- `./scripts/disk_audit.sh --clean --dry-run` → show the cleanup candidates that `--clean` would act on, without deleting

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

**Always use `du -sk` for these.** Never `stat`. The `disk-magician snapshot` generator already uses `du -sk` exclusively. To verify a sparse file's real size manually:
```bash
du -h ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw   # allocated
docker system df                                                          # itemized
```

### Docker.raw reclaim — daemon-required vs daemon-free paths

`Docker.raw` grows monotonically and never auto-shrinks (high-water mark). Two reclaim paths, by daemon health:

- **Daemon UP (selective, preserves data):** `docker system df -v` (inspect volumes first) → `docker system prune -a --volumes` + `docker builder prune --keep-storage 5g` (frees *inside* the VM ext4) → `docker run --privileged --pid=host docker/desktop-reclaim-space` (official host-level shrink of the .raw; Docker Desktop 4.28+ with Apple Virtualization also auto-TRIMs). This is the default — it lets you keep named volumes.
- **Daemon DOWN (destructive, daemon-free):** if Docker Desktop won't start, *every* `docker …` command is blocked, so selective prune is impossible. The only reclaim is to **delete the whole `Docker.raw` while Docker is stopped** → `rm` it, Docker recreates an empty one on next launch. Reclaims the full allocated size instantly but **destroys all images, containers, build cache, and named volumes (no review possible)** — requires explicit user approval. Confirm `ps aux | grep -i '[d]ocker'` shows no backend first, then `rm`. (2026-06-09: reclaimed 132 GiB this way after the daemon wedged.)

**Daemon-won't-start signature (GUI wedge, needs Mac reboot):** in `~/Library/Containers/com.docker.docker/Data/log/host/com.docker.backend.log`, `opening tray: starting electron: sending file descriptors: broken pipe` → `monitor exited: exit status 150`. The `gvisor: unable to accept vfkit connection: invalid magic length` line is a downstream symptom, not the cause — the Electron tray failure cancels the backend before the VM starts. A full reboot clears the wedged GUI state; the data is not corrupt.

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
7. **Reading the wrong host's snapshot** — `backup/` holds snapshots from multiple machines (`Mac/`, `Jeff-Ubuntu/`, `jeffreys-macbook-pro/`). A naive `backup/*/disk_snapshot.json` glob picks the first alphabetical (stale Ubuntu) file → garbage coverage (`52254%`), null docker_raw, "1 snapshot" history. Always go through `resolve_snapshot_path` (newest `timestamp` wins); the scripts now do this automatically.

## Context

- Snapshot generator: `disk-magician` CLI (installed at `~/.local/bin/disk-magician`); the local `disk_snapshot.sh` was removed in favor of it
- Reader script paths (kept, read user_scope's multi-host tree): `~/projects_other/user_scope/scripts/disk_{audit,usage_alert,history}.sh`, `snapshot_lib.sh` (host resolver)
- Generator config: `~/projects_other/user_scope/scripts/disk_magician_config.json` (51-dir coverage), passed via `DISK_MAGICIAN_CONFIG`
- Launchd alert: `com.$USER.disk-usage-alert.plist` (threshold default 787 GB)
- Snapshot cron: `backup-home.sh` calls `disk-magician snapshot --output backup/<host>/disk_snapshot.json` every 30 min, commits JSON to git
- Tests: `~/projects_other/user_scope/tests/test_snapshot_lib.py` (host resolution); generator parity is covered upstream in the `disk_magician` repo

## Triggers

disk audit, disk cleanup, clean disk, disk space, reclaim disk, disk usage, snapshot coverage, what's eating my disk
