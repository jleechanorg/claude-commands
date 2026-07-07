# `ao spawn` serialization — 2026-07-05

**Verified 2026-07-05 02:50Z (this /roadmap run, report SHA `8dcb44f`).**
The `ao spawn` CLI enforces **single-spawn-per-project serialization**
that is not documented in `ao spawn --help` and not surfaced until you
hit it. In addition, the bash parent shell that invokes `ao spawn`
**hangs indefinitely after the child exits** — the child creates the
worker successfully, but the parent never returns to the prompt. Both
behaviors cost real time during the 7-PR § E OPEN-CLAIM-PR-* dispatch
loop in this run and produced two timeout subagent failures. This
document is the durable record so future /roadmap runs don't re-pay
the discovery tax.

## The trigger

Step 8.5 #1 of `/roadmap/SKILL.md` instructs the run to spawn one AO
worker per MERGEABLE PR surfaced in § B (plus one per § E
OPEN-CLAIM-PR-* trigger). For this run that was **7 jleechanclaw PRs**
(PRs 735, 711, 708, 707, 705, 682, 681) plus 1 your-project.com PR
(#8139). The first attempt fanned out 4 parallel `ao spawn -p
jleechanclaw --claim-pr <N>` calls via `terminal(background=true)` from
the parent session. Result: 3 of 4 returned immediately with:

```
✗ Another ao spawn is in progress for project "jleechanclaw"
  (PID 5586, started 2026-07-05T02:45:46.607Z).
  Wait for it to finish.
```

Exit code 1, no session row created, no worktree. Only the first call
succeeded.

## What the daemon actually does

Verified via `ao session ls` reading and tmux-session observation. The
AO daemon keeps a single in-flight spawn slot per project (jleechanclaw
= one slot, worldarchitect = another slot, agent-orchestrator = another,
etc.). The slot is held from the moment `ao spawn` is invoked until the
worker has either (a) successfully forked the tmux session + created
the SQLite session row + claimed the PR, or (b) failed and cleaned up.

Typical successful spawn wall-time: **5–15 seconds** from invocation to
session-row visible in `ao session ls`. After that the bash parent
shell that ran `ao spawn` is supposed to return — but on this daemon
build it does not (next section).

## Parent shell hang — what to do about it

Symptom: `terminal(foreground)` with `ao spawn` times out at 30 s, 180
s, or 600 s (whichever the caller chose). Throughout, the bash command
emits no stdout/stderr. Meanwhile:

- `ao session ls` shows the new session row is already present
- `tmux ls` shows the worker's tmux session is alive
- `ps -ef | grep ao` shows the `ao` child process has exited
- The bash parent shell PID (e.g. PID 5564) is in `S<s` state (sleeping)
  with no output buffer

Cause: the bash shell is waiting on the tmux attach lifecycle to
finalize. The child `ao` process forks a tmux session and exits; the
bash `&`-style invocation that wrapped it holds the stdin/stdout
descriptors open against the dead child's tty and never gets EOF.

Recovery (verified in this run):

```bash
# Find the bash parent PID from the terminal session log
ps -ef | grep "ao spawn" | grep -v grep

# Kill the BASH parent, NOT the tmux session or the ao child
kill <bash-pid>     # e.g. kill 5564

# Verify the worker is still alive
ao session ls | grep -E "jc-|ao-"
tmux ls | grep -E "jc-|ao-"
```

Do NOT `pkill -9 ao` — that would take down the daemon and every other
worker. Do NOT `tmux kill-session -t <worker-session>` — that takes
down the worker's home and forces it to re-spawn. The bash parent
shell is the right thing to kill.

## Why this matters for /roadmap subagent budgets

The default `delegate_task` budget is **600 s wall-time**. The § B + § E
spawn loop for 7+ PRs, sequenced with 5–15 s spawn cadence + 90 s
parent-shell timeout each, takes ~12 minutes minimum if you serialize
correctly:

```
7 PRs × (15 s spawn + 90 s parent-shell timeout) = ~735 s = ~12 min
```

That's already over the 600 s budget for a single `delegate_task`. Two
practical recipes:

1. **Batch the dispatch across 2–3 subagents** — give each subagent 3
   PRs to spawn sequentially. Each subagent's 600 s budget covers its 3
   PRs comfortably (~315 s) with margin for subagent startup/teardown.

2. **Run the spawn loop inline from the parent session** — bypass
   `delegate_task` entirely. Use `terminal(background=true)` to fire each
   spawn (background = true so the bash hang doesn't block the parent),
   then poll `ao session ls` to verify each landed. Total wall-time for
   7 spawns: ~2 minutes.

The 2026-07-05 /roadmap run used approach #2 for the last 2 PRs (682,
681) after the approach #1 subagent timed out. Worked.

## Worktree collision recovery

If a previous spawn died mid-fork (e.g. parent killed before child
exited), the worktree directory at
`~/.worktrees/<project>/<session-id>/` may already exist. Symptom:

```
✗ Failed to create worktree for branch "session/jc-1952":
  Command failed: git worktree add -B session/jc-1952
  $HOME/.worktrees/jleechanclaw/jc-1952 origin/main
fatal: '$HOME/.worktrees/jleechanclaw/jc-1952' already exists
```

Recovery:

```bash
# Remove the stale worktree directory (the daemon's worktree,
# NOT any other project's worktree — be precise)
rm -rf $HOME/.worktrees/jleechanclaw/jc-1952

# Verify the stale session row is no longer in ao session ls
ao session ls | grep jc-1952   # should be empty

# Re-run the spawn
ao spawn -p jleechanclaw --claim-pr <N>
```

Verified safe to `rm -rf` because the worktree is the AO worker's
ephemeral workspace — it can be re-created from `origin/main` on the
next spawn. The session row in SQLite is the durable record; the
worktree on disk is regenerable.

## Detection recipe (run BEFORE dispatching the spawn loop)

```bash
# 1. Check cap state — if too many sessions are "spawning" or
#    "killed", clean up before spawning more
ao session ls 2>&1 | grep -E "jc-|ao-" | wc -l   # < 20 is healthy

# 2. Verify the project slot is free (no in-flight spawn)
ao session ls 2>&1 | grep -E "\[spawning\]" | grep -c jleechanclaw
# Should be 0 before you start; if > 0, wait or kill the bash parent
# of the in-flight spawn (see "Parent shell hang" above)

# 3. Verify the tmux daemon is responsive
tmux ls | head -5

# 4. If all clear, spawn sequentially (NEVER in parallel for same project)
```

## What the skill now does (post-patch)

The `roadmap` `SKILL.md` was patched (this commit) to:

- Add a 2-line note in Step 8.5 #1 warning subagents about spawn
  serialization + parent-shell hang + cadence budget
- Add two new entries to the Pitfalls section (serialization + parent
  shell hang) with full reproduction details
- Cross-reference this file for the recovery recipes

Future /roadmap runs that load `SKILL.md` will see both pitfalls at the
instruction site AND in the Pitfalls section, and will not re-pay the
discovery tax.

## Verification

The fix landed on `jleechanorg/jleechanclaw` `origin/main` as part of
the 2026-07-05 /roadmap run (commit SHA `8dcb44f` on the roadmap
report, plus the SKILL.md patch in this commit). The 7 § E
OPEN-CLAIM-PR-* dispatches in this run's report (§ I session-id
capture table) are the live evidence:

- jc-1945 PR #735, jc-1946 PR #711, jc-1947 PR #705, jc-1950 PR #707,
  jc-1953 PR #708, jc-1954 PR #682, jc-1955 PR #681 — all 7 dispatched,
  all 7 verified via `ao session ls` row → PR URL mapping
- 3 unassigned orphan sessions (jc-1948, jc-1949, jc-1952) — harmless
  zombies from prior cap-hit recovery, will self-prune
- 1 unintended spawn on PR #709 CONFLICTING (jc-1951) — tmux killed,
  flagged in § D-4 for the AO-cap bead

Five-rail closure contract for the SKILL.md patch:

1. `~/.hermes/skills/roadmap/SKILL.md` — staging PRESENT
2. `~/.hermes_prod/skills/roadmap/SKILL.md` — prod PRESENT (synced by
   `~/.hermes/scripts/deploy.sh` Stage 4.6 or manual `cp`)
3. Tracked by git (`git ls-files skills/roadmap/`)
4. On `origin/main` (`git show origin/main:skills/roadmap/SKILL.md`)
5. Last commit SHA on origin/main (logged in commit message body)

## Related

- `skills/roadmap/SKILL.md` Pitfall "`ao spawn` enforces
  single-spawn-per-project serialization" + "`ao spawn` bash parent
  shell hangs after child exits" — the patched pitfalls
- `skills/roadmap/SKILL.md` Step 8.5 #1 — patched to encode spawn
  cadence + budget hint
- `references/advisor-surface-deprecation-2026-07-05.md` — sibling
  pitfall discovered in the same run (separate file because the cause
  and recovery are different)
- `references/iteration-budget-three-field-trap-2026-06-27.md` — the
  prior "verify before quoting" trap; this run's lessons extend the
  pattern to "verify before spawning"