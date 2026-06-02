---
name: code-standards
description: Dispatch independent adversarial reviews for ZFC, ZFC leveling, and root-cause-first without duplicating their standards.
---

# Code Standards

Use this skill to dispatch code, diff, PR, or proposed-implementation review
against the repo's core standards. This is a pointer/dispatch skill: reference
the source skills below instead of duplicating their standards.

## Source Skills

Load the relevant source skills by path and treat them as authoritative.
These live at `~/.claude/skills/` (user-scope, shared across all repos) and are
mirrored under `.codex/skills/` as pointer files. Skill discovery resolves
personal skills before project skills.

- `.claude/skills/zero-framework-cognition/SKILL.md` (`/zfc`)
- `.claude/skills/zfc-leveling-roadmap/SKILL.md` (`/zfclevel`)
- `.claude/skills/root-cause-first/SKILL.md` (`/root-cause-first`)
- Thermo-nuclear: invoke via `Agent` tool with `subagent_type: thermo-nuclear-code-quality-review` (`/thermo`)

## Workflow

1. Define the scope from the command argument. If no argument is provided,
   review the current diff or active PR context.
2. Dispatch **four** adversarial, independent review lanes every time:
   `/zfc`, `/zfclevel`, `/root-cause-first`, and `/thermo`.
3. Give each lane only its scope, the relevant source skill path, and the
   instruction to look for blockers with file/line evidence. Do not paste or
   restate the full standard into the prompt.
4. For Claude callers, use a Codex subagent or Codex reviewer plugin for at
   least one independent lane when available, so one reviewer is not relying on
   the same model/context as the caller.
5. The `/thermo` lane uses `subagent_type: thermo-nuclear-code-quality-review`
   (NOT a bash command). Pass: diff summary, file list, working dir.
6. Require every lane to report PASS/WARN/FAIL, evidence, required fixes, and
   any N/A caveats. A lane may return N/A for a subsection only if the source
   skill permits that; the lane itself still runs.
7. Reconcile the lane results into one practical report. Do not dilute a FAIL
   from any required lane into a PASS.

## Report Format

Return a concise report:

```markdown
## Code Standards Report

Scope: <file, diff, PR, or task>

- ZFC: PASS/WARN/FAIL - <evidence>
- ZFC leveling: PASS/WARN/FAIL - <evidence or permitted N/A caveat>
- Root-cause-first: PASS/WARN/FAIL - <evidence or permitted N/A caveat>
- Thermo: PASS/WARN/FAIL - <evidence or structural blockers>

Blockers:
- <line-level issue and required fix>

Next checks:
- <tests, evidence, or review steps needed>
```

If there are no blockers, say so explicitly and list any residual risks. Do not
mark any of the four lanes as skipped.
