# Staging dirty + new clean PR needed — quarantine the unrelated work

**When the source-of-truth clone (`~/.hermes/` worktree or `project_jleechanclaw/jleechanclaw/`) has UNRELATED dirty work sitting on disk** — files modified by prior sessions, a `memory.db` from a prior auto-commit-pending run, partial Rust crate work, doctor.sh tweaks that never landed — **AND you need to open a NEW clean single-file PR**, the standard `git worktree add -b <new> origin/main` will fail or create a polluted branch with the unrelated history.

Verified 2026-07-21, jleechanclaw source-of-truth clone: 27 unrelated dirty files blocked opening a clean SOUL.md compression PR. The recipe below sidesteps the dirty-state problem entirely — the unrelated work stays recoverable on the original branch, the new PR is born clean from `origin/main`.

This is the sister recipe to `references/staging-dirty-surgical-sync.md`:
- **surgical-sync** = "fix is already on origin/main, I need to deploy it without a new PR"
- **quarantine-stash** = "I need a clean PR, but the worktree has unrelated dirty files I must not pollute the PR with"

## The diagnostic — how do you know you need this recipe?

```bash
cd $HOME/project_jleechanclaw/jleechanclaw  # the source-of-truth clone for ~/.hermes/
git status --short | wc -l       # how many entries? 0 = clean. >0 = dirty.
git log --oneline origin/main..HEAD  # any commits on the local branch ahead of origin/main?
```

If `git status --short` shows entries from UNRELATED sessions and you want to open a PR containing ONLY your change, the quarantine applies.

**Three bad states this recipe handles:**

| State | Symptom | What breaks |
|---|---|---|
| Many `MM`/`AD`/`??` entries from prior sessions | `git status --short` shows >5 entries unrelated to current task | `git worktree add` would either inherit the dirty state or fail |
| An old fix-branch with merged-in history | `git log origin/main..HEAD` is non-empty | `gh pr create` carries that history into your new PR |
| A long-lived `auto/commit-pending` branch with cron artifacts | `git branch --show-current` shows `auto/commit-pending` | Direct push to a clean branch would lose the cron history |

## The recipe (3 steps)

### Step 1 — Quarantine the dirty work to a stash (recoverable, not deleted)

```bash
cd $HOME/project_jleechanclaw/jleechanclaw

# Make sure git is configured (one-time)
git config user.email "$USER@users.noreply.github.com"
git config user.name "jleechanclaw-bot"

# Stash everything dirty (tracked + untracked), with a self-documenting message
git stash push -u -m "STASH pre-<purpose> YYYY-MM-DD — N unrelated dirty files. To recover: git stash pop. Source-thread: <slack-link>"
```

The `-u` flag includes untracked files (`.claude/worktrees/`, `scratch/`, `memory.db`, etc.). Without `-u`, untracked dirty files would silently remain unstashed.

The message convention (`STASH pre-<purpose> YYYY-MM-DD — N files`) makes the stash discoverable months later when someone runs `git stash list` and sees a stream of identically-named entries.

### Step 2 — Create a clean worktree from `origin/main`

```bash
git worktree add -b chore/soul-md-compress-30pct /tmp/wt-<purpose> origin/main
cd /tmp/wt-<purpose>
git log --oneline origin/main..HEAD    # MUST be empty
git rev-parse HEAD                      # MUST be origin/main's tip
```

The clean worktree at `/tmp/wt-<purpose>` is your PR-development playground. Make your edits here, commit, push, open PR.

### Step 3 — Recover the stashed dirty work (after the PR is opened)

The unrelated dirty work should land on the original branch (or a separate worktree on that branch), NOT pollute your new PR. Two options:

**Option A — recover to the original branch** (for ongoing development):
```bash
cd $HOME/project_jleechanclaw/jleechanclaw
git checkout <original-branch>          # the branch you were on before stashing
git stash pop                           # apply the stash back where it belongs
# Resolve any merge conflicts that emerged from the stash-vs-clean state
```

**Option B — orphan the dirty work in a separate worktree** (if the original branch should die):
```bash
# From the origin/main worktree, create a feature branch from the stash ref:
git checkout -b feat/capture-prior-dirty-work <stash-commit-sha>
git stash pop
# Commit, push, open a SEPARATE PR for the dirty-work recovery (do NOT
# bundle into your compression PR).
```

**Option C — accept the stash as orphaned, log it for later** (if the dirty work was from a prior session that never landed):
```bash
git stash list    # note the stash ref and message; do NOT delete the stash
# Future sessions can `git stash apply stash@{N}` if they need to investigate
```

For verified 2026-07-21 SOUL.md compression, **Option A** was used: the 27 dirty files were stashed, the compression PR opened clean, and the user can `git stash pop` on `fix/agent-orchestrator-mislabeled-project-blocks` whenever they want to recover the unrelated work (Rust crates, doctor.sh edits, etc.).

## Pitfalls

### Don't `git reset --hard` to "clean" the dirty state

Resetting wipes the dirty files entirely. They were made by a prior session for a reason, even if that reason is "in-progress jclaw-cliff work." If you `reset --hard`, those files are gone forever. The user will lose work.

`git stash` is the safe alternative: recoverable, named, dated.

### Don't include the stashed files in your PR commit

After stashing, `git status --short` should be empty in your clean worktree. Verify before committing:

```bash
cd /tmp/wt-<purpose>
git status --short                  # MUST be empty
ls workspace/SOUL.md                # verify your single file exists
```

If anything shows up besides your single-file edit, you accidentally inherited something from the parent branch — stop, re-check the worktree creation step.

### Don't use `--keep-index` or `--include-untracked` incorrectly

`git stash push` defaults are `--keep-index=false --include-untracked=false`. If you pass `-u`, untracked files are included. If you stash from a directory with `.gitignore`d files you DO want to recover (like `workspace/SOUL.md`), those will NOT be stashed (gitignore wins even in stash). Pre-flight with:
```bash
git status --ignored --short
```

### Don't bundle dirty-work recovery into your compression PR

The temptation when you have unrelated dirty files lying around is "while I'm at it, let me also commit doctor.sh…". Don't. The `pr-clean-branch-from-main-no-history-bloat` and `never-push-onto-someone-elses-pr-head` rules in SOUL.md explicitly prohibit this. One PR = one logical change. Open a second PR (Option B above) for the unrelated dirty work if it deserves to live.

### Don't lose the stash ref by accident

`git stash drop` (manual) or `git stash clear` removes stashes permanently. The default behavior of `git stash pop` (no args) is to drop the stash ONLY if the pop applies cleanly. Conflicts abort the pop. Both are fine. But:
- `git stash apply stash@{0}` does NOT drop (safer than pop when recovering)
- Always run `git stash list` before any `drop`/`clear` op to confirm what you're touching

## Verified worked example (2026-07-21)

**Setup:** source-of-truth clone `$HOME/project_jleechanclaw/jleechanclaw/` on branch `fix/agent-orchestrator-mislabeled-project-blocks` with 27 dirty files:

```
AD .github/workflows/ab-compare.yml
MM .github/workflows/hermes-pr-tag-listener.yml
A  Cargo.lock
A  Cargo.toml
MM agent-orchestrator.yaml
A  crates/abcompare/Cargo.toml
A  crates/abcompare/src/main.rs
A  crates/worldarchitect-hourly-pr-report/Cargo.toml
A  crates/worldarchitect-hourly-pr-report/src/main.rs
A  docs/rust-port-and-ab-harness/RUNBOOK.md  (+ HTML)
M  memory.db
MM scripts/doctor.sh
MM scripts/hermes-health.sh
MM scripts/launchd-env-wrapper.sh
MM scripts/worldarchitect-hourly-pr-report.sh
MM skills/skillify/SKILL.md
AD tests/worldarchitect-hourly-pr-report/fixtures/mock_gh_api.py
AD tests/worldarchitect-hourly-pr-report/fixtures/mock_prs.json
AD tests/worldarchitect-hourly-pr-report/run_ab.sh
MM workspace/AGENTS.md
MM workspace/SOUL.md
?? .claude/worktrees/
?? scratch/
```

**The user request:** compress `~/.hermes/workspace/SOUL.md` by ~30%. The compression must land in a clean PR with `workspace/SOUL.md` as the ONLY changed file.

**The conflict:** 26 of those 27 dirty files are unrelated to SOUL.md (Rust crate work, doctor.sh updates, memory.db from prior session). A `git worktree add -b chore/soul-md-compress origin/main` succeeds (it doesn't require clean state, just a different branch), but a naive approach would commit all 27 files together — `pr-clean-branch-from-main-no-history-bloat` failure mode.

**The recipe execution:**

```bash
cd $HOME/project_jleechanclaw/jleechanclaw
# Quarantine
git stash push -u -m "STASH pre-SOUL-compress 2026-07-21 — 27 unrelated dirty files (Rust crates, doctor.sh updates, memory.db, etc.). Run 'git stash pop' to recover. Branch user: see Slack thread C0BDEAJH8PK/p1784653229838839."
# Output: Saved working directory and index state On fix/agent-orchestrator-mislabeled-project-blocks: STASH pre-SOUL-compress 2026-07-21 — 27 unrelated dirty files…

# Verify clean
git status --short    # empty (only the 3 unignored worktrees/* entries already excluded by -u)

# Build the clean PR worktree
git worktree add -b chore/soul-md-compress-30pct /tmp/wt-soul-compress origin/main
cd /tmp/wt-soul-compress
git log --oneline origin/main..HEAD    # empty
git rev-parse HEAD                     # 0fe623a744 (origin/main tip at the time)

# Apply compression
cp /tmp/soul-compressed-preview.md workspace/SOUL.md
git add -f workspace/SOUL.md           # -f because workspace/ is gitignored
git commit -m "chore(soul): compress SOUL.md ~30% (105KB → 73KB)…"
git push -u origin HEAD:refs/heads/chore/soul-md-compress-30pct

# Open PR
gh pr create --title "chore(soul): compress SOUL.md ~30%…" --body-file /tmp/pr-body.md
# → https://github.com/jleechanorg/jleechanclaw/pull/789

# Stash is still alive for later recovery
git -C $HOME/project_jleechanclaw/jleechanclaw stash list
# stash@{0}: On fix/agent-orchestrator-mislabeled-project-blocks: STASH pre-SOUL-compress 2026-07-21 — 27 unrelated dirty files…
```

**Result:**
- PR #789: 1 file, +89 / −83 lines, clean 1-commit diff.
- 27 unrelated dirty files stashed, recoverable anytime via `git stash pop` on the original branch.

## When to use this recipe

- Source-of-truth clone has unrelated dirty work AND you want a clean single-file PR
- `auto/commit-pending` branch accumulated cron state and you want to open a feature PR cleanly
- The dirty work is from prior sessions and you don't know what it is — don't `reset --hard`, stash it and ask later

## When NOT to use this recipe

- The dirty work IS your actual task — then `git add` and commit it as-is.
- You want to recover the dirty work in the same PR — use Option B above (separate feature branch + separate PR).
- Staging is on `origin/main` already and clean — no quarantine needed, just create your worktree and PR directly.
