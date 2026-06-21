---
description: Create and install a proper macOS launchd job using the canonical /launchd skill
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Load and Apply Skill
**Action Steps:**
1. Open and apply the standards defined in the `~/.claude/skills/launchd/SKILL.md` skill file.
2. Generate the lightweight wrapper script that sources the user's interactive profile (`~/.bash_profile` or `~/.bashrc`) with `set +u` safety wrappers.
3. Write a clean, minimal plist file inside `~/Library/LaunchAgents/` using calendar or interval execution triggers.
4. Run a clean reinstallation by running `launchctl bootout` followed by `launchctl bootstrap`.
5. Verify the logs and verify the launchd registration status.
