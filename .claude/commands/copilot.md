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

## 🚨 MANDATORY WORKFLOW STEPS

**CRITICAL**: These steps are MANDATORY and CANNOT be skipped - each must complete before proceeding:

### Phase 1: GitHub Status Verification (MANDATORY)
```bash
# REQUIRED: Fresh GitHub state verification
gh pr view $PR_NUMBER --json state,mergeable,statusCheckRollup
```
- ✅ **MUST verify**: PR is OPEN and accessible
- ✅ **MUST check**: Current CI status (PASSING/FAILING/PENDING)
- ✅ **MUST confirm**: Mergeable state (MERGEABLE/CONFLICTING/UNMERGEABLE)
- ❌ **CANNOT proceed** if PR is CLOSED or MERGED

### Phase 2: Fresh Data Collection (MANDATORY)
```bash
# REQUIRED: Current comment and issue state
/commentfetch $PR_NUMBER
```
- ✅ **MUST fetch**: ALL comment sources (inline, general, review, bot)
- ✅ **MUST ensure**: Fresh data (no cache dependencies)
- ✅ **MUST count**: Total comments requiring responses
- ❌ **CANNOT skip** even if "no comments expected"

### Phase 3: CI/Conflict Resolution (MANDATORY)
```bash
# REQUIRED: Fix all GitHub-reported issues
/fixpr $PR_NUMBER
```
- ✅ **MUST resolve**: ALL failing CI checks
- ✅ **MUST fix**: ALL merge conflicts
- ✅ **MUST verify**: GitHub shows PASSING status after fixes
- ❌ **CANNOT proceed** with failing CI or conflicts

### Phase 4: Comment Response Processing (MANDATORY)
```bash
# REQUIRED: Address every individual comment
/commentreply $PR_NUMBER
```
- ✅ **MUST respond**: To EVERY individual comment (0 unresponded allowed)
- ✅ **MUST post**: Direct threaded replies via GitHub API
- ✅ **MUST include**: DONE/NOT DONE status for each
- ❌ **CANNOT skip** bot comments (Copilot, CodeRabbit, etc.)

### Phase 5: Coverage Verification (MANDATORY)
```bash
# REQUIRED: 100% coverage validation
/commentcheck $PR_NUMBER
```
- ✅ **MUST verify**: ZERO unresponded comments detected
- ✅ **MUST confirm**: All responses posted to GitHub
- ✅ **MUST validate**: Threading success rate
- ❌ **CANNOT proceed** if ANY unresponded comments found

### Phase 6: Final Sync (MANDATORY)
```bash
# REQUIRED: Push all changes to GitHub
/pushl --message "copilot: Complete PR analysis and response cycle"
```
- ✅ **MUST push**: ALL local changes to remote
- ✅ **MUST verify**: Push successful via GitHub API
- ✅ **MUST confirm**: Remote state matches local state
- ❌ **CANNOT complete** without successful push

## 🚨 ZERO-SKIP ENFORCEMENT

**CRITICAL PROTOCOL**: NO STEP CAN BE SKIPPED OR DECLARED "UNNECESSARY"

- ❌ **FORBIDDEN**: "No comments, skipping comment processing"
- ❌ **FORBIDDEN**: "CI already passing, skipping fixpr"
- ❌ **FORBIDDEN**: "No changes, skipping final push"
- ✅ **REQUIRED**: Execute ALL 6 phases regardless of apparent need
- ✅ **REQUIRED**: Each phase must complete successfully before next phase
- ✅ **REQUIRED**: Visible progress reporting for each mandatory step

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
