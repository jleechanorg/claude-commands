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

## 🔁 Single Source of Truth for Orchestration Code

The only supported package location is `orchestration/`. A historical duplicate lived at `orchestration/orchestration`, but it was an older snapshot missing newer features (for example, Gemini CLI support and the expanded CLI tests). We confirmed the duplicate differed only in `task_dispatcher.py` and `tests/test_cli_support.py`, and those newer behaviors are preserved in the canonical package. A regression test now fails fast if the nested package reappears.

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

## 🖥️ Why tmux? The Terminal Multiplexer Architecture

The orchestration system uses **tmux (terminal multiplexer)** as the core process isolation and monitoring mechanism. This design choice provides several critical benefits:

### Key Benefits of tmux

1. **Visual Monitoring**: Developers can attach to any agent session and watch it work in real-time
2. **Process Isolation**: Each agent runs in its own independent terminal session
3. **Session Persistence**: Agents survive terminal disconnects and continue working
4. **Clean Separation**: Each task gets its own environment without interference
5. **Easy Debugging**: Inspect agent output, logs, and errors interactively
6. **Resource Management**: Simple to kill, restart, or monitor individual agents
7. **Production Ready**: tmux is a mature, battle-tested tool available on all Unix systems

### tmux Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Complete tmux Lifecycle                         │
└─────────────────────────────────────────────────────────────────────┘

1. USER COMMAND
   └─> /orch "Fix all failing tests"
       └─> .claude/commands/orchestrate.md
           └─> python3 orchestration/orchestrate_unified.py

2. TASK ANALYSIS (orchestrate_unified.py)
   └─> TaskDispatcher.analyze_task_and_create_agents()
       ├─> Detect CLI (claude, codex, gemini, or cursor)
       ├─> Detect PR context (new vs update)
       └─> Generate agent specifications

3. WORKSPACE CREATION (task_dispatcher.py)
   └─> Create git worktree from main branch
       ├─> Location: ~/projects/orch_{repo_name}/{agent_name}/
       ├─> Branch: {agent_name}-work
       └─> Fresh checkout from main

4. PROMPT GENERATION
   └─> Write comprehensive prompt to /tmp/agent_prompt_{agent}.txt
       ├─> Task description
       ├─> Completion instructions
       ├─> PR creation requirements
       └─> Exit criteria

5. BASH SCRIPT CREATION
   └─> Generate /tmp/{agent}_run.sh
       ├─> Signal handlers (SIGINT, SIGTERM)
       ├─> CLI execution command
       ├─> Logging and error handling
       ├─> Result file creation
       └─> 1-hour keep-alive

6. TMUX SESSION START
   └─> tmux new-session -d -s {agent_name} -c {agent_dir} bash {script}
       ├─> Detached session (-d)
       ├─> Named session (-s {agent_name})
       ├─> Working directory (-c {agent_dir})
       └─> Executes bash script

7. CLI EXECUTION (Inside tmux)
   └─> Claude CLI:
       ├─> claude --model sonnet -p @{prompt_file}
       ├─> --output-format stream-json
       ├─> --verbose
       └─> --dangerously-skip-permissions
   └─> Codex CLI:
       ├─> codex exec --yolo
       └─> < {prompt_file}
   └─> Gemini CLI:
       ├─> gemini -m {model} --yolo
       └─> -p {prompt_file}
   └─> Cursor Agent CLI:
       ├─> cursor-agent -f -p @{prompt_file}
       ├─> --model ${CURSOR_MODEL:-composer-1}
       └─> --output-format text

8. AGENT WORK (Inside tmux session)
   └─> Agent reads prompt
   └─> Executes task
   └─> Commits changes
   └─> Creates PR (mandatory)
   └─> Writes result file

9. MONITORING (agent_monitor.py)
   └─> Pings every 2 minutes
   ├─> Check tmux session exists
   ├─> Capture recent output
   ├─> Check workspace modifications
   ├─> Detect stuck agents
   └─> Auto-restart if needed

10. COMPLETION
    └─> Agent writes result to /tmp/orchestration_results/{agent}_results.json
    └─> Session stays alive for 1 hour for debugging
    └─> Auto-cleanup after timeout
```

### How tmux Calls Claude or Codex

The system supports multiple LLM CLIs through a profile-based architecture:

**Claude CLI Profile:**
```python
{
    "binary": "claude",
    "command_template": (
        "{binary} --model sonnet -p @{prompt_file} "
        "--output-format stream-json --verbose{continue_flag} "
        "--dangerously-skip-permissions"
    ),
    "stdin_template": "/dev/null",
    "quote_prompt": False
}
```

**Codex CLI Profile:**
```python
{
    "binary": "codex",
    "command_template": "{binary} exec --yolo",
    "stdin_template": "{prompt_file}",
    "quote_prompt": True
}
```

**Cursor Agent CLI Profile:**
```python
{
    "binary": "cursor-agent",
    "command_template": "{binary} -f -p @{prompt_file} --model ${CURSOR_MODEL:-composer-1} --output-format text",
    "stdin_template": "/dev/null",
    "quote_prompt": False
}
```

**tmux Command Construction:**
```bash
# 1. Create bash script with CLI execution
bash_cmd = '''
#!/bin/bash
# Signal handlers for interruption
trap 'echo "Agent interrupted" | tee -a {log_file}; exit 130' SIGINT
trap 'echo "Agent terminated" | tee -a {log_file}; exit 143' SIGTERM

# Log startup
echo "[$(date)] Starting agent {agent_name}" | tee -a {log_file}

# Execute CLI (Claude example)
claude --model sonnet -p @{prompt_file} \
    --output-format stream-json \
    --verbose \
    --dangerously-skip-permissions \
    2>&1 | tee -a {log_file}

# Capture exit code
CLI_EXIT=$?

# Log completion
if [ $CLI_EXIT -eq 0 ]; then
    echo "Agent completed successfully" | tee -a {log_file}
else
    echo "Agent failed with exit code $CLI_EXIT" | tee -a {log_file}
fi

# Keep session alive for 1 hour
sleep 3600
'''

# 2. Write script to /tmp/{agent}_run.sh
# 3. Make executable: chmod 700
# 4. Create tmux session
tmux new-session -d -s {agent_name} -c {agent_dir} bash {script_path}
```

### Monitoring tmux Sessions

**Interactive Monitoring:**
```bash
# List all agent sessions
tmux list-sessions | grep task-agent

# Attach to agent (watch it work)
tmux attach -t task-agent-12345

# Detach without killing (Ctrl-b, then d)

# View agent output (last 50 lines)
tmux capture-pane -t task-agent-12345 -p | tail -50

# Check if agent is still working
tmux has-session -t task-agent-12345 && echo "Active" || echo "Completed"
```

**Automated Monitoring (agent_monitor.py):**
```python
def ping_agent(agent_name: str) -> dict:
    """Ping agent and collect status"""
    # 1. Check if tmux session exists
    subprocess.run(["tmux", "has-session", "-t", agent_name])

    # 2. Capture recent output
    subprocess.run(["tmux", "capture-pane", "-t", agent_name, "-p"])

    # 3. Check workspace modifications
    os.stat(workspace_path).st_mtime

    # 4. Check result files
    result_file = f"/tmp/orchestration_results/{agent_name}_results.json"

    # 5. Detect stuck agents (no activity for 10 minutes)
    if time_since_activity > 10 minutes:
        restart_agent(agent_name)
```

### Session Management

**Automatic Cleanup:**
- Sessions auto-close after 1 hour of inactivity
- Completed agents detected by monitoring system
- Stale sessions cleaned up on orchestration restart

**Manual Management:**
```bash
# Kill specific agent
tmux kill-session -t task-agent-12345

# Kill all agent sessions
tmux list-sessions | grep task-agent | cut -d: -f1 | xargs -I {} tmux kill-session -t {}

# Stop entire system
./orchestration/start_system.sh stop
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
# - Gemini CLI (`gemini`) – install from https://github.com/google-gemini/gemini-cli
# - Cursor Agent CLI (`cursor-agent`) – install from https://www.cursor.com/

# Ensure git and gh CLI are available
which git gh  # Should show both commands
```

### Starting the System

```bash
# Start the orchestration system (starts agent monitor)
./orchestration/start_system.sh start

# Create agents via your preferred CLI (Claude, Codex, Gemini, or Cursor)
/orch "Find and fix all inline imports"

# Direct orchestration command (for testing)
python3 orchestration/orchestrate_unified.py "Update the UI styling"

# Constraint examples
/orch "update mvp_site/readme.md with latest info. only update that file"
/orch "fix tests --max-changes 3 --no-servers"
```

## 🎮 tmux Live Mode - Interactive AI CLI

Beyond slash commands, you can now use the orchestration system as a CLI tool to start interactive AI sessions wrapped in tmux.

### Installation as PyPI Package

```bash
# Install from source (in orchestration directory)
cd orchestration
pip install -e .

# Or install from PyPI (when published)
pip install ai_orch
```

### Using Live Mode

```bash
# Start interactive Claude session
ai_orch live

# Start interactive Codex session
ai_orch live --cli codex

# Start with custom session name
ai_orch live --name my-coding-session

# Start in specific directory
ai_orch live --dir ~/my-project

# Start with specific model
ai_orch live --model opus

# Start in detached mode (don't attach immediately)
ai_orch live --detached

# List all active AI sessions
ai_orch list

# Attach to existing session
ai_orch attach my-coding-session

# Kill a session
ai_orch kill my-coding-session
```

### Live Mode Features

**Interactive Terminal Access:**
- Direct interaction with Claude, Codex, Gemini, or Cursor CLI
- Full tmux session management
- Persistent sessions that survive disconnects
- Multiple concurrent sessions supported

**Session Management:**
- Auto-generated unique session names
- Custom session naming
- List all active sessions
- Attach/detach from sessions
- Clean session termination

**tmux Integration:**
- Detach: `Ctrl+b`, then `d`
- Reattach: `ai_orch attach <session-name>`
- View all sessions: `ai_orch list`
- Kill session: `ai_orch kill <session-name>` or `tmux kill-session -t <session-name>`

### Use Cases

**Development Workflow:**
```bash
# Start a coding session
ai_orch live --name feature-auth --dir ~/projects/myapp

# Work interactively with Claude...
# Detach when needed (Ctrl+b, d)

# Reattach later
ai_orch attach feature-auth
```

**Multiple Parallel Sessions:**
```bash
# Frontend work
ai_orch live --name frontend --dir ~/app/ui

# Backend work in different session
ai_orch live --name backend --dir ~/app/api

# List all sessions
ai_orch list
# Output:
#   - ai-live-claude-frontend
#   - ai-live-claude-backend
```

**Quick Tasks:**
```bash
# Start quick session for current directory
ai_orch live

# Or use the shorter alias
orch live
```

### Architecture

Live mode uses the same CLI profiles as the orchestration system:

- **Claude Profile**: Interactive `claude` CLI with model selection
- **Codex Profile**: Interactive `codex exec` mode
- **Gemini Profile**: Interactive `gemini` CLI with the configured Gemini model
- **Cursor Profile**: Fresh-data analysis via `cursor-agent` CLI using a configurable model (defaults to composer-1 via `CURSOR_MODEL`)
- **tmux Wrapper**: Each session runs in isolated tmux session
- **Working Directory**: Sessions start in specified directory
- **Persistence**: Sessions survive terminal disconnects

### Comparison: Live Mode vs Orchestration Mode

| Feature | Live Mode (`ai_orch live`) | Orchestration Mode (`/orch`) |
|---------|---------------------------|------------------------------|
| **Interaction** | Interactive, user-driven | Autonomous agent execution |
| **Sessions** | Single persistent session | One session per task |
| **Workspace** | Current/specified directory | Git worktree per agent |
| **Output** | Real-time terminal output | Logged to files |
| **Use Case** | Direct development work | Automated task completion |
| **PR Creation** | Manual (user decision) | Mandatory (agent task) |
| **Control** | Full user control | Agent-driven with constraints |

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
