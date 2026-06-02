---
description: Use Agent Orchestrator with strict parameter fidelity and post-spawn verification
type: workflow
execution_mode: deferred
scope: user
---
# /ao — Strict AO usage

Use AO with parameter fidelity. User-specified AO constraints are mandatory.

## Read first

- `~/.hermes/agent-orchestrator.yaml` — **ALWAYS read this first** to resolve `--agent` shorthands (e.g. `agy`=`antigravity`); `defaults.agent` is the default when none specified
- `~/.claude/skills/agent-orchestrator/SKILL.md` — default workflow (start / spawn / status / send / cleanup) ⚠️ FILE MISSING — skill not yet created
- `~/.claude/skills/ao-worker-dispatch/SKILL.md` — pre-dispatch checklist (venv, commit discipline, branch drift, CodeRabbit verify)
- `~/.claude/skills/ao-operator-discipline/SKILL.md` — strict parameter fidelity + post-spawn verification
- `~/.claude/skills/ao-spawn-gate/SKILL.md` — pre-spawn safety gate
- `~/.claude/skills/ao-session-monitor/SKILL.md` — proper tmux inspection for live workers
- `~/.claude/skills/ao-model-override/SKILL.md` — override the worker's model (e.g. claude-sonnet-4-6, claude-opus-4-7) WITHOUT editing `~/.hermes/agent-orchestrator.yaml`. Use whenever the user names a specific model and the project default isn't it (e.g. "use claude sonnet with AO"). `ao spawn` has NO `--model` flag; the only inline override is `AO_CONFIG_PATH` pointing at a temp copy of the config — the skill ships `spawn-with-model.sh` for this.

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
