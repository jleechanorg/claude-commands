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
- **Explicit subagent decision**: Always state YES/NO with reasoning
  - YES: Multiple independent subtasks benefit from parallel work
  - NO: Sequential dependencies or coordination overhead exceeds benefits
- Identify tool requirements and dependencies
- Present comprehensive implementation strategy

**Parallel Execution Decision Matrix**:

**✅ USE SUBAGENTS** (YES) when:
- **Comment Processing**: >25 comments requiring individual responses
- **Multi-file Analysis**: >15 files needing independent review/modification
- **Research Tasks**: Independent API research, documentation analysis, testing protocols
- **CI Analysis**: >2 different CI failures requiring specialized investigation
- **Security Scanning**: Sensitive files (auth, crypto, permissions) need dedicated analysis
- **Performance**: Task estimated >10 minutes can be parallelized effectively

**❌ NO SUBAGENTS** (NO) when:
- **Sequential Dependencies**: Each step requires previous step completion
- **Single File Focus**: Working on 1-3 related files with tight coupling
- **Simple Tasks**: <5 minute estimated completion time
- **Coordination Overhead**: Communication costs exceed parallel benefits
- **Resource Constraints**: Limited API quota or system resources
- **Solo Developer Context**: User prefers direct, simple approaches over complex orchestration

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
- Coordinate subagents if planned
- Validate and commit when complete

**Tool Usage**:
- `Read` - Understand existing code
- `Write` - Create new files
- `Edit` - Modify existing files
- `Bash` - Run tests, git operations
- `Task` - Spawn subagents for parallel work
- `TodoWrite` - Track implementation progress

## Example Flows

**Simple task**:
```
User: /e fix the login button styling
Assistant:
Phase 1 - Planning (/plan):
Creating implementation plan with TodoWrite...
[Creates checklist: Check styles, Update CSS, Test changes, Commit]
**Subagent decision: NO** - Simple task with sequential dependencies, coordination overhead exceeds benefits

Phase 2 - Approval Chain:
/preapprove - Validating plan completeness and context
/autoapprove - Triggering automatic approval mechanism
User already approves - proceeding with execution

Phase 3 - Implementation:
[Follows plan: Read current styles, Edit CSS, Test, Commit]
```

**Complex task**:
```
User: /e implement user authentication system
Assistant:
Phase 1 - Planning (/plan):
Creating comprehensive implementation plan...
[Creates detailed TodoWrite with multiple subtasks]
**Subagent decision: YES** - Multiple independent components (auth logic, research, testing) with estimated 35% time savings from parallel work
  - Agent 1: Research security best practices and OAuth integration
  - Agent 2: Design database schema and user models
  - Agent 3: Create authentication middleware and session handling
  - Agent 4: Develop frontend login/register components
  - Claude: Orchestrate integration and ensure security consistency

Phase 2 - Approval Chain:
/preapprove - Validating comprehensive plan and dependencies
/autoapprove - Triggering automatic approval for complex implementation
User already approves - proceeding with execution

Phase 3 - Implementation:
[Spawns 4 parallel agents for independent components]
[Updates TodoWrite progress throughout]
[Coordinates and integrates all components]
```

**Real-world PR example**:
```
User: /e /copilot 1062
Assistant:
Phase 1 - Planning (/plan):
Analyzing PR #1062 with 47 comments across 15 files...
**Subagent decision: YES** - 47 comments exceed threshold (>25), multiple CI failures detected
  - Agent 1: Process comments 1-16 (CodeRabbit batch)
  - Agent 2: Process comments 17-32 (Copilot batch)
  - Agent 3: Process comments 33-47 (Review comments)
  - Agent 4: Analyze CI failures and generate fixes
  - Claude: Coordinate responses and ensure consistency

Phase 2 - Approval Chain:
/preapprove - Large PR scope validated, parallel processing beneficial
/autoapprove - User already approves - proceeding with execution

Phase 3 - Implementation:
[Agents work in parallel while Claude orchestrates]
[Real-time progress updates for each agent's completion]
[Integration and final verification by Claude]
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
