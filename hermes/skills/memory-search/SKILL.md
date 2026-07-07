---
name: memory-search
description: "Search across all memory systems — ~/roadmap, beads, claude memories, hermes sqlite, hermes briefings, hermes index, wiki, history, and slack. Use whenever the user asks to search memories, find something in memories, or looks for anything that might have been captured in any memory store. Trigger on: 'search memories', 'find in my memories', '/ms', '/memory_search', 'search across all memories', 'look up in memory', 'did I save this somewhere', 'do I have anything about X in memory'."
---

# Memory Search (Hermes-side overlay)

**This file is the Hermes-side resolver entry for the `memory-search` skill.**
The canonical implementation lives at `~/.claude/skills/memory-search/SKILL.md` (Claude Code user-scope).
Hermes's `skill_view(name='memory-search')` resolves this overlay directly; if your runtime cannot find this overlay, fall back to the Claude-side file.

## Why this overlay exists (added 2026-07-02)

Before 2026-07-02, `~/.hermes/skills/memory-search/SKILL.md` did NOT exist. SOUL.md's `## COMMIT: ms-on-new-task` told Hermes agents to call `skill_view(name='memory-search')` but the resolver could not find it from `~/.hermes/skills/` — only from `~/.claude/skills/`. Telemetry from `~/.hermes/state.db` showed 0 of the 1,951 tool-using sessions in 7 days called `memory-search` via `skill_view`; only the slash-command surface (`/ms`) worked, and only from Claude Code / Codex runtimes. This overlay closes the resolver gap so `skill_view(name='memory-search')` works from any runtime (Slack, CLI, cron, terminal).

## How to execute the 9-store fan-out

Read the canonical implementation at `~/.claude/skills/memory-search/SKILL.md` and execute its `Execution` section. The 9 sources are:

1. `~/roadmap` — Project roadmaps and planning docs (`~/roadmap/`)
2. `beads` — Issue/bead tracking (`br search "$QUERY" --json | head -40`)
3. `claude memories` — Session memories (`~/.claude/projects/*/memory/`)
4. `hermes sqlite` — `~/.hermes/state.db` (`messages` table + FTS5 trigram index). NOTE: `~/.hermes/memory.db` is 0 bytes — DO NOT use it
5. `hermes briefings` — `~/.hermes/memory/briefing-*.md`, `mcp-mail-ack-log.md`
6. `hermes index` — `~/.hermes/MEMORY.md`
7. `wiki` — `~/llm_wiki/`
8. `history` — `~/.claude/projects/*/*.jsonl` (use 2-phase grep with -m flag, never read raw)
9. `slack` — `mcp__slack__conversations_search_messages` (skip if MCP unavailable)

Run all 9 searches in parallel via `delegate_task` (or `/e` subagents in Claude Code). Cache TTL = 1 hour, cache dir = `~/llm_wiki/.cache/memory-search/`.

## Per-runtime invocation

| Runtime | How to invoke |
|---|---|
| Claude Code / Codex | Type `/ms <query>` (slash command resolves to `~/.claude/commands/ms.md`) |
| Hermes (any runtime) | `skill_view(name='memory-search')` reads THIS overlay, then execute the 9-store fan-out |
| Cron / launchd / cmux | `skill_view(name='memory-search')` + execute fan-out via `delegate_task` |

## Aggregation output format

```
# Memory Search: "<query>"

## ~/roadmap
[results]

## Beads
[results]

## Claude Memories
[results]

## Hermes SQLite
[results]

## Hermes Briefings
[results]

## Hermes Index
[results]

## Wiki
[results]

## History
[results]

## Slack
[results]
```

## Cross-references

- Canonical implementation: `~/.claude/skills/memory-search/SKILL.md` (Claude Code user-scope)
- Trigger rule: `~/.hermes/workspace/SOUL.md` `## COMMIT: ms-on-new-task`
- Per-session fan-out: `~/.hermes/workspace/AGENTS.md` `Session-Start Recall Routine`
- Audit detector: `~/.hermes/scripts/audit_ms_proactive_firing.sh` (verifies firing rate after each deploy)
- Mirror: `~/.codex/skills/memory-search/SKILL.md` (Codex-readable, kept in sync)
- Bug-ref: 2026-07-02 Slack C0AJ3SD5C79 ts 1783036536.864119 — user asked to root-cause + fix `/ms` not firing proactively