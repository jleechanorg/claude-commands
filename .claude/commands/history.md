---
description: /history — search Claude Code, Codex, and Hermes conversation history in parallel
type: llm-orchestration
execution_mode: immediate
---

# /history [query] [--flags]

Search all conversation history across three sources in parallel.

Read `~/.claude/skills/history-search/SKILL.md` and execute the full workflow with the provided query.

## Sources searched (parallel)

| Source | Data |
|--------|------|
| Claude Code | `~/.claude/projects/*/*.jsonl` |
| Codex | `~/.codex/state_5.sqlite` threads |
| Hermes | `~/.hermes_prod/state.db` messages (FTS5) |

## Flags

- `--recent N` — last N days only
- `--source claude|codex|hermes` — single source
- `--limit N` — results per source (default 20)
- `--date YYYY-MM` — filter by month

## Examples

```
/history "skeptic gate"
/history "load gate" --recent 7
/history "auth" --source hermes
/history "merge conflict" --limit 5
```
