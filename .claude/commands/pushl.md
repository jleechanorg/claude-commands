# Push Lite Command (pushl alias)

**Purpose**: Enhanced reliable push to GitHub with selective staging, uncommitted change verification, and error handling

**Action**: Push current branch to origin with comprehensive reliability improvements, post-push verification, and optional PR creation (alias for pushlite)

**Basic Usage**:
- `/pushl` - Push current branch to origin
- `/pushl pr` - Push and create PR
- `/pushl force` - Force push to origin

**🆕 Conditional Lint Fixes**:
- Automatically applies lint fixes to Python files that are being staged/committed
- Only fixes files already being modified (safe and targeted)
- Runs `./run_lint.sh fix` before committing and re-stages any fixed files
- Skips lint fixes if no Python files are staged or if `SKIP_LINT=true`

**🆕 Post-Push Verification**:
- Checks for uncommitted changes after push completion
- Interactive options to handle unclean repository state:
  - Stage and commit remaining changes
  - Show detailed diff of uncommitted changes
  - Continue with uncommitted changes (not recommended)
  - Stash uncommitted changes for later
- Prevents the "forgot to commit/push" syndrome

**Enhanced Options**:
- `/pushl --verbose` - Enable detailed debugging output
- `/pushl --dry-run` - Preview operations without executing
- `/pushl --include "*.py"` - Include only files matching pattern
- `/pushl --exclude "test_*"` - Exclude files matching pattern
- `/pushl -m "message"` - Custom commit message

**🆕 PR Intelligence Features**:
- `/pushl pr --smart` - Create PR with auto-generated labels and description
- `/pushl --update-description` - Refresh existing PR description vs origin/main  
- `/pushl --labels-only` - Update PR labels without changing description
- `/pushl --detect-outdated` - Check if PR description matches current changes

**🤖 Auto-Generated PR Features**:

**Smart Labels** (based on git diff vs origin/main):
- **Type**: bug, feature, improvement, infrastructure, documentation, testing
- **Size**: small (<100), medium (100-500), large (500-1000), epic (>1000 lines)
- **Scope**: frontend, backend, fullstack (based on file types)
- **Priority**: critical, high, normal, low (based on keywords and file patterns)

**Smart Descriptions**:
- Analyzes complete diff vs origin/main (not just recent commits)
- Lists all changed files with line count statistics
- Auto-detects outdated descriptions (>20% file deviation)
- Generates comprehensive change summaries

**Outdated Description Detection**:
- Compares PR body file list vs current `git diff --name-only origin/main...HEAD`
- Flags PRs where line counts don't match actual `git diff --stat`
- Warns when PR description describes old changes

**Example Smart PR Description**:
```markdown
## 🔄 Changes vs origin/main
**Files Changed**: 8 files (+247 -63 lines)
**Type**: improvement | **Size**: medium | **Scope**: backend

### 📋 Change Summary
- Enhanced pushl command with PR intelligence
- Added automatic label generation
- Improved outdated description detection

### 🎯 Key Files Modified
1. pushlite.sh (+156 lines) - Core intelligence logic
2. pushl.md (+45 lines) - Documentation updates
3. CLAUDE.md (+32 lines) - Protocol enhancements

🤖 Generated with enhanced /pushl - reflects complete diff vs origin/main
```

**Implementation**:
Execute: `./claude_command_scripts/commands/pushlite.sh $ARGUMENTS`

**Note**: This is an alias for pushlite - both commands provide identical functionality.
