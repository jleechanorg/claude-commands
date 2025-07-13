# Claude Code Hooks Setup for Automatic Header Generation

## Overview

This setup automatically generates the mandatory branch header before every tool use, ensuring 100% compliance with the CLAUDE.md header protocol.

## Configuration

**Location**: `~/.config/claude-code/settings.json`
**Source**: Copy from `.claude-code-config/settings.json` in this repository

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "cd \"$(git rev-parse --show-toplevel)/worktree_roadmap\" && ./claude_command_scripts/git-header.sh",
            "description": "Auto-generate branch header for CLAUDE.md compliance"
          }
        ]
      }
    ]
  }
}
```

## How It Works

**Trigger**: Before **every** tool use (Bash, Read, Edit, etc.)
**Action**: Runs `./claude_command_scripts/git-header.sh` to generate branch header
**Output**: `[Local: branch | Remote: upstream | PR: #num url]`

## Benefits

✅ **100% Compliance** - Never forget headers again
✅ **Zero Manual Effort** - Completely automated  
✅ **Deterministic** - Runs every single time
✅ **No Cognitive Load** - Remove human memory factor

## Backup Options

**Manual Command**: `/header` - Still available if hooks fail
**Direct Script**: `./git-header.sh` - Direct execution
**Manual Commands**: Individual git commands (fallback)

## Hook Event Details

- **PreToolUse**: Runs before tool execution
- **Matcher**: `"*"` matches all tools 
- **Command**: Changes to project directory and runs header script
- **Description**: Documents the hook purpose

## Testing

Test that hooks work by running any tool command. The header should appear automatically in Claude's output.

## Troubleshooting

**If headers don't appear:**
1. Check Claude Code settings file exists
2. Verify `git-header.sh` is executable
3. Ensure project path is correct
4. Use `/header` manual fallback
5. Check Claude Code logs for hook errors

## Security Note

Hooks run with full user permissions. This specific hook only reads git information and generates text output - no dangerous operations.