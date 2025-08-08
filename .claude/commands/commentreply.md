# /commentreply Command

🚨 **CRITICAL**: Systematically addresses **ALL** GitHub PR comments with **REAL GITHUB THREADING** - no fake formatting!

## 🚨 MANDATORY: REAL THREADED REPLIES ONLY

**ZERO TOLERANCE FOR FAKE THREADING**: This command creates REAL threaded replies using GitHub's native threading API, NOT standalone comments with visual formatting.

✅ **REAL THREADING**: `#discussion_r{id}` URLs, nested under parent comments, `in_reply_to_id` populated
❌ **FAKE THREADING**: Standalone comments with 🧵 formatting, `#issuecomment-{id}` URLs, separate timeline entries

**CORRECT API**: `gh api repos/owner/repo/pulls/PR/comments --method POST --field in_reply_to=PARENT_ID`
**WRONG API**: `gh pr comment PR --body "🧵 Reply to Comment #ID"` (creates fake threading)

## 🎯 INDIVIDUAL COMMENT REQUIREMENT

**MANDATORY**: This command MUST reply to every single individual comment with REAL threading, including:
- **Copilot bot comments** - Automated suggestions and feedback
- **CodeRabbit comments** - AI code review feedback
- **Human reviewer comments** - Inline code suggestions
- **Suppressed comments** - Including hidden/collapsed feedback

**Evidence**: PR #864 had 11 individual comments (3 Copilot + 8 CodeRabbit) with ZERO replies - this MUST be prevented.

🚨 **CRITICAL WARNING**: Code implementation alone is NOT sufficient. You MUST post direct replies to each individual comment using GitHub API or `gh pr comment` with specific comment references.

## Usage
```
/commentreply
/commentr (alias)
```

## What it does

1. **Checks Comment Availability**: Verifies comments are present in conversation from `/commentfetch`
2. **Validates Prerequisites**: Warns if `/commentfetch` needs to be called first
3. **Processes Each Comment**: Analyzes feedback and determines response
4. **Addresses Systematically**: For each comment:
   - Analyze the feedback
   - Implement fix if needed
   - Mark as ✅ DONE or ❌ NOT DONE with explanation
   - Post inline reply via GitHub API
5. **Provides Summary**: Lists all comments addressed in chat

## Individual Comment Types (ALL REQUIRED)

🚨 **MANDATORY**: Every single individual comment MUST be replied to:

### Primary Sources (MOST CRITICAL)
- **Inline Pull Request Comments**: Line-specific code feedback (ID: 2223812756, 2223812765, etc.)
- **Review Thread Comments**: Comments within PR review discussions
- **Bot-Generated Comments**: Copilot, CodeRabbit, GitHub Actions feedback
- **Suppressed/Collapsed Comments**: Hidden or minimized feedback

### Secondary Sources
- **General Issue Comments**: Overall PR discussion
- **Review Summary Comments**: High-level review feedback

### Examples from PR #864 (FAILURE CASE)
```
❌ FAILED: These 11 individual comments received ZERO replies:

Copilot Comments (3):
- #2223812756: "Function reference table shows inconsistent parameter documentation"
- #2223812765: "Table lists all existing test files as using 'Local Playwright'"
- #2223812783: "Test URL format shows port 8081, but other docs use port 6006"

CodeRabbit Comments (8):
- #2223818404: "Primary method section violates tooling standard"
- #2223818407: "Repeats Playwright-first message contrary to CLAUDE.md"
- #2223818409: "Example section should showcase Puppeteer MCP"
- #2223818412: "Contradicts project-wide mandate: Puppeteer MCP must be primary"
- #2223818415: "Function reference table tied to Playwright MCP will become obsolete"
- #2223818416: "Statement enforces Playwright MCP for new tests – conflicts with mandate"
- #2223887761: "Fallback hierarchy wording is inverted"
```

**LESSON**: This MUST NOT happen again - every individual comment requires a direct reply.

🚨 **EXECUTION REQUIREMENT**: For EACH individual comment, you must BOTH:
1. ✅ **Implement technical fix** (if applicable) - address the actual issue
2. ✅ **Post REAL threaded reply** - use `gh api repos/owner/repo/pulls/PR/comments --method POST --field in_reply_to=PARENT_ID`

**🚨 CRITICAL ANTI-PATTERNS** (❌ FORBIDDEN):
- Using `gh pr comment [PR] --body "🧵 Reply to Comment #[ID]..."` (creates fake threading)
- Creating standalone comments with visual formatting instead of real threading
- Claiming "100% coverage" after only implementing fixes without posting threaded replies
- Any response that results in `#issuecomment-{id}` URLs instead of `#discussion_r{id}` URLs

🎆 **THREADING API BREAKTHROUGH VALIDATED**:
**GitHub API threading has been tested and confirmed working on PR #1166!**

✅ **VERIFIED WORKING API**: `gh api repos/owner/repo/pulls/PR/comments --method POST --field in_reply_to=PARENT_ID`
❌ **BROKEN API**: `gh pr comment PR --body "🧵 Reply to..."` (creates fake threading)

**✅ TESTED RESULTS** (Validated on PR #1166):
- ✅ **Real Threading**: `#discussion_r{id}` URLs, nested under parent, `in_reply_to_id` properly populated
- ✅ **Test Evidence**: Comment #2250135960 successfully threaded to #2250119301
- ✅ **Verification**: `in_reply_to_id: 2250119301` confirmed in API response
- ❌ **Fake Threading**: `#issuecomment-{id}` URLs, separate timeline entries, no threading relationship

**🚨 CRITICAL LIMITATION DISCOVERED**:
- ✅ **PR Review Comments**: Full threading support with `in_reply_to_id`
- ❌ **Issue Comments**: NO threading support (ignores `in_reply_to` parameter)
- **Impact**: Only inline file comments can be threaded, general PR comments cannot

**🧪 VALIDATION TESTING SUMMARY**:
- **Date Tested**: 2025-08-03 on PR #1166
- **PR Comment Threading**: ✅ WORKS - Created comment #2250141090 threaded to #2250119301
- **Issue Comment Threading**: ❌ FAILS - Comment #3148698724 ignored `in_reply_to` parameter
- **Threading Fields**: `in_reply_to_id` properly populated for PR comments, null for issue comments
- **URL Format Verification**: PR comments get `#discussion_r{id}`, issue comments get `#issuecomment-{id}`
- **API Commands Used**:
  - ✅ Working: `gh api repos/owner/repo/pulls/PR/comments --method POST --field in_reply_to=PARENT_ID`
  - ❌ Fails for issue comments: `gh api repos/owner/repo/issues/PR/comments --method POST --field in_reply_to=PARENT_ID`

**🚨 CRITICAL FIELD NAME CLARIFICATION** (Bug Fix: 2025-08-03):
- **API Parameter Name**: `--field in_reply_to=` (what you send to GitHub API)
- **API Response Field**: `"in_reply_to_id":` (what GitHub returns in JSON)
- **❌ COMMON MISTAKE**: Using `--field in_reply_to_id=` causes API rejection with "not a permitted key"
- **✅ CORRECT USAGE**: Always use `--field in_reply_to=` in API calls
- **🎯 Memory Aid**: API Parameter ≠ Response Field Name

## Process Flow

### 1. Prerequisite Validation Phase
- **Check for comments file**: Look for `/tmp/{branch_name}/comments.json` from `/commentfetch`
- **Validate file exists**: Ensure `/commentfetch` was executed and file is present
- **Warn if missing**: Alert user to run `/commentfetch` first if no file found
- **Load comment data**: Read and parse comment data from the JSON file

### 2. Execute Implementation Phase
🚨 **MANDATORY**: Use `/e` (execute) command for systematic comment processing with potential subagent delegation:

**Implementation Strategy**:
```
/e Process all PR comments from /tmp/{branch_name}/comments.json systematically:

1. Load and validate comment data from file
2. Analyze comment complexity and determine delegation strategy:
   - Simple acknowledgments: Process directly
   - Complex technical issues requiring file changes: Consider subagent delegation
   - Code fixes with multiple file impacts: Use subagents for parallel processing
3. For each comment:
   - Read comment content and context
   - Determine required action (fix, acknowledge, clarify)
   - Implement actual file changes when needed using Edit/MultiEdit tools
   - Post threaded GitHub API reply with enhanced context
   - Mark as completed in tracking system
4. Generate comprehensive summary of all addressed comments
5. Verify all replies posted successfully

Use subagents when:
- Comment requires changes to multiple files
- Complex architectural changes needed
- Parallel processing would improve efficiency
- Independent comment themes can be processed simultaneously

Process directly when:
- Simple acknowledgments or clarifications
- Single file edits
- Sequential dependencies between comments
```

### 3. Comment Processing Protocol
🚨 **MANDATORY**: Process EVERY individual comment systematically:

**Key Requirements**:
- **Process each comment individually** - no batching or grouping
- **Include bot comments** - Copilot, CodeRabbit, etc. are NOT exceptions
- **Verify comment count** - Ensure expected number of comments are found
- **Use GitHub API** - Direct API calls for reliable data retrieval

### 3. Response Processing Protocol

See "Enhanced Autonomous Workflow" section below (§4.1) for complete file editing and validation protocols.

### 3.1. FILE EDITING REQUIREMENTS (LLM-Native Implementation)

🚨 **CRITICAL**: When comments identify code issues requiring fixes:

#### Issue Identification
- Extract file path and line number from comment
- Identify the specific problem being reported
- Determine the appropriate fix strategy

#### Implementation Execution
- Use Claude Code CLI Edit/MultiEdit tools
- Make surgical, targeted changes
- Preserve code style and conventions
- Avoid unnecessary modifications

#### Verification Protocol
- Run `git diff` to confirm changes
- Test relevant functionality if possible
- Commit with descriptive message including comment reference
- Format: `git commit -m "Fix [issue] from comment #[ID]: [description]"`

### 4. Individual Comment Reply System (CRITICAL)
🚨 **MANDATORY**: Reply to EACH individual comment using LLM-native Claude Code CLI approach:

**Enhanced Context Reply Features**:
- **Rich Context**: File path, line number, and comment excerpt
- **Real Threading**: Use GitHub's native threading API where supported
- **Fallback System**: General comments when threading unavailable
- **Verification**: Confirm successful posting and threading

**🚨 CRITICAL THREADING REQUIREMENTS**:
- **REAL threading ONLY** - Use GitHub's native threading API, no fake 🧵 formatting
- **Correct API endpoint** - `gh api repos/owner/repo/pulls/PR/comments --method POST --field in_reply_to=PARENT_ID`
- **Threading verification** - All replies MUST have `in_reply_to_id` populated and `#discussion_r{id}` URLs
- **File editing mandatory** - MUST make actual file changes when addressing code issues
- **No fake formatting** - NEVER create standalone comments with visual threading simulation
- **Review comments only** - Only review comments can be threaded; issue comments use general fallback
- **Status markers required** - ✅ DONE or ❌ NOT DONE in every reply with commit hash
- **Zero tolerance** - Any fake threading (🧵 formatting in general comments) is a critical failure

### 4.1. Enhanced Autonomous Workflow & Validation

🚨 **MANDATORY FILE EDITING PROTOCOL**:
When addressing code issues:
1. ✅ **ALWAYS identify the exact file and line number**
2. ✅ **ALWAYS use Edit/MultiEdit tools to make actual changes**
3. ✅ **NEVER claim fixes without actual file modifications**
4. ✅ **ALWAYS verify changes with git diff**
5. ✅ **ALWAYS commit changes with descriptive message**

**ENHANCED AUTONOMOUS WORKFLOW**:
1. **Load comment data**: Read comment.body from GitHub API directly
2. **Genuine analysis**: Address SPECIFIC technical points raised in each comment
3. **Implement fixes**: Use Edit/MultiEdit tools to make actual file changes when needed
4. **Verify changes**: Run git diff to confirm file modifications occurred
5. **Commit changes**: Create descriptive commit with comment reference
6. **Self-validate**: Apply validation protocol below
7. **Status determination**: Mark as DONE (with commit hash) or NOT DONE with technical substance
8. **Post reply**: Use GitHub API to respond with threaded format including commit verification

🚨 **MANDATORY SELF-VALIDATION PROTOCOL**:
Before posting ANY response, verify:
1. ✅ **Content Reading**: "Did I read the actual comment.body text from the data?"
2. ✅ **Specific Analysis**: "Does my response address specific technical points raised?"
3. ✅ **File Editing**: "Did I make actual file changes if the comment requires fixes?"
4. ✅ **Verification**: "Did I run git diff to confirm changes were made?"
5. ✅ **Technical Substance**: "Does my response show technical understanding, not generic acknowledgment?"

**Verification Protocol**:
1. **File Changes**: Verify actual modifications occurred using `git diff`
2. **Fix Relevance**: Ensure changes address specific comment content
3. **Commit Verification**: Include commit hash in response for tracking
4. **Test Functionality**: Validate changes work as expected when possible

## Response Format

🚨 **MANDATORY THREADING FORMAT**
All comment replies MUST use GitHub's enhanced threaded reply format:

### Enhanced Threading Template
```markdown
🧵 **Reply to Inline Comment #[COMMENT_ID]**
📁 **File**: `[file_path:line_number]`
📍 **Line**: [line_number]
💬 **Original**: "[comment excerpt]..."

> [Original comment quote]

**Fixed in [commit_hash]**: [file_path:line_number]

**Changes Made**:
- [Specific change 1]
- [Specific change 2]

**Verification**: `git show [commit_hash] -- [file_path]`

✅ DONE: [explanation of fix/change made] (Commit: [short-hash])

*(Enhanced Context Reply System)*
```

### Standard Response Format
Each reply follows this format with **MANDATORY commit hash reference**:
- **✅ DONE**: `✅ DONE: [explanation of fix/change made] (Commit: [short-hash])`
- **❌ NOT DONE**: `❌ NOT DONE: [reason why not addressed] (Current: [short-hash])`

**Threading Requirements**:
- Quote original comment for context using `> prefix`
- Reference specific files and line numbers
- Include commit hashes for verification
- Provide clear change summaries
- Link to specific file changes

**Commit Hash Requirements**:
- **ALWAYS include current commit hash** in every comment reply
- Use `git rev-parse --short HEAD` to get 7-character short hash
- Format: `(Commit: abc1234)` for completed changes
- Format: `(Current: abc1234)` for unchanged/declined items

## Individual Comment Summary (MANDATORY)

🚨 **CRITICAL**: At the end, provides a comprehensive summary showing EVERY individual comment was addressed:

```
## Individual Comment Response Summary

### 🎯 INDIVIDUAL COMMENT COVERAGE
**Total Individual Comments Found**: 11
- Copilot bot comments: 3
- CodeRabbit comments: 8
- Human reviewer comments: 0

### ✅ Individual Comments Addressed (11 comments)
1. Comment #2223812756 (Copilot): Function parameter docs → ✅ DONE: Updated table format (Commit: abc1234) [ENHANCED: #2223999001]
2. Comment #2223812765 (Copilot): Migration status column → ✅ DONE: Added status tracking (Commit: def5678) [ENHANCED: #2223999002]
3. Comment #2223812783 (Copilot): Port inconsistency → ✅ DONE: Fixed to port 6006 (Commit: ghi9012) [ENHANCED: #2223999003]
4. Comment #2223818404 (CodeRabbit): Playwright vs Puppeter → ❌ NOT DONE: Playwright is correct per CLAUDE.md (Current: jkl3456) [FALLBACK: #2223999004]
5. Comment #2223818407 (CodeRabbit): Primary method conflict → ❌ NOT DONE: Intentional Playwright focus (Current: jkl3456) [ENHANCED: #2223999005]
6. [... continues for all 11 individual comments ...]

### ❌ Individual Comments NOT Addressed (0 comments)
[MUST BE ZERO - Every individual comment requires a response]

### 📊 Coverage Statistics
- **Individual comment coverage: 100% (11/11)**
- **Enhanced context success rate: 90% (10/11 enhanced, 1/11 fallback)**
- **API replies posted: 11 responses (10 enhanced context + 1 basic)**
- **Bot comment coverage: 100% (11/11)**
- **Verification success: 100% (all replies confirmed via API)**
```

**SUCCESS CRITERIA**:
- ✅ 100% individual comment coverage (zero unaddressed)
- ✅ Every code issue comment has actual file modifications (zero fake implementations)
- ✅ Every Copilot/CodeRabbit comment has an enhanced context reply
- ✅ All enhanced context replies successfully posted to GitHub with proper format (🧵 **Reply to Inline Comment #[ID]**)
- ✅ All file changes verified with git diff and commit hash references
- ✅ No responses without verified implementation when fixes are required

### QUALITY GATES (ZERO TOLERANCE)

🚨 **MANDATORY QUALITY CHECKS** - Must pass ALL gates before posting responses:

#### Gate 1: File Editing Compliance
- ❌ **REJECT**: Any response claiming fixes without actual file changes
- ✅ **REQUIRE**: Git diff verification showing actual modifications
- ✅ **REQUIRE**: Commit hash reference in response

#### Gate 2: Threading Format Compliance
- ❌ **REJECT**: Generic responses without enhanced context format
- ✅ **REQUIRE**: Proper 🧵 **Reply to Inline Comment #[ID]** format
- ✅ **REQUIRE**: Original comment quote and file/line context

#### Gate 3: Technical Accuracy
- ❌ **REJECT**: Template-based responses without reading comment content
- ✅ **REQUIRE**: Specific technical analysis addressing actual comment points
- ✅ **REQUIRE**: Evidence of understanding the reported issue

#### Gate 4: Verification Completeness
- ❌ **REJECT**: Missing commit hash or verification steps
- ✅ **REQUIRE**: Complete verification report with git commands
- ✅ **REQUIRE**: Clear DONE/NOT DONE status with technical justification

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
- **Enhanced context**: Rich file/line/snippet context for superior user experience
- **Clear audit trail**: Visible status for each comment
- **GitHub visibility**: Enhanced context replies appear as general comments with rich context
- **Time savings**: Automated posting of formatted enhanced context replies
- **Accountability**: Clear DONE/NOT DONE tracking with context

## Integration with PR Workflow

Works seamlessly with existing PR processes:
1. Create PR and receive comments
2. Run `/commentreply` to address all feedback
3. Continue with normal PR review cycle
4. All stakeholders see inline responses immediately

## Command Aliases

- `/commentreply` - Full command name
- `/commentr` - Short alias for convenience
