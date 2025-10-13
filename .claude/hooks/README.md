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

### 🚫 Anti-Speculation Hook (`detect_speculation_and_fake_code.sh`)
**Purpose**: Prevent Claude from saying "let me wait for command to complete"

**Reality Check**: Commands have already completed when Claude receives them

**Detects**:
- "Let me wait for..."
- "Command is running"
- "I'll wait for results"
- Other speculation patterns

### 🤖 Smart Fake Code Detection Hook (`smart_fake_code_detection.sh`)
**Purpose**: Run the `/fake` command automatically after any Write tool output to audit for placeholders or simulated results.

**How it works**:
- Captures the Write tool payload to collect every touched file
- Launches `claude -p --dangerously-skip-permissions --model sonnet` headlessly
- Pipes a `/fake` command with context about the modified files
- Streams the analysis back into the transcript and logs it under `~/.local/state/claude/`

**Configuration**:
- `SMART_FAKE_TIMEOUT` (seconds, e.g. `60s`): override the default 120-second `/fake` audit timeout when the claude CLI supports longer or shorter checks.

**Detects**:
- Placeholder or fake implementations introduced during edits
- Simulated REST/API responses or fabricated data
- Suspicious speculation inside new or updated files

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

Configure hooks in your project's `.claude/settings.json` using the hook scripts in this directory.

**Directory Independence**: All hooks automatically detect the project root, so they work from any subdirectory.

**Auto-Recognition**: Claude Code CLI knows to look in `.claude/hooks/` for hook scripts automatically.

## Tuning the Command Output Trimmer

The `command_output_trimmer.py` hook keeps chat transcripts concise, but you have full control over how aggressive it is:

- **One-off full output** – Prefix any command with an environment override such as `CLAUDE_TRIMMER_DISABLE=1 <command>` or `CLAUDE_TRIMMER_MODE=full <command>` to bypass trimming for that run entirely.
- **Magic markers in output** – If a command prints `[claude:show-full-output]`, `[claude:full-output]`, or `[claude:no-trim]` anywhere in its output, the trimmer will now pass everything through untouched.
- **Plain-language overrides** – You can also say things like “show full output” or “display full output” in the transcript and the trimmer will recognize the request and skip trimming automatically.
- **Persistent configuration** – Edit either `.claude/settings.json` (project default) or `~/.claude/settings.json` (user override) and adjust the `output_trimmer` section. You can disable it (`"enabled": false`), turn off performance mode, or tweak limits like `"max_output_lines"`.

These options let you opt into full logs whenever you explicitly request them without disabling the savings for everyday commands.

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
├── detect_speculation_and_fake_code.sh  # Command speculation blocker
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
