# /pushl Command

**Usage**: `/pushl [--message MESSAGE] [--force]`

**Purpose**: Push local changes to remote repository with verification.

## Description

Pure Python implementation that handles git operations for pushing changes. This is a simple wrapper around git commands with added verification and result tracking.

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

Creates `/tmp/copilot_{branch}/push.json` with:

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

## Note

This is a placeholder implementation. As noted in the plan: "leave /pushl alone for now, it already exists". Will be enhanced if issues arise during usage.
