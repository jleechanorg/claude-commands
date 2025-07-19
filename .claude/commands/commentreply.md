# /commentreply Command

Systematically addresses all GitHub PR comments with inline replies and status tracking.

## Usage
```
/commentreply
/commentr (alias)
```

## What it does

1. **Detects Current PR**: Gets PR number from current branch
2. **Fetches ALL Comments**: Retrieves inline, general, and review comments
3. **Presents Each Comment**: Shows context and asks for response
4. **Addresses Systematically**: For each comment:
   - Analyze the feedback
   - Implement fix if needed
   - Mark as ✅ DONE or ❌ NOT DONE with explanation
   - Post inline reply via GitHub API
5. **Provides Summary**: Lists all comments addressed in chat

## Comment Types Handled

- **Inline Code Comments**: Specific to file lines
- **General PR Comments**: Overall feedback
- **Review Comments**: From PR reviews
- **Suppressed Comments**: Including Copilot suggestions

## Process Flow

### 1. Discovery Phase
```bash
# Get current PR
PR_NUMBER=$(gh pr view --json number -q .number)

# Get repository info
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
```

### 2. Comment Fetching
```bash
# Fetch inline comments
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments"

# Fetch general comments  
gh pr view --json comments -q .comments

# Fetch review comments
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews"
```

### 3. Response Processing
For each comment:
1. **Present to user**: Show comment text and context
2. **Get response**: User addresses the feedback
3. **Status determination**: Mark as DONE or NOT DONE
4. **Post reply**: Use GitHub API to respond inline

### 4. API Reply Examples
```bash
# Reply to inline comment
gh api "repos/$OWNER/$REPO/pulls/comments/$COMMENT_ID/replies" \
  -f body="✅ DONE: Fixed the issue by updating the validation logic"

# Reply to review comment
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews/$REVIEW_ID/comments" \
  -f body="❌ NOT DONE: This change is intentional for performance reasons"
```

## Response Format

Each reply follows this format:
- **✅ DONE**: `✅ DONE: [explanation of fix/change made]`
- **❌ NOT DONE**: `❌ NOT DONE: [reason why not addressed]`

## Summary Output

At the end, provides a comprehensive summary:
```
## Comment Response Summary

### ✅ Addressed (5 comments)
1. Line 23 validation issue → Fixed null check
2. Performance concern → Added caching
3. Code style issue → Applied formatting
4. Missing error handling → Added try/catch
5. Documentation request → Added docstring

### ❌ Not Addressed (2 comments)  
1. Architecture change → Out of scope for this PR
2. Optional enhancement → Deferring to future work

### API Responses Posted: 7 inline replies
```

## Requirements

- Must be on a branch with an associated PR
- Requires GitHub CLI (`gh`) authentication
- GitHub API access for posting replies

## Error Handling

- **No PR found**: Clear error message with guidance
- **API failures**: Retry mechanism for network issues
- **Invalid comments**: Skip malformed comments with warning
- **Permission issues**: Clear explanation of auth requirements

## Example Usage

```bash
# Basic usage
/commentreply

# Will process all comments like:
# Comment 1: "This function needs error handling"
# → User: "Added try/catch block"  
# → Status: ✅ DONE
# → Reply: "✅ DONE: Added try/catch block for error handling"
```

## Benefits

- **No comments missed**: Systematic processing of ALL feedback
- **Clear audit trail**: Visible status for each comment
- **Inline visibility**: Responses appear directly on GitHub
- **Time savings**: Automated posting of formatted replies
- **Accountability**: Clear DONE/NOT DONE tracking

## Integration with PR Workflow

Works seamlessly with existing PR processes:
1. Create PR and receive comments
2. Run `/commentreply` to address all feedback
3. Continue with normal PR review cycle
4. All stakeholders see inline responses immediately

## Command Aliases

- `/commentreply` - Full command name
- `/commentr` - Short alias for convenience