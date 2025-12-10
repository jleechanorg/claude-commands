---
description: /copilot-lite - Streamlined PR Processing
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**

**Available tools/capabilities:** Shell commands (`gh`, `git`, `python3`), local file reads/writes, `commentfetch/commentreply/commentcheck` modules, and git commit/push. No external plugins beyond these.

## 🎯 MISSION

Atomic single-pass PR comment processor with ground truth verification.

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
# Fetch all comments from all sources
python3 -m .claude.commands._copilot_modules.commentfetch "$PR_NUMBER" 2>/dev/null || \
    gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --paginate > "$WORK_DIR/inline_comments.json" && \
    gh api "repos/$REPO/issues/$PR_NUMBER/comments" --paginate > "$WORK_DIR/issue_comments.json"

echo "📥 Comments fetched to $WORK_DIR/comments.json"
```

### Phase 3: Atomic Comment Processing (CORE - LLM RESPONSIBILITY)

**🚨 CRITICAL: Claude (LLM) MUST process each comment atomically:**

For EACH comment in `/tmp/{branch}/comments.json`:

1. **READ** the comment body and understand what is being requested
2. **CATEGORIZE** the request:
   - `CRITICAL`: Security vulnerabilities, production blockers, data corruption
   - `BLOCKING`: CI failures, build failures, breaking changes
   - `IMPORTANT`: Performance issues, logic errors, missing validation
   - `ROUTINE`: Code style, documentation, optional refactoring

3. **ATTEMPT** the fix (if applicable):
   - Read affected files via shell (`cat`, `sed`) or repo-aware tools
   - Edit code using the built-in `Edit/MultiEdit` capabilities of Claude Code (no external editor required)
   - Run relevant tests with project scripts (e.g., `./run_tests_with_coverage.sh`, `pytest path/to/test.py`)
   - Stage and commit with `git` when tests pass; revert or leave a NOT DONE reply if they fail

4. **GENERATE** a truthful response based on ACTUAL outcome:

**Response Types**:
- **FIXED**: Successfully implemented the change
  - MUST include: commit hash, files modified, verification status
- **NOT DONE**: Could not implement (with REAL reason from actual attempt)
  - MUST include: specific error or constraint that prevented implementation
- **ACKNOWLEDGED**: Style suggestion noted for future consideration
- **ALREADY IMPLEMENTED**: Code already does this (MUST show evidence)
  - MUST include: file path, line number, code snippet proving implementation

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

### Rule 4: Every Comment Gets Response
- **FIXED**: Change was made and verified
- **NOT_DONE**: Attempted but failed (include real reason)
- **ACKNOWLEDGED**: Style suggestion, noted
- **ALREADY_IMPLEMENTED**: Code already does this (with evidence)

**NO COMMENT LEFT BEHIND** - 100% response rate is mandatory.

## 📊 Response Categories

| Response | When to Use | Required Fields |
|----------|-------------|-----------------|
| `FIXED` | Successfully implemented change | `action_taken`, `files_modified`, `commit`, `verification` |
| `NOT_DONE` | Attempted but couldn't implement | `reason` (from actual failure) |
| `ACKNOWLEDGED` | Style/non-blocking suggestion | `explanation` |
| `ALREADY_IMPLEMENTED` | Code already has this feature | `evidence` (file, line, code snippet) |

## 🔧 Integration with Existing Commands

This command composes with:
- `/commentfetch` - Fetches all PR comments
- `/commentreply` - Posts responses with proper threading
- `/commentcheck` - Verifies 100% coverage
- `/fixpr` - For complex merge conflict resolution
- `/pushl` - For pushing changes

## ✅ SUCCESS CRITERIA

### Accuracy Requirements (MANDATORY)
- [ ] No miscategorizations (ACKNOWLEDGED when should be FIXED)
- [ ] No false implementation claims
- [ ] Every "ALREADY IMPLEMENTED" includes code evidence
- [ ] Every "FIXED" includes commit hash and verification
- [ ] Every "NOT DONE" includes real failure reason from actual attempt

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

**Key Difference from /copilot:**
- `/copilot`: Multi-phase (Phase 0-3), can lose state between phases
- `/copilot-lite`: Single-pass atomic, each comment fully processed before moving to next

## 🚨 Autonomous Operation

This command operates autonomously without user approval prompts for:
- ✅ Code analysis and fixes
- ✅ Response generation
- ✅ Comment posting
- ✅ Push operations

**EXCEPTION**: Merge operations ALWAYS require explicit user approval ("MERGE APPROVED").
