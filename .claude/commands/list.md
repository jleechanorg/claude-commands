# List Commands Command

**Purpose**: Display all available slash commands with descriptions

**Action**: Show comprehensive list of all slash commands and their purposes

**Usage**: `/list`

## Implementation

**Enhanced Process**:
1. **Shell script** finds the commands directory from any git location
2. **Python script** dynamically scans all .md files in the commands directory
3. **Smart extraction** of command names and purposes from markdown documentation
4. **Sorted output** of all available slash commands with clean formatting

**Commands**:
- Generate command list: `./claude_command_scripts/list.sh`
- Direct Python execution: `python3 .claude/commands/list.py`

This automatically:
1. Finds the correct .claude/commands directory from any git location
2. Scans all .md files for command definitions
3. Extracts command names and purposes
4. Provides sorted, formatted output of all available commands
5. Works from any directory within the project (worktrees, subdirectories)

**Benefits**:
- ✅ **Always up-to-date** - Dynamically scans actual command files
- ✅ **Location agnostic** - Works from any directory in the project
- ✅ **Comprehensive** - Shows ALL available commands automatically
- ✅ **Formatted output** - Clean, readable command list
- ✅ **Maintenance-free** - No manual updates needed when commands change

## Output Format

Generates a comprehensive list of all available slash commands:
```
Available Slash Commands:
- /arch - Short form of the Architecture Review command for quick access
- /archreview - Conduct comprehensive architecture and design reviews
- /bclean - Delete local branches without open GitHub PRs
... (all commands listed dynamically)
```

## Usage in Workflow

**Best Practice**: Use `/list` to:
- See all available commands when starting work
- Discover new commands that have been added
- Get quick reminders of command purposes
- Ensure you're using the most current command set

**Integration**: 
- Run whenever you need to see available commands
- Use as a reference for command capabilities
- Perfect for onboarding or when returning to the project

## Compliance Note

This command helps maintain awareness of all available slash commands in the Claude Code CLI system. It ensures you always have access to the most current command set without needing to manually maintain command lists.