# /commentreply Command

🚨 **CRITICAL**: Systematically addresses **ALL** GitHub PR comments, especially **INDIVIDUAL COMMENTS**, with inline replies and status tracking.

## 🎯 INDIVIDUAL COMMENT REQUIREMENT

**MANDATORY**: This command MUST reply to every single individual comment, including:
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

1. **Detects Current PR**: Gets PR number from current branch
2. **Fetches ALL Comments**: Retrieves inline, general, and review comments
3. **Presents Each Comment**: Shows context and asks for response
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
2. ✅ **Post direct reply** - use `gh pr comment [PR] --body "📍 Reply to Comment #[ID]..."`

**ANTI-PATTERN**: Claiming "100% coverage" after only implementing fixes without posting replies.

## Process Flow

### 1. Discovery Phase
```bash
# Get current PR
PR_NUMBER=$(gh pr view --json number -q .number)

# Get repository info
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
```

### 2. Individual Comment Fetching (CRITICAL)
🚨 **MANDATORY**: Fetch EVERY individual comment with these specific API calls:

```bash
# 1. Fetch ALL inline pull request comments (PRIMARY SOURCE)
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate

# 2. Fetch review comments from all reviews
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" --paginate | \
  jq -r '.[] | select(.body != null) | .id' | \
  xargs -I {} gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews/{}/comments"

# 3. Fetch general issue comments
gh api "repos/$OWNER/$REPO/issues/$PR_NUMBER/comments" --paginate

# 4. VERIFY: Aggregate ALL sources and count total individual comments
pull_comments=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate)
issue_comments=$(gh api "repos/$OWNER/$REPO/issues/$PR_NUMBER/comments" --paginate)
review_comments=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" --paginate | \
  jq -r '.[].id' | \
  xargs -I {} gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews/{}/comments" 2>/dev/null || echo '[]')

if [ $? -ne 0 ]; then
  echo "Error: Failed to fetch pull request comments from the GitHub API." >&2
  exit 1
fi

# Combine and count all comment sources - FIXED: Safe defaults for empty sources
if [ -z "$pull_comments" ] || [ "$pull_comments" = "null" ]; then
  pull_comments='[]'
fi
if [ -z "$issue_comments" ] || [ "$issue_comments" = "null" ]; then
  issue_comments='[]'
fi
if [ -z "$review_comments" ] || [ "$review_comments" = "null" ]; then
  review_comments='[]'
fi

all_comments=$(printf '%s\n%s\n%s\n' "$pull_comments" "$issue_comments" "$review_comments" | jq -s 'add | unique_by(.id)')
total_comments=$(echo "$all_comments" | jq length)
echo "Total individual comments to process: $total_comments"
```

**Key Requirements**:
- **Use `--paginate`** to ensure ALL comments are retrieved
- **Process each comment individually** - no batching or grouping
- **Include bot comments** - Copilot, CodeRabbit, etc. are NOT exceptions
- **Double-check count** - Verify expected number of comments are found

### 3. Response Processing (🚨 CRITICAL: AUTONOMOUS GENUINE INTELLIGENCE)
For each comment in autonomous operation:

🚨 **MANDATORY SELF-VALIDATION PROTOCOL**:
Before posting ANY response, verify:
1. ✅ **Content Reading**: "Did I read the actual comment.body text from the data?"
2. ✅ **Specific Analysis**: "Does my response address specific technical points raised?"
3. ✅ **Understanding Demo**: "Does my response demonstrate I understood the comment's context?"
4. ✅ **No Templates**: "Am I using genuine analysis, not pattern-based generation?"
5. ✅ **Technical Substance**: "Does my response show technical understanding, not generic acknowledgment?"

**AUTONOMOUS WORKFLOW**:
1. **Load comment data**: Read comment.body from GitHub API directly
2. **Genuine analysis**: Address SPECIFIC technical points raised in each comment
3. **Self-validate**: Apply 5-point validation protocol above
4. **Status determination**: Mark as DONE or NOT DONE with technical substance
5. **Post reply**: Use GitHub API to respond inline with authentic analysis

🚨 **FORBIDDEN TEMPLATE PATTERNS**:
- ❌ NEVER use `if 'coderabbit' in author: response = template`
- ❌ NEVER generate generic acknowledgments without reading comment content
- ❌ NEVER execute unauthorized Python code for response generation
- ✅ ALWAYS read each comment's ACTUAL CONTENT before responding
- ✅ ALWAYS provide genuine Claude analysis addressing specific technical content
- ✅ ALWAYS pass self-validation before posting responses

### 4. Individual Comment Reply APIs (CRITICAL)
🚨 **MANDATORY**: Reply to EACH individual comment using the EXACT GitHub API method for TRUE threading:

```bash
# METHOD 1: TRUE THREADED REPLY (ONLY WORKING METHOD)
# Creates actual threaded replies using GitHub's replies endpoint
create_true_threaded_reply() {
  local original_comment_id="$1"
  local response_body="$2"

  echo "🔄 Creating TRUE threaded reply to comment #$original_comment_id..."

  # THE CORRECT GITHUB API FOR THREADING - FIXED: JSON envelope format
  printf '{"body": "📍 **Threaded Reply**: %s"}' "$response_body" | \
    gh api -X POST "repos/$OWNER/$REPO/pulls/comments/$original_comment_id/replies" \
      --input -

  if [ $? -eq 0 ]; then
    echo "✅ SUCCESS: Threaded reply created for comment #$original_comment_id"
    return 0
  else
    echo "❌ FAILED: Threading failed for comment #$original_comment_id"
    return 1
  fi
}

# METHOD 2: Verification Layer (CRITICAL)
# Verify TRUE threading worked by checking in_reply_to_id field
verify_true_threading() {
  local original_id="$1"
  local max_attempts=3

  for attempt in $(seq 1 $max_attempts); do
    sleep 2  # Allow API to process

    # Check if any new comment has in_reply_to_id matching our original
    THREADED_REPLY=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
      jq -r '.[] | select(.in_reply_to_id == '$original_id') | .id')

    if [ -n "$THREADED_REPLY" ]; then
      echo "✅ VERIFIED: Threaded reply $THREADED_REPLY created for comment $original_id"
      return 0
    fi

    echo "⏳ Attempt $attempt: Waiting for threading verification..."
  done

  echo "❌ THREADING FAILED: No threaded reply found for comment $original_id"
  return 1
}

# METHOD 3: Fallback System (RELIABILITY)
# If threading fails, create general comment with clear reference
create_fallback_comment() {
  local original_id="$1"
  local response_body="$2"

  gh pr comment $PR_NUMBER --body "📍 **FALLBACK Reply to Comment #$original_id**:
$response_body
🔗 Threading failed - this is a general comment reference"

  echo "⚠️ FALLBACK: General comment created for #$original_id"
}

# METHOD 4: Complete Threading Workflow (ROBUST)
# Implements threading with verification and fallback
reply_to_individual_comment() {
  local comment_data="$1"
  local response_body="$2"

  # Extract comment details
  local comment_id=$(echo "$comment_data" | jq -r '.id')
  local file_path=$(echo "$comment_data" | jq -r '.path // empty')
  local line_number=$(echo "$comment_data" | jq -r '.line // .original_line // empty')

  echo "🔄 Processing comment #$comment_id..."

  # Step 1: Attempt true threaded reply
  if create_true_threaded_reply "$comment_id" "$response_body"; then
    # Step 2: Verify threading worked
    if verify_true_threading "$comment_id"; then
      echo "✅ SUCCESS: Threaded reply created for #$comment_id"
      return 0
    fi
  fi

  # Step 3: Fallback to general comment
  create_fallback_comment "$comment_id" "$response_body"
  return 1
}
```

**Critical Notes**:
- **Every single comment gets its own reply** - no exceptions for bots
- **Use GitHub MCP for threading** - ensures proper in_reply_to_id field
- **Verification mandatory** - confirm threading worked via API check
- **Fallback system required** - general comments if threading fails
- **Include status markers** - ✅ DONE or ❌ NOT DONE in every reply
- **Track success rate** - monitor threading vs fallback ratio

## Response Format

Each reply follows this format:
- **✅ DONE**: `✅ DONE: [explanation of fix/change made]`
- **❌ NOT DONE**: `❌ NOT DONE: [reason why not addressed]`

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
1. Comment #2223812756 (Copilot): Function parameter docs → ✅ DONE: Updated table format [THREADED: #2223999001]
2. Comment #2223812765 (Copilot): Migration status column → ✅ DONE: Added status tracking [THREADED: #2223999002]
3. Comment #2223812783 (Copilot): Port inconsistency → ✅ DONE: Fixed to port 6006 [THREADED: #2223999003]
4. Comment #2223818404 (CodeRabbit): Playwright vs Puppeter → ❌ NOT DONE: Playwright is correct per CLAUDE.md [FALLBACK: #2223999004]
5. Comment #2223818407 (CodeRabbit): Primary method conflict → ❌ NOT DONE: Intentional Playwright focus [THREADED: #2223999005]
6. [... continues for all 11 individual comments ...]

### ❌ Individual Comments NOT Addressed (0 comments)
[MUST BE ZERO - Every individual comment requires a response]

### 📊 Coverage Statistics
- **Individual comment coverage: 100% (11/11)**
- **Threading success rate: 90% (10/11 threaded, 1/11 fallback)**
- **API replies posted: 11 responses (10 threaded + 1 general)**
- **Bot comment coverage: 100% (11/11)**
- **Verification success: 100% (all replies confirmed via API)**
```

**SUCCESS CRITERIA**:
- ✅ 100% individual comment coverage (zero unaddressed)
- ✅ Every Copilot/CodeRabbit comment has a reply
- ✅ All API responses successfully posted to GitHub

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
