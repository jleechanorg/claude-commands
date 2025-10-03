---
description: Legacy alias for Cerebras code generation (redirects to /cerebras)
type: llm-orchestration
execution_mode: immediate
allowed-tools: Bash(qwen:*), Read, Edit, TodoWrite
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Task Execution

**Action Steps:**
Claude: Check for `cerebras_direct.sh` in the trusted locations (look in `~/.claude/commands/cerebras` first, then in the repository `.claude/commands/cerebras`). Once you find it, run the script with the original arguments. If the script is missing from both locations, surface a clear error explaining the lookup failure.

## 📋 REFERENCE DOCUMENTATION

# /qwen - Legacy Alias

**This command has been renamed to `/cerebras`**

## Automatic Redirect

This command automatically redirects to the new `/cerebras` command for backward compatibility.

## New Command Names

- `/cerebras` - Primary command name
- `/qwen` - This legacy alias (for backwards compatibility)
- `/c` - Short alias
- `/cereb` - Alternative short alias

## Migration Notice

While `/qwen` continues to work, please update your workflows to use `/cerebras` for the primary command.

## Post-Generation Analysis

I'll now review the Cerebras-generated output and provide:

1. **Code Quality Assessment** - Security, performance, best practices
2. **Integration Strategy** - How to merge with existing codebase  
3. **Testing Recommendations** - Unit tests, edge cases, validation
4. **Refinements** - Error handling, documentation, optimizations
5. **Next Steps** - Implementation plan, deployment considerations

The Cerebras output provides the foundation - I'll add the architectural thinking and integration expertise.
