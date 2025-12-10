---
description: /copilot-lite - Streamlined PR Processing
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🎯 MISSION

Atomic single-pass PR comment processor with ground truth verification.

**SCOPE**: ONLY fixes GitHub PR comments. Does NOT:
- ❌ Fix merge conflicts (use `/fixpr` separately)
- ❌ Fix failing tests (handle separately)
- ❌ Handle CI failures (not in scope)

**Key Principle**: Ground truth over inference - try the fix, report what actually happened.

**Architecture**:
- **Claude (LLM)**: Analyzes comments, attempts fixes, generates truthful responses
- **Python**: ONLY manages state and API calls (NO hardcoded responses)
- **Threading**: Proper GitHub threading via `in_reply_to` parameter

## 🚨 EXECUTION WORKFLOW

### Phase 1: Environment Setup

**Action Steps:**
```bash
# Get PR context
BRANCH_NAME=$(git branch --show-current)
SAFE_BRANCH=$(echo "$BRANCH_NAME" | tr -cd '[:alnum:]._-')
WORK_DIR="/tmp/$SAFE_BRANCH"
mkdir -p "$WORK_DIR"

# Detect PR number
PR_NUMBER=$(gh pr view --json number -q '.number' 2>/dev/null || echo "")
if [ -z "$PR_NUMBER" ]; then
    echo "❌ ERROR: No PR found for current branch"
    exit 1
fi

REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
echo "🎯 Processing PR #$PR_NUMBER on $REPO (branch: $BRANCH_NAME)"
```

### Phase 2: Fetch ALL Comments

**Action Steps:**
Execute `/commentfetch` OR run directly:
```bash
# Fetch all comments from all sources (human + bot)
python3 -m .claude.commands._copilot_modules.commentfetch "$PR_NUMBER" 2>/dev/null || \
    gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --paginate > "$WORK_DIR/inline_comments.json" && \
    gh api "repos/$REPO/issues/$PR_NUMBER/comments" --paginate > "$WORK_DIR/issue_comments.json"

echo "📥 Comments fetched to $WORK_DIR/comments.json"
```

**Important**: This fetches ALL comments including:
- Human reviewer comments
- Bot comments (Codex, GitHub bots, etc.)
- Inline review comments
- General PR conversation comments

### Phase 3: Atomic Comment Processing (CORE - LLM RESPONSIBILITY)

**🚨 CRITICAL: Claude (LLM) MUST process each comment atomically:**

For EACH comment in `/tmp/{branch}/comments.json` (including bot comments):

1. **READ** the comment body and understand what is being requested
   - **Bot comments** requesting code changes should be treated like human comments
   - **Bot status updates** (e.g., "CI passed", "Merge conflict detected") should be SKIPPED

2. **CATEGORIZE** the comment request:
   - `CRITICAL`: Security vulnerabilities, production blockers, data corruption in PR code
   - `IMPORTANT`: Performance issues, logic errors, missing validation in PR code
   - `ROUTINE`: Code style, documentation, optional refactoring suggestions
   - **SKIP**: Bot status updates, merge conflicts, test failures, or CI issues (not in scope)
     - Examples to SKIP: "Merge conflict detected", "Tests failed", "CI check pending"
     - Examples to PROCESS: "@codex please fix this bug", "Bot: This function has a security issue"

3. **ATTEMPT** the fix (if applicable):
   - Read the affected file(s)
   - Make the code change using Edit/MultiEdit tools
   - Verify syntax is correct
   - Commit the change with descriptive message
   - **NOTE**: Do NOT fix tests or merge conflicts - only address the specific comment request
     - If the comment is about merge conflicts, failing tests, or CI status, categorize it as **SKIP** in Step 2 and respond with a `SKIPPED` entry (no ATTEMPT changes)

4. **GENERATE** a truthful response based on ACTUAL outcome:

**Response Types**:
- **FIXED**: Successfully implemented the change
  - MUST include: commit hash, files modified, verification status
- **NOT DONE**: Could not implement (with REAL reason from actual attempt)
  - MUST include: specific error or constraint that prevented implementation
- **ACKNOWLEDGED**: Style suggestion noted for future consideration
- **ALREADY IMPLEMENTED**: Code already does this (MUST show evidence)
  - MUST include: file path, line number, code snippet proving implementation
- **SKIPPED**: Comment is about merge conflicts, test failures, CI issues, or bot status updates (out of scope)
  - MUST include: brief note directing to appropriate command (/fixpr for merge conflicts)
  - Examples: Bot status updates like "Merge conflict detected", "CI pending"
  - **NOTE**: Bot comments requesting actual code changes should NOT be skipped - treat them like human comments

### Phase 4: Build responses.json

**🚨 Claude MUST write responses to `/tmp/{branch}/responses.json`:**

```json
{
  "response_protocol": "ACTION_ACCOUNTABILITY",
  "responses": [
    {
      "comment_id": "2357534669",
      "category": "CRITICAL",
      "response": "FIXED",
      "action_taken": "Removed strict=True from zip() for Python 3.8 compatibility",
      "files_modified": ["testing_integration/test_file.py:171"],
      "commit": "946958873",
      "verification": "✅ Tests pass, Python 3.8+ compatible",
      "reply_text": "[AI responder] ✅ **FIXED**\n\n**Category**: CRITICAL\n**Action**: Removed strict=True from zip() for Python 3.8 compatibility\n**Files**: testing_integration/test_file.py:171\n**Commit**: 946958873\n**Verification**: ✅ Tests pass",
      "in_reply_to": null
    },
    {
      "comment_id": "2357534670",
      "category": "BLOCKING",
      "response": "NOT_DONE",
      "reason": "cast() is required for mypy type inference - removing it causes 'object has no attribute append' error",
      "reply_text": "[AI responder] ❌ **NOT DONE**\n\n**Category**: BLOCKING\n**Reason**: cast() is required for mypy type inference. Attempted removal, but mypy fails with: 'object has no attribute append'\n**Evidence**: Ran `mypy src/file.py` - exit code 1",
      "in_reply_to": null
    },
    {
      "comment_id": "2357534671",
      "category": "ROUTINE",
      "response": "ACKNOWLEDGED",
      "explanation": "Good suggestion for code clarity, will apply in next refactoring cycle",
      "reply_text": "[AI responder] 📝 **ACKNOWLEDGED**\n\n**Category**: ROUTINE\n**Note**: Good suggestion for code clarity. Noting for future refactoring.",
      "in_reply_to": null
    },
    {
      "comment_id": "2357534672",
      "category": "IMPORTANT",
      "response": "ALREADY_IMPLEMENTED",
      "evidence": {
        "file": "src/utils.py",
        "line": 45,
        "code": "branch_name = branch_name.replace('/', '_').replace('\\\\', '_')"
      },
      "reply_text": "[AI responder] ✅ **ALREADY IMPLEMENTED**\n\n**Category**: IMPORTANT\n**Evidence**: Branch sanitization exists at src/utils.py:45\n```python\nbranch_name = branch_name.replace('/', '_').replace('\\\\', '_')\n```\n**Verified**: Actual code shows path-safe character replacement",
      "in_reply_to": null
    },
    {
      "comment_id": "2357534673",
      "comment_author": "codex-bot",
      "category": "IMPORTANT",
      "response": "FIXED",
      "action_taken": "Added null check before accessing user.name property",
      "files_modified": ["src/auth.py:45"],
      "commit": "abc123def",
      "verification": "✅ Syntax valid, null pointer exception prevented",
      "reply_text": "[AI responder] ✅ **FIXED**\n\n**Category**: IMPORTANT\n**Action**: Added null check before accessing user.name property (from @codex-bot comment)\n**Files**: src/auth.py:45\n**Commit**: abc123def\n**Verification**: ✅ Syntax valid, null pointer exception prevented",
      "in_reply_to": null
    },
    {
      "comment_id": "2357534674",
      "comment_author": "github-actions[bot]",
      "category": "SKIP",
      "response": "SKIPPED",
      "reason": "Bot status update about merge conflicts - use /fixpr command",
      "reply_text": "[AI responder] ⏭️ **SKIPPED**\n\n**Reason**: This is a bot status update about merge conflicts, which is out of scope for /copilot-lite.\n**Action**: Please run `/fixpr` to resolve merge conflicts separately.",
      "in_reply_to": null
    }
  ]
}
```

### Phase 5: Post Responses with Threading

**Action Steps:**
```bash
# Get repo info
OWNER=$(gh repo view --json owner -q '.owner.login')
REPO_NAME=$(gh repo view --json name -q '.name')
PR_NUMBER=$(gh pr view --json number -q '.number')

# Post all responses with proper threading
python3 .claude/commands/commentreply.py "$OWNER" "$REPO_NAME" "$PR_NUMBER"
```

**Threading Contract**:
- `in_reply_to` field enables GitHub's native threading
- Review comments (inline): Uses `POST /repos/{owner}/{repo}/pulls/{pull}/comments` with `in_reply_to`
- Issue comments (general): Uses `POST /repos/{owner}/{repo}/issues/{pull}/comments` with reference link

### Phase 6: Verification

**Action Steps:**
Execute `/commentcheck` to verify 100% comment coverage:
```bash
/commentcheck
```

**Success Criteria**:
- ✅ Every comment has a response in responses.json
- ✅ Every response was successfully posted to GitHub
- ✅ All FIXED responses have valid commit hashes
- ✅ All NOT_DONE responses have real failure reasons

### Phase 7: Push & Summary

**Action Steps:**
```bash
# Push all committed fixes
git push origin HEAD

# Generate summary
echo "📊 COPILOT-LITE SUMMARY:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━"
jq -r '.responses | group_by(.response) | .[] | "\(.[0].response): \(length)"' "$WORK_DIR/responses.json"
```

## 🚨 CRITICAL RULES

### Rule 1: Ground Truth Verification
```python
# ❌ WRONG (inference without verification)
if comment.suggests("sanitize branch name"):
    response = "ALREADY IMPLEMENTED - .strip() handles this"
    # ^ FALSE! .strip() removes whitespace, NOT path separators

# ✅ RIGHT (actual code verification)
code = read_file("src/utils.py")
if ".replace('/', '_')" in code:
    response = f"ALREADY IMPLEMENTED - See src/utils.py:{line_number}"
    # Show actual code snippet as proof
else:
    # Not implemented - attempt to fix it
    result = attempt_fix(comment)
```

### Rule 2: Try Before Claiming NOT_DONE
```python
# ❌ WRONG (assumption without attempt)
return "NOT DONE: This would require significant refactoring"
# ^ Made up reason without trying

# ✅ RIGHT (real attempt with real outcome)
try:
    apply_fix()
    run_tests()
    commit()
    return f"FIXED: {commit_hash}"
except Exception as e:
    return f"NOT DONE: {str(e)}"
# ^ Actual reason from actual attempt
```

### Rule 3: No False Implementation Claims
```python
# ❌ WRONG (confusing similar operations)
# Comment: "Sanitize branch name for file system"
# Code has: result.stdout.strip()
response = "ALREADY IMPLEMENTED - branch is sanitized"
# ^ .strip() removes whitespace, NOT slashes!

# ✅ RIGHT (verify exact behavior)
# Look for: .replace('/', '_') or similar
# Only claim implemented if actual sanitization exists
```

### Rule 4: Every Comment Gets Response (Human + Bot)
- **FIXED**: Change was made and verified
- **NOT_DONE**: Attempted but failed (include real reason)
- **ACKNOWLEDGED**: Style suggestion, noted
- **ALREADY_IMPLEMENTED**: Code already does this (with evidence)
- **SKIPPED**: Bot status updates, merge conflicts, test failures, or CI (out of scope)

**Bot Comment Handling:**
- Bot comments requesting code changes → Process like human comments (FIXED/NOT_DONE/etc.)
- Bot status updates (CI, merge conflicts) → SKIPPED

**NO COMMENT LEFT BEHIND** - 100% response rate is mandatory (human + bot).

## 📊 Response Categories

| Response | When to Use | Required Fields |
|----------|-------------|-----------------|
| `FIXED` | Successfully implemented change (human or bot comment) | `action_taken`, `files_modified`, `commit`, `verification` |
| `NOT_DONE` | Attempted but couldn't implement (human or bot comment) | `reason` (from actual failure) |
| `ACKNOWLEDGED` | Style/non-blocking suggestion (human or bot comment) | `explanation` |
| `ALREADY_IMPLEMENTED` | Code already has this feature (human or bot comment) | `evidence` (file, line, code snippet) |
| `SKIPPED` | Bot status updates, merge conflicts, tests, or CI | `reason` (brief explanation + command to use) |

## 🔧 Integration with Existing Commands

This command composes with:
- `/commentfetch` - Fetches all PR comments
- `/commentreply` - Posts responses with proper threading
- `/commentcheck` - Verifies 100% coverage
- `/pushl` - For pushing changes

**NOT included** (handle separately):
- `/fixpr` - Use separately for merge conflict resolution
- Test fixing - Handle via separate test commands
- CI troubleshooting - Handle via separate debugging

## ✅ SUCCESS CRITERIA

### Accuracy Requirements (MANDATORY)
- [ ] No miscategorizations (ACKNOWLEDGED when should be FIXED)
- [ ] No false implementation claims
- [ ] Every "ALREADY IMPLEMENTED" includes code evidence
- [ ] Every "FIXED" includes commit hash and verification
- [ ] Every "NOT DONE" includes real failure reason from actual attempt
- [ ] Every "SKIPPED" correctly identifies out-of-scope comments (merge conflicts, tests, CI)

### Coverage Requirements (MANDATORY)
- [ ] 100% comment response rate (human + bot comments)
- [ ] All responses posted with proper threading
- [ ] No comments skipped without explicit reason

### Quality Requirements
- [ ] All FIXED changes pass tests
- [ ] All commit messages reference the comment being addressed
- [ ] Response text clearly explains what was done or why not

## 📝 Usage

```bash
# Run the command
/copilot-lite

# Or use alias
/copilotl
```

**What happens:**
1. Fetches ALL PR comments (human + bot)
2. For EACH comment: attempts fix → verifies → generates truthful response
3. Posts ALL responses with proper threading
4. Verifies 100% coverage
5. Pushes all committed fixes

**What this does NOT handle:**
- ❌ Merge conflicts (use `/fixpr`)
- ❌ Test failures (handle separately)
- ❌ CI issues (debug separately)

**Key Difference from /copilot:**
- `/copilot`: Multi-phase (Phase 0-3), can lose state between phases
- `/copilot-lite`: Single-pass atomic, each comment fully processed before moving to next
- `/copilot-lite`: ONLY fixes code comments, not merge conflicts or tests

## 🚨 Autonomous Operation

This command operates autonomously without user approval prompts for:
- ✅ Code analysis and fixes
- ✅ Response generation
- ✅ Comment posting
- ✅ Push operations

**EXCEPTION**: Merge operations ALWAYS require explicit user approval ("MERGE APPROVED").
