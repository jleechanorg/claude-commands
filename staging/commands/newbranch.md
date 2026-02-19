---
description: /newbranch or /nb - Create new branch from latest main
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Branch Creation

**Action Steps:**
1. Execute the newbranch.py Python script with user arguments
2. Script handles: stashing changes, fetching main, creating branch, cherry-picking commits
3. Verify branch creation success and report new branch name
4. If cherry-picks requested, confirm commits were applied
5. Confirm working tree changes were restored

## 📋 REFERENCE DOCUMENTATION

# /newbranch or /nb - Create a new branch from fresh `origin/main`

Creates a fresh branch from the latest `origin/main` while carrying forward your current working tree changes. When the command detects language such as "bring in changes" it will also cherry-pick the requested committed changes onto the new branch.

## Usage
- `/newbranch` - Creates a new branch with timestamp (dev{timestamp})
- `/nb` - Alias for /newbranch
- `/newbranch test1234` - Creates a branch named `test1234`
- `/nb feature-xyz` - Creates a branch named `feature-xyz`
- `/nb bring in changes abc123` - Creates a branch named `bring-in-changes` and cherry-picks commit `abc123` before restoring uncommitted edits
- `/newbranch polish ui include changes 123abc 456def` - Creates a branch named `polish-ui` and cherry-picks commits `123abc` and `456def`

## Behavior
1. Detects uncommitted changes and stashes them (including untracked files).
2. Fetches, checks out, and pulls the latest `origin/main`.
3. Creates the new branch directly from `origin/main`.
4. Optionally cherry-picks requested commits that exist on the previous branch.
5. Restores any stashed changes so your working tree matches your previous edits.
6. Pushes the branch and sets upstream tracking to `origin/<branch_name>`.

## Examples
```
/nb
→ Creates branch like dev1751992265

/nb my-feature
→ Creates branch named my-feature

/newbranch bugfix-123
→ Creates branch named bugfix-123

/nb bring in changes abc123 def456
→ Creates branch named bring-in-changes and cherry-picks abc123 + def456

/nb feature tweaks with commits
→ Creates branch named feature-tweaks and cherry-picks every local commit not on origin/main
```

## Error Cases
- Rebase conflicts → Command stops with instructions so you can resolve and continue
- Branch name already exists → Git will report error
- Network issues → Fetch may fail

## Implementation Notes
- Works in both regular repos and worktrees
- Always fetches and pulls the latest `origin/main` before creating the branch
- Cherry-picks requested commits from the previous branch when keywords like "bring in changes" are present
- Automatically sets up remote tracking to origin/<branch_name>
- ⚠️ **CRITICAL**: Must use Python script (.claude/commands/newbranch.py)
- ❌ **NEVER** manually run: `git branch --set-upstream-to=origin/main`
- ✅ **CORRECT**: Let script handle tracking with `git push -u origin <branch>`
