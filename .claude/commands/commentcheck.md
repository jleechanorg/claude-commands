# /commentcheck Command

**Usage**: `/commentcheck [PR_NUMBER]`

🚨 **CRITICAL PURPOSE**: Verify 100% **INDIVIDUAL COMMENT** coverage and response quality after comment reply process.

## 🎯 INDIVIDUAL COMMENT VERIFICATION MANDATE

**MANDATORY**: This command MUST verify that EVERY single individual comment received a direct reply:
- **Zero tolerance policy** - No individual comment may be left without a response
- **Bot comment priority** - Copilot, CodeRabbit, GitHub Actions comments are REQUIRED responses
- **Evidence requirement** - Must show specific comment ID → reply ID mapping
- **Failure prevention** - Must catch cases like PR #864 (11 individual comments, 0 replies)
- **Direct reply verification** - Code fixes alone are insufficient; direct replies must be posted

## Description

Pure markdown command (no Python executable) that systematically verifies all PR comments have been properly addressed with appropriate responses. This command runs AFTER `/commentreply` to ensure nothing was missed.

## What It Does

1. **Loads comments data** from `/tmp/copilot_{branch}/comments_{branch}.json`
2. **Fetches current PR comment responses** from GitHub API
3. **Cross-references** original comments with posted responses
4. **Verifies coverage** - ensures every comment has a corresponding response
5. **Quality check** - confirms responses are substantial, not generic
6. **Reports status** with detailed breakdown

## Individual Comment Verification Process (CRITICAL)

### Step 1: Load ALL Individual Comments
🚨 **MANDATORY**: Systematically fetch every individual comment by type:

```bash
# 1. Load original comment data from /commentfetch
BRANCH=$(git branch --show-current)
SANITIZED_BRANCH=$(echo "$BRANCH" | sed 's/[^a-zA-Z0-9._-]/_/g' | sed 's/^[.-]*//g')
TOTAL_ORIGINAL=$(cat /tmp/copilot_${SANITIZED_BRANCH}/comments_${SANITIZED_BRANCH}.json | jq '.comments | length')
echo "Original comments found: $TOTAL_ORIGINAL"

# 2. Fetch current individual pull request comments
PULL_COMMENTS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq length)
echo "Current pull request comments: $PULL_COMMENTS"

# 3. Fetch current issue comments
ISSUE_COMMENTS=$(gh api "repos/$OWNER/$REPO/issues/$PR_NUMBER/comments" --paginate | jq length)
echo "Current issue comments: $ISSUE_COMMENTS"

# 4. Fetch current review comments - FIXED: More robust pagination and counting
REVIEW_COMMENTS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" --paginate 2>/dev/null | jq -r '.[] | select(.body != null and .body != "") | .id' | wc -l 2>/dev/null || echo "0")
echo "Current review comments: $REVIEW_COMMENTS"

# 5. Count total individual comments with enhanced error handling and stderr capture
API_ERRORS=""
if ! [[ "$PULL_COMMENTS" =~ ^[0-9]+$ ]]; then
  API_ERRORS="${API_ERRORS}PULL_COMMENTS API error: $PULL_COMMENTS; "
fi
if ! [[ "$ISSUE_COMMENTS" =~ ^[0-9]+$ ]]; then
  API_ERRORS="${API_ERRORS}ISSUE_COMMENTS API error: $ISSUE_COMMENTS; "
fi
if ! [[ "$REVIEW_COMMENTS" =~ ^[0-9]+$ ]]; then
  API_ERRORS="${API_ERRORS}REVIEW_COMMENTS API error: $REVIEW_COMMENTS; "
fi

if [[ -n "$API_ERRORS" ]]; then
  echo "Error: GitHub API failures detected: $API_ERRORS" >&2
  echo "This usually indicates authentication issues, network problems, or invalid PR number." >&2
  exit 1
fi

TOTAL_CURRENT=$((PULL_COMMENTS + ISSUE_COMMENTS + REVIEW_COMMENTS))
echo "Total individual comments found: $TOTAL_CURRENT"
```

### Step 2: Individual Comment Threading Verification (ENHANCED)
🚨 **MANDATORY**: For EACH individual comment, verify THREADED response exists with in_reply_to_id:

```bash
# Enhanced threading verification with error handling - FETCH ALL COMMENT SOURCES
echo "=== THREADING VERIFICATION ANALYSIS ==="

# Fetch all comment sources: PR comments, issue comments, and review comments
PR_COMMENTS_DATA=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate 2>/dev/null)
ISSUE_COMMENTS_DATA=$(gh api "repos/$OWNER/$REPO/issues/$PR_NUMBER/comments" --paginate 2>/dev/null)
REVIEW_COMMENTS_DATA=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" --paginate 2>/dev/null | jq -r '.[].id' | xargs -I {} gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews/{}/comments" 2>/dev/null || echo '[]')

if [ $? -ne 0 ] || [ -z "$PR_COMMENTS_DATA" ]; then
  echo "Error: Failed to fetch pull request comments from GitHub API" >&2
  exit 1
fi

# Combine all comment sources into one dataset
COMMENTS_DATA=$(echo "$PR_COMMENTS_DATA $ISSUE_COMMENTS_DATA $REVIEW_COMMENTS_DATA" | jq -s 'add | unique_by(.id)')

# Step 2A: Analyze threading status for ALL comments
echo "$COMMENTS_DATA" | jq -r '.[] | "ID: \(.id) | Author: \(.user.login) | In-Reply-To: \(.in_reply_to_id // "none") | Threaded: \(.in_reply_to_id != null)"'

# Step 2B: Count threading success rates
TOTAL_COMMENTS=$(echo "$COMMENTS_DATA" | jq length)
THREADED_REPLIES=$(echo "$COMMENTS_DATA" | jq '[.[] | select(.in_reply_to_id != null)] | length')
UNTHREADED_COMMENTS=$(echo "$COMMENTS_DATA" | jq '[.[] | select(.in_reply_to_id == null)] | length')

echo "Total comments: $TOTAL_COMMENTS"
echo "Threaded replies: $THREADED_REPLIES"
echo "Unthreaded comments: $UNTHREADED_COMMENTS"

if [ "$TOTAL_COMMENTS" -gt 0 ]; then
  THREADING_PERCENTAGE=$(( (THREADED_REPLIES * 100) / TOTAL_COMMENTS ))
  echo "Threading success rate: $THREADING_PERCENTAGE%"
fi

# Step 2C: Detailed bot comment threading analysis
echo "\n=== BOT COMMENT THREADING ANALYSIS ==="
echo "$COMMENTS_DATA" | \
  jq -r '.[] | select(.user.login | test("(?i)^(copilot(\\[bot\\])?|coderabbitai\\[bot\\])$")) | "Bot Comment #\(.id) (\(.user.login)): Threaded=\(.in_reply_to_id != null) | Reply-To: \(.in_reply_to_id // "none")"'

# Step 2D: Find orphaned original comments (no replies to them)
echo "\n=== ORPHANED ORIGINAL COMMENTS ==="
echo "$COMMENTS_DATA" | \
  jq -r '.[] | select(.in_reply_to_id == null) | .id' | \
  while read -r original_id; do
    # Check if any comment replies to this original
    REPLIES_TO_THIS=$(echo "$COMMENTS_DATA" | jq "[.[] | select(.in_reply_to_id == $original_id)] | length")
    if [ "$REPLIES_TO_THIS" -eq 0 ]; then
      COMMENT_INFO=$(echo "$COMMENTS_DATA" | jq -r ".[] | select(.id == $original_id) | \"Comment #\(.id) (\(.user.login)): NO THREADED REPLIES\"")
      echo "❌ ORPHANED: $COMMENT_INFO"
    else
      COMMENT_INFO=$(echo "$COMMENTS_DATA" | jq -r ".[] | select(.id == $original_id) | \"Comment #\(.id) (\(.user.login)): $REPLIES_TO_THIS threaded replies\"")
      echo "✅ REPLIED: $COMMENT_INFO"
    fi
  done
```

### Step 3: Individual Comment Coverage Analysis (ENHANCED ZERO TOLERANCE)
🚨 **CRITICAL**: For each original individual comment:
- **Threading verification** - Confirm comment has in_reply_to_id field populated correctly
- **Exact ID matching** - Find corresponding threaded response using comment ID
- **Direct reply verification** - Confirm reply was posted to that specific comment thread
- **Bot comment priority** - Ensure ALL Copilot/CodeRabbit comments have THREADED responses
- **Response quality check** - Verify responses address the specific technical content
- **Fallback detection** - Identify general comments that reference but don't thread to originals
- **Success rate analysis** - Calculate threading vs fallback vs missing response ratios

### Step 4: Quality Assessment & Fake Comment Detection
🚨 **CRITICAL**: Response quality criteria PLUS fake comment detection:
- **Not generic** - No template responses like "Thanks for feedback"
- **Addresses specifics** - Responds to actual technical content
- **Proper status** - Clear DONE/NOT DONE indication
- **Professional tone** - Appropriate for PR context

### 🚨 FAKE COMMENT DETECTION (MANDATORY)
**MUST identify and flag template/fake responses:**

```bash
echo "=== FAKE COMMENT DETECTION ==="

# Pattern 1: Identical repeated responses
echo "Checking for identical repeated responses..."
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.user.login == "jleechan2015") | .body' | \
  sort | uniq -c | sort -nr | head -10

# Pattern 2: Template-based responses
echo "Checking for template patterns..."
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.user.login == "jleechan2015") | .body' | \
  grep -E "(Thank you .* for|Comment processed|The threading implementation|copilot threading system)" | \
  wc -l

# Pattern 3: Generic acknowledgments without specifics
echo "Checking for generic responses..."
GENERIC_COUNT=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.user.login == "jleechan2015") | .body' | \
  grep -c "100% coverage achieved\|threading system is fully operational" || echo 0)
echo "Generic template responses found: $GENERIC_COUNT"

# Pattern 4: Author-based templating detection
echo "Checking for author-based templating..."
CODERABBIT_RESPONSES=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.user.login == "jleechan2015") | .body' | \
  grep -c "Thank you CodeRabbit" || echo 0)
COPILOT_RESPONSES=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.user.login == "jleechan2015") | .body' | \
  grep -c "Thank you.*Copilot" || echo 0)

echo "CodeRabbit-specific templates: $CODERABBIT_RESPONSES"
echo "Copilot-specific templates: $COPILOT_RESPONSES"

# Flag as FAKE if template patterns detected
if [ "$GENERIC_COUNT" -gt 5 ] || [ "$CODERABBIT_RESPONSES" -gt 10 ] || [ "$COPILOT_RESPONSES" -gt 5 ]; then
  echo "🚨 FAKE COMMENTS DETECTED - Template patterns found"
  echo "RECOMMENDATION: Delete fake responses and re-run with genuine analysis"
fi
```

## Individual Comment Coverage Report (MANDATORY FORMAT)

🚨 **CRITICAL**: Report must show individual comment coverage with zero tolerance for missing replies:

```
## 🎯 Individual Comment Coverage Analysis

### 📊 INDIVIDUAL COMMENT INVENTORY
**Total Individual Comments**: 11
- Copilot bot comments: 3
- CodeRabbit bot comments: 8
- Human reviewer comments: 0
- GitHub Actions comments: 0

### ✅ Individual Comments WITH Responses (TARGET: 100%)
1. Comment #2223812756 (Copilot): "Function parameter docs inconsistent"
   → Reply #XXXXX: "✅ DONE: Updated table to show all parameters consistently"

2. Comment #2223812765 (Copilot): "Migration status column missing"
   → Reply #XXXXX: "✅ DONE: Added Migration Status column with tracking"

3. Comment #2223812783 (Copilot): "Port inconsistency 8081 vs 6006"
   → Reply #XXXXX: "✅ DONE: Fixed all references to use port 6006"

[... continues for ALL individual comments ...]

### ❌ Individual Comments WITHOUT Responses (TARGET: 0)
[THIS SECTION MUST BE EMPTY - Any entries here indicate FAILURE]

### ⚠️ Poor Quality Individual Responses (TARGET: 0)
[List any generic/template responses that don't address specific technical content]

### 🚨 FAILURE CASE REFERENCES

**PR #864**: 11 individual comments received ZERO replies
- All 3 Copilot comments: NO RESPONSE
- All 8 CodeRabbit comments: NO RESPONSE
- Result: Complete failure of individual comment coverage

**PR #867 (Initial)**: 7 individual comments with code fixes but NO direct replies
- All 5 Copilot comments: Code fixes implemented but NO individual replies posted
- 1 CodeRabbit comment: NO direct reply
- 1 Copilot-PR-Reviewer: NO direct reply
- Result: False claim of "100% coverage" when actual coverage was 0%
- **Corrected**: Direct replies posted to achieve actual 100% coverage

### 📈 Individual Comment Coverage Statistics
- **Individual comments found: 11**
- **Individual comments with responses: 11 (100%)**
- **Missing individual responses: 0 (0%)**
- **Bot comment coverage: 100% (11/11)**
- **COVERAGE SCORE: 100% ✅**
```

## Individual Comment Success Criteria (ZERO TOLERANCE)

🚨 **✅ PASS REQUIREMENTS**: 100% individual comment coverage with quality responses
- **ALL individual comments have direct replies** (no exceptions for bots)
- **Every Copilot comment has a response** (technical feedback must be addressed)
- **Every CodeRabbit comment has a response** (AI suggestions require acknowledgment)
- **All responses address specific technical content** (not generic acknowledgments)
- **Appropriate ✅ DONE/❌ NOT DONE status** (clear resolution indication)
- **Professional and substantial replies** (meaningful engagement with feedback)

🚨 **❌ FAIL CONDITIONS**: Any individual comment coverage gap
- **ANY individual comment without response** (immediate failure)
- **Generic/template responses** ("Thanks!" or "Will consider" are insufficient)
- **Bot comments ignored** (Copilot/CodeRabbit feedback requires responses)
- **Responses don't address technical content** (must engage with specific suggestions)
- **Unprofessional or inadequate replies** (maintain PR review standards)

### 🎯 SPECIFIC FAIL TRIGGERS
- **Zero individual responses** (like PR #864 - complete failure)
- **Partial bot coverage** (some Copilot/CodeRabbit comments without replies)
- **Template responses only** (generic acknowledgments without substance)
- **Ignored technical suggestions** (failing to address specific code feedback)

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

## Individual Comment Verification API Commands (CRITICAL)

🚨 **MANDATORY**: Use these exact API commands to verify individual comment coverage:

```bash
# 1. Get ALL individual pull request comments with pagination
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate

# 2. Count individual comments by author type
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq 'group_by(.user.login) | map({author: .[0].user.login, count: length})'

# 3. Check for replies on EACH individual comment
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | "ID: \(.id) | Author: \(.user.login) | Replies: \(.replies_url)"'

# 4. Verify bot comment coverage specifically
echo "=== COPILOT COMMENTS ==="
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.user.login == "Copilot") | "Comment #\(.id): \(.body[0:80])..."'

echo "=== CODERABBIT COMMENTS ==="
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.user.login == "coderabbitai[bot]") | "Comment #\(.id): \(.body[0:80])..."'

# 5. Check for actual reply threads on individual comments (CORRECTED METHOD)
echo "Fetching all comments and checking for actual replies..."
gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
jq -r '.[] | "Comment ID: \(.id) | Author: \(.user.login) | Has Threaded Replies: \(if .in_reply_to_id then "No (this is a reply)" else "Checking..." end)"'

# Check for replies to each original comment
for comment_id in $(gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq -r '.[] | select(.in_reply_to_id == null) | .id'); do
  echo "Checking original comment $comment_id for replies..."
  replies_count=$(gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq "[.[] | select(.in_reply_to_id == $comment_id)] | length")
  echo "Comment $comment_id → replies: $replies_count"
done

# 6. CRITICAL: Verify PR #864 failure pattern doesn't repeat
COPILOT_COUNT=$(gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq '[.[] | select(.user.login | test("(?i)^copilot(\\[bot\\])?$"))] | length')
CODERABBIT_COUNT=$(gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq '[.[] | select(.user.login == "coderabbitai[bot]")] | length')
echo "Copilot comments: $COPILOT_COUNT | CodeRabbit comments: $CODERABBIT_COUNT"
echo "All bot comments MUST have responses or this check FAILS"
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
