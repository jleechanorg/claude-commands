---
description: /history — sparse conversation history search (Claude, Codex, Hermes, agy CLI, Cursor) with quota guard
type: llm-orchestration
execution_mode: immediate
---

# /history [query] [--flags]

Search conversation history using the **sparse** skill. Default is lean and fast.
Use `--deep` only when sparse results are insufficient and you explicitly need the full 7-source search.

## 🚨 CODEX MODEL ROUTING (mandatory for Codex sessions)

- **Model**: `gpt-5.3-codex-spark` for all history search work (Codex sessions). Policy: `~/.codex/rules/model-routing-policy.md`.
- **Sparse-first**: Apply `conversation-history-sparse` budget:
  max 3 files per source, 3 prompts per file, 200 chars per prompt. Never `cat` full history files.

## ⚠️ DEDUP GATE (run before starting a new history search)

Check for active in-flight threads using shared helper `~/.codex/hooks/codex-dedup-check.sh "<query>"`:
```bash
~/.codex/hooks/codex-dedup-check.sh "QUERY" 1800
# Equivalent SQL:
# sqlite3 ~/.codex/state_5.sqlite "SELECT COUNT(*) FROM threads WHERE first_user_message LIKE '%QUERY%' AND tokens_used=0 AND created_at_ms>(unixepoch('now')-1800)*1000;"
```
If duplicate in-flight thread exists, steer existing thread instead of spawning fresh.

## Default (sparse)

Read `~/.claude/skills/conversation-history-sparse/SKILL.md` and execute the sparse workflow.

Sources (5 only by default — keep the budget tight):

| Source | Data |
|--------|------|
| Claude Code | `~/.claude/projects/*/*.jsonl` |
| Codex | `~/.codex/state_5.sqlite` threads |
| Hermes | `~/.hermes/state.db` messages (FTS5) |
| agy CLI | `~/.gemini/antigravity-cli/conversation_summaries.db` |
| Cursor | `~/.cursor/prompt_history.json` + `~/.cursor/chats/` |

## Flags

- `--recent N` — last N days only
- `--source claude|codex|hermes|agy|cursor` — single source (cheapest: pick one)
- `--limit N` — results per source (default 5, sparse max 20)
- `--date YYYY-MM` — filter by month
- `--deep` — escape hatch: run the full `~/.claude/skills/history-search/SKILL.md`
  (7 sources, higher cost). Requires explicit user intent.

## Examples

```
/history "skeptic gate"
/history "load gate" --recent 7
/history "auth" --source hermes
/history "agy conversation" --source agy
/history "merge conflict" --limit 5
/history "PR 353" --deep   ← full search, use sparingly
```
