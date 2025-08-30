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
Ultra-fast PR processing using direct GitHub MCP tools instead of Task delegation. Optimized for 2-3 minute execution vs 20+ minute agent overhead.

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

# Record start time for performance tracking
COPILOT_START_TIME=$(date +%s)
```

### 🚨 EXECUTION MANDATE: Immediate Parallel Agent Launch

**STEP 1 - MANDATORY**: Launch both agents simultaneously using Task tool:

```bash
# REQUIRED: Launch both agents in parallel - NO EXCEPTIONS
Task(
  subagent_type="general-purpose",
  description="copilot-fixpr agent execution",
  prompt="Execute copilot-fixpr workflow for PR fixes and implementation"
)

Task(
  subagent_type="general-purpose",
  description="copilot-analysis agent execution",
  prompt="Execute copilot-analysis workflow for communication and coordination"
)
```

**CRITICAL RULES**:
- ❌ **NEVER skip agent launch** - even for "simple" PRs
- ❌ **NEVER handle tasks directly** - always delegate to agents
- ✅ **ALWAYS use Task tool** to launch both agents
- ✅ **ALWAYS coordinate results** after agents complete

### Phase 1: Parallel Agent Launch & Coordination Setup
**Orchestration**: Launch specialized agents in parallel with shared GitHub data
- **Agent 1**: `copilot-fixpr` - Handles all code implementation and fixes
- **Agent 2**: `copilot-analysis` - Handles communication, analysis, and workflow coordination
- Create TodoWrite tracking for parallel execution monitoring
- Share fresh GitHub PR data with both agents simultaneously

### Phase 2: Parallel Execution with Coordination
**PARALLEL PROCESSING ARCHITECTURE**:

**copilot-fixpr Agent (Parallel Track 1)**:
- **Focus**: Security → Runtime → Test → Style fixes with actual code implementation
- **Tools**: Edit/MultiEdit for code changes, Serena MCP for pattern detection
- **Protocol**: Mandatory File Justification Protocol compliance for all changes
- **Output**: Git diff results, implementation summaries, pattern detection reports

**copilot-analysis Agent (Parallel Track 2)**:
- **Focus**: `/commentfetch` → `/commentreply` → `/commentcheck` → coordination workflow
- **Tools**: GitHub MCP tools, slash command orchestration, coverage verification
- **Protocol**: 100% comment coverage, implementation verification, workflow management
- **Output**: Communication results, coverage reports, coordination status

**COORDINATION PROTOCOL**:
```bash
# Launch both agents in parallel with shared PR data
# Agent coordination managed through status sharing and result integration
# copilot-fixpr focuses on implementation while copilot-analysis handles communication
# Both agents work on same GitHub PR data but with specialized responsibilities
```

### Phase 3: Implementation & Communication Integration
**DUAL-TRACK PROCESSING**:
- **Implementation Track (copilot-fixpr)**:
  - Implement security fixes, runtime error corrections, test infrastructure repairs
  - Apply File Justification Protocol for all code changes
  - Use pattern detection to fix similar issues across codebase
  - Provide git diff verification of all implemented changes

- **Communication Track (copilot-analysis)**:
  - Execute `/commentfetch` for comprehensive comment collection
  - Generate technical responses incorporating fixpr implementation details
  - Execute `/commentreply` with proper GitHub threading
  - Monitor parallel implementation progress for response accuracy

### Phase 4: Verification & Quality Gates
**DUAL VERIFICATION REQUIREMENTS**:
- **Implementation Verification (copilot-fixpr responsibility)**:
  - ✅ All identified issues have actual code implementations
  - ✅ Git diff shows concrete file modifications for each fix
  - ✅ File Justification Protocol followed for every change
  - ✅ Security issues resolved with proper implementation

- **Communication Verification (copilot-analysis responsibility)**:
  - ✅ Execute `/commentcheck` for 100% comment coverage verification
  - ✅ All copilot-fixpr implementations integrated into reviewer responses
  - ✅ Proper GitHub threading for all line-specific comments
  - ✅ No generic templates, context-aware responses only

### Phase 5: Iterative Coordination & Workflow Management
**COORDINATED ITERATION CYCLE**:
- **copilot-analysis**: Monitors for new comments, coordinates additional `/commentfetch` cycles
- **copilot-fixpr**: Handles additional fixes identified through new GitHub feedback
- **Integration Point**: Results merged for comprehensive PR status updates
- **Continuation Logic**: Iterate until no new comments, all tests pass, CI green, 100% coverage

### Phase 6: Final Integration & Push Coordination
**UNIFIED COMPLETION**:
- **copilot-analysis**: Execute `/pushl` with labels and description updates
- **copilot-fixpr**: Provide implementation summary for PR description
- **Integration**: Combine all fixes, responses, and documentation
- **Verification**: Ensure both tracks completed successfully before final push

### Phase 7: Performance & Coverage Reporting
**PARALLEL EXECUTION METRICS**:
```bash
# Calculate total execution time across both parallel tracks
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))

# Coverage verification with warnings (from copilot-analysis)
TOTAL_COMMENTS=$(gh api "repos/OWNER/REPO/pulls/PR/comments" --paginate | jq length)
THREADED_REPLIES=$(gh api "repos/OWNER/REPO/pulls/PR/comments" --paginate | jq '[.[] | select(.in_reply_to_id != null)] | length')
ORIGINAL_COMMENTS=$(gh api "repos/OWNER/REPO/pulls/PR/comments" --paginate | jq '[.[] | select(.in_reply_to_id == null)] | length')

# Implementation verification (from copilot-fixpr)
IMPLEMENTED_FIXES=$(git diff --name-only | wc -l)
PATTERN_FIXES_FOUND=$(# pattern detection count from copilot-fixpr)

if [ "$ORIGINAL_COMMENTS" -gt 0 ]; then
    COVERAGE_PERCENT=$(( (THREADED_REPLIES * 100) / ORIGINAL_COMMENTS ))
    if [ "$COVERAGE_PERCENT" -lt 100 ]; then
        MISSING_REPLIES=$((ORIGINAL_COMMENTS - THREADED_REPLIES))
        echo "🚨 WARNING: INCOMPLETE COMMENT COVERAGE DETECTED!"
        echo "❌ Missing replies: $MISSING_REPLIES comments"
        echo "⚠️ Coverage: $COVERAGE_PERCENT% ($THREADED_REPLIES/$ORIGINAL_COMMENTS)"
        echo "🔧 REQUIRED ACTION: copilot-analysis must run additional /commentreply"
    fi
fi

# Performance reporting - target maintained at 2-3 minutes with parallel execution
if [ $COPILOT_DURATION -gt 180 ]; then
    COPILOT_MINUTES=$((COPILOT_DURATION / 60))
    COPILOT_SECONDS=$((COPILOT_DURATION % 60))
    echo "⚠️ PARALLEL PERFORMANCE: Duration ${COPILOT_MINUTES}m ${COPILOT_SECONDS}s exceeded 3m target"
    echo "📊 EFFICIENCY GAIN: Parallel execution vs sequential workflow"
fi

# Success metrics for parallel coordination
echo "✅ PARALLEL EXECUTION SUMMARY:"
echo "🔧 Implementations: $IMPLEMENTED_FIXES files modified (copilot-fixpr)"
echo "💬 Communications: $COVERAGE_PERCENT% coverage achieved (copilot-analysis)"
echo "🎯 Pattern Detection: $PATTERN_FIXES_FOUND additional issues resolved"
```

### Phase 8: Guidelines Integration & Parallel Learning
**DUAL-TRACK LEARNING**:
- **copilot-analysis**: Execute `/guidelines` for systematic communication pattern capture
- **copilot-fixpr**: Contribute implementation patterns and fix methodologies to guidelines
- **Integration**: Combine lessons learned from both specialized tracks
- **Enhancement**: Update guidelines system with parallel coordination insights

## 🧠 Decision Logic

### When to Use /copilot
- **High comment volume** (10+ comments requiring technical responses)
- **Complex PR reviews** with multiple reviewers and feedback types
- **Critical security issues** requiring systematic resolution
- **CI failures** combined with code review feedback
- **Time-sensitive PRs** needing rapid but thorough processing

### Autonomous Operation Mode
- **Continues through conflicts** - doesn't stop for user approval on fixes
- **Applies systematic resolution** - follows security → runtime → style priority
- **Maintains full transparency** - all actions visible in command execution
- **Preserves user control** - merge operations still require explicit approval

## ⚡ Performance Optimization

### Recent Comments Focus (Default Behavior)
- **Default Processing**: Last 30 comments chronologically (90%+ faster)
- **Rationale**: Recent comments contain 80% of actionable feedback
- **Performance Impact**: ~20-30 minutes → ~3-5 minutes processing time
- **Context Efficiency**: 90%+ reduction in token usage

### When to Use Full Processing
- **Security Reviews**: Process all comments for comprehensive security analysis
- **Major PRs**: Full processing for critical architectural changes
- **Compliance**: Complete audit trail requirements
- **Implementation**: Use full comment processing instead of recent 30 focus

### Performance Comparison
| Scenario | Comments | Processing Time | Context Usage |
|----------|----------|-----------------|---------------|
| **Default (Recent 30)** | 30 | ~3-5 minutes | Low |
| **Full Processing** | 300+ | ~20-30 minutes | Very High |
| **Performance Gain** | 90% fewer | 80%+ faster | 90%+ efficient |

## 🔧 Error Handling & Recovery

### Common Scenarios
**Merge Conflicts:**
- Automatic conflict detection and resolution
- Backup creation before conflict fixes
- Validation of resolution correctness

**CI Failures:**
- Test failure analysis and systematic fixes
- Dependency issues and import errors
- Build configuration problems

**Comment Threading Issues:**
- Fallback to general comments if threading fails
- Retry mechanism for API rate limits
- Error logging for debugging

### Recovery Patterns
```bash
# If /commentfetch fails
- Check GitHub API connectivity
- Verify repository access permissions
- Retry with exponential backoff

# If /fixpr gets stuck
- Review error logs for specific issues
- Apply manual fixes for complex conflicts
- Continue with remaining automated fixes

# If /commentreply fails
- Check comment posting permissions
- Verify threading API parameters
- Fall back to non-threaded comments
```

## 📊 Success Criteria

### 🚨 CRITICAL: Comment Coverage Requirements (ZERO TOLERANCE)
- ✅ **100% Comment Coverage**: Every original comment MUST have a threaded reply
- 🚨 **Coverage Warnings**: Automatic alerts when coverage < 100%
- ⚠️ **Missing Response Detection**: Explicit identification of unresponded comments
- 🔧 **Auto-Fix Trigger**: Automatically runs `/commentreply` if gaps detected
- 📊 **Coverage Metrics**: Real-time tracking of responses vs originals ratio
- ❌ **FAILURE STATE**: < 100% coverage triggers warnings and corrective action

### 🚨 IMPLEMENTATION SUCCESS CRITERIA (ZERO TOLERANCE)
- ✅ **Code Changes Made**: `git diff` shows actual file modifications for reported issues
- ✅ **Implementation Verification**: Fixed code can be demonstrated with specific file references
- ❌ **FAILURE STATE**: GitHub reviews acknowledging issues without implementing fixes
- 🔧 **ANTI-PATTERN DETECTION**: Any issue marked "fixed" must have corresponding file changes

### Completion Indicators
- ✅ All critical comments addressed with technical responses
- ✅ All security vulnerabilities resolved
- ✅ All test failures fixed
- ✅ All merge conflicts resolved
- ✅ CI passing (green checkmarks)
- ✅ No unaddressed reviewer feedback
- ✅ **GitHub State**: Clean PR ready for merge
- ✅ **Iteration Complete**: `/commentfetch` shows no new actionable issues
- ✅ **Comment Coverage**: 100% response rate verified with warnings system

### Quality Gates
- **Technical Accuracy**: Responses demonstrate actual understanding
- **Complete Coverage**: No comments left without appropriate response
- **Real Implementation**: All fixes are functional, not placeholder
- **Proper Threading**: Comments use GitHub's threading API correctly
- **Coverage Tracking**: Continuous monitoring with explicit warnings

## 💡 Usage Examples

### Standard PR Review Processing
```bash
/copilot
# NEW: Parallel agent execution for typical PR with 5-15 comments
# copilot-fixpr: Implements security/runtime/test fixes with File Justification Protocol
# copilot-analysis: Handles /commentfetch → /commentreply → /commentcheck → /pushl workflow
# Estimated time: 2-3 minutes (maintained with parallel efficiency)
# Expected outcome: All comments resolved, CI passing, implementation verified
```

### High-Volume Comment Processing
```bash
/copilot
# NEW: Parallel specialized processing for PRs with 20+ comments from multiple reviewers
# copilot-fixpr: Pattern detection, bulk fixes, comprehensive implementation across codebase
# copilot-analysis: Recent 30 comments focus, systematic communication workflow, coverage verification
# Estimated time: 2-3 minutes (parallel optimization maintains target)
# Expected outcome: Systematic resolution with implementation + communication excellence
```

### Security-Critical PR Processing
```bash
/copilot
# NEW: Dual-track security processing with specialized expertise
# copilot-fixpr: Priority security implementations (SQL injection, XSS, auth fixes) with protocol compliance
# copilot-analysis: Security reviewer communication, comprehensive response coordination
# Estimated time: 2-3 minutes (parallel security focus)
# Expected outcome: All vulnerabilities implemented + documented, tests passing, reviewer confidence
```

## 🔗 Integration Points

### Related Commands
- **`copilot-fixpr` Agent** - Specialized implementation agent (launched in parallel by /copilot)
- **`copilot-analysis` Agent** - Specialized communication agent (launched in parallel by /copilot)
- **`/commentfetch`** - Executed by copilot-analysis agent for comprehensive comment collection
- **`/fixpr`** - Implementation expertise integrated into copilot-fixpr agent
- **`/commentreply`** - Executed by copilot-analysis agent for systematic response generation
- **`/commentcheck`** - Executed by copilot-analysis agent for dual verification (communication + implementation)
- **`/pushl`** - Executed by copilot-analysis agent for final git operations and branch management
- **`/guidelines`** - Executed by copilot-analysis agent for post-execution learning integration

### Workflow Combinations
```bash
# NEW: Parallel Agent Execution Pattern
/copilot → Launch copilot-fixpr + copilot-analysis in parallel → Integration & Verification

# Parallel Agent Coordination:
# copilot-fixpr: Handles implementation (Edit/MultiEdit, pattern detection, File Justification Protocol)
# copilot-analysis: Handles communication (/commentfetch, /commentreply, /commentcheck, /pushl, /guidelines)
# Both agents work simultaneously on shared GitHub PR data

# Iterative Parallel Cycles (until clean):
# 1. Both agents process fresh GitHub data simultaneously
# 2. copilot-fixpr implements fixes while copilot-analysis manages communication
# 3. Integration point: Merge implementation results with communication responses
# 4. Verification: Both comment coverage AND implementation coverage must be 100%
# 5. Repeat until GitHub shows: no failing tests, no merge conflicts, no unaddressed comments

# Success Criteria for Parallel Completion:
# ✅ copilot-fixpr: All issues implemented with git diff verification + File Justification Protocol
# ✅ copilot-analysis: 100% comment coverage + /pushl + /guidelines execution
# ✅ Integration: Implementation details incorporated into reviewer responses
# ✅ GitHub Status: Clean PR ready for merge with no blockers
```

## 🚨 Important Notes

### Autonomous Operation Protocol
- **NEVER requires user approval** for comment processing and fixes
- **NEVER requires user approval** for merge operations - operates fully autonomously
- **Continues through standard conflicts** and applies systematic resolution
- **Maintains full transparency** in all operations

### Priority Handling
1. **Critical Security Issues** (undefined variables, injection risks)
2. **Runtime Errors** (missing imports, syntax errors)
3. **Test Failures** (failing assertions, integration issues)
4. **Style & Performance** (optimization suggestions, formatting)
5. **Documentation** (comment clarifications, README updates)

### Resource Management
- **Context Monitoring**: Automatically manages token usage
- **API Rate Limiting**: Handles GitHub API limits gracefully
- **Parallel Processing**: Optimizes comment handling for efficiency
- **Strategic Checkpointing**: Saves progress for large PR processing

---

**Purpose**: Complete autonomous PR comment processing with systematic issue resolution and real GitHub integration.
