# Execute Command - Enhanced Protocol

**Purpose**: Strategic planning and execution of complex tasks with comprehensive subagent coordination

**Usage**: `/execute` or `/e`

**Note**: This command replaces the previous `/plan` command - all planning functionality has been consolidated here for a unified workflow.

## 🚨 MANDATORY 3-PHASE PROTOCOL

### Phase 1: Circuit Breaker
🚨 **MANDATORY**: Use TodoWrite circuit breaker checklist:
```
## EXECUTE PROTOCOL CHECKLIST
- [ ] Context check: ___% remaining  
- [ ] Task complexity assessment: Low/Medium/High
- [ ] Subagent strategy needed? Yes/No (Why: ___)
- [ ] Git worktree strategy confirmed: Yes/No
- [ ] Scratchpad update frequency set: ___ 
- [ ] Comprehensive plan presented to user: Yes/No
- [ ] User approval received: YES/NO
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
- Establish execution order and coordination protocols
- Plan handoff procedures and data sharing between subagents

**Git Worktree Subtrees Strategy**:
- ✅ **Confirm use of git worktree subtrees** for parallel development
- Explain branch management and naming conventions
- Define integration strategy back to main branch
- Establish backup and rollback procedures
- Plan for conflict resolution and merge strategies

**Progress Tracking & Scratchpad Management**:
- **Update Frequency Options**:
  - `continuous` - After every major step or subagent action
  - `milestone` - At predefined project milestones
  - `hourly` - Regular time-based updates
  - `phase` - After each major phase completion
- Define level of detail for progress updates
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

### Phase 3: Execution (ONLY after approval)
- **STOP HERE** - Do not proceed without explicit user approval
- Wait for explicit user approval of the plan
- Address any user questions or modifications
- Only proceed after "YES" approval received

**Execution Modes**:
- **Direct**: Work with 5-minute milestone updates
- **Subagents**: Create worktrees, assign tasks, coordinate results
- Follow approved plan and strategy
- Update progress according to agreed frequency

## Example Flow
```
User: /e implement JSON backend support