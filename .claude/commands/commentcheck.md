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

Pure markdown command (no Python executable) that systematically verifies all PR comments have been properly addressed with appropriate responses. **ORCHESTRATES /commentfetch for data source** instead of duplicating GitHub API calls. This command runs AFTER `/commentreply` to ensure nothing was missed.

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

1. **Orchestrates /commentfetch** for comprehensive comment data (eliminates duplicate API calls)
2. **Analyzes JSON output** from commentfetch for coverage verification
3. **Cross-references** original comments with posted responses using structured data
4. **Verifies coverage** - ensures every comment has a corresponding response
5. **Quality check** - confirms responses are substantial, not generic
6. **Reports status** with detailed breakdown using commentfetch metadata

## Individual Comment Verification Process (ORCHESTRATED)

### Step 1: Load ALL Individual Comments (ORCHESTRATED)
🚨 **MANDATORY**: Use `/commentfetch` for comprehensive comment data instead of duplicating API calls:

```bash
# 1. Get PR number and validate
PR_NUMBER=${1:-$(gh pr view --json number --jq .number)}
if [ -z "$PR_NUMBER" ]; then
  echo "❌ ERROR: Could not determine PR number. Please specify PR number or run from PR branch."
  echo "EXIT CODE: 2 (API_FAILURE - Copilot execution must halt)"
  exit 2
fi

echo "🚀 ORCHESTRATING: Fetching comprehensive comment data via /commentfetch..."
echo "🔍 COMPREHENSIVE COMMENT ANALYSIS FOR PR #$PR_NUMBER"
echo "=================================================================="

# 2. Execute commentfetch Python implementation for comprehensive multi-API comment fetching
cd .claude/commands && python3 -c "
import _copilot_modules.commentfetch as cf
import sys
fetch = cf.CommentFetch(sys.argv[1])
fetch.execute()
" "$PR_NUMBER"

# 3. Use structured JSON output from commentfetch
BRANCH_NAME=$(git branch --show-current)
COMMENTS_FILE="/tmp/$BRANCH_NAME/comments.json"

if [ ! -f "$COMMENTS_FILE" ]; then
  echo "🚨 CRITICAL: COPILOT EXECUTION HALTED" >&2
  echo "🚨 REASON: commentfetch failed to provide structured data at $COMMENTS_FILE" >&2
  echo "This indicates commentfetch execution failure or missing output file." >&2
  echo "EXIT CODE: 2 (API_FAILURE - Copilot execution must halt)" >&2
  exit 2
fi

echo "✅ DATA SOURCE: Using commentfetch structured output from $COMMENTS_FILE"

# 4. Extract comprehensive comment statistics from commentfetch JSON
TOTAL_COMMENTS=$(jq '.metadata.total' "$COMMENTS_FILE" 2>/dev/null || echo "0")
UNRESPONDED_COUNT=$(jq '.metadata.unresponded_count' "$COMMENTS_FILE" 2>/dev/null || echo "0")
INLINE_COUNT=$(jq '.metadata.by_type.inline' "$COMMENTS_FILE" 2>/dev/null || echo "0")
GENERAL_COUNT=$(jq '.metadata.by_type.general' "$COMMENTS_FILE" 2>/dev/null || echo "0")
REVIEW_COUNT=$(jq '.metadata.by_type.review' "$COMMENTS_FILE" 2>/dev/null || echo "0")
COPILOT_COUNT=$(jq '.metadata.by_type.copilot' "$COMMENTS_FILE" 2>/dev/null || echo "0")

echo "📊 COMPREHENSIVE COMMENT BREAKDOWN (via commentfetch):"
echo "   Total comments detected: $TOTAL_COMMENTS"
echo "   Inline review comments: $INLINE_COUNT"
echo "   General PR comments: $GENERAL_COUNT"
echo "   Review summary comments: $REVIEW_COUNT"
echo "   Copilot comments: $COPILOT_COUNT"
echo "   Unresponded comments: $UNRESPONDED_COUNT"

# 5. Validate commentfetch data quality
if [ "$TOTAL_COMMENTS" -eq 0 ]; then
  echo "⚠️ WARNING: No comments detected by commentfetch"
  echo "This may indicate API access issues or an empty PR"
fi

echo "🎯 COMMENTFETCH ORCHESTRATION: Successfully loaded $TOTAL_COMMENTS comments"
echo "📈 UNRESPONDED ANALYSIS: $UNRESPONDED_COUNT comments require attention"
```

### Step 2: Individual Comment Threading Verification (JSON-BASED)
🚨 **MANDATORY**: Use commentfetch JSON data for threading analysis instead of duplicate API calls:

```bash
# Enhanced threading verification using commentfetch structured data
echo "=== THREADING VERIFICATION ANALYSIS (JSON-BASED) ==="

# Use commentfetch JSON output instead of making new API calls
ALL_COMMENTS=$(jq '.comments' "$COMMENTS_FILE" 2>/dev/null || echo '[]')
if [ "$(echo "$ALL_COMMENTS" | jq length)" -eq 0 ]; then
  echo "🚨 CRITICAL: COPILOT EXECUTION HALTED" >&2
  echo "🚨 REASON: No comment data available from commentfetch JSON" >&2
  echo "EXIT CODE: 2 (API_FAILURE - Copilot execution must halt)" >&2
  exit 2
fi

echo "✅ USING COMMENTFETCH DATA: $(echo "$ALL_COMMENTS" | jq length) comments loaded"

# Step 2A: Analyze threading status for ALL comments (from commentfetch data)
echo "📊 THREADING STATUS ANALYSIS:"
echo "$ALL_COMMENTS" | jq -r '.[] | "ID: \(.id) | Author: \(.author) | Type: \(.type) | Replied: \(.already_replied)"'

# Step 2B: Count threading success rates (using commentfetch metadata)
TOTAL_COMMENTS=$(echo "$ALL_COMMENTS" | jq length)
ALREADY_REPLIED=$(echo "$ALL_COMMENTS" | jq '[.[] | select(.already_replied == true)] | length')
REQUIRES_RESPONSE=$(echo "$ALL_COMMENTS" | jq '[.[] | select(.requires_response == true)] | length')

echo ""
echo "📈 THREADING STATISTICS (from commentfetch):"
echo "   Total comments: $TOTAL_COMMENTS"
echo "   Already replied: $ALREADY_REPLIED"
echo "   Requires response: $REQUIRES_RESPONSE"

if [ "$TOTAL_COMMENTS" -gt 0 ]; then
  RESPONSE_PERCENTAGE=$(( (ALREADY_REPLIED * 100) / TOTAL_COMMENTS ))
  echo "   Response rate: $RESPONSE_PERCENTAGE%"
fi

# Step 2C: Bot comment analysis (using commentfetch classification)
echo ""
echo "🤖 BOT COMMENT ANALYSIS (from commentfetch):"
BOT_COMMENTS=$(echo "$ALL_COMMENTS" | jq '[.[] | select(.author | test("coderabbitai|cursor|copilot"))]')
BOT_COUNT=$(echo "$BOT_COMMENTS" | jq length)
BOT_UNRESPONDED=$(echo "$BOT_COMMENTS" | jq '[.[] | select(.already_replied == false)] | length')

echo "   Total bot comments: $BOT_COUNT"
echo "   Bot comments unresponded: $BOT_UNRESPONDED"
if [ "$BOT_COUNT" -gt 0 ]; then
  echo "   Bot response rate: $(( (BOT_COUNT - BOT_UNRESPONDED) * 100 / BOT_COUNT ))%"
else
  echo "   Bot response rate: N/A"
fi

# Step 2D: List unresponded comments (using commentfetch filtering)
echo ""
echo "❌ UNRESPONDED COMMENTS (from commentfetch analysis):"
UNRESPONDED_COMMENTS=$(echo "$ALL_COMMENTS" | jq '[.[] | select(.already_replied == false)]')
echo "$UNRESPONDED_COMMENTS" | jq -r '.[] | "❌ Comment #\(.id) (\(.author)): \(.body[0:80])..."'
```

### Step 3: Quality Assessment & Fake Comment Detection (JSON-BASED)
🚨 **CRITICAL**: Use commentfetch data for response quality analysis instead of duplicate API calls:

```bash
echo "=== QUALITY ASSESSMENT & FAKE COMMENT DETECTION (JSON-BASED) ==="

# Use commentfetch JSON for quality analysis
HUMAN_RESPONSES=$(echo "$ALL_COMMENTS" | jq '[.[] | select(.author == "jleechan2015")]')
HUMAN_RESPONSE_COUNT=$(echo "$HUMAN_RESPONSES" | jq length)

echo "📊 RESPONSE QUALITY ANALYSIS:"
echo "   Human responses found: $HUMAN_RESPONSE_COUNT"

# Pattern analysis using commentfetch data
echo "🔍 PATTERN ANALYSIS (using commentfetch data):"

# Pattern 1: Check for template responses
TEMPLATE_RESPONSES=$(echo "$HUMAN_RESPONSES" | jq '[.[] | select(.body | test("Thank you.*for|Comment processed|threading implementation"))]')
TEMPLATE_COUNT=$(echo "$TEMPLATE_RESPONSES" | jq length)
echo "   Template-based responses: $TEMPLATE_COUNT"

# Pattern 2: Generic acknowledgments
GENERIC_RESPONSES=$(echo "$HUMAN_RESPONSES" | jq '[.[] | select(.body | test("100% coverage achieved|threading system is fully operational"))]')
GENERIC_COUNT=$(echo "$GENERIC_RESPONSES" | jq length)
echo "   Generic acknowledgments: $GENERIC_COUNT"

# Pattern 3: Bot-specific templating
CODERABBIT_RESPONSES=$(echo "$HUMAN_RESPONSES" | jq '[.[] | select(.body | test("Thank you CodeRabbit"))]')
CODERABBIT_COUNT=$(echo "$CODERABBIT_RESPONSES" | jq length)
echo "   CodeRabbit-specific templates: $CODERABBIT_COUNT"

# Quality assessment
if [ "$GENERIC_COUNT" -gt 5 ] || [ "$CODERABBIT_COUNT" -gt 10 ] || [ "$TEMPLATE_COUNT" -gt 5 ]; then
  echo "🚨 CRITICAL: COPILOT EXECUTION HALTED"
  echo "🚨 REASON: Fake/template comments detected"
  echo "🚨 FAKE COMMENTS DETECTED - Template patterns found"
  echo "🚨 REQUIRED ACTION: Delete fake responses and re-run with genuine analysis"
  echo ""
  echo "TEMPLATE ANALYSIS:"
  echo "   TEMPLATE COUNT: $TEMPLATE_COUNT | GENERIC: $GENERIC_COUNT | CODERABBIT: $CODERABBIT_COUNT"
  echo ""
  echo "EXIT CODE: 1 (FAILURE - Fake comments prevent copilot execution)"
  exit 1
else
  echo "✅ QUALITY CHECK PASSED: No excessive template patterns detected"
fi
```

### Step 4: Final Coverage Report (COMPREHENSIVE)
🚨 **CRITICAL**: Generate final coverage report using commentfetch comprehensive data:

```bash
echo "=================================================================="
echo "🚨 COMPREHENSIVE COMMENT COVERAGE REPORT (COMMENTFETCH-BASED)"
echo "=================================================================="

# Use commentfetch data for final assessment
FINAL_UNRESPONDED_COUNT=$(jq '.metadata.unresponded_count' "$COMMENTS_FILE" 2>/dev/null || echo "0")
FINAL_TOTAL_COUNT=$(jq '.metadata.total' "$COMMENTS_FILE" 2>/dev/null || echo "0")
FINAL_BY_TYPE=$(jq '.metadata.by_type' "$COMMENTS_FILE" 2>/dev/null || echo '{}')

if [ "$FINAL_UNRESPONDED_COUNT" -eq 0 ]; then
    echo "✅ **ZERO TOLERANCE POLICY: PASSED**"
    echo "🎉 **SUCCESS**: All $FINAL_TOTAL_COUNT comments have received responses"
    echo "📈 **COVERAGE SCORE**: 100% ✅ PASSED"
    echo ""
    echo "📊 **COMPREHENSIVE STATISTICS (via commentfetch):**"
    echo "   - Total comments detected: $FINAL_TOTAL_COUNT"
    echo "   - Inline review comments: $(echo "$FINAL_BY_TYPE" | jq '.inline // 0')"
    echo "   - General PR comments: $(echo "$FINAL_BY_TYPE" | jq '.general // 0')"
    echo "   - Review summary comments: $(echo "$FINAL_BY_TYPE" | jq '.review // 0')"
    echo "   - Copilot comments: $(echo "$FINAL_BY_TYPE" | jq '.copilot // 0')"
    echo "   - All comments addressed: ✅"
    echo ""
    echo "🎯 **COMMENTFETCH ORCHESTRATION SUCCESS**: Comprehensive coverage verified"
    echo "✅ COPILOT CLEARED: All comments processed successfully"
    echo "✅ PROCEEDING: Copilot execution may continue"
    echo ""
    echo "EXIT CODE: 0 (SUCCESS - Copilot may proceed)"
    exit 0
else
    echo "🚨 **ZERO TOLERANCE POLICY: FAILED**"
    echo "❌ **FAILURE**: $FINAL_UNRESPONDED_COUNT unresponded comments detected"
    echo "📈 **COVERAGE SCORE**: $(( (FINAL_TOTAL_COUNT - FINAL_UNRESPONDED_COUNT) * 100 / FINAL_TOTAL_COUNT ))% ❌ FAILED"
    echo ""
    echo "🚨 **UNRESPONDED COMMENTS REQUIRING IMMEDIATE ATTENTION**:"

    # List unresponded comments from commentfetch data
    UNRESPONDED_LIST=$(jq -r '.comments[] | select(.already_replied == false) | "❌ Comment #\(.id) (\(.author)): \(.body[0:80])..."' "$COMMENTS_FILE" 2>/dev/null)
    echo "$UNRESPONDED_LIST"

    echo ""
    echo "🚨 CRITICAL: COPILOT EXECUTION HALTED"
    echo "🚨 REASON: $FINAL_UNRESPONDED_COUNT unresponded comments detected"
    echo "🚨 REQUIRED ACTION: Address ALL unresponded comments before copilot can continue"
    echo ""
    echo "🔧 **REQUIRED ACTION**: Run /commentreply to address unresponded comments"
    echo "⚠️ **WORKFLOW HALT**: Cannot proceed until all comments addressed"
    echo "📊 **COMMENTFETCH DATA**: $FINAL_TOTAL_COUNT total, $FINAL_UNRESPONDED_COUNT unresponded"
    echo ""
    echo "EXIT CODE: 1 (FAILURE - Copilot execution must halt)"
    exit 1
fi
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

## Architectural Benefits

- **Orchestration over Duplication** - Follows CLAUDE.md principles
- **Single source of truth** - commentfetch is authoritative for comment data
- **Consistent data format** - Both commands use same JSON structure
- **Reduced maintenance** - Bug fixes in commentfetch benefit both commands
- **Clear separation** - commentfetch fetches, commentcheck verifies
- **Performance** - No duplicate API calls or processing

## Error Handling

- **commentfetch failures**: Clear error with diagnostic information
- **JSON parsing issues**: Graceful fallback with error reporting
- **Missing data files**: Explicit error messages with remediation steps
- **API access problems**: Delegated to commentfetch for handling

## Benefits

- **Quality assurance** - Ensures responses meet professional standards
- **Complete coverage** - Guarantees no comments are missed (via commentfetch)
- **Audit trail** - Provides detailed verification report
- **Process improvement** - Identifies patterns in response quality
- **User confidence** - Confirms all feedback was properly addressed
- **Architectural compliance** - Eliminates code duplication

## Example Usage

```bash
# After running /commentreply
/commentcheck 1603

# Will orchestrate commentfetch and verify:
# ✅ All comments have responses
# ✅ Responses address specific content
# ✅ Proper DONE/NOT DONE classification
# ✅ Professional and substantial replies
# 📊 Generate detailed coverage report
```

This command ensures the comment response process maintains high quality and complete coverage for professional PR management, with proper orchestration of commentfetch eliminating code duplication.
