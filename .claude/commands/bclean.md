# Branch Cleanup Command

**Purpose**: Safe cleanup of Git branches and worktrees with comprehensive safety features

**Action**: Execute the enhanced branch-cleanup.sh script with worktree cleanup functionality

**Usage**: `/bclean [options]`

## Available Options
- `--dry-run` - Preview what would be cleaned without making changes
- `--force` - Skip confirmation prompts (use with caution)
- `--days N` - Age threshold for worktree cleanup (default: 2 days)
- `--help` - Show detailed help and examples

## Enhanced Features
✅ **Branch Cleanup**: Safely removes local branches without open PRs
✅ **Worktree Cleanup**: Removes stale worktrees based on commit age
✅ **PR-Aware**: Preserves branches with active GitHub PRs
✅ **Safety First**: Never deletes uncommitted work or current branch
✅ **Configurable**: Adjustable age thresholds for worktree cleanup

## Implementation
When `/bclean` is used, Claude should execute the enhanced branch-cleanup.sh script:

**Action**: Execute `./claude_command_scripts/commands/branch-cleanup.sh` with any provided arguments

This provides:
- **Comprehensive Git workspace cleanup** (branches + worktrees)  
- **Battle-tested safety features** with PR checking
- **Interactive confirmations** and dry-run preview
- **Clear status reporting** with color-coded output
- **Flexible configuration** with command-line options

## Examples
- `/bclean --dry-run` - Preview cleanup without changes
- `/bclean` - Interactive cleanup with confirmations  
- `/bclean --days 7` - Clean worktrees older than 7 days
- `/bclean --help` - Show detailed usage information

**Command executes the enhanced script with all provided arguments for full functionality.**