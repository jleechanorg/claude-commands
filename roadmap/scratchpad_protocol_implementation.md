# Protocol Implementation Scratchpad

**Branch**: architecture_refactor_2025
**Date**: 2025-07-08
**Goal**: Make documented protocols actually followable

## Problem Analysis

### Issue Identified
- Good protocols exist in CLAUDE.md but aren't being followed consistently
- Specific case: Violated "verify before assuming" principle when user asked about /think ultrathink
- Root cause: No systematic way to enforce protocol compliance

### 10 Whys Analysis Completed
1. Didn't realize file already had ultrathink change
2. Didn't check current state before acting
3. Focused on execution rather than verification
4. Treated as simple edit request
5. Didn't recognize need to apply documented principles
6. No habit of checking documented principles
7. No systematic review of meta-rules
8. No consistent pre-action checkpoint process
9. Haven't internalized meta-rules into working behavior
10. No feedback loop to reinforce following protocols

## Proposed Solutions

### 1. Hierarchy of Rules (CLAUDE_CORE.md)

**Problem**: 2000+ lines of CLAUDE.md creates cognitive overload

**Solution**: Create CLAUDE_CORE.md with ~10 essential rules that MUST be internalized:

```markdown
# CLAUDE_CORE.md - The Essential 10

1. 🚨 **VERIFY BEFORE ACTING**: Read current state before any edit
2. 🚨 **NEVER SIMULATE**: Admit limitations rather than fake results
3. 🚨 **EVIDENCE FIRST**: Extract actual errors/code before analyzing
4. 🚨 **TEST = TRUTH**: Fix ALL failures, no excuses
5. 🚨 **BRANCH DISCIPLINE**: Never switch branches without permission
6. ⚠️ **TODO TRACKING**: Use TodoWrite for complex tasks
7. ⚠️ **PR WORKFLOW**: All changes via PRs, never push to main
8. ⚠️ **TOOL BOUNDARIES**: Browser tests = Playwright, HTTP tests = requests
9. ✅ **CONCISE OUTPUT**: Minimal response, especially with /think
10. ✅ **UNCERTAINTY OK**: Say "I don't know" when unsure
```

### 2. Trigger-Based Habits
```markdown
TRIGGERS → PROTOCOL CHECKS
- Before any file edit → Read current state first
- Before answering user requests → "Is this asking me to change something that might already exist?"
- Before using tools → Check if I'm about to violate any rules
- When user asks for something → Verify current state before assuming it needs change
```

### 2. Ultra-Simple Checkpoint
```markdown
🚨 BEFORE ANY ACTION, ASK:
1. What is the current state?
2. Am I about to violate any rules?
3. Should I verify first?
```

### 5. Workflow-Specific Checklists

#### PR Creation Checklist
```markdown
- [ ] `git status` - verify clean state
- [ ] `git branch` - confirm correct branch
- [ ] `./run_tests.sh` - all tests pass
- [ ] `./coverage.sh` - check coverage
- [ ] Review changes with `git diff`
- [ ] Commit with clear message
- [ ] Push to remote branch
- [ ] `gh pr create` with test results
```

#### Bug Fix Checklist
```markdown
- [ ] Reproduce issue locally
- [ ] Extract exact error message
- [ ] Trace data flow (backend→API→frontend)
- [ ] Identify root cause with evidence
- [ ] Implement minimal fix
- [ ] Verify fix in multiple scenarios
- [ ] Write regression test
- [ ] Document in lessons.mdc if novel
```

#### Feature Implementation Checklist
```markdown
- [ ] Read existing similar code
- [ ] Check dependencies/imports
- [ ] Write failing tests first (TDD)
- [ ] Implement incrementally
- [ ] Run tests after each change
- [ ] Integrate with existing code
- [ ] Update documentation
- [ ] Consider edge cases
```

#### Code Review Checklist
```markdown
- [ ] `gh pr view --comments` for all comments
- [ ] Extract EVERY comment (even suppressed)
- [ ] Categorize: critical/important/minor
- [ ] Address critical first
- [ ] Test each fix
- [ ] Respond to every comment
- [ ] Verify nothing broken
- [ ] Request re-review
```

#### Test Execution Checklist
```markdown
- [ ] Verify environment activated
- [ ] Check test type (UI/HTTP/Unit)
- [ ] Confirm dependencies installed
- [ ] Use correct test runner
- [ ] STOP if dependencies missing
- [ ] Report actual results only
- [ ] Fix ALL failures (no excuses)
- [ ] Document any issues
```

### 6. Cognitive Load Reduction Strategies

#### Visual Hierarchy
- 🚨 **CRITICAL**: Life-or-death rules (NEVER simulate, ALWAYS verify)
- ⚠️ **MANDATORY**: Must follow but not critical (PR workflow, test all)
- ✅ **BEST PRACTICE**: Strongly recommended (concise output, uncertainty OK)
- 💡 **HELPFUL**: Good to know (archive process, command shortcuts)

#### Context-Aware Rules
Show only relevant rules based on current task:
- **Editing files**: Show verify rules, import rules, file placement
- **Running tests**: Show test protocols, coverage requirements
- **Creating PR**: Show git workflow, commit format, PR checklist
- **Debugging**: Show evidence extraction, debugging protocol

#### Progressive Disclosure
```
Level 1: CLAUDE_CORE.md (10 rules - always visible)
   ↓
Level 2: Task-specific rules (5-10 rules - shown when relevant)
   ↓
Level 3: Full CLAUDE.md (2000+ lines - reference only)
```

#### Memory Aids
- **VESTS**: Verify, Evidence, Simulate-never, Test-all, Say-uncertain
- **BEFORE**: Branch-check, Evidence-extract, Fix-all, Output-minimal, Read-first, Edit-after
- **Visual patterns**: 🚨 = Stop, ⚠️ = Caution, ✅ = Go, ❌ = Never

#### Decision Trees
```
About to edit file?
├─ YES → Did you read it first?
│  ├─ YES → Proceed with edit
│  └─ NO → STOP - Read first
└─ NO → Continue with current task

Test failing?
├─ Can reproduce locally?
│  ├─ YES → Extract error → Debug
│  └─ NO → Check environment
└─ Is it "minor"? → NO - Fix it
```

### 3. Tool Integration
- Build protocol checking into TodoWrite templates
- Never edit without reading first (already enforced)
- Always start complex tasks with verification step

### 4. Comprehensive Forcing Functions

#### Tool-Level Forcing
- **Edit requires Read**: Already enforced by Claude Code
- **Test requires Verify**: Must check dependencies before running
- **Push requires Tests**: GitHooks can enforce test passage
- **PR requires Description**: GitHub templates enforce completeness

#### Workflow-Level Forcing
- **Bug Fix**: Must reproduce → extract evidence → trace flow → fix → verify
- **Feature**: Must read existing → write tests → implement → integrate
- **Review**: Must extract ALL comments → categorize → address → verify
- **Deploy**: Must pass tests → get approval → verify staging → deploy

#### Cognitive-Level Forcing
- **Complex = TodoWrite**: >3 steps triggers mandatory task tracking
- **Debug = Evidence**: Error analysis requires extracted output first
- **Assume = Verify**: Any assumption triggers verification requirement
- **Stuck = Admit**: 2 failed attempts triggers "I cannot" response

#### Meta-Level Forcing
- **Every 10 actions**: Quick protocol compliance check
- **Every error**: Document learning immediately
- **Every correction**: Update relevant rule file
- **Every session**: Review protocol adherence

### 7. Anti-Patterns Gallery

#### Anti-Pattern: "Assuming Without Verifying"
**Violation Example**:
```
User: "Add ultrathink to the command"
Bad: *immediately edits file to add ultrathink*
Good: *reads file first, discovers ultrathink already exists*
```
**Consequence**: Duplicate code, confused user, wasted time
**Correct Approach**: ALWAYS read current state before editing

#### Anti-Pattern: "Simulating When Stuck"
**Violation Example**:
```
Error: "Playwright not installed"
Bad: *creates fake test output in text file*
Good: "Cannot run browser tests - Playwright not installed"
```
**Consequence**: Broken trust, hidden failures, cascading issues
**Correct Approach**: Admit limitations immediately

#### Anti-Pattern: "Skipping Evidence Extraction"
**Violation Example**:
```
User: "Fix the error in the login"
Bad: "The error is probably due to..."
Good: *extracts actual error* "TypeError at auth.py:45 - 'NoneType' has no attribute 'id'"
```
**Consequence**: Wrong fixes, wasted debugging time
**Correct Approach**: Extract first, analyze second

#### Anti-Pattern: "Partial Test Success"
**Violation Example**:
```
Test results: 97/99 passing
Bad: "Tests mostly pass, just 2 minor failures"
Good: *investigates failures* "2 tests fail due to missing mock data"
```
**Consequence**: Broken builds, regression bugs
**Correct Approach**: 100% pass rate or it's not done

#### Anti-Pattern: "Tool Boundary Violations"
**Violation Example**:
```
Task: Write browser test for login
Bad: *uses requests.post() to simulate login*
Good: *uses Playwright to click buttons and fill forms*
```
**Consequence**: Fake tests that don't catch real UI bugs
**Correct Approach**: Browser tests = browser automation

## Implementation Plan

### Phase 1: CLAUDE.md Updates
- [ ] Move PRE-ACTION CHECKPOINT to top of file
- [ ] Create CLAUDE_CORE.md file with 10 essential rules
- [ ] Add protocol checking to common workflows
- [ ] Build verification into TodoWrite templates
- [ ] Add decision trees to relevant sections

### Phase 2: Habit Formation
- [ ] Practice trigger-based habits for 1 week
- [ ] Document compliance/non-compliance
- [ ] Adjust protocols based on what actually works

### Phase 3: Reinforcement
- [ ] Regular review of protocol compliance
- [ ] Feedback loop for improvement
- [ ] Integration with existing tools

## Verification Protocol

### Success Metrics
1. **Pre-Action Checkpoint Usage**: Track % of actions with verification
2. **Simulation Incidents**: Count fake outputs (target: 0)
3. **Evidence Extraction Rate**: % of debug sessions with proper extraction
4. **Test Success Standards**: % of sessions achieving 100% pass rate
5. **Protocol Violations**: Daily count of rule breaks

### Weekly Review Questions
- Which protocols were followed consistently?
- Which were ignored under pressure?
- What patterns trigger non-compliance?
- Which forcing functions actually work?
- What needs simplification?

### Continuous Improvement
- Document violations in lessons.mdc
- Update CLAUDE_CORE.md based on patterns
- Refine checklists based on usage
- Strengthen working forcing functions
- Remove/revise ineffective rules

## Next Steps

1. Update CLAUDE.md with practical protocol implementation
2. Test new approach on next few tasks
3. Iterate based on what actually works
4. Merge improvements to main branch

## Notes

- This is a meta-problem: having good processes but not following them
- Solution needs to be practical, not just theoretical
- Focus on making protocols easy to follow, not just comprehensive
- Tool integration is key to success

## API Timeout Lessons Learned

### Immediate Solutions
1. **Avoid /think for simple tasks** - Adds massive overhead
2. **Ultra-minimal responses** - 2-3 lines max when using /think
3. **No tool calls during /think** - Process mentally, execute after
4. **Split work aggressively** - One tiny task per message

### Better Approach
- Make targeted edits directly
- Focus on one section at a time
- Keep each edit small and specific
- Skip unnecessary planning when action is clear
