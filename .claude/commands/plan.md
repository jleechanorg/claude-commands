# Plan Command - Execute with Approval

**Purpose**: Same as `/execute` but requires user approval before implementation

**Usage**: `/plan` - Present execution plan and wait for approval

## 🧠 MEMORY INTEGRATION

**Enhanced Planning with Memory MCP**: `/plan` automatically consults Memory MCP before creating execution plans to apply learned patterns, user preferences, and corrections.

### Pre-Planning Memory Query
- **Automatic Consultation**: Queries learned patterns relevant to the task
- **Pattern Categorization**: Groups findings by type (corrections, preferences, workflows)
- **Context Integration**: Applies memory insights to planning decisions
- **Execution Strategy**: Uses memory patterns to inform parallel vs sequential choices

## 🚨 PLAN PROTOCOL

### Phase 1: TodoWrite Circuit Breaker (MANDATORY)

**Required TodoWrite Checklist**:
```
## PLANNING PROTOCOL CHECKLIST - ENHANCED WITH MEMORY
- [ ] Memory consultation completed: ✅ YES
- [ ] Memory insights applied: [Count] relevant patterns found
- [ ] Context check: ___% remaining
  *Guidance*: Estimate the percentage of the task or project that remains incomplete. For example, if 3 out of 10 subtasks are done, the remaining percentage is 70%.
- [ ] Complexity assessment: Simple/Complex (memory-informed)
- [ ] Execution method decision: Parallel Tasks/Sequential with reasoning
  *Required*: Must state "Parallel Tasks - [reason]" or "Sequential - [reason]"
  *Reference*: See [parallel-vs-subagents.md](./parallel-vs-subagents.md) for decision criteria
- [ ] Tool requirements: Read, Write, Edit, Bash, Task
- [ ] Memory-enhanced execution plan presented to user
- [ ] User approval received
```

❌ **NEVER proceed without explicit user approval marked as checked (`[x]`) in the checklist**

### Phase 2: Present Execution Plan

**Analysis Presentation**:
- **Task complexity**: Simple (direct execution) or Complex (coordination needed)
- **Execution method decision** (memory-informed):
  - **Parallel Tasks** (0 extra tokens): For simple, independent operations < 30s
  - **Sequential Tasks**: For complex workflows or coordinated operations
  - See [parallel-vs-subagents.md](./parallel-vs-subagents.md) for full criteria
- **Tool requirements**: Which tools will be used
- **Implementation approach**: Step-by-step plan
- **Expected timeline**: Realistic estimate

**Parallel Tasks Plan (if applicable)**:
- **Method**: Background processes (&), GNU parallel, xargs, or batched calls
- **Tasks**: List of independent operations to run in parallel
- **Aggregation**: How results will be combined

**Sequential Task Plan (if applicable)**:
- **Main task**: What I'll focus on
- **Task 1**: Independent analysis/research task
- **Task 2**: Documentation/testing task
- **Integration**: How results will be combined

### Phase 3: Wait for Approval

**User must explicitly approve the plan before execution**

### Phase 4: Execute Same Protocol as `/execute`

**After approval, follows identical execution protocol as `/execute`**:
- Use available tools systematically
- Execute tasks as planned (parallel or sequential)
- Work through implementation
- Integrate results and commit

## Example Flow

**`/plan` Flow**:
```
User: /plan implement user authentication system
Assistant: I'll create a plan for implementing user authentication system.

[Uses TodoWrite circuit breaker]

Memory-Enhanced Execution Plan:
- Complexity: Complex (memory-informed)
- **Execution method: Sequential Tasks** (applying learned patterns)
  - Sequential workflow for: Security implementation requiring coordination
  - Memory insight: Authentication systems need careful step-by-step validation
- Applied memory corrections: POST methods, session-based auth, rate limiting
- Tools: Read, Write, Edit, Bash (using `/e` based on memory patterns)
- Timeline: ~45 minutes (includes security pattern application)

[Waits for user approval]

User: Approved
Assistant: [Executes same protocol as /execute command]
```

## Key Characteristics

- ✅ **TodoWrite circuit breaker required**
- ✅ **User approval required** before execution
- ✅ **Plan presentation** with realistic assessment
- ✅ **Same execution protocol** as `/execute` after approval
- ✅ **Execution-method decision recorded** – "Parallel Tasks – [reason]" or "Sequential Tasks – [reason]" with clear rationale

**Memory Enhancement**: This command automatically searches memory context using Memory MCP for relevant past planning approaches, execution patterns, and lessons learned to enhance plan quality and accuracy. See CLAUDE.md Memory Enhancement Protocol for details.
