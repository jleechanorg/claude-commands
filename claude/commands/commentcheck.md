# /commentcheck Command

**Usage**: `/commentcheck [PR_NUMBER]`

**Purpose**: Verify 100% comment coverage and response quality after comment reply process.

## Description

Pure markdown command (no Python executable) that systematically verifies all PR comments have been properly addressed with appropriate responses. This command runs AFTER `/commentreply` to ensure nothing was missed.

## What It Does

1. **Loads comments data** from `/tmp/copilot/comments.json` 
2. **Fetches current PR comment responses** from GitHub API
3. **Cross-references** original comments with posted responses
4. **Verifies coverage** - ensures every comment has a corresponding response
5. **Quality check** - confirms responses are substantial, not generic
6. **Reports status** with detailed breakdown

## Verification Process

### Step 1: Load Original Comments
```bash
# Read the original comment data collected by /commentfetch
cat /tmp/copilot/comments.json | jq '.comments | length'
```

### Step 2: Fetch Current PR Responses  
```bash
# Get all current comments/responses from GitHub
gh pr view [PR_NUMBER] --json comments
gh api "/repos/owner/repo/pulls/[PR_NUMBER]/comments"
```

### Step 3: Coverage Analysis
For each original comment:
- **Match by ID** - Find corresponding response thread
- **Check response exists** - Verify response was actually posted
- **Validate content** - Ensure response addresses the specific comment
- **Confirm threading** - Verify inline responses are properly threaded

### Step 4: Quality Assessment
Response quality criteria:
- **Not generic** - No template responses like "Thanks for feedback"
- **Addresses specifics** - Responds to actual technical content
- **Proper status** - Clear DONE/NOT DONE indication
- **Professional tone** - Appropriate for PR context

## Coverage Report Format

```
## 📊 Comment Coverage Analysis

### ✅ Properly Addressed (X comments)
1. Comment #123 (inline): "Fix validation logic" → ✅ DONE: "Added null check in line 45" 
2. Comment #456 (general): "Update documentation" → ❌ NOT DONE: "Will address in separate PR"
3. Comment #789 (review): "Performance concern" → ✅ DONE: "Optimized with caching"

### ❌ Missing Responses (Y comments)  
1. Comment #111: "Consider error handling" → NO RESPONSE FOUND
2. Comment #222: "Code style issue" → NO RESPONSE FOUND

### ⚠️ Low Quality Responses (Z comments)
1. Comment #333: Generic "Thanks!" response - needs improvement
2. Comment #444: Template response - doesn't address specific concern

### 📈 Coverage Statistics
- Total comments: X
- Properly addressed: Y (Z%)  
- Missing responses: A
- Low quality responses: B
- **Coverage Score: Z%**
```

## Success Criteria

**✅ PASS**: 100% coverage with quality responses
- All comments have responses
- All responses address specific content  
- Appropriate DONE/NOT DONE status
- Professional and substantial replies

**❌ FAIL**: Missing responses or quality issues
- Any comment without response
- Generic/template responses detected
- Responses don't address actual content
- Unprofessional or inadequate replies

## Integration with Workflow

### When to Run
- **After** `/commentreply` completes
- **Before** final `/pushl` in copilot workflow
- **Verify** comment coverage is complete

### Actions on Failure  
If `/commentcheck` finds issues:
1. **Report specific problems** - List missing/poor responses
2. **Suggest fixes** - Indicate what needs improvement  
3. **Prevent completion** - Workflow should not proceed until fixed
4. **Re-run commentreply** - Address missing/poor responses

## Command Flow Integration

```
/commentfetch → /fixpr → /pushl → /commentreply → /commentcheck → /pushl (final)
                                                        ↓
                                               [100% coverage verified]
```

## GitHub API Commands Used

```bash
# Get PR comments
gh pr view $PR_NUMBER --json comments

# Get inline comments with threading info
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate

# Get review comments
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" --paginate  

# Search for AI Responder comments
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" | jq '.[] | select(.body | contains("[AI Responder]"))'
```

## Error Handling

- **No comments.json found**: Clear error with guidance to run `/commentfetch` first
- **GitHub API failures**: Retry mechanism with exponential backoff  
- **Permission issues**: Clear explanation of authentication requirements
- **Malformed data**: Skip problematic entries with warnings

## Benefits

- **Quality assurance** - Ensures responses meet professional standards
- **Complete coverage** - Guarantees no comments are missed
- **Audit trail** - Provides detailed verification report
- **Process improvement** - Identifies patterns in response quality
- **User confidence** - Confirms all feedback was properly addressed

## Example Usage

```bash
# After running /commentreply
/commentcheck 820

# Will analyze all 108 comments and verify:
# ✅ All comments have responses
# ✅ Responses address specific content
# ✅ Proper DONE/NOT DONE classification
# ✅ Professional and substantial replies
# 📊 Generate detailed coverage report
```

This command ensures the comment response process maintains high quality and complete coverage for professional PR management.