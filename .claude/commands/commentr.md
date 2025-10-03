---
description: Comment Reply Command (Alias)
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Documented Workflow

**Action Steps:**
1. Invoke the underlying workflow by running `/commentreply $ARGUMENTS` (pass through any user-supplied options).
2. Follow `/commentreply` Phase 2-4 instructions to load comment JSON, generate replies, and write `/tmp/<branch>/responses.json`.
3. Execute the automated posting step (`python3 .claude/commands/commentreply.py ...`) to submit replies to GitHub.
4. Summarize posted replies and remaining follow-up actions before returning success.

## 📋 REFERENCE DOCUMENTATION

# Comment Reply Command (Alias)

**Alias for**: `/commentreply`

**Usage**: `/commentr` or `/commentreply`

**Purpose**: Systematically address all GitHub PR comments with inline replies

See [commentreply.md](./commentreply.md) for full documentation.
