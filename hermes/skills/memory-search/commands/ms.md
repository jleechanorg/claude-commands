---
description: Alias for /memory_search — search across all memory systems (Hermes-side overlay)
type: llm-orchestration
execution_mode: immediate
---

# /ms — Hermes-side Alias for /memory_search

**This file is the Hermes-side resolver entry for the `/ms` slash command.**
The canonical Claude-side file lives at `~/.claude/commands/ms.md`.
Hermes runtimes resolve THIS file when the user types `/ms` outside Claude Code.

## Action

Read `~/.hermes/skills/memory-search/SKILL.md` (Hermes-side overlay) and execute the
10-store fan-out end-to-end. Falls back to `~/.claude/skills/memory-search/SKILL.md`
if the overlay is missing in a given runtime.

## Per-runtime dispatch

| Runtime | Slash-command resolution |
|---|---|
| Claude Code / Codex | `~/.claude/commands/ms.md` (canonical, identical content) |
| Hermes (Slack / CLI / cron) | `~/.hermes/skills/memory-search/SKILL.md` (this overlay) |

Both runtimes land at the same 10-store fan-out (~/roadmap, beads, claude memories,
hermes sqlite, hermes briefings, hermes index, openclaw memories, wiki, history, slack).

## Usage

```
/ms <query> [--flags]
```

Examples:

```
/ms slack misroute failure 5
/ms hermes deploy --recent 7
/ms $USER-owka --source beads --limit 5
```

## Why this overlay exists (added 2026-07-02)

Before 2026-07-02, `/ms` only resolved from Claude Code / Codex runtimes via `~/.claude/commands/ms.md`.
Slack / CLI / cron Hermes sessions could not invoke `/ms` because `~/.hermes/skills/memory-search/SKILL.md`
did not exist and there was no slash-command resolver on the Hermes side. The
`## COMMIT: ms-on-new-task` rule in SOUL.md told agents to call `memory-search` skill via
`skill_view`, but the resolver path was broken from Hermes. Telemetry from `~/.hermes/state.db`
showed 0 of 1,951 tool-using sessions in 7 days called `memory-search` via `skill_view` — the
wiring was missing, not just the wording.

This overlay + the `skills/memory-search/SKILL.md` overlay close that gap.

## Cross-references

- Canonical: `~/.claude/commands/ms.md` (Claude Code user-scope, 109 B → ~1 KB rewrite 2026-06-25)
- Canonical skill: `~/.claude/skills/memory-search/SKILL.md`
- Hermes overlay skill: `~/.hermes/skills/memory-search/SKILL.md`
- Trigger rule: `~/.hermes/workspace/SOUL.md` `## COMMIT: ms-on-new-task`
- Per-session fan-out: `~/.hermes/workspace/AGENTS.md` `Session-Start Recall Routine`
- Audit detector: `~/.hermes/scripts/audit_ms_proactive_firing.sh`
- Bug-ref: 2026-07-02 Slack C0AJ3SD5C79 ts 1783036536.864119