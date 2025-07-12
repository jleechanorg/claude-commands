# Execute Command - Enhanced Protocol

**Purpose**: Strategic planning and execution of complex tasks with comprehensive subagent coordination

**Usage**: 
- `/plan` - Preview plan and wait for approval before execution
- `/execute` or `/e` - Use best judgment and execute immediately

**Command Differences**:
- **`/plan`**: Presents complete strategic plan and waits for explicit user approval before execution
- **`/execute` and `/e`**: Uses best judgment to analyze task and execute immediately without requiring approval

## 🚨 MANDATORY 3-PHASE PROTOCOL

### Phase 1: Circuit Breaker
🚨 **MANDATORY**: Use TodoWrite circuit breaker checklist:

**Core Checklist (shared by all commands)**:
```
## EXECUTE PROTOCOL CHECKLIST - CORE
- [ ] Context check: ___% remaining  
- [ ] Task complexity assessment: Low/Medium/High
- [ ] Execution approach: Direct/Subagent (Why: ___)
- [ ] Checkpoint frequency: Every 5 min OR 3-5 files
- [ ] Scratchpad location: roadmap/scratchpad_[branch].md
- [ ] PR update strategy: Push at each checkpoint
```

**Additional items by command**:

**`/plan` only**:
```
- [ ] Subagent strategy needed? Yes/No (Why: ___)
- [ ] Git worktree strategy confirmed: Yes/No
- [ ] Parallel execution strategy: Yes/No (Why: ___)
- [ ] Worktree usage justified: Yes/No (Why: ___)
- [ ] Subagent coordination plan: ___
- [ ] 🚨 MANDATORY: Complete plan presented to user: YES/NO
- [ ] User approval received: YES/NO
```

**`/execute` and `/e` only**:
```
- [ ] Best judgment strategy determined: ___
- [ ] Ready to execute immediately: YES
```

### Phase 2: Strategic Analysis & Planning

**Subagent Strategy Analysis**:
- Determine which subagents are required:
  - `analysis-agent` - Code analysis and architecture review
  - `main-analysis-agent` - Main codebase analysis and integration
  - `gemini-analysis-agent` - AI service integration analysis  
  - `coding-agent` - Implementation and development
  - `testing-agent` - Test creation and validation
  - Custom subagents for specialized tasks
- Define each subagent's specific responsibilities and scope

**Execution Strategy Decision Tree**:
- ✅ **Parallel Execution** (default for independent tasks):
  - Different code modules/components
  - Analysis tasks with no dependencies  
  - Non-conflicting file modifications
  - Research/investigation work
- ⚠️ **Sequential Execution** (when dependencies exist):
  - Tasks building on previous results
  - Shared resource constraints (API limits)
  - Complex coordination overhead exceeds parallel benefits
  - Database schema changes requiring specific order

**Parallel Subagent Coordination**:
- **Synchronization Points**: Define when subagents check in with each other
- **Resource Sharing**: Identify shared files/services requiring coordination
- **Merge Strategy**: Plan for combining parallel work (merge order, conflict resolution)
- **Progress Aggregation**: How to combine checkpoint updates from multiple subagents
- Establish execution order and coordination protocols
- Plan handoff procedures and data sharing between subagents

**Git Worktree Strategy**:
- **Worktree Usage Decision Criteria**:
  - ✅ **Use Worktrees When**:
    - True file isolation needed (conflicting changes expected)
    - Different branches/approaches being tested simultaneously
    - Long-running parallel implementation work
    - Multiple subagents modifying same files independently
  - ❌ **Skip Worktrees When**:
    - Analysis-only tasks (read-only operations)
    - Quick modifications to different files
    - Simple coordination prevents conflicts
    - Task completion time < worktree setup overhead
- **When Using Worktrees**:
  - Explain branch management and naming conventions
  - Define integration strategy back to main branch
  - Establish backup and rollback procedures
  - Plan for conflict resolution and merge strategies

**Progress Tracking & Scratchpad Management**:
- **Scratchpad Updates Must Include**:
  - Current progress percentage
  - Files modified/created since last update
  - Next immediate steps
  - Any blockers or issues encountered
- **PR Updates** (push to remote):
  - Same frequency as scratchpad (5 min or 3-5 files)
  - Use `git add -A && git commit` with descriptive message
  - Push with `git push origin HEAD`
- Establish checkpoint markers and success criteria
- Plan user monitoring and intervention points

**Comprehensive Plan Presentation**:
Present to user:
1. **Executive Summary**: High-level task breakdown and approach
2. **Subagent Deployment Plan**: 
   - Which subagents will be used
   - Each subagent's specific role and responsibilities
   - Execution sequence and dependencies
3. **Technical Strategy**:
   - Git worktree subtrees usage confirmed
   - Branch management approach
   - Integration and testing strategy
4. **Progress Tracking**:
   - Scratchpad update frequency: `[selected frequency]`
   - Milestone markers and checkpoints
   - User review points
5. **Resource Assessment**:
   - Estimated complexity and timeline
   - Risk factors and mitigation strategies
   - Dependencies and prerequisites
6. **Success Criteria**: Clear definition of completion

**Strategy Examples**:

**Example: Parallel with Worktrees**
```
Task: "Implement user authentication system"
- Subagent 1: Frontend login/signup forms (worktree: auth-frontend)
- Subagent 2: Backend API endpoints (worktree: auth-backend)  
- Subagent 3: Database schema and migrations (worktree: auth-db)
- Coordination: Sync on API contract design at 25% completion
- Merge order: Database → Backend → Frontend
```

**Example: Parallel without Worktrees**
```
Task: "Analyze codebase for performance issues"
- Subagent 1: Frontend performance patterns (read-only analysis)
- Subagent 2: Backend bottlenecks (read-only analysis)
- Subagent 3: Database query efficiency (read-only analysis)
- Coordination: Share findings in shared analysis document
- Result: Combined performance report with recommendations
```

**Example: Sequential Execution**
```
Task: "Migrate database schema with data preservation"
- Step 1: Analyze current schema and dependencies
- Step 2: Design migration strategy based on analysis results
- Step 3: Implement migration based on validated strategy
- Reason: Each step requires results from previous step
```

### Phase 3: Execution

**For `/plan` command (ONLY after approval)**:
- **STOP HERE** - Do not proceed without explicit user approval
- Wait for explicit user approval of the plan
- Address any user questions or modifications
- Only proceed after "YES" approval received

**For `/execute` and `/e` commands (immediate execution)**:
- Use best judgment to determine optimal execution strategy
- Proceed immediately based on complexity assessment
- Apply appropriate subagent strategy if beneficial
- Follow checkpoint frequency requirements

**Execution Modes**:
- **Direct Mode**: 
  - Work directly in current branch
  - 🚨 **Checkpoint every 5 minutes OR 3-5 file edits**
  - Update scratchpad with progress
  - Commit and push changes at each checkpoint
- **Subagent Mode**: 
  - Create worktrees for parallel development
  - Assign tasks to specialized subagents
  - Coordinate results and merge back
  - 🚨 **Same checkpoint frequency applies to each subagent**
- Follow approved plan and strategy
- Update progress according to MANDATORY frequency

## 🚨 CHECKPOINT REMINDERS

**Every 5 Minutes OR Every 3-5 File Edits**:
1. **Pause current work**
2. **Update scratchpad** (`roadmap/scratchpad_[branch].md`):
   - Progress percentage
   - Files changed
   - Current status
   - Next steps
3. **Commit changes**:
   ```bash
   git add -A
   git commit -m "Progress update: [brief description]"
   ```
4. **Push to PR**:
   ```bash
   git push origin HEAD
   ```
5. **Resume work**

**Why This Matters**:
- Prevents context loss from timeouts
- Enables user monitoring
- Creates restore points
- Documents decision history
- Maintains PR momentum

## Example Flows

**`/plan` Flow (with approval)**:
```
User: /plan implement JSON backend support
Assistant: I'll plan JSON backend support implementation. Using TodoWrite:

[Shows PLAN TodoWrite checklist with all items filled out]

## Plan Overview
1. **Analyze current JSON handling** (10 min)
2. **Implement improvements** (20 min) 
3. **Add tests** (15 min)

Shall I proceed?

User: Yes
Assistant: [Begins execution]
```

**`/execute` or `/e` Flow (immediate execution)**:
```
User: /e implement JSON backend support
Assistant: I'll implement JSON backend support using best judgment. TodoWrite assessment:

[Shows EXECUTE TodoWrite checklist with immediate execution decision]

Based on complexity assessment: Medium complexity, direct execution approach.
[Immediately begins implementation with regular checkpoints]
```
