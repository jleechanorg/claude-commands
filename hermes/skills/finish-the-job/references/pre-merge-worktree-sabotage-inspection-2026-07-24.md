# Pre-Merge Worktree Sabotage Inspection

**Verified 2026-07-24, $GITHUB_REPOSITORY PR #8548 (companion-quest cadence injection, fix commit `ac5d0c400b`).**

The Green Gate workflow, CodeRabbit, the `gh pr view mergeable: MERGEABLE` flag, and `gh pr checks` all evaluate the **COMMITTED head SHA** of the PR branch. None of them inspect the local worktree's working tree. A worktree that has staged-but-uncommitted reverts of a committed fix (or staged deletions of a regression test added at HEAD) will still report a clean, green, mergeable PR — but the moment an agent picks it up, runs `git commit && git push` (or a rebase), or even just `gh pr merge` after a worktree reset, the sabotage lands in main.

This is the local-side analog of `drive-pr-to-green` v2.5.10(b) "race-with-AO-worker" (which catches REMOTE-side races). Green Gate covers the COMMITTED end of the merge path; the WORKING-TREE end is the agent's responsibility.

## The 4-line pre-merge worktree audit

Run BEFORE any `gh pr merge` on a worktree that any prior session has touched:

```bash
cd <worktree>
echo "=== HEAD ==="          && git rev-parse HEAD
echo "=== working diff ==="  && git diff HEAD          # unstaged changes
echo "=== staged diff ==="   && git diff --cached HEAD # staged changes
echo "=== remote tip ==="    && git rev-parse origin/<branch>
```

Interpretation:
- `git diff HEAD` empty AND `git diff --cached HEAD` empty → safe to merge.
- `git diff HEAD` non-empty → the working tree has unstaged edits; investigate before merge.
- `git diff --cached HEAD` non-empty → the working tree has STAGED edits that are NOT in the committed HEAD. **If any of these reverts a regression test added in commits on this branch, STOP.** Discard the sabotage per the recipe below before merging.

## Detection recipe: regressions of tests added in this branch

The dangerous pattern is: a regression test exists at `git show HEAD:<test_file>` but is deleted in the staged/working diff. Detect this before merge:

```bash
# Enumerate test files added/modified in this branch
TEST_FILES=$(git log --diff-filter=AM --name-only origin/main..HEAD -- '$PROJECT_ROOT/tests/*.py' \
  | grep '\.py$' | sort -u)

# For each test file, check if the staged/working diff reverts test methods
for tf in $TEST_FILES; do
  # Get test method names that EXIST in HEAD
  HEAD_METHODS=$(git show "HEAD:$tf" | grep -E '^[[:space:]]+def test_' | sed 's/.*def \(test_[a-zA-Z0-9_]*\).*/\1/')
  # Get test method names in the working file (post-staged+unstaged)
  WORKING_METHODS=$(grep -E '^[[:space:]]+def test_' "$tf" | sed 's/.*def \(test_[a-zA-Z0-9_]*\).*/\1/')
  # Missing methods in working file = deletions
  for m in $HEAD_METHODS; do
    if ! echo "$WORKING_METHODS" | grep -qx "$m"; then
      echo "REGRESSION: $tf is missing test method '$m' in working tree"
    fi
  done
done
```

Or, more directly: `git diff HEAD -- <test_file>` and look for `-    def test_` (test-method deletion) AND `git diff HEAD -- <source_file>` and look for `+        "mvp_site",` (re-introduction of the anti-pattern).

## Discard recipe (verified 2026-07-24)

When the audit surfaces staged reverts of a committed fix:

```bash
cd <worktree>

# Discard the staged reverts (keep the committed fix at HEAD)
git restore --staged <file1> <file2> ...
git checkout -- <file1> <file2> ...

# Verify the working tree now matches HEAD
git status
# Expected: "nothing to commit, working tree clean"
git rev-parse HEAD
# Expected: <same SHA as origin/<branch>>

# Verify the regression test still passes at HEAD
python3 -m pytest <test_file>::<test_class>::<test_method> -v
# Expected: PASSED

# Now safe to merge
gh pr merge <N> --repo <OWNER>/<REPO> --squash --delete-branch
```

## Verified case: PR #8548, 2026-07-24

PR #8548 (companion-quest cadence mirror, `fix/companion-quest-cadence-mirror-8526-clean`). The PR's HEAD commit `ac5d0c400b` fixed a Docker-WORKDIR path bug (codex P1 review) by switching `os.path.join("mvp_site", constants.LIVING_WORLD_COMPANION_CADENCE_PATH)` to `os.path.join(os.path.dirname(__file__), constants.LIVING_WORLD_COMPANION_CADENCE_PATH)` and added a regression test `TestCompanionCadenceInjectionFileContract::test_injection_path_resolves_under_docker_workdir` that pins the source contains the fix AND does NOT contain the anti-pattern.

The PR was 7-green:
- Green Gate: PASS (run #30077520579, verdict `=== GREEN GATE: PASS ===`)
- CodeRabbit: SUCCESS
- Bugbot gate: PASS
- All tests passing
- mergeable: MERGEABLE, mergeStateStatus: CLEAN

The worktree at `~/projects/wt-companion-quests-8526-clean` (which held the branch checkout) had **two staged changes** that would have re-broken the fix:
1. `$PROJECT_ROOT/agent_prompts.py` — reverts `os.path.dirname(__file__)` back to the buggy `os.path.join("mvp_site", ...)` (12 lines changed in staged diff, 5+/7-)
2. `$PROJECT_ROOT/tests/test_living_world_companion_quest_cadence_8526.py` — deletes the `test_injection_path_resolves_under_docker_workdir` regression test (40 lines deleted in staged diff)

Neither change was pushed (so `origin/HEAD == ac5d0c400b` still had the correct fix), but the worktree was in a "sabotage staged" state. The commits on the branch were clean; the worktree was not.

Mitigation (in 4 commands, ~30 seconds):
```bash
cd ~/projects/wt-companion-quests-8526-clean
git restore --staged $PROJECT_ROOT/agent_prompts.py $PROJECT_ROOT/tests/test_living_world_companion_quest_cadence_8526.py
git checkout -- $PROJECT_ROOT/agent_prompts.py $PROJECT_ROOT/tests/test_living_world_companion_quest_cadence_8526.py
git status  # → "nothing to commit, working tree clean"
python3 -m pytest $PROJECT_ROOT/tests/test_living_world_companion_quest_cadence_8526.py -v
# → 17 passed in 0.62s
gh pr merge 8548 --repo $GITHUB_REPOSITORY --squash --delete-branch
# → merge commit 80400c9685 on origin/main
```

Followup: bead `rev-mgju0` / GitHub issue #8563 "REPRO: Staged-but-uncommitted revert of merged PR fix can re-break production" filed to track the harness gap. The structural fix (pre-push hook that aborts if staged changes would REVERT a regression test added in the same branch) is a separate bead.

## `git status` vs `git diff HEAD` vs `git diff --cached HEAD`

The three are not the same. `git status` is the conversational summary (M/A/D/R + staged/unstaged); `git diff HEAD` is the full diff of working tree against HEAD (including both staged AND unstaged changes); `git diff --cached HEAD` is JUST the staged changes. The audit recipe uses both `git diff HEAD` (catches unstaged local edits) and `git diff --cached HEAD` (catches staged-but-uncommitted sabotage) to be exhaustive.

If you only run `git status` and see nothing alarming (no "Changes to be committed" section), you might miss the unstaged edits. Always run `git diff HEAD` for the full diff, not `git status --short`.

## Anti-pattern: trusting `gh pr view mergeable: MERGEABLE` as a green light

`gh pr view --json mergeable,mergeStateStatus` reads from GitHub's view of the PR's `headRefName` + the merge-base commit. It does NOT inspect any worktree. A worktree can have a sabotage-staged state while GitHub happily reports `MERGEABLE+CLEAN` and Green Gate reports PASS. The only signal the agent gets is the local `git status` / `git diff HEAD` audit. If you skip that audit, the sabotage propagates to main on the next merge.

## Anti-pattern: assuming the worktree is a faithful mirror of the branch

Worktrees are long-lived. They can accumulate uncommitted edits from prior sessions that crashed, were killed, or simply never finished a commit. They can also accumulate hand-edits from manual debugging that the agent never reverted. Trust the COMMITTED head SHA (verified via `git rev-parse origin/<branch>`); the working tree is untrusted input that must be audited before merge.

## Class-level rule for future PR-merge drives

**Before any `gh pr merge`:**
1. `git rev-parse HEAD` — confirm you are at the PR branch
2. `git rev-parse origin/<branch>` — confirm the remote is at the same SHA
3. `git diff HEAD` — full diff, must be empty
4. `git diff --cached HEAD` — staged diff, must be empty
5. `git status` — must say "working tree clean"
6. THEN `gh pr merge`

Total cost: 4 commands, 10 seconds. Cost of skipping: a production re-broken bug, post-merge revert PR, or worse.

## Related

- `drive-pr-to-green` v2.5.10(b) "race-with-AO-worker" — REMOTE-side race detection (`git ls-remote` + `git merge-base --is-ancestor`). This reference is the LOCAL-side complement.
- `drive-pr-to-green` v2.5.6 "WORKFLOW_DISPATCH HEAD_BRANCH PITFALL" — another place where the GitHub-side state is misleading (dispatch lands on `main`, not the PR branch).
- `finish-the-job` pitfall "60-min clarify silence is not a license to stop pushing" — both are about taking the right action on the right artifact at the right time; this is the merge-side analog.
- Bead `rev-mgju0` / GitHub issue #8563 — opened in the same session; the long-term prevention (pre-push hook) is a separate bead.
