# 📚 Claude Commands - Reference Export

## ⚠️ Important Disclaimer

**This is a reference export from a working Claude Code project.** These commands and configurations contain project-specific paths, settings, and assumptions that require adaptation for your environment.

**You may need to personally debug some configurations, but Claude Code can easily adjust for your specific needs.**

These configurations may include:
- Project-specific paths and settings that need updating for your environment
- Setup assumptions and dependencies specific to the original project
- References to particular GitHub repositories and project structures

Feel free to use these as a starting point - Claude Code excels at helping you adapt and customize them for your specific workflow.

---

## 🚀 Introduction

This repository contains a comprehensive Claude Code command system designed for AI-powered development workflows. The system includes:

- **70+ slash commands** for development, testing, debugging, and automation
- **Multi-agent orchestration system** for parallel task delegation
- **Complete infrastructure scripts** for development environment management
- **Automated PR processing** with intelligent code review and fixing
- **Self-hosted Claude bot** for repository-based command processing

### Quick Start

1. **Install**: Run `./install-claude-commands.sh` for automated setup
2. **Explore**: Use `/help` and `/list` to discover available commands
3. **Start Simple**: Try cognitive commands like `/think`, `/arch`, `/debug`
4. **Scale Up**: Explore orchestration with `/orch` for parallel workflows

---

## 📋 Table of Contents

- [🎯 Main Highlights](#-main-highlights)
  - [Orchestration System](#orchestration-system)
  - [Most Interesting Commands](#most-interesting-commands)
  - [Most Interesting Scripts](#most-interesting-scripts)
- [🛠️ Installation & Setup](#️-installation--setup)
- [📂 System Architecture](#-system-architecture)
- [🔧 Command Categories](#-command-categories)
- [🚀 Advanced Systems](#-advanced-systems)
- [📖 Usage Examples](#-usage-examples)
- [🔍 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)

---

## 🎯 Main Highlights

### Orchestration System

**🚨 Multi-Agent Task Delegation (WIP Prototype)**

The orchestration system enables parallel AI agent execution for complex development workflows:

```bash
# Autonomous multi-agent task delegation
/orch "fix all failing tests and create PR"
/orch "implement user authentication feature"
/orch "analyze performance bottlenecks"

# Real-time agent monitoring
/orch monitor agents
/orch What's the status?
```

**Key Features:**
- **tmux-based agents** with specialized capabilities (frontend, backend, testing, opus-master)
- **Redis coordination** for A2A communication and task distribution
- **Cost-effective**: $0.003-$0.050 per task
- **Autonomous workflow**: task creation → agent assignment → execution → PR creation
- **Production verified**: Successfully creates PRs and completes complex workflows

**Architecture:**
- **Agent Management**: Dynamic task agents (task-agent-*) managed by Python monitor
- **Scaling**: 3-5 parallel agents simultaneously
- **Monitoring**: Real-time status via `/orch monitor` and direct tmux attachment
- **Recovery**: Timeout handling, failed agent cleanup, orphaned task management

### Most Interesting Commands

#### 🧠 Cognitive Commands (AI-Enhanced)

1. **`/think`** - Sequential thinking with memory enhancement
   ```bash
   /think "How should we architect the user authentication system?"
   ```
   - Multi-step reasoning with memory integration
   - Persistent learning across sessions
   - Technical problem decomposition

2. **`/arch`** - Architecture analysis and design
   ```bash
   /arch "Review the current microservices setup"
   ```
   - System architecture evaluation
   - Design pattern recommendations
   - Scalability assessment

3. **`/copilot`** - Autonomous PR analysis and fixing
   ```bash
   /copilot  # Analyzes current PR context
   /copilot 1234  # Analyzes specific PR
   ```
   - **6-phase workflow**: Status → Comments → CI/Conflicts → Responses → Coverage → Sync
   - **Enhanced context replies** with threaded conversation analysis
   - **Autonomous operation** with merge approval safeguards

#### ⚙️ Operational Commands (Workflow Automation)

4. **`/execute`** - Auto-approved task execution
   ```bash
   /execute "refactor the database layer"
   ```
   - Built-in auto-approval for streamlined workflows
   - TodoWrite progress tracking
   - Complexity assessment and parallel execution decisions

5. **`/fake`** - Comprehensive fake code detection
   ```bash
   /fake  # Audits entire codebase for fake implementations
   ```
   - **Composition**: `/arch /thinku /devilsadvocate /diligent`
   - Identifies placeholder code, demo implementations, duplicate protocols
   - Prevents shipping non-functional code

#### 🔬 Meta Commands (System Management)

6. **`/learn`** - Unified learning with Memory MCP integration
   ```bash
   /learn "API integration patterns"
   ```
   - Persistent knowledge graph storage
   - Auto-learning from corrections and failures
   - Cross-session knowledge retention

### Most Interesting Scripts

#### 🚀 Development Environment Management

1. **`claude_start.sh`** - Complete ecosystem startup
   ```bash
   ./claude_start.sh
   ```
   - **Multi-service management**: Claude Code CLI, MCP servers, orchestration system
   - **Health checks**: Service verification and dependency validation
   - **Logging**: Branch-isolated logs in `/tmp/your-project.com/[branch]/`
   - **Auto-recovery**: Failed service restart and monitoring

2. **`claude_mcp.sh`** - Comprehensive MCP server installation
   ```bash
   ./claude_mcp.sh
   ```
   - **20+ MCP servers**: GitHub, filesystem, memory, browser automation, AI models
   - **Automated installation**: Package management, configuration, testing
   - **Error handling**: Detailed diagnostics and recovery procedures
   - **Integration testing**: End-to-end MCP functionality validation

#### 🤖 Autonomous Systems

3. **`automation/simple_pr_batch.sh`** - Intelligent PR automation (Production Ready)
   ```bash
   # Runs via cron every 10 minutes
   */10 * * * * /path/to/simple_pr_batch.sh
   ```
   - **Autonomous `/copilot` integration** for comprehensive PR analysis
   - **Error handling**: Timeout detection (20min), attempt limits (max 3), cooldown (4hr)
   - **Email notifications**: Manual intervention alerts
   - **Production metrics**: Success rates, processing frequency, failure patterns

4. **`start-claude-bot.sh`** - GitHub-based command processing (Production Ready)
   ```bash
   ./start-claude-bot.sh
   ```
   - **Repository-native commands**: Post GitHub issue → Self-hosted runner → Claude execution
   - **Automated PR creation**: Command results posted as PR with threaded responses
   - **Version-controlled history**: All commands tracked in repository issues
   - **Debugging tools**: Comprehensive test suite and error diagnostics

#### 🔧 Git Workflow Management

5. **`integrate.sh`** - Fresh branch creation workflow
   ```bash
   ./integrate.sh
   ```
   - **Fresh branches from main**: Automated cleanup and safety checks
   - **Context preservation**: Scratchpad migration and progress tracking
   - **Conflict prevention**: Pre-integration validation and dependency checks

6. **`resolve_conflicts.sh`** - Systematic conflict resolution
   ```bash
   ./resolve_conflicts.sh
   ```
   - **Critical file analysis**: CSS, main.py, configs, schemas prioritization
   - **Both-version assessment**: Intelligent merge strategy selection
   - **Test integration**: Conflict resolution validation
   - **Documentation**: Decision tracking and rollback procedures

---

## 🛠️ Installation & Setup

### Automated Installation

```bash
# Clone the repository
git clone https://github.com/jleechanorg/claude-commands.git
cd claude-commands

# Run the installer
./install-claude-commands.sh
```

The installer will:
- ✅ Check prerequisites (git, python3, pip)
- ✅ Set up directory structure
- ✅ Install command definitions and scripts
- ✅ Configure infrastructure components
- ✅ Validate the installation

### Manual Setup

1. **Prerequisites**:
   - Claude Code CLI: https://claude.ai/code
   - Git, Python 3.8+, pip
   - Optional: Redis (for orchestration), tmux (for agents)

2. **Directory Structure**:
   ```
   your-project/
   ├── .claude/commands/     # Command definitions
   ├── claude_command_scripts/  # Script implementations
   ├── orchestration/        # Multi-agent system (optional)
   ├── automation/          # PR automation (optional)
   ├── claude-bot-commands/ # Self-hosted bot (optional)
   └── infrastructure-scripts/  # Environment management
   ```

3. **Configuration**:
   - Copy `CLAUDE.md` to your project root
   - Adapt file paths and project references
   - Configure MCP servers using `claude_mcp.sh`

---

## 📂 System Architecture

### Command Processing Architecture

**Dual Composition System:**
- **Cognitive Commands**: `/think`, `/arch`, `/debug` - Universal semantic understanding
- **Operational Commands**: `/orchestrate`, `/handoff` - Protocol enforcement
- **Tool Commands**: `/execute`, `/test`, `/pr` - Direct task execution

### Data Flow

```
User Input → Command Recognition → Type Classification → Workflow Execution
     ↓              ↓                    ↓                    ↓
Slash Command → .md Template → Command Logic → Tool Execution
     ↓              ↓                    ↓                    ↓
Context → Memory Enhancement → Result Generation → Progress Tracking
```

### Memory Enhancement

Enhanced commands automatically integrate Memory MCP for:
- Previous experiences and patterns
- Technical learnings from corrections
- Cross-session knowledge retention
- Workflow insights and optimizations

---

## 🔧 Command Categories

### 🧠 Cognitive (AI-Enhanced Thinking)
- `/think` - Sequential reasoning with memory
- `/arch` - Architecture analysis and design
- `/debug` - Enhanced debugging with context
- `/learn` - Knowledge capture and retention
- `/analyze` - Deep technical analysis

### ⚙️ Operational (Workflow Automation)
- `/execute` - Auto-approved task execution
- `/orchestrate` - Multi-agent delegation
- `/copilot` - Autonomous PR processing
- `/handoff` - Context-aware task transfer

### 🔧 Tool (Direct Execution)
- `/test` - Comprehensive testing workflows
- `/pr` - Pull request management
- `/pushl` - Git operations with verification
- `/fixpr` - CI failure analysis and resolution

### 🎯 Meta (System Management)
- `/fake` - Code quality auditing
- `/exportcommands` - System sharing and backup
- `/header` - Branch context tracking
- `/list` - Command discovery

---

## 🚀 Advanced Systems

### Orchestration System Setup

1. **Prerequisites**:
   ```bash
   # Install Redis
   sudo apt-get install redis-server  # Ubuntu/Debian
   brew install redis                 # macOS
   
   # Install tmux
   sudo apt-get install tmux         # Ubuntu/Debian
   brew install tmux                 # macOS
   ```

2. **Start the system**:
   ```bash
   ./orchestration/start_system.sh start
   ```

3. **Usage examples**:
   ```bash
   /orch "fix failing tests in the authentication module"
   /orch "implement user dashboard with real-time updates"
   /orch monitor agents
   ```

### Automation System Setup

1. **Install**:
   ```bash
   # Set up cron job
   crontab -e
   # Add: */10 * * * * /path/to/automation/simple_pr_batch.sh
   ```

2. **Configure email notifications**:
   ```bash
   # Edit automation/simple_pr_batch.sh
   # Set EMAIL_RECIPIENT and SMTP settings
   ```

### Claude Bot System Setup

1. **GitHub repository setup**:
   ```bash
   # Create repository for command processing
   gh repo create claude-commands --private
   ```

2. **Self-hosted runner setup**:
   ```bash
   ./setup-github-runner.sh
   ```

3. **Bot server startup**:
   ```bash
   ./start-claude-bot.sh
   ```

---

## 📖 Usage Examples

### Basic Workflow

```bash
# Discover available commands
/list

# Start with thinking
/think "How should we approach this refactoring?"

# Execute the plan
/execute "refactor user authentication system"

# Create PR and review
/pr "Refactor authentication for better security"
/copilot  # Autonomous PR analysis and fixing
```

### Advanced Orchestration

```bash
# Parallel development
/orch "implement login API endpoints"
/orch "create user dashboard UI"
/orch "write integration tests"

# Monitor progress
/orch monitor agents
/orch What's the status?

# Complex workflows
/orch "analyze performance, fix bottlenecks, and optimize database queries"
```

### Automated Maintenance

```bash
# Set up automation (one-time)
./automation/setup_automation.sh

# Commands run automatically:
# - PR analysis every 10 minutes
# - CI failure fixing
# - Comment response generation
# - Email alerts for manual intervention
```

---

## 🔍 Troubleshooting

### Common Issues

1. **Command not found**:
   ```bash
   # Check if Claude Code CLI is installed
   claude --version
   
   # Verify command exists
   ls .claude/commands/
   ```

2. **MCP server failures**:
   ```bash
   # Reinstall MCP servers
   ./claude_mcp.sh
   
   # Check specific server status
   claude list-mcps
   ```

3. **Orchestration issues**:
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Restart orchestration system
   ./orchestration/start_system.sh restart
   ```

### Debug Commands

```bash
# System diagnostics
/debug "MCP server connectivity"

# Memory analysis
/learn --debug

# Architecture review
/arch --validate
```

---

## 🤝 Contributing

### Adding New Commands

1. **Create command definition**:
   ```bash
   # Add to .claude/commands/new-command.md
   # Follow existing patterns and documentation
   ```

2. **Implement functionality**:
   ```bash
   # Add script to claude_command_scripts/ if needed
   # Keep Python minimal, leverage Claude intelligence
   ```

3. **Test integration**:
   ```bash
   # Test command execution
   /new-command --test
   
   # Verify with fake code detection
   /fake
   ```

### Best Practices

- **Minimal Python**: Use for data collection only
- **Maximum Claude**: Leverage AI intelligence in .md files
- **Explicit execution**: Users should see what's running
- **Memory integration**: Enhance commands with learning
- **Error handling**: Graceful degradation with helpful messages

### Development Principles

- **Single Responsibility**: Each command does one thing well
- **Clear Interfaces**: Obvious inputs, outputs, side effects
- **Documentation**: Every command has usage examples
- **Testing**: Validate both automated and manual execution

---

**For support and updates, visit: https://github.com/jleechanorg/claude-commands**

---

*Generated with Claude Code - AI-powered development workflows*