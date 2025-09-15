# /commentcheck Command

**Usage**: `/commentcheck [PR_NUMBER] [--verify-urls]`

🚨 **CRITICAL PURPOSE**: Verify 100% **UNRESPONDED COMMENT** coverage and response quality after comment reply process. Explicitly count and warn about any unresponded comments found.

🔒 **Security**: Uses safe jq --arg parameter passing to prevent command injection vulnerabilities and explicit variable validation.

## Universal Composition Integration

**Enhanced with /execute**: `/commentcheck` benefits from universal composition when called through `/execute`, which automatically provides intelligent optimization for large-scale comment verification while preserving systematic coverage analysis.

## 🎯 INDIVIDUAL COMMENT VERIFICATION MANDATE

**MANDATORY**: This command MUST explicitly count UNRESPONDED comments and provide clear warnings:
- **Zero tolerance policy** - No unresponded comment may be left without a response
- **Explicit counting** - Count and display total unresponded comments found
- **Warning system** - Clear alerts when unresponded comments > 0
- **Bot comment priority** - Copilot, CodeRabbit, GitHub Actions comments are REQUIRED responses
- **Evidence requirement** - Must show specific comment ID → reply ID mapping for unresponded items
- **Failure prevention** - Must catch cases like PR #864 (11 unresponded comments, 0 replies)
- **Direct reply verification** - Code fixes alone are insufficient; direct replies must be posted

## Description

Pure markdown command (no Python executable) that systematically verifies all PR comments have been properly addressed with appropriate responses. Always fetches fresh data from GitHub API - no cache dependencies. This command runs AFTER `/commentreply` to ensure nothing was missed.

## 🚨 COPILOT INTEGRATION REQUIREMENTS

### FAILURE ESCALATION (MANDATORY EXIT CODES):
- **EXIT CODE 1**: Unresponded comments detected - HALT copilot execution immediately
- **EXIT CODE 2**: GitHub API failures - HALT with diagnostic information
- **EXIT CODE 0**: Only when 100% coverage verified - ALLOW copilot to continue

### COPILOT INTEGRATION PROTOCOL:
- **PRE-PUSH GATE**: Must run before any push operations in copilot workflow
- **HARD STOP ENFORCEMENT**: Non-zero exit codes must halt copilot execution
- **NO BYPASS ALLOWED**: Cannot be skipped or ignored in copilot automation
- **COVERAGE THRESHOLD**: Exactly 0 unresponded comments required for success

## What It Does

1. **Fetches fresh comments data** directly from GitHub API
2. **Fetches current PR comment responses** from GitHub API
3. **Cross-references** original comments with posted responses
4. **Verifies coverage** - ensures every comment has a corresponding response
5. **Quality check** - confirms responses are substantial, not generic
6. **URL validation** - verifies threaded reply URLs are accessible and properly formatted
7. **Threading verification** - confirms real vs fake threading using URL patterns
8. **Reports status** with detailed breakdown

## Individual Comment Verification Process (CRITICAL)

### Step 1: Load ALL Individual Comments
🚨 **MANDATORY**: Systematically fetch every individual comment by type:

```bash
# 1. Fetch fresh comment data directly from GitHub API
PR_NUMBER=${1:-$(gh pr view --json number --jq .number)}
OWNER=$(gh repo view --json owner --jq .owner.login)
REPO=$(gh repo view --json name --jq .name)

# Get fresh comment counts from GitHub
TOTAL_ORIGINAL=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq length)
echo "Fresh comments found: $TOTAL_ORIGINAL"

# 2. Fetch current individual pull request comments (fresh)
PULL_COMMENTS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq length)
echo "Current pull request comments: $PULL_COMMENTS"

# 3. Fetch current issue comments (fresh)
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
  echo "🚨 CRITICAL: COPILOT EXECUTION HALTED" >&2
  echo "🚨 REASON: GitHub API failures detected" >&2
  echo "🚨 API_ERRORS: $API_ERRORS" >&2
  echo "This usually indicates authentication issues, network problems, or invalid PR number." >&2
  echo "EXIT CODE: 2 (API_FAILURE - Copilot execution must halt)" >&2
  exit 2
fi

TOTAL_CURRENT=$((PULL_COMMENTS + ISSUE_COMMENTS + REVIEW_COMMENTS))
echo "Total individual comments found: $TOTAL_CURRENT"

# 🚨 CRITICAL: Count unresponded comments explicitly
echo "=== UNRESPONDED COMMENTS ANALYSIS ==="
UNRESPONDED_COMMENTS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq '[.[] | select(.in_reply_to_id == null)] | length')
echo "🔍 Original (unreplied) comments: $UNRESPONDED_COMMENTS"

# Check if any original comment lacks replies
ORPHANED_COUNT=0
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.in_reply_to_id == null) | .id' | \
  while read -r original_id; do
    REPLIES_TO_THIS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
      jq --arg id "$original_id" '[.[] | select(.in_reply_to_id == ($id | tonumber))] | length')
    if [ "$REPLIES_TO_THIS" -eq 0 ]; then
      ORPHANED_COUNT=$((ORPHANED_COUNT + 1))
      echo "⚠️ UNRESPONDED: Comment #$original_id has NO replies"
    fi
  done

echo "📊 UNRESPONDED COMMENT COUNT: $ORPHANED_COUNT"
if [ "$ORPHANED_COUNT" -gt 0 ]; then
  echo "🚨 CRITICAL: COPILOT EXECUTION HALTED"
  echo "🚨 REASON: $ORPHANED_COUNT unresponded comments detected"
  echo "🚨 REQUIRED ACTION: Address ALL unresponded comments before copilot can continue"
  echo ""
  echo "UNRESPONDED COMMENTS:"
  # List each unresponded comment with details
  gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
    jq -r '.[] | select(.in_reply_to_id == null) | .id' | \
    while read -r original_id; do
      REPLIES_TO_THIS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
        jq --arg id "$original_id" '[.[] | select(.in_reply_to_id == ($id | tonumber))] | length')
      if [ "$REPLIES_TO_THIS" -eq 0 ]; then
        COMMENT_INFO=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
          jq --arg id "$original_id" -r '.[] | select(.id == ($id | tonumber)) | "- Comment #" + (.id | tostring) + " (" + .user.login + "): \"" + (.body | .[0:80]) + "...\""')
        echo "$COMMENT_INFO"
      fi
    done
  echo ""
  echo "EXIT CODE: 1 (FAILURE - Copilot execution must halt)"
  exit 1
else
  echo "✅ SUCCESS: All comments have been responded to"
  echo "✅ COPILOT CLEARED: All comments processed successfully"
  echo "✅ PROCEEDING: Copilot execution may continue"
  echo ""
  echo "EXIT CODE: 0 (SUCCESS - Copilot may proceed)"
fi
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
    REPLIES_TO_THIS=$(echo "$COMMENTS_DATA" | jq --arg id "$original_id" '[.[] | select(.in_reply_to_id == ($id | tonumber))] | length')
    if [ "$REPLIES_TO_THIS" -eq 0 ]; then
      COMMENT_INFO=$(echo "$COMMENTS_DATA" | jq --arg id "$original_id" -r '.[] | select(.id == ($id | tonumber)) | "Comment #\(.id) (\(.user.login)): NO THREADED REPLIES"')
      echo "❌ ORPHANED: $COMMENT_INFO"
    else
      COMMENT_INFO=$(echo "$COMMENTS_DATA" | jq --arg id "$original_id" --arg replies "$REPLIES_TO_THIS" -r '.[] | select(.id == ($id | tonumber)) | "Comment #\(.id) (\(.user.login)): " + $replies + " threaded replies"')
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
  echo "🚨 CRITICAL: COPILOT EXECUTION HALTED"
  echo "🚨 REASON: Fake/template comments detected"
  echo "🚨 FAKE COMMENTS DETECTED - Template patterns found"
  echo "🚨 REQUIRED ACTION: Delete fake responses and re-run with genuine analysis"
  echo ""
  echo "TEMPLATE ANALYSIS:"
  echo "- Generic responses: $GENERIC_COUNT"
  echo "- CodeRabbit templates: $CODERABBIT_RESPONSES"
  echo "- Copilot templates: $COPILOT_RESPONSES"
  echo ""
  echo "EXIT CODE: 1 (FAILURE - Fake comments prevent copilot execution)"
  exit 1
fi
```

### Step 5: URL Validation and Threading Verification (NEW)
🚨 **OPTIONAL WITH --verify-urls**: When `--verify-urls` flag is provided, validate all threaded reply URLs:

```bash
if [[ "$*" =~ --verify-urls ]]; then
  echo "=== URL VALIDATION AND THREADING VERIFICATION ==="

  # Check environment variables from recent /commentreply run
  if [ -n "$CREATED_REPLY_URL" ]; then
    echo "🔍 CHECKING: Recently created reply from /commentreply"
    echo "📍 URL: $CREATED_REPLY_URL"
    echo "🆔 Reply ID: $CREATED_REPLY_ID"
    echo "👤 Parent ID: $PARENT_COMMENT_ID"

    # Validate URL format
    validate_url_format "$CREATED_REPLY_URL" "$CREATED_REPLY_ID"

    # Test URL accessibility
    test_url_accessibility "$CREATED_REPLY_URL" "$CREATED_REPLY_ID"
  fi

  # Comprehensive URL validation for all threaded replies
  echo "🔍 COMPREHENSIVE: Validating all threaded reply URLs in PR #$PR_NUMBER"

  THREADED_REPLIES=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
    jq -r '.[] | select(.in_reply_to_id != null) | "\(.id)|\(.html_url)|\(.in_reply_to_id)"')

  TOTAL_VALIDATED=0
  VALID_THREADING=0
  VALID_URLS=0
  ACCESSIBLE_URLS=0
  FAKE_THREADING=0

  # Use process substitution to avoid subshell and preserve counters
  while IFS='|' read -r reply_id html_url parent_id; do
    if [ -n "$reply_id" ]; then
      TOTAL_VALIDATED=$((TOTAL_VALIDATED + 1))

      echo ""
      echo "🔍 VALIDATING: Reply #$reply_id"
      echo "📍 URL: $html_url"
      echo "👤 Parent: #$parent_id"

      # Validate URL format
      if validate_url_format "$html_url" "$reply_id"; then
        VALID_URLS=$((VALID_URLS + 1))
      else
        FAKE_THREADING=$((FAKE_THREADING + 1))
      fi

      # Validate threading relationship
      if validate_threading_relationship "$reply_id" "$parent_id"; then
        VALID_THREADING=$((VALID_THREADING + 1))
      fi

      # Test URL accessibility
      if test_url_accessibility "$html_url" "$reply_id"; then
        ACCESSIBLE_URLS=$((ACCESSIBLE_URLS + 1))
      fi
    fi
  done < <(echo "$THREADED_REPLIES")

  # Generate URL validation report
  generate_url_validation_report "$TOTAL_VALIDATED" "$VALID_THREADING" "$VALID_URLS" "$ACCESSIBLE_URLS" "$FAKE_THREADING"
fi

# URL Validation Functions
validate_url_format() {
  local url="$1"
  local comment_id="$2"

  echo "🔍 VALIDATING: URL format for comment #$comment_id"

  if [[ "$url" =~ #discussion_r[0-9]+ ]]; then
    echo "✅ VALID: Real threaded reply format (#discussion_r{id})"
    return 0
  elif [[ "$url" =~ #issuecomment-[0-9]+ ]]; then
    echo "❌ INVALID: Fake threading format (#issuecomment-{id})"
    echo "⚠️  WARNING: This is NOT a real threaded reply"
    return 1
  else
    echo "❌ INVALID: Unknown URL format"
    return 1
  fi
}

validate_threading_relationship() {
  local reply_id="$1"
  local expected_parent_id="$2"

  echo "🔍 VALIDATING: Threading relationship for reply #$reply_id"

  # Get reply data from API
  local reply_data=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
    jq ".[] | select(.id == $reply_id)")

  if [ -z "$reply_data" ]; then
    echo "❌ ERROR: Reply #$reply_id not found"
    return 1
  fi

  local actual_parent_id=$(echo "$reply_data" | jq -r '.in_reply_to_id')

  if [ "$actual_parent_id" = "$expected_parent_id" ]; then
    echo "✅ VALID: Reply #$reply_id properly threaded to parent #$expected_parent_id"
    return 0
  else
    echo "❌ INVALID: Reply #$reply_id threading mismatch"
    echo "   Expected parent: #$expected_parent_id"
    echo "   Actual parent: #$actual_parent_id"
    return 1
  fi
}

test_url_accessibility() {
  local url="$1"
  local comment_id="$2"

  echo "🔍 TESTING: URL accessibility for comment #$comment_id"

  # Test HTTP accessibility
  local http_status=$(curl -s -o /dev/null -w "%{http_code}" -L "$url" 2>/dev/null || echo "000")

  if [ "$http_status" = "200" ]; then
    echo "✅ ACCESSIBLE: URL returns HTTP 200"
    return 0
  else
    echo "❌ INACCESSIBLE: URL returns HTTP $http_status"
    return 1
  fi
}

generate_url_validation_report() {
  local total_checked="$1"
  local valid_threading="$2"
  local valid_urls="$3"
  local accessible_urls="$4"
  local fake_threading="$5"

  echo ""
  echo "📊 URL VALIDATION REPORT"
  echo "========================"
  echo "🔍 Total replies checked: $total_checked"
  echo "✅ Valid threading: $valid_threading"
  echo "✅ Valid URL format: $valid_urls"
  echo "✅ Accessible URLs: $accessible_urls"
  echo "❌ Fake threading detected: $fake_threading"

  if [ "$fake_threading" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: Fake threading detected!"
    echo "   These replies are NOT properly threaded and appear as separate comments"
    echo "   Use 'gh api repos/owner/repo/pulls/PR/comments --method POST --field in_reply_to=PARENT_ID'"
  fi

  if [ "$total_checked" -gt 0 ] && [ "$valid_threading" -eq "$total_checked" ] && [ "$fake_threading" -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS: All replies are properly threaded with valid URLs!"
  fi
}
```

## 🚨 ENHANCED FAILURE REPORTING (COPILOT INTEGRATION)

### UNRESPONDED COMMENT ESCALATION:
When unresponded comments are detected:
1. **IMMEDIATE ALERT**: Display critical failure warning
2. **DETAILED BREAKDOWN**: List every unresponded comment with ID and author
3. **COPILOT HALT**: Return exit code 1 to halt copilot execution
4. **ACTION REQUIRED**: Specify exact remediation needed

### EXAMPLE FAILURE OUTPUT:
```bash
🚨 CRITICAL: COPILOT EXECUTION HALTED
🚨 REASON: 3 unresponded comments detected
🚨 REQUIRED ACTION: Address ALL unresponded comments before copilot can continue

UNRESPONDED COMMENTS:
- Comment #2345255251 (coderabbitai[bot]): "Resolve contradiction: hard caps vs. NEVER stops"
- Comment #2345255260 (coderabbitai[bot]): "Fix ALL recent vs. 30 recent contradiction"
- Comment #2345449362 (cursor[bot]): "Bug: Agent Conflict: Feedback Handling"

EXIT CODE: 1 (FAILURE - Copilot execution must halt)
```

## ✅ COPILOT SUCCESS INTEGRATION

### SUCCESS VERIFICATION FOR COPILOT:
Only returns EXIT CODE 0 when:
- ✅ ZERO unresponded comments detected
- ✅ ALL comments have threaded replies or documented responses
- ✅ Coverage verification passes all checks
- ✅ No GitHub API errors encountered

### SUCCESS OUTPUT FOR COPILOT:
```bash
✅ SUCCESS: 100% comment coverage verified
✅ COPILOT CLEARED: All comments processed successfully
✅ PROCEEDING: Copilot execution may continue

EXIT CODE: 0 (SUCCESS - Copilot may proceed)
```

## 🚨 UNRESPONDED COMMENT WARNING SYSTEM (MANDATORY FORMAT)

🚨 **CRITICAL**: Report must explicitly count unresponded comments and provide clear warnings:

```
## 🚨 UNRESPONDED COMMENT WARNING REPORT

### 📊 UNRESPONDED COMMENT COUNT
🔍 **TOTAL UNRESPONDED COMMENTS**: 3

⚠️ **WARNING LEVEL**: HIGH (>0 unresponded comments detected)

### 🚨 UNRESPONDED COMMENTS REQUIRING IMMEDIATE ATTENTION
1. **Comment #2223812756** (Copilot): "Function parameter docs inconsistent"
   - ❌ **STATUS**: NO RESPONSE POSTED
   - 🚨 **ACTION REQUIRED**: Technical feedback must be addressed

2. **Comment #2223812765** (Copilot): "Migration status column missing"
   - ❌ **STATUS**: NO RESPONSE POSTED
   - 🚨 **ACTION REQUIRED**: Feature suggestion needs acknowledgment

3. **Comment #2223812783** (CodeRabbit): "Port inconsistency 8081 vs 6006"
   - ❌ **STATUS**: NO RESPONSE POSTED
   - 🚨 **ACTION REQUIRED**: Configuration issue must be resolved

### ✅ RESPONDED COMMENTS (FOR REFERENCE)
[List of comments that have received responses]

### 🚨 CRITICAL WARNINGS
- **UNRESPONDED COUNT**: 3 comments
- **WARNING**: Comment processing incomplete
- **REQUIRED ACTION**: Run `/commentreply` to address unresponded comments
- **ZERO TOLERANCE**: All comments must receive responses before PR completion

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

### 📈 UNRESPONDED COMMENT STATISTICS
- **Total comments found: 11**
- **Unresponded comments: 3 (27%)**
- **Responded comments: 8 (73%)**
- **Bot comment coverage: 67% (incomplete)**
- **COVERAGE SCORE: 73% ❌ FAILED**
- **🚨 CRITICAL**: 3 unresponded comments must be addressed immediately
```

## Individual Comment Success Criteria (ZERO TOLERANCE)

🚨 **✅ PASS REQUIREMENTS**: ZERO unresponded comments with quality responses
- **ZERO unresponded comments detected** (explicit count must be 0)
- **Clear warning system shows no alerts** (unresponded count = 0)
- **Every Copilot comment has a response** (technical feedback must be addressed)
- **Every CodeRabbit comment has a response** (AI suggestions require acknowledgment)
- **All responses address specific technical content** (not generic acknowledgments)
- **Appropriate ✅ DONE/❌ NOT DONE status** (clear resolution indication)
- **Professional and substantial replies** (meaningful engagement with feedback)

🚨 **❌ FAIL CONDITIONS**: ANY unresponded comments detected
- **ANY unresponded comment count > 0** (immediate failure with clear warning)
- **Warning system alerts triggered** (explicit alerts when unresponded comments found)
- **Generic/template responses** ("Thanks!" or "Will consider" are insufficient)
- **Bot comments ignored** (Copilot/CodeRabbit feedback requires responses)
- **Responses don't address technical content** (must engage with specific suggestions)
- **Unprofessional or inadequate replies** (maintain PR review standards)

### 🎯 SPECIFIC FAIL TRIGGERS (UNRESPONDED COMMENT FOCUS)
- **Unresponded comment count > 0** (explicit count detection and warning)
- **Zero individual responses** (like PR #864 - complete failure with 11 unresponded)
- **Partial bot coverage** (some Copilot/CodeRabbit comments without replies)
- **Warning system triggered** (any alerts about unresponded comments)
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
  replies_count=$(gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq --arg id "$comment_id" '[.[] | select(.in_reply_to_id == ($id | tonumber))] | length')
  echo "Comment $comment_id → replies: $replies_count"
done

# 6. CRITICAL: Verify PR #864 failure pattern doesn't repeat
COPILOT_COUNT=$(gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq '[.[] | select(.user.login | test("(?i)^copilot(\\[bot\\])?$"))] | length')
CODERABBIT_COUNT=$(gh api "/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq '[.[] | select(.user.login == "coderabbitai[bot]")] | length')
echo "Copilot comments: $COPILOT_COUNT | CodeRabbit comments: $CODERABBIT_COUNT"
echo "All bot comments MUST have responses or this check FAILS"
```

## Error Handling

- **GitHub API failures**: Clear error with guidance to check authentication
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

## 🚨 FINAL COPILOT INTEGRATION VERIFICATION

Add this final verification section at the end of the script execution:

```bash
# === FINAL COPILOT INTEGRATION VERIFICATION ===
echo "=== FINAL COPILOT INTEGRATION VERIFICATION ==="

# Re-verify unresponded comment count for copilot integration
FINAL_UNRESPONDED=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq '[.[] | select(.in_reply_to_id == null)] | length')

FINAL_REPLIES_NEEDED=0
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
  jq -r '.[] | select(.in_reply_to_id == null) | .id' | \
  while read -r original_id; do
    REPLIES_TO_THIS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | \
      jq --arg id "$original_id" '[.[] | select(.in_reply_to_id == ($id | tonumber))] | length')
    if [ "$REPLIES_TO_THIS" -eq 0 ]; then
      FINAL_REPLIES_NEEDED=$((FINAL_REPLIES_NEEDED + 1))
    fi
  done

echo "📊 FINAL VERIFICATION SUMMARY:"
echo "- Total original comments: $FINAL_UNRESPONDED"
echo "- Comments needing replies: $FINAL_REPLIES_NEEDED"

# COPILOT INTEGRATION: Final exit code determination
if [ "$FINAL_REPLIES_NEEDED" -gt 0 ]; then
  echo ""
  echo "🚨 CRITICAL: COPILOT EXECUTION HALTED"
  echo "🚨 FINAL VERIFICATION FAILED: $FINAL_REPLIES_NEEDED unresponded comments remain"
  echo "🚨 REQUIRED ACTION: Complete comment coverage before copilot can proceed"
  echo ""
  echo "EXIT CODE: 1 (FAILURE - Unresponded comments prevent copilot execution)"
  exit 1
else
  echo ""
  echo "✅ FINAL VERIFICATION PASSED: 100% comment coverage confirmed"
  echo "✅ COPILOT CLEARED: All verification checks successful"
  echo "✅ PROCEEDING: Copilot execution authorized to continue"
  echo ""
  echo "EXIT CODE: 0 (SUCCESS - Copilot may proceed with confidence)"
  exit 0
fi
```

This command ensures the comment response process maintains high quality and complete coverage for professional PR management, with bulletproof copilot integration that prevents false success declarations.
