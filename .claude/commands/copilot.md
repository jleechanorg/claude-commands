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
Ultra-fast PR processing using ALWAYS-ON parallel agent orchestration. Launches copilot-fixpr and copilot-handle-comments agents by default for comprehensive coverage and quality assurance.

## ⚡ **PERFORMANCE ARCHITECTURE: Mandatory Parallel Agent Orchestration**

🚨 **CRITICAL REQUIREMENT**: /copilot ALWAYS uses parallel agents - NO EXCEPTIONS

- **MANDATORY**: Launch `copilot-fixpr` and `copilot-handle-comments` agents in parallel for EVERY execution
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

**🚀 Launch copilot-handle-comments Agent**:
Launch specialized agent for complete comment-driven development workflow:
- Execute /commentfetch to gather all PR comments and issues
- Fix identified code issues directly using Edit/MultiEdit tools
- Execute /commentreply to respond with implementation details
- Execute /commentcheck to verify 100% coverage achievement

**Coordination Setup**: Both agents work in parallel on shared GitHub PR data with specialized tool usage (Edit/MultiEdit for both agents, GitHub MCP for communication)

### Phase 2: Agent Coordination & Integration
**Integration of parallel agent results**:

**Agent Result Collection**:
- copilot-fixpr provides: Technical analysis, code fixes, security recommendations, implementation verification
- copilot-handle-comments provides: Comment processing, code issue fixes, response generation, coverage verification
- Both agents maintain: Specialized tool usage boundaries and shared data coordination

**Quality Integration**: Combine technical fixes from copilot-fixpr with comment-driven development from copilot-handle-comments for comprehensive PR processing

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
REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
PR_NUMBER="${PR_NUMBER:-$(gh pr view --json number -q .number)}"

# Aggregate all pages, then compute counts
REV_JSON="$(gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq -s 'add // []')"
REV_ORIGINAL="$(jq -r '[.[] | select(.in_reply_to_id == null)] | length' <<<"$REV_JSON")"
REV_REPLIES="$(jq -r  '[.[] | select(.in_reply_to_id != null)] | length' <<<"$REV_JSON")"
ISSUE_COMMENTS="$(gh api "repos/$REPO/issues/$PR_NUMBER/comments" --paginate | jq -s 'map(length) | add // 0')" || ISSUE_COMMENTS=0

# Threadable coverage (review comments); issue comments tracked separately
ORIGINAL_COMMENTS="${REV_ORIGINAL:-0}"
THREADED_REPLIES="${REV_REPLIES:-0}"

if [ "${ORIGINAL_COMMENTS:-0}" -gt 0 ]; then
  COVERAGE_PERCENT=$(( THREADED_REPLIES * 100 / ORIGINAL_COMMENTS ))
  if [ "$COVERAGE_PERCENT" -lt 100 ]; then
    missing=$(( ORIGINAL_COMMENTS - THREADED_REPLIES ))
    [ "$missing" -lt 0 ] && missing=0
    echo "🚨 WARNING: INCOMPLETE REVIEW-COMMENT COVERAGE: ${COVERAGE_PERCENT}% (missing: ${missing})"
  fi
fi
echo "ℹ️ Issue comments (not threadable): ${ISSUE_COMMENTS:-0} tracked separately."

if [ "${COPILOT_DURATION:-0}" -gt 180 ]; then
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
- **BOUNDARY**: Never handles GitHub comment responses - delegates to copilot-handle-comments

### copilot-handle-comments Responsibilities:
- **PRIMARY**: Complete comment-driven workflow - /commentfetch, FIX ISSUES, /commentreply, /commentcheck
- **TOOLS**: GitHub MCP, Edit/MultiEdit for code changes, slash command orchestration
- **FOCUS**: Code fixes AND comment responses - full-stack responsibility
- **BOUNDARY**: Self-contained workflow - no delegation needed

### Coordination Protocol:
- **SHARED DATA**: Both agents work on same GitHub PR analysis simultaneously
- **PARALLEL EXECUTION**: Independent operation with coordination capability
- **VERIFICATION**: Both implementation coverage AND communication coverage required
- **INTEGRATION**: copilot-handle-comments makes code changes directly and includes implementation details in responses

## 🎯 **SUCCESS CRITERIA**

### **DUAL VERIFICATION REQUIREMENTS** (BOTH REQUIRED):
1. **Implementation Coverage**: All actionable issues have actual file changes from copilot-fixpr
2. **Communication Coverage**: 100% comment response rate with proper threading from copilot-handle-comments

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
- ❌ **Communication Overreach**: copilot-fixpr posting reviews OR unauthorized code changes outside agent boundaries
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