# /copilot Command - Intelligent PR Analysis with Universal Composition

**Usage**: `/copilot <PR_NUMBER>`

**Purpose**: Comprehensively analyze and address PR issues using adaptive intelligence.

## 🚨 CRITICAL: EXECUTION GUARANTEE

**MANDATORY STARTUP PROTOCOL**:
```
🤖 /copilot - Starting intelligent PR analysis for PR #[NUMBER]
🔧 Reading PR status and planning workflow...
📊 PR Status: [OPEN/MERGED/CLOSED] | CI: [PASSING/FAILING] | Mergeable: [YES/NO]
🚀 Beginning 6-phase autonomous workflow with full transparency...

=== COPILOT WORKFLOW INITIATED ===
```

**NEVER FAIL SILENTLY**: Every execution MUST show visible progress through all 6 phases
**NEVER STOP EARLY**: Complete all phases unless explicitly blocked by unrecoverable errors
**ALWAYS BE VERBOSE**: Show commands, results, progress, and decisions in real-time

## 🔧 **Commands Used by /copilot (Orchestration)**

**CRITICAL**: /copilot orchestrates existing commands - does NOT duplicate their functionality:

1. **`/commentfetch [PR]`** - Data collection
   - Python: `.claude/commands/_copilot_modules/commentfetch.py`
   - Output: Branch-specific directory `/tmp/copilot_{branch}/comments_{branch}.json`

2. **`/fixpr [PR]`** - Fix CI failures and conflicts FIRST
   - Markdown: `.claude/commands/fixpr.md` (Claude executes)
   - Handles: CI analysis, conflict resolution, code fixes

3. **`/pushl`** - Push fixes to remote
   - Script: `.claude/commands/pushl` (existing command)
   - Handles: git add, commit, push with proper messaging

4. **`/commentreply`** - Comment response processing (AFTER fixes are live)
   - Markdown: `.claude/commands/commentreply.md` (Claude executes)  
   - Handles: All comment types, DONE/NOT DONE tracking, GitHub API posting

5. **`/commentcheck`** - Verify 100% comment coverage
   - Markdown: `.claude/commands/commentcheck.md` (Claude executes)
   - Handles: Coverage verification, quality assessment, response validation

6. **`/pushl`** - Final push if needed
   - For any additional changes made during comment processing

**ARCHITECTURE**: /copilot = orchestrator, NOT implementer

## Description

The `/copilot` command uses **universal composition** to intelligently orchestrate PR analysis and fixes. It leverages Claude's natural language processing to adapt the workflow based on PR needs, maintaining full transparency throughout the process.

## 🚨 CRITICAL: Transparency First

**Before posting ANY replies or making changes**:
1. Generate all responses/fixes
2. Display them in chat for visibility  
3. Indicate which will be auto-posted
4. Then execute with full transparency

**This ensures user awareness of all actions before they happen.**

## 🚨 CRITICAL: NEVER SIMULATE INTELLIGENCE

**This rule has been violated 100+ times and MUST be enforced:**

### ❌ ABSOLUTELY FORBIDDEN - ZERO TOLERANCE:
- NEVER create Python functions that generate "intelligent" responses with templates
- NEVER use pattern matching like `if 'pagination' in comment: return "I'll fix pagination!"`
- NEVER use author-based templating like `if 'coderabbit' in author: return template_response`
- NEVER build `_create_contextual_response()` methods that fake understanding
- NEVER generate generic acknowledgments that don't address specific technical content
- NEVER execute unauthorized Python code for response generation during /copilot

### ✅ MANDATORY REQUIREMENTS:
- ALWAYS read each comment's ACTUAL CONTENT before responding
- ALWAYS use genuine Claude analysis for each individual comment
- ALWAYS address SPECIFIC technical points raised in the comment
- ALWAYS ensure responses demonstrate reading and understanding the comment
- ALWAYS require user approval before executing comment response code

### 🚨 EXPLICIT BAN ON TEMPLATE PATTERNS:
**NEVER use patterns like:**
```python
# FORBIDDEN PATTERN - IMMEDIATE VIOLATION
if 'coderabbit' in author.lower():
    response = 'Thank you CodeRabbit for the comprehensive feedback...'
if 'copilot' in author.lower():
    response = 'Thank you GitHub Copilot for the suggestion...'
```

### ✅ REQUIRED ARCHITECTURE:
1. **Python**: Collects data ONLY (comments, CI status, etc.)
2. **Claude**: Reads ACTUAL comment content for each comment individually
3. **Claude**: Provides genuine analysis based on specific technical content
4. **Claude**: Generates responses addressing exact points raised
5. **User**: Approves any automated response generation

**ENFORCEMENT**: Any template-based response generation is an immediate protocol violation requiring correction.

## 🚨 CRITICAL: 100% INDIVIDUAL Comment Coverage Rule

🚨 **ZERO TOLERANCE POLICY**: EVERY individual comment must be explicitly addressed:

### MANDATORY Individual Comment Requirements
- **ALL individual comments MUST receive direct replies** (no exceptions for bots)
- **Copilot comments MUST be replied to** (technical feedback requires responses)
- **CodeRabbit comments MUST be replied to** (AI suggestions require acknowledgment)
- **Human reviewer comments MUST be replied to** (inline feedback requires responses)

### Status Tracking (DONE/NOT DONE)
- **✅ DONE**: Direct reply posted via GitHub API with technical substance
- **❌ NOT DONE**: Needs response (show the planned response)

### Evidence Requirement
- **PR #864 FAILURE**: 11 individual comments (3 Copilot + 8 CodeRabbit) with ZERO replies
- **PREVENTION**: This MUST NOT happen again - zero tolerance for missed individual comments

**Never leave ambiguity** - systematically reply to ALL individual comments with no exceptions!

## 🚨 DELEGATION TO EXISTING COMMANDS

**CRITICAL**: /copilot does NOT reimplement existing functionality. Instead:

### Comment Processing → Use `/commentreply`
- **Why**: `.claude/commands/commentreply.md` already has complete systematic protocol
- **What it handles**: All comment types, DONE/NOT DONE tracking, GitHub API threading
- **Result**: 100% comment coverage with proper inline responses

### Git Operations → Use `/pushl`  
- **Why**: `.claude/commands/pushl` already handles git add/commit/push workflow
- **What it handles**: Staging, committing, pushing, verification
- **Result**: Clean git operations with proper messaging

### Data Collection → Use `/commentfetch`
- **Why**: `.claude/commands/_copilot_modules/commentfetch.py` already fetches all comment types
- **What it handles**: Inline, general, review, Copilot comments → branch-specific comments file  
- **Result**: Complete comment data for processing

## How It Works

🚨 **MANDATORY EXECUTION SEQUENCE** - Every step MUST be completed with VERBOSE OUTPUT:

## 🚨 CRITICAL: MANDATORY VERBOSE OUTPUT

**EVERY phase MUST produce visible output in chat:**
- ✅ **Start Message**: "🔧 PHASE X: [Phase Name] - Starting..."
- ✅ **Progress Updates**: Show commands being executed and their results
- ✅ **Success/Failure**: Clear indication of phase completion status
- ✅ **Error Details**: If phase fails, show exact error and recovery steps
- ✅ **Phase Summary**: "✅ PHASE X COMPLETE" or "❌ PHASE X FAILED: [reason]"
- ❌ **NEVER SILENT**: No phase may execute without chat visibility

**ENFORCEMENT**: If any phase produces no output, it's considered a failure requiring immediate correction.

### PHASE 1: Data Collection (MANDATORY)
**🔧 PHASE 1: DATA COLLECTION - Starting...**

1. **MUST RUN** `/commentfetch [PR]` to gather ALL comments → branch-specific directory
   - Show: "Running `/commentfetch [PR]`..."
   - Show: Command output and comment count found
   - Show: "Comments saved to /tmp/copilot_{branch}/comments_{branch}.json"

2. **MUST VERIFY** data collection completed successfully
   - Show: "Verifying comment data collection..."
   - Show: Total comment count and breakdown by type
   - Show: File size and data validation results

3. **FAIL IF**: Comments not collected or data incomplete
   - Show: Exact error message and troubleshooting steps
   - Show: Recovery actions being attempted

**OUTPUT**: "✅ PHASE 1 COMPLETE: [X] comments collected" or "❌ PHASE 1 FAILED: [detailed error]"

### PHASE 2: Fix Issues First (MANDATORY)
**🔧 PHASE 2: ISSUE FIXING - Starting...**

**MUST RUN** `/fixpr [PR]` to resolve CI failures and conflicts:
- Show: "Running `/fixpr [PR]`..."
- Show: "Analyzing CI status and conflicts..."
- **MANDATORY**: Analyze and resolve test failures, linting errors
  - Show: "CI Status: [passing/failing] - [X] checks found"
  - Show: Each CI failure with analysis and fix plan
- **MANDATORY**: Handle merge conflicts and compatibility issues
  - Show: "Merge Status: [mergeable/conflicts] - [X] conflicts found"  
  - Show: Each conflict with resolution strategy
- **MANDATORY**: Apply necessary fixes based on analysis
  - Show: "Applying [X] fixes: [list of changes]"
  - Show: Each file being modified and why
- **MANDATORY**: Ensure fixes are ready before commenting
  - Show: "Verifying all fixes applied successfully..."
- **FAIL IF**: CI failures remain or conflicts unresolved
  - Show: Remaining issues and why they couldn't be resolved

**OUTPUT**: "✅ PHASE 2 COMPLETE: [X] issues fixed" or "❌ PHASE 2 FAILED: [detailed issues remaining]"

### PHASE 3: Push Fixes (MANDATORY)
**🔧 PHASE 3: PUSHING FIXES - Starting...**

**MUST RUN** `/pushl` to push all fixes to remote:
- Show: "Running `/pushl`..."
- **MANDATORY**: Stage and commit all code improvements
  - Show: "Staging [X] modified files..."
  - Show: "Commit message: [message]"
  - Show: Git add/commit command results
- **MANDATORY**: Push to remote - Make fixes available on GitHub
  - Show: "Pushing to origin/[branch]..."
  - Show: Push command output and success confirmation
- **MANDATORY**: Verify deployment - Confirm fixes are live before responding
  - Show: "Verifying fixes are live on GitHub..."
  - Show: Remote commit verification results
- **FAIL IF**: Fixes not pushed or verification fails
  - Show: Exact git error and troubleshooting steps
  - Show: Manual commands needed to resolve

**OUTPUT**: "✅ PHASE 3 COMPLETE: Fixes pushed and verified" or "❌ PHASE 3 FAILED: [git error details]"

### PHASE 4: Comment Response Processing (MANDATORY) - ENHANCED AUTONOMOUS GENUINE INTELLIGENCE
**🔧 PHASE 4: COMMENT PROCESSING - Starting...**

**MUST RUN** `/commentreply` (AFTER fixes are live):
- Show: "Running `/commentreply` for [X] comments..."
- Show: "Loading comment data from branch-specific directory..."
- Show: "Comment breakdown: [X] inline, [X] general, [X] review, [X] bot comments"

🚨 **MANDATORY GENUINE ANALYSIS WORKFLOW** - For EACH comment individually:
1. ✅ **Read Actual Content**: Load comment.body from branch-specific comments file (never skip reading)
   - Show: "Processing comment #[ID] from [author]: [first 50 chars]..."
2. ✅ **Genuine Analysis**: Analyze specific technical content (no pattern matching allowed)
   - Show: "Analyzing technical content: [key points identified]"
3. ✅ **Address Specifics**: Generate response targeting exact points raised in comment
   - Show: "Generated response: [first 100 chars of response]..."
4. ✅ **Self-Validation**: Ask "Does this response demonstrate I read the actual comment?"
   - Show: "Self-validation: ✅ PASS" or "❌ FAIL - regenerating..."
5. ✅ **Authentic Posting**: Post via GitHub API with genuine technical analysis
   - Show: "Posting reply via GitHub API... Response ID: [ID]"

**AUTONOMOUS OPERATION REQUIREMENTS**:
- **MANDATORY**: Process ALL individual comments (including bot comments)
  - Show: "Processing [X]/[total] comments... Current: [comment summary]"
- **MANDATORY**: DONE/NOT DONE tracking for every single comment
  - Show: "Status: ✅ DONE - [reason]" or "❌ NOT DONE - [reason]"
- **MANDATORY**: Post direct replies to ALL individual comments via GitHub API
  - Show: "Posted [X]/[total] replies successfully"
- **MANDATORY**: Each response must demonstrate reading actual comment content
  - Show: "Quality check: Response addresses specific technical points"
- **FAIL IF**: ANY individual comment left without response (zero tolerance)
  - Show: "ERROR: [X] comments remaining without responses"
- **FAIL IF**: ANY response shows template patterns or fails self-validation
  - Show: "ERROR: Template pattern detected in response to comment #[ID]"

**LARGE VOLUME HANDLING**: For 100+ comments:
- Show: "⚠️ LARGE VOLUME: [X] comments detected"
- Show: "Processing in batches of 50 for stability..."
- Show: "Batch [X]/[Y] progress: [X]% complete"
- Show: "ETA: [estimated time] remaining"

**OUTPUT**: "✅ PHASE 4 COMPLETE: [X]/[X] comments processed, [X] responses posted" or "❌ PHASE 4 FAILED: [X] comments failed processing"

### PHASE 5: Verification (MANDATORY)
**🔧 PHASE 5: VERIFICATION - Starting...**

**MUST RUN** `/commentcheck` to verify 100% individual comment coverage:
- Show: "Running `/commentcheck` for coverage verification..."
- **MANDATORY**: Verify ALL individual comments received responses
  - Show: "Checking [X] comments for response coverage..."
  - Show: "Coverage analysis: [X]/[X] comments have responses ([X]%)"
- **MANDATORY**: Quality assessment - responses are substantial and appropriate
  - Show: "Quality assessment: [X] responses pass quality check"
  - Show: "Template patterns detected: [X] responses flagged"
- **MANDATORY**: Generate detailed coverage report with bot comment tracking
  - Show: "Bot comment coverage: Copilot [X]/[X], CodeRabbit [X]/[X]"
  - Show: "Coverage report generated with detailed breakdown"
- **FAIL IF**: Coverage < 100% or any bot comments without responses
  - Show: "COVERAGE FAILURE: [X] comments missing responses"
  - Show: "Missing responses: [list of comment IDs and authors]"

**OUTPUT**: "✅ PHASE 5 COMPLETE: 100% coverage verified" or "❌ PHASE 5 FAILED: [X]% coverage, [X] missing responses"

### PHASE 6: Final Operations (CONDITIONAL - MANDATORY IF NEEDED)
**🔧 PHASE 6: FINAL OPERATIONS - Starting...**

**MUST RUN** `/pushl` if additional changes made during verification:
- Show: "Checking for uncommitted changes..."
- Show: "Git status: [X] files modified, [X] files staged"
- **MANDATORY**: Final commit for any updates made during comment verification
  - Show: "Final commit: [commit message]"
  - Show: "Committing [X] files with verification updates"
- **MANDATORY**: Complete workflow - ensure all changes pushed and verified
  - Show: "Final push to origin/[branch]..."
  - Show: "Workflow completion verification..."
- **FAIL IF**: Changes made but not committed/pushed
  - Show: "ERROR: [X] uncommitted changes detected"
  - Show: "Manual cleanup required: [list of files]"

**OUTPUT**: "✅ PHASE 6 COMPLETE: Final changes committed and pushed" or "✅ PHASE 6 SKIPPED: No additional changes" or "❌ PHASE 6 FAILED: [git issues]"

🚨 **ENFORCEMENT**: Each phase MUST complete successfully before proceeding to next phase. NO skipping steps.

## 🚨 CRITICAL: NO SILENT FAILURES

**MANDATORY CONTINUATION RULES**:
- ❌ **NEVER stop silently** - Always show what's happening
- ❌ **NEVER skip phases** - Execute all 6 phases in sequence  
- ❌ **NEVER assume success** - Verify each phase completion
- ✅ **ALWAYS show progress** - Verbose output for every action
- ✅ **ALWAYS continue on errors** - Show error and attempt recovery
- ✅ **ALWAYS complete workflow** - Push through to Phase 6 unless blocked

**LARGE VOLUME PROTOCOL**: For 100+ comments:
- ✅ **Show warning**: "⚠️ LARGE VOLUME: [X] comments - this will take time"
- ✅ **Batch processing**: Process in groups with progress updates
- ✅ **Continue automatically**: No user approval required for autonomous operation
- ✅ **Show ETA**: Estimated completion time based on progress
- ✅ **Error recovery**: If batch fails, continue with remaining batches

**Key Principles:**
- **Zero tolerance for missed comments** - every single one gets processed
- **Complete transparency** - show everything before doing it  
- **Systematic execution** - follow the protocol exactly, no shortcuts
- **Proper threading** - responses appear in the right place
- **Self-improving** - commit any improvements made during execution
- **Complete workflow** - from comment analysis to git operations

### Command Composition Integration:

#### Primary Command: `/commentfetch [PR]`
- **Data Collection**: Gathers ALL comments from PR
- **Output**: Branch-specific directory with complete comment data
- **Role**: The foundation - provides data for systematic processing

#### Integrated Processing (via copilot.md protocol):
- **Comment Analysis**: Claude reads branch-specific comments file directly
- **Response Generation**: Claude creates responses using the systematic protocol
- **GitHub API Execution**: Claude posts responses with proper threading
- **Verification**: Claude confirms 100% coverage achieved

#### Supporting Commands (as needed):
- **`/fixpr [PR]`**: For CI failures (if detected during analysis)
- **`/pushl`**: For git operations (if code changes needed)
- **Direct `gh` commands**: For response posting and verification

#### Direct Tools (Claude executes):
- `gh pr checks` - Quick CI status check
- `gh pr view --json` - Get PR metadata
- `gh api` - Direct API calls when needed
- File editing - Apply fixes directly

**The Clean Flow**: /commentfetch (Python) → Claude reads .md files → Claude executes everything directly

## Universal Composition Approach

The command adapts based on PR needs:

### **No Issues Found**
Quick assessment and confirmation that PR is clean

### **Comments Only**
1. Fetch comments using `commentfetch.py`
2. Analyze which need responses
3. **Display ALL planned replies in chat**
4. Auto-post obvious acknowledgments
5. Show which replies need manual review

### **CI Failures**
1. Check CI status across multiple layers
2. Analyze root causes
3. **Show planned fixes before applying**
4. Execute fixes with visibility
5. Verify resolution

### **Complex PRs**
Full orchestration combining all capabilities with complete transparency at each step

## The Clean Data Flow

```
PHASE 1: DATA COLLECTION
/commentfetch → branch-specific comments file (ONLY Python usage)
     ↓
PHASE 2: INTELLIGENT ORCHESTRATION
/copilot reads all .md files and data
     ↓
PHASE 3: TRANSPARENT PLANNING
Claude shows ALL planned actions in chat
     ↓
PHASE 4: DIRECT EXECUTION
/fixpr - Claude analyzes CI and fixes issues
/commentreply - Claude posts replies via gh api
/pushl - Git operations when needed
```

**Clean Architecture**: Minimal Python (only /commentfetch), .md files for intelligence, Claude executes directly

## Example Flow

### Simple PR with comments:
```
/copilot 123
> Analyzing PR #123...
> 
> ## 🔧 Composing Commands:
> 
> 1. Running /commentfetch 123...
>    ✅ Found 5 comments → branch-specific directory
> 
> 2. Running /fixpr 123...
>    ✅ Claude reads fixpr.md and checks CI status
>    ✅ No failures or conflicts found
> 
> 3. Analyzing comments (100% coverage):
>    - @user "Fix pagination" - NOT DONE
>    - @bot "CI passed" - DONE (informational)
>    - @reviewer "LGTM" - DONE (approval)
>    - @user "Add tests" - NOT DONE
>    - @user "Thanks!" - DONE (acknowledgment)
> 
> 4. Running /commentreply...
>    ✅ Claude reads commentreply.md
>    ✅ Posting 2 responses directly via gh api:
>    → "Fixed pagination in commit abc123"
>    → "Added tests in test_edge_cases.py"
> 
> ✅ Complete! Orchestrated all 4 modular commands
```

### PR with CI failures:
```
/copilot 456
> Analyzing PR #456...
> 
> ## 🔧 Composing Commands:
> 
> 1. Running /commentfetch 456...
>    ✅ Found 3 comments → branch-specific directory
>
> 2. Running /fixpr 456...
>    ✅ Claude reads fixpr.md and analyzes CI
>    - GitHub CI: 2 failures detected
>    - Analyzing failure patterns...
>    
>    ## 🔧 Planned Fixes:
>    1. **Test failure in test_auth.py**: Missing import statement
>    2. **Linting error in main.py**: Unused variable
> 
> 3. [Shows exact changes before applying]
> 
> 4. Applying fixes directly...
>    ✅ Fixed both issues
> 
> 5. Running /pushl to commit and push...
>    ✅ Pushed fixes to remote
> 
> ✅ Complete! Used /fixpr + direct fixes + /pushl
```

### Complex PR with everything:
```
/copilot 789
> Analyzing PR #789...
> 
> ## 🔧 Full Orchestration:
> 
> 1. Running /commentfetch 789...
>    ✅ Found 12 comments → branch-specific directory
>    - 8 need responses (NOT DONE)
>    - 4 informational (DONE)
> 
> 2. Running /fixpr 789...
>    ✅ Collected comprehensive data:
>    - GitHub CI: 3 failures, 1 timeout
>    - Local CI: 2 failures reproduced
>    - Merge conflicts: 2 files conflicted
> 
> 3. Intelligent Analysis Phase:
>    [Using fixpr.md + commentreply.md intelligence]
>    
>    ## Fixes Identified:
>    - Import error: Add missing firebase import
>    - Test timeout: Increase async timeout to 30s
>    - Flaky test: Add retry logic
>    - Conflicts: Merge both feature additions
>    
>    ## Responses Generated:
>    - Technical replies for 8 comments
>    - Acknowledgments where appropriate
> 
> 4. Execution Phase:
>    a. Applying code fixes...
>       ✅ Fixed all 3 CI issues
>    b. Resolving conflicts...
>       ✅ Merged changes preserving both features
>    c. Running /commentreply 789...
>       ✅ Posted 8 responses
>    d. Running /pushl...
>       ✅ Committed and pushed all fixes
> 
> 5. Verification:
>    - Re-running /fixpr 789...
>    - ✅ All CI checks now passing
>    - ✅ No conflicts remaining
> 
> ✅ Complete! Full hybrid orchestration successful
```

## GitHub API Command Reference

### Posting Inline Comments (with proper threading)

```bash
# First, get original comment details for commit_id:
original=$(gh api "/repos/{owner}/{repo}/pulls/comments/{comment_id}")
commit_id=$(echo "$original" | jq -r .commit_id)
path=$(echo "$original" | jq -r .path)
line=$(echo "$original" | jq -r .line)

# Then post inline reply:
gh api "/repos/{owner}/{repo}/pulls/{pr}/comments" \
  -f body="**[AI Responder]**\n\n{reply_text}" \
  -F in_reply_to="{comment_id}" \
  -f commit_id="${commit_id}" \
  -f path="${path}" \
  -F line="${line}"
```

### Posting General Comments

```bash
gh pr comment {pr} --body "**[AI Responder]**\n\n{reply_text}"
```

### PR Reviews

```bash
# Approve
gh pr review {pr} --approve --body "LGTM! All tests passing."

# Request changes
gh pr review {pr} --request-changes --body "Please address..."

# Comment only
gh pr review {pr} --comment --body "Some observations..."
```

## Adaptive Intelligence Features

- **Skip unnecessary steps**: No comments? Skip comment fetching
- **Prioritize by urgency**: Security issues first, style issues last  
- **Context awareness**: First-time contributors get more detailed help
- **Error recovery**: Continue with remaining tasks if one fails
- **State management**: All data in `/tmp/copilot_${SANITIZED_BRANCH}/` for debugging

## Key Principles

1. **Transparency First**: Show everything before doing it
2. **Genuine Intelligence**: Claude analyzes, not Python patterns
3. **Clean Architecture**: One Python script for data, Claude for everything else
4. **User Control**: Clear visibility of all actions
5. **Adaptive Workflow**: Adjust to PR needs, not rigid phases

Remember: The power comes from Claude's genuine understanding and transparent execution, not from rigid orchestration phases.