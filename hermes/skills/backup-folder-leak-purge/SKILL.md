---
name: backup-folder-leak-purge
description: Force-purge a launchd/cron-driven home-config backup folder (backup/, snapshot/, home-config/) from a public GitHub repo, then prevent recurrence. Trigger when (a) `git push` keeps re-pushing personal home-dir content to a public repo every N hours, (b) `gh api .../git/trees/main?recursive=1` shows hundreds-to-thousands of paths under `backup/` or similar, (c) a closed-PR scan reveals leaked credential/secret dirs, or (d) you discover a `.gitignore` entry for backup/ that was bypassed via `git add -f`. Verified 2026-07-15 against jleechanorg/claude-commands (491 MiB / 6,820 files purged from origin/main).
tags: [security, git, github, launchd, data-leak, public-repo, pre-push-hook, gitleaks-bypass]
---

# Backup-folder leak purge

A launchd/cron job is running a home-config backup script that rsyncs `~/` into
a repo's `backup/` (or similar) folder then `git push origin main`. Pre-existing
`.gitignore` entries are bypassed by `git add -f`. The gitleaks pre-push hook
doesn't catch this class because it scans for secret patterns, not path prefixes.

This skill gives the full 6-phase recipe. Run phases IN ORDER — the leak
resumes within minutes if you skip ahead.

## When to use this skill

- A repo's `origin/main` has paths like `backup/`, `snapshot/`, `home-config/`,
  `private/`, `secrets/` that you did NOT intentionally add.
- A `scripts/backup-home.sh` (or similar) is run by launchd and pushes to `origin/main`.
- A user says "stop this backup cron", "the folder shouldn't be in this repo",
  "my home dir is on github", "backup-home.sh is leaking", or asks about a PR
  with thousands of unrelated file changes.
- `gh api repos/<org>/<repo>/git/trees/main?recursive=1 --jq '[.tree[]|select(.path|startswith("backup/"))]|length'` returns a non-zero number.

## Failure pattern

1. A `scripts/backup-home.sh` rsyncs a curated subset of `~/` into `$REPO/backup/<hostname>/`.
2. The script commits with `git add backup/ && git commit -m "backup: automated home config snapshot ..."`.
3. If local branch is main, `git push origin main` directly. Otherwise a
   temporary worktree is created on main, the commit is staged there, and pushed.
4. `.gitignore` has `backup/` but the script uses `git add -f backup/` to bypass.
5. The pre-push gitleaks hook scans staged content for secrets — `backup/` has
   no secret patterns, so the push is allowed.
6. Each launchd tick (every 1-12h) adds a new "backup: ..." commit, growing the
   leak by ~hundreds of MiB per day.

## Recipe — 6 phases (execute in order)

**CRITICAL: clarify user intent FIRST.** A home-config backup script often has TWO modes:
- **Local mode** (writes to `$REPO_ROOT/backup/<host>/` on disk, never pushes)
- **Push mode** (also `git push`es to origin)

If the script supports local-only mode (via `ALLOW_GIT_BACKUP_PUSH=0`), the user may want
that preserved — only the push needs to be disabled. **Do NOT assume they want the entire
cron killed.** Verified 2026-07-15 — Jeffrey said "I want the files in user_scope/backup,
NOT in claude-commands backup" after I overcorrected by disabling the whole cron.

**Generalized rule (apply to ANY destructive fix):** When the user reports a bug
"X is happening that shouldn't", default to:
1. Identify the *minimal* intervention that stops X
2. Preserve everything else that was working
3. **Never** delete/disable a wider system as the primary fix unless the user
   explicitly says "kill it" / "stop it completely" / "take it down"
4. If the user's request is ambiguous, prefer reversible targeted fixes
   (env var change, config flip, plist reload) over irreversible ones
   (rename + chmod 000, `mv .disabled`, git reset --hard, force-push)
5. After the targeted fix, run the `home-config-backup-audit` skill to
   verify NO sibling landmines exist before declaring done

**Intent probe before Phase 1:**
- "Should the cron keep running and just stop pushing?" → Skip Phase 1+2, do Phase 2-ALT instead
- "Stop the cron entirely?" → All 6 phases

### Phase 2-ALT: Push-only disable (most common — local backups wanted)

When the cron should keep running but never push:

```bash
# In ~/Library/LaunchAgents/<label>.plist AND its .template source:
#   <key>ALLOW_GIT_BACKUP_PUSH</key>
#   <string>0</string>   # was 1
#
# Keep ALLOW_GIT_BACKUP_SYNC=1 so local backups still write to $REPO_ROOT/backup/<host>/

# Reload to pick up new env
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/<label>.plist
launchctl load -w ~/Library/LaunchAgents/<label>.plist

# Verify
launchctl print gui/$(id -u)/<label> | grep ALLOW_GIT_BACKUP_PUSH
# Expected: ALLOW_GIT_BACKUP_PUSH => 0
```

The next launchd tick runs the rsync + local write step (because `ALLOW_GIT_BACKUP_SYNC=1`)
but skips `git commit`/`git push` (because `ALLOW_GIT_BACKUP_PUSH=0`). User gets local
backup files; nothing leaves the machine.

### Phase 1: Stop the cron immediately

The cron runs every N hours. If you delete from origin first, the next tick
re-pushes and you're back at square one.

```bash
launchctl list 2>/dev/null | grep -E "backup|home-config" | head   # find label
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/<label>.plist
mv ~/Library/LaunchAgents/<label>.plist ~/Library/LaunchAgents/<label>.plist.disabled-<date>
```

Verify: `launchctl print gui/$(id -u)/<label>` returns "Could not find service".

### Phase 2: Kill the script itself

Defense in depth — even if launchd is resurrected, the script can't run.

```bash
mv scripts/backup-home.sh scripts/backup-home.sh.DISABLED-<date>-leak
chmod 000 scripts/backup-home.sh.DISABLED-<date>-leak
mv scripts/<org>.<label>.plist.template scripts/<org>.<label>.plist.template.DISABLED-<date>
```

### Phase 3: Find the clean reset target + force-push origin/main

```bash
# First commit that touched backup/ (chronologically earliest)
FIRST_LEAK_SHA=$(gh api "repos/<org>/<repo>/commits?path=backup&per_page=100" \
    --jq 'sort_by(.commit.author.date) | .[0].sha')

# Parent of that commit = clean tip
PARENT_SHA=$(gh api "repos/<org>/<repo>/commits/$FIRST_LEAK_SHA" --jq '.parents[0].sha')

# Reset + force-push
git -C <local-clone> reset --hard "$PARENT_SHA"
git -C <local-clone> push --force-with-lease origin main
```

**Target selection:** Often the clean tip is the commit that originally added
`backup/` to `.gitignore`. Resetting there keeps the gitignore defense in place
AND drops every leak commit. Don't reset to a "good" backup-fix commit — those
added plumbing that may also need to be reverted if it shipped to main.

### Phase 4: Verify origin is clean

```bash
gh api "repos/<org>/<repo>/git/trees/main?recursive=1" \
    --jq '[.tree[] | select(.path | startswith("backup/"))] | length'
# Expected: 0

gh api "repos/<org>/<repo>/contents/backup"
# Expected: 404 Not Found
```

### Phase 5: Prevent recurrence

**5a. Pre-push hook** — See [`templates/pre-push-backup-block.sh`](templates/pre-push-backup-block.sh).
Install at `<repo>/.git/hooks/pre-push` (chmod 755) in EVERY clone that could
push to this repo (especially the one the cron writes from).

**Critical:** stdin field order per `git/githooks.adoc` is
`<local-ref> SP <local-sha> SP <remote-ref> SP <remote-sha>`. Wrong order
makes the hook silently pass. See
[`references/git-hooks-pre-push-stdin-format.md`](references/git-hooks-pre-push-stdin-format.md)
for the full bug analysis + 3-test verification harness.

**Verify the hook actually works** — see
[`scripts/verify-hook-blocks-backup-push.sh`](scripts/verify-hook-blocks-backup-push.sh).
Run this BEFORE declaring the fix done. If Test 1 (forbidden path in main
push) exits 0 instead of 1, the hook is silently broken — fix immediately.

**5b. Watchdog launchd job** — See [`templates/backup-leak-watchdog.sh`](templates/backup-leak-watchdog.sh).
Runs every 15 min, checks: (a) `ALLOW_GIT_BACKUP_PUSH` in active plist is `0`
(or plist absent — cron disabled), (b) origin/main has 0 forbidden paths.
Posts to Slack on any anomaly with 6h cooldown.

**Note:** The earlier version of this watchdog checked "is the launchd label
unloaded" — that's wrong if the cron is supposed to keep running locally.
The correct check is "is `ALLOW_GIT_BACKUP_PUSH=1`", since the cron being
loaded is fine as long as it's not pushing.

**5c. Token gate** — The existing gitleaks pre-push hook should ALSO refuse
the push if `git add -f backup/` was used. Add the path-prefix check
(BEFORE the secret scan) to your pre-push hook so both run.

### Phase 6: Local cleanup

```bash
du -sh ~/projects_other/<user_scope>/backup/   # was 8.2 GiB in our case
rm -rf ~/projects_other/<user_scope>/backup/

# Other dormant worktrees — leave the branch HEAD alone (history preserved),
# but the working-dir residue is harmless if the branch is local-only and not pushed
```

## Pitfalls

1. **Don't delete the .gitignore entry.** Even though the leak bypassed it via
   `git add -f`, the gitignore prevents future accidental `git add backup/`
   from working in the common case.

2. **Don't reset to the latest backup-fix commit.** Those commits modified
   `scripts/backup-home.sh` to make it dropbox-only by default — but they were
   the same broken pipeline that leaked. Reset to the commit BEFORE the first
   backup-touching commit (often the .gitignore commit itself).

3. **Pre-push stdin field order is `<local-ref> SP <local-sha> ...`.** Common
   bug: `read -r local_sha local_ref remote_sha _` swaps SHA and ref, hook
   silently passes. See
   [`references/git-hooks-pre-push-stdin-format.md`](references/git-hooks-pre-push-stdin-format.md).

4. **gitleaks pre-push hooks don't catch path-prefix leaks.** They scan for
   secret patterns (apiKey, tokens, etc.), not path prefixes. Add a path-prefix
   check alongside the secret scan, not as a replacement.

5. **The leak could happen in branches too.** The hook only enforces on
   `refs/heads/main`. Feature branches can still add forbidden paths; the next
   main merge re-introduces them. If your workflow merges feat → main, also
   check on `refs/heads/feat/*` or enforce a server-side pre-receive rule.

6. **GitHub's web UI keeps deleted files briefly.** After force-push, the
   folder disappears from the tree view, but commits remain in reflog and
   forks. To minimize: `gh api -X DELETE repos/<org>/<repo>/git/refs/heads/<leaked-branch>`
   for any branches that ever pushed forbidden paths.

7. **`mv + chmod 000` is reversible.** Don't rely on it alone. The pre-push
   hook is the durable fix; the rename just stops the bleeding while you fix.

8. **After fixing one cron, sibling landmines usually exist.** One bad launchd
   job is rarely the only one in the fleet. Run
   [`home-config-backup-audit`](../home-config-backup-audit/SKILL.md) BEFORE
   declaring the incident closed. Common siblings: dormant plists with the
   same script, `auto-push-to-main.sh` invoked from cron pipelines, broken
   scripts whose bugs are masking the leak.

## Support files

- [`references/git-hooks-pre-push-stdin-format.md`](references/git-hooks-pre-push-stdin-format.md) —
  bug analysis of the field-order trap that makes hooks silently pass, with
  3-test verification harness.
- [`scripts/verify-hook-blocks-backup-push.sh`](scripts/verify-hook-blocks-backup-push.sh) —
  re-runnable 3-test harness. Run BEFORE declaring any backup/ pre-push hook done.
- [`templates/pre-push-backup-block.sh`](templates/pre-push-backup-block.sh) —
  drop-in pre-push hook. Edit `FORBIDDEN_PATTERNS` + `PROTECTED_BRANCHES` env vars.
- [`templates/backup-leak-watchdog.sh`](templates/backup-leak-watchdog.sh) —
  re-emergence watchdog. Wrap in launchd plist (StartInterval 900).

## Companion skill

- [`home-config-backup-audit`](../home-config-backup-audit/SKILL.md) —
  **RUN THIS AFTER applying any fix from this skill.** Audits the entire fleet
  (loaded launchd jobs + system crontab + dormant plists + scripts that combine
  `git push` with `~/` patterns + recurring-pipeline callers) for sibling
  landmines (other crons/dormant scripts that would push to public repos if
  re-activated). Use when user says "double check all the backup jobs" or
  before declaring any single-fix event done.

## Provenance

- **Date:** 2026-07-15T20:00Z (first detected), fixed 2026-07-15T21:05Z
- **Affected:** jleechanorg/claude-commands public repo, ~491 MiB / 6,820 files over 12 hours
- **Trigger:** launchd `org.$USER.user-scope-backup` running `scripts/backup-home.sh` every 7200s
- **Files:** `~/.claude/CLAUDE.md`, `~/.hermes/CLAUDE.md`, `~/.claude/agents/*`, `~/.claude/claude-wa/backups/*`, `~/.gemini/*`, `~/.opencode/storage/session_diff/*`, `~/.openclaw/*`, `crontab.txt` — all under `backup/jeffreys-macbook-pro/`
- **Recurrence prevention:** `ai.hermes.backup-leak-watchdog` launchd plist (every 15 min) posts to `#all-$USER-ai` on any anomaly.
- **Recipe memory:** See `~/.hermes/MEMORY.md` entry "claude-commands backup/ leak (2026-07-15, 491 MiB PUBLIC)" for the compressed replay.