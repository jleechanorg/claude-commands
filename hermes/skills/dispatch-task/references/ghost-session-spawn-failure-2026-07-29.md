# Ghost-session spawn failure mode (verified 2026-07-29)

**Bead:** `$USER-a4m`
**Channel:** `C0AJ3SD5C79` (#jleechanclaw), parent thread `1784894565.689769`
**Project:** `jleechanorg/jleechanclaw` (45 open PRs at the time)
**Session:** `jleechanclaw-29` — registered but never spawned a worker

## TL;DR

`ao spawn` can register a session in `ao session ls` (state goes `[idle]` → `[no_signal]` over 1-2 minutes) WITHOUT actually creating the tmux session or worktree directory. Subsequent `ao send` calls return `MESSAGE_TOO_LONG` errors to a non-existent consumer. **Do not trust `ao session ls` alone** — verify the tmux session and worktree directory exist before treating a dispatch as live.

## Symptom signature

| Layer | State | Reads as |
|---|---|---|
| `ao spawn --project jleechanclaw --prompt "..."` | exit_code=124 (timeout) | Looks like the documented "timeout = success in progress" pitfall |
| `ao session ls -p jleechanclaw` | shows `jleechanclaw-29 (1m) [idle] worker` | Looks like the session landed |
| `ao session ls -p jleechanclaw` (2 min later) | shows `jleechanclaw-29 (2m) [no_signal] worker` | Looks like the worker is idle |
| `tmux list-sessions \| grep jleechanclaw-29` | **NO MATCH** | Other projects' tmux sessions show up (e.g. worldarchitect wa-3427..wa-3430) but not jleechanclaw-29 |
| `ls -la ~/.worktrees/jleechanclaw/jleechanclaw-29/` | **No such file or directory** | Worktree was never created |
| `ao send --session jleechanclaw-29 --message "..."` | `Message is too long (MESSAGE_TOO_LONG)` | Worker is NOT there to consume |

## Why this matters

The existing pitfall in this skill says: "`ao spawn` timeout is NOT a spawn failure — always verify with `ao session ls -p <project>`." That pitfall covers the case where the spawn IS landing, just slowly. The ghost-session case is the OPPOSITE: the session appears in `ao session ls` but never lands. Following the existing pitfall naively (trust the registration, send the brief) wastes quota on `ao send` calls that go nowhere, and the user's task never gets worked on.

## Diagnostic sequence (the 3-step gate)

Before treating any `ao spawn` as live, ALL THREE must pass:

```bash
# 1. Session registered (already covered by existing pitfall)
ao session ls -p <project> | grep <session-name>
# Expect: jleechanclaw-29 (Nm) [<state>] worker

# 2. Tmux session EXISTS — look for hash-prefixed name pattern
tmux list-sessions 2>&1 | grep -E '<session-name>|[0-9a-f]{12}-<session-name>'
# Expect: e.g. 953501c04ccc-jleechanclaw-29: 1 windows (created ...)
# If only OTHER project tmux sessions appear, the new one never spawned.

# 3. Worktree directory exists
ls -la ~/.worktrees/<project>/<session-name>/ 2>&1
# Expect: drwxr-xr-x ... gitignored clone
# If "No such file or directory", spawn died after registration but before tmux fork.
```

If step 2 or 3 fails: **ghost session**. Recovery:

```bash
ao session kill <session-name> -p <project>
# Returns: session jleechanclaw-29 killed (workspace preserved)
```

Then fall back to honest-triage (Phase 3 below) — do NOT keep retrying `ao send`, the worker is not there.

## Fallback pattern — honest triage (Phase 3 of finish-the-job)

When the dispatch fails and you have computed partial state (PR lists, file diffs, build outputs, etc.) that the user actually needs:

1. **Post the triage inline in the user's Slack thread** with raw `gh pr list --json` / `tmux list-sessions` / etc. output as proof.
2. **State explicitly what dispatch failure happened** — name the session ID, the exact error, the diagnostic gate that failed. Don't paraphrase; quote the raw output.
3. **Offer 3 concrete options** (per SOUL.md `no-pick-one-menus`):
   - RETRY-DISPATCH (one more `ao spawn` attempt)
   - INLINE-PARTIAL-EXECUTE (do a small subset inline — e.g. one PR at a time, single-file squash merges)
   - ADVICE-ONLY (post PR comments requesting second-opinion review without auto-merging)
4. **Set a default if no reply** (typically ADVICE-ONLY — least destructive).
5. **Arm a 30-min cron check-in** (`hermes cron create "30m" --deliver 'slack:<chan>' --repeat 1`) that posts a single-line status ping if the user hasn't replied.
6. **Update bead notes** with the full dispatch trail so a follow-up session has context.

## Why this is better than silent workarounds

The temptation when `ao spawn` "succeeds" (per `ao session ls`) is to keep retrying `ao send` with shorter messages, or to inline-implement the work to make the user happy. Both are anti-patterns:

- **Keep retrying `ao send`** — burns quota on `MESSAGE_TOO_LONG` errors and never gets the work done. The user waits for nothing.
- **Inline-implement** — bypasses the AO worker pattern the user is paying for (their USER PROFILE says "Coding dispatch: prefers `claudem`/`claudeminimax` over AO because claudem provides visible progress"). The user expects an AO worker, not a Slack gateway session doing mass merges.
- **Silent mass-merge** — the worst option. Merges 45 PRs without per-PR `/advice` review, violates SOUL.md `pr-green-dispatch` ("MUST dispatch via `ao spawn`... NEVER run a multi-cycle /green loop inline").

Honest triage + cron check-in is the documented end-state per SOUL.md `proof-before-claim` ("Raw terminal output from the actual commands MUST already be present in the current session before claiming completion. If output is not yet present, say 'not run yet' and run the commands first") and `finish-the-job` "if you can only cite the tool layer, say so explicitly."

## Related signals to watch

- **`ao status` shows `readyz: ready` but new spawns fail** — orchestrator is in a degraded state. Try `ao start <project> --no-dashboard --no-open` per the existing `lifecycle polling is inactive` recipe.
- **Latest tmux sessions are all from OTHER projects** — e.g. worldarchitect wa-3427..wa-3430 but no jleechanclaw-* in the list. Strong signal the jleechanclaw spawn lane is broken even when the worldarchitect one is healthy.
- **`MESSAGE_TOO_LONG` on a fresh send** — body was over the limit OR no consumer. Combine with the tmux check to disambiguate.
- **`ao session ls` state stays at `[idle]` for >2 min** — pathological. Should transition to `[working]` once the worker is consuming, or to `[errored]`/`[failed]` if it crashed. If it stays at `[idle]`, the worker never started.

## Companion bead

`$USER-a4m` (`br show $USER-a4m`) — original dispatch attempt, triage table, and full PR-by-PR bucket list. Bead status remained `open` after the failed dispatch (no auto-close on failure).