---
description: Search across all memory systems — roadmap, beads, claude memories, mem0, hermes, openclaw, wiki, history, and slack
type: llm-orchestration
execution_mode: immediate
---

# /memory_search [query] [--flags]

Search all memory stores in parallel.

Read `~/.claude/skills/memory-search/SKILL.md` and execute the full workflow with the provided query.

## Sources searched (parallel)

| Source | Data |
|--------|------|
| roadmap | `~/roadmap/` — project planning + learnings |
| beads | `~/.beads/beads.db` (SQLite, primary) + `br` CLI; do NOT read `issues.jsonl` directly |
| claude memories | `~/.claude/projects/*/memory/` |
| hermes sqlite | `~/.hermes/state.db` (3.6 GB Hermes state; `messages` table; FTS5 via `messages_fts`). Note: `~/.hermes/memory.db` is 0 bytes; data is in `state.db` |
| hermes briefings | `~/.hermes/memory/briefing-*.md` |
| hermes index | `~/.hermes/MEMORY.md` |
| openclaw | `~/openclaw-repo/MEMORY.md`, `~/.hermes/memory/` (legacy) |
| wiki | `~/llm_wiki/` (via wiki-search) |
| history | `~/.claude/projects/*/*.jsonl` |
| slack | `mcp__slack__conversations_search_messages` / `conversations_history` |

Note: mem0 (Qdrant at localhost:6333) not directly searchable — skip.

## Flags

- `--recent N` — last N days only
- `--source X` — single source (roadmap|beads|hermes|wiki|history|slack|...)
- `--limit N` — max results per source (default 20)
- `--cache-ttl SECONDS` — override 1-hour default cache TTL

## Examples

```text
# Recent learnings about a Slack misroute class
/memory_search "slack misroute failure 5" --recent 7

# Single source, scoped to beads
/memory_search "$USER-owka" --source beads

# Hermes-only state.db FTS search
/memory_search "iteration budget exhausted" --source hermes --limit 50
```

## Cache

Cache dir: `~/llm_wiki/.cache/memory-search/` — TTL 1 hour; key = SHA-256(canonicalized query).

## See also

- `/ms` — alias (same workflow)
- `/history` — conversation-history-only variant
