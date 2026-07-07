# Staging dirty + new skill just committed — manual skill-mirror recipe

**When `scripts/deploy.sh` won't run because `~/.hermes/` has uncommitted
changes that are NOT yours** (e.g. a separate `auto/commit-pending` branch
in flight, an in-progress slack-thread-roadmap-report plist, a fresh
`instr-audit-*.md` doc) **but you just committed + pushed a new skill to
`origin/main` and need it in prod**, the canonical deploy path is blocked.
This reference documents the surgical skill-mirror recipe that works in
that exact state without touching the unrelated dirty files.

The closest existing recipe is
[`references/staging-dirty-surgical-sync.md`](./staging-dirty-surgical-sync.md),
which covers **fixes already on `origin/main` from a prior session** and
single-file copies via worktree. This reference is the **new-skill-directory
case**: you just made the commit yourself, the skill is fresh in
`~/.hermes/skills/<name>/`, and you need `~/.hermes_prod/skills/<name>/` to
match so the prod resolver serves the new skill at runtime.

## Why `deploy.sh` is the wrong tool here

`deploy.sh` Stage 2 aborts on **any** uncommitted change in `~/.hermes/`,
not just changes that affect the new skill. If a sibling flow
(pre-deploy snapshot, in-flight script change, channel directory mutation)
left the working tree dirty, you cannot run `deploy.sh --skip-push` without
either (a) stashing unrelated work — which the user did not authorize and
which may interact badly with the in-flight flow — or (b) committing
someone else's WIP as a side-effect of your skill push.

The right move is to mirror the new skill by hand, run the Stage 5
health check, and **defer the rest of the deploy** (policy-file sync,
gateway restart, canary) to the next normal deploy window.

## The 5-step mirror (verified 2026-06-23)

### Step 1 — Confirm the new skill is on `origin/main`

```bash
cd ~/.hermes
git fetch origin main
git log --oneline origin/main -1 -- skills/<name>/
# Expect: the new commit's SHA + the feat(skills) commit message
```

If the commit is NOT on `origin/main`, you have a different problem
(skillify was incomplete; go back to the skillify skill → Phase 0 and
re-do the commit + push before continuing).

### Step 2 — Verify staging matches `origin/main` for the new skill

```bash
# Materialize the remote skill directory into a temporary path to perform a clean recursive diff:
mkdir -p /tmp/origin-skills-check
git archive origin/main skills/<name> | tar -x -C /tmp/origin-skills-check
diff -r ~/.hermes/skills/<name>/ /tmp/origin-skills-check/skills/<name>/
rm -rf /tmp/origin-skills-check
# Expect: empty output (staging is clean for this skill, even if the rest of the tree is dirty)
```

If the diff is non-empty, the staging copy is older than `origin/main` —
probably because of a partial commit or a worktree-vs-main mix-up. Re-sync
from origin/main before mirroring:

```bash
cd ~/.hermes
git checkout origin/main -- skills/<name>/
```

### Step 3 — Mirror staging → prod (rsync, NOT `deploy.sh`)

```bash
mkdir -p ~/.hermes_prod/skills/<name>
rsync -a --delete \
  ~/.hermes/skills/<name>/ \
  ~/.hermes_prod/skills/<name>/

# Verify
diff -r ~/.hermes/skills/<name>/ ~/.hermes_prod/skills/<name>/
# Expect: empty output
```

The `--delete` flag is intentional: it removes any stale files in prod
(e.g. an earlier draft of the skill, a test that was renamed) so the prod
copy is byte-identical to the staged + committed version.

### Step 4 — Mirror the RESOLVER.md update

`deploy.sh` Stage 4.5 syncs `CLAUDE.md SOUL.md TOOLS.md HEARTBEAT.md`
(`POLICY_FILES`) only — `skills/RESOLVER.md` is NOT in the list. The new
skill's trigger phrases need to be in **prod's** `RESOLVER.md` for the
gateway to route user phrases to it.

```bash
# Option A: copy the whole RESOLVER.md (only if the new skill is the
# only change)
diff -q ~/.hermes/skills/RESOLVER.md ~/.hermes_prod/skills/RESOLVER.md
# If different, do a targeted section append:
#   - read the new ## <name> section from staging RESOLVER.md
#   - append it to prod RESOLVER.md at the same position
#   - or just `cp` the whole file if the new skill is the only change

# Option B: surgical copy of just the new section
python3 -c "
import re
staging = open('$HOME/.hermes/skills/RESOLVER.md').read()
prod = open('$HOME/.hermes_prod/skills/RESOLVER.md').read()
# Extract the new ## <name> section
m = re.search(rf'^## {re.escape("<name>")}$.*?(?=^## |\Z)', staging, re.MULTILINE | re.DOTALL)
if m and m.group(0) not in prod:
    new_section = m.group(0).rstrip() + '\n\n'
    prod = prod.rstrip() + '\n\n' + new_section
    open('$HOME/.hermes_prod/skills/RESOLVER.md', 'w').write(prod)
    print('appended')
else:
    print('already present or not found')
"

# Verify
grep -c '^## <name>$' ~/.hermes_prod/skills/RESOLVER.md
# Expect: 1 (or more if duplicates, in which case deduplicate)
```

The Python recipe is safer than `cp` for the general case because
`RESOLVER.md` typically has unrelated entries from prior skillify passes
that prod may not have yet.

### Step 5 — Health check (Stage 5 only, skip the rest)

The deploy script's Stage 5 (canary / health check) is a standalone
guard. You can run it without re-running Stages 1-4:

```bash
HERMES_HEALTH_PORT="${HERMES_PROD_PORT:-8643}" \
  bash ~/.hermes/scripts/hermes-health.sh
```

If health check passes, the new skill is live for the running prod
gateway. If it fails, do not restart the gateway — the skill files
themselves are independent of the gateway process, and the failure is
likely a transient LLM/route issue, not a skill problem.

## The closure summary you owe the user

When you ship a skill via this recipe instead of `deploy.sh`, the same-turn
closure MUST contain:

```bash
echo "1. commit on origin/main: $(cd ~/.hermes && git log --oneline origin/main -1 -- skills/<name>/)"
echo "2. staging has it:        $(test -d ~/.hermes/skills/<name> && echo PRESENT || echo MISSING)"
echo "3. prod has it:           $(test -d ~/.hermes_prod/skills/<name> && echo PRESENT || echo MISSING)"
echo "4. prod RESOLVER entry:   $(grep -c '^## <name>$' ~/.hermes_prod/skills/RESOLVER.md) match"
echo "5. staging == prod:       $(diff -rq ~/.hermes/skills/<name>/ ~/.hermes_prod/skills/<name>/ >/dev/null && echo YES || echo DRIFT)"
echo "6. health check:          HERMES_HEALTH_PORT=${HERMES_PROD_PORT:-8643} bash ~/.hermes/scripts/hermes-health.sh (exit $?)"
echo "7. other dirty files:     $(cd ~/.hermes && git status --short | grep -vE 'skills/<name>/' | wc -l | tr -d ' ') (NOT TOUCHED)"
```

The "other dirty files" line is critical: it tells the user what you
deliberately did not touch, so they can see the next deploy window will
still need to clean them up.

## When to use this recipe

- You just committed + pushed a new skill (`feat(skills): <name>`) to
  `jleechanorg/jleechanclaw`'s `origin/main`.
- `deploy.sh` Stage 2 aborts with "Uncommitted changes in `~/.hermes/`" and
  the dirty files are NOT yours.
- The new skill needs to be in `~/.hermes_prod/skills/<name>/` for the
  prod gateway to serve it.
- The user has not explicitly asked for a full deploy + gateway restart
  — they asked to push the skill to origin/main and ship it to prod.

## When NOT to use this recipe

- The dirty files in `~/.hermes/` ARE your changes and you simply haven't
  committed them yet — commit them and let the normal `git push` + `deploy.sh`
  path handle the rest.
- The user explicitly asked for a full deploy ("deploy to prod", "publish
  everything", "run deploy.sh") — even if the dirty files aren't yours,
  ask whether to defer or whether the user wants to clean up first.
- The skill is a Hermes Agent core-file change (NOT a self-contained
  skill in `~/.hermes/skills/`) — those go through
  `~/projects/hermes-agent/` and the `hermes-deploy-pipeline` core-file
  rules, not the skill-mirror path. See the deploy-pipeline umbrella
  skill's "Hermes Agent core-file editing" warning.
- The new skill is in `~/.claude/skills/` (Claude Code user-scope), not
  `~/.hermes/skills/` — those are picked up by Claude Code's skill
  discovery directly without needing a prod mirror. The prod mirror
  matters for the **Hermes gateway** (`~/.hermes_prod/skills/`) which
  serves skills at runtime via its resolver.

## Worked example (2026-06-23 — test-tui-claude-feature-via-cmux)

**The push:** I just shipped the new skill to `origin/main` (commit
`ca701ad421 feat(skills): test-tui-claude-feature-via-cmux — TUI slash
command test path`). Files in the commit: `SKILL.md`, `scripts/test-tui-feature.sh`,
`tests/test_test-tui-feature.sh`, `RESOLVER.md` entry.

**The blocker:** `deploy.sh` Stage 2 aborts with:
```
DEPLOY FAILED: Uncommitted changes in $HOME/.hermes — stash or commit before deploying.
```
The dirty files are NOT mine — they include
`launchd/ai.hermes.schedule.slack-thread-roadmap-report.plist.template`,
`scripts/slack-thread-roadmap-report.sh`, `workspace/SOUL.md`, and a new
`roadmap/instr-audit-dead-code-elimination.md` doc. These look like the
user's regular pre-deploy snapshot for the Tuesday 3pm PT window. Per
deploy-pipeline's "do not stash or commit unrelated work" rule, the
right move is the surgical mirror.

**The mirror execution:**

```bash
# Step 1: confirm on origin/main
cd ~/.hermes && git fetch origin main
git log --oneline origin/main -1 -- skills/test-tui-claude-feature-via-cmux/
# → ca701ad421 feat(skills): test-tui-claude-feature-via-cmux — TUI slash command test path

# Step 2: staging matches origin/main for the new skill
mkdir -p /tmp/origin-skills-check
git archive origin/main skills/test-tui-claude-feature-via-cmux | tar -x -C /tmp/origin-skills-check
diff -r ~/.hermes/skills/test-tui-claude-feature-via-cmux/ /tmp/origin-skills-check/skills/test-tui-claude-feature-via-cmux/
rm -rf /tmp/origin-skills-check
# → (empty, clean)

# Step 3: rsync to prod
rsync -a --delete \
  ~/.hermes/skills/test-tui-claude-feature-via-cmux/ \
  ~/.hermes_prod/skills/test-tui-claude-feature-via-cmux/
# → skill files now in prod

# Step 4: update prod RESOLVER.md (the new entry was the only change to RESOLVER.md)
# Safe to `cp` because the only RESOLVER.md change in the commit was the new entry
diff -q ~/.hermes/skills/RESOLVER.md ~/.hermes_prod/skills/RESOLVER.md
# → different → cp is safe
cp ~/.hermes/skills/RESOLVER.md ~/.hermes_prod/skills/RESOLVER.md

# Step 5: health check
HERMES_HEALTH_PORT=8643 bash ~/.hermes/scripts/hermes-health.sh
# → (if gateway responds healthy, the new skill is reachable)
```

**The followup I owed the user:** an explicit "other dirty files: 4 NOT TOUCHED"
line in the closure summary, with the file paths and the recommendation
that they be handled in the user's normal Tuesday 3pm PT deploy window.

## Cross-references

- [`references/staging-dirty-surgical-sync.md`](./staging-dirty-surgical-sync.md) — the
  sibling recipe for **fixes already on `origin/main` from prior sessions** and
  single-file copies. This new recipe is for **brand-new skill directories**.
- [`references/policy-files-skill-sync-gap.md`](./policy-files-skill-sync-gap.md) — the
  underlying "why `deploy.sh` doesn't sync skills" gap. The recommended
  fix (Option B: add Stage 4.6) is still not implemented; this recipe is
  the manual workaround for Option C.
- [`references/find-actually-running-source.md`](./find-actually-running-source.md) — the
  3-place Hermes source layout (staging, prod runtime, pip-installed
  editable) and the "is the fix actually live?" probe that comes after
  the mirror.
- Parent skill: `../SKILL.md` — the "Anti-Patterns" section already has
  a bullet for "Skills and RESOLVER.md are NOT in POLICY_FILES"; this
  reference extends that to the **staging-dirty** case.
- Companion skill: `skillify` → "Anti-Pattern: Deploy.sh POLICY_FILES
  Gap Silently Leaves Skills Out of Sync" — the skillify-side view of
  the same gap.
