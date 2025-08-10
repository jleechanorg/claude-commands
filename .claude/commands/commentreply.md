# /commentreply Command

🔒 **Security**: Functions use explicit parameter passing to prevent variable scoping issues and safe jq --arg parameter passing to prevent command injection vulnerabilities.

🚨 **CRITICAL**: Systematically addresses **ALL** GitHub PR comments with **REAL GITHUB THREADING** - no fake formatting!

## 🚨 MANDATORY COMMAND SEQUENCE

**CRITICAL**: This command MUST execute specific command dependencies in exact order:

### Step 1: FRESH Comment Collection (MANDATORY)
```bash
/commentfetch [PR_NUMBER]
```
**🚨 ZERO TOLERANCE**: MUST run fresh `/commentfetch` every single time before processing
**❌ FORBIDDEN**: Using cached data, `gh pr view --json`, or any shortcuts
**✅ REQUIRED**: Complete API fetch of ALL comment types (inline, general, review, copilot)

### Step 2: Systematic Comment Processing  
```bash
# For EACH comment found by commentfetch:
gh api repos/owner/repo/pulls/PR/comments --method POST --field body="..." --field in_reply_to=COMMENT_ID
```

### Step 3: Final Summary Comment
```bash
gh api repos/owner/repo/issues/PR/comments --method POST --field body="✅ **Comment Reply Analysis Complete**..."
```

## 🚨 COMMAND DEPENDENCY CHAIN

**ABSOLUTE REQUIREMENT**: 
1. **`/commentfetch`** → Gets ALL comments with complete metadata
2. **Process each comment** → Individual threaded replies using GitHub API
3. **Post summary** → Final status comment to main PR issue

**❌ FAILURE MODES**:
- Skipping `/commentfetch` = Missing comments
- Using `gh pr view --json comments` = Incomplete data (misses review comments)
- Relying on previous fetch results = Stale data, missed new comments

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
- **🚨 OWNER TEST COMMENTS** - Testing, debugging, or validation comments by PR author
- **🚨 SIMPLE COMMENTS** - Short comments like "reply to this", "see if commentreply catches this"
- **🚨 ALL AUTHORS** - External reviewers, bots, AND PR owner comments without exception

**Evidence**: PR #864 had 11 individual comments (3 Copilot + 8 CodeRabbit) with ZERO replies - this MUST be prevented.

🚨 **CRITICAL WARNING**: Code implementation alone is NOT sufficient. You MUST post direct replies to each individual comment using GitHub API or `gh pr comment` with specific comment references.

## Usage
```
/commentreply
/commentr (alias)
```

## What it does

1. **Detects Current PR**: Gets PR number from current branch
2. **🚨 EXECUTES `/commentfetch` FRESH**: **MANDATORY** - runs complete comment collection every time
   - **NO shortcuts**: Never skips this step, never uses cached data
   - **Complete coverage**: Fetches inline, general, review, and copilot comments
   - **Fresh data**: Gets latest comments including any added during workflow
3. **Presents Each Comment**: Shows context from commentfetch results for systematic processing
4. **Addresses Systematically**: For each comment found by `/commentfetch`:
   - Analyze the feedback
   - Implement fix if needed
   - Mark as ✅ DONE or ❌ NOT DONE with explanation
   - Post REAL threaded reply via GitHub API with `in_reply_to` parameter
5. **Posts Final Summary**: Comprehensive summary comment to main PR issue
6. **Verifies Coverage**: Ensures ALL comments from `/commentfetch` were processed

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
- **🚨 SKIPPING `/commentfetch`**: Using `gh pr view --json comments` or cached data instead of fresh fetch
- **🚨 INCOMPLETE DATA**: Missing review comments because only general comments were fetched  
- **🚨 STALE DATA**: Processing old comment lists while new comments were added
- Using `gh pr comment [PR] --body "🧵 Reply to Comment #[ID]..."` (creates fake threading)
- Creating standalone comments with visual formatting instead of real threading
- Claiming "100% coverage" after only implementing fixes without posting threaded replies
- Any response that results in `#issuecomment-{id}` URLs instead of `#discussion_r{id}` URLs
- **🚨 COMMENT FILTERING BUG**: Ignoring owner test comments, simple comments, or debugging comments
- **🚨 AUTHOR BIAS**: Assuming PR owner comments don't need responses
- **🚨 CONTENT BIAS**: Skipping "simple" comments like "reply to this" or "test comment"
- **🚨 FALSE COVERAGE**: Declaring complete coverage while missing ANY comment type

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

```bash
# METHOD 1: ENHANCED CONTEXT REPLY (OPTIMAL USER EXPERIENCE)
# Creates general comments with rich context - GitHub API limitation workaround
create_enhanced_context_reply() {
  local original_comment_id="$1"
  local response_body="$2"
  local comment_data="$3"
  local pr_number="$4"
  local owner="$5"
  local repo="$6"

  # Extract context information
  local file_path=$(echo "$comment_data" | jq -r '.path // "N/A"')
  local line_number=$(echo "$comment_data" | jq -r '.line // .original_line // "N/A"')
  local snippet=$(echo "$comment_data" | jq -r '.body' | head -c 100)

  echo "🔄 Creating enhanced context reply to comment #$original_comment_id..."

  # Enhanced context reply with file, line, and snippet context
  local enhanced_body="🧵 **Reply to Inline Comment #$original_comment_id**"
  enhanced_body+="\n📁 **File**: \`$file_path\`"
  enhanced_body+="\n📍 **Line**: $line_number"
  enhanced_body+="\n💬 **Original**: \"$snippet...\""
  enhanced_body+="\n\n$response_body"
  enhanced_body+="\n\n*(Enhanced Context Reply System)*"

  # Post as general comment (works reliably vs threading limitations)
  gh pr comment "$pr_number" --body "$enhanced_body"

  if [ $? -eq 0 ]; then
    echo "✅ SUCCESS: Enhanced context reply created for comment #$original_comment_id"
    return 0
  else
    echo "❌ FAILED: Enhanced context reply failed for comment #$original_comment_id"
    return 1
  fi
}

# METHOD 2: Enhanced Context Verification (CRITICAL)
# Verify enhanced context reply was posted successfully
verify_enhanced_context_reply() {
  local original_id="$1"
  local owner="$2"
  local repo="$3"
  local pr_number="$4"
  local max_attempts=3

  for attempt in $(seq 1 $max_attempts); do
    sleep 2  # Allow API to process

    # Check if enhanced context reply was posted (look for our unique format)
    ENHANCED_REPLY=$(gh api "repos/$owner/$repo/issues/$pr_number/comments" --paginate | \
      jq --arg id "$original_id" -r '.[] | select(.body | contains("🧵 **Reply to Inline Comment #" + $id + "**")) | .id')

    if [ -n "$ENHANCED_REPLY" ]; then
      echo "✅ VERIFIED: Enhanced context reply $ENHANCED_REPLY created for comment $original_id"
      return 0
    fi

    echo "⏳ Attempt $attempt: Waiting for enhanced context reply verification..."
  done

  echo "❌ ENHANCED REPLY FAILED: No enhanced context reply found for comment $original_id"
  return 1
}

# METHOD 3: Fallback System (RELIABILITY) - Basic Context Reply
# If enhanced context fails, create basic comment with clear reference
create_fallback_comment() {
  local original_id="$1"
  local response_body="$2"
  local pr_number="$3"
  local owner="$4"
  local repo="$5"

  gh pr comment "$pr_number" --body "📍 **FALLBACK Reply to Comment #$original_id**:
$response_body
🔗 Enhanced context failed - this is a basic comment reference"

  echo "⚠️ FALLBACK: Basic comment created for #$original_id"
}

# METHOD 4: Comment Type Detection (VALIDATED)
# Determines if comment supports real threading based on validation testing
determine_comment_type() {
  local comment_data="$1"

  # Check if comment has path field (indicates PR review comment)
  local path=$(echo "$comment_data" | jq -r '.path // null')
  local line=$(echo "$comment_data" | jq -r '.line // null')

  if [ "$path" != "null" ] && [ "$line" != "null" ]; then
    echo "PR_REVIEW"  # Supports real threading
  else
    echo "ISSUE_COMMENT"  # No threading support
  fi
}

# METHOD 5: Complete Enhanced Context Workflow with File Editing (ROBUST)
# Implements enhanced context replies with mandatory file editing and verification
reply_to_individual_comment() {
  local comment_data="$1"
  local response_body="$2"
  local pr_number="$3"
  local owner="$4"
  local repo="$5"

  # Extract comment details
  local comment_id=$(echo "$comment_data" | jq -r '.id')
  local file_path=$(echo "$comment_data" | jq -r '.path // "N/A"')
  local line_number=$(echo "$comment_data" | jq -r '.line // .original_line // "N/A"')
  local comment_body=$(echo "$comment_data" | jq -r '.body')

  echo "🔄 Processing comment #$comment_id with enhanced context and file editing..."

  # Step 1: Determine if comment requires file editing
  local requires_file_edit=false
  if echo "$comment_body" | grep -iE "(fix|change|update|modify|replace|add|remove|correct)" > /dev/null; then
    if [ "$file_path" != "N/A" ] && [ "$file_path" != "null" ]; then
      requires_file_edit=true
      echo "📝 REQUIRES FILE EDIT: Comment #$comment_id identifies code issue in $file_path"
    fi
  fi

  # Step 2: Implement file changes if required
  local commit_hash=""
  if [ "$requires_file_edit" = true ]; then
    echo "🛠️ IMPLEMENTING FIX: Making file changes for comment #$comment_id..."

    # Get current commit before changes
    local before_commit=$(git rev-parse --short HEAD)

    # LLM-NATIVE DESIGN PATTERN: Hybrid Architecture
    # - Shell script: Provides workflow orchestration, git operations, API calls
    # - Claude Code CLI: Handles intelligent file editing via Edit/MultiEdit tools
    # - Benefits: Combines shell's system integration with LLM's code understanding
    # - Responsibility: Script orchestrates; Claude executes contextual code changes
    echo "⚠️  CLAUDE MUST: Use Edit/MultiEdit tools to fix issue in $file_path:$line_number"
    echo "⚠️  CLAUDE MUST: Address specific issue: $(echo "$comment_body" | head -c 100)..."

    # Verify changes were made
    if ! git diff --quiet; then
      echo "✅ CHANGES DETECTED: Files modified, committing changes..."

      # Stage only the specific file if it exists, otherwise require manual staging
      if [ "$file_path" != "N/A" ] && [ "$file_path" != "null" ] && [ -f "$file_path" ]; then
        echo "📁 STAGING: Specific file $file_path"
        git add "$file_path"
      else
        echo "⚠️  SECURITY: Cannot stage unknown files - manual staging required"
        echo "📋 Modified files: $(git diff --name-only)"
        echo "💡 Use: git add [specific-files] before running commit"
        return 1
      fi

      # Safely construct commit message with proper escaping
      local safe_comment_body
      safe_comment_body=$(echo "$comment_body" | head -c 50 | tr '\n' ' ' | sed 's/["`$\\]/\\&/g')
      git commit -m "Fix issue from comment #$comment_id: $safe_comment_body..."

      commit_hash=$(git rev-parse --short HEAD)
      echo "✅ COMMITTED: Changes in commit $commit_hash"

      # Run git diff to show what changed
      echo "🔍 VERIFICATION: git diff \"$before_commit\"..\"$commit_hash\""
      git diff "$before_commit".."$commit_hash"
    else
      echo "❌ NO CHANGES: No file modifications detected - MANDATORY for code issues!"
      echo "⚠️  This violates the mandatory file editing protocol"
      commit_hash=$(git rev-parse --short HEAD)
    fi
  else
    commit_hash=$(git rev-parse --short HEAD)
    echo "💬 COMMENT ONLY: No file changes required for comment #$comment_id"
  fi

  # Step 3: Update response with commit verification
  if [ -n "$commit_hash" ] && [ "$requires_file_edit" = true ]; then
    response_body="$response_body (Commit: $commit_hash)"
  else
    response_body="$response_body (Current: $commit_hash)"
  fi

  # Step 4: Determine comment type and create appropriate reply
  local comment_type=$(determine_comment_type "$comment_data")
  echo "🔍 COMMENT TYPE: $comment_type for comment #$comment_id"

  if [ "$comment_type" = "PR_REVIEW" ]; then
    # Use real threading for PR review comments (VALIDATED WORKING)
    echo "🔗 THREADING: Creating real threaded reply (supports in_reply_to_id)"
    if create_real_threaded_reply "$comment_id" "$response_body" "$pr_number" "$owner" "$repo"; then
      # Step 5: Verify real threading worked using exported reply ID from API response
      # FIX: Use the reply ID directly from the API response (exported by create_real_threaded_reply)
      # instead of the dangerous tail -1 pattern that could grab wrong comment in parallel operations
      local reply_id="$CREATED_REPLY_ID"

      if verify_real_threaded_reply "$comment_id" "$reply_id" "$pr_number" "$owner" "$repo"; then
        echo "✅ SUCCESS: REAL threaded reply created for #$comment_id"
        return 0
      fi
    fi
    echo "⚠️ THREADING FAILED: Falling back to general comment"
  else
    # Issue comments don't support threading - use general comment
    echo "💬 GENERAL COMMENT: Issue comment detected (no threading support)"
  fi

  # Step 6: Fallback to general comment (NOT threaded)
  echo "📝 FALLBACK: Creating general comment (no threading capability)"
  create_fallback_general_comment "$comment_id" "$response_body" "$pr_number"
  return 1
}

# METHOD 6: Real threaded reply implementation (CRITICAL)
# Creates actual GitHub threaded replies using correct API
create_real_threaded_reply() {
  local comment_id="$1"
  local response_body="$2"
  local pr_number="$3"
  local owner="$4"
  local repo="$5"

  echo "🔗 CREATING: Real threaded reply to comment #$comment_id..."

  # Validate and sanitize parameters for safe API usage
  if [[ ! "$owner" =~ ^[a-zA-Z0-9._-]+$ ]] || [[ ! "$repo" =~ ^[a-zA-Z0-9._-]+$ ]] || [[ ! "$pr_number" =~ ^[0-9]+$ ]]; then
    echo "❌ SECURITY ERROR: Invalid characters in API parameters (owner: $owner, repo: $repo, pr: $pr_number)"
    return 1
  fi

  # Use the correct GitHub API for creating threaded PR review comments
  # FIX: Use JSON input with proper escaping to prevent injection
  local response=$(jq -n \
    --arg body "$response_body" \
    --arg reply_to "$comment_id" \
    '{body: $body, in_reply_to: ($reply_to | tonumber)}' | \
    gh api "repos/$owner/$repo/pulls/$pr_number/comments" \
      --method POST --header "Content-Type: application/json" --input -)

  if [ $? -eq 0 ]; then
    # Extract the new comment ID and URL from response
    local new_comment_id=$(echo "$response" | jq -r '.id')
    local html_url=$(echo "$response" | jq -r '.html_url')

    echo "✅ SUCCESS: Real threaded reply created for comment #$comment_id"
    echo "🔗 REPLY URL: $html_url"
    echo "📋 REPLY ID: $new_comment_id"

    # Store for validation (global variable for /commentcheck)
    export CREATED_REPLY_URL="$html_url"
    export CREATED_REPLY_ID="$new_comment_id"
    export PARENT_COMMENT_ID="$comment_id"

    return 0
  else
    echo "❌ FAILED: Real threaded reply creation failed for comment #$comment_id"
    return 1
  fi
}

# METHOD 7: Real threaded reply verification (CRITICAL)
# Verifies that the reply was actually created with proper threading
verify_real_threaded_reply() {
  local original_comment_id="$1"
  local reply_id="$2"
  local pr_number="$3"
  local owner="$4"
  local repo="$5"

  echo "🔍 VERIFYING: Real threaded reply $reply_id for comment #$original_comment_id..."

  # Validate reply_id is not empty/null to prevent jq syntax errors
  if [ -z "$reply_id" ] || [ "$reply_id" = "null" ]; then
    echo "❌ VERIFICATION FAILED: Empty or null reply_id provided"
    return 1
  fi

  # Validate parameters before API call
  if [[ ! "$owner" =~ ^[a-zA-Z0-9._-]+$ ]] || [[ ! "$repo" =~ ^[a-zA-Z0-9._-]+$ ]] || [[ ! "$pr_number" =~ ^[0-9]+$ ]]; then
    echo "❌ SECURITY ERROR: Invalid characters in verification API parameters"
    return 1
  fi

  # Verify the reply exists and has correct in_reply_to_id (safe jq with --arg parameter)
  local reply_data=$(gh api "repos/$owner/$repo/pulls/$pr_number/comments" --paginate | \
    jq --arg id "$reply_id" '.[] | select(.id == ($id | tonumber))')

  if [ -z "$reply_data" ]; then
    echo "❌ VERIFICATION FAILED: Reply $reply_id not found"
    return 1
  fi

  local in_reply_to=$(echo "$reply_data" | jq -r '.in_reply_to_id')
  local html_url=$(echo "$reply_data" | jq -r '.html_url')

  if [ "$in_reply_to" = "$original_comment_id" ]; then
    echo "✅ VERIFICATION PASSED: Reply $reply_id properly threaded to #$original_comment_id"
    echo "🔗 URL format: $html_url (should be #discussion_r$reply_id)"
    return 0
  else
    echo "❌ VERIFICATION FAILED: Reply $reply_id not properly threaded (in_reply_to: $in_reply_to, expected: $original_comment_id)"
    return 1
  fi
}

# METHOD 8: Fallback general comment (RELIABILITY)
# Creates general comment when threading fails
create_fallback_general_comment() {
  local comment_id="$1"
  local response_body="$2"
  local pr_number="$3"

  echo "⚠️ FALLBACK: Creating general comment for #$comment_id..."

  # Ensure repo identifiers for API call
  : "${OWNER:=$(gh repo view --json owner -q .owner.login)}"
  : "${REPO:=$(gh repo view --json name -q .name)}"
  
  local fallback_body="**Response to Comment #$comment_id** (Note: Real threading unavailable):

$response_body

*(This is a general comment since threaded replies are not supported for this comment type)*"
  
  local response=$(jq -n --arg body "$fallback_body" '{body: $body}' | \
    gh api "repos/$OWNER/$REPO/issues/$pr_number/comments" \
      --method POST --header "Content-Type: application/json" --input -)

  if [ $? -eq 0 ]; then
    # Extract URL from response
    local html_url=$(echo "$response" | jq -r '.html_url')
    local comment_id_new=$(echo "$response" | jq -r '.id')

    echo "✅ FALLBACK SUCCESS: General comment created for #$comment_id"
    echo "🔗 FALLBACK URL: $html_url"
    echo "📋 FALLBACK ID: $comment_id_new"

    # Store for validation
    export CREATED_REPLY_URL="$html_url"
    export CREATED_REPLY_ID="$comment_id_new"
    export PARENT_COMMENT_ID="$comment_id"

    return 0
  else
    echo "❌ FALLBACK FAILED: General comment creation failed for #$comment_id"
    return 1
  fi
}
```

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

## 🚨 MANDATORY: FINAL SUMMARY COMMENT POSTING

**CRITICAL**: After processing all individual threaded replies, MUST post a final summary comment to the main PR issue:

### Final Summary Comment Implementation
```bash
# METHOD 9: Final Summary Comment (MANDATORY)
# Posts comprehensive summary to main PR issue after all threaded replies complete
post_final_summary_comment() {
  local pr_number="$1"
  local total_comments="$2"
  local done_count="$3"
  local not_done_count="$4"
  local commit_hash="$5"
  
  echo "📝 POSTING: Final summary comment to PR #$pr_number..."
  
  # Build summary content
  local summary_body="✅ **Comment Reply Analysis Complete**

**Summary**:
- 📊 **Total Comments Processed**: $total_comments
- ✅ **Resolved**: $done_count comments  
- ⚠️ **Acknowledged**: $not_done_count comments
- 🔄 **Threading**: All replies posted with proper threading where supported
- 📝 **Commit**: $commit_hash

**Individual Responses**: See individual threaded replies above for detailed technical responses to each comment.

**Process**: Each comment received a dedicated threaded reply using GitHub's native threading API when supported, with fallback to enhanced context comments for compatibility.

*Generated by /commentreply - Complete individual comment processing with dual response system (threaded + summary)*"

  # Ensure repo identifiers
  : "${OWNER:=$(gh repo view --json owner -q .owner.login)}"
  : "${REPO:=$(gh repo view --json name -q .name)}"
  # Post summary comment to main PR issue (returns JSON)
  local response=$(jq -n --arg body "$summary_body" '{body: $body}' | \
    gh api "repos/$OWNER/$REPO/issues/$pr_number/comments" \
      --method POST --header "Content-Type: application/json" --input -)
  
  if [ $? -eq 0 ]; then
    local summary_url
    summary_url=$(echo "$response" | jq -r '.html_url')
    local summary_id
    summary_id=$(echo "$response" | jq -r '.id')
    
    echo "✅ SUCCESS: Final summary comment posted to PR #$pr_number"
    echo "🔗 SUMMARY URL: $summary_url"
    echo "📋 SUMMARY ID: $summary_id"
    
    # Store for validation
    export FINAL_SUMMARY_URL="$summary_url"
    export FINAL_SUMMARY_ID="$summary_id"
    
    return 0
  else
    echo "❌ FAILED: Final summary comment posting failed for PR #$pr_number"
    return 1
  fi
}

# METHOD 10: Complete Workflow Integration (CRITICAL)
# Integrates final summary posting into main workflow
complete_comment_reply_workflow() {
  local pr_number="$1"
  
  echo "🚀 STARTING: Complete comment reply workflow with dual response system..."
  
  # Step 1: Process all individual comments (existing functionality)
  local total_comments=0
  local done_count=0
  local not_done_count=0
  local all_replies_successful=true
  
  # [Existing individual comment processing loop goes here]
  # This maintains all current threading functionality
  
  # Step 2: Calculate final statistics
  # [Statistics calculation from individual processing]
  
  # Step 3: MANDATORY - Post final summary comment
  local current_commit=$(git rev-parse --short HEAD)
  
  echo "📝 MANDATORY STEP: Posting final summary comment..."
  if ! post_final_summary_comment "$pr_number" "$total_comments" "$done_count" "$not_done_count" "$current_commit"; then
    echo "❌ CRITICAL FAILURE: Final summary comment posting failed"
    echo "⚠️  Individual threaded replies were posted successfully, but summary failed"
    return 1
  fi
  
  # Step 4: Final verification
  echo "🔍 VERIFICATION: Dual response system complete"
  echo "- ✅ Individual threaded replies: Posted"
  echo "- ✅ Final summary comment: Posted"
  echo "- 🔗 Summary comment URL: $FINAL_SUMMARY_URL"
  
  return 0
}
```

### Integration Requirements

**MANDATORY INTEGRATION**: Add final summary posting to the main workflow:

1. **Keep existing threaded reply functionality** (working perfectly like "test3" example)
2. **Add final summary step** after all individual replies complete
3. **Track statistics** during individual processing (done/not done counts)
4. **Post summary to main PR issue** using `gh pr comment`
5. **Verify both systems** work together

### Final Comment Format
```markdown
✅ **Comment Reply Analysis Complete**

**Summary**:
- 📊 **Total Comments Processed**: 8
- ✅ **Resolved**: 6 comments  
- ⚠️ **Acknowledged**: 2 comments
- 🔄 **Threading**: All replies posted with proper threading where supported
- 📝 **Commit**: abc1234

**Individual Responses**: See individual threaded replies above for detailed technical responses to each comment.

**Process**: Each comment received a dedicated threaded reply using GitHub's native threading API when supported, with fallback to enhanced context comments for compatibility.

*Generated by /commentreply - Complete individual comment processing with dual response system (threaded + summary)*
```

This gives you **BOTH**:
- ✅ **Individual threaded replies** (like your "test3" example) 
- ✅ **Final summary comment** on the main PR issue

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
