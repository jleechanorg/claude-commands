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

## ⚡ **PERFORMANCE ARCHITECTURE: Parallel Orchestration**
– Launch `copilot-fixpr` and `copilot-analysis` in parallel
– Use GitHub MCP directly for analysis; delegate code edits to fixpr via Edit/MultiEdit
- **30 recent comments focus** - Process only actionable recent feedback
- **Expected time**: **3-5 minutes** with parallel agents (superior quality and coverage)

## 🚀 Core Workflow - Subcommand Orchestration

**IMPLEMENTATION**: Use existing subcommands systematically until GitHub is completely clean

**INITIAL STATUS & TIMING SETUP**: Get comprehensive status and initialize timing
```bash
# Get comprehensive PR status first
/gstatus

# Record start time for performance tracking
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
- Fix failing tests and CI pipeline problems (with necessity proof)
- **Continue until**: All technical issues resolved with verified code changes AND justified modifications
- **ANTI-PATTERN**: Posting GitHub reviews acknowledging issues ≠ fixing issues
- **PROTOCOL VIOLATION**: Making file changes without FILE JUSTIFICATION PROTOCOL compliance

### Phase 3.1: Implementation Tool Requirements (MANDATORY)
**IMPLEMENTATION TOOLS** (in priority order):
1. **Edit/MultiEdit tools** - For code changes, bug fixes, implementation
2. **GitHub MCP tools** - ONLY for communication, NOT for implementation
3. **Bash commands** - For file operations, testing, validation

**CRITICAL DISTINCTION**:
- ❌ **PERFORMATIVE**: `github_create_review("Fixed import issue")`
- ✅ **ACTUAL**: `Edit(old_string="import module", new_string="from package import module")`

### Phase 4: Response Generation
**Command**: `/commentreply` - Reply to all review comments
- Post technical responses to reviewer feedback
- Address bot suggestions with implementation details
- Use proper GitHub threading for line-specific comments
- **Continue until**: All comments have appropriate responses

### Phase 5: Coverage & Implementation Verification (MANDATORY)
**Command**: `/commentcheck` - Verify 100% comment coverage AND actual implementation
- **DUAL VERIFICATION REQUIRED**:
  1. **Communication Coverage**: All comments have threaded responses
  2. **Implementation Coverage**: All fixable issues have actual code changes
- **IMPLEMENTATION VERIFICATION**: Use `git diff` to confirm file modifications
- Validates response quality (not generic templates)
- Detects any missed or unaddressed feedback
- **🚨 CRITICAL**: Issues explicit warnings for unresponded comments
- **FAILURE CONDITIONS**:
  - ❌ Comments acknowledged but not fixed = FAILURE
  - ❌ GitHub reviews posted without code changes = FAILURE
  - ✅ Comments responded to AND issues implemented = SUCCESS
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
# COVERAGE VERIFICATION - MANDATORY
# Get current comment statistics - resolve repo and PR dynamically
OWNER=$(gh repo view --json owner --jq .owner.login)
REPO=$(gh repo view --json name --jq .name)
PR_NUMBER=$(gh pr view --json number --jq .number)

TOTAL_COMMENTS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq length)
THREADED_REPLIES=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq '[.[] | select(.in_reply_to_id != null)] | length')
ORIGINAL_COMMENTS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq '[.[] | select(.in_reply_to_id == null)] | length')

# Calculate CORRECT coverage percentage - original comments with at least one reply
ORIGINALS_WITH_REPLIES=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq -r '.[] | select(.in_reply_to_id == null) | .id' | while read -r original_id; do
  replies_count=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate | jq --arg id "$original_id" '[.[] | select(.in_reply_to_id == ($id | tonumber))] | length')
  if [ "$replies_count" -gt 0 ]; then echo "1"; fi
done | wc -l)

if [ "$ORIGINAL_COMMENTS" -gt 0 ]; then
    COVERAGE_PERCENT=$(( (ORIGINALS_WITH_REPLIES * 100) / ORIGINAL_COMMENTS ))

    # MANDATORY WARNING SYSTEM - only output if incomplete
    if [ "$COVERAGE_PERCENT" -lt 100 ]; then
        MISSING_REPLIES=$((ORIGINAL_COMMENTS - ORIGINALS_WITH_REPLIES))
        echo "🚨 WARNING: INCOMPLETE COMMENT COVERAGE DETECTED!"
        echo "❌ Missing replies: $MISSING_REPLIES comments"
        echo "⚠️ Coverage: $COVERAGE_PERCENT% ($ORIGINALS_WITH_REPLIES/$ORIGINAL_COMMENTS)"
        echo "🔧 REQUIRED ACTION: Run /commentreply to address missing responses"
    fi
fi

# Calculate execution time - only report if over target
COPILOT_END_TIME=$(date +%s)
COPILOT_DURATION=$((COPILOT_END_TIME - COPILOT_START_TIME))
if [ $COPILOT_DURATION -gt 180 ]; then
    COPILOT_MINUTES=$((COPILOT_DURATION / 60))
    COPILOT_SECONDS=$((COPILOT_DURATION % 60))
    echo "⚠️ PERFORMANCE: Duration ${COPILOT_MINUTES}m ${COPILOT_SECONDS}s exceeded 3m target"
fi
```

### Phase 9: Guidelines Integration & Learning
**Command**: `/guidelines` - Post-execution guidelines consultation and pattern capture
- **Universal Composition**: Call `/guidelines` at completion for systematic learning
- **Pattern Capture**: Document successful approaches and anti-patterns discovered
- **Mistake Prevention**: Update PR-specific guidelines with lessons learned
- **Continuous Improvement**: Enhance guidelines system with execution insights
- **Integration**: Seamless handoff using command composition for systematic learning

```bash
# PHASE 9: POST-EXECUTION GUIDELINES INTEGRATION
# Execute and capture output + status
GUIDE_OUTPUT=$(/guidelines 2>&1)
GUIDE_STATUS=$?

# Surface output for transparency
printf "%s\n" "$GUIDE_OUTPUT"

if [ "$GUIDE_STATUS" -ne 0 ]; then
  echo "❌ /guidelines failed (exit $GUIDE_STATUS)" >&2
  return 1 2>/dev/null || exit 1
fi
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
- **`/guidelines`** - Post-execution pattern capture and mistake prevention system enhancement

### Workflow Combinations
```bash
# Standard /copilot execution pattern
/execute → /commentfetch → /fixpr → /commentreply → /commentcheck → /pushl → /guidelines

# Continue until clean (repeat cycle)
/execute → /commentfetch → /fixpr → /commentreply → /commentcheck → /pushl → /guidelines
# Keep iterating until GitHub shows: no failing tests, no merge conflicts, no unaddressed comments
# Final /guidelines call captures patterns and enhances mistake prevention system

# /commentcheck MUST pass (100% coverage) before /pushl
# If /commentcheck fails → re-run /commentreply → /commentcheck → /pushl → /guidelines
```

## 🚨 Important Notes

### Autonomous Operation Protocol
- **NEVER requires user approval** for comment processing and fixes
- **Merges require explicit enablement** (`COPILOT_ALLOW_AUTOMERGE=1`) and must pass branch protection
- Default: prepare merge and request approval; auto-merge only when policy allows
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
