# 🚨 CRITICAL: Hook Registration Requirements

**⚠️ MANDATORY**: ALL hooks MUST be registered in `.claude/settings.json` or they will NEVER execute!

## Hook Registration Checklist

### When Adding ANY New Hook:
1. ✅ Create hook file in `.claude/hooks/`
2. ✅ Make file executable: `chmod +x .claude/hooks/HOOK_NAME.{py,sh}`
3. ✅ **REGISTER in `.claude/settings.json`** (CRITICAL STEP)
4. ✅ Use ROBUST command pattern (see below)
5. ✅ Test execution with appropriate trigger
6. ✅ Verify hook appears in Claude Code's loaded hooks

## 🛡️ ROBUST Registration Patterns

### For Python Hooks (RECOMMENDED):
```json
{
  "type": "command",
  "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x \"$ROOT/.claude/hooks/HOOK_NAME.py\" ] && python3 \"$ROOT/.claude/hooks/HOOK_NAME.py\"; fi; exit 0'",
  "description": "What this hook does"
}
```

### For Shell Hooks (RECOMMENDED):
```json
{
  "type": "command",
  "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x \"$ROOT/.claude/hooks/HOOK_NAME.sh\" ] && exec \"$ROOT/.claude/hooks/HOOK_NAME.sh\"; fi; exit 0'",
  "description": "What this hook does"
}
```

### ❌ FRAGILE Pattern (DO NOT USE):
```json
{
  "type": "command",
  "command": "python3 \"$ROOT/.claude/hooks/HOOK_NAME.py\"",
  "description": "BREAKS if $ROOT not set - causes system lockout!"
}
```

## 🔧 Pattern Explanation

**Robust Pattern Benefits:**
- ✅ **Environment Independent**: Works without `$ROOT` variable
- ✅ **Graceful Failure**: Exits cleanly if not in git repo
- ✅ **Executable Check**: Only runs if file exists and is executable
- ✅ **Cross-Worktree Compatible**: Works in any git worktree
- ✅ **No System Lockout**: Never blocks Claude Code operations

**Pattern Breakdown:**
```bash
bash -c '
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then  # Check if in git repo
    ROOT=$(git rev-parse --show-toplevel);                      # Get project root dynamically
    [ -x "$ROOT/.claude/hooks/HOOK_NAME.py" ] &&               # Check file exists and executable
    python3 "$ROOT/.claude/hooks/HOOK_NAME.py";                # Execute hook
  fi; 
  exit 0                                                       # Always exit cleanly
'
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

### ✅ Registered Hooks (ROBUST PATTERN):
- `pre_command_optimize.py` - PreToolUse (FIXED with robust pattern)
- `context_monitor.py` - PreToolUse (FIXED with robust pattern)
- `command_output_trimmer.py` - PostToolUse 
- `detect_speculation_and_fake_code.sh` - PostToolUse
- `post_commit_sync.sh` - PostToolUse for git commits
- `git-header.sh` - Stop
- `compose-commands.sh` - UserPromptSubmit

### 🔧 Recent Fixes Applied:
- **Environment Robustness**: All hooks now use dynamic `ROOT=$(git rev-parse --show-toplevel)`
- **System Lockout Prevention**: Hooks gracefully fail instead of blocking operations
- **Cross-Worktree Compatibility**: Works in any git worktree without environment setup

## ✅ Example Complete Registration

Here's how `context_monitor.py` is properly registered:

```json
"PreToolUse": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x \"$ROOT/.claude/hooks/context_monitor.py\" ] && python3 \"$ROOT/.claude/hooks/context_monitor.py\"; fi; exit 0'",
        "description": "Monitor context usage and provide real-time warnings"
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

## 🚨 Troubleshooting Hook Issues

### System Lockout (All Tools Blocked):
**Symptom**: Error: "can't open file '/.claude/hooks/HOOK_NAME.py': No such file or directory"
**Cause**: Hook commands using `$ROOT` variable without proper resolution
**Solution**: Use robust command pattern (see above)

### Hook Not Executing:
1. ✅ Check file exists: `ls -la .claude/hooks/HOOK_NAME.py`
2. ✅ Check executable: `test -x .claude/hooks/HOOK_NAME.py && echo "✅ OK"`
3. ✅ Check registration: `jq '.hooks' .claude/settings.json | grep HOOK_NAME`
4. ✅ Test manually: `python3 .claude/hooks/HOOK_NAME.py`

### Environment Issues:
- **Problem**: Hook works in one worktree but not another
- **Solution**: Use robust pattern - never depend on environment variables

## 📋 Quick Add New Hook Checklist

```bash
# 1. Create hook file
touch .claude/hooks/my_new_hook.py
chmod +x .claude/hooks/my_new_hook.py

# 2. Add to settings.json (use robust pattern!)
# Edit .claude/settings.json and add hook registration

# 3. Test hook
python3 .claude/hooks/my_new_hook.py  # Test directly
# Then test through Claude Code operation
```

## 📚 Historical Issues & Fixes

### 2025-08-22: Hook Environment Robustness Fix
- **Issue**: PR #1410 introduced system lockout when `$ROOT` undefined
- **Root Cause**: Hard dependency on environment variable without fallback
- **Fix**: Implemented robust pattern using `git rev-parse --show-toplevel`
- **Impact**: Prevents future system lockouts across all worktrees

## 🚨 CRITICAL REMINDER

**A hook file in `.claude/hooks/` does NOTHING by itself!**
**It MUST be registered in `.claude/settings.json` to execute!**
**ALWAYS use the ROBUST command pattern to prevent system lockouts!**

Last Updated: 2025-08-22
Issue Reference: Fixed system lockout from PR #1410 hook environment issues