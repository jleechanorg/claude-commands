---
description: Code standards review - dispatch independent ZFC, ZFC leveling, and root-cause-first review lanes
type: quality
execution_mode: immediate
---

# /code-standards

Load and follow `.claude/skills/code-standards/SKILL.md`.

Use this command when reviewing current work, a PR, a file, or a proposed fix
against the repo's core code standards. It must dispatch adversarial,
independent review lanes for all three source standards:

- `/zfc` via `.claude/skills/zero-framework-cognition/SKILL.md` (user-scope: `~/.claude/skills/`)
- `/zfclevel` via repo command `.claude/commands/zfclevel.md`
- `/root-cause-first` via `.claude/skills/root-cause-first/SKILL.md` (user-scope: `~/.claude/skills/`)

Source skills live at `~/.claude/skills/` (user-scope, shared across all repos)
and are mirrored under `.codex/skills/` as pointer files. The repo-local
`.claude/skills/` paths resolve via skill discovery order: personal > project.

Pass any command arguments through as the review scope.

For Claude callers: use a Codex subagent or Codex reviewer plugin for at least
one independent review lane when available.
