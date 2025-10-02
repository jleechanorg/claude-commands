---
description: /copilot-lite - Streamlined PR Processing
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Core Workflow - MANDATORY ACTION PHASES

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### Phase 1: Assessment

**Action Steps:**
`/execute` - Plan PR processing work

### Phase 2: Collection

**Action Steps:**
`/commentfetch` - Get ALL PR comments and issues (human + automated)

### Phase 3: Resolution (MANDATORY FIXES)

**Action Steps:**
`/fixpr` - **MUST FIX** ALL feedback by priority: Human Questions → Human Style → Security → Runtime → Tests → Automated Style
1. **MANDATORY**: Resolve ALL merge conflicts (not just detect them)
2. **MANDATORY**: Fix ALL failing tests (not just report them)
3. **MANDATORY**: Apply actual code changes (not just analysis)

### Phase 4: Response (MANDATORY COMMENT REPLIES)

**Action Steps:**
`/commentreply` - **MUST POST** replies to ALL unresponded comments (human + automated)
1. **MANDATORY**: Generate responses for EVERY unresponded comment (prioritize human questions)
2. **MANDATORY**: Post actual GitHub comment replies (not just drafts)
3. **MANDATORY**: Achieve 100% ALL comment coverage (not just measure it)

### Phase 5: Verification

**Action Steps:**
`/commentcheck` - Verify 100% comment coverage with warnings if incomplete

### Phase 6: Iteration (MANDATORY UNTIL COMPLETE)

**Action Steps:**
**MANDATORY**: Repeat Phases 3–5 until GitHub shows ALL criteria met, with strict bounds:
1. ✅ No failing tests
2. ✅ No merge conflicts
3. ✅ No unaddressed comments (human + automated)
4. ✅ CI passing
5. ⏱️ **Hard caps**: max 5 iterations or 30 minutes total runtime for the entire PR processing workflow (whichever comes first), with exponential backoff between attempts; on cap, stop and post a summary + next actions
6. **Stop** when no-op cycles are detected (no diffs, no new replies), then surface a summary and next actions

### Phase 7: Push

**Action Steps:**
`/pushl` - Push changes with labels and description

### Phase 8: Learning

**Action Steps:**
`/guidelines` - Capture patterns for mistake prevention

## 📋 REFERENCE DOCUMENTATION

# /copilot-lite - Streamlined PR Processing

**Purpose**: Ultra-fast PR processing that FIXES ALL ISSUES until GitHub shows ready-for-merge

🚨 **CRITICAL**: This command DOES WORK - fixes conflicts, responds to comments, resolves test failures. NOT a diagnostic tool.

## 🚨 ALL COMMENTS FIRST - MANDATORY HUMAN PRIORITY PROTOCOL

**🚨 CRITICAL REQUIREMENT**: EVERY PR comment MUST receive a response - human feedback takes ABSOLUTE PRIORITY over automated suggestions.

**HUMAN COMMENT HANDLING REQUIREMENTS**:
- ✅ **Check ALL authors including human reviewers** - Not just bots
- ✅ **Respond to questions, not just fix issues** - Human questions require answers
- ✅ **Human comments are equally important as bot comments** - Actually MORE important
- ✅ **100% ALL comment response rate** - No exceptions, no priorities that skip comments

**PRIORITY ORDER - HUMAN FIRST**: Human Questions → Human Style Feedback → Security → Runtime Errors → Test Failures → Automated Style

## Success Criteria - WORK COMPLETION REQUIRED

🚨 **MANDATORY WORK COMPLETION**:
- **100% ALL comment response rate** - EVERY unresponded comment (human + automated) MUST receive posted replies
- **Zero merge conflicts** - ALL conflicts MUST be resolved (not just detected)
- **All tests passing** - ALL failing tests MUST be fixed (not just reported)
- **CI green** - ALL checks MUST pass (not just analyzed)
- **GitHub mergeable** - PR MUST show ready-for-merge status

**FAILURE CONDITIONS**:
- ❌ Declaring "success" with unresponded comments (human or automated)
- ❌ Reporting conflicts without resolving them
- ❌ Identifying test failures without fixing them
- ❌ Analysis without implementation
- ❌ Stopping before GitHub shows mergeable

## Usage

```bash
/copilot-lite

# FIXES all PR issues until GitHub ready-for-merge

# POSTS ALL comment replies (human + automated) until 100% coverage

# RESOLVES all conflicts until clean merge

# Stops when work is complete OR caps are reached; on cap, posts a summary + next actions

```

🚨 **WORK-FOCUSED OPERATION**: MUST complete actual work - resolve conflicts, post replies, fix tests. Analysis alone = FAILURE.

**Autonomous Operation**: Continues through conflicts without user approval for fixes. Merge operations still require explicit approval.
