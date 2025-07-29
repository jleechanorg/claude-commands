# Plan Command - Execute with Approval

**Purpose**: Same as `/execute` but requires user approval before implementation

**Usage**: `/plan` - Present execution plan and wait for approval

## 🚨 PLAN PROTOCOL

### Phase 1: TodoWrite Circuit Breaker (MANDATORY)

**Required TodoWrite Checklist**:
```
## PLANNING PROTOCOL CHECKLIST
- [ ] Context check: ___% remaining
  *Guidance*: Estimate the percentage of the task or project that remains incomplete. For example, if 3 out of 10 subtasks are done, the remaining percentage is 70%.
- [ ] Complexity assessment: Simple/Complex
- [ ] Subagent decision: YES/NO with explicit reasoning
  *Required*: Must state "Subagents: YES - [reason]" or "Subagents: NO - [reason]"
- [ ] Tool requirements: Read, Write, Edit, Bash, Task
- [ ] Execution plan presented to user
- [ ] User approval received
```

❌ **NEVER proceed without explicit user approval marked as checked (`[x]`) in the checklist**

### Phase 2: Present Execution Plan

**Analysis Presentation**:
- **Task complexity**: Simple (direct execution) or Complex (subagents beneficial)
- **Subagent decision**: **YES** or **NO** with explicit reasoning
  - If YES: Specific parallel work strategy
  - If NO: Why sequential execution is better
- **Tool requirements**: Which tools will be used
- **Implementation approach**: Step-by-step plan
- **Expected timeline**: Realistic estimate

**Subagent Plan (if applicable)**:
- **Main task**: What I'll focus on
- **Subagent 1**: Independent analysis/research task
- **Subagent 2**: Documentation/testing task
- **Integration**: How results will be combined

### Phase 3: Wait for Approval

**User must explicitly approve the plan before execution**

### Phase 4: Execute Same Protocol as `/execute`

**After approval, follows identical execution protocol as `/execute`**:
- Use available tools systematically
- Spawn subagents if planned
- Work through implementation
- Integrate results and commit

## Example Flow

**`/plan` Flow**:
```
User: /plan implement user authentication system
Assistant: I'll create a plan for implementing user authentication system.

[Uses TodoWrite circuit breaker]

Execution Plan:
- Complexity: Complex
- **Subagent decision: YES** - Multiple independent subtasks (auth logic, research, testing) with estimated 30% time savings from parallel work
- Strategy:
  * Main: Core authentication logic implementation
  * Subagent 1: Research existing auth patterns in codebase
  * Subagent 2: Create comprehensive test suite
- Tools: Read, Write, Edit, Bash, Task
- Timeline: ~45 minutes with subagent coordination

[Waits for user approval]

User: Approved
Assistant: [Executes same protocol as /execute command]
```

## Key Characteristics

- ✅ **TodoWrite circuit breaker required**
- ✅ **User approval required** before execution
- ✅ **Plan presentation** with realistic assessment
- ✅ **Same execution protocol** as `/execute` after approval
- ✅ **Explicit subagent decision** - always YES/NO with reasoning

**Memory Enhancement**: This command automatically searches memory context using Memory MCP for relevant past planning approaches, execution patterns, and lessons learned to enhance plan quality and accuracy. See CLAUDE.md Memory Enhancement Protocol for details.
