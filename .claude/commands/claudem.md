---
description: /claudem - Delegate coding work to claude-code-claudem on a clean worktree (default coding skill, MiniMax M3 wrapper)
type: delegation
execution_mode: immediate
---

# /claudem — Direct invocation of the `claude-code-claudem` skill

**Usage**: `/claudem <task description>` or `/claudeminimax <task description>` (alias)

This is the direct entry point for the default coding-delegation skill. It runs `claude-code-claudem` (the bashrc `claudem` / `claudeminimax` wrapper routed to MiniMax M3) on a clean worktree from `origin/main`, bypassing AO/agento entirely.

`/claudem` is a thin wrapper. The operational behavior lives in:

- `skills/claude-code-claudem/SKILL.md`

The skill is the canonical `claude-code-claudem` v1.8.3 (Hermes side) — landed in [jleechanorg/jleechanclaw#800](https://github.com/jleechanorg/jleechanclaw/pull/800).

## Rules

- This command is the force-claudem path. It does NOT route to AO/agento under any circumstance.
- `/claudem <task>` always runs `claudem -p "<task>"` on a clean worktree (`git worktree add … origin/main -b feat/…`), with `--max-turns` tuned to the brief (see the skill's sizing table).
- For AO, use `/claw`, `/af`, or `/auto-factory` instead.
- For the Hermes handler (in a Slack thread), the inline gateway session can also invoke `claudem` directly via `bash -lic 'claudem -p "<task>"'`.

## Execution

When invoked with `$ARGUMENTS`, read `skills/claude-code-claudem/SKILL.md` and execute that workflow on a clean worktree with `$ARGUMENTS` as the task brief.

If asked to invoke from a terminal (not as a slash command), the canonical command is:

```bash
# from a clean worktree
git worktree add /tmp/claudem-<topic> -b feat/<topic> origin/main
cd /tmp/claudem-<topic>
bash -lic 'claudem -p "<task>"' --max-turns <N>
```

If you want the operator to see progress in a Slack thread, the dispatch shape is:

```bash
bash -lic 'claudem -p "<task>"' --max-turns <N> --output-format json --verbose
# tail the worktree's logs and post evidence to the originating thread
```
