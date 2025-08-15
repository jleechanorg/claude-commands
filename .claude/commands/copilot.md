# /copilot - Fast Direct Orchestrated PR Processing

## 🚨 Mandatory Comment Coverage Tracking
This command automatically tracks comment coverage and warns about missing responses:
```bash
# COVERAGE TRACKING: Monitor comment response completion
echo "🔍 TRACKING: Comment coverage monitoring enabled"
echo "⚠️ WARNING: Will alert if any comments remain unresponded"
echo "📊 METRIC: Tracks original comments vs threaded replies ratio"
```

## ⏱️ Automatic Timing Protocol
This command automatically tracks and reports execution time:
```bash
# START: Record start time
COPILOT_START_TIME=$(date +%s)

# [Command execution phases happen here]

# END: Calculate and display timing
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
COPILOT_MINUTES=$((COPILOT_DURATION / 60))
COPILOT_SECONDS=$((COPILOT_DURATION % 60))

echo ""
echo "⏱️ COPILOT EXECUTION TIMING"
echo "=========================="
echo "🚀 Start time: $(date -d @$COPILOT_START_TIME '+%H:%M:%S')"
echo "🏁 End time: $(date -d @$COPILOT_END_TIME '+%H:%M:%S')"
echo "⏱️ Total duration: ${COPILOT_MINUTES}m ${COPILOT_SECONDS}s"
echo "🎯 Performance target: 2-3 minutes"
if [ $COPILOT_DURATION -le 180 ]; then
    echo "✅ PERFORMANCE: Target achieved (≤3 minutes)"
else
    echo "⚠️ PERFORMANCE: Exceeded target (>3 minutes)"
fi
echo ""
```

## 🎯 Purpose
Ultra-fast PR processing using direct GitHub MCP tools instead of Task delegation. Optimized for 2-3 minute execution vs 20+ minute agent overhead.

## ⚡ **PERFORMANCE ARCHITECTURE: Direct Orchestration**
- **No Task delegation** - Orchestrate all workflow phases directly within the copilot context (no external agents)
- **Direct GitHub MCP tools** - Use GitHub MCP tools directly in each phase
- **30 recent comments focus** - Process only actionable recent feedback
- **Expected time**: **2-3 minutes** (vs 20+ minutes with Task overhead)

## 🚀 Core Workflow - Subcommand Orchestration

**IMPLEMENTATION**: Use existing subcommands systematically until GitHub is completely clean

**TIMING SETUP**: Initialize timing at start of execution
```bash
# Record start time for performance tracking
COPILOT_START_TIME=$(date +%s)
echo "⏱️ COPILOT STARTED: $(date '+%H:%M:%S')"
```

### Phase 1: Assessment & Planning
**Command**: `/execute` - Plan the PR processing work with TodoWrite tracking
- Analyze current PR state and comment volume
- Create systematic processing plan with TodoWrite
- Set up progress tracking for all phases
- Evaluate skip conditions based on PR state

### Phase 2: Comment Collection
**Command**: `/commentfetch` - Get all PR comments and issues
- Fetches recent comments requiring responses
- Identifies critical issues, security problems, merge conflicts
- Creates clean JSON dataset for systematic processing

### Phase 3: Issue Resolution  
**Command**: `/fixpr` - Fix all identified problems systematically
- **Priority Order**: Security → Runtime Errors → Test Failures → Style
- Apply code fixes for review comments and bot suggestions
- Resolve merge conflicts and dependency issues
- Fix failing tests and CI pipeline problems
- **Continue until**: All technical issues resolved

### Phase 4: Response Generation
**Command**: `/commentreply` - Reply to all review comments
- Post technical responses to reviewer feedback
- Address bot suggestions with implementation details
- Use proper GitHub threading for line-specific comments
- **Continue until**: All comments have appropriate responses

### Phase 5: Coverage Verification (MANDATORY WARNINGS)
**Command**: `/commentcheck` - Verify 100% comment coverage and quality with warnings
- Confirms all comments received appropriate responses
- Validates response quality (not generic templates)
- Detects any missed or unaddressed feedback
- **🚨 CRITICAL**: Issues explicit warnings for unresponded comments
- **Must pass**: Zero unresponded comments before proceeding
- **AUTO-FIX**: If coverage < 100%, automatically runs `/commentreply` again

### Phase 6: Verification & Iteration  
**Iterative Cycle**: Repeat `/commentfetch` → `/fixpr` → `/commentreply` → `/commentcheck` cycle until completion
- **Keep going until**: No new comments, all tests pass, CI green, 100% coverage
- **GitHub State**: Clean PR with no unresolved feedback
- **Merge Ready**: No conflicts, no failing tests, all discussions resolved
- **Note**: This is an iterative loop, not a single linear execution

### Phase 7: Final Push
**Command**: `/pushl` - Push all changes with labels and description
- Commit all fixes and responses
- Update PR description with complete change summary
- Apply appropriate labels based on changes made

### Phase 8: Coverage & Timing Report
**MANDATORY COVERAGE + TIMING COMPLETION**: Calculate and display execution performance with coverage warnings
```bash
# COVERAGE VERIFICATION FIRST - MANDATORY
echo ""
echo "📊 COMMENT COVERAGE VERIFICATION"
echo "================================="

# Get current comment statistics
TOTAL_COMMENTS=$(gh api "repos/OWNER/REPO/pulls/PR/comments" --paginate | jq length)
THREADED_REPLIES=$(gh api "repos/OWNER/REPO/pulls/PR/comments" --paginate | jq '[.[] | select(.in_reply_to_id != null)] | length')
ORIGINAL_COMMENTS=$(gh api "repos/OWNER/REPO/pulls/PR/comments" --paginate | jq '[.[] | select(.in_reply_to_id == null)] | length')

echo "📝 Total comments: $TOTAL_COMMENTS"
echo "💬 Threaded replies: $THREADED_REPLIES"
echo "📋 Original comments: $ORIGINAL_COMMENTS"

# Calculate coverage percentage
if [ "$ORIGINAL_COMMENTS" -gt 0 ]; then
    COVERAGE_PERCENT=$(( (THREADED_REPLIES * 100) / ORIGINAL_COMMENTS ))
    echo "📊 Coverage: $COVERAGE_PERCENT% ($THREADED_REPLIES/$ORIGINAL_COMMENTS)"
    
    # MANDATORY WARNING SYSTEM
    if [ "$COVERAGE_PERCENT" -lt 100 ]; then
        MISSING_REPLIES=$((ORIGINAL_COMMENTS - THREADED_REPLIES))
        echo ""
        echo "🚨 WARNING: INCOMPLETE COMMENT COVERAGE DETECTED!"
        echo "❌ Missing replies: $MISSING_REPLIES comments"
        echo "⚠️ Coverage below 100% - some comments unresponded"
        echo "🔧 REQUIRED ACTION: Run /commentreply to address missing responses"
        echo ""
    else
        echo "✅ COVERAGE: 100% - All comments responded to"
    fi
else
    echo "✅ No comments found requiring responses"
fi

# Calculate execution time and display results
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
COPILOT_MINUTES=$((COPILOT_DURATION / 60))
COPILOT_SECONDS=$((COPILOT_DURATION % 60))

echo ""
echo "⏱️ COPILOT EXECUTION TIMING"
echo "=========================="
echo "🚀 Start time: $(date -d @$COPILOT_START_TIME '+%H:%M:%S')"
echo "🏁 End time: $(date -d @$COPILOT_END_TIME '+%H:%M:%S')"
echo "⏱️ Total duration: ${COPILOT_MINUTES}m ${COPILOT_SECONDS}s"
echo "🎯 Performance target: 2-3 minutes"
if [ $COPILOT_DURATION -le 180 ]; then
    echo "✅ PERFORMANCE: Target achieved (≤3 minutes)"
elif [ $COPILOT_DURATION -le 300 ]; then
    echo "⚠️ PERFORMANCE: Slightly over target (3-5 minutes)"
else
    echo "❌ PERFORMANCE: Significantly exceeded target (>5 minutes)"
fi
echo ""
```

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
# Handles typical PR with 5-15 comments
# Estimated time: 2-3 minutes
# Expected outcome: All comments resolved, CI passing
```

### High-Volume Comment Processing  
```bash
/copilot
# For PRs with 20+ comments from multiple reviewers
# Estimated time: 2-3 minutes (with recent comments focus)
# Expected outcome: Systematic resolution with full documentation
```

### Security-Critical PR Processing
```bash
/copilot
# Prioritizes security issues, applies fixes systematically
# Estimated time: 2-3 minutes  
# Expected outcome: All vulnerabilities patched, tests passing
```

## 🔗 Integration Points

### Related Commands
- **`/commentfetch`** - Can be used standalone for comment analysis
- **`/fixpr`** - Can be used independently for issue resolution
- **`/commentreply`** - Handles response generation and posting
- **`/pushl`** - Handles git operations and branch management

### Workflow Combinations
```bash
# Standard /copilot execution pattern
/execute → /commentfetch → /fixpr → /commentreply → /commentcheck → /pushl

# Continue until clean (repeat cycle)
/execute → /commentfetch → /fixpr → /commentreply → /commentcheck → /pushl
# Keep iterating until GitHub shows: no failing tests, no merge conflicts, no unaddressed comments

# /commentcheck MUST pass (100% coverage) before /pushl
# If /commentcheck fails → re-run /commentreply → /commentcheck → /pushl
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
