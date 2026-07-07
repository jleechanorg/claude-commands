---
name: hermes-budget-fields
description: When user asks about "iteration budget" or "turn limit" for Hermes or AO worker, use this skill FIRST. It documents the 3 distinct fields (agent.max_turns, delegation.max_iterations, and AO's NO-iteration-concept) so you never conflate them. Triggers on phrases like "iteration budget", "turn limit", "max_iterations", "how many iterations", "agent loop", "change to 100/300/500/1000", "what's the cap on".
---

# Hermes iteration / turn budget fields

## The 3 fields (and which is which)

When the user asks about "iteration budget" or "turn limit", they may mean any of these:

| # | Field | Where | Default | What it actually caps |
|---|-------|-------|---------|----------------------|
| 1 | `agent.max_turns` | `~/.hermes_prod/config.yaml` line 20 | **1000** (as of 2026-06-27) | Hermes chat-agent loop (the main agent in a Slack/Cron session). One turn = one LLM call + tool executions. |
| 2 | `delegation.max_iterations` | `~/.hermes_prod/config.yaml` line 348 | **500** | Subagent (`delegate_task`) recursion depth. How deep a subagent can recurse before the parent is forced to stop. |
| 3 | **(none)** | n/a | n/a | AO worker has NO iteration budget. The loop is the model's tool-call loop, terminated by `child_timeout_seconds: 600` (10 min) or `max_spawn_depth: 1` (no recursion past one level). |

**Bug-ref 2026-06-27 02:32 PT:** I conflated all three in a /roadmap report. User corrected: Hermes `max_turns` is 1000 (not 300); AO worker has no iteration concept (verified by grep, zero `iter` matches in `agent-orchestrator.yaml`). mem0 entries saved.

## How to verify (the 30-second check)

```bash
# 1. Chat-agent turns
grep -n "agent:" $HOME/.hermes_prod/config.yaml | head -3
grep -n "max_turns:" $HOME/.hermes_prod/config.yaml | head -3

# 2. Delegation/subagent iterations
grep -n "delegation:" $HOME/.hermes_prod/config.yaml | head -3
grep -n "max_iterations:" $HOME/.hermes_prod/config.yaml | head -3

# 3. AO worker — should print NOTHING
grep -inE "iter|iteration" $HOME/.openclaw/agent-orchestrator.yaml
```

If step 3 prints anything, the config has drifted. AO workers do not count iterations — they count tool calls and wall-clock time.

## How to change

| User asks | File | Field | Line |
|-----------|------|-------|------|
| "Change Hermes chat budget" | `~/.hermes_prod/config.yaml` | `agent.max_turns` | 20 |
| "Change subagent recursion cap" | `~/.hermes_prod/config.yaml` | `delegation.max_iterations` | 348 |
| "Change AO worker time/count" | `~/.openclaw/agent-orchestrator.yaml` | `child_timeout_seconds` / `max_concurrent_children` / `max_spawn_depth` | (no `iter` field) |

**Always run the verify above BEFORE editing.** The numbers in the table above are correct as of 2026-06-27 — confirm they're still current before assuming.

## Common confusions

- "iteration budget 300" → user may mean field 1, field 2, or both. **Ask which**, or grep both and report current values to user before changing.
- "AO worker iteration cap" → there is none. Point user at `child_timeout_seconds: 600` instead.
- "max_iterations 100" → that's field 2 (delegation), not AO. Don't change `agent-orchestrator.yaml` thinking it controls this.
- "Hermes crashes after N iterations" → field 1 (`agent.max_turns`). Crash usually means the LLM hit max_turns and the gateway returned an error rather than continuing.
- "Subagent hangs" → field 2 OR `child_timeout_seconds`. Run the verify and check both.

## Why this matters

The user has asked about iteration budget 4 times in 7 days across different threads (`C0AJ3SD5C79 / 1782436438`, `C0AJ3SD5C79 / 1782379496`, etc.). Each time I had to re-derive which field was being asked about. This skill makes the answer 30 seconds instead of 30 minutes.

## Related

- `agento` SKILL.md § "Per-project concurrent-spawn lock" — also talks about `max_concurrent_children` but not as iteration budget
- `delegation.max_concurrent_children: 3` — caps how many subagents run in parallel, NOT iterations
- `delegation.max_spawn_depth: 1` — caps nesting depth, NOT iterations
- mem0 entry `hermes-budget-fields-three` and `ao-no-iteration-concept`
