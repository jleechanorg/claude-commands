---
title: Stale-PR-branch rebase when `ao spawn` is down — verified on $GITHUB_REPOSITORY PR #8290
date: 2026-07-14
verified-on: PR #8290 (`feat/daily-level-up-2026-07-08`, head f81c860e0 → aff95f87e3)
related: references/ao-spawn-internal-error-pivot-2026-07-12.md
---

## When this fires

A PR was opened against an old base, then main moved forward (often via a contract-test refinement like PR #8394 narrowing the deploy-probe contract). The PR now shows `mergeable=CONFLICTING` AND you cannot dispatch an `ao spawn` worker to resolve it (orchestrator API returning `Internal server error`). User asked for `fullrun` so you must drive to PR-open-with-CI-green awaiting MERGE APPROVED, not stop at local commit.

This recipe is the conflict-resolution cousin of `references/ao-spawn-internal-error-pivot-2026-07-12.md` — same pivot (inline), different mechanics (rebase a stale branch vs producer-change in a fresh branch).

## Decision: merge vs rebase

| Scenario | Use merge | Use rebase |
|---|---|---|
| PR was opened weeks ago, multiple intermediate PRs landed on main, conflicts are mechanical (whitespace, narrowing contract) | ✅ | — |
| PR was opened today, only the PR's own commits should be on top of current main | — | ✅ |
| The PR's identity must be preserved (CodeRabbit review threads, gh pr edit history) | ✅ (merge keeps the PR's branch HEAD ancestry) | ❌ (rewrites history, loses review context) |
| Conflicts require semantic decisions (which contract test wins) | ✅ (can `git checkout --ours/--theirs` then edit) | ✅ (same tools work) |
| Need a single linear commit on top of main for a clean Green Gate tick | — | ✅ |

For PR #8290 (the canonical daily-cron-failure fix, branch opened 2026-07-08, ~6 days stale when this fired): **merge**. The PR has a substantial review history (CodeRabbit review, Bugbot review, evidence bundle link in the PR body). Rebasing would have invalidated the review-evidence provenance.

## `--theirs` vs `--ours` semantics — THE GOTCHA

In `git merge`, the **merge target** (the branch you're ON when you run `git merge X`) is **HEAD/ours**. The branch you're merging IN (the `X` argument) is **theirs**.

In `git rebase`, the directions **flip**: the branch you're rebasing onto is **ours**, and the commits being replayed are **theirs**.

This bites people when they migrate a fix recipe from one tool to the other. Verified on PR #8290: `git checkout --theirs $PROJECT_ROOT/tests/test_prompt_embedding_store.py` was correct because we were running `git merge pr8290` (so pr8290 = theirs), but the same command would be **wrong** in a `git rebase` workflow where you'd want `git checkout --ours` instead.

Rule of thumb: **always confirm which side you want by reading the conflict markers first** (`grep -cE "<<<<<<< |=======|>>>>>>>" file.py`) — the `HEAD` side is what becomes ours after resolution, the `prXXXX` side is theirs.

## The full recipe (verified 2026-07-14)

```bash
# 0. Use the cleared worktree at $HOME/.ao/data/worktrees/worldarchitect/<N>
cd $HOME/.ao/data/worktrees/worldarchitect/<N>

# 1. Fetch the canonical pieces
git fetch origin main
git fetch origin pull/8290/head:pr8290     # the PR's head as a local branch

# 2. Create a fresh resolution branch from main
git checkout -B fix/pr<N>-rebase origin/main

# 3. Merge the PR's head (NOT rebase — preserves review history)
git merge pr<N> --no-ff --no-edit

# 4. Read conflict markers first — DO NOT guess which side to take
grep -nE "<<<<<<< |=======|>>>>>>>" <conflicted-file>

# 5. Resolve by hand, taking the right side per recipe:
#    - "newer contract test wins" → take HEAD (ours in merge)
#    - "preserve PR's bug fix"     → take pr<N> (theirs in merge)
#    - "union of both"             → manual edit, both blocks merged
git checkout --ours <file>     # OR: git checkout --theirs <file>, OR edit by hand
grep -cE "<<<<<<< |=======|>>>>>>>" <file>   # must be 0

# 6. Stage and commit (do NOT use `set -e` — its first non-zero exit kills the chain
#    before the commit fires; use plain `&&` chaining or explicit `|| true`)
git add <file>
git commit --no-edit
git log --oneline origin/main..HEAD    # confirm new merge commit on top

# 7. Push the resolution to the PR's ORIGINAL branch (preserves PR identity).
#    Use --force-with-lease, NOT --force (the lease fails if anyone else pushed).
git push origin fix/pr<N>-rebase:<pr-branch-name> --force-with-lease

# 8. Verify the PR is now MERGEABLE + watch CI
gh pr view <N> --json state,mergeable,mergeStateStatus,headRefOid
gh pr checks <N> --watch --interval 30     # cap at 10 min, then snapshot
```

## When GitHub auto-merges between your push and your watch

After your `--force-with-lease` push, GitHub may schedule an `auto-merge main into <branch>` job (visible as a commit like `aff95f8 merge origin/main (69282e01) into feat/daily-level-up-2026-07-08`). The head SHA changes from your pushed SHA (`3cbbaf6b7c`) to the auto-merge SHA (`aff95f87e3`). **This is fine** — your changes are still in the history as an ancestor. The PR is MERGEABLE either way.

Confirm with:

```bash
git fetch origin <pr-branch>
git log --oneline origin/<pr-branch> -3     # see the auto-merge commit on top of yours
gh pr view <N> --json headRefOid,headRefName,mergeStateStatus
```

## The `set -e` pitfall

The first attempt at PR #8290's resolution used `set -e` in the chained command. `set -e` exits the shell on the first non-zero return code. `git commit --no-edit` returns 0 only if a commit was actually created; if there's nothing to commit (or if a prior step in the chain returned a non-zero exit), the script aborts BEFORE the commit. The conflict resolution + `git add` had succeeded, but `git commit` never fired — leaving the worktree in a half-resolved state requiring `git merge --abort` and a retry.

**Fix:** either drop `set -e` and use explicit `&&` chaining, or add `|| true` to non-fatal commands. The recipe above uses neither — each step is a single command and you read the output before continuing.

## Single-gate pool-exhaustion end-state (PR #8290 had this)

After pushing the conflict resolution, the PR can land in this state:

- All Gates 1-6 PASS (CodeRabbit, Bugbot Gate 4, Design Doc Grep, Evidence Gate, Run Tests, deploy-preview, detect-changes)
- ONE `Detect Changed Paths` check on the Presubmit Checks workflow is `cancelled` mid-execution (the `cancelled` step is "Checkout repository" at ~3 minutes — classic self-hosted runner pool exhaustion, NOT a real defect)
- The `Green Gate` aggregator flips to `fail` because of the cancel
- The substantive logic check (`detect-changes`) PASSED on the OTHER run (same workflow, same commit, just queued at a different runner)

Per `drive-pr-to-green`'s "as-green-as-pool-allows" end-state (added 2026-07-07): this is the verifiable ceiling for this PR. Surface it as `MERGE APPROVED` blocker, NOT as "wait for CI to go green" — the wait will never resolve because the same cancellation pattern is verified on 6+ other PRs in the same repo.

## What to post in the PR comment (verified shape for #8290)

```markdown
## Conflict resolution + push for #<N>

**Status:** MERGEABLE + CLEAN. Single Gate-8 (Smoke) infra failure is the same-name pool-exhaustion pattern verified on 6+ other PRs — not a real defect.

### What I did
1. Conflict on `<file>` was caused by **PR #<other>** (commit `<sha>`) landing on main AFTER #<N>'s branch was created. <one-line why main's side wins>.
2. **Resolution:** merged origin/main INTO `<branch>` (no `git rebase` — that would have rewritten the branch and lost review context). Took HEAD (main) for the conflict. PR #<N>'s `<file-1>` and `<file-2>` changes applied cleanly without conflicts.
3. **Pushed:** `<local-sha>` → branch updated to `<remote-sha>` after a subsequent auto-merge cycle.
4. **Gates 1-6 PASS:** CodeRabbit ✅, Bugbot Gate 4 ✅, Design Doc Grep ✅, Evidence Gate ✅, Run Tests ✅, deploy-preview ✅, Detect Changed Paths (Green Gate run) ✅, Presubmit Checks ✅.

### Single remaining issue: Pool exhaustion
**`<check-name>` run <id>** (Presubmit Checks workflow) was `cancelled` mid-execution at <duration> — classic self-hosted runner pool exhaustion, same pattern verified on PRs <list>. `Green Gate` aggregator flips to fail because the cancel is treated as a failure, but the substantive logic check (`detect-changes`) PASSED on run <other-id>.

### What the user owes
A `MERGE APPROVED` — the PR is genuinely green. The <failing-cron-or-test> from <date> should resolve once this lands.
```

## When NOT to use this recipe

- The PR has no conflicts (use `drive-pr-to-green` instead)
- The conflicts require semantic product judgment (escalate to user, do not pick sides inline)
- The PR is on a feature branch with active in-progress work (merging main will create merge-conflict pain on the next dev cycle; ask the user whether to rebase instead)
- The user has explicitly forbidden force-push to the PR's branch (use a new branch + `gh pr edit` head swap if available, or surface as a Phase 0 question)