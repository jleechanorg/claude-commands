# `POLICY_FILES` ↔ Skill sync gap in `deploy.sh`

## Status (2026-06-25): SKILLS SIDE CLOSED — `.claude/commands/` still requires manual `cp`

The skills part of this gap was closed on 2026-06-25 by adding **Stage 4.6 (Skills Sync)** and **Stage 5.5b (Skills Drift Warning)** to `deploy.sh` (commit [`2d540be9b3`](https://github.com/jleechanorg/jleechanclaw/commit/2d540be9b3865d01d89535f0bd9e2fc85d28d082) on `jleechanclaw` origin/main). Skill edits committed to `~/.hermes/skills/` in `jleechanorg/jleechanclaw` now auto-propagate to `~/.hermes_prod/skills/` on every `deploy.sh` run. Companion upstream fix landed in [jleechanorg/hermes-agent PR #34](https://github.com/jleechanorg/hermes-agent/pull/34): `tools/skill_manager_tool.py` now pins `SKILLS_DIR` to `~/.hermes/skills/` (canonical git root) via `_get_canonical_skills_root()`, with `HERMES_SKILLS_DIR` env override for tests/Docker/CI. Previously, `skill_manage` derived `SKILLS_DIR = HERMES_HOME / "skills"`, so prod-profile sessions (`HERMES_HOME=$HOME/.hermes_prod`) wrote skills to `~/.hermes_prod/skills/` and never touched git — silent data loss.

**What still requires manual `cp`** (NOT yet closed):

- `~/.hermes/.claude/commands/<name>.md` — slash commands. Deploy.sh still does NOT sync `.claude/commands/`. See SKILL.md anti-pattern (`.claude/commands/ is also NOT in POLICY_FILES`).
- `~/.hermes/scripts/<name>.sh` — companion cron scripts that live outside the Stage 4.5 + 4.6 sync.
- `~/.hermes/launchd/*.plist.template` — cron job plist templates.

The remainder of this doc is kept for historical context. The original gap, the 2026-06-19 worked example, and the decision matrix are all still load-bearing — the SKILLS gap is closed but the same drift class can recur for OTHER directories (cron scripts, launchd templates, .claude/commands/).

---

## The gap (historical, partially closed)

`~/.hermes/scripts/deploy.sh` Stage 4.5 (Policy Sync) only syncs four files:

```bash
POLICY_FILES=(CLAUDE.md SOUL.md TOOLS.md HEARTBEAT.md)
```

Anything outside this list is **not** synced between `~/.hermes/` (staging) and `~/.hermes_prod/` (prod runtime) by the deploy pipeline. That includes:

- ~~`~/.hermes/skills/<name>/SKILL.md` and its `tests/`, `references/`, `templates/`, `scripts/`~~ — **closed 2026-06-25 by Stage 4.6**
- ~~`~/.hermes/skills/RESOLVER.md` — the trigger-pattern index~~ — **closed 2026-06-25** (RESOLVER.md lives inside `skills/` and is now rsynced by Stage 4.6)
- `~/.hermes/scripts/*.sh` — companion cron scripts — **STILL OPEN**
- `~/.hermes/launchd/*.plist.template` — cron job plist templates — **STILL OPEN**
- `~/.hermes/cron/jobs.json` — handled separately by `install-launchagents.sh`, but still not in `POLICY_FILES` — **STILL OPEN**
- `~/.hermes/.claude/commands/<name>.md` — slash commands — **STILL OPEN, see SKILL.md anti-pattern**

When a skillify pass writes to staging only, the prod resolver doesn't see the skill. When it writes to prod only, the staging git checkout is empty and a future `git pull --ff-only` could delete it without warning.

## Worked example — finish-the-job (2026-06-19)

A skillify pass for the `finish-the-job` skill wrote:

| Artifact | Home |
|---|---|
| `SKILL.md` + `tests/` + `references/` | `~/.hermes_prod/skills/finish-the-job/` (direct write) |
| `RESOLVER.md` entry | `~/.hermes_prod/skills/RESOLVER.md` (direct write) |
| `finish-the-job-autoarm.sh` | `~/.hermes/scripts/` (staging) |
| `ai.hermes.schedule.finish-the-job-autoarm.plist.template` | `~/.hermes/launchd/` (staging) |
| `## COMMIT: finish-the-job` | `~/.hermes/workspace/SOUL.md` (via `~/.hermes/SOUL.md` symlink) |

`deploy.sh --skip-pull` ran:
- Stage 4 (Gateway Restart): passed
- Stage 4.5 (Policy Sync): `POLICY_FILES` matched → all 4 files identical → no sync fired
- Stage 5 (Canary): FAILED — LLM provider flake, **unrelated to the skill files**

The skill was reachable from the prod resolver (it had been written to prod directly), but the cron script + plist template only existed in staging. Recovery:

```bash
# Manual SOUL.md sync (since canary failed and Stage 4.5 was the planned sync path)
cp ~/.hermes/SOUL.md ~/.hermes_prod/SOUL.md
diff -q ~/.hermes/SOUL.md ~/.hermes_prod/SOUL.md && echo "in sync"

# Note: the cron script and plist template are in staging only.
# To deploy them, either (a) widen POLICY_FILES, (b) rsync the script dirs, or
# (c) accept the manual cp in the rollout script.
```

## Decision matrix — how to fix it

Three options, pick based on user's deploy conventions:

### Option A — Widen `POLICY_FILES` (simplest)

Edit `deploy.sh`:
```bash
POLICY_FILES=(CLAUDE.md SOUL.md TOOLS.md HEARTBEAT.md skills/RESOLVER.md)
# Skills live in skills/ and are versioned in git, but they're large trees —
# NOT single-file syncs. Better to keep POLICY_FILES single-file-only and
# add a separate Stage 4.6 skills sync instead.
```

Downside: `POLICY_FILES` is single-file-shaped (the loop does `cp src dst`). Adding a directory means reworking Stage 4.5.

### Option B — Add a Stage 4.6 skills sync (cleanest separation) ✅ CHOSEN 2026-06-25

Insert after Stage 4.5:

```bash
section "Stage 4.6: Skills Sync → $PROD_DIR"
if [[ "${SKIP_SYNC:-0}" == "1" ]]; then
  echo "  skipped (--no-sync)"
else
  rsync -a -c \
    --exclude='__pycache__' \
    --exclude='.usage.json' \
    --exclude='.curator_backups' \
    "$REPO_DIR/skills/" "$PROD_DIR/skills/"
  echo "  skills/ → $PROD_DIR/skills/ (add-only, no --delete)"
fi
```

Plus a Stage 5.5b non-blocking drift check:

```bash
section "Stage 5.5b: Skills drift warning"
DRIFT_COUNT=$(rsync -a -c --dry-run \
  --exclude='__pycache__' --exclude='.usage.json' --exclude='.curator_backups' \
  "$REPO_DIR/skills/" "$PROD_DIR/skills/" 2>/dev/null \
  | wc -l | tr -d ' ')
if [[ "$DRIFT_COUNT" -gt 0 ]]; then
  echo "  ⚠ $DRIFT_COUNT files in skills/ differ between staging and prod"
else
  echo "  skills/ in sync"
fi
```

**Critical: `--delete` MUST NOT be used.** Prod has 354 skill dirs, staging has 188. The 166 prod-only skills are hub-installed skills that are NOT in the `jleechanorg/jleechanclaw` git repo. `--delete` would wipe them out on the first deploy. Add-only rsync (the recipe above) is the safe default. Verified 2026-06-25 during the initial dry-run.

**rsync `-c` flag is mandatory** — it forces checksum-based change detection (vs. timestamp+mtime). Without `-c`, rsync can miss changes after `git checkout` switches branch tips.

**Skillify-pass verification (same turn as the commit):**

```bash
echo "1. staging skill:  $(test -d ~/.hermes/skills/<name> && echo PRESENT || echo MISSING)"
echo "2. prod skill:     $(test -d ~/.hermes_prod/skills/<name> && echo PRESENT || echo MISSING)"
echo "3. RESOLVER entry: $(grep -c '^## <name>$' ~/.hermes/skills/RESOLVER.md)/1 staging"
echo "4. RESOLVER entry: $(grep -c '^## <name>$' ~/.hermes_prod/skills/RESOLVER.md)/1 prod"
echo "5. drift check:    $(rsync -a -c --dry-run --exclude='__pycache__' --exclude='.usage.json' --exclude='.curator_backups' ~/.hermes/skills/<name>/ ~/.hermes_prod/skills/<name>/ 2>/dev/null | wc -l | tr -d ' ') files differ (0 = in sync)"
echo "6. Stage 4.6 dry:  $(~/.hermes/scripts/deploy.sh --no-sync --dry-run 2>&1 | grep -c 'Stage 4.6') match"
```

### Option C — Document manual `cp` in the closure summary (current workaround for STAGING-ONLY files)

Accept that `POLICY_FILES` is single-file and have every skillify pass include a manual sync block:

```bash
# In the rollout's same-turn verification:
cp ~/.hermes/SOUL.md ~/.hermes_prod/SOUL.md
diff -q ~/.hermes/SOUL.md ~/.hermes_prod/SOUL.md && echo "SOUL.md in sync"

# Cron script: accept staging-only if the prod launcher picks it up via PATH
test -x ~/.hermes/scripts/finish-the-job-autoarm.sh && echo "cron script in staging"

# Plist template: commit to staging, render + install via install-launchagents.sh
test -f ~/.hermes/launchd/ai.hermes.schedule.finish-the-job-autoarm.plist.template && echo "plist template in staging"
```

Downside: manual step, easy to forget. **The current state of the deploy pipeline as of 2026-06-19 for skills**, but **superseded by Stage 4.6 as of 2026-06-25 for the skills/ tree only**. Still applies to scripts/ + launchd/ + .claude/commands/.

## Recommended next step (status as of 2026-06-25)

**Skills/ tree: PARTIALLY DONE.** Option B landed on 2026-06-25. Stage 4.6 rsyncs skills add-only (no `--delete`) on every `deploy.sh` run; Stage 5.5b emits a non-blocking drift warning. Out of the original recommendation, only the skills directory rsync and the Stage 5.5b drift warning are complete, while the remaining sub-items (for scripts, launchd templates, and cron/jobs.json) are still pending:

1. ✅ Rsync new/changed skill directories from `~/.hermes/skills/` to `~/.hermes_prod/skills/` (add-only, NOT `--delete`)
2. ⏳ Rsync `~/.hermes/scripts/` to `~/.hermes_prod/scripts/` — NOT YET done. Skillify rollouts that add cron scripts still need a manual `cp`.
3. ⏳ Rsync `~/.hermes/launchd/*.plist.template` to `~/.hermes_prod/launchd/` — NOT YET done.
4. ⏳ Rsync `~/.hermes/cron/jobs.json` to `~/.hermes_prod/cron/jobs.json` — handled by `install-launchagents.sh`, NOT by deploy.sh.
5. ✅ Emit a visible diff count, warn if any dir drifts unexpectedly (Stage 5.5b)

**Companion upstream fix in `jleechanorg/hermes-agent`** ([PR #34](https://github.com/jleechanorg/hermes-agent/pull/34), pending merge): `tools/skill_manager_tool.py` was patched to pin `SKILLS_DIR` to `~/.hermes/skills/` (canonical git root) regardless of `HERMES_HOME`. Without this fix, prod-profile sessions (`HERMES_HOME=~/.hermes_prod`) wrote skills to `~/.hermes_prod/skills/` directly, bypassing git. Stage 4.6 alone is insufficient — the write target must also be canonical. Both fixes ship together; either alone leaves a partial gap.

**Still open:** same shape (Stage 4.7/4.8) for `scripts/`, `launchd/`, `cron/jobs.json`, and `.claude/commands/`. The decision matrix above applies unchanged — the user can choose Option A (widen `POLICY_FILES`) or Option B (separate Stage) when the time comes. For each of these directories, run the same `--delete` audit: prod may have files that aren't in staging (hub-installed scripts, runtime-generated configs, etc.) and `--delete` would wipe them out.

## Cross-references

- Parent skill: `../SKILL.md` — "Anti-Patterns" section: the `POLICY_FILES` gap bullet
- Companion skill `skillify` — "Anti-Pattern: Deploy.sh POLICY_FILES Gap Silently Leaves Skills Out of Sync"
- Companion case study: `~/.hermes_prod/skills/skillify/references/finish-the-job-skillify-case-study-2026-06-19.md`
