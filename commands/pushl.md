# Push Lite Command (pushl alias)

**Purpose**: Enhanced reliable push to GitHub with selective staging, error handling, and debugging capabilities

**Action**: Push current branch to origin with comprehensive reliability improvements and optional PR creation (alias for pushlite)

**Basic Usage**:
- `/pushl` - Push current branch to origin
- `/pushl pr` - Push and create PR
- `/pushl force` - Force push to origin

**🆕 Conditional Lint Fixes**:
- Automatically applies lint fixes to Python files that are being staged/committed
- Only fixes files already being modified (safe and targeted)
- Runs `./run_lint.sh fix` before committing and re-stages any fixed files
- Skips lint fixes if no Python files are staged or if `SKIP_LINT=true`

**Enhanced Options**:
- `/pushl --verbose` - Enable detailed debugging output
- `/pushl --dry-run` - Preview operations without executing
- `/pushl --include "*.py"` - Include only files matching pattern
- `/pushl --exclude "test_*"` - Exclude files matching pattern
- `/pushl -m "message"` - Custom commit message

**Implementation**:
Execute: `./claude_command_scripts/commands/pushlite.sh $ARGUMENTS`

**Note**: This is an alias for pushlite - both commands provide identical functionality.
