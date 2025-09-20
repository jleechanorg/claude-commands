# /copilot-expanded - Complete Self-Contained PR Analysis & Enhancement

## 🚨 Purpose
Comprehensive PR processing with integrated comment analysis, code fixes, security review, and quality enhancement. A complete workflow that integrates with existing project protocols and tools for seamless PR enhancement.

## ⚡ Core Workflow - Self-Contained Implementation

### Phase 1: Analysis & Assessment
**Initial Assessment:** Gather branch status, commit history, merge conflicts, and GitHub comments using git/gh CLI with error handling:
```bash
# Initialize with error checking
COPILOT_START_TIME=$(date +%s)
BRANCH_NAME=$(git branch --show-current) || { echo "❌ CRITICAL: Not in git repository"; exit 1; }
PR_NUMBER=$(gh pr view --json number --jq '.number' 2>/dev/null) || { echo "❌ CRITICAL: No PR found for branch $BRANCH_NAME"; exit 1; }

# Create working directory with cleanup on failure
WORK_DIR="/tmp/$BRANCH_NAME"
mkdir -p "$WORK_DIR" || { echo "❌ CRITICAL: Cannot create work directory"; exit 1; }
trap 'rm -rf "$WORK_DIR"' EXIT
```
Parse and categorize feedback using keyword-based priority classification:
- **Security**: Keywords 'vulnerability', 'injection', 'auth', 'XSS', 'SQL', 'CSRF', 'security'
- **Runtime errors**: Keywords 'error', 'exception', 'crash', 'timeout', 'hang', 'fail'
- **Test failures**: Keywords 'test', 'failing', 'assertion', 'coverage', 'CI', 'build'
- **Quality**: Keywords 'refactor', 'clean', 'improve', 'optimize', 'pattern'
- **Style**: Keywords 'format', 'lint', 'style', 'spacing', 'naming'
Use configurable comment processing with smart filtering algorithm:
  - **Actionable detection**: Comments containing question marks, imperative verbs ('fix', 'change', 'add'), or action keywords
  - **Priority scoring**: Security keywords (+3), runtime errors (+2), test failures (+2), quality (+1), style (+0)
  - **Recency weighting**: Comments from last 24 hours (×2 weight), last 7 days (×1.5 weight), older (×1 weight)
  - **Author filtering**: Bot comments (CodeRabbit, Copilot) always processed, human reviewers prioritized over contributors

**Security & Quality Scan:** Identify vulnerabilities with structured data collection:
```bash
# File structure for data management
COMMENTS_FILE="$WORK_DIR/comments.json"
RESPONSES_FILE="$WORK_DIR/responses.json"
ANALYSIS_FILE="$WORK_DIR/analysis.json"
OPERATIONS_LOG="$WORK_DIR/operations.log"

# Data flow: Fetch → Analyze → Process → Respond
echo "📊 Setting up data pipeline"
log_operation "Initializing data files"

# Initialize structured data files
echo '{"comments":[], "metadata":{"total":0, "processed":0}}' > "$COMMENTS_FILE"
echo '{"responses":[], "metadata":{"posted":0, "failed":0}}' > "$RESPONSES_FILE"
echo '{"vulnerabilities":[], "performance":[], "quality":[]}' > "$ANALYSIS_FILE"

# Data validation
validate_data_files() {
    for file in "$COMMENTS_FILE" "$RESPONSES_FILE" "$ANALYSIS_FILE"; do
        if ! jq empty "$file" 2>/dev/null; then
            echo "❌ CRITICAL: Invalid JSON in $file"
            exit 1
        fi
    done
    log_operation "Data files validated"
}
```
Identify vulnerabilities (injection, auth), performance bottlenecks, code quality issues, test coverage gaps, and systematic improvement opportunities.

### Phase 2: Implementation & Fixes
**File Modification Strategy:** Apply File Justification Protocol with error recovery:
```bash
# File modification with rollback capability
cp .claude/commands/copilot-expanded.md .claude/commands/copilot-expanded.md.backup || {
    echo "❌ WARNING: Cannot create backup"
}

# Apply changes with validation
if ! python3 -c "import sys; sys.exit(0)"; then
    echo "❌ CRITICAL: Python not available for file operations"
    exit 1
fi

# Restore on failure
trap 'mv .claude/commands/copilot-expanded.md.backup .claude/commands/copilot-expanded.md 2>/dev/null' ERR
```
Use integration-first approach - modify existing files over creating new ones. Implement security fixes with validation, address runtime errors with robust handling, fix test failures.

**Code Enhancement:** Remove unused imports/dead code with file tracking:
```bash
# Track file modifications with backup and restore capability
BACKUP_DIR="$WORK_DIR/backups"
mkdir -p "$BACKUP_DIR"

# Function to safely modify files
safe_file_edit() {
    local file="$1"
    local operation="$2"

    # Create backup
    cp "$file" "$BACKUP_DIR/$(basename "$file").$(date +%s).bak" || {
        echo "❌ Cannot backup $file"
        return 1
    }

    # Apply modification with Edit/MultiEdit tools
    log_operation "Modifying $file: $operation"

    # Validate changes
    if ! python3 -m py_compile "$file" 2>/dev/null && [[ "$file" == *.py ]]; then
        echo "⚠️  Syntax error in $file, restoring backup"
        cp "$BACKUP_DIR/$(basename "$file")."*.bak "$file" 2>/dev/null || true
        return 1
    fi

    log_operation "Successfully modified $file"
    return 0
}
```
Implement error handling patterns, add type hints/documentation, optimize performance sections, ensure consistent style using Edit/MultiEdit tools with semantic search for context.

### Phase 3: GitHub Integration & Response
**Response Generation:** Create detailed technical responses to each comment explaining fixes and solutions:
```bash
# GitHub API Integration with authentication and rate limiting
GH_API_BASE="https://api.github.com"
REPO_OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO_NAME=$(gh repo view --json name --jq '.name')

# Fetch comments with error handling and rate limiting
fetch_pr_comments() {
    echo "🔄 Fetching PR comments via GitHub API"
    local pr_number="$1"

    # Check rate limit before making requests
    local rate_remaining=$(gh api rate_limit --jq '.rate.remaining')
    if [ "$rate_remaining" -lt 10 ]; then
        echo "⚠️  WARNING: GitHub API rate limit low ($rate_remaining remaining)"
        local reset_time=$(gh api rate_limit --jq '.rate.reset')
        echo "Rate limit resets at: $(date -d @$reset_time)"
        read -p "Continue anyway? (y/N): " confirm
        [ "$confirm" = "y" ] || exit 1
    fi

    # Fetch comments using GitHub CLI with structured output
    gh pr view "$pr_number" --json comments,reviews > "$COMMENTS_FILE" || {
        echo "❌ CRITICAL: Failed to fetch PR comments"
        exit 1
    }

    # Process and categorize comments
    jq -r '.comments[] | select(.body | length > 0) | {id: .id, body: .body, author: .author.login, created_at: .createdAt}' "$COMMENTS_FILE" > "$WORK_DIR/processed_comments.json"

    log_operation "Fetched $(jq '.comments | length' "$COMMENTS_FILE") comments"
}

# Generate and post responses with API integration
generate_and_post_responses() {
    echo "📝 Processing comments for responses"

    jq -r '.[] | @base64' "$WORK_DIR/processed_comments.json" | while read -r comment_data; do
        comment=$(echo "$comment_data" | base64 --decode)
        comment_id=$(echo "$comment" | jq -r '.id')
        comment_body=$(echo "$comment" | jq -r '.body')
        author=$(echo "$comment" | jq -r '.author')

        echo "📝 Processing comment $comment_id from $author"

        # Generate response based on comment content
        response_body="## Response to Comment $comment_id

Thank you @$author for your feedback.

$(generate_technical_response "$comment_body")

---
🤖 Generated with [Claude Code](https://claude.ai/code)"

        # Post response using GitHub CLI
        if echo "$response_body" | gh pr comment "$PR_NUMBER" --body-file -; then
            echo "✅ Posted response to comment $comment_id"
            log_operation "Posted response to comment $comment_id"
        else
            echo "❌ Failed to post response to comment $comment_id"
            log_operation "FAILED: Response to comment $comment_id"
        fi

        # Rate limiting: sleep between requests
        sleep 1
    done
}
```

**GitHub Operations:** Post structured replies and update PR status:
```bash
# GitHub operations with comprehensive error handling
update_pr_metadata() {
    echo "🔄 Updating PR metadata and status"

    # Update PR description with change summary
    local change_summary="## 🤖 Copilot-Expanded Processing Summary

**Processing Date**: $(date)
**Files Modified**: $(git diff --name-only | wc -l)
**Comments Processed**: $(jq length "$WORK_DIR/processed_comments.json")
**Response Rate**: $(calculate_response_rate)%

**Changes Made**:
$(git diff --stat)

---
*Processed by copilot-expanded command*"

    # Get current PR body and append summary
    local current_body=$(gh pr view "$PR_NUMBER" --json body --jq '.body')
    local updated_body="$current_body

$change_summary"

    # Update PR with new description
    if echo "$updated_body" | gh pr edit "$PR_NUMBER" --body-file -; then
        echo "✅ Updated PR description"
        log_operation "Updated PR description"
    else
        echo "⚠️  WARNING: Failed to update PR description"
    fi

    # Add labels to categorize the processing
    gh pr edit "$PR_NUMBER" --add-label "copilot-enhanced" --add-label "auto-processed" || {
        echo "⚠️  WARNING: Failed to add labels"
    }
}

# Verify GitHub operations and final status
verify_github_status() {
    echo "🔍 Verifying GitHub operations"

    # Check PR status after all operations
    local pr_status=$(gh pr view "$PR_NUMBER" --json state,mergeable --jq '{state: .state, mergeable: .mergeable}')
    echo "PR Status: $pr_status"

    # Run test suites and check CI status
    if ./run_tests.sh > "$WORK_DIR/final_test_results.log" 2>&1; then
        echo "✅ All tests passing after processing"
        log_operation "Final tests passed"
    else
        echo "❌ WARNING: Tests failing after processing"
        log_operation "Final tests failed"
    fi

    # Wait for CI checks and report status
    echo "🕰️ Waiting for CI checks..."
    if gh pr checks "$PR_NUMBER" --wait --interval 30; then
        echo "✅ All CI checks completed"
    else
        echo "⚠️  WARNING: Some CI checks failed"
    fi
}
```

### Phase 4: Documentation & Validation
**Evidence Collection:** Generate comprehensive change summary with concrete metrics:
```bash
# Collect evidence and metrics
COPILOT_END_TIME=$(date +%s)
DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
echo "📊 COPILOT EXECUTION EVIDENCE:"
echo "⏱️ Execution time: ${DURATION}s"
echo "🔧 Files modified: $(git diff --name-only | wc -l)"
echo "📈 Change summary: $(git diff --stat)"
echo "📝 Comments processed: $(jq '.metadata.unresponded_count' "$COMMENTS_FILE")"
echo "✅ Response rate: $(jq '.comments | length' "$RESPONSES_FILE") responses posted"
```

**Final Validation:** Mandatory verification gates that block completion:
```bash
# HARD VERIFICATION GATE - Must pass before declaring success
echo "🔍 MANDATORY: Verifying 100% comment coverage"
UNRESPONDED=$(jq -r '.comments[] | select(.requires_response == true and .responded != true) | .id' "$COMMENTS_FILE" | wc -l)
if [ "$UNRESPONDED" -gt 0 ]; then
    echo "❌ CRITICAL: $UNRESPONDED unresponded comments remain"
    exit 1
fi

# Verify mergeable status
gh pr view --json mergeable --jq '.mergeable' | grep -q "MERGEABLE" || {
    echo "❌ CRITICAL: PR not mergeable after changes"
    exit 1
}
echo "✅ All validation gates passed"
```

## 🎯 Success Criteria & Quality Gates

**Technical Implementation Requirements:**
- All security vulnerabilities addressed with proper fixes (not just comments)
- Runtime errors resolved with robust error handling and validation
- Test failures fixed with updated test cases and corrected functionality
- Code quality improved through systematic refactoring and optimization

**Communication & Documentation Standards:**
- Every PR comment receives detailed technical response
- All code changes include proper justification and documentation
- Security fixes explained with vulnerability details and mitigation strategy
- Performance improvements quantified with before/after metrics:
```bash
# Performance measurement implementation
COPILOT_START_TIME=$(date +%s)
START_CONTEXT=$(ps -o rss= -p $$)  # Memory baseline
START_FILES=$(find . -name "*.py" -o -name "*.md" | wc -l)

# Track operations throughout execution
OPERATION_COUNT=0
log_operation() {
    OPERATION_COUNT=$((OPERATION_COUNT + 1))
    echo "$(date '+%H:%M:%S') [$OPERATION_COUNT] $1" >> "$WORK_DIR/operations.log"
}

# Final performance calculation
calculate_performance() {
    COPILOT_END_TIME=$(date +%s)
    DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
    END_CONTEXT=$(ps -o rss= -p $$)
    MEMORY_DELTA=$((END_CONTEXT - START_CONTEXT))

    echo "📊 PERFORMANCE METRICS:"
    echo "⏱️  Execution time: ${DURATION}s"
    echo "💾 Memory delta: ${MEMORY_DELTA}KB"
    echo "🔧 Operations: $OPERATION_COUNT"
    echo "📝 Files changed: $(git diff --name-only | wc -l)"
    echo "📈 Response rate: $(calculate_response_rate)%"

    # Performance gate
    if [ $DURATION -gt 300 ]; then
        echo "⚠️  WARNING: Execution exceeded 5-minute target"
    fi
}
```

**Quality Assurance Checkpoints:** Mandatory verification gates that block progression:
```bash
# CHECKPOINT 1: No regressions verification
verify_no_regressions() {
    echo "🔍 CHECKPOINT: Verifying no regressions introduced"
    ./run_tests.sh > "$WORK_DIR/test_results.log" 2>&1 || {
        echo "❌ CRITICAL: Tests failing after changes"
        echo "Test log: $WORK_DIR/test_results.log"
        exit 1
    }
    log_operation "Regression verification passed"
}

# CHECKPOINT 2: Implementation backing promises
verify_implementations() {
    echo "🔍 CHECKPOINT: Verifying code implementations"
    PROMISES_FILE="$WORK_DIR/promises.txt"
    IMPLEMENTATIONS_FILE="$WORK_DIR/implementations.txt"

    # Extract promises from responses
    jq -r '.responses[].body' "$WORK_DIR/responses.json" | grep -i "will\|implement\|fix" > "$PROMISES_FILE" || touch "$PROMISES_FILE"

    # Verify git diff shows actual changes
    git diff --stat > "$IMPLEMENTATIONS_FILE"
    if [ ! -s "$IMPLEMENTATIONS_FILE" ] && [ -s "$PROMISES_FILE" ]; then
        echo "❌ CRITICAL: Promises made but no code changes found"
        exit 1
    fi
    log_operation "Implementation verification passed"
}

# CHECKPOINT 3: Security validation
verify_security_patterns() {
    echo "🔍 CHECKPOINT: Validating security fixes"
    # Check for common vulnerability patterns
    if git diff | grep -E "shell=True|eval\(|exec\("; then
        echo "⚠️  WARNING: Potential security issues detected in changes"
        read -p "Continue anyway? (y/N): " confirm
        [ "$confirm" = "y" ] || exit 1
    fi
    log_operation "Security validation passed"
}
```

## ⚡ Optimization & Efficiency Features

**Context Management:**
- Process only recent, actionable comments for maximum efficiency:
    - "Recent" comments are configurable (default: last 7 days or 30 most recent, whichever is fewer) with smart scaling for high-activity PRs
    - "Actionable" comments include code change requests, bug reports, security/performance concerns, test failures
    - Non-actionable comments (general praise, off-topic discussion) are deprioritized automatically
- Use targeted file reads and semantic search to minimize context usage
- Batch similar changes together to reduce total tool invocations (max 3-4 edits per MultiEdit operation)
- Focus on high-impact changes that address multiple concerns simultaneously

**Intelligent Prioritization:**
- Security vulnerabilities receive highest priority and immediate attention
- Runtime errors addressed before style or minor quality issues
- Test failures fixed systematically to ensure reliable CI pipeline
- Performance optimizations applied where measurement shows clear benefit

This command provides complete PR enhancement capability in a single, self-contained workflow that requires no external slash commands or subagents while maintaining comprehensive coverage of all critical PR processing needs.
