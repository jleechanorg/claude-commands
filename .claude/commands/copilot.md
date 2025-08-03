# /copilot Command - Universal Composition with Execute

**Usage**: `/copilot [PR_NUMBER]`

**Purpose**: Comprehensively analyze and address PR issues using universal composition with intelligent execution optimization.

## 🎯 **DEFAULT BEHAVIOR** (No Arguments)

**When you run `/copilot` without arguments**:
- ✅ **Automatically targets the current branch's PR**
- ✅ **Shows clear confirmation**: `🎯 Targeting current branch PR: #123`
- ✅ **No guessing required**: You'll see exactly which PR is being processed

**Examples**:
```bash
/copilot           # ← Applies to current branch PR (most common usage)
/copilot 1062      # ← Applies to specific PR #1062
```

**🚨 IMPORTANT**: If your current branch doesn't have a PR, the command will display an error message indicating that no PR is associated with the branch.

## 🚨 CRITICAL: EXECUTION GUARANTEE

**MANDATORY STARTUP PROTOCOL**:
```
🤖 /copilot - Starting intelligent PR analysis
🎯 Targeting: [Current branch PR: #123] OR [Specified PR: #456]
🔧 Reading PR status and planning workflow...
📊 PR Status: [OPEN/MERGED/CLOSED] | ✅ CI Status: [PASSING/FAILING] | 🔄 Mergeable: [MERGEABLE/CONFLICTING/UNMERGEABLE]
🚀 Beginning 6-phase autonomous workflow with full transparency...

🚀 Delegating to /execute for intelligent workflow optimization...

=== COPILOT WORKFLOW INITIATED ===
```

**NEVER FAIL SILENTLY**: Every execution MUST show visible progress through all phases
**NEVER STOP EARLY**: Complete all phases - /copilot ALWAYS resolves everything autonomously
**ALWAYS BE VERBOSE**: Show commands, results, progress, and decisions in real-time
**ALWAYS FIX ALL PROBLEMS**: No failing allowed - autonomously fix all problems encountered

## ⚡ **Execution Strategy**

**DEFAULT: Direct Execution** ✅ (Recommended for most PRs)
- **Performance**: Immediate startup vs 5-10s Task delegation overhead
- **Resource Efficiency**: Critical for solo developers with limited resources
- **Progress Tracking**: Clear TodoWrite-based phase tracking
- **Universal Composition**: Claude naturally orchestrates commands without delegation

**Consider Task Delegation Only When ALL Criteria Met**:
- ✅ **Parallelism Opportunity**: Many comments that can be processed simultaneously
- ✅ **Resource Availability**: System memory <50% AND <3 Claude instances running
- ✅ **Independence**: Multiple unrelated CI failures or research tasks
- ✅ **Specialization Needed**: Complex domain-specific analysis required

**NEVER Delegate When**:
- ❌ **Sequential 6-Phase Workflow**: Phases have dependencies, no parallel benefit
- ❌ **Resource Constraints**: >50% memory usage, multiple Claude instances
- ❌ **Simple Orchestration**: Just calling existing commands in sequence
- ❌ **Solo Developer Context**: Speed and simplicity preferred over architectural complexity

**Performance Evidence**: PR #1062 - Direct execution (2 min) vs Task delegation timeout (5+ min)

## How It Works

The `/copilot` command uses **universal composition** to intelligently orchestrate PR analysis and fixes:

1. **Delegates to `/execute`**: The entire copilot workflow is executed via `/execute` which automatically:
   - Analyzes task complexity and PR size
   - Determines optimal execution strategy (parallel tasks vs sequential)
   - Provides intelligent execution optimization

2. **Natural Workflow Composition**: Composes the workflow using existing commands:
   - `/commentfetch` - Data collection
   - `/fixpr` - Fix CI failures and conflicts
   - `/pushl` - Push fixes to remote
   - `/commentreply` - Comment response processing
   - `/commentcheck` - Verify coverage
   - `/pushl` - Final push if needed

3. **Intelligent Optimization**: `/execute` handles all optimization decisions:
   - Large comment volumes → Parallel comment processing
   - Multiple CI failures → Specialized CI analysis
   - Complex conflicts → Merge resolution
   - Quality verification → Coverage validation

   **Note**: All substeps like `/fixpr`, `/commentreply` etc. also benefit from `/execute`'s intelligent optimization when invoked within the copilot workflow.

## 🚨 INTELLIGENT WORKFLOW PHASES

**SMART EXECUTION**: These phases use intelligent optimization - executing only when needed while maintaining comprehensive coverage:

### Phase 1: GitHub Status Verification (MANDATORY)
```bash
# REQUIRED: Fresh GitHub state verification + Skip Condition Evaluation
pr_json=$(gh pr view $PR_NUMBER --json state,mergeable,statusCheckRollup,comments,reviews)
PR_STATE=$(echo "$pr_json" | jq -r '.state')
PR_MERGEABLE=$(echo "$pr_json" | jq -r '.mergeable')
CI_STATUS=$(echo "$pr_json" | jq -r '.statusCheckRollup.state // "PENDING"')
COMMENT_COUNT=$(echo "$pr_json" | jq '(.comments | length) + (.reviews | length)')

# Evaluate skip conditions
if [[ "$PR_MERGEABLE" == "MERGEABLE" && "$CI_STATUS" == "SUCCESS" && "$COMMENT_COUNT" -eq 0 ]]; then
    export SKIP_CONDITIONS_MET="true"
    echo "⚡ OPTIMIZATION ENABLED: All skip conditions met"
    echo "   ✅ Mergeable: $PR_MERGEABLE"
    echo "   ✅ CI Status: $CI_STATUS"
    echo "   ✅ Comments: $COMMENT_COUNT"
else
    export SKIP_CONDITIONS_MET="false"
    echo "🔧 FULL EXECUTION: Skip conditions not met"
    echo "   📊 Mergeable: $PR_MERGEABLE | CI: $CI_STATUS | Comments: $COMMENT_COUNT"
fi
```
- ✅ **MUST verify**: PR is OPEN and accessible
- ✅ **MUST check**: Current CI status (PASSING/FAILING/PENDING)
- ✅ **MUST confirm**: Mergeable state (MERGEABLE/CONFLICTING/UNMERGEABLE)
- ✅ **MUST evaluate**: Skip conditions for intelligent optimization
- ❌ **CANNOT proceed** if PR is CLOSED or MERGED

### Phase 2: Fresh Data Collection (CONDITIONAL)
```bash
# SMART: Check if data collection needed
if [[ "$SKIP_CONDITIONS_MET" == "true" ]]; then
    echo "⚡ OPTIMIZING: Skip conditions met, performing lightweight data verification"
    # Quick verification with state update if comments found
    read COMMENT_COUNT REVIEW_COUNT < <(gh pr view $PR_NUMBER --json comments,reviews | jq '.comments | length, .reviews | length')
    if [[ "$COMMENT_COUNT" -eq 0 && "$REVIEW_COUNT" -eq 0 ]]; then
        echo "✅ No comments or reviews detected. Maintaining skip conditions."
    else
        echo "📊 Comments: $COMMENT_COUNT, Reviews: $REVIEW_COUNT. Updating to full execution."
        export SKIP_CONDITIONS_MET="false"
        /commentfetch $PR_NUMBER
    fi
else
    echo "📊 COLLECTING: Full data collection required"
    /commentfetch $PR_NUMBER
fi
```
- ✅ **SMART EXECUTION**: Full fetch only when comments/reviews detected
- ✅ **OPTIMIZATION**: Quick verification when skip conditions met
- ✅ **SAFETY**: Falls back to full collection if verification shows activity
- ✅ **TRANSPARENCY**: Logs decision reasoning

### Phase 3: CI/Conflict Resolution (CONDITIONAL)
```bash
# SMART: Check if CI/conflict fixes needed
pr_status=$(gh pr view $PR_NUMBER --json mergeable,statusCheckRollup)
ci_status=$(echo "$pr_status" | jq -r '.statusCheckRollup.state')
mergeable=$(echo "$pr_status" | jq -r '.mergeable')

if [[ "$ci_status" == "SUCCESS" && "$mergeable" == "MERGEABLE" ]]; then
    echo "⚡ OPTIMIZING: CI passing and mergeable, skipping fixpr"
    echo "✅ CI Status: $ci_status | Mergeable: $mergeable"
else
    echo "🔧 FIXING: CI issues or conflicts detected"
    /fixpr $PR_NUMBER
fi
```
- ✅ **SMART EXECUTION**: Skip when CI passing and no conflicts
- ✅ **SAFETY**: Always verify fresh GitHub status before skipping
- ✅ **COMPREHENSIVE**: Execute /fixpr if ANY issues detected
- ✅ **TRANSPARENCY**: Log all status checks and decisions

### Phase 4: Comment Response Processing (CONDITIONAL)
```bash
# SMART: Check if comment responses needed
unresponded_count=$(gh pr view $PR_NUMBER --json comments,reviews | jq '(.comments | length) + (.reviews | length)')

if [[ "$unresponded_count" -eq 0 ]]; then
    echo "⚡ OPTIMIZING: Zero comments detected, skipping comment processing"
    echo "✅ Comment Status: $unresponded_count total comments"
    export COMMENTS_PROCESSED="false"
else
    echo "💬 RESPONDING: $unresponded_count comments require responses"
    echo "🚀 DELEGATING: /commentreply $PR_NUMBER"

    # Delegate to commentreply command - it handles all verification internally
    /commentreply $PR_NUMBER

    # Trust commentreply to handle success/failure - no reimplementation
    if [[ $? -eq 0 ]]; then
        echo "✅ SUCCESS: Comment replies processed successfully"
        export COMMENTS_PROCESSED="true"
    else
        echo "❌ FAILURE: Comment reply processing failed"
        export COMMENTS_PROCESSED="false"
        echo "🚨 CRITICAL ERROR: Phase 4 cannot be marked complete"
        exit 1
    fi
fi
```
- ✅ **SMART EXECUTION**: Skip when no unresponded comments detected
- ✅ **DELEGATION**: Delegate to /commentreply instead of reimplementing
- ✅ **TRUST EXISTING COMMANDS**: Let /commentreply handle all verification internally
- ✅ **FAILURE HANDLING**: Hard stop if comment processing fails
- ✅ **STATE TRACKING**: Export COMMENTS_PROCESSED for Phase 5
- ✅ **NO REIMPLEMENTATION**: Removed duplicate verification logic

### Phase 5: Coverage Verification (CONDITIONAL) - Enhanced Context Verification
```bash
# SMART: Verify coverage only if comments were processed with enhanced context validation
if [[ "$COMMENTS_PROCESSED" == "true" ]]; then
    echo "🔍 VERIFYING: Enhanced context reply coverage validation"
    /commentcheck $PR_NUMBER
elif [[ "$SKIP_CONDITIONS_MET" == "true" ]]; then
    echo "⚡ OPTIMIZING: No comments processed, performing quick verification"
    final_count=$(gh pr view $PR_NUMBER --json comments,reviews | jq '(.comments | length) + (.reviews | length)')
    echo "✅ Verification: $final_count total comments (expected: 0)"
else
    echo "🔍 VERIFYING: Full enhanced context coverage validation"
    /commentcheck $PR_NUMBER
fi
```
- ✅ **CONTEXT AWARE**: Skip detailed coverage when no comments processed
- ✅ **ENHANCED CONTEXT FOCUS**: Verify enhanced context reply success
- ✅ **SAFETY**: Quick verification when skip conditions met
- ✅ **COMPREHENSIVE**: Full validation when comment processing occurred
- ✅ **TRANSPARENCY**: Log verification method and results

### Phase 6: Final Sync (MANDATORY)
```bash
# REQUIRED: Push all changes to GitHub
/pushl --message "copilot: Complete PR analysis and response cycle"
```
- ✅ **MUST push**: ALL local changes to remote
- ✅ **MUST verify**: Push successful via GitHub API
- ✅ **MUST confirm**: Remote state matches local state
- ❌ **CANNOT complete** without successful push

## 🚨 INTELLIGENT STAGE OPTIMIZATION

**SMART PROTOCOL**: CONDITIONAL EXECUTION BASED ON PR STATE

### 🎯 **SKIP CONDITIONS** (All must be met for stage skipping):
- ✅ **No merge conflicts**: PR shows MERGEABLE status
- ✅ **CI clean**: All status checks PASSING
- ✅ **No pending comments**: Zero unresponded comments detected

### 📋 **CONDITIONAL EXECUTION LOGIC**:
- ✅ **SMART SKIPPING**: Skip phases when conditions indicate no work needed
- ✅ **SAFETY FIRST**: Always verify conditions before skipping
- ✅ **TRANSPARENCY**: Log all skip decisions with reasoning
- ✅ **FALLBACK**: Execute phase if ANY condition check fails
- ✅ **REQUIRED**: Each phase must verify OR skip with logged reasoning
- ✅ **REQUIRED**: Visible progress reporting for executed AND skipped steps

### 🚨 **CRITICAL EXECUTION GUARANTEE**
**MANDATORY**: When phases determine work is needed, commands MUST be executed:
- ❌ **FORBIDDEN**: "Analysis complete" without execution
- ❌ **FORBIDDEN**: Marking phases "COMPLETED" when work identified but not done
- ✅ **REQUIRED**: Actually execute `/commentreply`, `/fixpr`, etc. when needed
- ✅ **REQUIRED**: Verify command success before marking phase complete
- 🚨 **HARD STOP**: Exit with error if any required execution fails

### 🚨 **COMMENT THREADING PROTOCOL COMPLIANCE**
**MANDATORY**: Comment replies must follow commentreply.md threading protocol:
- ✅ **COMMIT HASH REQUIRED**: All replies must include `(Commit: abc1234)` reference
- ✅ **COMMENT ID REFERENCE**: Use `📍 Reply to Comment #ID` for explicit threading
- ✅ **STATUS MARKERS**: Include `✅ DONE` or `❌ NOT DONE` with technical details
- ✅ **THREADING VERIFICATION**: Check replies include proper ID references and commit hashes
- ❌ **FORBIDDEN**: Generic replies without commit hash proof of work
- ❌ **FORBIDDEN**: Missing explicit comment ID references for threading
- 🚨 **LEARNED**: General PR comments don't support true threading - use fallback method

### ⚠️ **NEVER SKIP** (Always execute regardless of conditions):
- **Phase 1**: GitHub Status Verification (need fresh state)
- **Phase 6**: Final Sync (ensure all changes pushed)

## Universal Composition Benefits

- **Simplicity**: No complex agent coordination in copilot
- **DRY Principle**: Subagent logic lives in `/execute`, not duplicated
- **Universal Benefit**: ALL commands get intelligent optimization
- **Maintainability**: Clean separation of concerns
- **Performance**: Same optimization benefits with cleaner architecture

## Example Workflows

### Most Common Usage (No Arguments)
```
/copilot
🎯 Targeting: Current branch PR: #1074
→ Composes task: "Execute comprehensive PR analysis workflow"
→ /execute analyzes: PR complexity, comment count, CI status
→ /execute decides: Direct execution optimal for this PR
→ /execute orchestrates: All commands with intelligent optimization
→ Result: Fast, thorough PR analysis with minimal complexity
```

### Specific PR Targeting
```
/copilot 1062
🎯 Targeting: Specified PR: #1062
→ Composes task: "Execute comprehensive PR analysis workflow"
→ /execute analyzes: PR complexity, comment count, CI status
→ /execute decides: Parallel processing beneficial, spawning agents
→ /execute orchestrates: All commands with intelligent optimization
→ Result: Fast, thorough PR analysis with minimal complexity
```

## 🚨 CRITICAL: ZERO TOLERANCE MERGE APPROVAL PROTOCOL

→ See **CLAUDE.md §ZERO-TOLERANCE MERGE APPROVAL** for complete protocol

### ⚠️ **MANDATORY INTEGRATION**: Merge approval check applies to ALL phases

**Critical Checkpoints** (applied at multiple phases):
- **Phase 1**: Verify PR is still OPEN (not auto-merged during workflow)
- **Phase 3**: Check before applying CI/conflict fixes that might trigger auto-merge
- **Phase 6**: MANDATORY check before final push (most critical checkpoint)

### ✅ **Non-Interactive Implementation:**
```bash
# MANDATORY: Check before any push operation or merge-triggering action
check_merge_approval() {
    local pr_number="$1"
    pr_json=$(gh pr view "${pr_number:-}" --json state,mergeable 2>/dev/null)
    PR_STATE=$(jq -r '.state' <<<"$pr_json")
    PR_MERGEABLE=$(jq -r '.mergeable' <<<"$pr_json")

    if [[ "$PR_STATE" == "OPEN" && "$PR_MERGEABLE" == "MERGEABLE" ]]; then
        if [[ "${MERGE_APPROVAL:-}" != "MERGE APPROVED" ]]; then
            echo "🚨 ZERO TOLERANCE VIOLATION: PR is mergeable but no approval"
            echo "❌ Operation cancelled – User must type 'MERGE APPROVED' first"
            echo "❌ Set: export MERGE_APPROVAL='MERGE APPROVED' to proceed"
            exit 1
        else
            echo "✅ MERGE APPROVAL CONFIRMED: User authorized mergeable operations"
        fi
    else
        echo "ℹ️ PR not mergeable (STATE: $PR_STATE, MERGEABLE: $PR_MERGEABLE) - approval not required"
    fi
}

# Called at critical phases:
# check_merge_approval "$PR_NUMBER"  # Before fixpr (Phase 3)
# check_merge_approval "$PR_NUMBER"  # Before final pushl (Phase 6) - MANDATORY
```

**This protocol applies to ALL PR operations: manual, /copilot, orchestration agents, and any automated workflow.**

**ZERO EXCEPTIONS**: Every copilot execution MUST call merge approval check before any action that could trigger auto-merge.

## Adaptive Intelligence Features

- **Prioritize by urgency**: Security issues first, style issues last
- **Context awareness**: First-time contributors get more detailed help
- **Error recovery**: Continue with remaining tasks if one fails (unless merge approval blocks)
- **Fresh data**: Always fetches current GitHub state, no caching
- **Mandatory execution**: ALL 6 phases execute regardless of apparent need

## Key Principles

1. **Universal Composition**: Let `/execute` handle optimization decisions
2. **Clean Architecture**: Copilot orchestrates, execute optimizes
3. **Genuine Intelligence**: Claude analyzes, not rigid patterns
4. **User Control**: Clear visibility of all actions
5. **Adaptive Workflow**: Adjust to PR needs intelligently

The power comes from universal composition - `/execute` provides intelligent optimization for any complex workflow, making copilot both simpler and more powerful.
