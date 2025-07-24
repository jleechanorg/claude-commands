# Claude Orchestrator - AI Command System & Task Orchestration

A powerful system combining Claude AI commands with an advanced multi-agent task orchestration framework.

## 🚀 Overview

This repository contains two integrated systems:

1. **Claude Commands** - A comprehensive collection of AI-powered commands for development workflows
2. **Orchestration System** - Multi-agent task execution framework with Redis coordination and A2A SDK integration

## 📋 Features

### Claude Commands (/claude/commands/)
- **`/think`** - Deep sequential thinking for complex problem-solving
- **`/fake`** - Detect and audit fake/placeholder code
- **`/test`** - Automated testing workflows (UI, HTTP, integration)
- **`/copilot`** - GitHub PR analysis and automated fixes
- **`/orchestrate`** (`/orch`)- Delegate tasks to specialized agents
- **`/learn`** - Capture and persist learnings with Memory MCP
- **`/execute`** (`/e`) - Execute tasks with safety checks
- **`/plan`** - Strategic planning with approval workflow
- **`/debug`** - Systematic debugging approach
- **`/arch`** - Architecture and design analysis
- And 50+ more specialized commands...

### Orchestration System (/orchestration/)
- **Multi-Agent Architecture**: Specialized agents (frontend, backend, testing, opus-master)
- **Redis-Based Coordination**: Reliable task queuing and state management
- **A2A SDK Integration**: Google's Agent-to-Agent communication framework
- **Dynamic Task Assignment**: Intelligent load balancing across agents
- **Real-Time Monitoring**: Live agent status via tmux sessions
- **Automatic Agent Spawning**: Create task-specific agents on demand

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Redis server (6.0+)
- tmux (for agent monitoring)
- Git

### Quick Setup

1. **Clone the repository:**
```bash
git clone https://github.com/jleechan2015/claude-orchestrator.git
cd claude-orchestrator
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Start Redis:**
```bash
# Install Redis if needed
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# Start Redis
redis-server
```

5. **Initialize the orchestration system:**
```bash
./orchestration/start_system.sh start
```

## 📖 Usage

### Using Claude Commands

Claude commands are markdown files that define AI-powered workflows. They're designed to be used within Claude AI interfaces but can be adapted for other LLMs.

```bash
# List all available commands
ls claude/commands/*.md

# View command documentation
cat claude/commands/think.md

# Example: View the orchestrate command
cat claude/commands/orchestrate.md
```

### Using the Orchestrator Programmatically

```python
from orchestration.task_dispatcher import TaskDispatcher

# Create dispatcher
dispatcher = TaskDispatcher()

# Submit a task
task_id = dispatcher.create_task(
    description="Build a REST API with authentication",
    priority="high"
)

# Monitor progress
status = dispatcher.get_task_status(task_id)
print(f"Task {task_id}: {status}")
```

### Command Line Usage

```bash
# Create a new task
python orchestration/task_dispatcher.py create "Implement user authentication"

# List all tasks
python orchestration/task_dispatcher.py list

# Monitor agents
./orchestration/monitor_agents.sh
```

### Monitoring Agents

```bash
# View all running agents
tmux ls | grep agent

# Attach to a specific agent
tmux attach -t frontend-agent

# View agent logs
tail -f orchestration/logs/agent-*.log
```

## 🏗️ Architecture

### Command System Structure
```
claude/commands/
├── cognitive/          # Thinking and analysis commands
│   ├── think.md       # Sequential thinking
│   ├── arch.md        # Architecture analysis
│   └── debug.md       # Debugging workflows
├── operational/       # Task execution commands
│   ├── orchestrate.md # Multi-agent orchestration
│   ├── execute.md     # Direct execution
│   └── plan.md        # Planning workflows
└── quality/          # Code quality commands
    ├── fake.md        # Fake code detection
    ├── test.md        # Testing workflows
    └── review.md      # Code review automation
```

### Orchestration Components

1. **Task Dispatcher** (`task_dispatcher.py`)
   - Routes tasks to appropriate agents
   - Manages task lifecycle and priorities
   - Implements dynamic agent selection

2. **Message Broker** (`message_broker.py`)
   - Redis pub/sub for agent communication
   - Task queue management
   - State synchronization

3. **Agent System** (`agent_system.py`)
   - Agent lifecycle management
   - tmux session orchestration
   - Health monitoring

4. **A2A Integration** (`a2a_integration.py`)
   - Google A2A SDK bridge
   - Advanced workflow capabilities
   - Cross-agent coordination

## 🔧 Configuration

### Redis Configuration
```bash
# Default Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Agent Configuration
```python
# orchestration/config.py
AGENT_TYPES = {
    "frontend": {"capabilities": ["ui", "react", "vue"]},
    "backend": {"capabilities": ["api", "database", "auth"]},
    "testing": {"capabilities": ["unit", "integration", "e2e"]},
    "opus-master": {"capabilities": ["coordination", "planning"]}
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Adding New Commands
1. Create a new `.md` file in `claude/commands/`
2. Follow the existing command format
3. Test with Claude AI interface
4. Submit PR with examples

### Improving Orchestration
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit PR with description

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Resources

- [Claude AI Documentation](https://claude.ai/docs)
- [Redis Documentation](https://redis.io/docs)
- [tmux Cheat Sheet](https://tmuxcheatsheet.com)
- [Google A2A SDK](https://github.com/google/genai) (when available)

## 🚨 Security

- Never commit API keys or secrets
- Use environment variables for configuration
- Run Redis with authentication in production
- Limit agent permissions appropriately

## 📊 Status

- **Claude Commands**: 50+ commands, actively maintained
- **Orchestration**: Production-ready with Redis backend
- **A2A Integration**: Experimental, pending SDK availability

---

Created with ❤️ by the WorldArchitect.AI team