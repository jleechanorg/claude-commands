# GitHub Copilot PR Analysis - Autonomous LLM Workflow

🚨 **AUTONOMOUS OPERATION MODE**: This workflow operates without user prompts or approval requests

**First, run immediate status check. Then data collection. Then analyze and take action autonomously.**

## Phase 0: Immediate GitHub Status Check (RUN FIRST)

Execute GitHub MCP call immediately for PR status:

```python
# Get immediate PR status via GitHub MCP
pr_data = mcp__github_server__get_pull_request(
    owner="jleechanorg", 
    repo="worldarchitect.ai", 
    pull_number=$ARGUMENTS  # Replace with actual PR number
)

print(f"🔍 PR #{$ARGUMENTS} Immediate Status:")
print(f"  📊 Mergeable: {pr_data.get('mergeable')}")  
print(f"  📋 State: {pr_data.get('state')}")
print(f"  ✅ CI Status: {len(pr_data.get('status_check_rollup', []))} checks")

# AUTONOMOUS processing - no user prompts
if pr_data.get('mergeable') == 'CONFLICTING':
    print("⚠️ CONFLICTS DETECTED: Will analyze and auto-resolve")
    conflicts_detected = True
elif pr_data.get('mergeable') == 'UNKNOWN':
    print("🔄 GitHub still calculating merge status - proceeding with analysis")
    conflicts_detected = False
else:
    print("✅ No conflicts detected")
    conflicts_detected = False
```

**Always proceed to Phase 1 data collection - autonomous operation**

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

# Check GitHub status collected by Python
Read /tmp/copilot_pr_[PR_NUMBER]/github_status.json
```

### Step 1.5: Cross-Validate GitHub Status

Compare immediate MCP results with Python-collected data:

```bash
# Read Python-collected GitHub status
cat /tmp/copilot_pr_[PR_NUMBER]/github_status.json

# Cross-validation analysis:
# Phase 0 MCP: [status from Phase 0 - check conflicts_detected variable]
# Phase 1 Python: [status from github_status.json file]
# 
# Expected consistency:
# - Both should show same mergeable status
# - Both should detect same conflicts
# - Any discrepancies indicate timing issues or API changes
```

**Autonomous decision making**: If results differ, prioritize most recent data and proceed with analysis.

### Step 2: Categorize Issues by Priority (AUTONOMOUS)

Analyze all comments and CI failures with autonomous resolution:

- 🚨 **CRITICAL**: Merge conflicts, test failures, build errors, security vulnerabilities → **AUTO-FIX IMMEDIATELY**
- ⚠️ **HIGH**: Performance issues, potential bugs, CI failures → **AUTO-ADDRESS**  
- 💡 **MEDIUM**: Code quality improvements, best practices → **AUTO-APPLY**
- 🎨 **LOW**: Style, formatting, documentation → **AUTO-FORMAT**

**Autonomous Operation**: Claude automatically applies ALL fixes without user prompts or confirmations.

### Step 3: Apply Automatic Fixes (AUTONOMOUS)

For ALL detected issues, apply fixes without asking permission:

1. **Merge Conflicts**: Auto-resolve using conflict resolution strategies, prefer functionality preservation
2. **Test Failures**: Fix failing tests, update assertions, resolve import errors  
3. **Build Errors**: Fix compilation issues, resolve dependencies
4. **Security Issues**: Apply security best practices, fix vulnerabilities
5. **Style Issues**: Apply formatting, fix linting errors
6. **Logic Errors**: Fix obvious bugs when the solution is clear
7. **CI Failures**: Address build/lint issues that block PR approval

**Autonomous Execution**: Use Edit/MultiEdit tools to apply ALL fixes directly. No user confirmation required.

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

**Fallback Method - GitHub CLI Reviews:**
```bash
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
```

**Backup Method - General PR Comment (if threading fails):**
```bash
# If neither threaded replies nor MCP reviews work, use general PR comment:
gh pr comment [PR_NUMBER] --body "✅ ADDRESSED ALL: [Summary of all fixes applied]"
```

**KEY INSIGHTS FOR THREADED REPLIES:**
- Endpoint: /repos/{owner}/{repo}/pulls/{pr}/comments  
- Parameter: in_reply_to=[COMMENT_ID]
- Use -F flag for in_reply_to (treats as number)
- Use -f flag for body text (treats as string)  
- Creates proper threaded conversations like web interface

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