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
  "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x "$ROOT/.claude/hooks/HOOK_NAME.py" ] && python3 "$ROOT/.claude/hooks/HOOK_NAME.py"; fi; exit 0'",
  "description": "What this hook does"
}
```

### For Shell Hooks (RECOMMENDED):
```json
{
  "type": "command",
  "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x "$ROOT/.claude/hooks/HOOK_NAME.sh" ] && exec "$ROOT/.claude/hooks/HOOK_NAME.sh"; fi; exit 0'",
  "description": "What this hook does"
}
```