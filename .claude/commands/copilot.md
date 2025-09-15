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

## 🚨 MANDATORY EXECUTION DISCIPLINE PROTOCOL

### HARD STOP REQUIREMENTS (ZERO TOLERANCE):
- ❌ **ABSOLUTELY FORBIDDEN**: Any completion claim before /commentcheck shows 0 unresponded comments
- ❌ **ABSOLUTELY FORBIDDEN**: Arbitrary scope limitations without explicit user-provided constraints
- ❌ **ABSOLUTELY FORBIDDEN**: "Efficiency" optimizations that reduce comment coverage below 100%
- ❌ **ABSOLUTELY FORBIDDEN**: Declaring success with partial work completion
- ✅ **MANDATORY**: Full iteration until measurable success criteria met
- ✅ **MANDATORY**: Process ALL comments discovered, no exceptions
- ✅ **MANDATORY**: Continue Phase 6 iteration until /commentcheck reports 0 unresponded

### VERIFICATION CHECKPOINTS (CANNOT BE BYPASSED):
- **Phase 1 END**: Document total comments discovered vs total processed
- **Phase 2 END**: Verify ALL comments have processing plan, not subset
- **Phase 4 END**: Execute /commentcheck verification BEFORE any push operations
- **Phase 6 ITERATION**: Repeat Phase 3-5 until /commentcheck reports 0 unresponded comments
- **COMPLETION GATE**: No success declaration until measurable 100% coverage verified

## ⚡ Core Workflow

🚨 **OPTIMIZED HYBRID PATTERN**: /copilot uses direct execution + selective task agents for maximum reliability

- **DIRECT ORCHESTRATION**: Handle comment analysis, GitHub operations, and coordination directly
- **SELECTIVE TASK AGENTS**: Launch `copilot-fixpr` agent for file modifications in parallel
- **PROVEN COMPONENTS**: Use only verified working components - remove broken agents
- **PARALLEL FILE OPERATIONS**: Agent handles Edit/MultiEdit while orchestrator manages workflow
- **COMPLETE SCOPE PROCESSING** - Process ALL comments discovered without arbitrary limitations
- **ZERO SCOPE REDUCTION** - No "efficiency" optimizations that reduce coverage
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

**🎯 Direct Comment Analysis (COMPLETE SCOPE MANDATORY)**:
Execute comment processing workflow directly for reliable GitHub operations:
- Execute /commentfetch to gather ALL PR comments and issues (human + automated)
- **SCOPE DISCIPLINE**: Count total comments discovered and confirm ALL will be processed
- Analyze ALL comments and categorize by type (human questions, human style, security, runtime, tests, automated style)
- **NO ARBITRARY LIMITS**: Process every single comment found, regardless of quantity
- Process ALL comment responses and plan implementation strategy with HUMAN PRIORITY
- Handle all GitHub API operations directly (proven to work)
- **GUARDRAIL**: Document comment count at start, verify same count processed at end

**🚀 Parallel copilot-fixpr Agent Launch**:
Launch specialized agent for file modifications in parallel:
- **FIRST**: Execute `/fixpr` command to resolve merge conflicts and CI failures
- Analyze current GitHub PR status and identify potential improvements
- Review code changes for security vulnerabilities and quality issues
- Implement actual file fixes using Edit/MultiEdit tools with File Justification Protocol
- Focus on code quality, performance optimization, and technical accuracy

**Coordination Protocol**: Direct orchestrator manages workflow while agent handles file operations in parallel

## 🛡️ EXECUTION BOUNDARY PROTECTION (ANTI-OPTIMIZATION ABUSE)

### SCOPE DISCIPLINE ENFORCEMENT:
- **COMPLETE PROCESSING**: Process ALL items discovered unless explicitly constrained by USER
- **NO ARBITRARY LIMITS**: Any scope reduction requires documented user approval
- **OPTIMIZATION APPROVAL**: User approval required for efficiency decisions that impact coverage
- **DEFAULT TO MAXIMUM**: Default to complete coverage, optimize only when proven necessary by USER
- **SCOPE ACCOUNTABILITY**: Document initial scope vs final scope with justification for any differences

### SUCCESS CRITERIA ENFORCEMENT (MEASURABLE OUTCOMES):
- **MEASURABLE SUCCESS**: /commentcheck reports 0 unresponded comments (not partial coverage)
- **VERIFIABLE COMPLETION**: GitHub shows all comments have threaded replies (not just code fixes)
- **SUSTAINABLE COVERAGE**: Changes pushed without coverage regression (maintained over time)
- **NO PREMATURE CLAIMS**: Success declared only after measurable criteria met

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

**🚨 MANDATORY COVERAGE VERIFICATION (ABSOLUTE ENFORCEMENT):**
```bash
# CRITICAL: Comment coverage verification MUST execute regardless of CI status
echo "🔍 EXECUTING MANDATORY COVERAGE VERIFICATION"
/commentcheck  # authoritative coverage verification & reporting
COVERAGE_RESULT=$?

# HARD STOP: Any unresponded comments = IMMEDIATE FAILURE
if [ $COVERAGE_RESULT -ne 0 ]; then
    echo "🚨 CRITICAL FAILURE: Unresponded comments detected - EXECUTION HALTED"
    echo "🚨 BEHAVIORAL FAILURE PREVENTION: Cannot claim success with incomplete coverage"
    echo "🚨 PROTOCOL VIOLATION: /copilot requires 100% comment response rate"
    echo "🚨 REQUIRED ACTION: Fix all unresponded comments before completion"
    exit 1
fi

# SUCCESS VERIFICATION: Only proceed if 100% coverage confirmed
echo "✅ COVERAGE VERIFICATION PASSED: 100% comment response rate confirmed"
echo "✅ EXECUTION DISCIPLINE MAINTAINED: All comments processed"
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

### **FAILURE CONDITIONS** (ZERO TOLERANCE):
- ❌ **Coverage Gaps**: <100% ALL comment response rate OR unaddressed human/automated feedback
- ❌ **Protocol Violations**: File changes without proper justification documentation
- ❌ **Performative Fixes**: GitHub responses claiming fixes without actual code changes
- ❌ **Boundary Violations**: Agent handling GitHub responses OR orchestrator making file changes
- ❌ **Timing Failures**: Execution time >3 minutes without performance alerts
- ❌ **🚨 IMPLEMENTER'S PARADOX**: Claiming completion while implementing comment protocols WITHOUT responding to actual comments
- ❌ **🚨 STATUS BYPASS**: Skipping comment verification based on CI status (green/red irrelevant)
- ❌ **🚨 COVERAGE BYPASS**: Proceeding past /commentcheck failures without explicit remediation
- ❌ **🚨 ITERATION BYPASS**: Skipping Phase 6 iteration when coverage incomplete
- ❌ **🚨 SINGLE-PASS ASSUMPTION**: Assuming one execution cycle achieves 100% coverage

## ⚡ **HYBRID EXECUTION OPTIMIZATION**

## 🔄 **MANDATORY PHASE 6: ITERATION ENFORCEMENT**

### **ITERATION PROTOCOL (CANNOT BE BYPASSED)**:
- **MANDATORY CONTINUATION**: Repeat Phase 3-5 until /commentcheck returns EXIT CODE 0
- **NO SINGLE-PASS ASSUMPTION**: Must iterate until measurable success achieved
- **HARD ITERATION BOUNDS**: Maximum 5 iterations with exponential backoff between attempts
- **ESCALATION ON BOUNDS**: If max iterations reached without success, escalate to user

### **ITERATION SUCCESS CRITERIA**:
```bash
# Phase 6 Iteration Loop (MANDATORY)
for iteration in {1..5}; do
    echo "🔄 ITERATION $iteration: Executing Phase 3-5 cycle"

    # Phase 3-5 execution
    /fixpr || continue
    /commentreply || continue

    # Mandatory verification gate
    /commentcheck
    COVERAGE_RESULT=$?

    if [ $COVERAGE_RESULT -eq 0 ]; then
        echo "✅ ITERATION SUCCESS: 100% coverage achieved in iteration $iteration"
        break
    else
        echo "⚠️ ITERATION $iteration INCOMPLETE: Continuing to next iteration"
        sleep $((2**iteration))  # Exponential backoff
    fi
done

# Final verification
if [ $COVERAGE_RESULT -ne 0 ]; then
    echo "🚨 ITERATION BOUNDS EXCEEDED: Manual intervention required"
    exit 1
fi
```

### **NO-OP CYCLE DETECTION**:
- **Pattern Detection**: If no diffs or new replies for 2 consecutive iterations, surface summary
- **Manual Escalation**: Alert user when automated iteration cannot progress
- **Bounded Failure**: Prefer explicit failure over infinite loops

### **Context Management**:
- **COMPLETE SCOPE PROCESSING**: Process ALL comments discovered without arbitrary limitations
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
