# Multi-Agent Orchestration System

A comprehensive multi-agent orchestration system using real Claude Code CLI instances for autonomous software development.

## Overview

This system creates and manages multiple specialized AI agents that work together to handle different aspects of software development:

- **Frontend Agent**: UI/React development and styling
- **Backend Agent**: API/Database development and server logic  
- **Testing Agent**: Quality assurance and automated testing
- **Opus Master**: Task coordination and natural language interface

## Quick Start

```bash
# Start the full orchestration system
./start_system.sh

# Start with specific agent
./start_system.sh start dead-code    # Start dead code cleanup agent
./start_system.sh start testing     # Start testing agent

# Monitor system health
./dashboard.py

# Check system status
./start_system.sh status

# Stop all agents
./start_system.sh stop
```

## Architecture

### Core Components

1. **Agent Management** (`start_system.sh`, `start_claude_agent.sh`)
   - Starts and manages Claude Code CLI instances in tmux sessions
   - Handles headless mode for autonomous operation
   - Manages agent lifecycle and recovery

2. **Task Distribution** (`task_dispatcher.py`)
   - Intelligent task analysis and assignment
   - Agent capability matching
   - Load balancing and priority handling
   - Task dependency tracking

3. **Health Monitoring** (`agent_health_monitor.py`)
   - Continuous agent health checking
   - Automatic failure detection and recovery
   - Performance metrics and reporting
   - Redis-based coordination

4. **Dashboard** (`dashboard.py`)
   - Real-time system visualization
   - Agent status and workload monitoring
   - Recent PR activity tracking
   - Interactive system control

5. **Task Management** (`tasks/` directory)
   - File-based task queues for each agent
   - Shared status tracking
   - Health and performance reports

### Agent Capabilities

| Agent | Specialization | Task Types | Keywords |
|-------|---------------|------------|----------|
| Frontend | UI/React Development | Frontend, Documentation | ui, react, css, component, style |
| Backend | API/Database | Backend, Infrastructure | api, database, server, auth, endpoint |
| Testing | Quality Assurance | Testing, Bug Fixes | test, bug, validate, quality, coverage |
| Opus Master | Coordination | Task Management | orchestration, coordination, planning |

## Usage Examples

### Basic Operations

```bash
# Start all agents
./start_system.sh

# Connect to specific agent
tmux attach -t frontend-agent
tmux attach -t backend-agent
tmux attach -t testing-agent

# Assign tasks manually
echo "Create login form component" >> tasks/frontend_tasks.txt
echo "Implement auth API endpoint" >> tasks/backend_tasks.txt
echo "Add integration tests for auth" >> tasks/testing_tasks.txt
```

### Advanced Operations

```bash
# Intelligent task assignment
python3 task_dispatcher.py

# Monitor agent health
python3 agent_health_monitor.py

# Real-time dashboard
python3 dashboard.py

# Process specific agent tasks
./start_dead_code_agent.sh
./start_testing_agent.sh
```

### Task Management

```bash
# Add prioritized tasks
echo "CRITICAL: Fix production bug in auth system" >> tasks/backend_tasks.txt
echo "HIGH: Update user interface for mobile" >> tasks/frontend_tasks.txt
echo "MEDIUM: Add comprehensive test coverage" >> tasks/testing_tasks.txt

# Monitor task progress
cat tasks/task_report.json | jq '.agent_workload'
```

## Configuration

### Agent Settings

Edit `start_system.sh` to customize agent behavior:

```bash
# Agent tmux session configuration
CLAUDE_PATH="/home/jleechan/.claude/local/claude"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Agent specializations
FRONTEND_KEYWORDS=("ui" "react" "css" "component")
BACKEND_KEYWORDS=("api" "database" "server" "auth")
TESTING_KEYWORDS=("test" "quality" "validate" "coverage")
```

### Task Dispatcher Settings

Edit `task_dispatcher.py` to customize task assignment:

```python
# Agent capacity limits
"max_concurrent": 2,  # Maximum concurrent tasks per agent
"keywords": ["api", "database"],  # Task matching keywords
"types": [TaskType.BACKEND]  # Supported task types
```

### Health Monitor Settings

Edit `agent_health_monitor.py` to customize monitoring:

```python
monitoring_interval = 30  # Health check interval (seconds)
max_error_count = 3       # Maximum errors before restart
startup_script = "start_system.sh"  # Agent restart script
```

## Monitoring & Troubleshooting

### Health Monitoring

```bash
# Check agent health
python3 agent_health_monitor.py

# View health report
cat tasks/health_report.json | jq '.system_status'

# Check individual agent status
tmux capture-pane -t frontend-agent -p
```

### Log Analysis

```bash
# View system logs
./start_system.sh logs

# Monitor agent activity
./monitor_agents.sh

# Check Redis status
redis-cli ping
redis-cli keys "agent:*"
```

### Common Issues

1. **Agent Not Starting**
   - Check if Claude Code CLI is installed: `which claude`
   - Verify tmux is available: `tmux -V`
   - Check Redis connection: `redis-cli ping`

2. **Task Assignment Failing**
   - Verify task files exist: `ls -la tasks/`
   - Check agent capacity: `cat tasks/task_report.json`
   - Review task syntax and keywords

3. **Agent Becomes Unresponsive**
   - Health monitor will auto-restart agents
   - Manual restart: `./start_system.sh stop && ./start_system.sh start`
   - Check tmux sessions: `tmux list-sessions`

## Development

### Adding New Agents

1. Create agent startup script:
```bash
#!/bin/bash
# start_new_agent.sh
tmux new-session -d -s new-agent -c "$PROJECT_ROOT" "$CLAUDE_PATH"
tmux send-keys -t new-agent "I am the New Agent..." Enter
```

2. Add to agent capabilities in `task_dispatcher.py`:
```python
"new-agent": {
    "types": [TaskType.CUSTOM],
    "keywords": ["custom", "special"],
    "max_concurrent": 1
}
```

3. Update health monitor in `agent_health_monitor.py`:
```python
"new-agent": {
    "type": "custom",
    "specialization": "Special tasks",
    "task_file": "new_tasks.txt"
}
```

### Extending Task Types

Add new task types to `task_dispatcher.py`:

```python
class TaskType(Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    CUSTOM = "custom"  # New type
```

## Success Stories

### Dead Code Cleanup Agent
- **Task**: Remove unused code with high confidence
- **Process**: Autonomous branch creation → vulture analysis → selective cleanup → testing → PR creation
- **Result**: PR #646 successfully created with 161/161 tests passing
- **Impact**: Clean codebase with professional documentation

### Testing Agent
- **Task**: Comprehensive test suite validation
- **Process**: Automated test discovery → execution → reporting → issue identification
- **Result**: Consistent test suite maintenance
- **Impact**: Improved code quality and reliability

## Future Enhancements

1. **Natural Language Interface**
   - Voice commands for agent interaction
   - Conversational task assignment
   - Natural language progress reporting

2. **Advanced Task Planning**
   - Dependency resolution
   - Resource optimization
   - Deadline management

3. **Cross-Agent Collaboration**
   - Task handoff protocols
   - Shared knowledge base
   - Collaborative problem solving

4. **Integration Expansion**
   - GitHub Actions integration
   - Slack notifications
   - Email reporting

## API Reference

### Task Dispatcher API

```python
from task_dispatcher import TaskDispatcher

dispatcher = TaskDispatcher()

# Add task
task_id = dispatcher.add_task_from_description("Create user login form")

# Get agent workload
workload = dispatcher.get_agent_workload()

# Generate report
report = dispatcher.generate_task_report()
```

### Health Monitor API

```python
from agent_health_monitor import AgentHealthMonitor

monitor = AgentHealthMonitor()

# Get system health
health = monitor.get_system_health()

# Restart agent
monitor.restart_agent("frontend-agent")
```

## Contributing

1. Follow existing code patterns
2. Add comprehensive error handling
3. Include unit tests for new features
4. Update documentation
5. Test with multiple agents

## License

Part of WorldArchitect.AI project - see main project license.