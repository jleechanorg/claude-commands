---
description: /keychain_kill — Terminate macOS SecurityAgent and dismiss all stacked keychain modal prompts
type: llm-orchestration
execution_mode: immediate
---

# /keychain_kill

When this command is invoked, immediately dismiss all stacked macOS `SecurityAgent` credential popups by hard-killing their processes.

## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**YOU (Claude) must execute these steps immediately:**

1. Run the hard kill on SecurityAgent and related warning dialogs:
   ```bash
   pkill -9 -f SecurityAgent || killall -9 SecurityAgent || true
   pkill -9 -f universalAccessAuthWarn || true
   ```
2. Read and apply the comprehensive diagnostic guide in `~/.claude/skills/keychain-kill/SKILL.md`.
3. Inform the user that the keychain prompts have been dismissed.
