# /newbranch or /nb - Create new branch from latest main

Creates a fresh branch from the latest main branch code. Aborts if there are uncommitted changes.

## Usage
- `/newbranch` - Creates a new branch with timestamp (dev{timestamp})
- `/nb` - Alias for /newbranch
- `/newbranch test1234` - Creates a branch named 'test1234'
- `/nb feature-xyz` - Creates a branch named 'feature-xyz'

## Behavior
1. Checks for uncommitted changes using `git status`
2. Aborts if any uncommitted changes are found
3. Fetches latest code from origin/main
4. Creates and switches to new branch from origin/main
5. Sets up tracking to origin/main

## Examples
```
/nb
→ Creates branch like dev1751992265

/nb my-feature
→ Creates branch named my-feature

/newbranch bugfix-123
→ Creates branch named bugfix-123
```

## Error Cases
- Uncommitted changes present → Aborts with message
- Branch name already exists → Git will report error
- Network issues → Fetch may fail

## Implementation Notes
- Works in both regular repos and worktrees
- Always creates from origin/main (not local main)
- Automatically sets up remote tracking
