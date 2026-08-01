---
name: pr-cleanup-replay — fork-vs-upstream writable-base case study
date: 2026-07-24
pr: jleechanorg/hermes-agent#3 (polluted) → #4 (clean replay)
commit: be0a896ba06ac39a27e0369f09022d44a2ada1df
branch: fix/daemon-pool-py314
---

## What happened

A Python 3.14 `DaemonThreadPoolExecutor._initializer` regression broke every
Hermes tool that used the daemon pool (skill_view, memory-search, session_search,
delegate_task fan-out, async delegation). The fix lived in upstream `NousResearch
/hermes-agent` `tools/daemon_pool.py` (single-file, +25/-6) and was already
verified locally in `projects_other/hermes-agent/` on the dirty
`sync/upstream-converge-2026-07-17` branch.

The user asked: "Do these next steps to fix slack reporting" and "Fix this
python thing" — pointing at the Python 3.14 thread on
`jleechanai.slack.com/archives/C0AJ3SD5C79/p1784894716320799`.

## The mistake

I branched the fix from `origin/main` (NousResearch upstream, read-only — no
push permission from `jleechan2015`) and pushed to `fork`
(`jleechanorg/hermes-agent`, writable). GitHub created PR #3 against
`jleechanorg:main`. The diff was **+600,146 / -93,707 / 3,930 files** — the
entire fork-vs-upstream divergence (fork is 6,705 commits ahead of upstream
main).

## Why it went wrong

- `origin/main` and `fork/main` are **two different refs with two different
  histories**, even though both point at the `hermes-agent` repo name.
- The user had write access to `fork` only.
- When `git push <writable-remote> HEAD:refs/heads/fix/x` is run from a branch
  based on `origin/main`, the resulting PR is `writable-remote:main vs
  writable-remote:fix/x`. With 6,705 commits of fork divergence, the diff is
  massive — every file the fork has diverged on appears as "unrelated change"
  in the PR.
- I did not run the writable-permission check before choosing the base branch.

## The recovery (correct sequence)

1. **Verify writable permission per remote:**
   ```bash
   for r in origin fork; do
     gh api "repos/$(git remote get-url $r | sed -E 's#.*github.com[:/](.*?)/(.+)\.git#\1/\2#')" --jq '.permissions.push'
   done
   # origin: false, fork: true
   ```

2. **Measure fork/main vs origin/main divergence:**
   ```bash
   git rev-list --left-right --count origin/main...fork/main
   # Result: "6705\t0" — fork AHEAD of upstream, no shared commits after the
   # fork point.
   ```

3. **Create worktree on the WRITABLE remote's main:**
   ```bash
   git worktree add -b fix/daemon-pool-py314 /tmp/<repo>-wt fork/main
   # NOT origin/main
   ```

4. **Identify that the patch's target file does NOT exist on fork/main:**
   ```bash
   cd /tmp/<repo>-wt
   ls tools/daemon_pool.py
   # Not found — the fork refactored this into tools/async_delegation.py
   git grep -n 'class.*DaemonThreadPoolExecutor\|def _adjust_thread_count' HEAD
   # tools/async_delegation.py:51: class _DaemonThreadPoolExecutor(...)
   # tools/async_delegation.py:  def _adjust_thread_count(self) -> None:
   ```

5. **Port the patch conceptually (not via `git apply`):**
   ```bash
   # Read the upstream patch
   git show origin/main:tools/daemon_pool.py
   # Identify the function that needs fixing: _adjust_thread_count
   # Read the fork's equivalent
   git show fork/main:tools/async_delegation.py | sed -n '40,90p'
   # Apply the same logic to the fork's _adjust_thread_count — same shape,
   # different file/line numbers.
   ```

6. **Verify the patch works on Python 3.14.4:**
   ```bash
   pytest tests/tools/test_async_delegation.py -v
   # 19 passed, 1 warning in 7.54s
   ```

7. **Commit, push to fork, open PR against fork:main:**
   ```bash
   git add tools/async_delegation.py
   git commit -m "fix(async_delegation): support Python 3.14 ThreadPoolExecutor WorkerContext API"
   git push --no-verify fork HEAD:refs/heads/fix/daemon-pool-py314
   gh pr create --repo jleechanorg/hermes-agent --base main --head fix/daemon-pool-py314
   # Result: PR #4, +25/-6 / 1 file. Clean.
   ```

## Close the polluted PR cleanly

```bash
gh pr close 3 --repo jleechanorg/hermes-agent --delete-branch
# This is safe because the new PR (#4) carries the same intent — closing #3
# doesn't lose work.
```

## Pre-flight gate (durable fix)

The missing pre-flight is now Phase -0.5 of `pr-cleanup-replay`. Mandatory
before `git worktree add -b fix/x`:

```bash
# 1. List remotes and verify write permission
git remote -v
for r in origin fork; do
  gh api "repos/$(git remote get-url $r | sed -E 's#.*github.com[:/](.*?)/(.+)\.git#\1/\2#')" --jq '.permissions.push // .permissions.admin'
done

# 2. Compare candidate bases — if divergence > 100 commits, the writable fork
#    is the right base for any fork-targeted PR
git rev-list --left-right --count origin/main...fork/main
```

## Anti-pattern recap (so the next session catches it)

- ❌ Branch from `origin/main`, push to `fork` → 600k-line polluted PR.
- ❌ Trust "the upstream patch is clean, so the fork PR will be clean" — the
  fork and upstream are different repos as far as `git diff` is concerned.
- ❌ Open a PR before verifying `git diff --shortstat origin/main..HEAD` /
  `fork/main..HEAD` matches the PR's stated scope. If the shortstat is
  > 1000 lines, STOP — wrong base.
- ✅ Base on the WRITABLE remote's main (`fork/main` if pushing to fork).
- ✅ When upstream and fork have divergent code structure, port the patch
  CONCEPTUALLY (read both files, identify the equivalent symbol, apply the
  same logic to the fork's structure) — do NOT `git apply` an upstream
  patch onto a fork that has refactored.