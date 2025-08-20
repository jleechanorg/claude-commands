# Command Scripts Directory - Creation Policy

## 🚨 CRITICAL: SHELL SCRIPT & PYTHON FILE CREATION BAN

**ABSOLUTE PROHIBITION**: This directory is **BANNED** from containing shell scripts (.sh) or Python files (.py).

### Creation Requirements

Before creating **ANY** shell script or Python file in this directory, you **MUST** type:

```
approve1234
```

### Rationale

The `/copilotsuper` command has been enhanced to use pure markdown orchestration with Task subagents rather than bash scripts. This provides:

- ✅ Better integration with Claude Code CLI
- ✅ Cleaner architecture without script dependencies
- ✅ Task agent parallelization for true concurrency
- ✅ Reduced maintenance overhead

### Directory Contents

This directory should contain **ONLY**:
- This README.md file
- Documentation files (.md)
- Configuration files (if absolutely necessary)

### Enforcement

Any attempt to create .sh or .py files without the `approve1234` confirmation will be immediately rejected and the file(s) will be deleted.

### Alternative Solutions

Instead of shell scripts or Python files:
1. Use pure .md command files in `.claude/commands/`
2. Leverage Task subagents for parallel processing
3. Use Claude Code CLI's built-in orchestration capabilities

## Summary

**Shell scripts and Python files are BANNED in this directory without explicit `approve1234` approval.**
