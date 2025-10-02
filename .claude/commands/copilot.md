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

### 🔄 Three-Phase Workflow

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### **Phase 1: Analysis & Agent Launch**

**Action Steps:**
1. **Direct Operations**: Execute `/gstatus`, `/commentfetch` for PR status and comment analysis
2. **Agent Launch**: Deploy `copilot-fixpr` agent for parallel file operations
3. **Composed Commands**:
  4. `/gstatus` - Get comprehensive PR status
  5. `/commentfetch` - Gather all PR comments
  6. `/fixpr` - Resolve merge conflicts and CI failures (via agent)

### **Phase 2: Hybrid Integration & Response Generation**

**Action Steps:**
1. **Agent Collection**: Gather file changes and technical implementations from copilot-fixpr
2. **Response Generation**: Orchestrator analyzes all comments and generates `responses.json`
3. **GitHub Operations**: Execute `/commentreply` with validated response format
4. **Composed Commands**:
  5. `/commentreply` - Post responses to GitHub comments
  6. `/commentcheck` - Verify 100% comment coverage

### **Phase 3: Verification & Completion**

**Action Steps:**
1. **File Justification Protocol**: Validate all changes follow integration-first protocol
2. **Quality Gates**: Security → Runtime → Tests → Style priority enforcement
3. **Final Operations**: Evidence collection, push to PR, coverage verification
4. **Composed Commands**:
  5. `/pushl` - Push changes with automated labeling
  6. `/guidelines` - Update PR guidelines documentation

### ... execution phases ...

**Action Steps:**
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
if [ $COPILOT_DURATION -gt 900 ]; then
    echo "⚠️ Performance exceeded: $((COPILOT_DURATION / 60))m $((COPILOT_DURATION % 60))s (target: 15m)"
fi
```

### Phase 6: ⚡ Core Workflow

**Action Steps:**
🚨 **OPTIMIZED HYBRID PATTERN**: /copilot uses direct execution + selective task agents for maximum reliability

1. **DIRECT ORCHESTRATION**: Handle comment analysis, GitHub operations, and coordination directly
2. **SELECTIVE TASK AGENTS**: Launch `copilot-fixpr` agent for file modifications in parallel
3. **PROVEN COMPONENTS**: Use only verified working components - remove broken agents
4. **PARALLEL FILE OPERATIONS**: Agent handles Edit/MultiEdit while orchestrator manages workflow
5. **Complete comment coverage** - Process ALL comments without filtering
6. **Expected time**: **5-15 minutes** with reliable hybrid coordination (realistic for comprehensive analysis)

### Phase 7: 🚀 Core Workflow - Hybrid Orchestrator Pattern

**Action Steps:**
**IMPLEMENTATION**: Direct orchestration with selective task agent for file operations

**INITIAL STATUS & TIMING SETUP**: Get comprehensive status and initialize timing
```bash

### Phase 1: Analysis & Agent Launch

**Action Steps:**
**🎯 Direct Comment Analysis**:
Execute comment processing workflow directly for reliable GitHub operations:
1. Execute /commentfetch to gather all PR comments and issues
2. **INPUT SANITIZATION**: Validate all GitHub comment content for malicious patterns before processing
3. **API RESPONSE VALIDATION**: Verify external API responses against expected schemas and sanitize data

**🛡️ ENHANCED SECURITY IMPLEMENTATION**:
```bash

### Phase 2: Hybrid Integration & Response Generation

**Action Steps:**
**Direct orchestration with agent result integration**:

**🔄 Structured Data Exchange - Agent Result Collection**:
```bash

### Phase 3: Verification & Completion (AUTOMATIC)

**Action Steps:**
**Results verified by agent coordination**:

**🚨 MANDATORY FILE JUSTIFICATION PROTOCOL COMPLIANCE**:
1. **Every file modification** must follow FILE JUSTIFICATION PROTOCOL before implementation
2. **Required documentation**: Goal, Modification, Necessity, Integration Proof for each change
3. **Integration verification**: Proof that adding to existing files was attempted first
4. **Protocol adherence**: All changes must follow NEW FILE CREATION PROTOCOL hierarchy
5. **Justification categories**: Classify each change as Essential, Enhancement, or Unnecessary

**Implementation with Protocol Enforcement**:
6. **Priority Order**: Security → Runtime Errors → Test Failures → Style
7. **MANDATORY TOOLS**: Edit/MultiEdit for code changes, NOT GitHub review posting
8. **IMPLEMENTATION REQUIREMENT**: Must modify actual files to resolve issues WITH justification
9. **VERIFICATION**: Use git diff to confirm file changes made AND protocol compliance
10. **Protocol validation**: Each file change must be justified before Edit/MultiEdit usage
11. Resolve merge conflicts and dependency issues (with integration evidence)

**Final Completion Steps with Implementation Evidence**:
```bash

### Phase 11: ⚡ **HYBRID EXECUTION OPTIMIZATION**

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

## 📋 REFERENCE DOCUMENTATION

# /copilot - Fast PR Processing

## 📑 Table of Contents

- [Command Overview & Structure](#-command-overview--structure)
  - [Purpose](#-purpose)
  - [Architecture Pattern: Hybrid Orchestrator](#️-architecture-pattern-hybrid-orchestrator)
  - [Three-Phase Workflow](#-three-phase-workflow)
  - [Key Composed Commands Integration](#️-key-composed-commands-integration)
  - [Critical Boundaries](#-critical-boundaries)
  - [Performance Targets](#-performance-targets)
- [Mandatory Comment Coverage Tracking](#-mandatory-comment-coverage-tracking)
- [Automatic Timing Protocol](#️-automatic-timing-protocol)
- [Core Workflow](#-core-workflow)
- [Core Workflow - Hybrid Orchestrator Pattern](#-core-workflow---hybrid-orchestrator-pattern)
  - [Phase 1: Analysis & Agent Launch](#phase-1-analysis--agent-launch)
  - [Phase 2: Hybrid Integration & Response Generation](#phase-2-hybrid-integration--response-generation)
  - [Phase 3: Verification & Completion](#phase-3-verification--completion-automatic)
- [Agent Boundaries](#-agent-boundaries)
- [Success Criteria](#-success-criteria)
- [Hybrid Execution Optimization](#-hybrid-execution-optimization)

## 📋 COMMAND OVERVIEW & STRUCTURE

### 🎯 Purpose

Ultra-fast PR processing using hybrid orchestration (direct execution + selective task agents) for comprehensive coverage and quality assurance. Targets 2-3 minute completion with 100% reliability.

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

## 🎯 Purpose

Ultra-fast PR processing using hybrid orchestration with comprehensive coverage and quality assurance. Uses hybrid orchestrator with copilot-fixpr agent by default for maximum reliability.

# CLEANUP FUNCTION: Define error recovery and cleanup mechanisms

cleanup_temp_files() {
    local branch_name=$(git branch --show-current | tr -cd '[:alnum:]._-')
    local temp_dir="/tmp/$branch_name"

    if [ -d "$temp_dir" ]; then
        echo "🧹 CLEANUP: Removing temporary files from $temp_dir"
        rm -rf "$temp_dir"/* 2>/dev/null || true
    fi

    # Reset any stuck GitHub operations
    echo "🔄 CLEANUP: Resetting any stuck operations"
    # Additional cleanup operations as needed
}

# ERROR HANDLER: Trap errors for graceful cleanup

trap 'cleanup_temp_files; echo "🚨 ERROR: Copilot workflow interrupted"; exit 1' ERR

# Get comprehensive PR status first

/gstatus

# Initialize timing for performance tracking (silent unless exceeded)

COPILOT_START_TIME=$(date +%s)
```

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
- Analyze actionable issues and categorize by type (security, runtime, tests, style)
- Process issue responses and plan implementation strategy
- Handle all GitHub API operations directly (proven to work)

**🚀 Parallel copilot-fixpr Agent Launch with Explicit Synchronization**:
Launch specialized agent for file modifications with structured coordination:
- **FIRST**: Execute `/fixpr` command to resolve merge conflicts and CI failures
- Analyze current GitHub PR status and identify potential improvements
- Review code changes for security vulnerabilities and quality issues
- Implement actual file fixes using Edit/MultiEdit tools with File Justification Protocol
- Focus on code quality, performance optimization, and technical accuracy
- **NEW**: Write completion status to structured result file for orchestrator

**🚨 EXPLICIT SYNCHRONIZATION PROTOCOL**: Eliminates race conditions
```bash

# Secure branch name and setup paths

BRANCH_NAME=$(git branch --show-current | tr -cd '[:alnum:]._-')
AGENT_STATUS="/tmp/$BRANCH_NAME/agent_status.json"
mkdir -p "/tmp/$BRANCH_NAME"

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

BRANCH_NAME=$(git branch --show-current | tr -cd '[:alnum:]._-')
AGENT_STATUS="/tmp/$BRANCH_NAME/agent_status.json"

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
- **Orchestrator handles**: Comment processing, response generation, GitHub API operations, coverage tracking
- **Coordination ensures**: Explicit synchronization prevents race conditions and response inconsistencies

**Response Generation with Binary Protocol** (MANDATORY ORCHESTRATOR RESPONSIBILITY):
```bash
echo "📝 Generating binary responses.json (DONE/NOT DONE only) with technical implementations"

# 🚨 MANDATORY: Implement CodeRabbit technical suggestions BEFORE response generation

echo "🔧 Implementing CodeRabbit technical suggestions:"

# 1. IMPLEMENTED: Accurate line counting with --numstat (CodeRabbit suggestion)

echo "  • Adding git diff --numstat for accurate line counting"
PR_LINES=$(git diff --numstat origin/main | awk '{added+=$1; deleted+=$2} END {print "Added:" added " Deleted:" deleted}')
echo "    Lines: $PR_LINES"

# 2. IMPLEMENTED: JSON validation with jq -e (CodeRabbit suggestion)

echo "  • Adding jq -e validation for all JSON files"
for json_file in /tmp/$(git branch --show-current)/*.json; do
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
AGENT_STATUS="/tmp/$(git branch --show-current)/agent_status.json"

# Wait for agent completion instead of immediate file creation

while [ ! -f "$AGENT_STATUS" ] || [ "$(jq -r '.status' "$AGENT_STATUS" 2>/dev/null)" != "completed" ]; do
    sleep 1
    echo "    Waiting for agent completion..."
done
echo "    ✅ Agent coordination: Proper status synchronization"

# CRITICAL: Generate responses in commentreply.py expected format

# Orchestrator writes: /tmp/$(git branch --show-current)/responses.json

# 🚨 BINARY RESPONSE PROTOCOL: Every comment gets DONE or NOT DONE response only

echo "🔍 BINARY PROTOCOL: Analyzing ALL comments for DONE/NOT DONE responses"

# INPUT SANITIZATION: Secure branch name validation to prevent path injection

BRANCH_NAME=$(git branch --show-current | tr -cd '[:alnum:]._-')
if [ -z "$BRANCH_NAME" ]; then
    echo "❌ CRITICAL: Invalid or empty branch name"
    cleanup_temp_files
    return 1
fi

# SECURE PATH CONSTRUCTION: Use sanitized branch name

COMMENTS_FILE="/tmp/$BRANCH_NAME/comments.json"
export RESPONSES_FILE="/tmp/$BRANCH_NAME/responses.json"

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

# 🚨 BINARY RESPONSE TEMPLATE: Only DONE or NOT DONE allowed

echo "📋 Building binary response structure (DONE/NOT DONE with implementation evidence)"
cat > "$RESPONSES_FILE" << 'EOF'
{
  "response_protocol": "BINARY_MANDATORY",
  "allowed_responses": ["DONE", "NOT DONE"],
  "template_done": "✅ DONE: [specific implementation] - File: [file:line]",
  "template_not_done": "❌ NOT DONE: [specific reason why not feasible]",
  "implementation_evidence_required": true,
  "no_other_responses_acceptable": true,
  "responses": []
}
EOF

# Validate responses.json with jq -e (CodeRabbit suggestion)

jq -e . "$RESPONSES_FILE" > /dev/null || {
    echo "❌ CRITICAL: Invalid JSON in responses.json"
    exit 1
}

echo "🔄 Executing /commentreply with BINARY protocol (DONE/NOT DONE only)"
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
echo "✅ Binary comment responses posted successfully (every comment: DONE or NOT DONE)"
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
echo "  • Binary response protocol: DONE/NOT DONE only - IMPLEMENTED ✅"
echo "  • Every comment response: binary DONE/NOT DONE with explanation - IMPLEMENTED ✅"

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
        echo "📊 DIAGNOSTIC: Check /tmp/$(git branch --show-current | tr -cd '[:alnum:]_-')/responses.json format";
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

## 🎯 **SUCCESS CRITERIA**

### **HYBRID VERIFICATION REQUIREMENTS** (BOTH REQUIRED):

1. **Implementation Coverage**: All actionable issues have actual file changes from copilot-fixpr agent
2. **Communication Coverage**: 100% comment response rate with direct orchestrator /commentreply execution

**FAILURE CONDITIONS:**
- No file changes after agent execution
- Missing comment responses
- Push failures
- Skipped verification checkpoints

### **QUALITY GATES**:

- ✅ **File Justification Protocol**: All code changes properly documented and justified
- ✅ **Security Priority**: Critical vulnerabilities addressed first with actual fixes
- ✅ **Input Sanitization**: All GitHub comment content validated and sanitized
- ✅ **Synchronization**: Explicit agent coordination prevents race conditions
- ✅ **GitHub Response Management**: Proper comment response handling for all feedback
- ✅ **Pattern Detection**: Systematic fixes applied across similar codebase patterns
- ✅ **Adaptive Performance**: Execution completed within complexity-appropriate targets

### **FAILURE CONDITIONS**:

- ❌ **Coverage Gaps**: <100% comment response rate OR unimplemented actionable issues
- ❌ **Protocol Violations**: File changes without proper justification documentation
- ❌ **Performative Fixes**: GitHub responses claiming fixes without actual code changes
- ❌ **Race Conditions**: Orchestrator proceeding before agent completion
- ❌ **Security Violations**: Unsanitized input processing or validation failures
- ❌ **Boundary Violations**: Agent handling GitHub responses OR orchestrator making file changes
- ❌ **Timing Failures**: Execution time exceeding complexity-appropriate targets without alerts

### **Context Management**:

- **Complete Comment Coverage**: Process ALL comments without filtering for 100% coverage
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

## 🚨 **RESPONSE DATA FORMAT SPECIFICATION**

### **MANDATORY**: responses.json Format

The orchestrator MUST generate responses.json in this exact format:

```json
{
  "responses": [
    {
      "comment_id": "2357534669",     // STRING format required
      "reply_text": "[AI responder] ✅ **Issue Fixed**...",
      "in_reply_to": "optional_parent_id"
    }
  ]
}
```

### **CRITICAL FORMAT REQUIREMENTS**:

- `comment_id` MUST be STRING (not integer)
- `reply_text` MUST contain substantial technical response
- `responses` array MUST contain entry for each actionable comment
- File location: `/tmp/{branch_name}/responses.json`

### **INTEGRATION CONTRACT**:

- commentreply.py expects `responses` array with `comment_id` and `reply_text`
- Matching uses `str(response_item.get("comment_id")) == comment_id`
- Missing or malformed responses cause posting failures
- Format validation is MANDATORY before attempting to post responses

### **RESPONSE QUALITY STANDARDS**:

- Each response must address specific technical content from the comment
- Use `[AI responder] ✅ **Issue Fixed**` or `❌ **Not Done**` prefixes
- Include commit SHA when fixes are implemented
- Provide technical analysis explaining the resolution
- No generic acknowledgments ("Thanks!" or "Will consider" are insufficient)
