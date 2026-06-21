---
description: Create or update executable br follow-up beads with implementation instructions, signatures, and acceptance criteria
aliases: [bead]
type: workflow
execution_mode: immediate
---

# /beads — Executable Follow-up Beads

Use `~/.claude/skills/bead-followup-templates/SKILL.md` as the source of truth.

When invoked as `/beads <finding-or-task>`, create or update `br` follow-up beads using that skill's template. Each bead must include source context, current SHA, file/line evidence, exact implementation instructions, live-code API/function signatures, call-site examples, standards constraints, verification commands, acceptance criteria, and a staleness note.

Hard rules:
- Use `br --no-auto-flush` in worktrees and feature branches.
- Do not use `bd`.
- Do not invent API/function signatures from memory; read the current code first.
- If multiple beads come from the same PR, put the PR URL in the body instead of reusing the same `--external-ref`.
- For production `$PROJECT_ROOT/**` behavior, include the required `/es` evidence class in acceptance criteria.
