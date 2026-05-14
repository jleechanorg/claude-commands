---
name: eloop
description: Alias for /evolve_loop — autonomous AO ecosystem evolution loop
type: git
execution_mode: immediate
---

# /eloop

Alias for `/evolve_loop`. Use the canonical evolve-loop skill at:

- `~/.claude/skills/evolve-loop/SKILL.md`

Execution rule:
- Load that skill and follow it as the source of truth.
- For non-Claude runtimes, prefer the skill file over this wrapper.
- If repo-local automation needs a loop body, read the skill file directly rather than duplicating the command text.