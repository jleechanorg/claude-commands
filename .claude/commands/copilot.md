# /copilot - Fast PR Processing

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
# ... execution phases ...
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
if [ $COPILOT_DURATION -gt 180 ]; then
    echo "⚠️ Performance exceeded: $((COPILOT_DURATION / 60))m $((COPILOT_DURATION % 60))s (target: 3m)"
fi
```

## 🎯 Purpose
Ultra-fast PR processing using hybrid orchestration with comprehensive coverage and quality assurance. Uses hybrid orchestrator with copilot-fixpr agent by default for maximum reliability.

## ⚡ Core Workflow

🚨 **OPTIMIZED HYBRID PATTERN**: /copilot uses direct execution + selective task agents for maximum reliability

- **DIRECT ORCHESTRATION**: Handle comment analysis, GitHub operations, and coordination directly
- **SELECTIVE TASK AGENTS**: Launch `copilot-fixpr` agent for file modifications in parallel
- **PROVEN COMPONENTS**: Use only verified working components - remove broken agents
- **PARALLEL FILE OPERATIONS**: Agent handles Edit/MultiEdit while orchestrator manages workflow
- **30 recent comments focus** - Process only actionable recent feedback
- **Expected time**: **2-3 minutes** with reliable hybrid coordination

## 🚀 Core Workflow - Hybrid Orchestrator Pattern

**IMPLEMENTATION**: Direct orchestration with selective task agent for file operations

**INITIAL STATUS & TIMING SETUP**: Get comprehensive status and initialize timing
```bash
# Get comprehensive PR status first
/gstatus

# Initialize timing for performance tracking (silent unless exceeded)
COPILOT_START_TIME=$(date +%s)
```

### Phase 1: Analysis & Agent Launch

**🎯 Direct Comment Analysis**:
Execute comment processing workflow directly for reliable GitHub operations:
- Execute /commentfetch to gather all PR comments and issues
- Analyze actionable issues and categorize by type (security, runtime, tests, style)
- Process issue responses and plan implementation strategy
- Handle all GitHub API operations directly (proven to work)

**🚀 Parallel copilot-fixpr Agent Launch**:
Launch specialized agent for file modifications in parallel:
- **FIRST**: Execute `/fixpr` command to resolve merge conflicts and CI failures
- Analyze current GitHub PR status and identify potential improvements
- Review code changes for security vulnerabilities and quality issues
- Implement actual file fixes using Edit/MultiEdit tools with File Justification Protocol
- Focus on code quality, performance optimization, and technical accuracy

**Coordination Protocol**: Direct orchestrator manages workflow while agent handles file operations in parallel

### Phase 2: Hybrid Integration & Response Generation
**Direct orchestration with agent result integration**:

**Agent Result Collection**:
- copilot-fixpr provides: Technical analysis, actual file fixes, security implementations, code changes with justification
- Direct orchestrator handles: Comment processing, response generation, GitHub API operations, coverage tracking
- Coordination maintains: File operation delegation while ensuring reliable communication workflow

**Response Generation** (MANDATORY ORCHESTRATOR RESPONSIBILITY):
```bash
echo "📝 Generating responses.json from analyzed comments"
# CRITICAL: Generate responses in commentreply.py expected format
# Orchestrator writes: /tmp/$(git branch --show-current)/responses.json

# 🚨 MANDATORY: Orchestrator must generate responses for ALL comments
# The copilot-fixpr agent handles ONLY file operations, NOT comment responses
# Orchestrator MUST analyze all comments from commentfetch and create technical responses

echo "🔍 ORCHESTRATOR RESPONSIBILITY: Analyzing ALL comments for response generation"
BRANCH_NAME=$(git branch --show-current)
COMMENTS_FILE="/tmp/$BRANCH_NAME/comments.json"
export RESPONSES_FILE="/tmp/$BRANCH_NAME/responses.json"

# Verify we have comment data from commentfetch
if [ ! -f "$COMMENTS_FILE" ]; then
    echo "❌ CRITICAL: No comment data from commentfetch at $COMMENTS_FILE"
    exit 1
fi

TOTAL_COMMENTS=$(jq '.comments | length' "$COMMENTS_FILE")
echo "📊 Processing $TOTAL_COMMENTS comments for response generation"

# Generate responses for ALL unresponded comments
# This is ORCHESTRATOR responsibility, not agent responsibility

# 🚨 NEW: MANDATORY FORMAT VALIDATION
echo "🔧 VALIDATING: Response format compatibility with commentreply.py"
export RESPONSES_FILE="/tmp/$(git branch --show-current)/responses.json"
python3 -c '
import os, sys
responses_file = os.environ.get("RESPONSES_FILE", "")
if not responses_file:
    print("❌ RESPONSES_FILE environment variable not set")
    sys.exit(1)

import json
try:
    with open(responses_file, "r") as f:
        data = json.load(f)
    assert "responses" in data, "Missing responses array"
    for r in data["responses"]:
        assert "comment_id" in r, "Missing comment_id"
        assert "reply_text" in r, "Missing reply_text"
    print("✅ Response format validated")
except Exception as e:
    print(f"❌ CRITICAL: Response validation failed: {e}")
    sys.exit(1)
' || { echo "❌ CRITICAL: Invalid response format"; exit 1; }

# Verify responses.json exists and is valid before proceeding
if [ ! -f "$RESPONSES_FILE" ]; then
    echo "❌ CRITICAL: responses.json not found at $RESPONSES_FILE"
    echo "Orchestrator must generate responses before posting"
    exit 1
fi

echo "🔄 Executing /commentreply for all unresponded comments"
/commentreply || { echo "🚨 CRITICAL: Comment response failed"; exit 1; }
echo "🔍 Verifying coverage via /commentcheck"
/commentcheck || { echo "🚨 CRITICAL: Comment coverage failed"; exit 1; }
```
Direct execution of /commentreply with implementation details from agent file changes for guaranteed GitHub posting

### Phase 3: Verification & Completion (AUTOMATIC)
**Results verified by agent coordination**:

**🚨 MANDATORY FILE JUSTIFICATION PROTOCOL COMPLIANCE**:
- **Every file modification** must follow FILE JUSTIFICATION PROTOCOL before implementation
- **Required documentation**: Goal, Modification, Necessity, Integration Proof for each change
- **Integration verification**: Proof that adding to existing files was attempted first
- **Protocol adherence**: All changes must follow NEW FILE CREATION PROTOCOL hierarchy
- **Justification categories**: Classify each change as Essential, Enhancement, or Unnecessary

**Implementation with Protocol Enforcement**:
- **Priority Order**: Security → Runtime Errors → Test Failures → Style
- **MANDATORY TOOLS**: Edit/MultiEdit for code changes, NOT GitHub review posting
- **IMPLEMENTATION REQUIREMENT**: Must modify actual files to resolve issues WITH justification
- **VERIFICATION**: Use git diff to confirm file changes made AND protocol compliance
- **Protocol validation**: Each file change must be justified before Edit/MultiEdit usage
- Resolve merge conflicts and dependency issues (with integration evidence)

**Final Completion Steps**:
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
        echo "📊 DIAGNOSTIC: Check /tmp/$(git branch --show-current)/responses.json format";
        echo "📊 DIAGNOSTIC: Verify GitHub API permissions and rate limits";
        exit 1;
    }

    # Re-verify after recovery attempt
    /commentcheck || {
        echo "🚨 CRITICAL: Comment coverage still failing after recovery";
        exit 1;
    }
fi
echo "✅ Comment coverage verification passed - proceeding with completion"
```

**Final Timing:**
```bash
# Calculate and report timing (only if performance targets exceeded)
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
if [ $COPILOT_DURATION -gt 180 ]; then
    echo "⚠️ Performance exceeded: $((COPILOT_DURATION / 60))m $((COPILOT_DURATION % 60))s (target: 3m)"
fi

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
- ✅ **GitHub Response Management**: Proper comment response handling for all feedback
- ✅ **Pattern Detection**: Systematic fixes applied across similar codebase patterns
- ✅ **Performance**: Execution completed within 2-3 minute target

### **FAILURE CONDITIONS**:
- ❌ **Coverage Gaps**: <100% comment response rate OR unimplemented actionable issues
- ❌ **Protocol Violations**: File changes without proper justification documentation
- ❌ **Performative Fixes**: GitHub responses claiming fixes without actual code changes
- ❌ **Boundary Violations**: Agent handling GitHub responses OR orchestrator making file changes
- ❌ **Timing Failures**: Execution time >3 minutes without performance alerts

## ⚡ **HYBRID EXECUTION OPTIMIZATION**

### **Context Management**:
- **Recent Comments Focus**: Process 30 most recent comments for 90%+ efficiency
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
