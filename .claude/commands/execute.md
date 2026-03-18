---
description: Execute Command - Plan-Approve-Execute Composition
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 0: Native Memory Context

**Action Steps:**
1. **Read from Native Memory**: Use `memory_search` to search for relevant context about the task
2. **Retrieve Prior Learnings**: Search for related patterns, past implementations, and user preferences

### Phase 1: Planning (/planexec)

**Action Steps:**
**Executes `/planexec` command**: Follows the complete planning protocol documented in [`planexec.md`](./planexec.md)
1. **Memory Context Retrieval**: Search native memory for relevant context using `memory_search`
2. **Guidelines Consultation**: `/planexec` calls `/guidelines` directly for comprehensive consultation
3. **Comprehensive Context**: CLAUDE.md reading + base guidelines + PR/branch-specific guidelines via direct command composition
4. Creates TodoWrite checklist with specific steps including guidelines validation
4. Presents execution plan using the [Standard Plan Display Format](./planexec.md#📋-standard-plan-display-format)
5. Shows complexity, execution method, tools, timeline, and parallelization strategy
6. **Tool Selection**: Follows guidelines hierarchy (Serena MCP → Read tool → Bash commands)
7. Provides full visibility into the execution approach before auto-approval

### Phase 2: Approval Chain

**Action Steps:**
**Full Approval Workflow**:
1. **`/preapprove`**: Prepare approval context, validate plan completeness
2. **`/autoapprove`**: Trigger automatic approval mechanism (proceeds silently)
3. **Key difference from `/planexec`**: Built-in auto-approval eliminates manual approval requirement
4. Proceed directly to execution phase with approval satisfied

### Phase 3: Implementation

**Action Steps:**
**Execution**: Implements the approved plan from Phase 1
1. Updates TodoWrite status as tasks complete
2. Uses systematic tool progression and the execution method determined in planning
3. Executes tasks as planned (parallel Task tool agents or sequential based on plan decision)
4. 🚨 **PARALLEL TASK EXECUTION**: Can use multiple Task tool calls in single message for up to 10 concurrent subagents
5. Validates and commits when complete
6. **Writes to Native Memory**: Use `memory_save` to persist key learnings, patterns, and outcomes from the execution

## 📋 REFERENCE DOCUMENTATION

# Execute Command - Plan-Approve-Execute Composition

> **Summary**: `/execute` runs `/planexec`, auto-approves the generated plan,
> then performs execution with TodoWrite progress tracking in a single
> uninterrupted workflow.

**Purpose**: Execute tasks by composing `/planexec` → auto-approve → execute workflow

**Usage**: `/execute` or `/e` - Plan, auto-approve, then execute immediately

## 🚨 COMPOSITION PROTOCOL

### Command Flow

**The `/execute` command is a composition of**:
1. **`/planexec`** - Create detailed implementation plan with TodoWrite
2. **`/preapprove`** - Prepare approval context and validation
3. **`/autoapprove`** - Automatic approval mechanism (proceeds silently with execution)
4. **Execute** - Proceed with planned implementation

## Example Flows

**Simple task**:
```
User: /execute fix the login button styling
Assistant:
Phase 0 - Context Assessment:
Context Status: 65% remaining → Low context pressure

Phase 0.1 - Native Memory Context:
✅ Searching memory for related patterns and prior learnings
✅ Found X relevant memories for this task

Phase 1 - Planning (/planexec):
✅ CLAUDE.md read: Current rules, constraints, and protocols understood
✅ Guidelines consultation: `/guidelines` command completed - mistake prevention patterns applied
✅ Anti-patterns avoided: Using Edit tool for existing files, no _v2 or _backup files
Creating implementation plan with TodoWrite...
[Creates checklist: Check styles, Update CSS, Test changes, Commit]

[Displays execution plan using standard format from planexec.md]
Execution Plan:
- Task complexity: Simple (direct execution)
- **Execution method: Direct execution** - Simple file edits, no parallelization needed
- Tool requirements: Read, Edit, Bash (guidelines-validated tool selection)
- Implementation approach: Check current styling → Update CSS → Test → Commit
- Memory Integration: Native Claude memory for context and learning
- Expected timeline: ~10 minutes

Phase 2 - Approval Chain:
/preapprove - Validating plan completeness and context
/autoapprove - Proceeding with execution

Phase 3 - Implementation:
[Follows plan: Read current styles, Edit CSS, Test, Commit]
✅ Saved key learnings to native memory
```

**Complex task**:
```
User: /execute implement user authentication system
Assistant:
Phase 0 - Context Assessment:
Context Status: 32% remaining → High context pressure (< 35% threshold)

Phase 0.1 - Native Memory Context:
✅ Searching memory for related authentication patterns and prior learnings
✅ Found X relevant memories for auth implementation

Phase 1 - Planning (/planexec):
✅ CLAUDE.md read: Current rules, constraints, and security protocols understood
✅ Guidelines consultation: Applied security patterns from docs/pr-guidelines/{current}/guidelines.md + docs/pr-guidelines/base-guidelines.md
✅ Anti-patterns avoided: No subprocess shell=True, proper timeout enforcement, explicit error handling
Creating comprehensive implementation plan...
[Creates detailed TodoWrite with multiple subtasks]

[Displays execution plan using standard format from planexec.md]
Execution Plan:
- Task complexity: Complex (coordination needed)
- **Execution method: Sequential Tasks** - Security implementation requiring coordination
- Tool requirements: Read, Write, Edit, Bash, Task (guidelines-validated)
- Implementation approach: Research patterns → Core auth → Session management → Testing
- Guidelines applied: Subprocess safety, explicit error handling, 100% test coverage
- Memory Integration: Native Claude memory for context and learning
- Expected timeline: ~45 minutes

Sequential Task Plan:
- Main task: Implement core authentication system
- Task 1: Research existing auth patterns in codebase (using Serena MCP first)
- Task 2: Create security tests and documentation
- Integration: Apply patterns to implementation with test validation

Phase 2 - Approval Chain:
/preapprove - Validating comprehensive plan and dependencies
/autoapprove - Proceeding with implementation

Phase 3 - Implementation:
[Research: Auth patterns across codebase using Serena MCP]
[Implement: Core authentication system systematically]
[Updates TodoWrite progress throughout]
[Integrates findings with implementation]
✅ Saved key learnings and patterns to native memory
```

## Key Characteristics

- ✅ **Native Memory Integration** - Reads from and writes to Claude's native memory
- ✅ **Planned execution** - `/planexec` creates structured approach with detailed display
- ✅ **Plan presentation** - Shows complexity, execution method, tools, timeline, and strategy
- ✅ **Parallelization strategy** - Displays parallel vs sequential decision with reasoning
- ✅ **Full approval chain** - `/preapprove` + `/autoapprove` sequence
- ✅ **TodoWrite integration** - progress tracking built-in
- ✅ **Composition pattern** - combines 3 commands seamlessly
- ✅ **User approval message** - clear indication of auto-approval
- ✅ **Structured workflow** - plan → approval chain → execute phases

## Relationship to Other Commands

- **`/planexec`** - Just planning, requires manual approval, defines standard plan display format
- **`/execute`** - Planning + built-in auto-approval + execution (no manual approval needed), uses same display format as `/planexec`
- **`/preapprove`** - Prepare approval context and validation
- **`/autoapprove`** - Automatic approval mechanism that satisfies the approval requirement internally. When invoked, `/autoapprove` treats the plan as if the user explicitly approved it and proceeds directly to the execution phase. This command is integral to the `/execute` workflow, enabling seamless transitions from planning to implementation without user intervention.

**Format Consistency**: Both `/planexec` and `/execute` use the centralized plan display format documented in `planexec.md` to ensure consistent presentation of execution strategies and parallelization decisions.
