---
description: Use Agent Orchestrator with strict parameter fidelity and post-spawn verification
type: workflow
execution_mode: deferred
scope: user
---
# /ao — Strict AO usage

Use AO with parameter fidelity. User-specified AO constraints are mandatory.

## Read first

- `~/.claude/skills/agent-orchestrator/SKILL.md`
- `~/.claude/skills/ao-worker-dispatch/SKILL.md`
- `~/.claude/skills/ao-operator-discipline/SKILL.md`

## Rules

1. Respect explicit AO parameters exactly:
   - `--agent`
   - `--runtime`
   - `--project`
   - `--claim-pr`
   - target PR / branch / evidence standard

2. Never substitute another agent/runtime because defaults exist.

3. After every `ao spawn`, verify the spawned session file under `~/.agent-orchestrator/.../sessions/<session>`:
   - `agent=<expected>`
   - `runtimeHandle.data.launchCommand` contains the expected CLI

4. If the user asked for Codex workers, the session must show:
   - `agent=codex`
   - `launchCommand` contains `codex`

5. After metadata verification, inspect the tmux pane with at least 20 lines:
   - `tmux capture-pane -pt <tmux-session>:0.0 -S -40`

6. If verification fails, kill and replace the worker. Do not continue with a mismatched worker.

## Output requirements

When reporting AO setup or supervision, include:
- the exact session ids
- the target PR URLs
- proof of `agent=<expected>`
- proof of `launchCommand`
- whether each worker is productive, drifting, or dead

## Input

$ARGUMENTS
