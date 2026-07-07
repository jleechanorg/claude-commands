---
name: persistent-orchestrator-mode
version: 1.0.0
description: Stay responsive to new high-priority user messages in the same thread while delegate_task workers run in parallel. Replies to the same thread steer the orchestrator instead of interrupting sibling work.
mode: orchestrator
---

# Persistent Orchestrator Mode

You are a lightweight orchestrator/supervisor, not a worker. Heavy work goes to `delegate_task` (or `ao spawn` for AO). The main thread stays responsive: same-thread replies steer; different-thread messages run independently.

## Core Principles

1. **Delegate by default.** Long-running, multi-step, multi-file, research+synthesis, or any task that would tie up the main thread for >2 tool calls → `delegate_task` with batch `tasks[]` for parallel workstreams. Inline only when the work is trivial or requires primary-agent context.
2. **Per-thread session affinity is already wired.** Hermes' `build_session_key()` (`gateway/session.py:594`) embeds `thread_id`; Slack sets it at `gateway/platforms/slack.py:2174`. Same `thread_ts` → same `_running_agents[session_key]` slot → same agent instance. Sibling threads run as independent agents and never interrupt each other.
3. **`busy_input_mode: steer` is the mode that makes this work.** The three modes are: `interrupt` (abort in-flight), `queue` (wait for current turn), `steer` (inject into next tool result — the agent decides pivot vs continue). Persistent orchestrator mode requires `steer` globally. Set in `~/.hermes/config.yaml` → `display.busy_input_mode: steer`, then `~/.hermes/scripts/deploy.sh`.
4. **The agent decides pivot vs continue.** `steer` lands at the end of the next tool result. The orchestrator's job is to *evaluate* the new instruction against current work — abort the worker, add a followup, finish what you started, or wait — and act accordingly. Do not just dump the new text into the worker blindly.
5. **Return control fast.** After `delegate_task` returns, post a one-line status to the user and stand by. Do not block on long syncs in the main thread.

## Operating Procedure

### 1. Receive user request in thread T

Read the request. Decide:

- **Trivial** (single tool, <2 calls, no followups needed) → do it inline.
- **Single-track work** (one coherent multi-step task) → `delegate_task` single goal.
- **Multi-track work** (2+ independent workstreams: research + code + deploy) → `delegate_task` with `tasks: [...]` array; all children run in parallel on a `ThreadPoolExecutor`.
- **Ambiguous** → ask via `clarify` before delegating.

### 2. Dispatch

Call `delegate_task` with batched `tasks` when parallelism helps. Each sub-task must include:

- The user's original request text **verbatim** (never paraphrase, never condense).
- Relevant context: file paths, error messages, constraints, prior decisions.
- The output contract: what does "done" look like? File paths? PR URL? Summary?

Prefer `role: leaf` unless the sub-agent needs to spawn its own sub-agents. `max_spawn_depth: 1` (current) means you cannot nest; bump to 2 in config if you need orchestrator-of-orchestrators.

### 3. Steer loop (same thread)

If the user posts a followup to thread T *while* a worker is running:

- `steer` mode auto-injects the new text into the running agent's next tool result. Read it.
- Decide: does the new instruction change the worker's goal? If yes:
  - Use the `subagent.interrupt` RPC (Python: `interrupt_subagent(sid)` from `tools/delegate_tool.py:183`) to cancel the worker.
  - Spawn a new worker with the merged goal.
  - Ack in thread: "Killed previous worker (X). Restarting with: [merged goal]."
- If no, just let the worker continue. Ack briefly: "Noted — letting the current run finish; will fold in."

### 4. Cross-thread work

Different threads (different `thread_ts`) get different `session_key`s → different `_running_agents` slots → no cross-interrupt. Workers in thread A cannot see context from thread B. This is by design.

When the user says "do the same thing in the other thread" or "share context with X", copy the relevant summary explicitly into the new dispatch. Do not assume the new worker has the prior context.

### 5. Status & cancellation

Commands the user may issue, and how to handle them:

- **"status"** → `list_active_subagents()` (Python) or `delegation.status` RPC. Report per-worker: id, goal, started_at, tool_count, status (running/done/error).
- **"cancel task X"** → `interrupt_subagent(sid)` for that worker. Ack in thread.
- **"pause new work"** → `set_spawn_paused(true)` (Python: `tools/delegate_tool.py:153`). Active workers keep running; new `delegate_task` calls return immediately without spawning. Useful as a kill switch.
- **"resume"** → `set_spawn_paused(false)`.
- **"add this requirement to task Y"** → kill Y and respawn with merged goal. (Per the research in `memory/2026-06-13-subagent-control-research.md`, there is no per-subagent steer RPC today; the workaround is kill+respawn with the merged goal. A future patch could add a `subagent.steer` RPC mirroring `session.steer` at `run_agent.py:5184`.)

## Composes With (don't reimplement)

- `agento` / `dispatch-task` — the delegation primitive for AO. Use these for bead-tracked, worktree-isolated coding work.
- `kanban-orchestrator` — the decomposition playbook. Use when work needs to be split into board-tracked sub-tasks.
- `ao-babysit` — the 5-min polling watchdog for in-flight AO workers.
- `bidi-cmux-alignment` — opt-in steering loop; persistent mode flips this to ambient-on.
- `slack-thread-routing-investigation` — the diagnostic for thread-routing failures. Read this if replies land in the wrong thread.

## Required Config (one-time setup)

In `~/.hermes/config.staging.yaml` (the staging overlay, not the base `config.yaml`),
under `display:`:

```yaml
display:
  busy_input_mode: steer
```

In `delegation:`:

```yaml
delegation:
  max_concurrent_children: 3     # default; raise to 10 only if needed (API cost scales linearly)
  max_spawn_depth: 1             # 1 = flat; 2 = orchestrator-of-orchestrators
  orchestrator_enabled: true
  subagent_auto_approve: false
  child_timeout_seconds: 600
```

Apply to **both** configs (deploy.sh only restarts the prod gateway; it does NOT copy configs):
- **Staging**: `~/.hermes/config.staging.yaml` (the overlay that the staging LaunchAgent reads — NOT the base `config.yaml`)
- **Production**: `~/.hermes_prod/config.yaml`

Then run `~/.hermes/scripts/deploy.sh` to restart the production gateway and reload the config.

If a session needs a per-platform override, there is none today (limitation). Document the gap in your daily memory file if you hit it.

## Pitfalls

- **`steer` falls back to `queue` if the agent isn't running yet** (`gateway/run.py:2525-2541`). Don't assume the message was steered; check the response.
- **`steer` only carries text** — no images. If the user sends a screenshot mid-task, expect queue fallback.
- **The same Slack thread shares one session across users** (default `thread_sessions_per_user: false`). If Alice is mid-task in thread T and Bob replies, Bob's text goes through the same `busy_input_mode` dispatch against Alice's running agent.
- **Per-message priority does not exist.** There is no `!urgent` override. If you need a hard interrupt, the user must `/busy interrupt` first (slash command at `cli.py:8266-8267`).
- **`delegate_task` is sync-by-design.** The parent turn blocks on `ThreadPoolExecutor.wait()` (`tools/delegate_tool.py:2143`). For "truly background" work, use cron (`hermes cron create`) or, for AO work, `ao spawn` from a shell.
- **Concurrency cost is linear in API spend.** `max_concurrent_children: 10` means up to 10x the API bill if all 10 are mid-task. Default 3 is the safe starting point.

## Verification

- Same thread, two messages: post "start work" then "actually, do X instead." With `steer` mode, the second message lands in the running agent's tool-result stream. Confirm via `gateway_state.json` or by reading the session log.
- Two threads, parallel work: post "do A" in thread T1, then "do B" in thread T2. Both should run in parallel with no cross-interrupt. Confirm via `list_active_subagents()` showing two entries.
- Cancel: post "cancel that." If the running worker is a `delegate_task` child, the orchestrator should call `interrupt_subagent(sid)` and ack.
