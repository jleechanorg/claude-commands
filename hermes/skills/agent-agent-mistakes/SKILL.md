---
name: agent-agent-mistakes
description: "Build agent memory patterns that prevent the same mistakes — using session replay, error tracking, and a self-correcting knowledge base."
when_to_use: "Use when the user wants to stop their AI agent from making the same mistakes repeatedly. Examples: 'make agents learn from mistakes', 'build error memory for agents', 'agent self-correction system', 'stop agents repeating errors', 'agent mistake tracker', 'build a memory that prevents agent errors'"
arguments:
  - agent_name
  - error_sources
argument-hint: "[agent_name] [error_sources]"
context: inline
---

# Agent-Agent Mistakes — Stop Agents Repeating Errors

Build a self-correcting memory system so your agent never makes the same mistake twice. Based on Garry Tan's framework for agent error prevention.

## Goal

Agents accumulate error patterns, learn from session failures, and consult a mistake memory before repeating actions.

## Inputs

- `$agent_name`: Name of the agent to instrument (e.g. "hermes", "ao-primary")
- `$error_sources`: Comma-separated sources to monitor for errors (e.g. "session_replays, cron_outputs, slack_threads")

## Steps

### 1. Set Up Error Capture

Create a memory file at `memory/agent-errors.md` tracking all agent mistakes.

**Success criteria**: `memory/agent-errors.md` exists and is git-tracked.

**Why this works despite `.gitignore` ignoring `memory/`**: the repo's `.gitignore` ignores `memory/` as a whole (it's machine-specific runtime), but `memory/agent-errors.md` is allow-listed with `!memory/agent-errors.md` so `git add memory/agent-errors.md` works normally. The exception is intentional: this file is the cross-machine mistake registry, not a runtime artifact — losing it loses the whole skill's value. Do not generalize the exception to other `memory/*` files; they remain machine-specific.

### 2. Instrument Session Replay

After every agent session, extract error patterns:
- Failed tool calls (timeout, permission denied, not found)
- User corrections (things the agent had to be steered on)
- Context-ceiling spirals (long sessions that produced no output)
- Fabricated responses (confabulated IDs, fake confirmations)

**Success criteria**: Session logs are being reviewed and patterns extracted.

### 3. Build the Error Memory

For each unique error pattern, add an entry to `memory/agent-errors.md`:

```markdown
## Error: [short name]

**First seen**: YYYY-MM-DD
**Occurrences**: N
**Root cause**: What the agent got wrong
**Prevention**: What the agent should do instead
**Trigger phrase**: Phrases that indicate this error is happening again
```

**Success criteria**: At least 3 error patterns documented.

### 4. Pre-Action Verify (verify-before-upstream-claim gate)

Before any claim that involves:
- An upstream repo's current state (language, file layout, branch, default branch, CI status)
- A local path on this machine (file, directory, binary, command output)
- A thread, channel, or message on a connected platform

**run the actual verification command in the same turn and cite its output.** Do not fill the gap from training-data memory of what the project used to be in a prior architecture, and do not say "I can't fetch that" for tools the runtime exposes (Slack MCP, Playwright MCP, `gh api`, `web_extract`).

See `references/2026-06-25-verify-before-upstream-claim.md` for the worked example, the three failure modes from that thread, and the paste-able pre-flight gate.

### 5. Track Error Recurrence

If an error from the memory is repeated, increment its occurrence count and add a new timeline entry.

**Success criteria**: `memory/agent-errors.md` shows decreasing recurrence for documented errors.

## Anti-Patterns (worked examples in references/)

- **2026-06-25 verify-before-upstream-claim** — three failures in one Slack thread: hallucinated a `~/.hermes/agent-orchestrator/` Python folder that didn't exist, assumed upstream's TS→Go rewrite also rewrote the user's TS fork, and said "I can't fetch Slack URLs" when `mcp_slack_conversations_replies` was sitting right there. See `references/2026-06-25-verify-before-upstream-claim.md`.