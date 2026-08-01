# Pre-existing test-failure attribution (stash/reset/restore protocol)

When code removal makes tests fail, distinguish failures you caused from
failures that already existed on `origin/main`. This protocol prevents
the false claim "my PR broke these tests" when the breakage was
pre-existing environment-bound noise.

## When to use

- You deleted a file, function, or configuration that some tests
  reference.
- The deletion will obviously cause some test failures.
- Other failures appear that you're not sure about (might be yours,
  might be pre-existing).
- SOUL.md `same-test-name-rule` requires all FOUR checks before you
  can dismiss a failing test as pre-existing.

## The 5-step protocol

### 1. Capture current changes

```bash
git stash
```

Don't commit yet — you want to be able to restore verbatim.

### 2. Reset to origin/main (clean state)

```bash
git reset --hard origin/main
git log --oneline -1  # confirm HEAD = origin/main HEAD
```

### 3. Run the failing tests on clean main

```bash
.venv/bin/python -m pytest tests/test_X.py::test_specific_failure -v --no-header 2>&1 | tail -25
# capture: exit code, FAILED line, assertion message
```

### 4. Restore the branch + changes

```bash
# If your work was on a PR branch whose origin was deleted:
git checkout -B <branch> refs/remotes/origin/pr/<N>

# If your work was on a normal feature branch:
# git checkout -B <branch> origin/<branch>

git stash pop
git log --oneline -1  # confirm your commit is back on top
```

### 5. Compare results

| Comparison | Conclusion |
|---|---|
| Test FAILS on clean main with identical exit code + identical assertion line as observed during your deletion run | **PRE-EXISTING** — environment-bound or pre-existing bug, NOT caused by your deletion |
| Test PASSES on clean main + FAILS after your changes | **CAUSED BY YOUR CHANGES** — fix or revert |
| Different exit codes or different assertions | **MIXED SIGNAL** — investigate further; one variant may be a flaky test, the other a real regression |

## What to do with the conclusion

### Pre-existing (your deletion is clean)

- Cite the stash/reset verification in the PR summary: "verified failure
  X pre-exists on `origin/main` at commit `<base-sha>` with identical
  output — see `references/pre-existing-failure-attribution.md` for the
  protocol."
- If the failure is genuinely a real pre-existing bug, create a bead
  (`br create ... --type bug`) to track the fix as follow-up work, do not
  conflate with your PR.
- Per SOUL.md `same-test-name-rule` + `qa-test-failure-dismissal-anti-pattern`,
  this protocol satisfies the "explicit same-SHA reproduction" requirement.

### Caused by your changes

- Update the deletion or write a patch that handles the test deletion.
- Do NOT push with deliberate test failures — that hardens into a
  measurable "tests were broken when I merged" smell.

### Mixed signal

- Treat as caused-by-you until proven otherwise.
- Investigate: is the test flaky? Was the previous run cached? Is the
  local environment missing a binary?
- Default to fixing the deletion scope rather than the test (the deletion
  was the action under review).

## Verified cases

### 2026-07-21 — `jleechanorg/dark-factory` PR #407

- Removed 3 workflows + 1 action + 6 tests as part of skeptic-gate
  deletion.
- 4 test failures observed after deletion:
  - 1× `test_invoke_reviewer_nonzero_exit_returns_error` — environment
    (macOS `/bin/false` not in PATH)
  - 3× `test_git_lfs_helper.py::test_consumer_exits_two_when_git_lfs_missing_*`
    — environment (.githooks/post-merge PATH drift)
- Stash/reset verified ALL 4 failures pre-existing on `origin/main`
  with byte-identical output (same SHA + same assertion message).
- PR summary correctly attributed: "Zero new failures introduced by
  deletion." Bead `$USER-pm8f` closed.

## Common pitfalls

### P1 — Don't commit on clean main after the stash

If you run pytest on clean main and then accidentally commit something
before `git stash pop`, you've polluted main. Always `git stash pop`
immediately after pytest, in the same shell session.

### P2 — Don't trust cached pytest results

Stale `__pycache__/` files can mask test changes. Run pytest with
`--cache-clear` if you've deleted or renamed test modules:

```bash
.venv/bin/python -m pytest tests/test_X.py --cache-clear --no-header 2>&1 | tail -20
```

### P3 — Don't skip the protocol because "it's obvious"

Even when you can confidently predict the failure is pre-existing
(env-bound, flaky, unrelated), the protocol gives you **machine-checked
evidence** that survives user pushback and CodeRabbit review. The
proof-by-stash is the strongest available signal short of CI.

### P4 — `git stash` may merge conflicts on stash pop

If the deletion + the clean main have diverged in unrelated ways
(common when working on a long-running branch), `git stash pop` may
conflict. Resolve: take the stashed (your) version for the deletion
files; take clean main for everything else. Or run `git stash show -p`
and re-apply manually after the reset.
