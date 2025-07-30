# Claude Commands Reference Repository

> ⚠️ **REFERENCE ONLY - DO NOT USE DIRECTLY**
> 
> This is a reference export from a specific project setup. These configurations:
> - May contain project-specific paths and settings
> - Have not been tested in isolation
> - May require significant adaptation for your environment
> - Include setup-specific assumptions and dependencies

## Overview

This repository contains a comprehensive Claude command system export, including:
- **100+ slash commands** for enhanced AI collaboration
- **Multi-agent orchestration system** (WIP prototype) with proven production usage
- **Supporting scripts and utilities**
- **Complete documentation and setup guides**

## 🚨 Orchestration System (WIP Prototype)

The orchestration system is an active development prototype with real-world production metrics:

### Architecture
- **tmux-based agent isolation**: Each agent runs in its own session
- **Redis coordination**: Agent-to-agent (A2A) communication protocol
- **Dynamic agent pool**: frontend, backend, testing, opus-master agents
- **Autonomous workflows**: Task delegation → execution → PR creation

### Real-World Metrics
- **Cost**: $0.003-$0.050 per task
- **Success rate**: Verified PR generation from autonomous execution
- **Scale**: Handles complex multi-step workflows

### Quick Start
```bash
# Start Redis server
redis-server

# Basic usage
/orch "fix all failing tests and create PR"

# Monitor agents
/orch monitor agents

# Direct tmux access
tmux attach -t agent-frontend-1
```

## Command Categories

### 🧠 Cognitive Commands
Semantic understanding and analysis:
- `/think` - Structured problem-solving
- `/arch` - Architecture analysis
- `/debug` - Systematic debugging
- `/analyze` - Code analysis
- `/perp` - Multi-AI perspective analysis

### ⚙️ Operational Commands
Protocol enforcement and execution:
- `/headless` - Headless execution mode
- `/handoff` - Task handoff protocol
- `/orchestrate` - Multi-agent delegation
- `/execute` - Direct task execution

### 🔧 Tool Commands
Direct action commands:
- `/test` - Test execution
- `/pr` - Pull request operations
- `/fixpr` - PR issue resolution
- `/pushl` - Enhanced git push
- `/review` - Code review extraction

### 📚 Meta Commands
System and learning:
- `/learn` - Memory enhancement
- `/list` - Command listing
- `/help` - Help system
- `/exportcommands` - Export workflow

## Installation

### Prerequisites
- Claude Code CLI installed
- Git and GitHub CLI configured
- Python 3.11+ with virtual environment
- Redis server (for orchestration)
- tmux (for agent management)

### Basic Setup
```bash
# Clone this repository
git clone https://github.com/jleechanorg/claude-commands.git
cd claude-commands

# Create .claude directory structure
mkdir -p ~/.claude/commands
cp -r commands/* ~/.claude/commands/

# Copy scripts
mkdir -p ~/claude_command_scripts
cp -r scripts/* ~/claude_command_scripts/

# Set up orchestration (optional)
cp -r orchestration ~/
```

### Environment Variables
```bash
export WORKSPACE_ROOT="$HOME/projects/your-project"
export PROJECT_ROOT="$WORKSPACE_ROOT/your-app"
export GITHUB_TOKEN="your-token-here"
```

## Adapting for Your Project

### Path Replacements
All exported files use placeholders that need replacement:
- `$PROJECT_ROOT` → Your project's root directory
- `$WORKSPACE_ROOT` → Your workspace directory
- `${USER}` → Your username
- `your-project.com` → Your project domain

### Example Adaptation
```bash
# Replace placeholders in all files
find ~/.claude -type f -exec sed -i \
  -e "s|\$PROJECT_ROOT|/path/to/your/project|g" \
  -e "s|\$WORKSPACE_ROOT|/path/to/workspace|g" \
  -e "s|your-project.com|myproject.com|g" {} \;
```

## Command Composition Architecture

Claude commands use two composition mechanisms:

### Universal Composition (Cognitive Commands)
- Natural language understanding
- Semantic tool integration
- Adaptive execution

### Protocol Enforcement (Operational Commands)
- Mandatory workflow execution
- State management
- Error recovery

## Memory MCP Integration

Many commands integrate with Memory MCP for enhanced context:
- Automatic memory search
- Learning persistence
- Context enhancement

Enhanced commands: `/think`, `/learn`, `/debug`, `/analyze`, `/fix`, `/plan`, `/execute`, `/arch`, `/test`, `/pr`

## Troubleshooting

### Common Issues

1. **Command not found**
   - Verify `.claude/commands/` directory exists
   - Check file permissions (should be readable)
   - Restart Claude Code CLI

2. **Path errors**
   - Replace all placeholder variables
   - Use absolute paths
   - Check environment variables

3. **Orchestration issues**
   - Ensure Redis is running
   - Verify tmux is installed
   - Check agent workspace permissions

### Getting Help

For issues specific to:
- **This export**: Open issue on this repository
- **Claude Code**: Visit https://github.com/anthropics/claude-code/issues
- **Your adaptation**: Check original project documentation

## Contributing

This is a reference repository. Contributions should focus on:
- Improving documentation clarity
- Adding adaptation examples
- Fixing export issues
- Enhancing filtering rules

## License

This export is provided as-is for reference purposes. Original commands may have their own licensing terms.

## Acknowledgments

- Claude Code team for the command system architecture
- Original project contributors
- Community feedback and improvements

---

Remember: This is a reference implementation. Always adapt commands to your specific environment and requirements.