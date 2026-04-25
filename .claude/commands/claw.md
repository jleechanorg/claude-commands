---
description: /claw - Route tasks through Hermes gateway inference
type: orchestration
execution_mode: immediate
---
# /claw - Hermes Gateway Inference

**Usage**: `/claw <task description>`

`/claw` is a thin wrapper. The operational behavior lives in:

- `~/.claude/skills/claw-dispatch/SKILL.md`

If the `/claw` task dispatches or supervises AO workers, also follow:

- `~/.claude/commands/ao.md`
- `~/.claude/skills/ao-operator-discipline/SKILL.md`

## Rules

- User-specified AO parameters are mandatory and must not be weakened or ignored.
- Post-spawn AO verification is required when `/claw` crosses into AO.
- Keep this command file thin; update the skill for behavioral changes.

## Execution

When invoked with `$ARGUMENTS`, read `~/.claude/skills/claw-dispatch/SKILL.md` and execute that workflow with the provided task description.
