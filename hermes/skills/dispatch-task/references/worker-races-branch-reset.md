---
name: worker-races-branch-reset
description: Why the canonical post-spawn `git checkout -B <clean-name>` race fails when the brief says "create draft PR first", and the durable recovery recipe. Verified 2026-07-14 on $GITHUB_REPOSITORY PR #8385 (campaign-difficulty /repro dispatch). Read when `/repro` or any "create draft PR immediately" brief leaves the worktree on a different branch than the PR head.
---

# Worker races the gateway branch reset (verified 2026-07-14, PR #8385)

**Symptom:** The gateway dispatches `ao spawn -p <project> "<task slug>"` for a task whose brief says "create the draft PR immediately after the issue, then run /repro." The worker reads the brief, **opens the draft PR on the auto-derived branch before the gateway's `git checkout -B <clean-name>` step runs** in the gateway shell. By the time the gateway tries to rename the local branch to a clean slug, the worker's first commit is already on the auto-derived branch (`feat/repro-rmcpapdfuerh8mgruj6n-campaign-difficulty-regression-fu`) and pushed to `origin/<auto>`. The gateway's `git checkout -B repro/<clean>` succeeds against `origin/main` and creates a divergent local branch with no commits. The PR head stays on the auto-derived branch; the worker's later work flows there too. The clean local branch is dead weight.

**Why the canonical Step 4 ("reset branch BEFORE the worker commits") is not enough here:** the canonical recipe assumes the gateway can `git checkout -B` between spawn and the worker's first commit. With `/repro` (or any task that says "create the draft PR immediately as gate 2"), the worker's first commit happens within the same minute as spawn — long before a 60-120s gateway `terminal` call can return and run Step 4. The reset is a delayed, post-hoc cleanup.

**Verified sequence (wa-3280 / PR #8385, 2026-07-14):**

1. `ao spawn -p worldarchitect "Repro RMCPAPdfuErh8MgRuj6n ..."` → `✔ Session wa-3280 created`, branch `feat/repro-rmcpapdfuerh8mgruj6n-campaign-difficulty-regression-fu`
2. Gateway sees the spawn return; runs `git fetch origin <auto>` + `git checkout -B repro/RMCPAPdfuErh8MgRuj6n-difficulty origin/main` in a second `terminal` call.
3. **In parallel**, the worker reads the brief, runs `gh issue create` → #8384, `gh pr create --draft` → #8385, commits `61e15f8bdaac` and pushes. All on the auto-derived branch.
4. Gateway's reset lands on a different branch from where the PR head lives. The `git status --branch --short` shows the gateway's branch "clean" but the PR head branch has 1 commit the gateway never saw.

**Detection (≤30s, do this after EVERY spawn whose brief says "create draft PR first"):**

```bash
PR_BRANCH=$(gh pr view <N> --repo <owner>/<repo> --json headRefName -q .headRefName)
LOCAL_BRANCH=$(git -C "$WT" rev-parse --abbrev-ref HEAD)
PR_HEAD=$(gh pr view <N> --repo <owner>/<repo> --json headRefOid -q .headRefOid)
LOCAL_HEAD=$(git -C "$WT" rev-parse "origin/$PR_BRANCH")
if [ "$LOCAL_BRANCH" != "$PR_BRANCH" ] || [ "$PR_HEAD" != "$LOCAL_HEAD" ]; then
  echo "ALIGNMENT-RACE: worktree on $LOCAL_BRANCH @ $LOCAL_HEAD, PR on $PR_BRANCH @ $PR_HEAD — realign"
fi
```

**Recovery recipe (real-world proven):**

1. **Don't reset to a clean name** — the worker has already named and pushed the branch. Renaming now means re-pushing the PR head, which the worker will fight on its next commit. Live with the auto-derived name if it embeds the bead/issue IDs cleanly.
2. **Realign the local worktree to the actual PR head** — `git fetch origin "$PR_BRANCH" && git checkout -B "$PR_BRANCH" "origin/$PR_BRANCH"`. This makes the local worktree match what the PR actually shows.
3. **Stash + pop the gateway's local edits** if you had any in flight — `git stash push -u -m "gateway-preserve-<sid>-before-pr-head-align"` before the reset, then `git stash pop` after.
4. **Recopy the brief into the worktree** — the `AO-TASK-BRIEF.md` at the worktree root may have been wiped by the checkout. `cp /tmp/<project>/AO-TASK-BRIEF.md "$WT/AO-TASK-BRIEF.md"`.
5. **Re-send the steer** — `ao send <sid> "You are now aligned to the actual draft PR head branch <PR_BRANCH> for PR #N. Continue from AO-TASK-BRIEF.md. Do NOT reset branches again. Commit and push to this exact PR head. Commit + push after every green unit of work; never hold >30 minutes of uncommitted changes."` The "do NOT reset branches again" line is critical — without it the worker will try to honor the brief's branch-reset step and re-fork the branch.

**Pre-spawn mitigation (when you can predict the race):**

If the brief explicitly says "create draft PR first as gate 2", pass the clean branch name AS the task slug instead of relying on Step 4:

```bash
# Instead of:
ao spawn -p worldarchitect "Repro RMCPAPdfuErh8MgRuj6n campaign difficulty regression; full brief /tmp/.../AO-TASK-BRIEF.md"
# Use (slug IS the branch):
ao spawn -p worldarchitect "repro/RMCPAPdfuErh8MgRuj6n-difficulty: campaign difficulty regression. Full brief /tmp/.../AO-TASK-BRIEF.md"
```

The worker's auto-derived branch will be `feat/repro/RMCPAPdfuErh8MgRuj6n-difficulty-campaign-difficulty-reg` (slug-prefix preserved). This is uglier but stable across the race.

**Better long-term fix (requires AO CLI flag):** A `--branch <name>` flag on `ao spawn` that overrides the auto-derivation. Verified absent on this host (`--branch`, `--head-branch`, `--target-branch` all error with `unknown option`). File a bead if you hit this more than 2× — a 1-line CLI patch beats living with the race.

**Cross-reference:** `agento` skill §"Spawn Output — Branch Name Auto-Derivation (always reset)" already documents Step 4's limitation but does NOT cover the race where the worker beats the gateway. This file is the missing durable record.