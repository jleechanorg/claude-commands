# Claude Commands Export Repository

## 🚨 WARNING AND DISCLAIMER

### **REFERENCE-ONLY REPOSITORY**
This repository contains commands and configurations extracted from a development project as reference material. These commands are:

- **⚠️ UNTESTED** in isolation outside their original environment
- **⚠️ PROJECT-SPECIFIC** with configurations tailored to specific workflows
- **⚠️ DEPENDENCY-HEAVY** requiring specific MCP servers, tools, and environment setup
- **⚠️ EXPERIMENTAL** with some commands still in development/testing phases

**DO NOT EXPECT PLUG-AND-PLAY FUNCTIONALITY**

### **Use Case**
This repository serves as:
- ✅ **Inspiration** for building similar command systems
- ✅ **Reference implementation** of command composition patterns
- ✅ **Architecture examples** for Claude workflow automation
- ✅ **Technical learning resource** for AI-powered development tools

---

## 🚨 FEATURED: Orchestration System - WIP Prototype

### **Multi-Agent Task Delegation System**
The crown jewel of this export is the **orchestration system** - an active development prototype demonstrating multi-agent AI collaboration with verified production success metrics.

#### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code CLI                         │
├─────────────────────────────────────────────────────────────┤
│  /orch [task] → Task Dispatcher → Redis Coordination       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │ frontend-   │ │ backend-    │ │ testing-    │ │ opus-   │ │
│  │ agent       │ │ agent       │ │ agent       │ │ master  │ │
│  │ (tmux)      │ │ (tmux)      │ │ (tmux)      │ │ (tmux)  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│              A2A Communication Protocol                     │
│           Redis Queues + Task State Management              │
└─────────────────────────────────────────────────────────────┘
```

#### Real-World Performance Metrics
- **Cost**: $0.003-$0.050 per task delegation
- **Success Rate**: Verified end-to-end task completion with PR generation
- **Scalability**: Parallel agent execution with load balancing
- **Monitoring**: Real-time agent health and task progress tracking

#### Proven Workflows
```bash
# Basic task delegation
/orch "implement user authentication system"
→ agent analyzes requirements → creates implementation → tests → commits → creates PR

# Complex multi-step tasks  
/orch "fix all failing tests and optimize performance"
→ agents coordinate → parallel execution → conflict resolution → verification

# System monitoring
/orch monitor agents
→ real-time status → resource utilization → task queue depth
```

#### Architecture Components

**Task Dispatcher** (`orchestration/task_dispatcher.py`):
- Capability-based agent assignment with load balancing
- Dynamic workload distribution and conflict resolution
- Cost optimization through agent reuse and task batching

**Agent Communication** (`orchestration/redis_a2a_bridge.py`):
- Redis-backed A2A (Agent-to-Agent) protocol
- State synchronization and task handoff mechanisms
- Recovery procedures for failed agents and orphaned tasks

**Monitoring System** (`orchestration/agent_monitor.py`):
- Health checks and performance metrics collection
- Automatic agent restart and workspace cleanup
- Resource utilization tracking and optimization suggestions

#### Setup Requirements
```bash
# Core infrastructure
redis-server                    # Coordination backend
tmux                           # Session isolation
python3 -m venv orchestration  # Agent environments

# Agent workspaces (auto-created)
/tmp/agents/frontend-agent-{id}/
/tmp/agents/backend-agent-{id}/
/tmp/agents/testing-agent-{id}/
/tmp/agents/opus-master-{id}/
```

#### Usage Examples
```bash
# Development tasks
/orch "implement login validation with tests"
/orch "refactor database queries for performance"
/orch "add responsive design to dashboard"

# Maintenance tasks  
/orch "fix all TypeScript errors in components"
/orch "update dependencies and resolve conflicts"
/orch "optimize CI/CD pipeline performance"

# Monitoring and debugging
/orch monitor agents
/orch "debug failing integration tests"
tmux attach -t frontend-agent-1234  # Direct agent access
```

#### Success Verification
- **End-to-End Workflows**: Task → Implementation → Testing → PR Creation
- **Cost Tracking**: Real-time expense monitoring per task delegation
- **Quality Metrics**: Code review compliance and test coverage
- **Production Ready**: Proven in active development environments

---

## 📋 QUICK START

### Prerequisites
- [Claude Code CLI](https://claude.ai/code) - Primary execution environment
- Python 3.8+ with venv support
- Git with `gh` CLI for GitHub operations
- Redis 6.0+ (for orchestration features)
- Required MCP servers (see [Dependencies](#dependencies))

### Installation
```bash
git clone https://github.com/jleechanorg/claude-commands.git
cd claude-commands

# Install MCP servers
npm install @anthropic/mcp-server-github @anthropic/mcp-server-memory @playwright/mcp

# Setup environment (adapt to your needs)
cp .env.example .env
# Edit .env with your tokens and configuration
```

⚠️ **Important**: These commands require significant adaptation for your environment. See [Configuration](#configuration) and [Troubleshooting](#troubleshooting) sections.

---

## 🏗️ ARCHITECTURE OVERVIEW

### Command Composition System
The claude-commands system implements **Command Composition** - combining multiple slash commands to create enhanced AI behaviors.

**Example:**
```bash
/think deep /arch /security → Deep architectural security analysis
/debug /test /learn → Systematic debugging + testing + learning capture
```

### Directory Structure
```
commands/                  # 78+ command definitions
├── cognitive/            # Thinking and analysis commands
├── operational/          # Task execution commands  
├── quality/             # Code analysis and validation
├── communication/       # PR and comment management
└── meta/                # System commands

orchestration/           # 🚨 Multi-agent system (requires Redis/tmux)
├── agent_system.py     # Agent lifecycle management
├── task_dispatcher.py  # Load balancing and assignment
├── redis_a2a_bridge.py # Agent communication protocol
└── agent_monitor.py    # Health monitoring and recovery

scripts/                # Supporting scripts and utilities
```

---

## 📚 COMMAND CATEGORIES

### 🧠 Cognitive Commands
| Command | Description | Composition Examples |
|---------|-------------|---------------------|
| `/think [level]` | Sequential thinking (light/medium/deep/ultra) | `/think deep /arch` |
| `/arch` | Architecture analysis and design patterns | `/arch /security` |
| `/debug` | Systematic debugging with evidence collection | `/debug /test` |
| `/analyze` | Deep analysis with memory context | `/analyze /learn` |

### ⚙️ Operational Commands  
| Command | Description | Requirements |
|---------|-------------|--------------|
| `/orchestrate` | 🚨 Multi-agent task delegation | Redis, tmux |
| `/execute` | Task execution with safety checks | - |
| `/plan` | Strategic planning with decomposition | - |
| `/handoff` | Task handoff between contexts | - |

### 🔍 Analysis Commands
| Command | Description | Use Cases |
|---------|-------------|-----------|
| `/fake` | Detect placeholder/demo code | Code audits |
| `/test` | Testing automation workflows | CI/CD |
| `/learn` | Capture learnings to memory | Knowledge management |
| `/research` | Knowledge gathering with patterns | Investigation |

### 💬 Communication Commands
| Command | Description | GitHub Integration |
|---------|-------------|-------------------|
| `/commentreply` | Intelligent PR comment generation | GitHub API |
| `/copilot` | Automated PR analysis and fixes | GitHub MCP |
| `/pr` | Pull request workflow automation | gh CLI |

---

## 🔧 DEPENDENCIES

### Core Dependencies
```bash
# Essential tools
git                     # Version control
gh                      # GitHub CLI  
python3                 # Python runtime
redis-server           # Orchestration backend (required for /orch)
tmux                   # Multi-session management (required for /orch)
```

### MCP Server Dependencies
```bash
# Required
npm install @anthropic/mcp-server-github    # GitHub operations
npm install @anthropic/mcp-server-memory    # Learning persistence

# Recommended  
npm install @playwright/mcp                 # Browser automation
npm install @context7/mcp                   # Documentation lookup
npm install @perplexity/mcp                 # Research capabilities

# Optional
npm install @puppeteer/mcp                  # Alternative browser automation
npm install @gemini/mcp                     # AI model integration
```

### Environment Variables
```bash
# GitHub integration
GITHUB_TOKEN=ghp_...           # GitHub API access

# Optional integrations
GEMINI_API_KEY=...             # Google AI API
REDIS_URL=redis://localhost:6379/0  # Redis (for orchestration)
```

---

## 💡 USAGE EXAMPLES

### Basic Usage
```bash
# Single command execution
/think analyze this codebase
/debug find the authentication issue
/test run integration tests
```

### Command Composition
```bash
# Analytical workflows
/think deep /arch /security → Deep architectural security analysis
/debug /test /learn → Systematic debugging with test validation and learning

# Problem solving
/plan /execute /test → Strategic planning + execution + validation
/research /analyze /learn → Investigation + analysis + knowledge capture

# PR management
/copilot /commentreply → Automated PR analysis + intelligent responses
```

### 🚨 Advanced Orchestration (WIP Prototype)
```bash
# Multi-agent task delegation (requires Redis/tmux setup)
/orchestrate implement user authentication system
→ Cost: ~$0.010-$0.025 | Agents: backend + frontend + testing
→ Output: Complete implementation with tests and PR

/orchestrate analyze performance bottlenecks across codebase  
→ Cost: ~$0.015-$0.040 | Agents: backend + testing + monitoring
→ Output: Performance report with optimization recommendations

/orchestrate fix all failing tests and update dependencies
→ Cost: ~$0.005-$0.020 | Agents: testing + backend + maintenance  
→ Output: All tests passing with dependency updates and conflict resolution

# Orchestration monitoring
/orch monitor agents
→ Real-time: Agent status, task queue, resource utilization, cost tracking

# Direct agent access for debugging
tmux attach -t frontend-agent-1234    # Debug frontend agent workspace
tmux attach -t backend-agent-5678     # Debug backend agent workspace
```

---

## ⚙️ CONFIGURATION

### Environment Setup
1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure required variables:**
   ```bash
   GITHUB_TOKEN=your_github_token_here
   REDIS_URL=redis://localhost:6379/0  # For orchestration
   # Add other configuration as needed
   ```

3. **Install Python dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt  # If available
   ```

### Orchestration System Setup
```bash
# 1. Install and start Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                 # macOS
redis-server                       # Start Redis

# 2. Verify tmux installation  
tmux -V                           # Should show version

# 3. Test orchestration system
/orch "simple test task"          # Should create agent and execute
/orch monitor agents              # Should show agent status
```

### Claude Code CLI Integration
Reference the commands directory in your Claude Code CLI configuration. The exact method depends on your Claude Code CLI version.

---

## 🔧 TROUBLESHOOTING

### Common Issues

**Command Not Found**
- Verify command files are accessible to Claude Code CLI
- Check file permissions and paths
- Restart Claude Code CLI after configuration changes

**MCP Server Issues**
```bash
# Check MCP server status
npx @anthropic/mcp-server-github --version

# Verify GitHub token
gh auth status
```

**🚨 Orchestration System Issues**
```bash
# Check Redis connection
redis-cli ping  # Should return: PONG

# Verify tmux installation
tmux list-sessions  # Should show active sessions or "no server running"

# Test agent creation
/orch "test task"
tmux list-sessions  # Should show new agent sessions

# Debug agent logs
tail -f /tmp/orchestration_logs/agent_monitor.log
tail -f /tmp/agents/*/workspace.log
```

**GitHub Authentication**
```bash
# Check authentication
gh auth status

# Refresh if needed
gh auth refresh
```

### Debug Mode
```bash
# Enable verbose logging
export DEBUG=1
export LOG_LEVEL=DEBUG
```

---

## 🤝 ADAPTATION GUIDELINES

### Recommended Approach
1. **Start Small**: Begin with simple commands like `/think` or `/debug`
2. **Test Thoroughly**: Validate each command in your environment
3. **Adapt Gradually**: Modify commands for your specific needs
4. **Focus on Value**: Prioritize commands most relevant to your workflow

### High-Value Adaptations
- **Cognitive commands** (`/think`, `/arch`, `/debug`) - Universally applicable
- **Basic utilities** (`/list`, `/header`) - Simple and portable
- **Learning system** (`/learn`) - Valuable with Memory MCP

### High-Effort Adaptations
- **🚨 Orchestration system** - Requires complete Redis/tmux infrastructure
- **GitHub workflows** - Needs API reconfiguration for your repositories
- **Testing commands** - Framework-specific modifications required

### 🚨 Orchestration System Adaptation
The orchestration system represents the most sophisticated component requiring:

**Infrastructure Setup:**
- Redis server with persistence and memory optimization
- tmux with session management and recovery procedures
- Python virtual environments per agent type
- Workspace isolation and cleanup automation

**Cost Management:**
- Monitor API usage with real-time cost tracking
- Implement task batching and agent reuse strategies
- Set budget limits and alert thresholds
- Optimize agent assignments for cost efficiency

**Scaling Considerations:**
- Agent capacity planning based on workload patterns
- Load balancing across agent types and capabilities
- Resource utilization monitoring and optimization
- Performance tuning for concurrent task execution

### Creating Your Own Commands
```markdown
# Command Template Structure
## Purpose
Brief description of functionality

## Dependencies  
Required tools and environment

## Implementation
Detailed behavior specification

## Examples
Usage examples and expected outputs
```

---

## ⚠️ TECHNICAL LIMITATIONS

### Known Issues
- **Environment Coupling**: Contains project-specific assumptions
- **Dependency Complexity**: Heavy reliance on specific MCP servers and tools
- **Testing Status**: Many commands are experimental/untested in isolation
- **Performance**: Command composition can generate very long prompts

### Migration Considerations
**High-Effort**: 🚨 Orchestration system, GitHub workflows, Memory integration
**Medium-Effort**: Testing commands, project workflows, composition patterns  
**Low-Effort**: Basic cognitive commands, simple utilities

### 🚨 Orchestration System Limitations
- **Redis Dependency**: Requires persistent Redis instance with backup strategy
- **tmux Complexity**: Session management can become complex with many agents
- **Cost Scaling**: Expense grows with task complexity and agent utilization
- **Resource Usage**: Heavy memory and CPU usage during peak orchestration
- **Recovery Procedures**: Agent failures require manual intervention and cleanup

---

## 📄 LICENSE AND USAGE

This repository contains reference implementations extracted from a development project. 

**Recommended Approach:**
- Use as reference and inspiration
- Build your own implementations based on patterns shown
- Adapt commands to your specific environment and needs
- Respect any applicable licenses from underlying tools

---

## 🔗 RESOURCES

- [Claude Code CLI Documentation](https://claude.ai/code)
- [MCP Server Documentation](https://github.com/anthropic/mcp)
- [GitHub CLI Documentation](https://cli.github.com/)
- [Redis Documentation](https://redis.io/documentation)
- [tmux Documentation](https://github.com/tmux/tmux/wiki)

---

*Repository Status: Reference/Educational Use Only*  
*🚨 Featured: Multi-Agent Orchestration System (WIP Prototype)*  
*Last Updated: July 25, 2025*