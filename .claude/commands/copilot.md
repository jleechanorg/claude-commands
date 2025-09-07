# /copilot - Fast Direct Orchestrated PR Processing

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
Ultra-fast PR processing using ALWAYS-ON parallel agent orchestration. Uses hybrid orchestrator with copilot-fixpr agent by default for comprehensive coverage and quality assurance.

## ⚡ **PERFORMANCE ARCHITECTURE: Hybrid Orchestrator with Selective Task Agents**

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

### Phase 1: Hybrid Coordination Launch
**Direct orchestration with selective task agent for maximum reliability**:

**🎯 Direct Comment Analysis**:
Execute comment processing workflow directly for reliable GitHub operations:
- Execute /commentfetch to gather all PR comments and issues
- Analyze actionable issues and categorize by type (security, runtime, tests, style)
- Process issue responses and plan implementation strategy
- Handle all GitHub API operations directly (proven to work)

**🚀 Parallel copilot-fixpr Agent Launch**:
Launch specialized agent for file modifications in parallel:
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

**Response Generation**: Direct execution of /commentreply with implementation details from agent file changes for guaranteed GitHub posting

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
# Final integration and verification
/pushl

# Calculate and report timing (only if performance targets exceeded)
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))

# Coverage verification and warnings (automatic)
# Resolve repo/PR once; prefer nameWithOwner to avoid manual owner parsing
REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)}"
PR_NUMBER="${PR_NUMBER:-$(gh pr view --json number -q .number 2>/dev/null)}"

# Input validation to prevent injection attacks
if [[ ! "$REPO" =~ ^[a-zA-Z0-9._/-]+$ ]] || [[ ! "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
    echo "🚨 SECURITY ERROR: Invalid repository or PR number format"
    exit 1
fi

# Aggregate all pages, then compute counts with correct coverage math
REV_JSON="$(gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --paginate 2>/dev/null | jq -s 'add // []' 2>/dev/null)"
REV_ORIGINAL="$(jq -r '[.[] | select(.in_reply_to_id == null)] | length' <<<"$REV_JSON")"
# Count unique original comments that have replies (not raw reply count)
UNIQUE_REPLIED_ORIGINALS="$(jq -r '[.[] | select(.in_reply_to_id != null) | .in_reply_to_id] | unique | length' <<<"$REV_JSON")"
ISSUE_COMMENTS="$(gh api "repos/$REPO/issues/$PR_NUMBER/comments" --paginate 2>/dev/null | jq -s 'map(length) | add // 0' 2>/dev/null)" || ISSUE_COMMENTS=0

# Threadable coverage (review comments); issue comments tracked separately
ORIGINAL_COMMENTS="${REV_ORIGINAL:-0}"
REPLIED_ORIGINALS="${UNIQUE_REPLIED_ORIGINALS:-0}"

# Validate numeric values to prevent arithmetic errors
if [[ ! "$ORIGINAL_COMMENTS" =~ ^[0-9]+$ ]]; then ORIGINAL_COMMENTS=0; fi
if [[ ! "$REPLIED_ORIGINALS" =~ ^[0-9]+$ ]]; then REPLIED_ORIGINALS=0; fi

if [ "${ORIGINAL_COMMENTS:-0}" -gt 0 ]; then
  COVERAGE_PERCENT=$(( REPLIED_ORIGINALS * 100 / ORIGINAL_COMMENTS ))
  if [ "$COVERAGE_PERCENT" -lt 100 ]; then
    missing=$(( ORIGINAL_COMMENTS - REPLIED_ORIGINALS ))
    [ "$missing" -lt 0 ] && missing=0
    echo "🚨 WARNING: INCOMPLETE REVIEW-COMMENT COVERAGE: ${COVERAGE_PERCENT}% (${REPLIED_ORIGINALS}/${ORIGINAL_COMMENTS} originals replied, missing: ${missing})"
  fi
fi
echo "ℹ️ Issue comments (not threadable): ${ISSUE_COMMENTS:-0} tracked separately."

if [ "${COPILOT_DURATION:-0}" -gt 180 ]; then
  echo "⚠️ PERFORMANCE: Duration exceeded 3m target: $((COPILOT_DURATION / 60))m $((COPILOT_DURATION % 60))s"
fi

# Pattern capture and learning
/guidelines
```

## 🔧 **HYBRID ORCHESTRATION BOUNDARIES**

### copilot-fixpr Agent Responsibilities:
- **PRIMARY**: Security vulnerability detection and code implementation
- **TOOLS**: Edit/MultiEdit for file modifications, Serena MCP for semantic analysis
- **FOCUS**: Actual code changes with File Justification Protocol compliance
- **BOUNDARY**: File operations only - never handles GitHub comment responses

### Direct Orchestrator Responsibilities:
- **PRIMARY**: Comment processing, GitHub operations, workflow coordination
- **TOOLS**: /commentfetch, /commentreply, GitHub MCP for API operations
- **FOCUS**: Communication workflow and agent coordination
- **BOUNDARY**: Delegates file operations to copilot-fixpr agent

### Coordination Protocol:
- **HYBRID EXECUTION**: Direct orchestrator coordinates while agent handles file operations
- **PROVEN RELIABILITY**: Uses only components verified to work correctly
- **IMPLEMENTATION FOCUS**: Agent makes actual file changes, orchestrator handles responses
- **SIMPLIFIED WORKFLOW**: Eliminates broken components for 100% working system

## 🎯 **SUCCESS CRITERIA**

### **HYBRID VERIFICATION REQUIREMENTS** (BOTH REQUIRED):
1. **Implementation Coverage**: All actionable issues have actual file changes from copilot-fixpr agent
2. **Communication Coverage**: 100% comment response rate with direct orchestrator /commentreply execution

### **QUALITY GATES**:
- ✅ **File Justification Protocol**: All code changes properly documented and justified
- ✅ **Security Priority**: Critical vulnerabilities addressed first with actual fixes
- ✅ **GitHub Threading**: Proper comment threading API usage for all responses
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