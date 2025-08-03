# Claude Commands Reference Repository

> **⚠️ REFERENCE EXPORT ONLY**: This repository contains commands exported from a specific project for reference and sharing. These commands require adaptation for your environment.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/jleechanorg/claude-commands.git
cd claude-commands

# Auto-install commands and startup script
./install.sh

# Adapt commands for your project (see Adaptation Guide below)
# Then start Claude Code with MCP servers
./claude_start.sh
```

## 📋 What's Included

### Core Commands (3 exported so far)
- **`execute.md`**: Plan-Approve-Execute composition workflow
- **`debug.md`**: Systematic debugging with learning integration
- **`arch.md`**: MVP-focused architecture review for solo developers

### Installation System
- **`install.sh`**: Auto-installs commands to `.claude/commands/` and copies startup script
- **`claude_start.sh`**: Multi-service startup script (via infrastructure-scripts/)

### Infrastructure Scripts (Coming Soon)
- **Environment Bootstrap**: Complete Claude Code + MCP ecosystem startup
- **MCP Installation**: Comprehensive MCP server setup automation
- **GitHub Integration**: Repository-based command processing
- **Git Workflows**: Branch management and conflict resolution
- **CI/CD Setup**: Self-hosted runner automation
- **Service Management**: Multi-service orchestration utilities

## 🛠️ Installation Guide

### Prerequisites
- Git repository (install.sh validates git context)
- Claude Code CLI installed
- Bash shell environment

### Installation Steps

1. **Clone Repository**:
   ```bash
   git clone https://github.com/jleechanorg/claude-commands.git
   cd claude-commands
   ```

2. **Run Installation Script**:
   ```bash
   ./install.sh
   ```
   
   This will:
   - Create `.claude/commands/` directory if needed
   - Copy all command definitions from `commands/` to `.claude/commands/`
   - Install `claude_start.sh` to your repository root
   - Update `.gitignore` with appropriate entries

3. **Verify Installation**:
   ```bash
   ls -la .claude/commands/  # Should show installed commands
   ls -la claude_start.sh    # Should show startup script
   ```

### Adaptation Required

**⚠️ IMPORTANT**: These commands contain placeholder paths that need adaptation:

- Replace `$PROJECT_ROOT` with your actual project paths
- Update `your-project.com` with your domain
- Modify service configurations in `claude_start.sh`
- Adapt MCP server configurations for your environment

## 🎯 Command System Architecture

### Command Types

1. **Cognitive Commands**: Natural language understanding and analysis
   - `/debug` - Systematic debugging with evidence collection
   - `/arch` - Architecture review optimized for MVP development

2. **Execution Commands**: Direct task execution with progress tracking
   - `/execute` - Plan-approve-execute composition workflow

3. **Infrastructure Commands**: Development environment management
   - Startup scripts, MCP server management, git workflows

### Composition Patterns

Commands can be combined for enhanced functionality:
```bash
/debug /execute "fix authentication issue"    # Debug-enhanced execution
/arch /execute "refactor API layer"          # Architecture-reviewed implementation
```

## 🔧 Development Environment

### Claude Code Integration
These commands are designed to work with Claude Code CLI and require:
- MCP (Model Context Protocol) servers for enhanced capabilities
- TodoWrite integration for progress tracking
- Memory MCP for learning and pattern recognition

### Service Architecture
- **Claude Code CLI**: Primary interface
- **MCP Servers**: Context-aware tools and integrations
- **Memory System**: Persistent learning and knowledge graphs
- **Orchestration**: Multi-agent task delegation (coming soon)

## 📚 Advanced Features (Coming Soon)

### 🤖 Orchestration System (WIP Prototype)
- **Multi-agent Architecture**: tmux-based agents with Redis coordination
- **Autonomous Task Delegation**: `/orch "implement feature X"` with PR generation
- **Cost Metrics**: $0.003-$0.050 per task with success tracking
- **Monitoring**: Agent status, task progress, resource utilization

### 🔬 Claude Bot Self-Hosting System (Production Ready)
- **Repository-based Commands**: Process commands via GitHub issues
- **Automated Workflows**: GitHub Actions with self-hosted runner
- **PR Generation**: Automated pull request creation from command results

### ⚙️ Automated PR Fixer System (Production Ready)
- **Intelligent Cron Automation**: Every 10-minute PR analysis cycles
- **Comprehensive Error Handling**: Timeout detection, attempt limits
- **Email Notifications**: Manual intervention alerts

## 🚨 Current Status

**Phase**: Initial Export - Core Commands Only
- ✅ Basic command structure exported
- ✅ Installation system functional
- ⚠️ Infrastructure scripts pending export
- ⚠️ Advanced systems documentation in progress

**Next Exports Will Include**:
- Complete command library (70+ commands)
- Infrastructure scripts with adaptation guides
- Orchestration system documentation
- Bot self-hosting setup procedures
- Automated PR fixing system

## 📖 Usage Examples

### Basic Command Usage
```bash
# Plan and execute a task with automatic approval
/execute "add user authentication"

# Debug an issue with systematic approach
/debug "API timeout errors"

# Review architecture for MVP shipping
/arch security
```

### Command Composition
```bash
# Combined debugging and execution
/debug /execute "fix flaky test failures"

# Architecture review with implementation
/arch /execute "optimize database queries"
```

## 🔍 Troubleshooting

### Common Issues

1. **Commands Not Found**: Ensure `/install.sh` completed successfully
2. **Path Errors**: Adapt `$PROJECT_ROOT` placeholders in command files
3. **MCP Server Issues**: Update `claude_start.sh` with correct service paths

### Verification Steps
```bash
# Check command installation
ls -la .claude/commands/

# Verify file permissions
chmod +x claude_start.sh

# Test basic command loading
claude --help  # Should show installed commands
```

## 🤝 Contributing

This is a reference export repository. For issues or improvements:
1. Adapt commands for your environment
2. Test thoroughly in your project context
3. Share learnings and improvements via issues

## 📄 License

Reference commands exported for educational and development use. Adapt as needed for your projects.

---

**Last Export**: 2025-08-03  
**Source**: WorldArchitect.AI development command system  
**Status**: Partial export - core commands functional, full system pending