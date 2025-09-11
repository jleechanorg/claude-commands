# /copilot - Fast PR Processing

## 🎯 Purpose
Ultra-fast PR processing using hybrid orchestration: direct comment handling + copilot-fixpr agent for file operations.

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
# Get comprehensive PR status and initialize timing
/gstatus
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

### copilot-fixpr Agent Responsibilities:
- **FIRST PRIORITY**: Execute `/fixpr` command to resolve merge conflicts and CI failures
- **PRIMARY**: Security vulnerability detection and code implementation
- **TOOLS**: Edit/MultiEdit for file modifications, Serena MCP for semantic analysis, `/fixpr` command
- **FOCUS**: Make PR mergeable first, then actual code changes with File Justification Protocol compliance
- **BOUNDARY**: File operations and PR mergeability - never handles GitHub comment responses

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
