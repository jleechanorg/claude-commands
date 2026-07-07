# Hermes Deploy Pipeline — Actual State (2026-06-09)

This reference documents the **actual state** of the deploy pipeline
as observed on 2026-06-09. The umbrella `hermes-deploy-pipeline` SKILL.md
documents the **intended state**. They differ.

## What the umbrella SKILL.md says

> Always write to `~/.hermes` (staging) first. Test. Then deploy to
> `~/.hermes_prod/` via `scripts/deploy.sh`.

The umbrella references `~/.hermes/scripts/deploy.sh` for deploy
operations.

## What is actually there (as of 2026-06-09)

`~/.hermes/scripts/deploy.sh` **does not exist**. Confirmed via
`find ~/.hermes -name "deploy*.sh"` returning only `cron-backup-sync.sh`,
`install-claude-memory-sync.sh`, `sync-check.sh`, `sync-claude-memory.sh`,
`sync-to-smartclaw.sh`, and `sync_branch.sh`. None of these are the
documented `deploy.sh`.

`~/.hermes_prod/` is **not a git repository** and **not a worktree** of
`~/.hermes`. It is a plain directory that the running gateway process
reads from. Verified via:
```bash
ls -la ~/.hermes_prod/.git     # → No such file or directory
cd ~/.hermes_prod && git status  # → fatal: not a git repository
```

## So how does staging → prod sync actually work today?

**It doesn't, automatically.** The two directories are independent.
A change made in `~/.hermes/skills/foo/SKILL.md` is NOT automatically
mirrored to `~/.hermes_prod/skills/foo/SKILL.md`. The agent at runtime
loads from `~/.hermes_prod/` (because that's what the running
gateway is using), so any staging-only change is invisible to the
agent until you manually `cp` it.

The actual sync procedure as of today is:
1. Edit/write in `~/.hermes/` (staging, git-tracked)
2. `cp -r ~/.hermes/skills/<name>/ ~/.hermes_prod/skills/<name>/` to
   copy the skill (or `cp` the specific files for non-skill edits)
3. For scripts/launchd: same manual cp
4. For `~/.hermes/config.yaml`: cp + restart gateway (the umbrella
   SKILL.md does describe this part correctly)
5. `cd ~/.hermes && git add -A && git commit && git push origin main`
   to record the change in the git history

**There is no script that does this for you.** You must `cp` manually.

## Concrete worked example: 2026-06-09 cmux-send-submit

When adding the `cmux-send-submit` skill (new SKILL.md + helper
script + tests + 6 skill patches + 1 SOUL.md COMMIT), the actual
sequence was:

1. **Wrong:** I wrote everything to `~/.hermes_prod/skills/...` first
   (opposite of the umbrella's "staging first" rule)
2. **Caught it** by checking the deploy-pipeline skill, which
   referenced `scripts/deploy.sh` — and that file didn't exist
3. **Manual cp from prod → staging** for the 5 files that staging
   actually had (2 staging skills were missing entirely; this is a
   pre-existing condition, see below)
4. **Committed staging:** `cd ~/.hermes && git add -A && git commit
   -m "[Auto] Add cmux-send-submit..."` → commit `74621e7cb3`
5. **No automated prod sync happened.** The agent running NOW
   sees the changes because they exist in prod (where I wrote them
   in step 1). A future agent reading from staging would NOT see
   the changes.

The right way (for next time): write to `~/.hermes/` first, then
`cp` to `~/.hermes_prod/`, then commit staging. This matches the
umbrella's documented intent even if the `deploy.sh` script is missing.

## Staging/prod drift observed on 2026-06-09

The `~/.hermes/skills/` and `~/.hermes_prod/skills/` trees are NOT
identical. Specifically:
- `~/.hermes/skills/ao-babysit/SKILL.md` — does not exist in staging
  (only the `state/` subdir is there). The full SKILL.md is only in
  prod.
- `~/.hermes/skills/hermes/terminal-agent-communication/SKILL.md` —
  the `hermes/` subdir doesn't exist in staging at all.
- Many other skills present in prod but not in staging (per
  `diff <(ls ~/.hermes/skills/ | sort) <(ls ~/.hermes_prod/skills/ | sort)`).

**Net effect:** Staging is incomplete relative to prod. A change
made to staging-only and not manually copied to prod will be
invisible to the running agent.

**Workaround (temporary):** when adding/updating a skill, check
both trees:
```bash
ls ~/.hermes/skills/<name>/SKILL.md 2>/dev/null
ls ~/.hermes_prod/skills/<name>/SKILL.md 2>/dev/null
```
If staging is missing the file, write directly to whichever tree
the running agent reads (prod) and copy to staging afterward.

## The deploy-pipeline contract — what to actually do today

Until a `deploy.sh` script is built (separate task), the contract
is:

1. **Decide which tree the running agent reads from.** Today: prod
   (`~/.hermes_prod/`). SOUL.md is loaded from `~/.openclaw/SOUL.md`
   (separate path), so SOUL.md COMMITs only need to live there.
2. **Write to staging first** (`~/.hermes/`) per the umbrella's
   documented rule, even if the `deploy.sh` script doesn't exist.
3. **Manually `cp` to prod** to make the change live.
4. **Commit + push staging** to keep git history.
5. **Note in the change description** that prod sync was manual,
   so future agents don't expect automation that doesn't exist.

## What's needed to make this match the documented contract

These are deferred work items (separate from this session):

1. **Build `~/.hermes/scripts/deploy.sh`** that does:
   - `cp` from `~/.hermes/skills/` to `~/.hermes_prod/skills/` (with
     rsync --delete to avoid drift)
   - `cp` from `~/.hermes/scripts/` to `~/.hermes_prod/scripts/`
   - Gateway restart if launchd plists changed
   - Optional git push with `--skip-push` flag
2. **Fill in the missing staging skills** (ao-babysit/SKILL.md,
   hermes/terminal-agent-communication/SKILL.md, and the ~80 other
   skills present in prod but not staging)
3. **Update the umbrella SKILL.md** to remove references to the
   non-existent `deploy.sh` and replace with the actual manual-cp
   procedure documented here

These are tracked as open thread (2026-06-09) — the openclaw/mctrl
cleanup track may naturally cover item 2.

## Why this matters

When you make a change to a skill or a SOUL.md COMMIT and the
running agent doesn't pick it up, **the most likely cause is staging
↔ prod drift, not the change itself being wrong**. Diagnose via:
```bash
diff -q ~/.hermes/skills/<name>/SKILL.md ~/.hermes_prod/skills/<name>/SKILL.md
```
If the files differ, copy staging to prod (or vice versa) and
restart the gateway if the change is in a runtime-loaded file.
