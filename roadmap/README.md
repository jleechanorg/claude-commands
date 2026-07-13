# user_scope (claude-commands) roadmap

Rolling status for /Users/jleechan/projects_other/user_scope → jleechanorg/claude-commands.

## Recent activity (rolling)

### 2026-07-12 — user-scope backup hard stop

- Added a Dropbox-only guard in `scripts/backup-home.sh` (`REQUIRE_DROPBOX_ONLY=1` by default), which forces git snapshot sync/push off unless explicitly disabled.
- Added `backup/` to repo `.gitignore`.
- Updated `scripts/org.jleechan.user-scope-backup.plist.template` to set `ALLOW_GIT_BACKUP_PUSH=0`, `GIT_BACKUP_PUSH_REMOTE=origin`, `GIT_BACKUP_PUSH_BRANCH=main`.
- Added `scripts/check-bashrc-token-health.sh` and wired it into backup runs with `TOKEN_HEALTH_PRECHECK=1` (warn-only in-flight; does not block scheduled snapshots).
- Added fail-closed behavior for token health checks: `TOKEN_HEALTH_PRECHECK_FAIL_ON_FAILURE=1` now aborts backup runs by default unless explicitly disabled.
- Incident evidence inventory remains externalized at `/Users/jleechan/roadmap/evidence-2026-07-12-agent-teams/claude-commands-LEAK-rotation-inventory.md` (no token mutation applied here).

### 2026-07-06 — claude-wa profile + backup incident cleanup

- Shipped scripts/install-claude-wa-profile.sh: symlinks shared tooling from ~/.claude into ~/.claude-wa (including projects), WA-local .claude.json.
- Extended scripts/backup-home.sh to snapshot claude-wa JSON + symlink manifest; pushed backup commit to origin/main.
- Incident: org.jleechan.user-scope-backup (2h interval, no flock) stacked with ~2-day stuck Dropbox rsync → 84 duplicate processes; killed cleanly. Git portion had already succeeded.
- Open: [jleechan-lqw / GH #318](https://github.com/jleechanorg/claude-commands/issues/318) — flock overlap guard (P1). Handoff: /Users/jleechan/roadmap/nextsteps-2026-07-06-user-scope-backup-claude-wa.md.
