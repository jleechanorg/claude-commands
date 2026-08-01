# Worker execution checkpoint gate — keep the gateway thread honest

**Captured 2026-07-28 from the Spellblade/Valeria campaign task in $GITHUB_REPOSITORY.** This reference codifies the proof-of-execution contract between a gateway session and a background worker (`claudem`, `ao spawn`, opencode, Codex, etc.) so the user can actually watch the work happen in their Slack / chat thread.

## The two failure modes this reference prevents

1. **"Did you actually do the work, or are you pretending?"** — the gateway session posts a confident "On it — let me start a worker" message, spawns the worker, but never posts an observable checkpoint. The user comes back hours later and sees zero progress. The worker may have actually run for 25 minutes, but the thread shows nothing.
2. **"Tell it to update this thread every minute"** — the user assumes the worker can post into the thread. **It cannot.** The worker is its own process with terminal + filesystem access only; no Slack MCP, no thread_ts, no way to call `mcp__slack__conversations_add_message`. The gateway session that spawned it is the only entity that can post.

Both failure modes collapse into one durable lesson: **observable checkpoints in the user's thread must come from the gateway session, not from the worker.** The gateway polls the worker + the worktree and surfaces proofs.

## Gateway-session contract when spawning a coding worker

Spawn the worker with these six properties so the gateway session can monitor it:

```text
1. process_id:   surface process.poll/process.log session_id in the next thread reply
2. worktree:     surface absolute worktree path + branch name + base SHA
3. log_poll:     process(action='log', session_id=<pid>, offset=0, limit=200) on a timer
4. worktree_diff: git -C <wt> status --short + git diff --stat + git log --oneline -3 on the same timer
5. checkpoint_gap: 5-minute default; 1-minute if user explicitly asked for high-frequency updates
6. kill_early:   if first 2 log blocks show zero tool calls AND uptime > 90s, kill and respawn
```

Every reply between spawn and completion must include at least one of:

- `process` poll result (worker stdout / stderr, exit reason, uptime)
- `git` snapshot (status --short / diff --stat / log -3)
- explicit "no change since last checkpoint" statement

When the user asks for high-frequency updates ("every minute"), honor it from the gateway, not by asking the worker.

## What the gateway posts when the worker hits `max-turns` with zero edits

This is the canonical 4-line surface the gateway must show in the next thread reply when `claudem -p "... --max-turns 25"` exits `Error: Reached max turns (25)` and the worktree is empty:

```text
Worker exited: Error: Reached max turns (25)
Worktree: <absolute path> on branch <branch> from <base-sha>
git status --short: <empty>
git diff --stat:    <empty>
```

Followed by the next-action statement: "Re-spawning with `--max-turns 50` and an execution-shaped brief. The new worker is `<new-process-id>`."

## What the gateway posts when the worker produces durable state

When the worker exits cleanly (`claudem -p` returns a structured result with a commit SHA, or the worktree `git log` shows a new commit on the planned branch), the gateway posts:

```text
Worker commit: <SHA> on branch <branch>
Changed files: <git diff --name-only origin/main..HEAD>
Test result:   <pytest / npm test summary line>
PR URL:        <gh pr view URL when worker creates one>
```

If the worker only edited files but didn't commit, the gateway commits on the worker's behalf (after verifying the diff with `git diff HEAD` against `git status --short` — no surprise reverts, per the pre-merge-worktree-sabotage-inspection pitfall).

## Why the user can't see the worker directly

The `claudem` bashrc function executes `claude --dangerously-skip-permissions --effort high "$@"` — that's the Claude Code CLI binary running as a subprocess of the bashrc-sourced shell. Its tool surface is whatever Claude Code exposes: `Read`, `Edit`, `Bash`, `Grep`, etc. **Slack MCP tools are not part of that toolset.** The worker doesn't know the user's thread_ts, the channel ID, or even that it's running "inside a Slack thread."

The gateway session in Hermes is what wraps the worker in a thread context. The gateway holds:

- the user's thread_ts (from the inbound Slack message envelope)
- the channel ID (C0... ID)
- the OAuth scopes for `chat.postMessage`
- the ability to call `mcp__slack__conversations_add_message` or the underlying `chat.postMessage` API

That asymmetry is what makes the gateway the only thread-poster. Codifying it in a skill prevents the next session from inventing worker-side "thread update" instructions.

## Cadence — what "every minute" actually means

When the user says "every minute," the gateway session runs this loop for the duration of the worker run:

```bash
# Pseudo-code — execute from the gateway via terminal + process
while process.status == 'running':
    process(action='log', session_id=<pid>, limit=50, offset=-1)
    git -C <wt> status --short
    git -C <wt> diff --stat
    git -C <wt> log --oneline -3
    post to thread_ts: "<truncated progress line>"
    sleep 60
```

If the loop is too aggressive for the gateway session's own tool-call budget, fall back to a 5-minute cadence and say so explicitly. The user's "every minute" was a desire for liveness, not a literal cron contract — a 5-minute cadence with proof-of-polling artifacts in each post is a defensible interpretation. **Never silently skip the cadence.**

## When the worker fails AND the user asked for high-frequency updates

If the worker is killed by the gateway (because the 90-second no-tool-call early-kill window fires), the gateway posts:

```text
Killed worker <pid> at uptime=<s>s — zero tool calls in first <n> log blocks
Re-spawning with explicit execution brief
New worker: <new-pid>
```

This satisfies "Are you really executing?" with concrete proof: the gateway is observing, deciding, and respawning. It also prevents the user from later asking "why did the worker silently die?"

## Verified case (2026-07-28, Spellblade/Valeria prompt task)

- Worker #1: `proc_eea1ad9d60be` — `claudem -p "<long brief>" --max-turns 25` exited `Error: Reached max turns (25)` after 51s uptime with empty `git diff --stat` on branch `feat/spellblade-valeria-prompts` (worktree `/private/tmp/spellblade-prompts`).
- Gateway response: surfaced the proof (process ID, worktree path, empty diff), re-spawned with `--max-turns 50` and an execution-shaped brief.
- Worker #2: `proc_71ca51b72247` — re-spawned with the explicit "do not re-explain the task and do not stop at analysis — execute now" brief.

The user pushback verbatim: *"Are you really executing? ... Will I actually see updates in this thread or will you never update it again?"* — this reference exists so the next session cannot silently fall back into "ack + spawn + silence."

## Companion references

- `references/claudem-fallback-when-ao-minimax-unavailable-2026-07-26.md` — the AO-down `claudem -p` fallback chain.
- `references/ao-spawn-internal-error-pivot-2026-07-12.md` — pivot-to-inline when AO returns Internal server error.
- `references/pr-topology-preflight-recurring-alert-2026-07-09.md` — existing-worktree scan before dispatch.
- The `claude-code-claudem` skill "Worker scope vs gateway scope" section — direct read of why a worker cannot post to Slack.

## Quick checklist for any `terminal(background=true, notify_on_complete=true, pty=true)` claudem spawn

Before the spawn:

- [ ] Worktree is clean (per `always-pr-never-local-edit` v1.6.0 "Dirty-checkout pre-flight")
- [ ] Branch is set (`git worktree add -B <topic> <path> origin/main`)
- [ ] `bash -lic 'type claudem && claudem --version'` returns OK
- [ ] Brief includes: explicit execution directive, max-turns justified by scope, commit SHA + test output gate at the end
- [ ] Spawn command captures the process session_id in the next reply

In every follow-up reply until worker exits:

- [ ] `process(action='log', session_id=<pid>, limit=50)` output (or "no new output since last poll")
- [ ] `git -C <wt> status --short` (or "clean since last poll")
- [ ] `git -C <wt> log --oneline -3` (or "no new commits since last poll")
- [ ] If the user requested high-frequency updates, the cadence is honored
- [ ] No "worker will update you" promises — only gateway-side updates

When worker exits:

- [ ] Exit reason surfaced (`Reached max turns`, `Completed normally`, `Killed`, etc.)
- [ ] Durable state surfaced (commit SHA, file list, test output, PR URL or "PR not created — left on branch X for your review")
- [ ] If `Error: Reached max turns` AND `git diff --stat` empty → re-spawn with stricter brief, surface both worker IDs in the next reply
- [ ] Final end-state declaration per finish-the-job Phase 4.6 (root-cause fix vs detector vs evidence)
