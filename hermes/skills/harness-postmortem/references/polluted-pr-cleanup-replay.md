# Polluted PR Cleanup & Replay (2026-07-14)

The detection + recovery recipe for a **polluted PR** — one whose branch carries another PR's full history (beads drift, CI fixes, merge chains, unrelated feature commits) when the PR body's stated scope is a focused fix.

This is the third distinct "fix is in the wrong place" failure class (alongside Phase 1.5 "fix stranded on branch" and Phase 1.5b "fix documented but unreachable").

## Why this class matters

When the agent picks `git merge --no-ff origin/<other-feature-branch>` instead of `git cherry-pick -x <single-sha>` or `git show origin/<branch> -- <files> | git apply`, the resulting branch carries **every commit on the merged branch** — not just the load-bearing fix. The pattern is **silent**: every individual commit message looks clean ("Merge remote-tracking branch", "fix(beads): resync issues.jsonl", "[fixpr jleechan2015-automation-commit]") so `git log --oneline` does not flag anything. The cumulative diff is >2x the load-bearing fix.

It violates `.cursor/rules/pr-branch-from-main.mdc` step 1: *"Create or reset the branch from `origin/main`, e.g. `git checkout -B <branch> origin/main`. Do not stack unrelated work."*

## Detection — three cheap checks before any push or merge

```bash
# 1. Diff stat — what's the scope?
git diff --shortstat origin/main...HEAD
# For a 2-file focused fix: expect <1000 lines, <10 files
# For a PR titled "[scope] fix(specific bug)": expect ONE logical change
# If the diff stat is >1000 lines for a "fix specific bug" PR, the PR is probably polluted

# 2. Commits vs origin/main — are they all related to the PR scope?
git log --oneline origin/main..HEAD
# Watch for: "Merge remote-tracking branch", "[fixpr ...]", "fix(beads)",
# "chore(deps):", "refactor: extract ...", or any commit whose message
# does not match the PR title/body

# 3. Branch base — is the branch from origin/main or from another feature branch?
git log --oneline origin/main..HEAD | wc -l  # many = came from a long-lived branch
git merge-base origin/main HEAD
# If HEAD has many commits not on origin/main, the branch was created
# from a non-main base. Expected for clean replay: 1-3 commits.
```

If any check fails, the PR is polluted. Recovery procedure below.

## Recovery — clean replay as a new PR

### Step 1: Close the polluted PR with a cross-reference

```bash
gh pr close <polluted_pr_number> --comment "Closing in favor of clean replay #<new_pr_number>.
Original PR inadvertently pulled <K> unrelated commits (merge chains, beads drift,
CI fixes). The clean replay contains only the load-bearing fix in <J> files."
```

**Why close instead of force-push:** the user's audit trail of the original PR is valuable. Force-pushing erases the diff that exposed the bloat in the first place.

### Step 2: Create a fresh worktree from origin/main

```bash
cd <project-root>
git worktree add -b fix/<topic>-replay /tmp/wt-<topic> origin/main
cd /tmp/wt-<topic>
```

### Step 3: Identify load-bearing commits via Strategy A or Strategy B

**Strategy A — Cherry-pick individual commits.** Use when the polluted PR's history contains 3-5 distinct commits whose messages match the PR scope, plus noise.

```bash
# Identify the load-bearing commits (skip merge/auto/CI/beads commits)
git log --oneline origin/main..origin/<polluted-branch> --no-merges \
  --grep='^fix' --grep='^feat' --grep='^chore(<scope>)'
# Note the SHAs in chronological order

# Cherry-pick load-bearing commits only
cd /tmp/wt-<topic>
git cherry-pick -x <sha1> <sha2> <sha3>
# Resolve any conflicts; if a conflict is structural (different file shapes),
# skip it and apply the change manually via patch.
```

**Strategy B — Extract the file diff directly.** Use when the polluted PR's history is entirely noise (only merge commits + beads drift) but the file-level diff IS the fix.

```bash
# Identify the load-bearing files
git diff --name-only origin/main...origin/<polluted-branch>

# In the fresh worktree from origin/main:
cd /tmp/wt-<topic>
git show origin/<polluted-branch> -- <file1> <file2> > /tmp/load_bearing.patch
git apply /tmp/load_bearing.patch
# Verify the patch applies cleanly; resolve any fuzz/rejects manually.
```

**Strategy A → B pivot is normal.** Cherry-pick conflicts on rebased branches are common; extracting the file diff directly is often cleaner. If `git cherry-pick` produces structural conflicts, fall back to Strategy B.

### Step 4: Run tests in the fresh worktree

```bash
# Run the load-bearing test file (or full suite for the touched module)
pytest <test_path> -v
# Expect: ALL tests pass; no new failures introduced

# If a test that was passing on origin/main now fails, the cherry-pick missed a
# dependency or extracted the wrong diff. Go back to Step 3.
```

### Step 5: Commit + push + open new PR + verify

```bash
cd /tmp/wt-<topic>

# Single clean commit on the fresh branch
git add -A
git commit -m '[<scope>] <one-line summary> (#<orig_issue>)' \
  -m '<multi-line description matching the PR body scope>'

# Push and create the new PR
git push -u origin fix/<topic>-replay
gh pr create --base main --head fix/<topic>-replay \
  --title '<same title as the polluted PR>' \
  --body '<updated body, link the polluted PR + issue, explain the cleanup>'

# Verify
gh pr view <new_pr_number> --json additions,deletions,changedFiles
# Expect: small numbers; 2-5 files typically, <1000 lines diff
gh pr view <polluted_pr_number> --json state
# Expect: "CLOSED"
```

## Anti-patterns

- **Do NOT force-push to the polluted branch** — that would race with any in-flight CR or CI. Open a new branch instead.
- **Do NOT delete the old branch immediately** — leave it for 24h in case CI/CR feedback needs to be cross-referenced. Cleanup cron will reap it.
- **Do NOT absorb the cleanup into the polluted PR's commits** — `git rebase -i` will lose the audit trail. Close and replay.
- **Do NOT skip Strategy A because cherry-pick conflicts** — try B if A fails. Both are valid; A preserves commit messages, B preserves file content.
- **Tests can pass on the polluted PR but fail on the clean replay** — this means the pollution was carrying a hidden test fix that needs to be a separate commit. Add it as a follow-up commit and link it in the PR body.

## Prevention — the pre-push audit

Per SOUL.md `## COMMIT: pr-clean-branch-from-main-no-history-bloat`, before any `git push` or `gh pr create`, run:

```bash
# 1. Branch base check
git log --oneline origin/main..HEAD | wc -l
# Expected: 1-3 commits for a focused PR; >5 means the branch came from another feature branch

# 2. Diff stat budget check
git diff --shortstat origin/main
# Expected: <1000 lines for non-docs PRs touching $PROJECT_ROOT/

# 3. Forbidden commit pattern check
git log --oneline origin/main..HEAD | grep -E "Merge remote-tracking branch|\[fixpr |fix\(beads\)"
# Expected: empty (no forbidden patterns)

# If any check fails, abort the push and replay clean per this recipe.
```

## Originating incident (2026-07-14)

- **Polluted PR:** [#8401](https://github.com/$GITHUB_REPOSITORY/pull/8401) — 22 commits, 31 files, +1413/-629. Branched from `origin/feat/fix-xp-overflow-no-level-up-7931-full-brief-at-tmp-wa-task-i` (PR #7952's branch).
- **Diagnosis:** `git log --oneline origin/main..origin/fix/visenya-v8-stuck-lu-8400` showed 19 of 22 commits were noise. The load-bearing commits were only 3.
- **Clean replay PR:** [#8403](https://github.com/$GITHUB_REPOSITORY/pull/8403) — 1 commit, 2 files, +597/-20. Used Strategy A (cherry-pick the 3 load-bearing commits, resolve conflicts), then added 1 surgical change for the `level_up_complete` guard, ported `test_xp_overflow_level_up_ceremony.py`, added `TestCustomLevelCapXpOverflow` with Visenya V8 fixtures.
- **Harness fix:** [jleechanclaw PR #780](https://github.com/jleechanorg/jleechanclaw/pull/780) — added SOUL.md `## COMMIT: pr-clean-branch-from-main-no-history-bloat` + companion skill `pr-cleanup-replay` + contract test `test_pr_clean_branch_contract.py` (5/5 pass).
- **User feedback (verbatim):** "Seems like this wasnt made from a clean branch from origin/main? lets run /learn and /skillify and /harness how do we make you stop screwing up"

## Related

- SOUL.md `## COMMIT: pr-clean-branch-from-main-no-history-bloat` — the trigger-based rule
- Skill `~/.hermes/skills/pr-cleanup-replay/SKILL.md` — the recipe
- Test `~/.hermes/skills/pr-cleanup-replay/tests/test_pr_clean_branch_contract.py` — 5 contract tests
- `.cursor/rules/pr-branch-from-main.mdc` — the project-level rule this skill operationalizes