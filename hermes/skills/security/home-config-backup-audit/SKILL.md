---
name: home-config-backup-audit
description: Audit ALL home/~/backup/sync/snapshot-related jobs + scripts on a Mac for any that push personal home-dir content to PUBLIC GitHub repos. Trigger when a backup/ leak is found in a public repo, when the user says "double check all the backup jobs", or when any cron-driven backup is added/changed. Use after fixing one backup leak to catch sibling landmines in the same fleet.
tags: [security, git, github, launchd, data-leak, public-repo, backup, audit, cron]
---

# Home-config backup audit (fleet-wide sibling scan)

When one backup/ sync leaks personal home-dir content to a public repo, there are
usually **sibling landmines** nearby — other crons that haven't leaked *yet* but use
the same anti-pattern (rsync ~/ <somewhere> + git add + git push origin main).
This skill catches them before they leak.

Verified 2026-07-15 against `$HOME/`: after fixing the
`org.$USER.user-scope-backup` leak, this audit flagged
`ai.hermes.schedule.cron-backup-sync` (latent landmine — bash-bug currently masks it),
4 dormant scripts (`backup-hermes-full.sh`, `backup-openclaw-full.sh`, etc.) wired to
an uninstalled launchd job, and the `daily-repo-export` pipeline that calls
auto-push-to-main.sh.

## When to use this skill

- A backup/ leak was just fixed. **Run this skill BEFORE declaring done.**
- User says "double check all the backup jobs", "audit all the crons", "any other
  push to public repos?", "what else is leaking?".
- A new home-config backup script is added anywhere on disk.
- Periodic security sweep (monthly or on cron-bundle changes).

## Audit surface — every place a home-config backup could leak

There are **5 surfaces** a backup cron can push from. Each needs its own probe:

### Surface 1: Loaded launchd jobs
```bash
launchctl list | grep -iE "backup|home-config|user-scope|conversation-backup|disk-snapshot|cron-backup|qdrant-backup|snapshot|home\\.sh"
```
For each hit, read the plist + identify the script: `plutil -convert xml1 -o - <plist>`.

### Surface 2: System crontab
```bash
crontab -l
```
Look for any line referencing `backup`, `home-config`, `user-scope`, or any
`rsync`/`tar` followed by `git push`.

### Surface 3: Dormant launchd plists
```bash
ls ~/Library/LaunchAgents/ | grep -iE "backup|home-config|user-scope|snapshot"
```
Filter for `.plist` (active) AND `.plist.disabled*` (dormant but on disk). The
dormant ones are landmines: a single `launchctl load` re-enables them.

### Surface 4: Shell scripts with backup + push logic
```bash
# Scripts that have BOTH a push AND a ~/ backup
grep -l "git push" ~/scripts/*.sh ~/projects_other/*/scripts/*.sh ~/.hermes/scripts/*.sh 2>/dev/null | while read f; do
  if grep -qE "backup/|/backup|home-config|user_scope|~/" "$f"; then
    echo "$f"
  fi
done
```
**Skip intentional per-repo wrappers**: `push.sh`, `sync_branch.sh`,
`integrate.sh`, `commit-pending.sh`, `auto-push-to-main.sh`,
`consolidate-*-snapshots.sh`. Those are repo-local, not home-config backup.

### Surface 5: Each backup script's target repo privacy
For every backup-push script found, trace:
- `REPO_ROOT` in the script = where it `cd`s before `git push`
- The git remote of that path: `git -C <REPO_ROOT> remote -v`
- **Public repos** (jleechanorg/* are mostly public by default) → red flag
- **Private repos** (org/repo, or private fork) → review contents

## Per-job audit checklist

For each launchd-loaded suspicious job:

1. **What script does it run?** `plutil -convert xml1 -o - <plist>` →
   extract the program argument.

2. **What does the script write?** Grep for `rsync`, `cp`, `>`, `tee`, etc.
   - If it writes only to `~/<something>` and/or Dropbox/`/Volumes` → local
   - If it writes to `$REPO_ROOT/backup/...` and then `git add && git push` → red flag

3. **Where does it push?** Grep for `git push`, `gh repo`, `hub api`:
   - `git push origin main` → check `git -C <REPO_ROOT> remote get-url origin`
   - Look for `HEAD:refs/heads/...` (custom refspec), worktree-based pushes,
     `--force-with-lease`, `--no-verify` (hint that hook was bypassed)

4. **What content does it include?** Sample the JSON/MD/text output:
   - Just metadata (cron IDs, names, schedules) → low risk
   - Source code, configs, dots (claude/, openclaw/) → high risk

5. **Is the push step guarded?** Look for:
   - `ALLOW_GIT_BACKUP_PUSH=0` env var (script-level guard) ✓
   - `if [[ "$REMOTE" == *github.com/jleechanorg* ]]; then skip` (caller-side) ✓
   - Pre-push hook checking `^backup/` paths (filesystem-level guard) ✓
   - `git add -f` to override .gitignore (sign it's bypassing safety) 🚩
   - `--no-verify` on push (sign hook is being skipped) 🚩

6. **Is the script currently broken?** `set -e` + bash syntax error = push
   silently never runs. **Latent risk**: fixing the bug without removing the
   push resumes the leak. Probe by reading the .err.log.

7. **Is it actually loaded?** Cross-check `launchctl list` (active) vs. the
   `.plist` file existing. A plist can exist without being loaded.

## Common sibling anti-patterns

These appear in ANY home-config backup script on the user's fleet:

| Anti-pattern | Risk | Where seen |
|---|---|---|
| `rsync -a ~/ $REPO/backup/<host>/` + `git add backup/ && git push origin main` | **Catastrophic** — direct home-dir push to public repo | backup-home.sh, backup-hermes-full.sh, backup-openclaw-full.sh |
| `git add -f backup/` to bypass `.gitignore` | **Critical** — same pattern as catostrophic, just hidden | backup-home.sh originally |
| `git commit "backup: ..." && git push` in cron | **High** — automated pushes with no human review | backup-home.sh, disk-magician snapshot |
| `command not found` errors in stderr but commit succeeds elsewhere | **Latent** — broken script masked the leak for months | cron-backup-sync.sh (bash bug since 2026-05-18) |
| Disk-magician style: script with caller-output vs default-push branch | **Moderate** — depends on which branch is taken | disk_magician.sh line 285 |
| Cron schedule uses 4h/2h cadence (StartInterval <14400) | **High** — leak rate matches schedule | backup-home.sh, daily-repo-export 24h |

## Audit outcome — what to fix vs what to report

For each finding, classify:
- **FIX**: Push to public of private content. Stop it now.
- **REPORT**: Push to public of metadata. User decision: kill it or accept the leak.
- **DEFEND**: Push to public of nothing relevant. Add pre-push hook, watchdog.
- **IGNORE**: Local-only. No action.

**Default for ambiguous metadata-push-to-public cases**: REPORT, don't auto-fix.
Reason: past session showed user-preference is "I want local backup, not in claude-commands"
— which means they want to keep the cron running. Killing it without consent
leads to "I think you got it backwards" corrections.

## Recurring-pipeline check (the 6th surface)

Even if you audit all the cron jobs, there's a **6th place** a backup can leak:
scripts that *call* backup scripts, e.g.
`$HOME/.worktrees/jleechanclaw/watchdog-20min/scripts/standard_ao_jobs.py`.
That file's `default_jobs()` calls `backup-home.sh --prepare-only` on the
`user-scope` repo. Even though the wrapper's own `git add -u` doesn't stage
new backup/ paths, the underlying `backup-home.sh` does. So if
`backup-home.sh`'s git-commit step is re-enabled, this pipeline ALSO pushes.

**Probe for it**:
```bash
# Find scripts that invoke known backup scripts
grep -lE "backup-home|backup-hermes|backup-openclaw|backup-smartclaw|disk_magician" \
  $HOME/scripts/*.sh $HOME/.worktrees/*/scripts/*.sh 2>/dev/null
```
For each match, read the call site — does it pass flags that disable the
push step (`--prepare-only` was a phantom flag in 2026-07-15;
`backup-home.sh` only knows `--dry-run` and no-args)?

## Verification recipe after fixes

Once you've patched plist env vars, scripts, or gitignores:

```bash
# 1. Re-list ALL backup jobs (sanity)
launchctl list | grep -iE "backup|home-config|user-scope|snapshot"

# 2. For each impacted script, do a dry-run if it has one
~/projects_other/user_scope/scripts/backup-home.sh --dry-run 2>&1 | grep -E "Skipping|push|origin" | head -5

# 3. Verify env actually loaded
launchctl print gui/$(id -u)/<label> | grep ALLOW_GIT_BACKUP_PUSH

# 4. Force a tick and check the log
launchctl kickstart -k gui/$(id -u)/<label>
sleep 5
tail -20 ~/Library/Logs/<label>.launchd.log | grep -E "git|dropbox|SUCCESS|skip"

# 5. Run the watchdog at least once to confirm it doesn't false-alarm
~/scripts/user-scope-backup-watchdog.sh
tail -3 ~/Library/Logs/user-scope-backup-disable-watchdog.log
```

## Pitfalls

1. **One bad launchd job often masks sibling latent risk.** The fix you do for
   the known leak may turn a dormant sibling into the next leak. Always run
   this audit AFTER fixing any backup incident, not before.

2. **A plist file existing ≠ loaded.** Many repos leave `.plist.template` and
   even `.plist` files around that aren't loaded. `launchctl list` is the only
   reliable source of truth for what's actually scheduled.

3. **`set -e` + bash error = silent non-execution.** If a script has been
   "running" daily for months with no successful push, suspect `set -e` is
   bailing out before the push step. Fix the bash bug only AFTER you've
   removed the push-to-public step — otherwise you re-leak.

4. **The `daily-repo-export` pipeline runs `auto-push-to-main.sh` for
   `llm-wiki`, `roadmap`, AND `user-scope`.** `user-scope`'s remote is
   `jleechanorg/claude-commands` — a SECOND fork of `user_scope` is pushing
   to the same PUBLIC repo. `auto-push-to-main.sh` uses `git add -u` so it
   won't pick up new backup/ files, but if any of those repos already have
   backup/ tracked, it's game over.

5. **Don't grep only the obvious cron names.** `backup`, `home-config`,
   `user-scope`, `snapshot` are the obvious ones. Also grep for:
   `crontab-backup`, `cron-backup-sync`, `disk_snapshot`, `home.sh`,
   `home-config`. Use multiple greps and union them.

6. **Dormant scripts still have `git push` lines.** Even if not scheduled,
   a future `install-hermes-backup-jobs.sh` run wires them up. Treat the
   script's `git push origin main` as a latent risk to flag, not an active
   one to ignore.

## Provenance

- **Date:** 2026-07-15T21:00Z
- **Affected fleet:** `$HOME/.hermes`, `$HOME/projects_other/{user_scope,jleechanbrain,openclaw}`
- **Surfaced:** `ai.hermes.schedule.cron-backup-sync` (latent — bash bug since 2026-05-18),
  `~/.hermes/scripts/backup-hermes-full.sh` (dormant),
  `~/projects_other/jleechanbrain/scripts/backup-{hermes,openclaw}-full.sh` (dormant),
  `~/projects_other/openclaw/scripts/backup-openclaw-full.sh` (dormant),
  `ai.hermes.schedule.daily-repo-export` (safe today, but watches backup-home.sh)
- **Sibling skill:** `backup-folder-leak-purge` — fix the immediate leak; run THIS skill afterward.
- **Output format:** save audit as Markdown to `~/.hermes/logs/backup-leak-audit-<date>.md`
  so future agents have the fleet state.
