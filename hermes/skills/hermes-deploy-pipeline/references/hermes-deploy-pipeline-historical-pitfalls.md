---
name: hermes-deploy-pipeline-historical-pitfalls
description: "Historical pitfalls and bug history for the Hermes deploy pipeline that predate the 2026-06-23 umbrella rewrite. Load only when triaging the specific failure modes: 'git commit landed on feature branch, push rejected', 'Qdrant stash CONFLICT noise on git stash pop', 'skill_manage() wrote to prod without staging copy', 'SOUL.md commit on wrong branch'. Absorbed from the older devops/hermes-deploy-pipeline skill (2026-05-21)."
when_to_use: "Use when (a) `git push origin main` returns non-fast-forward because the commit landed on a feature branch, (b) `git stash pop` after pull produces dozens of CONFLICT (modify/delete) entries for qdrant_storage_staging/ paths, (c) you used skill_manage(action='create'/'patch') and the skill now exists in ~/.hermes_prod/skills/ but NOT in ~/.hermes/skills/, or (d) the user reports 'the skill is in prod but not in jleechanclaw repo'."
---

# Hermes Deploy Pipeline — Historical Pitfalls (pre-2026-06-23)

These pitfalls predate the 2026-06-23 umbrella rewrite. They were captured in the older `devops/hermes-deploy-pipeline` skill (2026-05-21, 5KB), which is now archived in `~/.hermes/skills/.archive/`. The current canonical deploy-pipeline SKILL.md covers the modern pipeline (file routing table, deploy.sh, dirty-staging surgical-sync). This reference covers the failure modes that existed BEFORE that rewrite.

## Pitfall 1: Commit on the wrong branch (2026-05-21)

**Symptom:** `git push origin main` rejected as non-fast-forward. The commit landed on a feature branch (e.g. `feat/long-running-harness`) instead of `main`.

**Root cause:** `git commit` uses the current branch. If you don't verify the branch before committing policy changes (SOUL.md, deploy pipeline, etc.), the commit goes to the wrong place.

**Fix:**

```bash
# Verify branch BEFORE committing
git branch --show-current   # must be 'main'

# If on a feature branch, recover:
git checkout main
git pull origin main
git cherry-pick <SHA>
git push origin main
```

**Verified case:** 2026-05-21 SOUL.md commit landed on `feat/long-running-harness`, push to main rejected. The current canonical SKILL.md has an implicit assumption that you're on main; this reference is the explicit reminder.

## Pitfall 2: Qdrant stash CONFLICT noise on `git stash pop` (2026-05-21)

**Symptom:** `git stash pop` after `git pull` produces dozens of `CONFLICT (modify/delete)` entries for `qdrant_storage_staging/` files.

**Root cause:** Qdrant staging storage is ephemeral runtime data, not code. `git stash` saves it, `git pull` brings new commits, `git stash pop` tries to re-apply ephemeral data on top of possibly-removed paths.

**Fix:** The CONFLICT entries are NOISE. They're irrelevant to policy deploys. Drop the stash or `git checkout --theirs` the qdrant paths:

```bash
# Option A: drop the stash entirely (data is ephemeral)
git stash drop

# Option B: keep the stash but resolve all qdrant conflicts to "theirs"
git checkout --theirs qdrant_storage_staging/
git add qdrant_storage_staging/
```

**Why this matters:** agents can spend 5+ minutes manually resolving qdrant CONFLICT entries, thinking they're real merge conflicts. They're not.

## Pitfall 3: `skill_manage()` writes to prod only (2026-05-21 + multiple)

**Symptom:** Used `skill_manage(action='create'|'patch')` to create/update a skill. The skill is in `~/.hermes_prod/skills/<name>/` but NOT in `~/.hermes/skills/<name>/`. Next time `scripts/deploy.sh --system hermes` runs, the prod skill is overwritten by the (missing) staging version, and the prod-only change is lost.

**Root cause:** `skill_manage()` writes to `~/.hermes_prod/skills/` by default (the runtime path), not to `~/.hermes/skills/` (the staging path). The deploy pipeline then DEPLOYS from staging to prod — so a skill that exists only in prod will be deleted on the next deploy.

**Fix:**

```bash
# After skill_manage creates/updates a skill:
mkdir -p ~/.hermes/skills/<category>/<name>/
rsync -a ~/.hermes_prod/skills/<category>/<name>/ ~/.hermes/skills/<category>/<name>/
cd ~/.hermes && git add skills/ && git commit -m "<type>(<scope>): <description>" && git push origin main
```

**Better fix:** write the SKILL.md directly to `~/.hermes/skills/` first, then let `deploy.sh` or explicit copy move it to prod. The current canonical SKILL.md enforces this in step 1 of the contract.

**Verified case:** 2026-05-08 `browser-skill-optimizer` written to prod only via `skill_manage()`. Forgotten about for 3 days, lost on next deploy.

## Pitfall 4: Treat `~/.hermes_prod/` as source of truth (multiple, recurring)

**Symptom:** Agent reads `~/.hermes_prod/skills/<name>/SKILL.md` and treats it as the canonical version, even though the git-tracked source is `~/.hermes/skills/<name>/SKILL.md`. After a deploy, the prod version overwrites the staging version (because `deploy.sh` copies staging → prod), and the canonical content is lost.

**Root cause:** Same as Pitfall 3 — `~/.hermes_prod/` is a DEPLOY TARGET, not a source of truth. The git remote is `jleechanorg/jleechanclaw` and the staging path is `~/.hermes/`.

**Fix:** When in doubt about which path is canonical, run:

```bash
# Verify staging and prod match
diff -r ~/.hermes/skills/<name>/ ~/.hermes_prod/skills/<name>/

# If they differ, the staging version is canonical
cat ~/.hermes/skills/<name>/SKILL.md   # this is the source of truth
```

## Bug history (pre-2026-06-23)

| Date | What happened | Root cause | Reference |
|------|--------------|------------|-----------|
| 2026-05-08 | `browser-skill-optimizer` written to prod only via `skill_manage()` | Forgot to copy to staging after creating | Pitfall 3 |
| 2026-05-21 | SOUL.md commit landed on `feat/long-running-harness`, push to main rejected | Didn't check current branch before committing | Pitfall 1 |
| Multiple | Skills exist in prod but not in jleechanclaw repo | `skill_manage` default path is prod, not staging | Pitfall 3 + 4 |

## Anti-patterns (older framework, still relevant)

- ❌ Writing directly to `~/.hermes_prod/` as primary action
- ❌ Using `skill_manage()` which writes to `~/.hermes_prod/skills/` without also writing to `~/.hermes/skills/`
- ❌ Forgetting to `git push origin main` after committing
- ❌ Treating `~/.hermes_prod/` as source of truth — it's a deploy target only
- ❌ Using `skill_manage(action='create')` and then separately copying — just write to staging first

## Cross-references

- Main `hermes-deploy-pipeline` umbrella SKILL.md — the modern 2026-06-23 rewrite (file routing table, deploy.sh, dirty-staging surgical-sync recipe).
- `references/staging-dirty-surgical-sync.md` (in the umbrella) — the recipe for the "fix already on origin/main, deployed is stale" case.
- `scripts/deploy.sh` — the actual deploy mechanism referenced in both this and the modern umbrella.
- SOUL.md `## COMMIT: staging-first-deploy` — behavioral enforcement of Pitfalls 3 + 4.