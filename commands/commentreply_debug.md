# Comment Coverage Debugging Protocol

**CRITICAL BUG PATTERN IDENTIFIED**: PR #1250 revealed systematic comment filtering bug where owner test comments were ignored.

## Coverage Verification Protocol

**MANDATORY BEFORE claiming complete coverage**:

1. **List ALL Comments with IDs**:
```bash
# Get complete comment inventory with IDs and authors
gh api repos/owner/repo/pulls/PR/comments --paginate | jq '.[] | {id, author: .user.login, body: .body[0:50], created_at}'
```

2. **Verify EVERY Comment ID Processed**:
```bash
# Cross-reference each comment ID against replies
for comment_id in $(gh api repos/owner/repo/pulls/PR/comments --paginate | jq -r '.[] | .id'); do
  echo "Checking coverage for comment #$comment_id..."
  # Verify this ID was processed/replied to
done
```

3. **Check for Author Bias**:
```bash
# Identify all unique comment authors
gh api repos/owner/repo/pulls/PR/comments --paginate | jq -r '.[] | .user.login' | sort | uniq -c
# EVERY author must have their comments processed
```

## Bug Pattern: Owner Comment Filtering

**DISCOVERED PATTERN**:
- ✅ Bot comments (CodeRabbit, Copilot): Always processed
- ❌ Owner test comments: **SYSTEMATICALLY IGNORED**
- ❌ Simple debugging comments: **FILTERED OUT**

**Examples of MISSED Comments**:
- Comment #2265148224: "see if commentreply catches this" (MISSED by copilot)
- Comment #2265160301: "reply to this" (MISSED by copilot)

**Root Cause**: Implicit filtering logic assumes:
- Owner comments don't need responses
- Simple/test comments aren't "actionable feedback"
- Only external reviewer comments require processing

## Anti-Filter Protocol

**MANDATORY**: Process ALL comments with these characteristics:
- ✅ **Author**: PR owner, external reviewers, bots - ALL treated equally
- ✅ **Content**: Technical, testing, debugging, simple - ALL get responses
- ✅ **Purpose**: Feedback, validation, debugging - ALL are valid
- ✅ **Length**: Long detailed reviews AND short test comments

## Verification Commands

```bash
# MANDATORY: Run before declaring coverage complete
echo "🔍 FINAL VERIFICATION: Comment coverage audit"

# 1. Count ALL comments
TOTAL_COMMENTS=$(gh api repos/owner/repo/pulls/PR/comments --paginate | jq '. | length')

# 2. Count comments by author  
echo "📊 Comments by author:"
gh api repos/owner/repo/pulls/PR/comments --paginate | jq -r '.[] | .user.login' | sort | uniq -c

# 3. List any unprocessed comment IDs
echo "⚠️  Any unprocessed comments:"
# Implementation needed: Compare against reply records

# 4. Verify NO bias patterns
echo "🚨 Checking for filtering bias..."
# Implementation needed: Ensure owner comments aren't skipped
```

**ZERO TOLERANCE**: ANY missed comment = FAILED coverage, regardless of technical complexity