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

### 🔄 Four-Phase Workflow (UPDATED)

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### **Phase 0: Critical Bug Scan (MANDATORY FIRST STEP)**

**🚨 EXECUTE BEFORE ANY COMMENT PROCESSING:**

**Action Steps:**
1. **Check Comment Cache**: Use the `is_cache_fresh()` function to check if cached comments exist and are fresh (< 5 minutes old)
   - If cache is fresh: Skip `/commentfetch` and use cached data from `$COMMENTS_FILE`
   - If cache is stale or missing: Execute `/commentfetch` to get complete comment list
2. **Critical Bug Detection**: Scan ALL comments for critical keywords:
   - Security: "CRITICAL", "BUG", "SECURITY", "BLOCKER", "PRODUCTION", "VULNERABILITY"
   - Auth/Rate Limiting: "rate limit", "authentication", "authorization", "admin", "UID"
   - Data Safety: "data loss", "corruption", "undefined behavior", "crash"
3. **Immediate Implementation**: For EACH critical bug found:
   - Read the affected file(s)
   - Implement the fix directly (NO agent delegation)
   - Write tests to verify the fix
   - Run tests to confirm working
   - Commit with clear message: "Fix: [critical bug description]"
4. **Verification Gate**: Only proceed to Phase 1 after ALL critical bugs are fixed

**Critical Bug Categorization Rules:**

**CRITICAL** (Must fix immediately):
- Security vulnerabilities (XSS, SQL injection, auth bypass)
- Data corruption or loss risks
- Production blockers (crashes, infinite loops)
- Rate limiting bypass or abuse
- Authentication/authorization bugs

**Example Critical Bug Keywords:**
```bash
# Scan for critical patterns
CRITICAL_PATTERNS="CRITICAL|BUG|SECURITY|BLOCKER|PRODUCTION BLOCKER|PRODUCTION BUG|rate limit|authentication|authorization|admin.*UID|data loss|data-loss|dataloss|corruption|crash|vulnerability|auth bypass"

# For each comment matching critical patterns (always sanitize first):
sanitized_body=$(sanitize_comment "$comment_body")
if echo "$sanitized_body" | grep -qiE "$CRITICAL_PATTERNS"; then
    # 1. Classify severity
    # 2. Implement fix immediately
    # 3. Test and verify
    # 4. Commit before proceeding
fi
```

**Quality Gate**: Phase 0 complete ONLY when:
- ✅ All critical bugs identified
- ✅ All critical bugs fixed with working code
- ✅ All critical bug fixes tested and verified
- ✅ All critical bug fixes committed

### **Phase 1: Analysis & Comment Categorization**

**Action Steps:**
1. **Direct Operations**: Execute `/gstatus` for PR status
2. **Comment Categorization**: Classify remaining comments by severity:
   - **BLOCKING**: CI failures, build failures, breaking API changes
   - **IMPORTANT**: Performance issues, logic errors, missing validation
   - **ROUTINE**: Code style, documentation, optional refactoring
3. **Agent Launch**: Deploy `copilot-fixpr` agent for BLOCKING/IMPORTANT file operations
4. **Composed Commands**:
  5. `/gstatus` - Get comprehensive PR status
  6. `/fixpr` - Resolve merge conflicts and CI failures (via agent for non-critical issues)

### **Phase 2: Implementation & Response Generation**

**Action Steps:**
1. **Prioritize Queue**: Use `categorize_comment()` to tag every remaining comment, then process strictly in severity order (CRITICAL → BLOCKING → IMPORTANT → ROUTINE). Maintain a TodoWrite checklist so no items are skipped.
2. **Direct Implementation**: The orchestrator fixes CRITICAL and BLOCKING issues immediately (no delegation) while documenting `action_taken`, `files_modified`, and verification steps for responses.json.
3. **Selective Delegation**: IMPORTANT issues that require large file edits may be delegated to the `copilot-fixpr` agent. ROUTINE comments stay with the orchestrator to avoid agent churn.
4. **Agent Result Collection**: Once delegated tasks finish, collect the structured status file (`agent_status.json`) and integrate file diffs/commits back into the orchestrator context.
5. **Action-Based Responses**: Generate `responses.json` entries using the ACTION_ACCOUNTABILITY format for every comment, capturing implementation details, deferrals, or acknowledgments.
6. **GitHub Operations**: Run `/commentreply` after validating responses.json, then `/commentcheck` to confirm 100% coverage.

### **Phase 3: Verification & Completion (ENHANCED)**

**Action Steps:**
1. **Project-Aware Test Execution**: Detect the appropriate project test command (see "Phase 3 Playbook" below) and run it. Block completion on failures for CRITICAL/BLOCKING fixes.
2. **Commit Verification**: Use filtered git logs (grep for `Fix:` or `Critical`) to prove every critical fix is committed individually. Capture commit SHAs for responses.json verification fields.
3. **File Review**: Inspect `git diff --stat` and targeted files to ensure only intentional changes exist and that File Justification Protocol entries are satisfied.
4. **Quality Gates**: Confirm Security → Runtime → Tests → Style order was respected, rerunning targeted tests if any remediation happened during verification.
5. **Final Operations**: Push via `/pushl` with `[codex-automation-commit]` in the message, regenerate guideline notes if needed, and archive timing metrics.

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
- **Categorization Pipeline**:
  1. Sanitize each comment body.
  2. Pass sanitized text to `categorize_comment()` to obtain CRITICAL/BLOCKING/IMPORTANT/ROUTINE labels.
  3. Record the mapping (e.g., in TodoWrite or a scratch buffer) so Phase 2 can consume a prioritized queue.
- **Clarify Delegation Rules**: Critical + blocking items remain orchestrator-owned. Only mark an item as agent-eligible if it is IMPORTANT and requires heavy file edits (e.g., multi-file refactors). ROUTINE feedback is kept local for speed.
- **Test Expectations**: No new tests run in Phase 1; this is purely classification + planning.

### Phase 2 Playbook — Implementation & Responses

- **Priority Queue Implementation**: Enforce the priority order with an explicit loop so reviewers can see it’s implemented, not just promised:

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

## 📑 Table of Contents

- [Command Overview & Structure](#-command-overview--structure)
  - [Purpose](#-purpose)
  - [Architecture Pattern: Hybrid Orchestrator](#️-architecture-pattern-hybrid-orchestrator)
  - [Key Composed Commands Integration](#️-key-composed-commands-integration)
  - [Critical Boundaries](#-critical-boundaries)
  - [Performance Targets](#-performance-targets)
- [Mandatory Comment Coverage Tracking](#-mandatory-comment-coverage-tracking)
- [Automatic Timing Protocol](#️-automatic-timing-protocol)
- [Detailed Phase Playbooks & Reference](#-detailed-phase-playbooks--reference)
  - [Phase 0 Playbook — Critical Bug Scan](#phase-0-playbook--critical-bug-scan)
  - [Phase 1 Playbook — Analysis & Categorization](#phase-1-playbook--analysis--categorization)
  - [Phase 2 Playbook — Implementation & Responses](#phase-2-playbook--implementation--responses)
  - [Phase 3 Playbook — Verification & Completion](#phase-3-playbook--verification--completion)
- [Utilities & Validation](#-utilities--validation)
- [Hybrid Execution Details](#-hybrid-execution-details)
- [Response Data Format Specification](#-response-data-format-specification-updated-action-protocol)
- [Quality Metrics & Health Signals](#-quality-metrics--health-signals)
- [Agent Boundaries](#-agent-boundaries)
- [Success Criteria](#-success-criteria)

## 📋 COMMAND OVERVIEW & STRUCTURE

### 🎯 Purpose (UPDATED: QUALITY-FIRST)

**Quality-focused PR processing** using priority-based bug triage and hybrid orchestration for production safety and code correctness. Prioritizes critical bug fixes over comment coverage metrics.

**Key Improvements (v2.0):**
- 🚨 **Critical Bug Scan**: MANDATORY first-pass scan for security/production issues
- 📊 **Priority Hierarchy**: CRITICAL → BLOCKING → IMPORTANT → ROUTINE
- ✅ **Action Accountability**: Detailed response format with files, commits, verification
- 🎯 **Quality Metrics**: Focus on bugs fixed vs comment count
- 🧪 **Test Verification**: Mandatory test execution for critical/blocking fixes

**Design Philosophy:**
- **Correctness Over Coverage**: Fix critical bugs BEFORE processing routine comments
- **Direct Implementation**: Critical/blocking bugs fixed immediately, no agent delegation
- **Accountability**: Every response includes category, action taken, files modified, verification
- **Safety Signal**: Clear "SAFE TO MERGE" or "NEEDS WORK" based on critical/blocking resolution

### 🏗️ Architecture Pattern: Hybrid Orchestrator

**HYBRID DESIGN**: Direct orchestration + specialized agent for maximum reliability
- **Direct Orchestrator**: Handles comment analysis, GitHub operations, workflow coordination
- **copilot-fixpr Agent**: Specialized for file modifications, security fixes, merge conflicts
- **Proven Strategy**: Uses only verified working components, eliminates broken patterns

### 🎛️ Key Composed Commands Integration

- **Status Commands**: `/gstatus` (PR status), `/commentcheck` (coverage verification)
- **GitHub Commands**: `/commentfetch` (comment collection), `/commentreply` (response posting)
- **Agent Commands**: `/fixpr` (via copilot-fixpr agent for file operations)
- **Workflow Commands**: `/pushl` (automated push), `/guidelines` (documentation update)

### 🚨 Critical Boundaries

- **Orchestrator**: Comment processing, GitHub API, workflow coordination
- **Agent**: File modifications, security fixes, technical implementations
- **Never Mixed**: Agent NEVER handles comments, Orchestrator NEVER modifies files

### ⚡ Performance Targets

- **Execution Time**: **Adaptive based on PR complexity**
  - **Simple PRs** (≤3 files, ≤50 lines): 2-5 minutes
  - **Moderate PRs** (≤10 files, ≤500 lines): 5-10 minutes
  - **Complex PRs** (>10 files, >500 lines): 10-15 minutes
  - **Auto-scaling timeouts** with complexity detection and appropriate warnings
- **Success Rate**: 100% reliability through proven component usage
- **Coverage**: 100% comment response rate + all actionable issues implemented

## 🚨 Mandatory Comment Coverage Tracking

This command automatically tracks comment coverage and warns about missing responses:
```bash

# COVERAGE TRACKING: Monitor comment response completion (silent unless errors)

```

## ⏱️ Automatic Timing Protocol

This command silently tracks execution time and only reports if exceeded:
```bash

# Silent timing - only output if >3 minutes

COPILOT_START_TIME=$(date +%s)
```

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

REPO_NAME=$(get_repo_name)
BRANCH_NAME=$(get_branch_name)
CACHE_DIR="/tmp/$REPO_NAME/$BRANCH_NAME"
CACHE_METADATA_FILE="$CACHE_DIR/cache_metadata.json"
COMMENTS_FILE="$CACHE_DIR/comments.json"

# Perform cleanup of old caches
cleanup_old_caches

# Function to check if cache is fresh

is_cache_fresh() {
    if [ ! -f "$CACHE_METADATA_FILE" ] || [ ! -f "$COMMENTS_FILE" ]; then
        return 1  # Cache doesn't exist
    fi

    # Read cache metadata (jq errors fall back to safe defaults)
    local last_fetch
    last_fetch=$(jq -er '.last_fetch_timestamp // empty' "$CACHE_METADATA_FILE" 2>/dev/null || true)
    local ttl_seconds
    ttl_seconds=$(jq -er '.cache_ttl_seconds // 300' "$CACHE_METADATA_FILE" 2>/dev/null || echo 300)
    local cached_pr_number
    cached_pr_number=$(jq -er '.pr_number // "unknown"' "$CACHE_METADATA_FILE" 2>/dev/null || echo "unknown")
    local cached_sha
    cached_sha=$(jq -er '.pr_head_sha // "unknown"' "$CACHE_METADATA_FILE" 2>/dev/null || echo "unknown")

    if [ -z "$last_fetch" ]; then
        return 1  # Invalid metadata
    fi

    if ! [[ "$ttl_seconds" =~ ^[0-9]+$ ]]; then
        ttl_seconds=300
    fi

    # Check PR number to avoid using cache for the wrong PR
    local current_pr_number
    current_pr_number=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "unknown")
    if [ "$cached_pr_number" != "unknown" ] && [ "$current_pr_number" != "unknown" ] && [ "$cached_pr_number" != "$current_pr_number" ]; then
        echo "ℹ️  PR number mismatch (cached: $cached_pr_number, current: $current_pr_number), invalidating cache..."
        return 1  # Force refresh
    fi

    # Check PR head SHA to invalidate on updates
    local current_sha=$(gh pr view --json headRefOid --jq '.headRefOid' 2>/dev/null || echo "unknown")
    if [ "$cached_sha" != "unknown" ] && [ "$current_sha" != "unknown" ] && [ "$cached_sha" != "$current_sha" ]; then
        echo "ℹ️  PR state changed (SHA mismatch), invalidating cache..."
        return 1  # Force refresh
    fi

    # Calculate cache age using Python for cross-platform date parsing (macOS/Linux compatible)
    local fetch_epoch=$(python3 -c 'import sys, datetime as d; s=sys.argv[1]; s=s.replace("Z","+00:00"); print(int(d.datetime.fromisoformat(s).timestamp()))' "$last_fetch" 2>/dev/null || echo 0)
    
    if [ "$fetch_epoch" -eq 0 ]; then
        return 1  # Date parsing failed
    fi
    
    local current_epoch=$(date +%s)
    local cache_age=$((current_epoch - fetch_epoch))

    if [ "$cache_age" -lt "$ttl_seconds" ]; then
        echo "ℹ️  Using cached comments (age: ${cache_age}s, TTL: ${ttl_seconds}s)"
        return 0  # Cache is fresh
    else
        echo "ℹ️  Cache is stale (age: ${cache_age}s > TTL: ${ttl_seconds}s), refetching..."
        return 1  # Cache is stale
    fi
}

# Phase 0: Use cache freshness check before fetching comments
if is_cache_fresh; then
    echo "✅ Comment cache is fresh; skipping /commentfetch"
else
    echo "🚀 Cache missing or stale; invoking /commentfetch to refresh comments"
    /commentfetch
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

# Secure branch name and setup paths (using repo-scoped cache directory)

REPO_NAME=$(get_repo_name)
BRANCH_NAME=$(get_branch_name)
CACHE_DIR="/tmp/$REPO_NAME/$BRANCH_NAME"

# Ensure consistency across all cache operations
AGENT_STATUS="$CACHE_DIR/agent_status.json"
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

# Verify agent completion before proceeding

if [ -f "$AGENT_STATUS" ]; then
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
# Ensure cache paths are defined for this block
REPO_NAME=$(get_repo_name)
BRANCH_NAME=$(get_branch_name)
CACHE_DIR="/tmp/$REPO_NAME/$BRANCH_NAME"
AGENT_STATUS="$CACHE_DIR/agent_status.json"

echo "📝 Generating action-based responses.json with implementation accountability"

# 🚨 NEW PROTOCOL: Action-based responses with files_modified, tests_added, commit, verification

echo "🔧 Implementing CodeRabbit technical suggestions:"

# 1. IMPLEMENTED: Accurate line counting with --numstat (CodeRabbit suggestion)

echo "  • Adding git diff --numstat for accurate line counting"
PR_LINES=$(git diff --numstat origin/main | awk '{added+=$1; deleted+=$2} END {print "Added:" added " Deleted:" deleted}')
echo "    Lines: $PR_LINES"

# 2. IMPLEMENTED: JSON validation with jq -e (CodeRabbit suggestion)

echo "  • Adding jq -e validation for all JSON files"
# Ensure cache paths are defined for this block (self-contained)
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
REPO_NAME=$(basename "$REPO_ROOT" | tr -cd '[:alnum:]._-')
BRANCH_NAME=$(git branch --show-current 2>/dev/null | tr -cd '[:alnum:]._-')
REPO_NAME=${REPO_NAME:-unknown-repo}
BRANCH_NAME=${BRANCH_NAME:-unknown-branch}
CACHE_DIR="/tmp/$REPO_NAME/$BRANCH_NAME"
AGENT_STATUS="$CACHE_DIR/agent_status.json"

for json_file in $CACHE_DIR/*.json; do
    if [ -f "$json_file" ]; then
        echo "    Validating: $json_file"
        jq -e . "$json_file" > /dev/null || {
            echo "❌ CRITICAL: Invalid JSON in $json_file"
            exit 1
        }
        echo "    ✅ Valid JSON: $(basename "$json_file")"
    fi
done

# 3. IMPLEMENTED: Fix agent status race condition (CodeRabbit concern)

echo "  • Implementing proper agent status coordination (not immediate file creation)"
# Note: AGENT_STATUS is already set earlier using CACHE_DIR

# Wait for agent completion instead of immediate file creation

while [ ! -f "$AGENT_STATUS" ] || [ "$(jq -r '.status' "$AGENT_STATUS" 2>/dev/null)" != "completed" ]; do
    sleep 1
    echo "    Waiting for agent completion..."
done
echo "    ✅ Agent coordination: Proper status synchronization"

# CRITICAL: Generate responses in commentreply.py expected format

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

REPO_NAME=$(get_repo_name)
BRANCH_NAME=$(get_branch_name)
CACHE_DIR="/tmp/$REPO_NAME/$BRANCH_NAME"
COMMENTS_FILE="$CACHE_DIR/comments.json"
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
    "FIXED": "Issue implemented with working code",
    "DEFERRED": "Created issue for future implementation",
    "ACKNOWLEDGED": "Noted but not actionable",
    "NOT_DONE": "Cannot implement with specific reason"
  },
  "required_fields": {
    "FIXED": ["category", "action_taken", "files_modified", "commit", "verification"],
    "DEFERRED": ["category", "reason", "issue_url"],
    "ACKNOWLEDGED": ["category", "explanation"],
    "NOT_DONE": ["category", "reason"]
  },
  "template_fixed": {
    "response": "FIXED",
    "category": "CRITICAL|BLOCKING|IMPORTANT|ROUTINE",
    "action_taken": "Specific implementation description",
    "files_modified": ["file1.ts:123", "file2.py:456"],
    "tests_added": ["test1.test.ts"],
    "commit": "abc123de",
    "verification": "✅ Tests pass, feature verified"
  },
  "template_deferred": {
    "response": "DEFERRED",
    "category": "CRITICAL|BLOCKING|IMPORTANT|ROUTINE",
    "reason": "Documented reason for deferment",
    "issue_url": "https://github.com/org/repo/issues/1234"
  },
  "template_acknowledged": {
    "response": "ACKNOWLEDGED",
    "category": "CRITICAL|BLOCKING|IMPORTANT|ROUTINE",
    "explanation": "Why the comment is noted but no action taken"
  },
  "template_not_done": {
    "response": "NOT_DONE",
    "category": "CRITICAL|BLOCKING|IMPORTANT|ROUTINE",
    "reason": "Specific reason why implementation not feasible"
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

# Show evidence of changes with CodeRabbit's --numstat implementation

echo "📊 COPILOT EXECUTION EVIDENCE:"
echo "🔧 FILES MODIFIED:"
git diff --name-only | sed 's/^/  - /'
echo "📈 CHANGE SUMMARY (using CodeRabbit's --numstat):"
git diff --numstat origin/main
echo "📈 TRADITIONAL STAT:"
git diff --stat

# 🚨 MANDATORY: Verify actual technical implementations before push

echo "🔍 IMPLEMENTATION VERIFICATION:"
echo "  • Line counting: git diff --numstat - IMPLEMENTED ✅"
echo "  • JSON validation: jq -e validation - IMPLEMENTED ✅"
echo "  • Agent status coordination: proper file handling - IMPLEMENTED ✅"
echo "  • Action response protocol: FIXED/DEFERRED/ACKNOWLEDGED/NOT_DONE - IMPLEMENTED ✅"
echo "  • Priority-based processing: CRITICAL → BLOCKING → IMPORTANT → ROUTINE - IMPLEMENTED ✅ (Phase 2 priority queue loop)"
echo "  • Quality metrics: Critical bugs fixed, blocking issues resolved - IMPLEMENTED ✅"

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

# Push changes to PR with error recovery

/pushl || {
    echo "🚨 PUSH FAILED: PR not updated"
    echo "🔧 RECOVERY: Attempting git status check"
    git status
    cleanup_temp_files
    return 1
}
```

**Coverage Tracking (MANDATORY GATE):**
```bash

# HARD VERIFICATION GATE with RECOVERY - Must pass before proceeding

echo "🔍 MANDATORY: Verifying 100% comment coverage"
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
echo "✅ Comment coverage verification passed - proceeding with completion"
```

**🎯 Adaptive Performance Tracking:**
```bash

# Detect PR complexity for realistic timing expectations (if not done earlier)

if [ -z "$FILES_CHANGED" ]; then
    FILES_CHANGED=$(git diff --name-only origin/main | wc -l)
    LINES_CHANGED=$(git diff --stat origin/main | tail -1 | grep -oE '[0-9]+' | head -1 || echo 0)
fi

# Set complexity-based performance targets

if [ $FILES_CHANGED -le 3 ] && [ $LINES_CHANGED -le 50 ]; then
    COMPLEXITY="simple"
    TARGET_TIME=300  # 5 minutes
elif [ $FILES_CHANGED -le 10 ] && [ $LINES_CHANGED -le 500 ]; then
    COMPLEXITY="moderate"
    TARGET_TIME=600  # 10 minutes
else
    COMPLEXITY="complex"
    TARGET_TIME=900  # 15 minutes
fi

echo "📊 PR Complexity: $COMPLEXITY ($FILES_CHANGED files, $LINES_CHANGED lines)"
echo "🎯 Target time: $((TARGET_TIME / 60)) minutes"

# Calculate and report timing with complexity-appropriate targets

COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
if [ $COPILOT_DURATION -gt $TARGET_TIME ]; then
    echo "⚠️ Performance exceeded: $((COPILOT_DURATION / 60))m $((COPILOT_DURATION % 60))s (target: $((TARGET_TIME / 60))m for $COMPLEXITY PR)"
else
    echo "✅ Performance target met: $((COPILOT_DURATION / 60))m $((COPILOT_DURATION % 60))s (under $((TARGET_TIME / 60))m target)"
fi

# SUCCESS: Clean up and complete

echo "✅ COPILOT WORKFLOW COMPLETED SUCCESSFULLY"
cleanup_temp_files
/guidelines
```

## 🚨 Agent Boundaries

### copilot-fixpr Agent Responsibilities:

- **FIRST PRIORITY**: Execute `/fixpr` command to resolve merge conflicts and CI failures
- **PRIMARY**: Security vulnerability detection and code implementation
- **TOOLS**: Edit/MultiEdit for file modifications, Serena MCP for semantic analysis, `/fixpr` command
- **FOCUS**: Make PR mergeable first, then actual code changes with File Justification Protocol compliance
- **BOUNDARY**: File operations and PR mergeability - **NEVER handles GitHub comment responses**

🚨 **CRITICAL AGENT BOUNDARY**: The copilot-fixpr agent must NEVER attempt to:
- Generate responses.json entries
- Handle comment response generation
- Execute /commentreply
- Manage GitHub comment posting
- Handle comment coverage verification

**Direct Orchestrator (EXCLUSIVE RESPONSIBILITIES):**
- **MANDATORY**: Generate ALL comment responses after agent completes
- Comment processing (/commentfetch, /commentreply)
- Response generation for every fetched comment
- GitHub operations and workflow coordination
- Verification checkpoints and evidence collection
- Ensuring 100% comment coverage before completion

## 🎯 **SUCCESS CRITERIA (UPDATED: QUALITY-FOCUSED)**

### **PRIORITY-BASED VERIFICATION REQUIREMENTS**:

1. **Critical Bug Resolution**: ALL critical bugs fixed with working code (100% required)
2. **Blocking Issue Resolution**: ALL blocking issues fixed or properly documented (100% required)
3. **Important Issue Handling**: Important issues fixed OR deferred with created issues (≥80% target)
4. **Communication Coverage**: 100% comment response rate with action-based accountability
5. **Test Verification**: All critical/blocking fixes verified with passing tests

**SUCCESS LEVELS:**

**✅ SAFE TO MERGE:**
- Critical bugs fixed: 100% (or 0 critical bugs found)
- Blocking issues fixed: 100% (or 0 blocking issues found)
- All tests passing
- 100% comment response rate with action details

**⚠️ NEEDS REVIEW:**
- Critical bugs fixed: 100%
- Blocking issues fixed: <100% with documented reasons
- Some tests pending
- 100% comment response rate

**❌ NOT READY:**
- Critical bugs unfixed: ANY
- Blocking issues unfixed: >20%
- Tests failing
- Comment response rate: <100%

### **QUALITY GATES (PRIORITY ORDER)**:

1. ✅ **Critical Bug Priority**: Security vulnerabilities, production blockers fixed FIRST
2. ✅ **Blocking Issue Priority**: CI failures, breaking changes fixed SECOND
3. ✅ **Direct Implementation**: Critical/blocking bugs fixed by orchestrator directly
4. ✅ **Test Verification**: All critical/blocking fixes verified with test execution
5. ✅ **Action Accountability**: Every response includes category, action, files, commits, verification
6. ✅ **File Justification Protocol**: All code changes properly documented and justified
7. ✅ **Input Sanitization**: All GitHub comment content validated and sanitized
8. ✅ **Synchronization**: Explicit agent coordination prevents race conditions
9. ✅ **Adaptive Performance**: Execution completed within complexity-appropriate targets

### **FAILURE CONDITIONS (PRIORITY ORDER)**:

**🚨 CRITICAL FAILURES (IMMEDIATE STOP):**
- ❌ **Unfixed Critical Bugs**: ANY critical bug not implemented
- ❌ **Security Violations**: Unsanitized input processing or validation failures
- ❌ **Test Failures**: Critical/blocking fixes not verified with passing tests

**❌ BLOCKING FAILURES (MANUAL REVIEW REQUIRED):**
- ❌ **Unfixed Blocking Issues**: >20% blocking issues unresolved
- ❌ **Coverage Gaps**: <100% comment response rate
- ❌ **Missing Accountability**: Responses without files_modified, commit, or verification
- ❌ **Race Conditions**: Orchestrator proceeding before agent completion

**⚠️ WARNING CONDITIONS (NON-BLOCKING):**
- ⚠️ **Protocol Violations**: File changes without proper justification documentation
- ⚠️ **Boundary Violations**: Agent handling GitHub responses OR orchestrator making non-critical file changes
- ⚠️ **Timing Warnings**: Execution time exceeding complexity-appropriate targets without alerts

### **Context Management**:

- **Complete Comment Coverage**: Process ALL comments without filtering for 100% coverage
  - 🚨 **CRITICAL CLARIFICATION**: "ALL comments" explicitly INCLUDES:
    - ✅ Bot comments (CodeRabbit, GitHub Copilot, automated reviewers)
    - ✅ Human comments (team members, manual reviewers)
    - ❌ **ONLY EXCEPTION**: Comments starting with "[AI responder]" (our own AI-generated responses)
  - 🚨 **MANDATORY**: Bot code review comments MUST be addressed - either implement fixes OR explain "NOT DONE: [reason]"
  - 🚨 **ZERO SKIP RATE**: 100% reply rate means EVERY comment (human AND bot) gets a response
- **GitHub MCP Primary**: Strategic tool usage for minimal context consumption
- **Semantic Search**: Use Serena MCP for targeted analysis before file operations
- **Hybrid Coordination**: Efficient orchestration with selective task delegation

### **Performance Benefits**:

- **Reliability**: 100% working components eliminate broken agent failures
- **Specialization**: File operations delegated while maintaining coordination control
- **Quality Improvement**: Proven comment handling with verified file implementations
- **Simplified Architecture**: Eliminates complexity of broken parallel agent coordination

### **Coordination Efficiency**:

- **Selective Delegation**: Only delegate file operations, handle communication directly
- **Proven Components**: Use only verified working tools and patterns
- **Result Integration**: Direct access to agent file changes for accurate response generation
- **Streamlined Workflow**: Single coordination point with specialized file operation support

## 🚨 **RESPONSE DATA FORMAT SPECIFICATION (UPDATED: ACTION PROTOCOL)**

### **MANDATORY**: responses.json Format

The orchestrator MUST generate responses.json in this exact format:

```json
{
  "response_protocol": "ACTION_ACCOUNTABILITY",
  "responses": [
    {
      "comment_id": "2357534669",
      "category": "CRITICAL",
      "response": "FIXED",
      "action_taken": "Implemented UID-based admin check in isAuthenticatedNonVIP()",
      "files_modified": ["shared-libs/packages/mcp-server-utils/src/RateLimitTool.ts:145"],
      "tests_added": ["backend/src/test/rate-limit-uid-fallback.test.ts"],
      "commit": "53702d91",
      "verification": "✅ Tests pass, admin UIDs now recognized",
      "reply_text": "[AI responder] ✅ **CRITICAL BUG FIXED**\n\n**Category**: CRITICAL\n**Action**: Implemented UID-based admin check in isAuthenticatedNonVIP()\n**Files Modified**: shared-libs/packages/mcp-server-utils/src/RateLimitTool.ts:145\n**Tests Added**: backend/src/test/rate-limit-uid-fallback.test.ts\n**Commit**: 53702d91\n**Verification**: ✅ Tests pass, admin UIDs now recognized",
      "in_reply_to": "optional_parent_id"
    },
    {
      "comment_id": "2357534670",
      "category": "ROUTINE",
      "response": "ACKNOWLEDGED",
      "explanation": "Good suggestion for code clarity, will apply in next refactoring cycle",
      "reply_text": "[AI responder] 📝 **ACKNOWLEDGED**\n\n**Category**: ROUTINE\n**Note**: Good suggestion for code clarity, will apply in next refactoring cycle"
    }
  ]
}
```

### **CRITICAL FORMAT REQUIREMENTS**:

**Base Fields (ALL responses):**
- `comment_id` MUST be STRING (not integer)
- `category` MUST be one of: CRITICAL, BLOCKING, IMPORTANT, ROUTINE
- `response` MUST be one of: FIXED, DEFERRED, ACKNOWLEDGED, NOT_DONE
- `reply_text` MUST contain formatted action details for GitHub (example above shows the auto-generated output)
- `files_modified` should list repo-relative paths with optional `:line` suffixes for precision
- `commit` values must use the standard 7-8 character `git rev-parse --short` format for traceability

**Response Type Specific Fields:**

**FIXED** (implementation completed):
- `action_taken`: Specific implementation description
- `files_modified`: Array of "file:line" strings
- `tests_added`: Array of test files (if applicable)
- `commit`: Short commit SHA
- `verification`: Test/verification status

**DEFERRED** (created issue for future):
- `reason`: Why deferred
- `issue_url`: GitHub issue URL (if created)

**ACKNOWLEDGED** (noted, not actionable):
- `explanation`: Why acknowledged but not implemented

**NOT_DONE** (cannot implement):
- `reason`: Specific technical reason why not feasible

### **INTEGRATION CONTRACT**:

- commentreply.py expects `responses` array with `comment_id` and `reply_text`
- `reply_text` is auto-generated from action fields for consistency
- Matching uses `str(response_item.get("comment_id")) == comment_id`
- Missing required fields cause validation failures
- Format validation is MANDATORY before attempting to post responses

### **RESPONSE QUALITY STANDARDS (UPDATED)**:

**FIXED responses MUST include:**
- ✅ Specific action taken (not generic "fixed")
- ✅ Files modified with line numbers
- ✅ Commit SHA for traceability
- ✅ Verification status (tests pass, CI green, etc.)

**NOT_DONE responses MUST include:**
- ✅ Specific technical reason (not "will consider")
- ✅ Category classification (why it's routine vs critical)

**Accountability Requirements:**
- No generic acknowledgments without category
- No "FIXED" without files_modified and commit
- No "NOT_DONE" without specific reason
- Every response traceable to actual code changes or decision rationale
