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
3. **`/autoapprove`** - Automatic approval mechanism (proceeds silently with execution)
4. **Execute** - Proceed with planned implementation

### Phase 1: Planning (/plan)

**Executes `/plan` command**: Follows the complete planning protocol documented in [`plan.md`](./plan.md)
- **Guidelines Consultation**: `/plan` calls `/guidelines` directly for comprehensive consultation
- **Comprehensive Context**: CLAUDE.md reading + base guidelines + PR/branch-specific guidelines via direct command composition
- Creates TodoWrite checklist with specific steps including guidelines validation
- Presents execution plan using the [Standard Plan Display Format](./plan.md#📋-standard-plan-display-format)
- Shows complexity, execution method, tools, timeline, and parallelization strategy
- **Tool Selection**: Follows guidelines hierarchy (Serena MCP → Read tool → Bash commands)
- Provides full visibility into the execution approach before auto-approval

### Phase 2: Approval Chain

**Full Approval Workflow**:
- **`/preapprove`**: Prepare approval context, validate plan completeness
- **`/autoapprove`**: Trigger automatic approval mechanism (proceeds silently)
- **Key difference from `/plan`**: Built-in auto-approval eliminates manual approval requirement
- Proceed directly to execution phase with approval satisfied

### Phase 3: Implementation

**Execution**: Implements the approved plan from Phase 1
- Updates TodoWrite status as tasks complete
- Uses systematic tool progression and the execution method determined in planning
- Executes tasks as planned (parallel Task tool agents or sequential based on plan decision)
- 🚨 **PARALLEL TASK EXECUTION**: Can use multiple Task tool calls in single message for up to 10 concurrent subagents
- Validates and commits when complete