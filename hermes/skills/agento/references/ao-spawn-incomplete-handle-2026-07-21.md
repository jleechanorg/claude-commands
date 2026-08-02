---
name: ao-spawn-incomplete-handle-2026-07-21
description: Verified recovery recipe for the 2026-07-21 AO daemon failure mode `SESSION_INCOMPLETE_HANDLE`. Three consecutive `ao spawn --harness codex` (and `claude-code`) registered sessions (`worldarchitect-80/81/82`) but every `ao send` returned `SESSION_INCOMPLETE_HANDLE` — workers stuck at `status:no_signal, activity:idle`, worktrees `locked`. Distinct from the older Codex usage-limit failure covered by `ao-spawn-model-preflight.md`. Companion to the SKILL.md §"AO spawn failure mode — SESSION_INCOMPLETE_HANDLE" entry.
tags: [agento, ao, spawn-failure, session-incomplete-handle, inline-pivot, dispatch-fallback, worktree-cleanup, worldarchitect, 2026-07-21]
---

# AO spawn `SESSION_INCOMPLETE_HANDLE` recovery recipe

Verified 2026-07-21 at 17:14Z on $GITHUB_REPOSITORY issue #8508 dispatch (campaigns `q04GfOEl4SWnEQrFUVST` + `wSm8Z8McTLJ8oQjqlTyJ`). Three consecutive `ao spawn --harness codex` AND `ao spawn --harness claude-code` all exhibited the same harness-binding failure. **Both harnesses affected — not a model-tier problem.** The session IS registered (visible in `ao session ls`) but the runtime/workspace handles are missing, so `ao send` cannot deliver the brief.

## Symptom signature

```text
ao session get <session-id>
  → status: no_signal
  → activity: idle
  → harness: codex        # OR claude-code

ao send --session <session-id> --message "ping"
  → Session is missing runtime or workspace handles (SESSION_INCOMPLETE_HANDLE)
```

Worktree at `~/.ao/data/worktrees/<project>/<session-id>/` is **`locked`** — `git worktree list` shows the branch as checked-out there, blocking any new worktree on the same branch name. Each spawn attempt leaves a dead branch + orphan worktree.

## Why retry fails

The daemon records the session entry but the harness-attachment layer fails. Retrying with a different harness (codex ↔ claude-code) does NOT help — the same code path (session registration) succeeds but the binding step fails identically. Retrying with a different `ao spawn` invocation produces MORE orphan worktrees + dead branches that pollute `git worktree list` and block future worktree creation.

## Recovery recipe (verified, 2026-07-21)

### Step 1 — detect, do NOT retry

```bash
# 1. Confirm the failure on the harness-attachment layer
ao session get <session-id>      # status:no_signal, activity:idle
ao send --session <session-id> --message "ping"   # INCOMPLETE_HANDLE
# 2. Confirm the worktree is locked
git worktree list | grep <session-id>             # shows "locked" marker
# 3. CAP: if 2 consecutive spawn attempts (different harnesses) both fail,
#    pivot to inline. Do not attempt a 3rd.
```

### Step 2 — clean up the orphan worktree + dead branch

Each `ao spawn` attempt left a `~/.ao/data/worktrees/<project>/<session-id>/` directory holding the worktree + branch. Clean up BEFORE creating a new worktree, or `git worktree add` will fail with "branch already checked out":

```bash
# 1. Unlock the orphan worktree (the harness-bound session left it locked)
git worktree unlock $HOME/.ao/data/worktrees/<project>/<session-id>

# 2. Force-remove the worktree entry
git worktree remove --force $HOME/.ao/data/worktrees/<project>/<session-id>

# 3. Prune any stale entries
git worktree prune --verbose

# 4. Delete the dead branch (the harness-attached session owned it but
#    the actual work never happened; the branch has 0 commits beyond origin/main)
git branch -D <branch-name>
```

Verified on 2026-07-21: `worldarchitect-80` orphan at `~/.ao/data/worktrees/worldarchitect/worldarchitect-80` (branch `fix/unbounded-scaling-stale-clear-8508` locked) was cleaned up in 3 commands, freeing the branch for the inline worktree `git worktree add`.

### Step 3 — pivot to inline execution

When the user is in-session and the change is bounded (1-4 files, ≤500 lines, 1 logical commit), do the work directly on a fresh worktree from the canonical checkout. The `dispatch-task` skill's spawn wrapper is irrelevant here — you're already in the session.

```bash
# 1. Create the worktree from origin/main (NEVER from the orphan's dirty state)
cd $HOME/projects/<project>   # canonical checkout
git fetch origin
git worktree add $HOME/projects/wt-<topic> -b fix/<topic>-<issue-N> origin/main

# 2. cd into the worktree for all subsequent work
cd $HOME/projects/wt-<topic>

# 3. Verify the worktree is on the expected branch and clean
git status --short                      # MUST be empty
git rev-parse --abbrev-ref HEAD         # MUST be the new branch
```

### Step 4 — apply the fix (RED → GREEN → commit → push)

Per `$PROJECT_ROOT/tests/test_clear_level_up_lock_flags.py` walk-from-`__file__` repo root resolver pattern:

```bash
# 1. Write the failing test FIRST (use the worktree's own copy)
# 2. Run the test on baseline (expect RED) — proves the bug exists
./vpython -m pytest $PROJECT_ROOT/tests/test_<topic>_<issue-N>.py -v

# 3. Apply the fix to the relevant source files
#    (game_state.py / agents.py / prompts/ etc.)

# 4. Re-run the test (expect GREEN)
./vpython -m pytest $PROJECT_ROOT/tests/test_<topic>_<issue-N>.py -v

# 5. Run the regression sweep (broader cluster tests)
./vpython -m pytest <cluster-test-files> -q 2>/dev/null | tail -5

# 6. Commit + push
git add <files>
git commit -m "[agento] fix: <summary> (#<issue-N>)

<2-3 paragraph body with verified bug class, root-cause, fix shape, test coverage>

Refs: #<issue-N>"
git push origin fix/<topic>-<issue-N>

# 7. Verify the push landed
git rev-parse origin/fix/<topic>-<issue-N>   # MUST match the new SHA
```

### Step 5 — open the draft PR via REST (GraphQL may be rate-limited)

If `gh-safe-publish pr create` fails with `GraphQL: API rate limit already exceeded for user ID 13840161.`, fall back to `urllib.request` POST against the REST API. Verified 2026-07-21 on PR #8509:

```bash
python3 <<'PYEOF'
import json, urllib.request, subprocess
with open("$HOME/.hermes/wa-repro-<N>/pr-body.md") as f:
    body = f.read()
token = subprocess.check_output(["gh", "auth", "token"]).decode().strip()
data = json.dumps({
    "head": "fix/<topic>-<issue-N>",
    "base": "main",
    "title": "[agento] <title> (#<issue-N>)",
    "body": body,
    "draft": True,
    "maintainer_can_modify": True,
}).encode()
req = urllib.request.Request(
    "https://api.github.com/repos/<OWNER>/<REPO>/pulls",
    data=data,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "hermes-agent",
    },
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    d = json.loads(resp.read())
    print("PR_URL:", d.get("html_url"), "PR_NUM:", d.get("number"))
PYEOF
```

### Step 6 — post the diagnostic in Slack + tag the issue

```bash
# Issue comment via REST (GraphQL may be exhausted)
python3 -c 'import json, urllib.request, subprocess; ...'  # mirror Step 5 with /issues/<N>/comments
```

The reply should include:
- Branch URL (`https://github.com/<OWNER>/<REPO>/tree/fix/<topic>-<issue-N>`)
- PR URL (from Step 5)
- Commit SHA (`git rev-parse origin/fix/<topic>-<issue-N>`)
- Diagnosis summary + fix shape
- Explicit note: "AO dispatch attempt failed (SESSION_INCOMPLETE_HANDLE on 3 spawns); work done inline per user steer 'directly investigate it don't use AO'."

## Heuristic: when to pivot vs when to wait for AO

| Task shape | Recommended path |
|---|---|
| 1-3 file change, single commit, ~50 lines | Always inline — `ao` overhead > work |
| Multi-file fix that needs `/es` evidence + pytest loop | **Inline is fine** if the user is actively watching the session and can steer mid-turn |
| Cross-campaign cluster fix with 3+ sub-components | Inline if AO is broken; dispatch when AO is healthy |
| Long-running babysit (CI → green, 30+ min loop) | Dispatch via AO when AO is healthy; otherwise inline with cron babysit |
| Multi-PR fanout (N parallel workers) | Always AO — no realistic inline path |

When AO is healthy, prefer AO for any task that benefits from durable state (the worker can outlive your session). When AO is broken AND the user is in-session AND the change is bounded, inline + cron babysit is acceptable.

## Pitfalls (verified 2026-07-21)

1. **DO NOT keep retrying `ao spawn`.** Each attempt costs ~90s AND leaves a locked orphan worktree + dead branch. Cap at 2 attempts with different harnesses; pivot to inline after that.

2. **DO NOT pre-clean the orphan BEFORE confirming INCOMPLETE_HANDLE.** Sometimes the harness binding is delayed — `ao session get` may show `no_signal` for the first ~30s and then update to `working`. Always send one ping `ao send --message "ping"` and confirm INCOMPLETE_HANDLE before cleanup.

3. **DO NOT create a worktree on the same branch name as the dead one without first deleting the dead branch.** `git worktree add -b fix/<name> <path> origin/main` succeeds even with a dead branch in the way, but `git push` will fail with "branch already exists on remote" if the dead branch was ever pushed. Always `git branch -D <name>` after `git worktree prune` succeeds.

4. **DO NOT skip the regression sweep.** Inline fixes can pass the new contract test but break sibling tests in the cluster. Run the broader pytest sweep BEFORE pushing — `tail -5` of the pytest output gives pass/fail/skip counts. If anything other than `passed` or `skipped`/`xfailed` shows up, fix it before pushing.

5. **DO NOT trust `ao session ls` as proof of working.** A session can be in the list with `status:working` for ~30s before the harness-attachment layer fires. If `ao send` returns INCOMPLETE_HANDLE after that, the harness is broken even though `ls` looks healthy.

## Cross-references

- `~/.hermes/skills/agento/SKILL.md` §"AO spawn failure mode — SESSION_INCOMPLETE_HANDLE" — the SKILL-level entry that this reference file backs up.
- `~/.hermes/skills/repro/references/repro-unbounded-scaling-stale-pending-8508.md` — the bug class this recipe was first verified against (5th canonical-state-anchor sub-class).
- `~/.hermes/skills/dispatch-task/SKILL.md` — the older dispatch skill; the AO failure modes it documents (Codex usage-limit, tmux env overflow, lifecycle polling inactive) are DIFFERENT failure modes from INCOMPLETE_HANDLE.
- `~/.hermes/skills/always-pr-never-local-edit/SKILL.md` — the inline-work policy that overrides the "always dispatch" default when AO is broken.

## Status as of 2026-07-21

Verified inline-pivot on issue #8508 → PR [#8509](https://github.com/$GITHUB_REPOSITORY/pull/8509) (branch `fix/unbounded-scaling-stale-clear-8508`, HEAD `778e705b84`). User steer: *"Directly investigate it don't use AO"* (mid-turn after 3 spawn attempts failed). Fix shipped, push verified, draft PR opened via REST fallback (GraphQL was at 0/5000).