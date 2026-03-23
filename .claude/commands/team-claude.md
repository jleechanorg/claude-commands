---
description: Create a Claude-native agent team with opus orchestrating sonnet/haiku workers
type: agent-orchestration
execution_mode: immediate
---

## EXECUTION INSTRUCTIONS FOR CLAUDE

**When this command is invoked, YOU (Claude) must execute these steps immediately:**

1. Parse the user's prompt from the command arguments
2. Create a new team using `TeamCreate` with a descriptive name
3. Create tasks using `TaskCreate` for each subtask
4. Spawn teammates using `Agent` with `team_name` and `name` parameters
5. Coordinate via `SendMessage` and `TaskUpdate`
6. Shutdown teammates when complete

## HOW TEAM-CLAUDE WORKS

This command creates a **real Claude team** using the official TeamCreate infrastructure:
- **Opus** (you, the orchestrator/team lead) — plans, creates tasks, coordinates, reviews
- **Sonnet** teammates — `claude-pair-coder` and `claude-pair-verifier` for implementation and verification
- **Haiku** — quick tasks like file searches, simple checks, formatting

The team gets a shared task list, automatic message delivery between teammates, and coordinated task ownership.

## TEAM-CLAUDE COMMAND

Usage: `/team-claude <prompt>`

### Execution Steps:

1. **Create team:**
   ```python
   TeamCreate(
       team_name="claude-team-<short-description>",
       description="<what the team is working on>"
   )
   ```

2. **Create tasks** from the user's prompt:
   ```python
   TaskCreate(subject="<task>", description="<details>")
   ```
   Set up `blockedBy` dependencies between tasks where needed.

3. **Spawn sonnet teammates:**
   ```python
   Agent(
       subagent_type="claude-pair-coder",
       model="sonnet",
       name="coder-1",
       team_name="claude-team-<name>",
       description="<task description>",
       prompt="<detailed prompt>",
       run_in_background=True
   )
   ```
   ```python
   Agent(
       subagent_type="claude-pair-verifier",
       model="sonnet",
       name="verifier-1",
       team_name="claude-team-<name>",
       description="<verification description>",
       prompt="<detailed prompt>",
       run_in_background=True
   )
   ```

4. **Use haiku for lightweight tasks:**
   ```python
   Agent(
       model="haiku",
       name="scout",
       team_name="claude-team-<name>",
       description="<quick task>",
       prompt="<simple task prompt>"
   )
   ```

5. **Orchestrate via task list:**
   - Teammates check `TaskList` for available work
   - Claim tasks with `TaskUpdate(owner="coder-1")`
   - Mark tasks done with `TaskUpdate(status="completed")`
   - Communicate via `SendMessage(to="coder-1", message="...")`

6. **Shutdown teammates** when all tasks complete:
   ```python
   SendMessage(
       to="coder-1",
       message={"type": "shutdown_request", "reason": "All tasks complete"}
   )
   ```

### Model Budget Rules:
- **Opus**: Only for orchestration decisions, final review, complex reasoning
- **Sonnet**: Primary workhorse — coding, testing, verification, code review
- **Haiku**: File lookups, simple checks, formatting, trivial subtasks
- **Goal**: Maximize sonnet usage, minimize opus token spend

### Key Differences from Raw Agent() Calls:
- **Shared task list** — all teammates see progress and can claim work
- **Message routing** — teammates can communicate with each other and the lead
- **Task ownership** — prevents duplicate work, tracks who's doing what
- **Idle management** — teammates wake up when messaged with new work
- **Graceful shutdown** — proper cleanup when work is done

### Example:
```
/team-claude Implement bd-awq PR poller plugin with TDD — write failing tests first, then implement
```
