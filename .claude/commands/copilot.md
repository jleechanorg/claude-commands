# GitHub Copilot PR Analysis - Repeatable LLM Workflow

**First, run parallel data collection. Then analyze and take action.**

## Phase 1: Parallel Data Collection (RUN NOW)

Execute the Python data collector to gather all PR information in parallel:

```bash
python3 .claude/commands/copilot.py $ARGUMENTS
```

**Note**: Replace `$ARGUMENTS` with the actual PR number when executing (e.g., `722` for PR #722).

The collector runs **parallel data fetching** using ThreadPoolExecutor:
- Comments fetching (GitHub API)
- CI status checking (GraphQL)  
- Local CI replica execution

Wait for parallel collection to complete, then proceed to Phase 2.

**Data Location**: `/tmp/copilot_pr_[PR_NUMBER]/` (e.g., `/tmp/copilot_pr_722/`)

## Phase 2: LLM Analysis and Action (YOUR TASK)

You are now in the analysis phase. Follow this systematic workflow:

### Step 1: Read Collected Data

First, examine what data was collected:

```bash
# Read the data summary (replace [PR_NUMBER] with actual PR number)
Read /tmp/copilot_pr_[PR_NUMBER]/summary.md

# Read all comments for analysis  
Read /tmp/copilot_pr_[PR_NUMBER]/comments.json

# Check CI status
Read /tmp/copilot_pr_[PR_NUMBER]/ci_status.json

# Check local CI result
Read /tmp/copilot_pr_[PR_NUMBER]/ci_replica.txt

# Get comment ID mapping for replies
Read /tmp/copilot_pr_[PR_NUMBER]/comment_id_map.json
```

### Step 2: Categorize Issues by Priority

Analyze all comments and CI failures, categorizing by:

- 🚨 **CRITICAL**: Test failures, build errors, security vulnerabilities, logic errors
- ⚠️ **HIGH**: Performance issues, potential bugs, merge conflicts
- 💡 **MEDIUM**: Code quality improvements, best practices
- 🎨 **LOW**: Style, formatting, documentation

### Step 3: Apply Automatic Fixes

For issues you can confidently fix automatically:

1. **Test Failures**: Fix failing tests, update assertions, resolve import errors
2. **Build Errors**: Fix compilation issues, resolve dependencies
3. **Security Issues**: Apply security best practices, fix vulnerabilities
4. **Style Issues**: Apply formatting, fix linting errors
5. **Logic Errors**: Fix obvious bugs when the solution is clear

Use Edit/MultiEdit tools to apply fixes directly to files.

### Step 4: Reply to Comments Using Threaded Replies

For each comment that requires a response, use threaded replies for proper conversation flow:

**Primary Method - GitHub CLI Threaded Replies:**
```bash
# WORKING: Direct threaded replies to individual inline comments
# CRITICAL: Use -F flag for comment ID (number) and -f flag for text (string)

# For each comment ID from comment_id_map.json:
gh api repos/jleechanorg/worldarchitect.ai/pulls/[PR_NUMBER]/comments \
  -f body="✅ FIXED: [Specific response to this comment]" \
  -F in_reply_to=COMMENT_ID

# Example with actual IDs:
# Reply to Copilot suggestion on line 278:
gh api repos/jleechanorg/worldarchitect.ai/pulls/775/comments \
  -f body="✅ FIXED: Applied your suggestion and updated the placeholder." \
  -F in_reply_to=2217902292

# Reply to Copilot suggestion on line 279:  
gh api repos/jleechanorg/worldarchitect.ai/pulls/775/comments \
  -f body="✅ FIXED: Updated find command as recommended." \
  -F in_reply_to=2217902296
```

**Alternative Method - GitHub MCP Review (for multiple related comments):**
```
mcp__github-server__create_pull_request_review(
  owner="jleechanorg",
  repo="worldarchitect.ai", 
  pull_number=[PR_NUMBER],
  body="✅ ADDRESSED: Applied all automated suggestions",
  event="COMMENT",
  comments=[
    {
      "path": "file.py",
      "line": 123,
      "body": "✅ FIXED: [Specific fix description]"
    }
  ]
)
```

**Backup Method - General PR Comment (if threading fails):**
# If neither threaded replies nor MCP reviews work, use general PR comment:
gh pr comment [PR_NUMBER] --body "✅ ADDRESSED ALL: [Summary of all fixes applied]"

# KEY INSIGHTS FOR THREADED REPLIES:
# - Endpoint: /repos/{owner}/{repo}/pulls/{pr}/comments  
# - Parameter: in_reply_to=[COMMENT_ID]
# - Use -F flag for in_reply_to (treats as number)
# - Use -f flag for body text (treats as string)  
# - Creates proper threaded conversations like web interface
=======
# CORRECT: Create review with line-specific comments (if MCP fails)
# 1. Create JSON file with review data
cat > /tmp/review_response.json << 'EOF'
{
  "body": "✅ ADDRESSED: Applied all suggestions",
  "event": "COMMENT", 
  "comments": [
    {
      "path": "file.py",
      "line": 123,
      "body": "✅ FIXED: Applied your suggestion and updated the logic."
    }
  ]
}
EOF

# 2. Submit the review
gh api repos/jleechanorg/worldarchitect.ai/pulls/[PR_NUMBER]/reviews --input /tmp/review_response.json

# WRONG: Don't use these (they create general comments, not line-specific):
# gh pr comment [PR_NUMBER] --body "general response"
# gh api .../pulls/[PR_NUMBER]/comments -f body="..." -F in_reply_to="ID"

**Comment ID Reference**: Use `/tmp/copilot_pr_[PR_NUMBER]/comment_id_map.json` to find comment IDs

**📚 Complete Guide**: See `docs/github-threaded-replies-guide.md` for comprehensive documentation on GitHub threaded replies

### Step 5: Generate Final Report

Create a comprehensive report showing:

```
# PR #[PR_NUMBER] Mergeability Report

## 🚨 CRITICAL Issues (X total)
1. [FILE:LINE] Issue description → ✅ FIXED: Explanation + commit hash
2. [FILE:LINE] Issue description → 📋 NEEDS REVIEW: Why manual review needed

## ⚠️ HIGH Priority (X total)  
1. [FILE:LINE] Issue description → ✅ FIXED: Applied optimization
2. [FILE:LINE] Issue description → 🔄 MODIFIED: Made adjustment with reasoning

## 💡 MEDIUM Priority (X total)
1. [FILE:LINE] Issue description → ✅ APPLIED: Improved code quality  
2. [FILE:LINE] Issue description → ❌ DECLINED: Reasoning for declining

## 🎨 LOW Priority (X total)
1. [FILE:LINE] Issue description → ✅ FIXED: Applied formatting
2. [FILE:LINE] Issue description → ❌ SKIPPED: Non-blocking cosmetic issue

## 📊 Summary
- **Total Issues**: X analyzed
- **Automatically Fixed**: X issues resolved
- **Comments Replied**: X responses posted  
- **Tests Status**: ✅ ALL PASSING / ❌ X STILL FAILING
- **CI Status**: ✅ ALL CHECKS PASS / ❌ X CHECKS FAILING

## 🎯 PR Status: [READY TO MERGE / NEEDS MANUAL REVIEW / BLOCKED]

**Reasoning**: [Explanation of final status]
```

## Success Criteria

The PR is ready to merge when:
- ✅ All critical issues are fixed
- ✅ All tests pass (run tests to verify)
- ✅ All CI checks pass
- ✅ All actionable comments have been addressed
- ✅ All bot suggestions have been replied to

## Workflow Summary

This is a **repeatable process**:

1. **Parallel Data Collection** (Python script with ThreadPoolExecutor) → 
2. **LLM Analysis** (you analyze comments.json) → 
3. **Apply Fixes** (you use Edit tools) → 
4. **Reply to Comments** (you use GitHub MCP/CLI) → 
5. **Generate Report** (you create mergeability report)

**Key Files:**
- `comments.json` - All PR comments to analyze
- `ci_status.json` - CI check status  
- `comment_id_map.json` - For replying to specific comments
- `summary.md` - Human-readable overview

**Tools Available:**
- GitHub MCP for comment replies and PR operations
- Edit/MultiEdit for code fixes
- Bash for running tests and verification
- Read for examining files and data

The parallel data collection phase is complete. **Begin your analysis now.**