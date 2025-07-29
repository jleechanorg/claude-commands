# /pushl Command

**Usage**: `/pushl [--message MESSAGE] [--force]`

**Purpose**: Push local changes to remote repository with verification.

## Description

**NON-INTERACTIVE** bash implementation designed for automated copilot workflows. This is a simple wrapper around git commands with added verification and result tracking. Separate from interactive pushlite.sh to prevent automation conflicts.

## Universal Composition Integration

**Enhanced with /execute**: `/pushl` benefits from universal composition when called through `/execute`, which automatically provides intelligent optimization for complex git operations while preserving the reliable push workflow.

## Features

- Automatic change detection
- Staged commit creation
- Push with verification
- Force push support (with lease)
- Result JSON generation

## Options

- `--message, -m`: Commit message (default: "chore: Automated commit from copilot")
- `--force, -f`: Force push with lease for safety

## Output

Returns JSON result directly (no file creation) with:

```json
{
  "pushed_at": "2025-01-21T12:00:00Z",
  "branch": "feature-branch",
  "remote": "origin",
  "commit_sha": "abc123def",
  "message": "fix: Resolved CI failures",
  "success": true
}
```

## Examples

```bash
# Push with default message
/pushl

# Push with custom message
/pushl --message "fix: Resolve CI failures and conflicts"

# Force push (with lease)
/pushl --force --message "fix: Rebase and resolve conflicts"
```

## Safety Features

- Uses `--force-with-lease` instead of raw force
- Checks for changes before committing
- Reports push status in JSON

## Integration

Called by `/copilot` orchestrator after fixes are applied. Only runs if there are actual changes to push.

## Implementation Status

This command provides core git push functionality for the copilot workflow. The implementation handles standard push operations and is enhanced through the copilot orchestration system as needed.
