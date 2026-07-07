# user_scope (claude-commands) roadmap

Rolling status for /Users/jleechan/projects_other/user_scope → jleechanorg/claude-commands.

## Recent activity (rolling)

### 2026-07-06 — claude-wa profile + backup incident cleanup

- Shipped scripts/install-claude-wa-profile.sh: symlinks shared tooling from ~/.claude into ~/.claude-wa (including projects), WA-local .claude.json.
- Extended scripts/backup-home.sh to snapshot claude-wa JSON + symlink manifest; pushed backup commit to origin/main.
- Incident: org.jleechan.user-scope-backup (2h interval, no flock) stacked with ~2-day stuck Dropbox rsync → 84 duplicate processes; killed cleanly. Git portion had already succeeded.
- Open: [jleechan-lqw / GH #318](https://github.com/jleechanorg/claude-commands/issues/318) — flock overlap guard (P1). Handoff: /Users/jleechan/roadmap/nextsteps-2026-07-06-user-scope-backup-claude-wa.md.
