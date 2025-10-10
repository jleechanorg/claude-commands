# Multi-Agent Orchestration System

A **simple, working implementation** of AI agent orchestration that creates general-purpose agents on-demand to complete development tasks and create pull requests.

> **📋 Complete Design Documentation**: See [A2A_DESIGN.md](./A2A_DESIGN.md) for comprehensive A2A architecture and implementation details.

## ✅ System Overview

This system implements the **core design philosophy**: **one general agent per task** with **A2A (Agent-to-Agent) communication**

- **Simple**: Create agent → Agent works in tmux → Agent creates PR → Task complete
- **Isolated**: Each agent gets fresh git worktree from main branch
- **Reliable**: Mandatory PR creation ensures task completion
- **Monitored**: Lightweight Python coordinator tracks progress
- **A2A Protocol**: File-based inter-agent communication for coordination
- **Production Ready**: Complete A2A implementation with comprehensive testing
- **Massive Cleanup**: Removed 16,596 lines of outdated POC implementations

## 🎯 What It Actually Does

```bash
# User types this:
/orch "Fix all failing tests"

# System does this:
✅ Creates task-agent-1234 in tmux session
✅ Creates fresh git worktree from main branch
✅ Agent completes task in isolated workspace
✅ Agent commits, pushes, and creates PR
✅ Monitor tracks progress every 2 minutes
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│         File-Based A2A Protocol + Simple Safety Boundaries     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Task Pool   │  │Agent Registry│  │Safety Rules │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│  Terminal 1         │ │  Terminal 2         │ │  Terminal 3         │
│  ┌─────────────┐    │ │  ┌─────────────┐    │ │  ┌─────────────┐    │
│  │ Agent Mon   │    │ │  │ Task Agent  │    │ │  │ Task Agent  │    │
│  │ (Monitor)   │────┼─┼─▶│ (A2A Client)│◀───┼─┼─▶│ (A2A Client)│    │
│  └─────────────┘    │ │  └─────────────┘    │ │  └─────────────┘    │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                                │
                                ▼
                        File System: /tmp/orchestration/a2a/
```

## 🚀 Quick Start

### Prerequisites

```bash
# Ensure tmux is installed
sudo apt-get install tmux

# No external dependencies required - pure file-based coordination

# Install an LLM CLI (at least one of the following)
# - Claude Code CLI (`claude`) – see main README for setup
# - Codex CLI (`codex`) – ensure the `codex` binary is on your PATH

# Ensure git and gh CLI are available
which git gh  # Should show both commands
```

### Starting the System

```bash
# Start the orchestration system (starts agent monitor)
./orchestration/start_system.sh start

# Create agents via your preferred CLI (Claude Code or Codex)
/orch "Find and fix all inline imports"

# Direct orchestration command (for testing)
python3 orchestration/orchestrate_unified.py "Update the UI styling"

# Constraint examples
/orch "update mvp_site/readme.md with latest info. only update that file"
/orch "fix tests --max-changes 3 --no-servers"
```

## 🛡️ Simple Safety Boundary System

### Clear, Reliable Boundaries
Uses simple safety rules that apply consistently to all tasks:

**How It Works:**
```python
# No task classification - just clear boundaries for all tasks
task = "investigate why debug mode setting is ignored during character creation"
constraints = simple_constraints.create_constraints(max_files=50)
# Result: 50 file limit + safety boundaries + rich task description ✅
```

### Real Example: Debug Mode Investigation

**User Command:**
```bash
/orch "investigate why debug mode setting is ignored during character creation"
```

**Simple Boundary Process:**
1. **Task Description**: Passed directly to agent with full context
2. **Safety Boundaries**: Standard 50 file limit + forbidden paths/patterns
3. **No Classification**: Agent understands task from description, not constraints
4. **Clear Guidance**: Rich prompt explains task intent and approach

**Result:** Agent `task-agent-80914589` created with clear task understanding and safety boundaries

### Safety Boundary Examples

| Task Description | Old System (Complex) | New System (Simple) | Max Files |
|-----------------|---------------------|---------------------|-----------|
| `"update README.md with API changes"` | Pattern classification → doc constraints | No classification needed | 50 |
| `"investigate authentication logic"` | Keyword matching → debug constraints | Agent understands from context | 50 |
| `"run all tests and fix failures"` | Pattern matching → test constraints | Agent gets clear task description | 50 |
| `"change database timeout in config"` | Keyword matching → config constraints | Agent understands intent from task | 50 |

### Interactive Clarification

For ambiguous tasks, the LLM asks for clarification:

```
Task: "debug the configuration system"

🤔 This task mentions both settings/config and debugging. Should I:
1. Access source code files to investigate the logic/behavior?
2. Only access configuration files to change settings?
3. Both source code and config files?

User: "Access source code - need to investigate the logic"
✅ Result: Debugging constraints with Python file access
```

### Constraint Types Applied

**File Constraints:**
- `allowed_files`: Specific patterns like `['*.py', 'mvp_site/*']`
- `forbidden_files`: Dangerous patterns automatically excluded
- `max_file_changes`: Intelligent limits based on task scope

**Action Constraints:**
- `allowed_actions`: `['file_edit', 'test_run', 'git_commit', 'pr_create']`
- `forbidden_actions`: `['server_start', 'file_delete']` for safety

**Scope Constraints:**
- Single file updates: `max_file_changes: 1`
- Investigation tasks: `max_file_changes: 10`
- Broad refactoring: `max_file_changes: 15`

## 📁 Key Components

### Core Files
- **orchestrate_unified.py** - Main entry point for agent creation
- **task_dispatcher.py** - Task routing with dynamic agent assignment
- **a2a_integration.py** - File-based A2A protocol implementation (788 lines)
- **a2a_agent_wrapper.py** - Wrapper for existing agents to use A2A
- **llm_constraint_inference.py** - LLM-native constraint system (394 lines)
- **constraint_system.py** - TaskConstraints dataclass and inference engine
- **constraint_command_parser.py** - Parse user constraint overrides
- **agent_monitor.py** - Agent health monitoring via file-based protocol

### Agent Management
- **agent_monitor.py** - Monitors agent health and tmux sessions
- **start_system.sh** - System startup script

### LLM-Native Constraint System
- **llm_constraint_inference.py** - Natural language constraint determination
- **TaskConstraints** - Dataclass for constraint specifications
- **constraint_command_parser.py** - Parse user constraint flags
- **Interactive clarification** - Handles ambiguous task requirements

## 🔄 How It Works

1. **Task Submission**: User submits task via `/orch` command
2. **LLM Constraint Analysis**: Natural language understanding determines appropriate constraints
3. **Interactive Clarification**: System asks for clarification if task is ambiguous
4. **Agent Creation**: Creates general-purpose agent in tmux session with LLM-inferred constraints
5. **A2A Registration**: Agent registers with file-based A2A protocol
6. **Task Execution**: Agent works in isolated git worktree with smart constraints applied
7. **Inter-Agent Communication**: Agents communicate via file-based messaging with constraint data
8. **PR Creation**: Agent creates PR when task complete (mandatory)

## 📋 Complete Flow: `/orch` → PR Creation

### 1. **User Types Command**
```bash
/orch "Fix all failing tests"
```

### 2. **Claude CLI Processing**
- The `/orch` command is handled by `.claude/commands/orchestrate.md`
- This triggers execution of `orchestration/orchestrate_unified.py`

### 3. **Unified Orchestration System Starts**
```python
# orchestrate_unified.py
class UnifiedOrchestration:
    def orchestrate(self, task_description):
        # Check dependencies (tmux, git, gh, claude)
        # File-based A2A coordination always available
        # Call task dispatcher to analyze and create agents
```

### 4. **Task Analysis & Agent Creation with Constraints**
```python
# task_dispatcher.py
def analyze_task_and_create_agents_with_constraints(self, task_description, user_constraints=None):
    # Infer constraints from task description
    base_constraints = self.constraint_inference.infer_constraints(task_description)

    # Apply user overrides if provided
    if user_constraints:
        final_constraints = self.constraint_inference.apply_user_constraints(
            base_constraints, user_constraints
        )

    # Create agent with constraints
    return [{
        "name": f"task-agent-{timestamp}",
        "type": "development",
        "focus": task_description,
        "capabilities": ["task_execution", "development", "git_operations"],
        "constraints": final_constraints,
        "prompt": f"Task: {task_description}\n\nConstraints: {final_constraints}..."
    }]
```

### 5. **Dynamic Agent Creation**
```python
# task_dispatcher.py
def create_dynamic_agent(self, agent_spec):
    # Create git worktree from main branch
    subprocess.run(['git', 'worktree', 'add', '-b', branch_name, agent_dir, 'main'])

    # Generate comprehensive prompt with MANDATORY completion steps
    # Create tmux session with Claude
    tmux_cmd = [
        'tmux', 'new-session', '-d', '-s', agent_name,
        '-c', agent_dir,
        f'{claude_path} --model sonnet -p @{prompt_file}'
    ]
```

### 6. **Agent Executes Task**
The agent (Claude in tmux session) receives a prompt that includes:
- The specific task to complete
- Working directory and branch info
- **MANDATORY completion steps**:
  1. Complete the task
  2. Stage and commit changes
  3. Push branch to origin
  4. **Create PR using `gh pr create`**
  5. Write completion report

### 7. **PR Creation (Built into Agent Prompt)**
```bash
# The agent MUST execute these commands:
git add -A
git commit -m "Complete [task]..."
git push -u origin [branch-name]

# CREATE THE PR - THIS IS MANDATORY
gh pr create --title "Agent [name]: [task]" \
  --body "## Summary\n[details]..."

# Verify PR creation
gh pr view --json number,url
```

### 8. **Completion Verification**
- Agent writes to `/tmp/orchestration_results/[agent-name]_results.json`
- The prompt includes: **"❌ FAILURE TO CREATE PR = INCOMPLETE TASK"**
- Agent cannot terminate until PR is created and verified

### 9. **Key Points**

1. **PR Creation is MANDATORY** - Built into the agent prompt with explicit failure conditions
2. **Fresh Branch Policy** - Agents always branch from `main`, not current branch
3. **A2A Integration** - File-based coordination for agent communication
4. **Self-Contained** - Each agent has everything needed to complete task → PR
5. **Verification Required** - Agent must verify PR creation with `gh pr view`

The system ensures PR creation by making it part of the agent's core instructions, with clear failure criteria if skipped.

## 🔄 A2A Protocol: Concrete Examples

### File System Structure

The A2A protocol uses a simple file-based messaging system:

```
/tmp/orchestration/a2a/
├── registry.json                    # Global agent registry
├── agents/
│   └── task-agent-80914589/
│       ├── info.json               # Agent capabilities and status
│       ├── heartbeat.json          # Last heartbeat timestamp
│       └── inbox/                  # Incoming A2A messages
│           ├── processed/          # Archived messages
│           └── msg_1234.json       # Pending message
└── tasks/
    ├── available/                  # Task pool with constraints
    ├── claimed/                    # Active tasks
    └── completed/                  # Finished tasks
```

### Agent Registration Example

When an agent starts, it registers with the A2A system:

```json
// /tmp/orchestration/a2a/registry.json
{
  "task-agent-80914589": {
    "agent_id": "task-agent-80914589",
    "agent_type": "development",
    "capabilities": ["file_edit", "git_operations", "debugging", "pr_create"],
    "status": "idle",
    "current_task": null,
    "constraints": {
      "allowed_files": ["*.py", "mvp_site/*", "src/*"],
      "max_file_changes": 10,
      "constraint_source": "llm_native"
    },
    "created_at": 1753543971.23,
    "last_heartbeat": 1753543971.23,
    "workspace": "/tmp/agents/task-agent-80914589"
  }
}
```

### A2A Message Format

Agents communicate using structured JSON messages:

```json
// /tmp/orchestration/a2a/agents/task-agent-80914589/inbox/msg_1234.json
{
  "id": "msg-uuid-1234",
  "from_agent": "orchestrator",
  "to_agent": "task-agent-80914589",
  "message_type": "delegate",
  "payload": {
    "task_id": "debug-mode-investigation",
    "task_description": "investigate why debug mode setting is ignored during character creation",
    "constraints": {
      "allowed_files": ["*.py", "mvp_site/*", "src/*"],
      "forbidden_actions": ["server_start", "file_delete"],
      "max_file_changes": 10,
      "scope_description": "LLM-determined: debugging task with investigation scope",
      "constraint_source": "llm_native"
    },
    "requirements": ["debugging", "python", "file_edit"],
    "deadline": 3600
  },
  "timestamp": 1753543971.23,
  "reply_to": null
}
```

### Task Broadcasting with LLM Constraints

When orchestrator creates a task, it broadcasts via A2A with LLM-inferred constraints:

```python
# 1. LLM analyzes task
task = "investigate why debug mode setting is ignored during character creation"
constraints = llm_inference.infer_constraints(task)

# 2. Create A2A task message
task_data = {
    "task_id": str(uuid.uuid4()),
    "description": task,
    "constraints": constraints.to_dict(),
    "requirements": ["debugging", "python", "file_edit"],
    "created_at": time.time()
}

# 3. Broadcast to all agents
a2a_protocol.broadcast_task(task_data)
```

### Agent Task Claiming

Agents discover and claim tasks atomically:

```python
# Agent polls for new tasks
available_tasks = a2a_protocol.get_available_tasks()

for task in available_tasks:
    # Check if agent capabilities match requirements
    if agent.can_handle_task(task):
        # Atomic claim with file locking
        if a2a_protocol.claim_task(task["task_id"], agent.id):
            # Task successfully claimed
            agent.execute_task(task)
            break
```

### Constraint Enforcement During Execution

Agents enforce LLM-inferred constraints during task execution:

```python
# Before each file operation
def edit_file(self, file_path: str):
    # Check against LLM-inferred constraints
    if not self.constraints.allows_file_access(file_path):
        self.log_violation(f"File {file_path} not in allowed patterns: {self.constraints.allowed_files}")
        return False

    if self.file_changes >= self.constraints.max_file_changes:
        self.log_violation(f"Max file changes ({self.constraints.max_file_changes}) exceeded")
        return False

    # Proceed with edit
    self.perform_edit(file_path)
    self.file_changes += 1
```

### Agent Status Updates

Agents send periodic heartbeats and status updates:

```json
// /tmp/orchestration/a2a/agents/task-agent-80914589/heartbeat.json
{
  "agent_id": "task-agent-80914589",
  "status": "working",
  "current_task": "debug-mode-investigation",
  "progress": {
    "files_analyzed": ["mvp_site/main.py", "mvp_site/game_state.py"],
    "files_modified": [],
    "constraint_violations": 0
  },
  "timestamp": 1753543971.23
}
```

### Task Completion with Results

When finished, agents report results through A2A:

```json
// Agent completion message
{
  "message_type": "result",
  "payload": {
    "task_id": "debug-mode-investigation",
    "status": "completed",
    "files_modified": ["mvp_site/main.py", "mvp_site/debug_mode_parser.py"],
    "pr_url": "https://github.com/user/repo/pull/123",
    "constraint_compliance": {
      "files_within_allowed": true,
      "max_changes_respected": true,
      "forbidden_actions_avoided": true,
      "violations": []
    },
    "summary": "Found debug mode logic issue in main.py line 456. Fixed conditional check."
  }
}
```

### Real Command Flow

Here's what happens when you run a real command:

```bash
/orch "investigate why debug mode setting is ignored during character creation"
```

**A2A Message Flow:**
1. **LLM Analysis** → Debugging task, needs Python source access
2. **Task Creation** → Broadcast to A2A with constraints
3. **Agent Discovery** → `task-agent-80914589` finds task in inbox
4. **Task Claiming** → Atomic claim with file locking
5. **Constraint Application** → Agent restricted to `['*.py', 'mvp_site/*']`
6. **Execution** → Agent investigates debug logic in Python files
7. **PR Creation** → Agent creates PR with actual bug fix
8. **Result Reporting** → Success reported back through A2A

This complete A2A flow ensures agents work within LLM-determined boundaries while maintaining decentralized coordination.

## 📊 Monitoring & Status

### Basic Monitoring Commands

```bash
# List all active agents
tmux ls | grep agent

# Attach to a specific agent
tmux attach -t task-agent-1234

# View A2A system status
ls -la /tmp/orchestration/a2a/

# Check agent registry
cat /tmp/orchestration/a2a/registry.json | jq

# View available tasks
ls -la /tmp/orchestration/a2a/tasks/available/

# View agent logs
tail -f /tmp/orchestration_logs/agent_monitor.log
```

### Status Command

The orchestration system provides status monitoring through various methods:

```bash
# Run the monitoring script (updates every 10 seconds)
./orchestration/monitor_agents.sh

# Check agent sessions directly
tmux ls | grep -E "(agent|opus)"

# View completion results
ls -la /tmp/orchestration_results/

# Natural language status (when implemented in orchestrate.md)
/orch What's the status?
/orch monitor agents
/orch How's the progress?
```

#### What Status Shows

1. **System Components**:
   - File-based A2A coordination status
   - Opus-master coordinator status
   - Active agent count

2. **Agent Information**:
   - Agent names and types
   - Current tasks
   - Working directories
   - Creation timestamps
   - Current status (working/completed/failed)

3. **Task Progress**:
   - Task descriptions
   - Time elapsed
   - Completion status
   - Result file locations

4. **Advanced Status Options**:
   ```bash
   # Check specific agent
   tmux capture-pane -t task-agent-1234 -p | tail -50

   # View agent result files
   ls -la /tmp/orchestration_results/
   cat /tmp/orchestration_results/task-agent-1234_results.json

   # Check agent logs
   tail -f /tmp/orchestration_logs/task-agent-1234.log
   ```

#### Status Implementation

**monitor_agents.sh** provides real-time monitoring by:
1. Displaying running tmux sessions with last 5 lines of output
2. Showing shared status from `tasks/shared_status.txt`
3. Counting pending tasks in task files
4. Auto-refreshing every 10 seconds

**Manual status checking**:
1. Check tmux sessions for active agents
2. Read result files from `/tmp/orchestration_results/`
3. Query file-based A2A registry for active agents
4. Parse agent logs in `/tmp/orchestration_logs/`
5. View agent output with `tmux capture-pane`

**Future enhancement**: Natural language status queries (e.g., "What's the status?") will be handled by extending the orchestrate.md command to parse status-related queries and return formatted reports.

## 🔧 Configuration

Environment variables:
- `CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192` - Token limit for Claude
- `A2A_BASE_DIR=/tmp/orchestration/a2a` - A2A file system location
- `ORCHESTRATION_LOGS_DIR=/tmp/orchestration_logs` - Agent logs location

Constraint system settings:
- **Single file detection**: Automatically detects "update X file" patterns
- **Resource limits**: Memory and timeout constraints for agents
- **Action restrictions**: Control which operations agents can perform
- **Scope boundaries**: Limit agent access to specific directories/files

## 📚 Documentation

- [A2A_DESIGN.md](./A2A_DESIGN.md) - Complete A2A system design and architecture
- [README_A2A_INTEGRATION.md](./README_A2A_INTEGRATION.md) - Historical A2A protocol reference
- File system structure documentation in each component file


## ⚡ Key Features

- **File-based A2A protocol** with inbox/outbox messaging
- **Intelligent constraint inference** from natural language
- **tmux terminal separation** for visual monitoring
- **Dynamic agent creation** (one general agent per task)
- **Mandatory PR creation** for task completion
- **Isolated git worktrees** for agent workspaces
- **Agent health monitoring** via tmux session tracking
- **Constraint system** for precise task control
- **Command-line constraint overrides** via flags

## 🔮 Future Enhancements

- **File-based A2A protocol** for seamless agent coordination
- **Constraint validation** with real-time enforcement
- **Agent performance metrics** and optimization
- **Multi-agent workflow patterns** for complex tasks
- **Distributed constraint propagation** across agent mesh
- **Advanced task decomposition** with dependency management

---

## Appendix: Migration History

### 🚫 Removed Components

The following components have been removed during the evolution to the current file-based A2A system:

**Legacy Architecture Removed:**
- **External dependencies**: Previous Redis-based coordination replaced with pure file-based system
- **Hardcoded agent types**: Static "frontend-agent", "backend-agent" types replaced with dynamic general-purpose agents
- **Static task files**: Predefined task configurations replaced with dynamic constraint inference
- **Hardcoded capability mappings**: Manual task-to-agent-type mappings replaced with LLM-based constraint inference
- **Hub-spoke architecture**: Centralized broker pattern transformed to mesh communication via A2A protocol

**Benefits of Current Approach:**
- **Simplified deployment**: No external services required
- **Dynamic flexibility**: Agents adapt to any task type
- **Intelligent routing**: Natural language understanding for task constraints
- **Zero configuration**: System works out-of-the-box
- **Enhanced reliability**: No single points of failure

**Migration Completed:** The system successfully transitioned from experimental proof-of-concept with external dependencies to production-ready file-based implementation in PR #979.
