---
description: /copilot - Fast PR Processing
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

This command executes a four-phase workflow with priority-based bug triage:

- **Phase 0: Critical Bug Scan** - MANDATORY first step: scan all comments for security/production blockers and fix immediately with tests
- **Phase 1: Analysis & Categorization** - Execute /gstatus, categorize remaining comments (BLOCKING/IMPORTANT/ROUTINE), launch copilot-fixpr agent
- **Phase 2: Implementation & Response** - LLM analyzes EVERY comment fully, identifies ALL issues per comment, implements fixes with ACTION_ACCOUNTABILITY protocol, posts responses via /commentreply
- **Phase 3: Verification & Completion** - Run tests for critical/blocking fixes, verify commits, push via /pushl, confirm 100% comment coverage

See detailed playbooks below for complete phase specifications.

## 📘 DETAILED PHASE PLAYBOOKS & REFERENCE

### Phase 0 Playbook — Critical Bug Scan

- **Scope Clarification**: Claude (the orchestrator) owns Phase 0 end-to-end. Directly edit files, add tests, and run verification locally—do **not** delegate critical or blocking bugs to the agent. The agent only joins once Phase 0 is complete.
- **Sanitization First**: Run `sanitize_comment` on every comment body before keyword scans to avoid script injection. The sanitized payload feeds the `CRITICAL_PATTERNS` grep, ensuring detection happens on trusted text.
- **Testing & Commit Timing**:
  1. Apply the fix immediately after detecting a critical bug.
  2. Run the project’s detected test command (see Phase 3 Playbook) before proceeding.
  3. If tests fail, stay in Phase 0 until the fix passes; do **not** defer failures to Phase 3.
  4. Commit each fix individually using `git commit -m "Fix: <short description>"` before moving to the next issue. These commits are referenced later in responses.json.
- **Gate to Phase 1**: All critical bugs fixed, tested, and committed. Document each fix in TodoWrite so you can cite file paths and verification notes when generating responses.

### Phase 1 Playbook — Analysis & Categorization

- **Status + Comment Fetch**: Execute `/gstatus` immediately after Phase 0. Comments are already loaded from Phase 0 (either from cache or fresh fetch).
- **Outdated Comment Detection**: Before processing, check if comments reference code that has been refactored:
  ```bash
  # For each inline comment, check if the referenced commit is still relevant
  check_comment_outdated() {
      local comment_commit="$1"  # original_commit_id from the comment
      local comment_path="$2"    # file path the comment is on
      local comment_line="$3"    # line number

      # If comment references a commit not in current HEAD ancestry, it may be outdated
      if [ -n "$comment_commit" ] && ! git merge-base --is-ancestor "$comment_commit" HEAD 2>/dev/null; then
          echo "OUTDATED"
          return
      fi

      # Check if the file/line has been modified since the comment's commit
      if [ -n "$comment_commit" ] && [ -n "$comment_path" ]; then
          local changes=$(git diff "$comment_commit"..HEAD -- "$comment_path" 2>/dev/null | wc -l)
          if [ "$changes" -gt 50 ]; then
              echo "LIKELY_OUTDATED"
              return
          fi
      fi

      echo "CURRENT"
  }

  # Comments marked OUTDATED get response: "ALREADY FIXED - Code has been refactored since this comment"
  ```
- **Categorization Pipeline**:
  1. Sanitize each comment body.
  2. Check if comment is OUTDATED (references refactored code).
  3. Pass sanitized text to `categorize_comment()` to obtain CRITICAL/BLOCKING/IMPORTANT/ROUTINE labels.
  4. Record the mapping (e.g., in TodoWrite or a scratch buffer) so Phase 2 can consume a prioritized queue.
- **Clarify Delegation Rules**: Critical + blocking items remain orchestrator-owned. Only mark an item as agent-eligible if it is IMPORTANT and requires heavy file edits (e.g., multi-file refactors). ROUTINE feedback is kept local for speed.
- **Test Expectations**: No new tests run in Phase 1; this is purely classification + planning.

### Phase 2 Playbook — Implementation & Responses

- **Priority Queue Implementation**: Enforce the priority order with an explicit loop so reviewers can see it's implemented, not just promised:

```bash
PRIORITIZED_COMMENTS=$(jq -c '.comments[]' "$COMMENTS_FILE" | while read -r comment; do
    body=$(echo "$comment" | jq -r '.body')
    sanitized=$(sanitize_comment "$body")
    category=$(categorize_comment "$sanitized")
    echo "$category|$comment"
done | sort)

for entry in $PRIORITIZED_COMMENTS; do
    category="${entry%%|*}"
    comment_json="${entry#*|}"
    case "$category" in
        CRITICAL|BLOCKING)
            implement_directly "$comment_json"
            ;;
        IMPORTANT)
            delegate_to_agent_if_needed "$comment_json"
            ;;
        ROUTINE)
            handle_routine "$comment_json"
            ;;
    esac
done
```

- **Agent Coordination**: When delegation occurs, poll `/tmp/$REPO_NAME/$BRANCH_NAME/agent_status.json` until it reports `"status": "completed"`. Only then fold the diff back into responses.json.
- **Response Assembly**: Populate every response with the new ACTION_ACCOUNTABILITY fields (`action_taken`, `files_modified`, `commit`, `verification`, etc.) as you implement each fix so evidence is fresh.

#### Comprehensive Comment Analysis Protocol

**MANDATORY: For EVERY comment, regardless of author/type/length:**

❌ **ONLY EXCEPTION**: Comments starting with `[AI responder]` (our own AI-generated responses from previous runs) MUST be skipped to prevent self-response loops.

1. **Full Content Analysis**: Read entire body, identify ALL distinct issues, parse file:line references.
2. **Multi-Issue Detection**: Count distinct issues, determine action/files/severity for each.
3. **Consolidated Response**: ONE response per comment addressing ALL N issues. Group by Actionable/Nitpick/Informational with global issue numbering and completion stats.
4. **No Keyword Shortcuts**: NO pre-parsing, NO pre-categorization. LLM receives FULL body and makes ALL decisions.

### Phase 3 Playbook — Verification & Completion

- **Test Command Detection**:
  1. If `package.json` contains an npm `test` script, run `npm test`.
  2. Else if `pytest.ini` or `pyproject.toml` exists, run `pytest` via `./run_tests.sh`.
  3. Else fallback to `./run_tests.sh` if present, otherwise `./run_tests_with_coverage.sh`.
  4. Export `TEST_COMMAND` so the same path is logged in responses.
- **Execution & Exit Handling**:

```bash
if [ -z "$TEST_COMMAND" ]; then
    echo "❌ TEST_COMMAND not set - define project test entry point before Phase 3"
    exit 1
fi

echo "🧪 Running tests via: $TEST_COMMAND"
set +e
eval "$TEST_COMMAND"
TEST_EXIT=$?
set -e

if [ $TEST_EXIT -ne 0 ]; then
    echo "❌ Tests failed (exit $TEST_EXIT). Block completion until failure is resolved."
    exit $TEST_EXIT
fi
echo "✅ Test verification complete"
```

- **Failure Policy**: Critical/blocking fixes cannot be marked complete until tests pass. If failures persist, re-open the relevant Phase 2 item and capture the remediation steps in responses.json before retrying.
- **Metrics & Health Signal**: Once tests pass, recompute the quality metrics (see "Quality Metrics & Health" below) to determine SAFE TO MERGE vs NEEDS WORK.

# /copilot - Fast PR Processing

## 📋 Overview

**Quality-focused PR processing** with priority-based bug triage (CRITICAL > BLOCKING > IMPORTANT > ROUTINE). Hybrid orchestrator + copilot-fixpr agent design.

**Composed Commands**: `/gstatus`, `/commentcheck`, `/commentfetch`, `/commentreply`, `/fixpr`, `/pushl`, `/guidelines`

**Boundaries**: Orchestrator handles comments/GitHub API; Agent handles file modifications. Never mixed.

**Performance**: Adaptive timeouts — simple PRs (5m), moderate (10m), complex (15m). 100% comment response rate target.


## 🔧 Utilities & Validation

### Cleanup & Timing Helpers

Ultra-fast PR processing using hybrid orchestration still needs reliable cleanup and error handling to avoid leaking temp files.

```bash
# CLEANUP FUNCTION: Define error recovery and cleanup mechanisms

get_repo_name() {
    local repo_root
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
    local repo_name=""

    if [ -n "$repo_root" ]; then
        repo_name=$(basename "$repo_root")
    else
        repo_name=$(basename "$(pwd)")
    fi

    repo_name=$(echo "$repo_name" | tr -cd '[:alnum:]._-')
    echo "${repo_name:-unknown-repo}"
}

get_branch_name() {
    local branch_name
    branch_name=$(git branch --show-current 2>/dev/null || true)
    branch_name=$(echo "$branch_name" | tr -cd '[:alnum:]._-')
    echo "${branch_name:-unknown-branch}"
}

cleanup_temp_files() {
    local repo_name
    repo_name=$(get_repo_name)
    local branch_name
    branch_name=$(get_branch_name)
    local temp_dir="/tmp/$repo_name/$branch_name"

    # Safety: never allow cleanup to target /tmp itself
    if [ "$temp_dir" = "/tmp" ] || [ "$temp_dir" = "/tmp/" ]; then
        echo "⚠️  CLEANUP: Skipping unsafe temp_dir=$temp_dir"
        return 0
    fi

    if [ -d "$temp_dir" ]; then
        echo "🧹 CLEANUP: Removing temporary files from $temp_dir"
        rm -rf "$temp_dir"/* 2>/dev/null || true
    fi

    # Reset any stuck GitHub operations
    echo "🔄 CLEANUP: Resetting any stuck operations"
    # Additional cleanup operations as needed
}

# Cleanup old caches (older than 7 days)
cleanup_old_caches() {
    local repo_name
    repo_name=$(get_repo_name)
    local repo_cache_dir="/tmp/$repo_name"
    
    # Safety: never allow cleanup to target /tmp itself
    if [ "$repo_cache_dir" = "/tmp" ] || [ "$repo_cache_dir" = "/tmp/" ]; then
        echo "⚠️  CLEANUP: Skipping unsafe repo_cache_dir=$repo_cache_dir"
        return 0
    fi

    if [ -d "$repo_cache_dir" ]; then
        # Remove caches older than 7 days (within the repo-scoped directory only)
        find "$repo_cache_dir" -mindepth 1 -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    fi
}

# ERROR HANDLER: Trap errors for graceful cleanup

trap 'cleanup_temp_files; echo "🚨 ERROR: Copilot workflow interrupted"; exit 1' ERR

COPILOT_START_TIME=$(date +%s)

# Initialize path variables with repo name
# NOTE: These are set once here and used throughout - do not re-declare

REPO_NAME=$(get_repo_name)
BRANCH_NAME=$(get_branch_name)
CACHE_DIR="/tmp/$REPO_NAME/$BRANCH_NAME"
CACHE_METADATA_FILE="$CACHE_DIR/cache_metadata.json"
COMMENTS_FILE="$CACHE_DIR/comments.json"
AGENT_STATUS="$CACHE_DIR/agent_status.json"

# Perform cleanup of old caches
cleanup_old_caches

# ═══════════════════════════════════════════════════════════════════════════════
# CACHE STRATEGY: Always Fresh + Handled Registry (v2.0)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Previous approach: Complex staleness detection (is_cache_fresh_incremental, is_cache_fresh)
#   - Problem: Missed 12 comments because staleness check only covered 2/4 comment types
#   - Problem: Cache was "fresh" by TTL but stale in reality
#
# New approach: Always fetch fresh, skip already-handled comments
#   - Always get fresh comment data from GitHub (no staleness bugs)
#   - Per-comment cache tracks "handled" status after each successful reply
#   - Resumable: if interrupted mid-run, already-handled comments won't be reprocessed
#   - Thread-independent: each reply is tracked separately
#
# See bead worktree_worker4-qqj for design details
# ═══════════════════════════════════════════════════════════════════════════════

# Phase 0: ALWAYS fetch fresh comments - no staleness check
# The handled registry in per-comment cache ensures we don't reprocess comments
echo "🔄 Fetching fresh comments from GitHub API (always-fresh strategy)"
/commentfetch

# Resolve project root for Python helper import (must be before first use)
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Report unhandled comment count for visibility
if [ -d "$CACHE_DIR/comments" ]; then
    UNHANDLED_COUNT=$(python3 -c "
import sys
import os
sys.path.insert(0, os.path.join('$PROJECT_ROOT', '.claude', 'commands', '_copilot_modules'))
try:
    from per_comment_cache import PerCommentCache
    cache = PerCommentCache('$CACHE_DIR')
    unhandled = cache.get_unhandled_comments()
    print(len(unhandled))
except Exception as e:
    print(-1)
" || echo -1)

    if [ "$UNHANDLED_COUNT" -ge 0 ]; then
        echo "📊 Found $UNHANDLED_COUNT unhandled comment(s) requiring responses"
    fi
fi

# Get comprehensive PR status first

/gstatus

# Initialize timing for performance tracking (silent unless exceeded)
```

### Security Functions

```bash
# Security function for sanitizing GitHub comment content

sanitize_comment() {
    local input="$1"
    local max_length="${2:-10000}"  # Default 10KB limit

    # Length validation
    if [ ${#input} -gt $max_length ]; then
        echo "❌ Input exceeds maximum length of $max_length characters" >&2
        return 1
    fi

    # Remove null bytes and escape shell metacharacters
    local sanitized=$(echo "$input" | tr -d '\0' | sed 's/[`$\\]/\\&/g' | sed 's/[;&|]/\\&/g')

    # Check for suspicious patterns in original input (before escaping)
    if echo "$input" | grep -qE '(\$\(|`|<script|javascript:|eval\(|exec\()'; then
        echo "⚠️ Potentially malicious content detected and neutralized" >&2
        # Continue with sanitized version rather than failing completely
    fi

    echo "$sanitized"
}

# Validate branch name to prevent path injection

validate_branch_name() {
    local branch="$1"
    if [[ "$branch" =~ ^[a-zA-Z0-9._-]+$ ]] && [ ${#branch} -le 100 ]; then
        return 0
    else
        echo "❌ Invalid branch name: contains illegal characters or too long" >&2
        return 1
    fi
}
```

## 🤝 Hybrid Execution Details

### Orchestrator Responsibilities

- Analyze actionable issues and categorize by type (security, runtime, tests, style)
- Process issue responses and plan implementation strategy
- Handle all GitHub API operations directly (proven to work)

### 🚀 Parallel copilot-fixpr Agent Launch with Explicit Synchronization
Launch specialized agent for file modifications with structured coordination:
- **FIRST**: Execute `/fixpr` command to resolve merge conflicts and CI failures
- Analyze current GitHub PR status and identify potential improvements
- Review code changes for security vulnerabilities and quality issues
- Implement actual file fixes using Edit/MultiEdit tools with File Justification Protocol
- Focus on code quality, performance optimization, and technical accuracy
- **NEW**: Write completion status to structured result file for orchestrator

**🚨 EXPLICIT SYNCHRONIZATION PROTOCOL**: Eliminates race conditions
```bash

# Secure branch name and setup paths (using repo-scoped cache directory already set)

mkdir -p "$CACHE_DIR"

# Agent execution with status tracking

copilot-fixpr-agent > "$AGENT_STATUS" &
AGENT_PID=$!

# Detect PR complexity for appropriate timeout

FILES_CHANGED=$(git diff --name-only origin/main | wc -l)
LINES_CHANGED=$(git diff --stat origin/main | tail -1 | grep -oE '[0-9]+' | head -1 || echo 0)

if [ $FILES_CHANGED -le 3 ] && [ $LINES_CHANGED -le 50 ]; then
    TIMEOUT=300  # 5 minutes for simple PRs
elif [ $FILES_CHANGED -le 10 ] && [ $LINES_CHANGED -le 500 ]; then
    TIMEOUT=600  # 10 minutes for moderate PRs
else
    TIMEOUT=900  # 15 minutes for complex PRs
fi

echo "📊 PR Complexity: $FILES_CHANGED files, $LINES_CHANGED lines (timeout: $((TIMEOUT/60))m)"

# Orchestrator waits for agent completion with adaptive timeout

START_TIME=$(date +%s)
while [ ! -f "$AGENT_STATUS" ]; do
    # Check if agent is still running
    if ! kill -0 $AGENT_PID 2>/dev/null; then
        echo "⚠️ Agent process terminated unexpectedly"
        break
    fi

    CURRENT_TIME=$(date +%s)
    if [ $((CURRENT_TIME - START_TIME)) -gt $TIMEOUT ]; then
        echo "⚠️ Agent timeout after $((TIMEOUT/60)) minutes"
        kill $AGENT_PID 2>/dev/null
        break
    fi
    sleep 10
done

# Wait for agent to complete writing valid JSON with "completed" status
# Shell redirect creates file immediately, so file existence alone is insufficient
while [ -f "$AGENT_STATUS" ] && [ "$(jq -r '.status' "$AGENT_STATUS" 2>/dev/null)" != "completed" ]; do
    # Check if agent is still running
    if ! kill -0 $AGENT_PID 2>/dev/null; then
        echo "⚠️ Agent process terminated before completing"
        break
    fi

    CURRENT_TIME=$(date +%s)
    if [ $((CURRENT_TIME - START_TIME)) -gt $TIMEOUT ]; then
        echo "⚠️ Agent timeout after $((TIMEOUT/60)) minutes"
        kill $AGENT_PID 2>/dev/null
        break
    fi
    sleep 2
done

# Verify agent completion before proceeding

if [ -f "$AGENT_STATUS" ] && [ "$(jq -r '.status' "$AGENT_STATUS" 2>/dev/null)" = "completed" ]; then
    echo "✅ Agent completed successfully, proceeding with response generation"
else
    echo "❌ CRITICAL: Agent did not complete successfully"
    exit 1
fi
```

**Coordination Protocol**: Explicit synchronization prevents race conditions between orchestrator and agent

# Read structured agent results from status file

# Note: AGENT_STATUS is already set earlier in the workflow
# Using the centralized cache directory for consistency

if [ -f "$AGENT_STATUS" ]; then
    # Parse structured agent results with error handling
    FILES_MODIFIED=$(jq -r '.files_modified[]?' "$AGENT_STATUS" 2>/dev/null | head -20 || echo "")
    FIXES_APPLIED=$(jq -r '.fixes_applied[]?' "$AGENT_STATUS" 2>/dev/null | head -20 || echo "")
    COMMIT_HASH=$(jq -r '.commit_hash?' "$AGENT_STATUS" 2>/dev/null || echo "")
    EXECUTION_TIME=$(jq -r '.execution_time?' "$AGENT_STATUS" 2>/dev/null || echo "0")

    echo "📊 Agent Results:"
    [ -n "$FILES_MODIFIED" ] && echo "  Files: $FILES_MODIFIED"
    [ -n "$FIXES_APPLIED" ] && echo "  Fixes: $FIXES_APPLIED"
    [ -n "$COMMIT_HASH" ] && echo "  Commit: $COMMIT_HASH"
    echo "  Time: ${EXECUTION_TIME}s"
else
    echo "❌ No agent status file found - using fallback git diff"
    FILES_MODIFIED=$(git diff --name-only | head -10)
fi
```

**Agent-Orchestrator Interface**:
- **Agent provides**: Structured JSON with files_modified, fixes_applied, commit_hash, execution_time
- **Agent JSON contract**: `agent_status.json` also includes a `status` field (e.g., `"completed"`) so the orchestrator can block until work finishes. The copilot-fixpr agent implementation has been updated to emit this structure before the orchestrator consumes it.
- **Orchestrator handles**: Comment processing, response generation, GitHub API operations, coverage tracking
- **Coordination ensures**: Explicit synchronization prevents race conditions and response inconsistencies

**Response Generation with Action Protocol** (MANDATORY ORCHESTRATOR RESPONSIBILITY):
```bash
# Cache paths already defined at workflow start

echo "📝 Generating action-based responses.json with implementation accountability"

# Generate responses in commentreply.py expected format

# Orchestrator writes to: $CACHE_DIR/responses.json

# 🚨 ACTION RESPONSE PROTOCOL: Every comment gets detailed action report

echo "🔍 ACTION PROTOCOL: Analyzing ALL comments for categorized responses with accountability"

# Comment categorization for response generation
categorize_comment() {
    local comment_body="$1"

    # CRITICAL: Use same pattern as Phase 0 for consistency (must match line 48)
    local critical_pattern="(CRITICAL|BUG|SECURITY|BLOCKER|PRODUCTION BLOCKER|PRODUCTION BUG|rate limit|authentication|authorization|admin.*UID|data loss|data-loss|dataloss|corruption|crash|vulnerability|auth bypass)"
    local blocking_pattern="(CI fail|build fail|test fail|breaking change|resource leak|timeout)"
    local important_pattern="(performance|logic error|validation|architectural|latency)"

    # CRITICAL: Security, production blockers, data corruption (should be handled in Phase 0)
    if echo "$comment_body" | grep -qiE "$critical_pattern"; then
        echo "CRITICAL"
        return
    fi

    # BLOCKING: CI failures, build failures, breaking changes
    if echo "$comment_body" | grep -qiE "$blocking_pattern"; then
        echo "BLOCKING"
        return
    fi

    # IMPORTANT: Performance, logic errors, missing validation
    if echo "$comment_body" | grep -qiE "$important_pattern"; then
        echo "IMPORTANT"
        return
    fi

    # ROUTINE: Code style, documentation, optional refactoring
    echo "ROUTINE"
}

# INPUT SANITIZATION: Validate branch name (already sanitized earlier)

if [ -z "$BRANCH_NAME" ]; then
    echo "❌ CRITICAL: Invalid or empty branch name"
    cleanup_temp_files
    return 1
fi

# SECURE PATH CONSTRUCTION: Use repo-scoped cache directory

# Note: COMMENTS_FILE and CACHE_DIR are already set earlier in the workflow
export RESPONSES_FILE="$CACHE_DIR/responses.json"

# API RESPONSE VALIDATION: Verify comment data exists and is valid JSON (using jq -e)

if [ ! -f "$COMMENTS_FILE" ]; then
    echo "❌ CRITICAL: No comment data from commentfetch at $COMMENTS_FILE"
    cleanup_temp_files
    return 1
fi

# VALIDATION: Verify comments.json is valid JSON before processing (CodeRabbit's jq -e suggestion)

if ! jq -e empty "$COMMENTS_FILE" 2>/dev/null; then
    echo "❌ CRITICAL: Invalid JSON in comments file"
    cleanup_temp_files
    return 1
fi

TOTAL_COMMENTS=$(jq '.comments | length' "$COMMENTS_FILE")
echo "📊 Processing $TOTAL_COMMENTS comments for response generation"

# Generate responses for ALL unresponded comments

# This is ORCHESTRATOR responsibility, not agent responsibility

# 🚨 NEW: MANDATORY FORMAT VALIDATION

echo "🔧 VALIDATING: Response format compatibility with commentreply.py"

# Resolve repository root for downstream tooling
PROJECT_ROOT=$(git rev-parse --show-toplevel)
if [ -z "$PROJECT_ROOT" ]; then
    echo "❌ CRITICAL: Unable to resolve project root"
    exit 1
fi

# Use dedicated validation script for better maintainability
python3 "$PROJECT_ROOT/.claude/commands/validate_response_format.py" || {
    echo "❌ CRITICAL: Invalid response format";
    exit 1;
}

# Verify responses.json exists and is valid before proceeding

if [ ! -f "$RESPONSES_FILE" ]; then
    echo "❌ CRITICAL: responses.json not found at $RESPONSES_FILE"
    echo "Orchestrator must generate responses before posting"
    exit 1
fi

# 🚨 ACTION RESPONSE TEMPLATE: Detailed accountability required

echo "📋 Building action-based response structure with implementation tracking"
cat > "$RESPONSES_FILE" << 'EOF'
{
  "response_protocol": "ACTION_ACCOUNTABILITY",
  "response_types": {
    "FIXED": "Issue implemented with working code (STRONGLY PREFERRED)",
    "DEFERRED": "Cannot do now - MUST create real bead with ID",
    "ACKNOWLEDGED": "Purely informational - NO future promises allowed",
    "NOT_DONE": "Won't implement with specific technical reason"
  },
  "response_priority_rules": {
    "rule_1": "FIXED is STRONGLY PREFERRED - do the work if at all feasible",
    "rule_2": "DEFERRED requires real bead_id - no vague 'TODO tracked'",
    "rule_3": "ACKNOWLEDGED must NOT contain 'will', 'TODO', or future promises",
    "rule_4": "NOT_DONE requires specific technical reason why not feasible"
  },
  "required_fields": {
    "FIXED": ["category", "action_taken", "files_modified", "commit", "verification"],
    "DEFERRED": ["category", "reason", "bead_id"],
    "ACKNOWLEDGED": ["category", "explanation"],
    "NOT_DONE": ["category", "reason"]
  },
  "template_fixed": {
    "response": "FIXED",
    "category": "CRITICAL|BLOCKING|IMPORTANT|ROUTINE",
    "html_url": "https://github.com/owner/repo/pull/123#issuecomment-456",
    "action_taken": "Specific implementation description",
    "files_modified": ["file1.ts:123", "file2.py:456"],
    "tests_added": ["test1.test.ts"],
    "commit": "abc123de",
    "verification": "✅ Tests pass, feature verified"
  },
  "template_deferred": {
    "response": "DEFERRED",
    "category": "CRITICAL|BLOCKING|IMPORTANT|ROUTINE",
    "html_url": "https://github.com/owner/repo/pull/123#issuecomment-456",
    "reason": "Specific technical reason why cannot be done in this PR",
    "bead_id": "worktree_worker4-xyz",
    "note": "MUST create actual bead BEFORE using DEFERRED - no vague 'TODO tracked'"
  },
  "template_acknowledged": {
    "response": "ACKNOWLEDGED",
    "category": "CRITICAL|BLOCKING|IMPORTANT|ROUTINE",
    "html_url": "https://github.com/owner/repo/pull/123#issuecomment-456",
    "explanation": "Factual note only - NO future promises, NO 'will do', NO 'TODO'",
    "forbidden": ["will", "TODO", "follow-up", "future", "later"]
  },
  "template_not_done": {
    "response": "NOT_DONE",
    "category": "CRITICAL|BLOCKING|IMPORTANT|ROUTINE",
    "html_url": "https://github.com/owner/repo/pull/123#issuecomment-456",
    "reason": "Specific reason why implementation not feasible"
  },
  "template_multi_issue": {
    "comment_id": "3675347161",
    "html_url": "https://github.com/owner/repo/pull/123#issuecomment-3675347161",
    "analysis": {
      "total_issues": 11,
      "actionable": 6,
      "nitpicks": 5
    },
    "issues": [
      {
        "number": 1,
        "file": "game_state_instruction.md",
        "line": "751-776",
        "description": "Remove phrase-scanning triggers",
        "category": "BLOCKING",
        "response": "FIXED",
        "action_taken": "Removed phrase-scanning trigger patterns, converted to intent-based processing",
        "files_modified": ["game_state_instruction.md:751-776"],
        "commit": "abc123",
        "verification": "✅ Verified no phrase-scanning patterns remain",
        "html_url": "https://github.com/owner/repo/pull/123#discussion_r456"
      }
    ],
    "reply_text": "Consolidated markdown addressing all 11 issues"
  },
  "responses": []
}
EOF

# Validate responses.json with jq -e (CodeRabbit suggestion)

jq -e . "$RESPONSES_FILE" > /dev/null || {
    echo "❌ CRITICAL: Invalid JSON in responses.json"
    exit 1
}

echo "🔄 Executing /commentreply with ACTION protocol (FIXED/DEFERRED/ACKNOWLEDGED/NOT_DONE)"
/commentreply || {
    echo "🚨 CRITICAL: Comment response failed"
    cleanup_temp_files
    return 1
}
echo "🔍 Verifying coverage via /commentcheck"
/commentcheck || {
    echo "🚨 CRITICAL: Comment coverage failed"
    cleanup_temp_files
    return 1
}

## 📊 Quality Metrics & Health Signals

# 🚨 NEW: Quality-focused metrics reporting
echo ""
echo "📊 QUALITY METRICS (Priority-Based Assessment):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count responses by category and type
CRITICAL_FIXED=$(jq '[.responses[] | select(.category == "CRITICAL" and .response == "FIXED")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
CRITICAL_DEFERRED=$(jq '[.responses[] | select(.category == "CRITICAL" and .response == "DEFERRED")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
CRITICAL_TOTAL=$(jq '[.responses[] | select(.category == "CRITICAL")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
BLOCKING_FIXED=$(jq '[.responses[] | select(.category == "BLOCKING" and .response == "FIXED")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
BLOCKING_DEFERRED=$(jq '[.responses[] | select(.category == "BLOCKING" and .response == "DEFERRED")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
BLOCKING_TOTAL=$(jq '[.responses[] | select(.category == "BLOCKING")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
IMPORTANT_FIXED=$(jq '[.responses[] | select(.category == "IMPORTANT" and .response == "FIXED")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
IMPORTANT_TOTAL=$(jq '[.responses[] | select(.category == "IMPORTANT")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
IMPORTANT_DEFERRED=$(jq '[.responses[] | select(.category == "IMPORTANT" and .response == "DEFERRED")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
ROUTINE_RESPONSES=$(jq '[.responses[] | select(.category == "ROUTINE")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
TOTAL_RESPONSES=$(jq '.responses | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)

if [ $CRITICAL_TOTAL -gt 0 ]; then
    CRITICAL_PCT=$((CRITICAL_FIXED * 100 / CRITICAL_TOTAL))
    echo "🚨 Critical bugs fixed: $CRITICAL_FIXED/$CRITICAL_TOTAL ($CRITICAL_PCT%) — $CRITICAL_DEFERRED deferred"
else
    echo "🚨 Critical bugs fixed: $CRITICAL_FIXED/$CRITICAL_TOTAL (N/A)"
fi

if [ $BLOCKING_TOTAL -gt 0 ]; then
    BLOCKING_PCT=$((BLOCKING_FIXED * 100 / BLOCKING_TOTAL))
    echo "✅ Blocking issues fixed: $BLOCKING_FIXED/$BLOCKING_TOTAL ($BLOCKING_PCT%) — $BLOCKING_DEFERRED deferred"
else
    echo "✅ Blocking issues fixed: $BLOCKING_FIXED/$BLOCKING_TOTAL (N/A)"
fi

echo "⚠️  Important issues: $IMPORTANT_FIXED fixed, $IMPORTANT_DEFERRED deferred (of $IMPORTANT_TOTAL total)"
echo "📝 Routine responses: $ROUTINE_RESPONSES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Total comments processed: $TOTAL_RESPONSES"

# Determine PR health status
UNRESOLVED_CRITICAL=$((CRITICAL_TOTAL - CRITICAL_FIXED - CRITICAL_DEFERRED))
UNRESOLVED_BLOCKING=$((BLOCKING_TOTAL - BLOCKING_FIXED - BLOCKING_DEFERRED))

if [ $CRITICAL_TOTAL -eq 0 ] && [ $BLOCKING_TOTAL -eq 0 ]; then
    echo "✅ Overall health: SAFE TO MERGE (no critical/blocking issues)"
elif [ $CRITICAL_FIXED -eq $CRITICAL_TOTAL ] && [ $BLOCKING_FIXED -eq $BLOCKING_TOTAL ]; then
    echo "✅ Overall health: SAFE TO MERGE (all critical/blocking resolved)"
elif [ $UNRESOLVED_CRITICAL -eq 0 ] && [ $UNRESOLVED_BLOCKING -eq 0 ]; then
    # Check if any critical/blocking were deferred (not allowed for SAFE TO MERGE per success criteria)
    CRITICAL_DEFERRED_COUNT=$(jq -r '[.responses[] | select(.category == "CRITICAL" and .response == "DEFERRED")] | length' "$RESPONSES_FILE" 2>/dev/null || echo "0")
    BLOCKING_DEFERRED_COUNT=$(jq -r '[.responses[] | select(.category == "BLOCKING" and .response == "DEFERRED")] | length' "$RESPONSES_FILE" 2>/dev/null || echo "0")
    
    if [ "$CRITICAL_DEFERRED_COUNT" -gt 0 ] || [ "$BLOCKING_DEFERRED_COUNT" -gt 0 ]; then
        echo "⚠️ Overall health: NEEDS REVIEW (critical/blocking issues deferred - must be FIXED for SAFE TO MERGE per success criteria)"
    else
        echo "✅ Overall health: SAFE TO MERGE (all critical/blocking issues fixed)"
    fi
else
    echo "❌ Overall health: NEEDS WORK ($UNRESOLVED_CRITICAL critical, $UNRESOLVED_BLOCKING blocking unresolved)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "✅ Action-based comment responses posted successfully with accountability"
```
Direct execution of /commentreply with implementation details from agent file changes for guaranteed GitHub posting

# Run tests to verify all fixes (Phase 3 verification)
echo ""
echo "🧪 PHASE 3: VERIFICATION - Running tests to confirm fixes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if there are any critical or blocking fixes that need test verification
NEEDS_TESTING=$((CRITICAL_FIXED + BLOCKING_FIXED))

if [ $NEEDS_TESTING -gt 0 ]; then
    echo "📊 Testing $NEEDS_TESTING critical/blocking fixes"

    TEST_COMMAND=""
    if [ -f package.json ] && jq -e '.scripts.test' package.json >/dev/null 2>&1; then
        TEST_COMMAND="npm test"
    elif [ -f ./run_tests.sh ]; then
        TEST_COMMAND="./run_tests.sh"
    elif [ -f pytest.ini ] || [ -f pyproject.toml ]; then
        TEST_COMMAND="pytest"
    elif [ -f ./run_tests_with_coverage.sh ]; then
        TEST_COMMAND="./run_tests_with_coverage.sh"
    fi

    if [ -z "$TEST_COMMAND" ]; then
        echo "❌ TEST_COMMAND not set - define the project test runner before continuing"
        exit 1
    fi

    echo "Running test suite via: $TEST_COMMAND"
    set +e
    eval "$TEST_COMMAND"
    TEST_EXIT=$?
    set -e

    if [ $TEST_EXIT -ne 0 ]; then
        echo "❌ Tests failed (exit $TEST_EXIT). Resolve before marking verification complete."
        exit $TEST_EXIT
    fi

    echo "✅ Test verification complete"
else
    echo "ℹ️  No critical/blocking fixes requiring test verification"
fi

# Verify commits for critical bugs
if [ $CRITICAL_FIXED -gt 0 ]; then
    echo ""
    echo "📝 Verifying critical bug fix commits:"
    git log --oneline --grep="Fix:" --grep="Critical" | sed 's/^/  /'
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 📋 Generate commit message with comment URLs for tracking

echo ""
echo "📋 GENERATING COMMIT MESSAGE WITH COMMENT URL TRACKING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Centralized jq filter: Flatten responses and nested issues for proper classification
# For multi-issue responses, preserve parent's comment_id and html_url as fallback
JQ_FLATTEN='(if (.issues? | length) > 0 then (.comment_id as \$parent_id | .html_url as \$parent_url | .issues[] | .comment_id //= \$parent_id | .parent_html_url //= \$parent_url) else . end)'

# Extract comment URLs from responses.json grouped by response type.
FIXED_URLS=$(jq -r "
  .responses[]
  | $JQ_FLATTEN
  | select(.response == \"FIXED\")
  | .html_url // .parent_html_url // empty
" "$RESPONSES_FILE" 2>/dev/null | sed '/^$/d' | sort -u || echo "")

CONSIDERED_URLS=$(jq -r "
  .responses[]
  | $JQ_FLATTEN
  | select(.response == \"ACKNOWLEDGED\" or .response == \"NOT_DONE\" or .response == \"DEFERRED\")
  | .html_url // .parent_html_url // empty
" "$RESPONSES_FILE" 2>/dev/null | sed '/^$/d' | sort -u || echo "")

# Get comment URLs from comments.json as fallback for responses with missing html_url.
# Identify which specific comment IDs lack URLs and backfill only those.
FIXED_IDS_WITHOUT_URLS=$(jq -r "
  .responses[]
  | $JQ_FLATTEN
  | select(.response == \"FIXED\" and ((.html_url // \"\") | length == 0) and ((.parent_html_url // \"\") | length == 0))
  | .comment_id // empty
" "$RESPONSES_FILE" 2>/dev/null | sed '/^$/d' | sort -u || echo "")

if [ -n "$FIXED_IDS_WITHOUT_URLS" ]; then
    echo "⚠️ Backfilling missing FIXED URLs from comments.json for $(echo "$FIXED_IDS_WITHOUT_URLS" | wc -l) comment(s)"
    while IFS= read -r id; do
        [ -z "$id" ] && continue
        url=$(jq -r --arg id "$id" '.comments[] | select((.id | tostring) == $id) | .html_url // empty' "$COMMENTS_FILE" 2>/dev/null)
        if [ -n "$url" ]; then
            FIXED_URLS="${FIXED_URLS}\n${url}"
        fi
    done <<< "$FIXED_IDS_WITHOUT_URLS"
fi

CONSIDERED_IDS_WITHOUT_URLS=$(jq -r "
  .responses[]
  | $JQ_FLATTEN
  | select((.response == \"ACKNOWLEDGED\" or .response == \"NOT_DONE\" or .response == \"DEFERRED\") and ((.html_url // \"\") | length == 0) and ((.parent_html_url // \"\") | length == 0))
  | .comment_id // empty
" "$RESPONSES_FILE" 2>/dev/null | sed '/^$/d' | sort -u || echo "")

if [ -n "$CONSIDERED_IDS_WITHOUT_URLS" ]; then
    echo "⚠️ Backfilling missing considered URLs from comments.json for $(echo "$CONSIDERED_IDS_WITHOUT_URLS" | wc -l) comment(s)"
    while IFS= read -r id; do
        [ -z "$id" ] && continue
        url=$(jq -r --arg id "$id" '.comments[] | select((.id | tostring) == $id) | .html_url // empty' "$COMMENTS_FILE" 2>/dev/null)
        if [ -n "$url" ]; then
            CONSIDERED_URLS="${CONSIDERED_URLS}\n${url}"
        fi
    done <<< "$CONSIDERED_IDS_WITHOUT_URLS"
fi

FIXED_URLS=$(echo -e "$FIXED_URLS" | sed '/^$/d' | sort -u)
CONSIDERED_URLS=$(echo -e "$CONSIDERED_URLS" | sed '/^$/d' | sort -u)

# Build commit message with comment URL tracking
COMMIT_MSG="Fix PR comments from /copilot workflow

**Comment Tracking:**"

if [ -n "$FIXED_URLS" ]; then
    FIXED_COUNT=$(echo -e "$FIXED_URLS" | grep -c 'http' || true)
    COMMIT_MSG="$COMMIT_MSG

✅ Fixed ($FIXED_COUNT):
$(echo -e "$FIXED_URLS" | sed 's/^/- /')"
else
    COMMIT_MSG="$COMMIT_MSG

✅ Fixed: None"
fi

if [ -n "$CONSIDERED_URLS" ]; then
    CONSIDERED_COUNT=$(echo -e "$CONSIDERED_URLS" | grep -c 'http' || true)
    COMMIT_MSG="$COMMIT_MSG

📝 Considered (acknowledged/deferred/not-done) ($CONSIDERED_COUNT):
$(echo -e "$CONSIDERED_URLS" | sed 's/^/- /')"
else
    COMMIT_MSG="$COMMIT_MSG

📝 Considered: None"
fi

COMMIT_MSG="$COMMIT_MSG

[copilot-commit]"

echo "📝 Generated commit message with comment tracking:"
echo "$COMMIT_MSG"
echo ""

# Create commit if there are changes (including untracked files)
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo "💾 Creating tracking commit..."
    git add -A
    COMMIT_MSG_FILE=$(mktemp)
    printf '%s\n' "$COMMIT_MSG" > "$COMMIT_MSG_FILE"
    if git commit --allow-empty -F "$COMMIT_MSG_FILE"; then
        echo "✅ Tracking commit created"
    else
        echo "⚠️ Commit failed (possibly no changes or already committed)"
    fi
    rm -f "$COMMIT_MSG_FILE"
else
    echo "ℹ️ No changes to commit (all fixes already committed)"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Push changes to PR with error recovery

/pushl || {
    echo "🚨 PUSH FAILED: PR not updated"
    echo "🔧 RECOVERY: Attempting git status check"
    git status
    cleanup_temp_files
    return 1
}

# 🚨 POST-PUSH COMMENT REFRESH: Catch late comments posted during workflow
echo "🔄 POST-PUSH: Re-fetching comments to catch late arrivals"
/commentfetch

# Check for NEW unhandled comments that arrived during the workflow
NEW_UNHANDLED=$(python3 -c "
import sys
import os
sys.path.insert(0, os.path.join('$PROJECT_ROOT', '.claude', 'commands', '_copilot_modules'))
try:
    from per_comment_cache import PerCommentCache
    cache = PerCommentCache('$CACHE_DIR')
    unhandled = cache.get_unhandled_comments()
    print(len(unhandled))
except Exception as e:
    print(0)
" || echo 0)

if [ "$NEW_UNHANDLED" -gt 0 ]; then
    echo "⚠️ Found $NEW_UNHANDLED new comment(s) posted during workflow - processing..."
    /commentreply || echo "⚠️ Warning: Some late comments may need manual response"
fi
```

**Coverage Tracking (MANDATORY GATE):**
```bash

# HARD VERIFICATION GATE with RECOVERY - Must pass before proceeding
# Now includes ROUTINE comment coverage (90% minimum)

echo "🔍 MANDATORY: Verifying comment coverage (100% critical/blocking, 90% routine)"
if ! /commentcheck; then
    echo "🚨 CRITICAL: Comment coverage failed - attempting recovery"
    echo "🔧 RECOVERY: Re-running comment response workflow"

    # Attempt recovery by re-running comment responses
    /commentreply || {
        echo "🚨 CRITICAL: Recovery failed - manual intervention required";
        echo "📊 DIAGNOSTIC: Check $CACHE_DIR/responses.json format";
        echo "📊 DIAGNOSTIC: Verify GitHub API permissions and rate limits";
        exit 1;
    }

    # Re-verify after recovery attempt
    /commentcheck || {
        echo "🚨 CRITICAL: Comment coverage still failing after recovery"
        cleanup_temp_files
        return 1
    }
fi

# Additional check: Verify ROUTINE comments have ≥90% coverage
ROUTINE_TOTAL=$(jq '[.responses[] | select(.category == "ROUTINE")] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)
ROUTINE_RESPONDED=$(jq '[.responses[] | select(.category == "ROUTINE" and (.response == "FIXED" or .response == "ACKNOWLEDGED" or .response == "NOT_DONE"))] | length' "$RESPONSES_FILE" 2>/dev/null || echo 0)

if [ "$ROUTINE_TOTAL" -gt 0 ]; then
    ROUTINE_PCT=$((ROUTINE_RESPONDED * 100 / ROUTINE_TOTAL))
    if [ "$ROUTINE_PCT" -lt 90 ]; then
        echo "⚠️ ROUTINE coverage: $ROUTINE_RESPONDED/$ROUTINE_TOTAL ($ROUTINE_PCT%) - below 90% target"
        echo "🔧 Attempting to process remaining ROUTINE comments..."
        /commentreply
    else
        echo "✅ ROUTINE coverage: $ROUTINE_RESPONDED/$ROUTINE_TOTAL ($ROUTINE_PCT%)"
    fi
fi

echo "✅ Comment coverage verification passed - proceeding with completion"
```

**Completion:**
```bash
# Report timing using TIMEOUT from agent launch section
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
if [ $COPILOT_DURATION -gt $TIMEOUT ]; then
    echo "⚠️ Performance exceeded: $((COPILOT_DURATION / 60))m (target: $((TIMEOUT / 60))m)"
else
    echo "✅ Performance target met: $((COPILOT_DURATION / 60))m"
fi

echo "✅ COPILOT WORKFLOW COMPLETED SUCCESSFULLY"
cleanup_temp_files
/guidelines
```

## 🚨 Agent Boundaries

**Critical Rule**: Agent handles file operations, Orchestrator handles GitHub API. See Architecture section for details.

## 🎯 SUCCESS CRITERIA

**SUCCESS LEVELS:**

**✅ SAFE TO MERGE:**
- Critical bugs fixed: 100% (or 0 critical bugs found)
- Blocking issues fixed: 100% (or 0 blocking issues found)
- Routine issues responded: ≥90%
- All tests passing
- 100% comment response rate with action details

**⚠️ NEEDS REVIEW:**
- Critical bugs fixed: 100%
- Blocking issues fixed: <100% with documented reasons
- Routine issues responded: <90%
- Some tests pending
- 100% comment response rate

**❌ NOT READY:**
- Critical bugs unfixed: ANY
- Blocking issues unfixed: >20%
- Routine issues responded: <80%
- Tests failing
- Comment response rate: <100%

### 🚨 GitHub API Reply Requirements

**"100% reply rate" means ACTUAL GitHub API POST calls, not just responses.json tracking.**

Every comment MUST receive an actual GitHub reply via the appropriate API endpoint:

| Comment Type | Source | API Endpoint for Reply |
|--------------|--------|----------------------|
| **Inline review comments** | `gh api repos/.../pulls/{pr}/comments` | `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies -X POST -f body="..."` |
| **General issue comments** | `gh api repos/.../issues/{pr}/comments` | `gh api repos/{owner}/{repo}/issues/{pr}/comments -X POST -f body="..."` |
| **Review summary comments** | `gh pr view --json reviews` | Reply via inline comment on same review thread |

**Common Failure Mode (AVOID THIS):**
```
❌ WRONG: Track comment in responses.json → Post summary comment → Done
✅ RIGHT: Track comment in responses.json → Post DIRECT REPLY to that specific comment → Done
```

**Reply Patterns:**
- General comments: `gh api repos/{owner}/{repo}/issues/{pr}/comments -X POST -f body="..."`
- Inline comments: `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -X POST -f body="..."`
- Always post DIRECT REPLY to the specific comment, not a summary comment
- Verify ALL comments (human AND bot) received actual GitHub API replies

## Response Data Format

See `.claude/commands/_copilot_reference.md` for the complete response JSON schema, examples, and quality standards.
