# PR #2843: Rewards Protocol Clarification

_Last updated: 2025-12-31_

This branch focuses on making reward protocols explicit in the ESSENTIALS blocks of the combat and narrative system prompts so the LLM awards XP and loot reliably.

## Scope of Changes
- Prompt updates: reward-handling steps are now in ESSENTIALS for combat and social encounters:
  - [`combat_system_instruction.md`](../mvp_site/prompts/combat_system_instruction.md) – COMBAT END PROTOCOL
  - [`narrative_system_instruction.md`](../mvp_site/prompts/narrative_system_instruction.md) – SOCIAL VICTORY PROTOCOL
- Regression coverage: `testing_mcp/test_rewards_missed.py` validates combat and surrender reward flows without explicit OOC guidance.

## Out of Scope
- Ally turn order and combat resource visibility bugs mentioned in the original PR description are **not** addressed in this branch.
- Files `test_combat_ally_turns.py` and `test_combat_ally_turns_README.md` do not exist in this PR.

## Testing
Run the regression test with a local MCP server:

```bash
BASE_URL=http://localhost:8001 python testing_mcp/test_rewards_missed.py
```

Ensure the MCP server is running locally (e.g., via `./run_local_server.sh`),
or point `BASE_URL` at the deployed preview endpoint when available.
