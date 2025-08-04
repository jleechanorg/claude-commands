# Claude Code Hook System

The `.claude/hooks/` directory contains hooks that are auto-recognized by Claude Code CLI to improve behavior and prevent common issues.

## Hook Types

### 🚫 Anti-Demo Hook (`anti_demo_check_claude.sh`)
**Purpose**: Prevent generation of placeholder/demo code in production files

**Detects**:
- TODO/FIXME markers without implementation
- Demo/fake return values
- Placeholder implementations
- Empty function bodies

**Context-Aware**: Allows demo patterns in test/mock/example files

### 🚫 Anti-Speculation Hook (`detect_speculation.sh`)
**Purpose**: Prevent Claude from saying "let me wait for command to complete"

**Reality Check**: Commands have already completed when Claude receives them

**Detects**:
- "Let me wait for..."
- "Command is running"
- "I'll wait for results"
- Other speculation patterns

### 🚫 Anti-Root Files Hook (`check_root_files.sh`)
**Purpose**: Prevent file pollution in project root directory

**Enforces**: Proper file organization in subdirectories

**Allows**: Only essential root files (README.md, CLAUDE.md, etc.)

### 📋 Git Header Hook (`git-header.sh`)
**Purpose**: Generate branch information footer for responses

**Provides**: Current branch, remote status, and PR information

### 🔄 Post-Tool-Use Sync Hook (`post_commit_sync.sh`)
**Purpose**: Automatically sync commits to remote after git commit operations

**Features**:
- Triggers after git commit tool operations via PostToolUse hook
- Uses smart sync check to detect unpushed commits
- Automatically pushes to correct upstream remote
- Respects existing git workflows and configurations
- Portable across different development environments

## Integration

## Auto-Recognition

✅ **Claude Code CLI automatically recognizes hooks in `.claude/hooks/`**

Add to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "$(git rev-parse --show-toplevel)/.claude/hooks/anti_demo_check_claude.sh",
            "description": "Prevent demo/placeholder code"
          },
          {
            "type": "command",
            "command": "$(git rev-parse --show-toplevel)/.claude/hooks/check_root_files.sh",
            "description": "Prevent root directory pollution"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          {
            "type": "command",
            "command": "$(git rev-parse --show-toplevel)/.claude/hooks/post_commit_sync.sh",
            "description": "Auto-sync commits to remote after git commit operations"
          }
        ]
      }
    ],
    "PostResponse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$(git rev-parse --show-toplevel)/.claude/hooks/detect_speculation.sh",
            "description": "Detect speculation about command execution"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$(git rev-parse --show-toplevel)/claude_command_scripts/git-header.sh",
            "description": "Generate git branch header for response footer"
          }
        ]
      }
    ]
  }
}
```

**Directory Independence**: All hooks automatically detect the project root, so they work from any subdirectory.

**Auto-Recognition**: Claude Code CLI knows to look in `.claude/hooks/` for hook scripts automatically.

## Testing

Hook test files located in `.claude/hooks/tests/`:
- `hook_test_*.py` - Red/green test files for anti-demo hook
- `test_hook_patterns.py` - Test file patterns for anti-demo hook
- `test_hook_system.md` - Complete testing guide
- `test_directory_independence.sh` - Test hooks work from any directory

## Benefits

1. **Code Quality**: No placeholder implementations
2. **Accurate Communication**: No false waiting states
3. **File Organization**: Clean project structure
4. **Immediate Feedback**: Real-time validation

## File Organization Standards

- **Documentation** → `docs/`
- **Tests** → `tests/` or `testing_*/`
- **Scripts** → `claude_command_scripts/` or `scripts/`
- **Configs** → `configs/` or `.config/`
- **Examples** → `examples/`
- **Temporary** → `tmp/` or `temp/`

Keep project root clean with only essential files!

## Hook Files in .claude/hooks/

All hooks are properly located in the auto-recognized Claude directory:

```
.claude/hooks/
├── anti_demo_check_claude.sh        # Demo code prevention
├── detect_speculation.sh            # Command speculation blocker
├── check_root_files.sh              # Root directory protection
├── post_commit_sync.sh              # Post-tool-use (git commit) auto-sync
├── tests/                           # Test files directory
│   ├── hook_test_*.py              # Red/green test files
│   ├── test_hook_patterns.py       # Test file patterns
│   ├── test_hook_system.md         # Testing guide
│   └── test_directory_independence.sh # Directory test
└── README.md                        # This documentation
```

**Separate Command Scripts**:
```
claude_command_scripts/
├── git-header.sh                    # Branch header generation
└── other project scripts...         # General project automation
```
