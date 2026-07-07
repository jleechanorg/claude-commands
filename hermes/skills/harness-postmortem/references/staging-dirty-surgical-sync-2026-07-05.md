# Staging-Dirty Surgical Sync (2026-07-05)

The recipe used to land the babysit-cron-leak fix (`b2ad00770d`) when
`scripts/deploy.sh --skip-pull --skip-restart` failed at the port health
check. This is the canonical recipe for SOUL.md / skills / scripts
changes when staging is on a non-main branch with dirty diff.

## Why `deploy.sh` was wrong here

```
$ ~/.hermes/scripts/deploy.sh --skip-pull --skip-restart

=== Stage 5: Health Check ===
...
[FAIL] port:UNBOUND — nothing on :8643 (set HERMES_HEALTH_PORT='' to disable)

STATUS: DOWN (1 failure(s))
DEPLOY FAILED: Health check DOWN twice — production gateway may be unhealthy. Check logs.
```

The deploy script exited non-zero, but the underlying sync stages had
already succeeded silently under `[single-dir]` mode. The port check is
a downstream gate that fails on transient gateway states independent of
the sync itself.

Additionally:
- The `[single-dir]` note meant `~/.hermes_prod` is a symlink to
  `~/.hermes` on this machine, so the rsync was a no-op anyway.
- Staging was on `dev1783194285` (a dirty feature branch with ~20
  modified files unrelated to this work), so the `--skip-pull` flag
  didn't merge origin/main into staging — staging stayed on the dirty
  branch with the OLD files, and the new files only existed on
  origin/main.

## The recipe (5 steps)

```bash
# === Step 1: Verify origin/main has the new commits ===
git -C ~/.hermes fetch origin
git -C ~/.hermes rev-parse origin/main
# Expected: equals the SHA you just pushed (e.g. b2ad00770d)
git -C ~/.hermes log --oneline origin/main -5
# Expected: shows your new commits on top

# === Step 2: Confirm staging is dirty on a non-main branch ===
git -C ~/.hermes branch --show-current
# If NOT 'main', staging is on a dirty feature branch
git -C ~/.hermes status --short | wc -l
# >0 means dirty — confirms deploy.sh --skip-pull won't help

# === Step 3: Copy new files from worktree to staging ===
SRC=~/.worktrees/<feat-worktree>      # e.g. meta-babysit-self-cancel
DST=$HOME/.hermes                     # canonical tree; ~/.hermes_prod is a symlink

# SOUL.md needs -f because workspace/ is gitignored (only README.md is tracked)
git -C ~/.hermes add -f workspace/SOUL.md
# (the staging tree's existing SOUL.md is from before your fix; the
# add -f + cp -p below ensures the new COMMIT block is in place)

# All other files: plain cp -p (preserves timestamps/permissions)
for f in \
  scripts/<fix>.py \
  scripts/tests/test_<fix>.py \
  skills/<umbrella-skill>/SKILL.md \
  launchd/<name>.plist.template \
  ; do
  mkdir -p "$(dirname "$DST/$f")"
  cp -p "$SRC/$f" "$DST/$f"
done

# === Step 4: Run regression tests from staging ===
# (catches encoding drift / lost characters that cp -p would silently
# pass through)
cd ~/.hermes && PYTHONPATH=scripts python3 -m pytest \
  scripts/tests/test_<fix>_contract.py \
  scripts/tests/test_<watchdog>.py \
  skills/<skill>/scripts/test_<class>.py -q

# === Step 5: Verify the COMMIT block is in BOTH staging and prod SOUL.md ===
# On this machine ~/.hermes_prod is a symlink to ~/.hermes, so a single
# grep against either path is sufficient. On machines where staging and
# prod are separate directories, grep both.
grep -c "^## COMMIT: <name>$" \
  ~/.hermes/workspace/SOUL.md \
  ~/.hermes_prod/workspace/SOUL.md
# Expected: 1  1 (both trees contain the new block)
```

## When `deploy.sh` IS the right tool

- Staging is on `main` (not a feature branch)
- The dirty diff is empty or small (unrelated local edits)
- The gateway port is known-healthy (no recent restart needed)
- The change is ONLY a SOUL.md update and you want to verify the policy
  file sync via Stage 5.5 drift warning

For everything else (skills/scripts/launchd changes when staging is
dirty), use the staging-dirty-surgical-sync recipe above.

## Anti-patterns

- ❌ **Don't `cp -p` files into a non-existent directory** — `mkdir -p
  "$(dirname "$f")"` first. Common mistake: adding a new skill in
  `skills/<new-category>/<name>/SKILL.md` without creating
  `skills/<new-category>/` first.
- ❌ **Don't use `git checkout` to bring files from origin/main to
  staging** — that overwrites the dirty staging files for ALL files,
  not just the new ones. `cp -p` is selective.
- ❌ **Don't run `deploy.sh` after the surgical sync** — `deploy.sh`
  Stage 4.6 is a skills rsync that would re-overwrite what you just
  copied if there's a different skill file at the same path. Skip it.
- ❌ **Don't skip the regression test step** — even if `cp -p` is
  byte-exact, a quick pytest run catches the case where the staging
  tree has a stale `__pycache__` that masks the new file's import.

## Watchdog install (separate consideration)

If the change ships a launchd plist template, the operator must install
it manually from a shell OUTSIDE the gateway session:

```bash
cp ~/.hermes/launchd/<name>.plist.template \
   ~/Library/LaunchAgents/<name>.plist
sed -i '' "s|@HOME@|$HOME|g; s|@HERMES_SLACK_BOT_TOKEN@||g" \
   ~/Library/LaunchAgents/<name>.plist
plutil -lint ~/Library/LaunchAgents/<name>.plist
launchctl load -w ~/Library/LaunchAgents/<name>.plist
launchctl kickstart -k gui/$(id -u)/<name>
```

`launchctl load -w` can SIGTERM the running gateway, so this step MUST
NOT run inside a gateway session. Defer to the operator.