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
Ultra-fast PR processing using ALWAYS-ON parallel agent orchestration. Launches copilot-fixpr and copilot-analysis agents by default for comprehensive coverage and quality assurance.

## ⚡ **PERFORMANCE ARCHITECTURE: Mandatory Parallel Agent Orchestration**

🚨 **CRITICAL REQUIREMENT**: /copilot ALWAYS uses parallel agents - NO EXCEPTIONS

- **MANDATORY**: Launch `copilot-fixpr` and `copilot-analysis` agents in parallel for EVERY execution
- **NO DIRECT EXECUTION**: /copilot must NEVER handle tasks directly - always delegate to specialized agents
- **PARALLEL PROCESSING**: Both agents work simultaneously for maximum efficiency
- **EXPERTISE DISTRIBUTION**: Each agent handles its specialized domain (fixes vs analysis)
- **30 recent comments focus** - Process only actionable recent feedback
- **Expected time**: **2-3 minutes** with proper parallel agent coordination

## 🚀 Core Workflow - Parallel Agent Orchestration

**IMPLEMENTATION**: Launch two specialized agents in parallel for optimal performance and expertise distribution

**INITIAL STATUS & TIMING SETUP**: Get comprehensive status and initialize timing
```bash
# Get comprehensive PR status first
/gstatus

# Initialize timing for performance tracking (silent unless exceeded)
COPILOT_START_TIME=$(date +%s)
```

### Phase 1: Parallel Agent Launch (DEFAULT BEHAVIOR)
**ALWAYS launch parallel agents for optimal coverage and quality**:

**🚀 Launch copilot-fixpr Agent**:
Launch specialized agent for technical implementation and security analysis:
- Analyze current GitHub PR status and identify potential improvements
- Review code changes for security vulnerabilities and quality issues
- Verify implementations are properly coded and tested
- Focus on code quality, performance optimization, and technical accuracy

**🚀 Launch copilot-analysis Agent**:
Launch specialized agent for comment processing and communication coordination:
- Process all PR comments and verify 100% coverage achievement
- Generate technical responses with proper GitHub API threading
- Coordinate communication workflow and quality assessment
- Focus on comment coverage verification and threading API success

**Coordination Setup**: Both agents work in parallel on shared GitHub PR data with specialized tool usage (Edit/MultiEdit for fixpr, GitHub MCP for analysis)

### Phase 2: Agent Coordination & Integration
**Integration of parallel agent results**:

**Agent Result Collection**:
- copilot-fixpr provides: Technical analysis, code fixes, security recommendations, implementation verification
- copilot-analysis provides: Comment coverage verification, threading API results, communication quality assessment
- Both agents maintain: Specialized tool usage boundaries and shared data coordination

**Quality Integration**: Combine technical fixes from copilot-fixpr with communication strategies from copilot-analysis for comprehensive PR processing

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
# Define repository variables
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
PR_NUMBER=$(gh pr view --json number -q .number)

# Get comments with proper pagination handling
TOTAL_COMMENTS=$(gh api "repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments" --paginate | jq length)
THREADED_REPLIES=$(gh api "repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments" --paginate | jq '[.[] | select(.in_reply_to_id != null)] | length')
ORIGINAL_COMMENTS=$(gh api "repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments" --paginate | jq '[.[] | select(.in_reply_to_id == null)] | length')

if [ "$ORIGINAL_COMMENTS" -gt 0 ]; then
    COVERAGE_PERCENT=$(( (THREADED_REPLIES * 100) / ORIGINAL_COMMENTS ))
    if [ "$COVERAGE_PERCENT" -lt 100 ]; then
        echo "🚨 WARNING: INCOMPLETE COMMENT COVERAGE: $COVERAGE_PERCENT%"
        echo "Expected: 100% | Actual: $COVERAGE_PERCENT% | Missing: $((ORIGINAL_COMMENTS - THREADED_REPLIES)) responses"
    fi
fi

if [ $COPILOT_DURATION -gt 180 ]; then
    echo "⚠️ PERFORMANCE: Duration exceeded 3m target: $((COPILOT_DURATION / 60))m $((COPILOT_DURATION % 60))s"
fi

# Pattern capture and learning
/guidelines
```

## 🔧 **AGENT SPECIALIZATION BOUNDARIES**

### copilot-fixpr Responsibilities:
- **PRIMARY**: Security vulnerability detection and code implementation
- **TOOLS**: Edit/MultiEdit for file modifications, Serena MCP for semantic analysis
- **FOCUS**: Actual code changes with File Justification Protocol compliance
- **BOUNDARY**: Never handles GitHub comment responses - delegates to copilot-analysis

### copilot-analysis Responsibilities:
- **PRIMARY**: Comment processing and GitHub workflow coordination
- **TOOLS**: GitHub MCP for PR operations, slash command orchestration
- **FOCUS**: 100% comment coverage verification and reviewer communication
- **BOUNDARY**: Never handles code implementation - delegates to copilot-fixpr

### Coordination Protocol:
- **SHARED DATA**: Both agents work on same GitHub PR analysis simultaneously
- **PARALLEL EXECUTION**: Independent operation with coordination capability
- **VERIFICATION**: Both implementation coverage AND communication coverage required
- **INTEGRATION**: copilot-analysis incorporates copilot-fixpr implementation details into responses

## 🎯 **SUCCESS CRITERIA**

### **DUAL VERIFICATION REQUIREMENTS** (BOTH REQUIRED):
1. **Implementation Coverage**: All actionable issues have actual file changes from copilot-fixpr
2. **Communication Coverage**: 100% comment response rate with proper threading from copilot-analysis

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
- ❌ **Communication Overreach**: copilot-fixpr posting reviews OR copilot-analysis implementing code
- ❌ **Timing Failures**: Execution time >3 minutes without performance alerts

## ⚡ **PARALLEL EXECUTION OPTIMIZATION**

### **Context Management**:
- **Recent Comments Focus**: Process 30 most recent comments for 90%+ efficiency
- **GitHub MCP Primary**: Strategic tool usage for minimal context consumption
- **Semantic Search**: Use Serena MCP for targeted analysis before file operations
- **Agent Coordination**: Efficient data sharing between parallel agents

### **Performance Benefits**:
- **Time Efficiency**: 40-60% faster than sequential execution
- **Specialization**: Expert-focused implementation vs communication handling
- **Quality Improvement**: Better responses with verified implementation details
- **Scalability**: Handle complex PRs through specialized parallel processing

### **Coordination Efficiency**:
- **Data Sharing**: Single GitHub PR analysis shared between both agents
- **Tool Specialization**: Clear boundaries prevent tool usage conflicts
- **Result Integration**: Seamless combination of implementation and communication results
- **Verification Alignment**: Both agents contribute to comprehensive coverage verification