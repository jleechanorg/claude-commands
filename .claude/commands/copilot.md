# GitHub Copilot PR Analysis - Repeatable LLM Workflow

**First, run data collection. Then analyze and take action.**

## Phase 1: Data Collection (RUN NOW)

Execute the Python data collector to gather all PR information:

```bash
python3 .claude/commands/copilot.py $ARGUMENTS
```

**Note**: Replace `$ARGUMENTS` with the actual PR number when executing (e.g., `722` for PR #722).

Wait for completion, then proceed to Phase 2.

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

### Step 4: Reply to Comments Using GitHub MCP

For each comment that requires a response, use GitHub MCP with CLI fallback:

**Primary Method - GitHub MCP (try first):**
```
mcp__github-server__create_pull_request_review(
  owner="jleechanorg",
  repo="worldarchitect.ai", 
  pull_number=[PR_NUMBER],  # Replace with actual PR number
  body="Response to all comments",
  event="COMMENT",
  comments=[
    {
      "path": "file.py",
      "line": 123,
      "body": "✅ FIXED: Applied your suggestion and updated the logic."
    }
  ]
)
```

**Fallback Method - GitHub CLI:**
```bash
# For inline comments (if MCP fails) - replace [PR_NUMBER] with actual number
gh api repos/jleechanorg/worldarchitect.ai/pulls/[PR_NUMBER]/comments \
  -f body="✅ FIXED: Applied your suggestion" \
  -F in_reply_to="COMMENT_ID"

# For general PR comments
gh pr comment [PR_NUMBER] --body "✅ ADDRESSED: All issues resolved"
```

**Comment ID Reference**: Use `/tmp/copilot_pr_[PR_NUMBER]/comment_id_map.json` to find comment IDs

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

1. **Data Collection** (Python script) → 
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

The data collection phase is complete. **Begin your analysis now.**