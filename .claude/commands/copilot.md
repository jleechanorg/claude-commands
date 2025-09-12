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

## 🚨 ALL COMMENTS FIRST - MANDATORY HUMAN PRIORITY PROTOCOL

**🚨 CRITICAL REQUIREMENT**: EVERY PR comment MUST receive a response - human feedback takes ABSOLUTE PRIORITY over automated suggestions.

**HUMAN COMMENT HANDLING REQUIREMENTS**:
- ✅ **Check ALL authors including human reviewers** - Not just bots
- ✅ **Respond to questions, not just fix issues** - Human questions require answers
- ✅ **Human comments are equally important as bot comments** - Actually MORE important
- ✅ **100% ALL comment response rate** - No exceptions, no priorities that skip comments

**PRIORITY ORDER - HUMAN FIRST**: Human Questions → Human Style Feedback → Security → Runtime Errors → Test Failures → Automated Style

## ⚡ Core Workflow

🚨 **OPTIMIZED HYBRID PATTERN**: /copilot uses direct execution + selective task agents for maximum reliability

- **DIRECT ORCHESTRATION**: Handle comment analysis, GitHub operations, and coordination directly
- **SELECTIVE TASK AGENTS**: Launch `copilot-fixpr` agent for file modifications in parallel
- **PROVEN COMPONENTS**: Use only verified working components - remove broken agents
- **PARALLEL FILE OPERATIONS**: Agent handles Edit/MultiEdit while orchestrator manages workflow
- **30 recent comments focus** - Process ALL recent feedback (human + automated)
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
- Execute /commentfetch to gather ALL PR comments and issues (human + automated)
- Analyze ALL comments and categorize by type (human questions, human style, security, runtime, tests, automated style)
- Process ALL comment responses and plan implementation strategy with HUMAN PRIORITY
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
- **Priority Order**: Human Questions → Human Style Feedback → Security → Runtime Errors → Test Failures → Automated Style
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

**Coverage Tracking (delegated):**
```bash
/commentcheck  # authoritative coverage verification & reporting
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
- **PRIMARY**: Address ALL human feedback through code implementation, then security vulnerabilities
- **HUMAN INTERACTION**: Implement changes requested by human reviewers with highest priority
- **TOOLS**: Edit/MultiEdit for file modifications, Serena MCP for semantic analysis, `/fixpr` command
- **FOCUS**: Make PR mergeable first, implement ALL human feedback, then technical fixes with File Justification Protocol compliance
- **BOUNDARY**: File operations and PR mergeability - never handles GitHub comment responses directly

**Direct Orchestrator:**
- Comment processing (/commentfetch, /commentreply)
- GitHub operations and workflow coordination
- Verification checkpoints and evidence collection

## 🎯 **SUCCESS CRITERIA**

### **HYBRID VERIFICATION REQUIREMENTS** (BOTH REQUIRED):
1. **Implementation Coverage**: ALL comments (human + automated) have actual file changes or explicit responses from copilot-fixpr agent
2. **Communication Coverage**: 100% ALL comment response rate with direct orchestrator /commentreply execution - NO COMMENT LEFT UNADDRESSED

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
- ❌ **Coverage Gaps**: <100% ALL comment response rate OR unaddressed human/automated feedback
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
