---
description: /bashrc — safe wrapper and settings editing playbook
type: llm-orchestration
execution_mode: immediate
---

This command points to:

- `~/.claude/skills/bashrc.md`

Use this when editing `~/.bashrc` or changing any Claude CLI model/provider routing.

## What to do

### 1) Start with history checks

- Run `/history "bashrc minimax minimax_M3 claude settings.json" --recent 14` to confirm recent context.
- Run `/ms "claude ANTHROPIC_BASE_URL MINIMAX_API_KEY"` to check if there is prior recovery notes.
- If either output shows unresolved confusion, pause and resolve before editing.

### 2) Apply the Bashrc maintenance playbook

- Follow the protocol in `~/.claude/skills/bashrc.md`.
- Keep wrapper intent explicit:
  - `claude` = base client behavior.
  - `claudem` = MiniMax wrapper.
- Never set MiniMax env at the wrong layer for the requested target.

### 3) Validate after edit

- Confirm env values by source-loading a clean shell once.
- Declare functions `claude` and `claudem` and verify `claudem` includes Minimax settings.
- Verify plain `claude` is not unintentionally inheriting wrapper-level routing.

### 4) Record change summary

- In your final note include:
  - files changed,
  - expected model path per command,
  - exact validation commands + results.

If this command is run without edit intent, treat it as a checklist and stop before mutating files.
