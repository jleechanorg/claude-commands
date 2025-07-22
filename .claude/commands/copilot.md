# /copilot Command - Intelligent PR Analysis with Universal Composition

**Usage**: `/copilot <PR_NUMBER>`

**Purpose**: Comprehensively analyze and address PR issues using adaptive intelligence.

## 🔧 **Commands Used by /copilot (Orchestration)**

**CRITICAL**: /copilot orchestrates existing commands - does NOT duplicate their functionality:

1. **`/commentfetch [PR]`** - Data collection
   - Python: `.claude/commands/copilot_modules/commentfetch.py`
   - Output: `/tmp/copilot/comments.json`

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

### ❌ FORBIDDEN:
- NEVER create Python functions that generate "intelligent" responses with templates
- NEVER use pattern matching like `if 'pagination' in comment: return "I'll fix pagination!"`
- NEVER build `_create_contextual_response()` methods that fake understanding
- NEVER generate generic acknowledgments that don't address specific technical content

### ✅ REQUIRED:
- ALWAYS use actual Claude for response generation
- ALWAYS pass full comment context to Claude for genuine analysis
- ALWAYS let Claude read the actual technical content and respond specifically
- ALWAYS ensure responses address the exact points raised, not generic patterns

### The Architecture MUST Be:
1. **Python**: Collects data (comments, CI status, etc.)
2. **Claude**: Provides genuine intelligence and responses
3. **Claude**: Executes decisions directly (no Python middleman)

**Remember**: Python handles plumbing. Claude provides intelligence. Never fake it with templates.

## 🚨 CRITICAL: 100% Comment Coverage Rule

**EVERY comment must be explicitly marked as DONE or NOT DONE**:
- **DONE**: Response posted OR no response needed (with clear explanation)
- **NOT DONE**: Needs response (show the planned response)

**Never leave ambiguity** - systematically go through ALL comments and account for each one!

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
- **Why**: `.claude/commands/copilot_modules/commentfetch.py` already fetches all comment types
- **What it handles**: Inline, general, review, Copilot comments → comments.json  
- **Result**: Complete comment data for processing

## How It Works

**The `/copilot` command follows this EXACT execution sequence:**

### PHASE 1: Data Collection
1. **Run** `/commentfetch [PR]` to gather ALL comments → `/tmp/copilot/comments.json`
2. **Verify** data collection completed successfully

### PHASE 2: Fix Issues First
**Run** `/fixpr [PR]` to resolve CI failures and conflicts:
- **Fix CI issues** - Analyze and resolve test failures, linting errors
- **Resolve conflicts** - Handle merge conflicts and compatibility issues  
- **Code improvements** - Apply necessary fixes based on analysis
- **Prepare for responses** - Ensure fixes are ready before commenting

### PHASE 3: Push Fixes
**Run** `/pushl` to push all fixes to remote:
- **Commit fixes** - Stage and commit all code improvements
- **Push to remote** - Make fixes available on GitHub
- **Verify deployment** - Confirm fixes are live before responding to comments

### PHASE 4: Comment Response Processing
**Run** `/commentreply` (AFTER fixes are live):
- **Process all comments** - Address feedback with fixes already in place
- **DONE/NOT DONE tracking** - Mark issues as resolved or pending
- **Professional responses** - Post appropriate GitHub API responses

### PHASE 5: Verification
**Run** `/commentcheck` to verify 100% coverage:
- **Coverage analysis** - Ensure all comments received responses
- **Quality assessment** - Verify responses are substantial and appropriate
- **Report status** - Generate detailed coverage report

### PHASE 6: Final Operations
**Run** `/pushl` if additional changes needed:
- **Final commit** - Any updates made during comment verification
- **Complete workflow** - Ensure all changes are pushed and verified

**Key Principles:**
- **Zero tolerance for missed comments** - every single one gets processed
- **Complete transparency** - show everything before doing it  
- **Systematic execution** - follow the protocol exactly, no shortcuts
- **Proper threading** - responses appear in the right place
- **Self-improving** - commit any improvements made during execution
- **Complete workflow** - from comment analysis to git operations

### Command Composition Integration:

#### Primary Command: `/commentfetch [PR]`
- **Data Collection**: Gathers ALL 108 comments from PR #820
- **Output**: `/tmp/copilot/comments.json` with complete comment data
- **Role**: The foundation - provides data for systematic processing

#### Integrated Processing (via copilot.md protocol):
- **Comment Analysis**: Claude reads comments.json directly
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
/commentfetch → comments.json (ONLY Python usage)
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
>    ✅ Found 5 comments → /tmp/copilot/comments.json
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
>    ✅ Found 3 comments → /tmp/copilot/comments.json
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
>    ✅ Found 12 comments → /tmp/copilot/comments.json
>    - 8 need responses (NOT DONE)
>    - 4 informational (DONE)
> 
> 2. Running /fixpr 789 --comments /tmp/copilot/comments.json...
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
- **State management**: All data in `/tmp/copilot/` for debugging

## Key Principles

1. **Transparency First**: Show everything before doing it
2. **Genuine Intelligence**: Claude analyzes, not Python patterns
3. **Clean Architecture**: One Python script for data, Claude for everything else
4. **User Control**: Clear visibility of all actions
5. **Adaptive Workflow**: Adjust to PR needs, not rigid phases

Remember: The power comes from Claude's genuine understanding and transparent execution, not from rigid orchestration phases.