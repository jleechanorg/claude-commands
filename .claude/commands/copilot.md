# /copilot - Fast PR Processing

## 🎯 Purpose
Ultra-fast PR processing using hybrid orchestration: direct comment handling + copilot-fixpr agent for file operations.

## ⚡ Core Workflow

### Initial Setup
```bash
# Get comprehensive PR status and initialize timing
/gstatus
COPILOT_START_TIME=$(date +%s)
```

### Phase 1: Analysis & Agent Launch

**Direct Comment Processing:**
```bash
# Fetch and analyze PR comments
/commentfetch

# Analyze actionable issues by priority:
# 1. Security vulnerabilities
# 2. Runtime errors
# 3. Test failures
# 4. Style/quality issues
```

**Parallel copilot-fixpr Agent:**
- Launch agent for file modifications with File Justification Protocol
- Agent analyzes security vulnerabilities and implements fixes
- Agent uses Edit/MultiEdit tools for actual code changes
- Agent must verify target files exist before modifications

**🚨 PHASE 1 VERIFICATION (MANDATORY):**
```bash
# Hard stop: Verify agent made actual changes
CHANGES=$(git diff --name-only | wc -l)
[ "$CHANGES" -eq 0 ] && echo "🚨 AGENT FAILURE: No files modified" && exit 1
echo "✅ Verified: $CHANGES files modified"
git diff --stat
```

### Phase 2: Response Generation

**Integration & Communication:**
- Collect agent results: technical analysis, file fixes, security implementations
- Generate responses based on actual implemented changes
- Execute /commentreply with implementation details for guaranteed GitHub posting

**🚨 PHASE 2 VERIFICATION (MANDATORY):**
```bash
# Verify both changes and comment processing completed
[ -z "$(git diff --name-only)" ] && echo "🚨 NO MODIFICATIONS" && exit 1
[ ! -f "/tmp/copilot_comments_fetched" ] && /commentfetch && touch /tmp/copilot_comments_fetched
```

### Phase 3: Verification & Push

**🚨 MANDATORY VERIFICATION PROTOCOL:**
```bash
# Show evidence of changes
echo "📊 COPILOT EXECUTION EVIDENCE:"
echo "🔧 FILES MODIFIED:"
git diff --name-only | sed 's/^/  - /'
echo "📈 CHANGE SUMMARY:"
git diff --stat

# Push changes to PR
/pushl || { echo "🚨 PUSH FAILED: PR not updated"; exit 1; }
```

**Coverage Tracking:**
```bash
# Coverage verification (silent unless incomplete)
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)"
PR_NUMBER="$(gh pr view --json number -q .number 2>/dev/null)"

# Input validation
[[ ! "$REPO" =~ ^[a-zA-Z0-9._/-]+$ ]] || [[ ! "$PR_NUMBER" =~ ^[0-9]+$ ]] && echo "🚨 INVALID REPO/PR" && exit 1

# Calculate coverage
REV_JSON="$(gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --paginate 2>/dev/null | jq -s 'add // []' 2>/dev/null)"
REV_ORIGINAL="$(jq -r '[.[] | select(.in_reply_to_id == null)] | length' <<<"$REV_JSON")"
UNIQUE_REPLIED_ORIGINALS="$(jq -r '[.[] | select(.in_reply_to_id != null) | .in_reply_to_id] | unique | length' <<<"$REV_JSON")"

ORIGINAL_COMMENTS="${REV_ORIGINAL:-0}"
REPLIED_ORIGINALS="${UNIQUE_REPLIED_ORIGINALS:-0}"

[[ ! "$ORIGINAL_COMMENTS" =~ ^[0-9]+$ ]] && ORIGINAL_COMMENTS=0
[[ ! "$REPLIED_ORIGINALS" =~ ^[0-9]+$ ]] && REPLIED_ORIGINALS=0

if [ "${ORIGINAL_COMMENTS:-0}" -gt 0 ]; then
  COVERAGE_PERCENT=$(( REPLIED_ORIGINALS * 100 / ORIGINAL_COMMENTS ))
  if [ "$COVERAGE_PERCENT" -lt 100 ]; then
    missing=$(( ORIGINAL_COMMENTS - REPLIED_ORIGINALS ))
    [ "$missing" -lt 0 ] && missing=0
    echo "🚨 WARNING: INCOMPLETE COVERAGE: ${COVERAGE_PERCENT}% (missing: ${missing})"
  fi
fi
```

**Final Timing:**
```bash
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
[ "${COPILOT_DURATION:-0}" -gt 180 ] && echo "⚠️ PERFORMANCE: ${COPILOT_DURATION}s exceeded 3m target"

/guidelines
```

## 🚨 Agent Boundaries

**copilot-fixpr Agent:**
- File operations only (Edit/MultiEdit, security fixes)
- Must verify file existence before modifications
- Must run `git diff --stat` before reporting success

**Direct Orchestrator:**
- Comment processing (/commentfetch, /commentreply)
- GitHub operations and workflow coordination
- Verification checkpoints and evidence collection

## 🎯 Success Criteria

**BOTH REQUIRED:**
1. **Implementation**: All actionable issues have actual file changes
2. **Communication**: 100% comment response rate

**FAILURE CONDITIONS:**
- No file changes after agent execution
- Missing comment responses
- Push failures
- Skipped verification checkpoints

## 🚨 Critical Anti-Patterns
- ❌ Agent reports success but `git diff` shows no changes
- ❌ Agent targets non-existent files (app.py vs main.py)
- ❌ Skipping /commentfetch or /commentreply workflows
- ❌ Declaring completion without /pushl execution
- ❌ Accepting "implemented" without git evidence
