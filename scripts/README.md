# WorldArchitect.AI Development Scripts

This directory contains shared development utilities and tools for the WorldArchitect.AI project.

## Scripts

### sync_check.sh
**Purpose**: Smart post-command sync check to prevent local changes not being pushed to remote.

**Features**:
- Automatically detects unpushed commits
- Works from any directory (finds git root automatically)
- Robust error handling for edge cases
- Clear, actionable feedback with visual indicators
- Safe: only pushes when unpushed commits are detected
- Idempotent: safe to run multiple times

**Usage**:
```bash
# Direct execution (dynamic path)
$(git rev-parse --show-toplevel)/scripts/sync_check.sh

# Or source and call function
source $(git rev-parse --show-toplevel)/scripts/sync_check.sh
sync_check
```

### common_utils.sh
**Purpose**: Shared utility functions for development tools.

**Features**:
- Project root detection from any directory
- Smart sync check wrapper function
- Quick commit and sync utilities
- Project validation functions

**Usage**:
```bash
# Source utilities (dynamic path)
source $(git rev-parse --show-toplevel)/scripts/common_utils.sh

# Use functions
smart_sync_check
quick_commit_and_sync "commit message"
```

## Integration

These scripts are integrated into key development tools:
- `/fixpr` - Uses sync check after applying fixes
- `/commentreply` - Uses sync check after creating responses
- `/integrate` - Uses sync check before branch cleanup

## Protocol

According to CLAUDE.md, tools that create git commits MUST call the sync check at completion to prevent the "forgot to push" syndrome while maintaining workflow transparency.
