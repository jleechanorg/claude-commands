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

**Executes `/plan` command**: Follows the complete planning protocol documented in [`plan.md`](./plan.md)
- Creates TodoWrite checklist with specific steps
- Presents execution plan using the [Standard Plan Display Format](./plan.md#📋-standard-plan-display-format)
- Shows complexity, execution method, tools, timeline, and parallelization strategy
- Provides full visibility into the execution approach before auto-approval

### Phase 2: Approval Chain

**Full Approval Workflow**:
- **`/preapprove`**: Prepare approval context, validate plan completeness
- **`/autoapprove`**: Trigger automatic approval mechanism and display message: "User already approves - proceeding with execution"
- Bypass manual approval prompt that `/plan` normally requires
- Proceed directly to execution phase

### Phase 3: Implementation

**Execution**: Implements the approved plan from Phase 1
- Updates TodoWrite status as tasks complete
- Uses systematic tool progression and the execution method determined in planning
- Executes tasks as planned (parallel or sequential based on plan decision)
- Validates and commits when complete

## Example Flows

**Simple task**:
```
User: /execute fix the login button styling
Assistant:
Phase 1 - Planning (/plan):
Creating implementation plan with TodoWrite...
[Creates checklist: Check styles, Update CSS, Test changes, Commit]

[Displays execution plan using standard format from plan.md]
Execution Plan:
- Task complexity: Simple (direct execution)
- **Execution method: Direct execution** - Simple file edits, no parallelization needed
- Tool requirements: Read, Edit, Bash
- Implementation approach: Check current styling → Update CSS → Test → Commit
- Expected timeline: ~10 minutes

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

[Displays execution plan using standard format from plan.md]
Execution Plan:
- Task complexity: Complex (coordination needed)
- **Execution method: Sequential Tasks** - Security implementation requiring coordination
- Tool requirements: Read, Write, Edit, Bash, Task
- Implementation approach: Research patterns → Core auth → Session management → Testing
- Expected timeline: ~45 minutes

Sequential Task Plan:
- Main task: Implement core authentication system
- Task 1: Research existing auth patterns in codebase
- Task 2: Create security tests and documentation
- Integration: Apply patterns to implementation with test validation

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

- ✅ **Planned execution** - `/plan` creates structured approach with detailed display
- ✅ **Plan presentation** - Shows complexity, execution method, tools, timeline, and strategy
- ✅ **Parallelization strategy** - Displays parallel vs sequential decision with reasoning
- ✅ **Full approval chain** - `/preapprove` + `/autoapprove` sequence
- ✅ **TodoWrite integration** - progress tracking built-in
- ✅ **Composition pattern** - combines 3 commands seamlessly
- ✅ **User approval message** - clear indication of auto-approval
- ✅ **Structured workflow** - plan → approval chain → execute phases

## Relationship to Other Commands

- **`/plan`** - Just planning, requires manual approval, defines standard plan display format
- **`/execute`** - Planning + full approval chain + execution, uses same display format as `/plan`
- **`/preapprove`** - Prepare approval context and validation
- **`/autoapprove`** - Automatic approval mechanism that skips the manual approval step required by `/plan`. When invoked, `/autoapprove` treats the plan as if the user explicitly approved it and proceeds directly to the execution phase. This command is integral to the `/execute` workflow, enabling seamless transitions from planning to implementation without user intervention.

**Format Consistency**: Both `/plan` and `/execute` use the centralized plan display format documented in `plan.md` to ensure consistent presentation of execution strategies and parallelization decisions.
