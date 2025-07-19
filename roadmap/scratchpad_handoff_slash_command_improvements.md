# Handoff: Slash Command Improvements (/handoff + /commentreply)

## Problem Statement
1. The `/handoff` command doesn't automatically add tasks to roadmap.md, requiring manual updates
2. No automated way to systematically address all GitHub PR comments, leading to missed feedback

## Implementation Plan

### Task 1: Enhance /handoff Command
**Goal**: Integrate `/r` functionality to automatically add tasks to roadmap.md

**Changes to `.claude/commands/handoff.md`**:
1. After creating PR, automatically invoke the `/r` command logic
2. Add task entry to appropriate section in roadmap.md
3. Include PR number and handoff status

**Implementation approach**:
```bash
# After PR creation in handoff.sh
echo "## Adding task to roadmap.md..."

# Invoke /r logic
TASK_NAME="HANDOFF-$(echo $1 | tr '[:lower:]' '[:upper:]')"
TASK_DESC="$2"
PR_NUMBER=$(gh pr view --json number -q .number)
PR_URL=$(gh pr view --json url -q .url)

# Add to roadmap.md Active WIP Tasks section
# Use same format as /r command
```

### Task 2: Create /commentreply Command
**Goal**: Systematically address all GitHub PR comments with inline replies

**New file**: `.claude/commands/commentreply.md`

**Command behavior**:
1. Get current branch and associated PR
2. Fetch ALL comments (inline + general + reviews)
3. Present each comment to assistant
4. For each comment:
   - Address the feedback
   - Mark as ✅ DONE or ❌ NOT DONE with reason
   - Generate inline reply via GitHub API
5. Provide summary in chat

**Implementation structure**:
```markdown
# /commentreply Command

Systematically addresses all GitHub PR comments with inline replies.

## Usage
/commentreply
/commentr (alias)

## What it does
1. Fetches all PR comments (inline, general, reviews)
2. Addresses each comment systematically
3. Replies inline with ✅ DONE or ❌ NOT DONE
4. Provides summary of all addressed comments

## Requirements
- Must be on a branch with an associated PR
- Requires GitHub CLI (gh) authentication

## Process
1. Get PR number: `gh pr view --json number`
2. Fetch inline comments: `gh api repos/{owner}/{repo}/pulls/{pr}/comments`
3. Fetch general comments: `gh pr view --json comments`
4. Fetch review comments: `gh api repos/{owner}/{repo}/pulls/{pr}/reviews`
5. For each comment:
   - Present to assistant
   - Generate response
   - Post reply via `gh api`
6. Summarize all actions taken
```

**Key API calls**:
```bash
# Get all inline comments
gh api repos/{owner}/{repo}/pulls/{pr}/comments

# Reply to inline comment
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
  -f body="✅ DONE: Fixed the issue..."

# Get review comments
gh api repos/{owner}/{repo}/pulls/{pr}/reviews

# Reply to review comment
gh api repos/{owner}/{repo}/pulls/{pr}/reviews/{review_id}/comments \
  -f body="✅ DONE: Addressed this concern..."
```

## Files to Create/Modify

### Modify
1. `.claude/commands/handoff.md` - Add /r integration
2. `.claude/commands/handoff.sh` (if exists) - Add roadmap update logic

### Create
1. `.claude/commands/commentreply.md` - New command documentation
2. `.claude/commands/commentr.md` - Alias pointing to commentreply.md

## Testing Requirements

### /handoff Enhancement Testing
1. Run `/handoff test_task "Test description"`
2. Verify:
   - PR created as usual
   - Task automatically added to roadmap.md
   - Correct formatting and PR link
   - No duplicate entries

### /commentreply Testing
1. Create test PR with various comment types:
   - Inline code comments
   - General PR comments
   - Review comments
   - Suppressed Copilot comments
2. Run `/commentreply`
3. Verify:
   - All comments fetched
   - Each addressed with DONE/NOT DONE
   - Inline replies posted
   - Summary provided

## Success Criteria
1. `/handoff` automatically updates roadmap.md without manual intervention
2. `/commentreply` addresses 100% of PR comments
3. Clear DONE/NOT DONE status for each comment
4. Inline replies visible on GitHub
5. Summary helps track what was addressed

## Implementation Notes
- Use existing GitHub API patterns from codebase
- Ensure error handling for missing PRs
- Consider rate limiting for many comments
- Test with both public and private repos

## Timeline Estimate
- /handoff enhancement: 1-2 hours
- /commentreply implementation: 2-3 hours
- Testing: 1 hour
Total: ~4-6 hours