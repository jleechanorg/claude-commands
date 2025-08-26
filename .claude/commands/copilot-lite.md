# /copilot-lite - Streamlined PR Processing

**Purpose**: Ultra-fast PR processing with minimal output overhead

## Core Workflow

### Phase 1: Assessment
`/execute` - Plan PR processing work

### Phase 2: Collection  
`/commentfetch` - Get PR comments and issues

### Phase 3: Resolution
`/fixpr` - Fix issues by priority: Security → Runtime → Tests → Style

### Phase 4: Response
`/commentreply` - Reply to review comments with threading

### Phase 5: Verification
`/commentcheck` - Verify 100% comment coverage with warnings if incomplete

### Phase 6: Iteration
Repeat cycle until GitHub shows: no failing tests, no conflicts, no unaddressed comments

### Phase 7: Push
`/pushl` - Push changes with labels and description

### Phase 8: Learning
`/guidelines` - Capture patterns for mistake prevention

## Success Criteria

**Comment Coverage Requirements**:
- ✅ 100% response rate to original comments
- 🚨 Warnings for incomplete coverage
- 🔧 Auto-fix trigger if gaps detected

**Completion Indicators**:
- ✅ All critical issues resolved
- ✅ CI passing (green checkmarks)  
- ✅ No merge conflicts
- ✅ GitHub ready for merge

## Usage

```bash
/copilot-lite
# Handles typical PR with minimal output
# Expected: All comments resolved, CI passing
```

**Autonomous Operation**: Continues through conflicts without user approval for fixes. Merge operations still require explicit approval.