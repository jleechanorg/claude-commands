# Orchestration System Design Document

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [File Documentation](#file-documentation)
   - [Core Python Files](#core-python-files)
   - [Shell Scripts](#shell-scripts)
   - [Documentation Files](#documentation-files)
   - [Configuration Files](#configuration-files)
4. [User Flows](#user-flows)
   - [Basic Task Execution Flow](#basic-task-execution-flow)
   - [Monitoring Flow](#monitoring-flow)
   - [A2A Integration Flow](#a2a-integration-flow)
5. [Component Interactions](#component-interactions)
6. [System Capabilities](#system-capabilities)
7. [Configuration and Setup](#configuration-and-setup)

## System Overview

The Orchestration System is a **simple, working implementation** of multi-agent task coordination for development workflows. It creates general-purpose AI agents on-demand that work in isolated tmux sessions with fresh git branches to complete tasks and create pull requests.

**Core Design Principles:**
- **Simplicity**: One general agent per task, no complex categorization
- **Isolation**: Each agent gets unique workspace and git branch from main
- **Completeness**: Agents must create PRs to mark tasks complete
- **Monitoring**: Lightweight Python coordinator tracks agent progress
- **Optional Coordination**: Redis provides A2A messaging when available

**Key Features:**
- Dynamic agent creation via `/orch "task description"`
- Fresh git worktrees from main branch (no inheritance of unrelated changes)
- Mandatory PR creation for task completion
- Real-time monitoring with centralized logging
- A2A protocol integration for agent communication
- Graceful fallback when Redis unavailable

## Architecture

```
User Command: /orch "Fix failing tests"
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Entry Point                    │
│  orchestrate_unified.py - Main coordination logic               │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Task Dispatcher                             │
│  task_dispatcher.py - Agent creation and management             │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│   Git Worktree   │  │   tmux Session   │  │   Agent Monitor     │
│   Fresh branch   │  │   Claude Code    │  │   Status tracking   │
│   from main      │  │   CLI execution  │  │   A2A coordination  │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Result Collection                             │
│  • PR Creation (mandatory)                                      │
│  • Result files in /tmp/orchestration_results/                  │
│  • Logs in /tmp/orchestration_logs/                            │
└─────────────────────────────────────────────────────────────────┘

Optional Redis Coordination:
┌─────────────────────────────────────────────────────────────────┐
│                  Redis + A2A Protocol                           │
│  message_broker.py - Agent registration and messaging           │
└─────────────────────────────────────────────────────────────────┘
```

## File Documentation

### Core Python Files

#### `orchestrate_unified.py`
**Role**: Main orchestration entry point and system coordinator  
**What it does**: Initializes Redis (optional), calls task dispatcher to create agents, handles dependency checking and provides user feedback on agent creation status.  
**Key method**: `orchestrate(task_description)` - the main workflow function

#### `task_dispatcher.py` 
**Role**: Agent creation and lifecycle management  
**What it does**: Creates general-purpose task agents with unique names, sets up git worktrees from main branch, generates comprehensive prompts with mandatory PR creation steps, and manages agent collision detection.  
**Key methods**: `analyze_task_and_create_agents()`, `create_dynamic_agent()`

#### `message_broker.py`
**Role**: Redis-based coordination and A2A protocol integration  
**What it does**: Manages agent registration in Redis, provides pub/sub messaging capabilities, and enables optional inter-agent communication when Redis is available.  
**Key methods**: `register_agent()`, `send_task()`, heartbeat management

#### `agent_monitor.py`
**Role**: Lightweight monitoring coordinator without LLM capabilities  
**What it does**: Pings active agents every 2 minutes, checks tmux sessions and workspaces, logs agent status to centralized log file, and cleans up completed agents.  
**Key method**: `run()` - main monitoring loop, `ping_all_agents()`

### Shell Scripts

#### `start_monitor.sh`
**Role**: Agent monitoring service launcher  
**What it does**: Starts the Python monitoring coordinator in background, checks for existing monitor processes, and provides user-friendly status commands.

#### `monitor_agents.sh`
**Role**: Real-time agent status display script  
**What it does**: Shows live tmux session output and status updates every 10 seconds, displays shared status files and task counts.

### Documentation Files

#### `README.md`
**Role**: Primary system documentation and usage guide  
**What it does**: Provides architecture overview, quick start instructions, monitoring commands, and comprehensive feature documentation.

#### `README_A2A_INTEGRATION.md`
**Role**: A2A protocol integration documentation  
**What it does**: Documents the Agent-to-Agent SDK integration, real implementation details, and usage examples for inter-agent communication.

#### `DYNAMIC_AGENT_DESIGN.md`
**Role**: Agent creation architecture documentation  
**What it does**: Explains the dynamic agent creation system, capability-based selection, and removal of hardcoded agent types.

### Configuration Files

#### `REDIS_DECISION_GUIDE.md`
**Role**: Redis architecture decisions and rationale  
**What it does**: Documents why Redis was chosen for coordination, fallback mechanisms, and performance considerations.

## User Flows

### Basic Task Execution Flow

**User Action**: `/orch "Fix all failing tests"`

**Component Flow**:
1. **Claude CLI** → Executes `.claude/commands/orchestrate.md` 
2. **orchestrate.md** → Calls `orchestration/orchestrate_unified.py`
3. **orchestrate_unified.py** → 
   - Checks dependencies (tmux, git, gh, claude)
   - Initializes Redis MessageBroker (optional)
   - Calls TaskDispatcher.analyze_task_and_create_agents()
4. **task_dispatcher.py** →
   - Generates unique agent name (`task-agent-{timestamp}`)
   - Creates agent specification with capabilities
   - Calls create_dynamic_agent() with agent spec
5. **create_dynamic_agent()** →
   - Creates git worktree from main branch
   - Generates comprehensive prompt with mandatory PR steps
   - Starts tmux session with Claude Code CLI
   - Registers agent with Redis (if available)
6. **Agent Execution** →
   - Claude works in isolated workspace
   - Completes assigned task
   - Commits changes and pushes branch
   - Creates PR using `gh pr create`
   - Writes completion status to result file
7. **Completion** → PR created and task marked complete

### Monitoring Flow

**User Action**: `./orchestration/start_monitor.sh`

**Component Flow**:
1. **start_monitor.sh** →
   - Checks for existing monitor process
   - Starts `agent_monitor.py` in background
   - Provides status commands
2. **agent_monitor.py** →
   - Connects to Redis MessageBroker (optional)
   - Registers as coordinator in A2A protocol
   - Starts monitoring loop (2-minute intervals)
3. **Monitoring Loop** →
   - Discovers active tmux sessions (`tmux list-sessions`)
   - For each agent: checks workspace, result files, recent output
   - Logs comprehensive status to `/tmp/orchestration_logs/agent_monitor.log`
   - Cleans up completed agents
4. **Status Output** →
   - Real-time agent status (Working/Completed/Failed)
   - Recent agent output lines
   - Workspace and PR creation status

### A2A Integration Flow

**Component Interactions**:
1. **orchestrate_unified.py** → Initializes MessageBroker
2. **MessageBroker** → Connects to Redis and initializes A2A bridge
3. **Agent Creation** → Registers agent with capabilities in Redis
4. **agent_monitor.py** → Registers as coordinator in A2A protocol
5. **Inter-Agent Communication** → Agents can discover and message each other via Redis pub/sub

**Fallback Behavior**: If Redis unavailable, system continues with file-based coordination using result files in `/tmp/orchestration_results/`

## Component Interactions

### Core Workflow Interaction
```
User → Claude CLI → orchestrate.md → orchestrate_unified.py → task_dispatcher.py → tmux + git + Claude
                                                                     ↓
Redis (optional) ← message_broker.py ← agent registration    → agent_monitor.py → logging
```

### File System Integration
```
Agent Workspace: agent_workspace_{agent-name}/
Git Branch: {agent-name}-work (from main)
Result File: /tmp/orchestration_results/{agent-name}_results.json
Log File: /tmp/orchestration_logs/{agent-name}.log
Monitor Log: /tmp/orchestration_logs/agent_monitor.log
```

### Redis Integration (Optional)
```
agent_monitor.py → MessageBroker → Redis → A2A Protocol
orchestrate_unified.py → MessageBroker → Agent Registry
Agents → Self-registration → Capability Broadcasting
```

## System Capabilities

### ✅ **Working Features**
- Dynamic agent creation with unique naming
- Git worktree isolation from main branch
- Mandatory PR creation for completion
- Real-time monitoring with status logging
- Redis coordination when available
- A2A protocol integration for messaging
- Graceful fallback when Redis unavailable
- Agent collision detection and prevention
- Concurrent agent limits (MAX_CONCURRENT_AGENTS = 5)

### 🔄 **Monitoring Capabilities**
- **Agent Discovery**: Automatically finds active tmux sessions
- **Status Tracking**: Monitors workspace, result files, tmux activity
- **Progress Logging**: Centralized logs with timestamps and status
- **Completion Detection**: Identifies completed and failed agents
- **Resource Cleanup**: Removes completed agents from monitoring

### 📡 **A2A Protocol Features**
- **Agent Registration**: Automatic capability broadcasting
- **Message Routing**: Inter-agent communication via Redis
- **Coordinator Role**: Monitor acts as non-LLM coordinator
- **Heartbeat System**: Agent health monitoring
- **Discovery Service**: Agents can find each other

## Configuration and Setup

### **Environment Variables**
- `CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192` - Token limit for Claude
- `REDIS_HOST=localhost` - Redis server host  
- `REDIS_PORT=6379` - Redis server port
- `A2A_PORT=8000` - A2A protocol port

### **Directory Structure**
```
orchestration/
├── orchestrate_unified.py      # Main entry point
├── task_dispatcher.py          # Agent creation
├── message_broker.py           # Redis coordination
├── agent_monitor.py            # Monitoring coordinator
├── start_monitor.sh            # Monitor launcher
├── README.md                   # Primary documentation
├── ORCHESTRATION_DESIGN.md     # This design document
└── tests/                      # Test suite
    ├── test_simple_flow.py     # Basic workflow tests
    └── fixtures/               # Mock fixtures
```

### **Log Locations**
- **Agent Monitor**: `/tmp/orchestration_logs/agent_monitor.log`
- **Individual Agents**: `/tmp/orchestration_logs/{agent-name}.log`
- **Result Files**: `/tmp/orchestration_results/{agent-name}_results.json`

### **Commands**
```bash
# Create agent
/orch "task description"

# Start monitoring  
./orchestration/start_monitor.sh

# View monitor logs
tail -f /tmp/orchestration_logs/agent_monitor.log

# Test monitoring
python3 orchestration/agent_monitor.py --once

# Check system status
./orchestration/monitor_agents.sh
```

This system provides a **simple, reliable foundation** for AI agent orchestration with proper monitoring, coordination, and completion tracking.