# Execute Command - Plan-Approve-Execute Composition

> **Summary**: `/execute` runs `/plan`, auto-approves the generated plan,
> then performs execution with TodoWrite progress tracking in a single
> uninterrupted workflow.

**Purpose**: Execute tasks by composing `/plan` → auto-approve → execute workflow

**Usage**: `/execute` or `/e` - Plan, auto-approve, then execute immediately

## 🚨 COMPOSITION PROTOCOL

### Command Flow

**The `/execute` command is a composition of**:
1. **`/plan`** - Create detailed implementation plan with TodoWrite
2. **`/preapprove`** - Prepare approval context and validation
3. **`/autoapprove`** - Automatic approval mechanism that displays message: "User already approves - proceeding with execution"
4. **Execute** - Proceed with planned implementation

### Phase 1: Planning (/plan)

**Plan Generation**:
- Analyze task complexity and requirements
- Create TodoWrite checklist with specific steps
- **Execution method decision**: Choose optimal approach
  - **Parallel Tasks** (0 tokens): Simple, independent operations < 30s
  - **Sequential Tasks**: Complex workflows, coordinated operations
  - **Hybrid**: Parallel for research, sequential for implementation
  - See [parallel-vs-subagents.md](./parallel-vs-subagents.md) for criteria
- Identify tool requirements and dependencies
- Present comprehensive implementation strategy

### Phase 2: Approval Chain

**Full Approval Workflow**:
- **`/preapprove`**: Prepare approval context, validate plan completeness
- **`/autoapprove`**: Trigger automatic approval mechanism and display message: "User already approves - proceeding with execution"
- Bypass manual approval prompt that `/plan` normally requires
- Proceed directly to execution phase

### Phase 3: Implementation

**Execution Strategy**:
- Follow the plan created in Phase 1
- Update TodoWrite status as tasks complete
- Use systematic tool progression (Read → Write/Edit → Test)
- Execute tasks as planned (parallel or sequential)
- Validate and commit when complete

**Tool Usage**:
- `Read` - Understand existing code
- `Write` - Create new files
- `Edit` - Modify existing files
- `Bash` - Run tests, git operations
- `Task` - Handle parallel work coordination
- `TodoWrite` - Track implementation progress

## Example Flows

**Simple task**:
```
User: /execute fix the login button styling
Assistant:
Phase 1 - Planning (/plan):
Creating implementation plan with TodoWrite...
[Creates checklist: Check styles, Update CSS, Test changes, Commit]
**Execution method: Direct execution** - Simple file edits, no parallelization needed

Phase 2 - Approval Chain:
/preapprove - Validating plan completeness and context
/autoapprove - Triggering automatic approval mechanism
User already approves - proceeding with execution

Phase 3 - Implementation:
[Follows plan: Read current styles, Edit CSS, Test, Commit]
```

**Complex task**:
```
User: /execute implement user authentication system
Assistant:
Phase 1 - Planning (/plan):
Creating comprehensive implementation plan...
[Creates detailed TodoWrite with multiple subtasks]
**Execution method: Sequential approach**
- Sequential workflow: Research patterns, implement core system, testing
- Coordinated implementation following security best practices

Phase 2 - Approval Chain:
/preapprove - Validating comprehensive plan and dependencies
/autoapprove - Triggering automatic approval for complex implementation
User already approves - proceeding with execution

Phase 3 - Implementation:
[Research: Auth patterns across codebase]
[Implement: Core authentication system systematically]
[Updates TodoWrite progress throughout]
[Integrates findings with implementation]
```

## Key Characteristics

- ✅ **Planned execution** - `/plan` creates structured approach
- ✅ **Full approval chain** - `/preapprove` + `/autoapprove` sequence
- ✅ **TodoWrite integration** - progress tracking built-in
- ✅ **Composition pattern** - combines 3 commands seamlessly
- ✅ **User approval message** - clear indication of auto-approval
- ✅ **Structured workflow** - plan → approval chain → execute phases

## Relationship to Other Commands

- **`/plan`** - Just planning, requires manual approval
- **`/execute`** - Planning + full approval chain + execution
- **`/preapprove`** - Prepare approval context and validation
- **`/autoapprove`** - Automatic approval mechanism that skips the manual approval step required by `/plan`. When invoked, `/autoapprove` treats the plan as if the user explicitly approved it and proceeds directly to the execution phase. This command is integral to the `/execute` workflow, enabling seamless transitions from planning to implementation without user intervention.
