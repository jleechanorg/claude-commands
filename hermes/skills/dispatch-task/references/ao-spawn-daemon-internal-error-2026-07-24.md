---
name: ao-spawn-daemon-internal-error-2026-07-24
description: |
  Sixth failure mode for `ao spawn` — the daemon returns `INTERNAL_ERROR` to the
  CLI BUT still inserts the session row into `~/.ao/data/ao.db`. No tmux pane
  ever materializes, no worktree is created, and the bead gets bound to a
  dead-on-arrival session. Multiple retries compound the problem: each retry
  produces a fresh orphan row, and the per-project spawn lock eventually blocks
  further retries silently. This is distinct from the documented "tmux pane
  exhaustion" failure mode (the worktree IS supposed to land); the difference
  is that here the spawn API returns an error and the worktree never lands AT
  ALL. Verified 2026-07-24 on PR #8559 dispatch (bead rev-mj6bx).
created: 2026-07-24
verified: 2026-07-24
verified-on: PR #8559 ($GITHUB_REPOSITORY)
trigger: |
  `ao spawn -p <project> --issue <bead>` returns `Internal server error
  (INTERNAL_ERROR) [request <host>-<id>]` and exits non-zero. Subsequent
  `ao status --json` still reports `state: ready, health: ok` — the daemon
  is still listening. `tmux list-sessions` shows no pane for the new
  session id. `ao session ls --project <project>` shows the session row
  with `status: no_signal` and `isTerminated: false`.
---

# Sixth failure mode: `INTERNAL_ERROR` with session-row created

## Symptom

```
$ ao spawn --project worldarchitect --issue rev-mj6bx --harness claude-code \
    --prompt "tabletop hard-mode generic prompt + minimal backend" \
    --name hmgen
Internal server error (INTERNAL_ERROR) [request jeffreys-macbook-pro.local/PMYtmPaQdL-000094]
# exit_code: 0 (the CLI returns 0 even though it printed an error)
```

But immediately afterwards:

```
$ ao session ls --project worldarchitect
  worldarchitect-129  (1m)  [idle]  worker  rev-mj6bx
```

The session ROW exists in `ao.db` and is bound to your bead. The bead status flips
to `in_progress`. But the tmux pane never materialized:

```
$ tmux list-sessions | grep -E "(129|hmgen)"
# (empty)
```

No worktree at `~/.worktrees/worldarchitect/wa-129/` either. The session is
dead-on-arrival.

## Why retries don't fix it

If you retry the spawn (different `--name`, env wrapper, etc.), the daemon
silently creates ANOTHER orphan row. Verified 6 consecutive retries on
PR #8559 produced 6 orphan sessions bound to bead `rev-mj6bx` (sessions
123-128). After ~6 retries the per-project concurrent-spawn lock can also
trigger incorrectly because the orphan rows count as "active sessions" in
the project registry.

## Diagnostic recipe (run AFTER each spawn error)

```bash
# 1. Are there orphan session rows?
ao session ls --project <project> --json | \
  python3 -c "import sys,json; data=json.load(sys.stdin); \
  [print(s['id'], s.get('status'), s.get('createdAt')) \
   for s in data['data'] if not s.get('isTerminated')]"

# 2. Is there a tmux pane for any of them?
tmux list-sessions 2>&1 | grep -E "<session-id>|<name>"

# 3. Is there a worktree for any of them?
ls -la ~/.worktrees/<project>/ | grep -E "(wa-|<name>)"

# If rows exist but (2) and (3) are empty → sixth failure mode confirmed.
```

## Recovery (the safe subset)

### Step 1: Clean up the orphan rows

```bash
# Kill each orphan session, preserving any created workspace
for s in <orphan-id-1> <orphan-id-2> ...; do
  ao session kill "$s" --project <project>
done
# Output each line will be: session <id> killed (workspace preserved)
```

`workspace preserved` is fine — there is no workspace to preserve for an
orphan row, but the call is idempotent and won't break anything.

### Step 2: Retry the spawn ONCE

```bash
ao spawn --project <project> --issue <bead> --harness claude-code \
    --prompt "<short task summary>" --name <short-slug-20-chars-or-less>
```

If it returns `INTERNAL_ERROR` again, **stop retrying** — the daemon is
in a bad state. Pivot to Step 3.

### Step 3: Drive inline in a manually-created worktree

```bash
# 1. Create the worktree from origin/main (per .cursor/rules/pr-branch-from-main.mdc)
cd ~/projects/<repo>
git fetch origin
git worktree add -b <branch-name> ~/.worktrees/<project>/<short-slug> origin/main

# 2. Work, commit, push, gh pr create — directly in the worktree
cd ~/.worktrees/<project>/<short-slug>
# ... do the work, commit, push ...
git push origin <branch-name>
gh pr create --repo <owner>/<repo> --base main --head <branch-name> --title "..." --body "..."
```

Yes, this bypasses the AO worker / hermes-worker-harness, but the deliverable
(`github.com/<owner>/<repo>/pull/<N>`) is what matters. The supervisor,
babysit, and cmux layers are conveniences, not the goal.

### Step 4: Update the bead

```bash
br update <bead-id> --status in_progress
br update <bead-id> --notes "<PR URL> pushed at <sha>. Spawned inline after AO daemon returned INTERNAL_ERROR for N consecutive retries. Worktree: ~/.worktrees/<project>/<short-slug>."
```

### Step 5: Set up the status-cron babysit

```bash
hermes cron create "20m" --name "<bead-id> status (20m)" \
    --deliver "slack:<channel>:<thread-ts>" --repeat 1
# (use --at 20m, NOT --every — see SOUL.md `one-time-status-cron-on-request`)
```

## Why this is different from the documented failure modes

| Failure mode | Symptom | Worktree created? | Recovery |
|---|---|---|---|
| 20-slot cap | "Spawn rejected: 20 active sessions >= cap" | No | Bump `AO_MAX_CONCURRENT_SESSIONS=25` env var |
| Provider quota block | spawn returns 0, may or may not log | No | Pivot to a different provider CLI |
| Zombies that look active | queue is full but no workers actually running | No | `ao session kill --purge-session` |
| GHA runner saturation | spawn succeeds, worker hangs | Yes | Pivot to local-run contract |
| Tmux pane exhaustion | `ao spawn` returns ✔ Session N created, but tmux pane missing | Yes | `ao session restore` or drive inline in the existing worktree |
| **Sixth mode (this)** | `ao spawn` returns `INTERNAL_ERROR`, session row in `ao.db`, no tmux pane, no worktree | **No** | Kill orphans, drive inline in a manually-created worktree |

## Root cause (hypothesis, not confirmed)

The ao-go daemon's `internal error` surface appears to be triggered when the
spawn request payload exceeds some internal field limit (likely the
concatenation of `--prompt` + `--name` + `--issue` + env vars), causing the
request handler to fail AFTER the session row is inserted but BEFORE the
tmux pane is created. Recovery path: keep the `--prompt` short on the CLI
(send the long brief via `ao send --file` after the spawn), avoid `--name`
collisions, and try the env wrapper only if `ao status --json` shows the
daemon is healthy.

**Mitigation:** prefer the `ao send --file <brief>` steer pattern over
putting the full prompt in `--prompt`. The spawn's positional arg should
be a short branch-derived slug; the long brief goes into the worktree root
as `AO-TASK-BRIEF.md` AFTER the worker is up.

## Verified recovery (PR #8559, 2026-07-24)

After 6 orphan-induced spawn failures, drove inline in
`~/.worktrees/worldarchitect/wa-hardmode` (branched from `origin/main`
at `5285322aa1`). Made the 4-pillar edit (+469 lines / 4 files), ran
the 14 new tests (all green), committed, pushed, `gh pr create` →
[$GITHUB_REPOSITORY#8559](https://github.com/$GITHUB_REPOSITORY/pull/8559).
PR is OPEN + MERGEABLE on first push. Cron `48b01d106f27` (pr8559-status
20m) armed for follow-up.

## Status (2026-07-24)

This failure mode is **not yet fixed** in the ao-go daemon. Apply the
recovery recipe above when you see it. If the failure reproduces on
>2 spawns in a week's window, file a `br create --type bug --priority 1`
bead against the `jleechanclaw` repo titled "AO daemon returns
INTERNAL_ERROR while still creating session row — worktree never
materializes" and link to this reference.
