# /copilot-lite - Streamlined PR Processing

**Purpose**: Ultra-fast PR processing that FIXES ALL ISSUES until GitHub shows ready-for-merge

🚨 **CRITICAL**: This command DOES WORK - fixes conflicts, responds to comments, resolves test failures. NOT a diagnostic tool.

## Core Workflow - MANDATORY ACTION PHASES

### Phase 1: Assessment
`/execute` - Plan PR processing work

### Phase 2: Collection
`/commentfetch` - Get PR comments and issues

### Phase 3: Resolution (MANDATORY FIXES)
`/fixpr` - **MUST FIX** issues by priority: Security → Runtime → Tests → Style
- **MANDATORY**: Resolve ALL merge conflicts (not just detect them)
- **MANDATORY**: Fix ALL failing tests (not just report them)
- **MANDATORY**: Apply actual code changes (not just analysis)

### Phase 4: Response (MANDATORY COMMENT REPLIES)
`/commentreply` - **MUST POST** replies to ALL unresponded comments
- **MANDATORY**: Generate responses for EVERY unresponded comment
- **MANDATORY**: Post actual GitHub comment replies (not just drafts)
- **MANDATORY**: Achieve 100% comment coverage (not just measure it)

### Phase 5: Verification
`/commentcheck` - Verify 100% comment coverage with warnings if incomplete

### Phase 6: Iteration (MANDATORY UNTIL COMPLETE)
**MANDATORY**: Repeat Phases 3–5 until GitHub shows ALL criteria met, with strict bounds:
- ✅ No failing tests
- ✅ No merge conflicts
- ✅ No unaddressed comments
- ✅ CI passing
- ⏱️ **Hard caps**: max 5 iterations or 30 minutes per run (whichever comes first), exponential backoff between attempts
- **Stop** when no-op cycles are detected (no diffs, no new replies), then surface a summary and next actions

### Phase 7: Push
`/pushl` - Push changes with labels and description

### Phase 8: Learning
`/guidelines` - Capture patterns for mistake prevention

## Success Criteria - WORK COMPLETION REQUIRED

🚨 **MANDATORY WORK COMPLETION**:
- **100% comment response rate** - ALL unresponded comments MUST receive posted replies
- **Zero merge conflicts** - ALL conflicts MUST be resolved (not just detected)
- **All tests passing** - ALL failing tests MUST be fixed (not just reported)
- **CI green** - ALL checks MUST pass (not just analyzed)
- **GitHub mergeable** - PR MUST show ready-for-merge status

**FAILURE CONDITIONS**:
- ❌ Declaring "success" with unresponded comments
- ❌ Reporting conflicts without resolving them
- ❌ Identifying test failures without fixing them
- ❌ Analysis without implementation
- ❌ Stopping before GitHub shows mergeable

## Usage

```bash
/copilot-lite
# FIXES all PR issues until GitHub ready-for-merge
# POSTS all comment replies until 100% coverage
# RESOLVES all conflicts until clean merge
# NEVER stops until work is complete
```

🚨 **WORK-FOCUSED OPERATION**: MUST complete actual work - resolve conflicts, post replies, fix tests. Analysis alone = FAILURE.

**Autonomous Operation**: Continues through conflicts without user approval for fixes. Merge operations still require explicit approval.
