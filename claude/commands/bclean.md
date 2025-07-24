# Branch Cleanup Command

**Purpose**: Delete local branches without open GitHub PRs

**Action**: Delete local branches without open GitHub PRs

**Usage**: `/bclean`

**MANDATORY**: When using `/bclean` command, follow this exact sequence:

1. **GitHub PR Check**: Use `gh pr list --state open --json headRefName` to get all open PR branch names

2. **Local Branch List**: Use `git branch` to get all local branches (exclude main/master)

3. **Cross-Reference**: Identify local branches that do NOT have corresponding open GitHub PRs

4. **Safety Check**: 
   - ⚠️ **NEVER delete current branch**
   - ⚠️ **NEVER delete main/master branches**
   - ⚠️ **NEVER delete worktree branches** (check `git worktree list`)

5. **User Confirmation**: Present list of branches to delete and request explicit approval

6. **Branch Deletion**: Only delete branches after user confirms with:
   - `git branch -d <branch>` (safe delete - only if merged)
   - `git branch -D <branch>` (force delete - only if user explicitly requests)

7. **Result Reporting**: Summarize branches deleted, any that couldn't be deleted, and reasons

**Safety Rules**:
- ✅ **Only delete branches without open PRs**
- ✅ **Always check for unpushed commits** before deletion
- ✅ **Warn about unpushed work** and offer to create PRs first
- ❌ **NEVER delete without user confirmation**
- ❌ **NEVER delete branches with uncommitted changes**

**Command Purpose**: Clean up stale local branches that don't have active GitHub PRs, preventing branch pollution while preserving active work.