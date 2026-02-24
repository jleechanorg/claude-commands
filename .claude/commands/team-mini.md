---
description: Create a minimax-only agent team with haiku for work
type: agent-orchestration
execution_mode: immediate
---

## EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**

1. Parse the user's prompt from the command arguments
2. Create a new team using TeamCreate with `minimax-pair-coder` agent type (uses claudem() from bashrc)
3. Spawn subagents using ONLY minimax or haiku models - NO sonnet or opus
4. Execute the requested work using the team

## IMPORTANT: HOW MINIMAX WORKS

This command uses your `claudem()` bash function from ~/.bashrc which sets:
- `ANTHROPIC_BASE_URL="https://api.minimax.io/anthropic"`
- `ANTHROPIC_MODEL="MiniMax-M2.5"`
- `ANTHROPIC_SMALL_FAST_MODEL="MiniMax-M2.5"`

The `minimax-pair-coder` and `minimax-pair-verifier` agent types invoke `claudem()` internally.

## TEAM-MINI COMMAND

Usage: `/team-mini <prompt>`

This command creates a Claude team that uses ONLY:
- **MiniMax-M2.5** via `claudem()` bash function (minimax-pair-coder, minimax-pair-verifier)
- **Haiku** for quick/simple tasks (`model: "haiku"` in Task calls)

**NOT allowed:** sonnet, opus, or default Claude models (sonnet/opus will cost more)

### Execution Steps:

1. **Create team:**
   ```python
   TeamCreate(
       agent_type="minimax-pair-coder",
       description="Team using only minimax and haiku models",
       team_name="minimax-team-<timestamp>"
   )
   ```

2. **Spawn workers with model restrictions:**
   - Use `minimax-pair-coder` for main work (MiniMax-M2.5 via claudem)
   - Use `minimax-pair-verifier` for verification (MiniMax-M2.5 via claudem)
   - For simple quick tasks, use `model: "haiku"` in Task calls

3. **Execute the user's prompt** using the team

4. **Shutdown team** when complete

### Example:
```
/team-mini Write a test file that logs model usage to /tmp/test.log
```
