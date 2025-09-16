# /copilot - Type-Aware Threading Architecture

**Purpose**: Ultra-fast PR processing with type-segmented comment handling and mandatory threading verification.

## 🚨 TYPE-AWARE THREADING ARCHITECTURE

**CORE PRINCIPLE**: Each comment type requires specific API endpoint and threading verification
- ❌ NO GENERIC COMMENT PROCESSING - Type-specific handlers only
- ❌ NO THREADING WITHOUT VERIFICATION - Real-time threading success checks
- ❌ NO MIXED ENDPOINT USAGE - Strict API endpoint separation
- ✅ IMMEDIATE THREADING FEEDBACK PER COMMENT TYPE

## EXECUTION PROTOCOL

### Phase 1: Type-Segmented Comment Collection
**MANDATORY**: Collect and classify ALL comments by type with proof of success

```
STEP 1: Get current PR number and validate repository info
STEP 2: Fetch Issue Comments (GitHub issues API)
STEP 3: Fetch PR Comments (GitHub pulls API)
STEP 4: Fetch Review Comments (GitHub reviews API)
STEP 5: VERIFY: Each comment type count > 0 and properly classified
CHECKPOINT: Type-segmented comment data ready for processing
```

### Phase 2: Type-Specific Response Generation
**MANDATORY**: Generate responses tailored to each comment type

```
STEP 1: Process Issue Comments (general PR discussion responses)
STEP 2: Process PR Comments (inline code comment responses)
STEP 3: Process Review Comments (review-specific responses)
STEP 4: VERIFY: Response count matches input count per type
CHECKPOINT: All comment types have corresponding typed responses
```

### Phase 3: GitHub API Reality-Based Posting
**MANDATORY**: Post responses using GitHub's actual threading capabilities per comment type

```
STEP 1: Post Issue Comment Replies (REFERENCE-BASED - No Threading)
  - REALITY: GitHub Issue Comments DO NOT support in_reply_to_id threading
  - Use: gh api "repos/OWNER/REPO/issues/PR/comments" --method POST
  - Include: Reference to original comment in body text (e.g., "Re: Comment #12345")
  - Verify: Response posted successfully with reference notation

STEP 2: Post PR Comment Replies (THREADED - Full Threading Support)
  - REALITY: GitHub PR Comments fully support in_reply_to_id threading
  - Use: gh api "repos/OWNER/REPO/pulls/PR/comments" --method POST
  - Include: --field in_reply_to_id=PARENT_ID for proper threading
  - Verify: Response contains proper threading confirmation (in_reply_to_id populated)

STEP 3: Post Review Comment Replies (REVIEW-THREADED - Review Association)
  - REALITY: GitHub Review Comments thread via review association
  - Use: gh api "repos/OWNER/REPO/pulls/PR/reviews/REVIEW/comments" --method POST
  - Include: Review-specific parameters for association
  - Verify: Response properly associated with parent review

STEP 4: REALITY-BASED THREADING VERIFICATION per comment type
  - Issue Comments: Verify reference notation in body text (not threading)
  - PR Comments: Verify in_reply_to_id populated correctly
  - Review Comments: Verify review association successful
  - Capture success rate per comment type based on actual capabilities
CHECKPOINT: All responses posted using correct GitHub API patterns per type
```

### Phase 4: Real-Time Threading Verification
**MANDATORY**: Verify threading success immediately after each post

```
STEP 1: For each posted comment, verify threading via API
  - Check in_reply_to_id field is populated correctly
  - Verify parent-child relationship in GitHub data
  - Confirm proper URL format (#discussion_r vs #issuecomment-)

STEP 2: Generate threading success metrics per type
  - Issue Comment Threading: X/Y successful (Z% rate)
  - PR Comment Threading: X/Y successful (Z% rate)
  - Review Comment Threading: X/Y successful (Z% rate)

STEP 3: MANDATORY: Fix threading failures immediately
  - If threading failed: retry with corrected API endpoint
  - If retry failed: log specific failure reason and continue
  - Track threading failure patterns for debugging

CHECKPOINT: 100% threading verification complete per comment type
```

### Phase 5: Final Coverage Verification
**MANDATORY**: Run commentcheck with exit code verification

```
STEP 1: Execute commentcheck command with threading analysis
STEP 2: Check exit code (0 = success, 1 = failure)
STEP 3: VERIFY: 100% comment coverage AND 100% threading success
CHECKPOINT: commentcheck returns exit code 0 with threading verification
```

## TYPE-AWARE IMPLEMENTATION RULES

### Comment Type Separation (MANDATORY)
- **Issue Comments**: ONLY use GitHub issues API endpoint
- **PR Comments**: ONLY use GitHub pulls API endpoint
- **Review Comments**: ONLY use GitHub reviews API endpoint
- **NO CROSS-CONTAMINATION**: Never post comment type to wrong endpoint

### Real-Time Threading Verification (MANDATORY)
- **Immediate Check**: Verify threading after EACH individual post
- **Retry Logic**: Failed threading triggers immediate retry with correct parameters
- **Success Tracking**: Maintain threading success rate per comment type
- **Failure Logging**: Record specific API endpoint and parameter combinations that fail

### Type-Specific Error Recovery (MANDATORY)
- **Issue Comment Failure**: Retry with issues API + in_reply_to_id parameter
- **PR Comment Failure**: Retry with pulls API + in_reply_to_id parameter
- **Review Comment Failure**: Retry with reviews API + review-specific threading
- **Authentication Failure**: Escalate with specific API scope requirements per type
- **Rate Limiting**: Exponential backoff per API endpoint type

### Mandatory Verification Gates (ENHANCED)
- **Gate 1**: Comment data exists and properly type-segmented
- **Gate 2**: Response count matches comment count per type
- **Gate 3**: GitHub posting confirms with comment IDs per type
- **Gate 4**: Threading verification successful per comment type
- **Gate 5**: commentcheck shows 0 unresponded AND 100% threading

### Enhanced Fail-Fast Protocol
- **Type-specific failure**: Continue with other types, log specific failure
- **Complete type failure**: Stop workflow if any comment type completely fails
- **Threading failure**: Retry mechanism before declaring failure
- **No bypassing**: Cannot skip threading verification gates

## TYPE-AWARE SUCCESS CRITERIA

**ONLY declare success when**:
- ✅ All comments collected and type-segmented correctly
- ✅ All responses generated per comment type
- ✅ All responses posted to correct API endpoints with confirmed IDs
- ✅ All threading verification successful per comment type (100% rate)
- ✅ commentcheck returns exit code 0 with threading analysis
- ✅ No type-aware verification gates bypassed

## TYPE-SPECIFIC FAILURE CONDITIONS

**Immediate failure if**:
- ❌ Comment type segmentation fails (cannot classify comments)
- ❌ Wrong API endpoint used for comment type (cross-contamination)
- ❌ Threading verification shows <100% success after retries
- ❌ commentcheck shows unresponded comments OR threading failures
- ❌ Type-specific retry mechanisms fail after 3 attempts

## GITHUB API IMPLEMENTATION PATTERNS

### Issue Comment Reference-Based Response (GITHUB REALITY)
```bash
# REALITY: GitHub Issue Comments DO NOT support threading
# Use reference-based approach instead
gh api "repos/OWNER/REPO/issues/PR_NUMBER/comments" \
  --method POST \
  --field body="Re: Comment #$PARENT_COMMENT_ID

✅ DONE: [Response to original comment]

[Detailed response content here]

Original comment reference: https://github.com/OWNER/REPO/pull/PR_NUMBER#issuecomment-$PARENT_COMMENT_ID

🤖 Generated with [Claude Code](https://claude.ai/code)"

# Verify reference-based response success
REPLY_DATA=$(gh api "repos/OWNER/REPO/issues/PR_NUMBER/comments" | jq ".[] | select(.id == $NEW_COMMENT_ID)")
REFERENCE_SUCCESS=$(echo "$REPLY_DATA" | jq -r '.body' | grep -q "Re: Comment #$PARENT_COMMENT_ID" && echo "true" || echo "false")
if [ "$REFERENCE_SUCCESS" = "true" ]; then
  echo "✅ Issue comment reference SUCCESS"
else
  echo "❌ Issue comment reference FAILED - retry required"
fi
```

### PR Comment Threading (CORRECTED)
```bash
# Post threaded reply to PR comment
gh api "repos/OWNER/REPO/pulls/PR_NUMBER/comments" \
  --method POST \
  --field body="Response text" \
  --field in_reply_to_id=PARENT_COMMENT_ID

# Immediately verify threading success
REPLY_DATA=$(gh api "repos/OWNER/REPO/pulls/PR_NUMBER/comments" | jq ".[] | select(.id == $NEW_COMMENT_ID)")
THREADING_SUCCESS=$(echo "$REPLY_DATA" | jq -r '.in_reply_to_id')
if [ "$THREADING_SUCCESS" = "$PARENT_COMMENT_ID" ]; then
  echo "✅ PR comment threading SUCCESS"
else
  echo "❌ PR comment threading FAILED - retry required"
fi
```

### Type-Aware Processing Loop (MANDATORY PATTERN)
```bash
# CORRECT: Process each comment type separately
echo "=== PROCESSING ISSUE COMMENTS ==="
for comment_id in $(get_issue_comment_ids); do
  post_issue_reply "$comment_id"
  verify_issue_threading "$comment_id"
done

echo "=== PROCESSING PR COMMENTS ==="
for comment_id in $(get_pr_comment_ids); do
  post_pr_reply "$comment_id"
  verify_pr_threading "$comment_id"
done

echo "=== PROCESSING REVIEW COMMENTS ==="
for comment_id in $(get_review_comment_ids); do
  post_review_reply "$comment_id"
  verify_review_threading "$comment_id"
done
```

**Target Time**: 3-5 minutes with type-aware threading verification.
