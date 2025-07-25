# Multi-Agent Orchestration System

A **simple, working implementation** of AI agent orchestration that creates general-purpose agents on-demand to complete development tasks and create pull requests.

> **📋 Complete Design Documentation**: See [ORCHESTRATION_DESIGN.md](./ORCHESTRATION_DESIGN.md) for comprehensive system architecture, file documentation, and user flows.

## ✅ System Overview

This system implements the **core design philosophy**: **one general agent per task**

- **Simple**: Create agent → Agent works in tmux → Agent creates PR → Task complete
- **Isolated**: Each agent gets fresh git worktree from main branch
- **Reliable**: Mandatory PR creation ensures task completion
- **Monitored**: Lightweight Python coordinator tracks progress
- **Optional Coordination**: Redis provides A2A messaging when available

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
│                     Redis Message Broker + A2A Protocol         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Task Queues │  │Agent Registry│  │  A2A Bridge │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│  Terminal 1         │ │  Terminal 2         │ │  Terminal 3         │
│  ┌─────────────┐    │ │  ┌─────────────┐    │ │  ┌─────────────┐    │
│  │ Python Mon  │    │ │  │ Task Agent  │    │ │  │ Task Agent  │    │
│  │ Coordinator │────┼─┼─▶│ (Created)   │────┼─┼─▶│ (Created)   │    │
│  └─────────────┘    │ │  └─────────────┘    │ │  └─────────────┘    │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                                │
                                ▼
                        orchestrate_unified.py
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install Redis
sudo apt-get install redis-server

# Install Python Redis client
pip install redis

# Ensure tmux is installed
sudo apt-get install tmux

# Install Claude CLI
# (see main README for Claude Code setup)
```

### Starting the System

```bash
# Start the orchestration system (starts Redis and Python monitor)
./orchestration/start_system.sh start

# Create agents for specific tasks
python3 orchestration/orchestrate_unified.py "Find and fix all inline imports"

# Direct orchestration command
python3 orchestration/orchestrate_unified.py "Update the UI styling"
```

## 📁 Key Components

### Core Files
- **orchestrate_unified.py** - Main entry point for agent creation
- **task_dispatcher.py** - Task routing with capability-based assignment
- **message_broker.py** - Redis messaging infrastructure
- **redis_a2a_bridge.py** - A2A protocol integration with Redis
- **a2a_integration.py** - A2A SDK implementation

### A2A Integration
- **real_a2a_poc.py** - Real A2A protocol implementation
- **minimal_a2a_poc.py** - Minimal A2A proof of concept
- **simple_a2a_poc.py** - Simple A2A implementation

### Agent Management
- **agent_health_monitor.py** - Monitors agent health
- **dashboard.py** - Visual dashboard for agent status
- **start_system.sh** - System startup script

## 🔄 How It Works

1. **Task Submission**: User submits task via `orchestrate_unified.py`
2. **Agent Creation**: System creates appropriate agent in tmux session
3. **A2A Registration**: Agent registers with A2A protocol
4. **Redis Coordination**: Tasks coordinated via Redis message broker
5. **Inter-Agent Communication**: Agents communicate using A2A protocol
6. **Result Aggregation**: Opus-master collects and reports results

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
        # Initialize Redis if available (for coordination)
        # Call task dispatcher to analyze and create agents
```

### 4. **Task Analysis & Agent Creation**
```python
# task_dispatcher.py
def analyze_task_and_create_agents(self, task_description):
    # Generate unique timestamp
    # Create a general development agent specification
    return [{
        "name": f"task-agent-{timestamp}",
        "type": "development",
        "focus": task_description,
        "capabilities": ["task_execution", "development", "git_operations"],
        "prompt": f"Task: {task_description}..."
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
3. **A2A Integration** - If Redis available, agents register for coordination
4. **Self-Contained** - Each agent has everything needed to complete task → PR
5. **Verification Required** - Agent must verify PR creation with `gh pr view`

The system ensures PR creation by making it part of the agent's core instructions, with clear failure criteria if skipped.

## 📊 Monitoring & Status

### Basic Monitoring Commands

```bash
# List all active agents
tmux ls | grep agent

# Attach to a specific agent
tmux attach -t task-agent-1234

# View Redis messages
redis-cli monitor

# Check A2A agent status
curl http://localhost:8000/.well-known/agent

# View agent logs
tail -f /tmp/worldarchitectai_logs/$(git branch --show-current).log
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
   - Redis connection status
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
3. Query Redis for registered agents (if available)
4. Parse agent logs in `/tmp/orchestration_logs/`
5. View agent output with `tmux capture-pane`

**Future enhancement**: Natural language status queries (e.g., "What's the status?") will be handled by extending the orchestrate.md command to parse status-related queries and return formatted reports.

## 🔧 Configuration

Environment variables:
- `CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192` - Token limit for Claude
- `REDIS_HOST=localhost` - Redis server host
- `REDIS_PORT=6379` - Redis server port
- `A2A_PORT=8000` - A2A protocol port

## 📚 Documentation

- [README_A2A_INTEGRATION.md](./README_A2A_INTEGRATION.md) - A2A protocol details
- [REDIS_DECISION_GUIDE.md](./REDIS_DECISION_GUIDE.md) - Redis architecture decisions
- [DYNAMIC_AGENT_DESIGN.md](./DYNAMIC_AGENT_DESIGN.md) - Agent creation architecture
- [ORCHESTRATION_QUICK_START.md](../docs/orchestration/ORCHESTRATION_QUICK_START.md) - Quick start guide

## 🚫 Removed Components

The following static components have been removed:
- Hardcoded `frontend-agent`, `backend-agent`, `testing-agent` definitions
- Static task files (`frontend_tasks.txt`, `backend_tasks.txt`, `testing_tasks.txt`)
- Hardcoded agent capability mappings
- `start_testing_agent.sh` script

## ⚡ Key Features

- **Real Redis-based messaging** (not file polling)
- **A2A protocol compliance** for inter-agent communication
- **tmux terminal separation** for visual monitoring
- **Working agent hierarchy** (Opus → Task Agents)
- **Task delegation and result reporting**
- **Error handling and recovery**
- **Agent health monitoring**

## 🔮 Future Enhancements

- Enhanced A2A protocol features
- Advanced capability scoring algorithms
- Agent performance metrics
- Multi-agent collaboration patterns
- Distributed agent deployment