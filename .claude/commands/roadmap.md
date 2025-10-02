---
description: Roadmap Command
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: 2. **Integrated Workflow Execution**

**Action Steps:**
For each task, execute in sequence:
1. **`/think light`** - Quick analysis to understand task scope
2. **`/plan`** - Create detailed execution plan with optimal strategy
3. **`/handoff`** - Generate handoff branches and coordinate parallel work

## 📋 REFERENCE DOCUMENTATION

# Roadmap Command

**Purpose**: Update roadmap files with enhanced multi-task parallel processing and integrated agent workflow

**Action**: Commit local changes, switch to main, update roadmap/*.md, push to origin, switch back

**Usage**:
- `/roadmap` or `/r` - Single task (traditional mode)
- `/roadmap task1, task2, task3` - **Multi-task parallel processing** (comma-separated)
- `/roadmap "complex task 1" "simple task 2"` - **Multiple quoted tasks** for complex descriptions
- `/roadmap task1 task2 task3` - **Space-separated multiple tasks** (alternative format)

**Multi-Task Support**: The `/roadmap` command can process **multiple tasks simultaneously**. This is especially useful for:
- Breaking down large analysis work into focused individual tasks
- Creating parallel development streams
- Organizing related work items with proper task IDs and tracking

**MANDATORY**: When using `/roadmap` command, follow this exact sequence:

1. **Autonomy-Focused Task Clarification**: Ask detailed clarifying questions with the explicit goal of making tasks as autonomous as possible. Gather all necessary context, constraints, and requirements upfront.

2. **Task Classification**: Suggest classifications prioritizing autonomy:
   - **Small & LLM Autonomous**: LLM can complete independently with minimal guidance (PREFERRED)
   - **Small & Human-Guided**: Needs human oversight but straightforward
   - **Medium**: Requires detailed planning
   - **Large**: Requires comprehensive scratchpad

3. **Comprehensive Requirements Definition**: Based on classification:
   - **Small & LLM Autonomous**: Add complete 1-2 sentence requirements with all context needed
   - **Small & Human-Guided**: Add detailed 3-5 sentence requirements covering edge cases
   - **Medium**: ALWAYS create detailed `roadmap/scratchpad_task[NUMBER]_[brief-description].md` with implementation plan
   - **Large**: ALWAYS create comprehensive `roadmap/scratchpad_task[NUMBER]_[brief-description].md` with architecture and phases
   - **Any Detailed Task**: If defining tasks to a detailed degree during planning, ALWAYS create scratchpad files regardless of classification

4. **Autonomy Validation**: Before finalizing, verify each task has sufficient detail for independent execution

5. Record current branch name

6. If not on main branch:
   - Check for uncommitted changes with `git status`
   - If changes exist, commit them with descriptive message

7. Switch to main branch: `git checkout main`

8. Pull latest changes: `git pull origin main`

9. Create clean roadmap update branch: `git checkout -b roadmap-update-[timestamp]`

10. Make requested changes to:
   - `roadmap/roadmap.md` (main roadmap file)
   - `roadmap/sprint_current.md` (current sprint status)
   - `roadmap/scratchpad_task[NUMBER]_[description].md` (if applicable)

11. Commit changes with format: `docs(roadmap): [description]`

12. Push branch: `git push origin HEAD:roadmap-update-[timestamp]`

13. Create PR: `gh pr create --title "docs(roadmap): [description]" --body "Roadmap update via /roadmap command"`

14. Switch back to original branch: `git checkout [original-branch]`

15. **MANDATORY**: Explicitly report merge status: "✅ PR CREATED" with PR link for user to merge

**Files Updated**: `roadmap/roadmap.md`, `roadmap/sprint_current.md`, and task scratchpads as needed

**Workflow**: All roadmap changes now follow standard PR workflow - no exceptions to main push policy

## Enhanced Multi-Task Parallel Processing

**When multiple tasks are provided**, the command automatically:

### 1. **Task Parsing & Analysis**

- Parse comma-separated tasks or multiple arguments
- Identify task complexity and dependencies
- Group related tasks for efficient processing

### 3. **Parallel Task Coordination**

- Spawn dedicated tasks for each work item using `/orchestrate`
- Create isolated worktrees for conflict-free parallel work
- Each task works on its own feature branch
- Tasks execute autonomously with progress tracking

### 4. **Progress Tracking**

- Update `roadmap/roadmap.md` with parallel task status:
  ```
  ## Active Parallel Tasks (Auto-Generated)
  - **TASK-1234-AUTH** 🟡 [Agent: task-agent-1234] - Implementing authentication
  - **TASK-1235-API** 🟡 [Agent: task-agent-1235] - Building REST endpoints
  - **TASK-1236-UI** 🟢 [Agent: task-agent-1236] - Creating UI components
  ```
- Status indicators:
  - 🟢 Ready/Completed
  - 🟡 In Progress
  - 🔴 Blocked/Failed
  - ⚪ Pending

### 5. **Branch Management**

- Each task gets its own feature branch: `feature/task-[id]-[name]`
- Handoff branches for documentation: `handoff-[task-name]`
- Clean separation prevents merge conflicts

### 6. **Automatic PR Creation**

- Each completed task creates its own PR
- PRs reference the parent roadmap task
- Cross-references between related PRs

## Example Multi-Task Usage

```
User: /roadmap implement auth system, create API docs, add unit testsAssistant: I'll process these 3 tasks in parallel. Let me analyze each one:

[Executes /think light for each task]

Task 1: Implement auth system - Complex, needs design
Task 2: Create API docs - Medium, documentation task
Task 3: Add unit tests - Small, testing task

[Executes /plan for each task with optimal strategies]

[Executes /handoff for each task, creating branches]

Now spawning parallel tasks:
- Task task-1234 → Implementing auth system
- Task task-1235 → Creating API docs
- Task task-1236 → Adding unit tests

[Updates roadmap.md with parallel task tracking]

You can monitor progress with:
- `tmux attach -t task-agent-1234` (auth)
- `tmux attach -t task-agent-1235` (docs)
- `tmux attach -t task-agent-1236` (tests)
```

## Implementation Flow

1. **Parse Tasks**: Split by commas or process multiple args
2. **For Each Task**:
   - Execute `/think light` to analyze
   - Execute `/plan` to create strategy
   - Execute `/handoff` to create work branch
   - Spawn agent via `/orchestrate`
3. **Update Roadmap**: Add parallel task section
4. **Monitor Progress**: Track agent status
5. **Merge Results**: As agents complete tasks

## Implementation Approach

**LLM-Native Design**: This enhanced roadmap command works through Claude's natural interpretation of the above specifications, similar to other slash commands like `/think`, `/plan`, and `/handoff`.

When you use `/roadmap` with multiple tasks, Claude will:
1. Parse the input according to the specifications above
2. Execute the integrated workflow sequence naturally
3. Spawn agents via `/orchestrate` for parallel processing
4. Update roadmap.md with progress tracking

This LLM-native approach provides flexibility while maintaining consistency through clear documentation.
