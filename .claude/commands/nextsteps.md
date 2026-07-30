---
description: Situational assessment and roadmap sync after a work block. Default mode reads only beads (`br`) and `~/roadmap`; `--full` preserves the legacy all-source behavior (Claude auto-memory + mem0 + GitHub Issues).
type: orchestration
execution_mode: immediate
---

# /nextsteps

Situational assessment and roadmap sync after a work block.

**Skill:** `~/.claude/skills/nextsteps/SKILL.md`

## Usage

- `/nextsteps` — **default (lean)**: read beads + `~/roadmap`, write the independent nextsteps `.md` doc, update `br` + `roadmap/README.md` + `~/roadmap/learnings-YYYY-MM.md`. Skip Claude auto-memory, mem0, and GitHub Issue creation.
- `/nextsteps [brief]` — default mode, with an optional user-provided brief.
- `/nextsteps --full` — **legacy all-source**: everything in default **plus** Claude auto-memory writes + `MEMORY.md` pointers + mem0 sync + GitHub Issue creation per new bead.
- `/nextsteps --full [brief]` — `--full` mode with an optional brief.

The `--full` flag is the only recognized modifier. Any other token (`--help`,
`-h`, etc.) is treated as part of the brief.

## What changes vs. the legacy behavior

Before this change, `/nextsteps` always ran **all** phases including writing
Claude auto-memory, calling mem0, and creating GitHub Issues for every new
bead. The user explicitly asked to make `/nextsteps` lean by default and gate
the side-effecting phases behind `--full`. This command file + skill enforce
that split:

| Phase | Default | `--full` |
|-------|---------|----------|
| 1a/1b — gather context (git, beads, roadmap) | ✅ | ✅ |
| 2 — assess + update `roadmap/README.md` rolling activity | ✅ | ✅ |
| 2b — write/append the Nextsteps `.md` doc | ✅ | ✅ |
| 3 — execute parallel work | ✅ | ✅ |
| 4 — Claude auto-memory writes + `MEMORY.md` | ❌ | ✅ |
| 5 — mem0 sync | ❌ | ✅ |
| 6 — `~/roadmap/learnings-YYYY-MM.md` | ✅ | ✅ |
| 7 — bead create/update | ✅ | ✅ |
| 7b — GitHub Issue creation per new bead | ❌ | ✅ |
| 8 — report (mode-prefixed) | ✅ | ✅ |

See `~/.claude/skills/nextsteps/SKILL.md` for the full protocol.
