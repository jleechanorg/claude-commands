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

### 1. Trigger-Based Habits
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

### 3. Tool Integration
- Build protocol checking into TodoWrite templates
- Never edit without reading first (already enforced)
- Always start complex tasks with verification step

### 4. Forcing Functions
- Tool-enforced verification
- Habit-based verification
- Meta-cognitive verification

## Implementation Plan

### Phase 1: CLAUDE.md Updates
- [ ] Move PRE-ACTION CHECKPOINT to top of file
- [ ] Create simple 3-question trigger
- [ ] Add protocol checking to common workflows
- [ ] Build verification into TodoWrite templates

### Phase 2: Habit Formation
- [ ] Practice trigger-based habits for 1 week
- [ ] Document compliance/non-compliance
- [ ] Adjust protocols based on what actually works

### Phase 3: Reinforcement
- [ ] Regular review of protocol compliance
- [ ] Feedback loop for improvement
- [ ] Integration with existing tools

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
