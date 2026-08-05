---
description: /claudeminimax - Alias of /claudem (delegates to claude-code-claudem on a clean worktree, MiniMax M3 wrapper)
type: delegation
execution_mode: immediate
---

# /claudeminimax — alias of `/claudem`

**Usage**: `/claudeminimax <task description>` — identical behavior to `/claudem`.

This is a thin alias for `/claudem`. Both names resolve to the same `claude-code-claudem` skill, the same `claudem` bashrc function (which is itself aliased to `claudeminimax` in `~/.bashrc`), and the same MiniMax M3 routing.

The skill is the canonical `claude-code-claudem` v1.8.3 — landed in [jleechanorg/jleechanclaw#800](https://github.com/jleechanorg/jleechanclaw/pull/800).

## Rules

- Behavior is identical to `/claudem`. Use whichever name reads more naturally.
- This command is the force-claudem path. It does NOT route to AO/agento under any circumstance.
- For AO, use `/claw`, `/af`, or `/auto-factory` instead.

## Execution

When invoked with `$ARGUMENTS`, defer to `/claudem` (read `~/.claude/commands/claudem.md` and execute that workflow).
