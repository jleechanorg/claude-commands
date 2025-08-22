# 🚨 CRITICAL: Hook Registration Requirements

**⚠️ MANDATORY**: ALL hooks MUST be registered in `.claude/settings.json` or they will NEVER execute!

## Hook Registration Checklist

### When Adding ANY New Hook:
1. ✅ Create hook file in `.claude/hooks/`
2. ✅ **REGISTER in `.claude/settings.json`** (CRITICAL STEP)
3. ✅ Test execution with appropriate trigger
4. ✅ Verify hook appears in Claude Code's loaded hooks

## Registration Format

### For Python Hooks:
```json
{
  "type": "command",
  "command": "python3 \"$ROOT/.claude/hooks/HOOK_NAME.py\"",
  "description": "What this hook does"
}
```

### For Shell Hooks:
```json
{
  "type": "command",
  "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x \"$ROOT/.claude/hooks/HOOK_NAME.sh\" ] && exec \"$ROOT/.claude/hooks/HOOK_NAME.sh\"; fi; exit 0'",
  "description": "What this hook does"
}
```

## Hook Event Types

### PreToolUse
- Runs BEFORE any tool execution
- Use for: validation, preparation, optimization hints
- Example: `pre_command_optimize.py` should be here

### PostToolUse
- Runs AFTER tool execution completes
- Use for: cleanup, processing outputs, monitoring
- Example: `command_output_trimmer.py` is registered here

### Stop
- Runs when conversation ends
- Use for: status display, cleanup
- Example: `git-header.sh` is registered here

### UserPromptSubmit
- Runs when user submits prompt
- Use for: command composition, preprocessing
- Example: `compose-commands.sh` is registered here

## Current Hook Status (2025-08-22)

### ✅ Registered Hooks:
- `command_output_trimmer.py` - PostToolUse (line 205)
- `detect_speculation_and_fake_code.sh` - PostToolUse (line 195)
- `post_commit_sync.sh` - PostToolUse for git commits (line 185)
- `git-header.sh` - Stop (line 217)
- `compose-commands.sh` - UserPromptSubmit (line 229)

### ❌ UNREGISTERED HOOKS (WILL NOT RUN):
- **`context_monitor.py`** - Should be in PreToolUse or PostToolUse
- **`pre_command_optimize.py`** - Should be in PreToolUse

## How to Fix Missing Registrations

Add to `.claude/settings.json` in the appropriate section:

```json
"PreToolUse": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"$ROOT/.claude/hooks/pre_command_optimize.py\"",
        "description": "Optimize tool selection before command execution"
      },
      {
        "type": "command",
        "command": "python3 \"$ROOT/.claude/hooks/context_monitor.py\"",
        "description": "Monitor context usage and provide warnings"
      }
    ]
  }
]
```

## Verification Commands

```bash
# Check all hooks in directory
ls -la .claude/hooks/*.{py,sh}

# Check registered hooks
jq '.hooks' .claude/settings.json

# Verify specific hook is registered
jq '.hooks.PreToolUse' .claude/settings.json | grep -i "context_monitor"
```

## Common Mistakes

❌ **Creating hook file without registration** - Hook will never run
❌ **Wrong event type** - Hook runs at wrong time
❌ **Incorrect path** - Hook fails to load
❌ **Missing executable permissions** - Shell hooks fail

## Testing Hook Registration

```bash
# Test if hook loads (check Claude Code output)
echo "test" | python3 .claude/hooks/context_monitor.py

# Check if hook is executable (for shell scripts)
test -x .claude/hooks/my_hook.sh && echo "✅ Executable" || echo "❌ Not executable"
```

## 🚨 CRITICAL REMINDER

**A hook file in `.claude/hooks/` does NOTHING by itself!**
**It MUST be registered in `.claude/settings.json` to execute!**

Last Updated: 2025-08-22
Issue Reference: PR #1410 - Context optimization hooks not registered