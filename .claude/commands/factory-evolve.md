---
description: /factory-evolve — analyze conversation + git history to find where cold reviews (codex, Bugbot, CodeRabbit, /reviewdeep) caught issues the factory reviewer nodes missed. Proposes targeted .dot and runner improvements.
type: llm-orchestration
execution_mode: immediate
---

# /factory-evolve

Read `~/.claude/skills/factory-evolve/SKILL.md` and execute the full workflow with any flags passed.

Flags:
- `--days N` — lookback window (default 7)
- `--pr N` — audit one specific PR
- `--taxonomy` — structural G1+G2 audit only (no history search)

After completing, always end with: top-3 proposals, gap category breakdown, and a one-line "wiring health" verdict (e.g. "4 of 12 code-producing paths have no reviewer node").
