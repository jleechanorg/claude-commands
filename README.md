# 🤖 Claude Commands - Reference Export

**⚠️ REFERENCE ONLY**: This is an exported reference from a working Claude Code project. Configurations require adaptation for your environment.

## 🚀 ONE-CLICK INSTALL

```bash
./install.sh
```

The install script automatically:
- ✅ Copies commands from `commands/` to `.claude/commands/`
- ✅ Installs `claude_start.sh` to root directory with executable permissions
- ✅ Updates `.gitignore` with installed files
- ✅ Provides clear next steps and adaptation guidance

## 📋 Contents

### **🚀 ONE-CLICK INSTALL**: `./install.sh` script auto-installs commands to `.claude/commands/` and copies `claude_start.sh`
- Complete command system (100+ commands)
- **🚨 Infrastructure Scripts**: Complete development environment management (8+ scripts)
  - **Environment Bootstrap**: `claude_start.sh` - Multi-service startup with health checks
  - **MCP Installation**: `claude_mcp.sh` - Comprehensive MCP server setup automation
  - **GitHub Integration**: `start-claude-bot.sh` - Repository-based command processing
  - **Git Workflows**: `integrate.sh`, `resolve_conflicts.sh`, `sync_branch.sh` - Branch management
  - **CI/CD Setup**: `setup-github-runner.sh` - Self-hosted runner automation
  - **Service Management**: `test_server_manager.sh` - Multi-service orchestration

### Command Categories
- **🧠 Cognitive Commands**: `/think`, `/arch`, `/debug`, `/learn`, `/analyze`, `/fix`, `/perp`, `/research`
- **⚙️ Operational Commands**: `/headless`, `/handoff`, `/orchestrate` - Modify execution environment
- **🔧 Tool Commands**: `/execute`, `/test`, `/pr` - Direct task execution

## 🛠️ Installation & Setup

### Prerequisites
- Git repository (script validates git context)
- Claude Code CLI installed
- Bash shell environment

### Quick Start
1. **Clone this repository**:
   ```bash
   git clone https://github.com/jleechanorg/claude-commands.git
   cd claude-commands
   ```

2. **Run the installer**:
   ```bash
   ./install.sh
   ```

3. **Adapt for your project**:
   - Replace `$PROJECT_ROOT` placeholders in commands
   - Update `claude_start.sh` with your project-specific paths
   - Configure MCP servers for your environment

4. **Start Claude Code**:
   ```bash
   ./claude_start.sh
   ```

### Manual Installation
If you prefer manual setup:
1. Copy `commands/*` to `.claude/commands/`
2. Copy `infrastructure-scripts/claude_start.sh` to your project root
3. Make claude_start.sh executable: `chmod +x claude_start.sh`
4. Add to `.gitignore`: `.claude/`, `claude_start.sh`

## ⚠️ Adaptation Requirements

**These are reference commands that require project-specific adaptation**:

### Path Placeholders
- `$PROJECT_ROOT/` → Replace with your project's main directory
- `your-project.com` → Replace with your domain/project name
- `$USER` → Replace with your username

### Project-Specific Components
- **Database connections**: Update Firebase/database references
- **API endpoints**: Modify service URLs and authentication
- **Test paths**: Adjust test file locations and commands
- **Deployment configs**: Update Docker/cloud deployment settings

### MCP Server Configuration
The `claude_start.sh` script includes MCP server setup. You may need to:
- Install required MCP servers for your stack
- Configure authentication tokens
- Adjust service ports and endpoints

## 🔧 Command Usage

### Basic Command Structure
```bash
# Cognitive commands (thinking and analysis)
/think [task]
/debug [issue]
/analyze [component]

# Operational commands (environment control)
/execute [task]
/orchestrate [complex-task]

# Tool commands (direct execution)
/test [type]
/pr [action]
```

### Universal Composition
Commands can be composed naturally:
```bash
/think /execute "implement user authentication"
/debug /fix "resolve test failures"
```

## 📚 Documentation Structure

### Core Files
- **CLAUDE.md**: Primary operating protocol and rules
- **README.md**: This installation and usage guide
- **install.sh**: Automated installation script

### Command Categories
- **Infrastructure Scripts**: Development environment management
- **Command Definitions**: Executable Claude command templates
- **Documentation**: Setup guides and usage examples

## 🚨 Important Notes

### Reference Export Limitations
1. **Project-Specific Paths**: Many commands contain hardcoded paths that need updating
2. **Service Dependencies**: MCP servers and external services require configuration
3. **Authentication**: GitHub tokens and API keys need to be set up
4. **Testing Framework**: Test commands may need adaptation for your project structure

### Security Considerations
- Review all scripts before execution
- Update authentication tokens and API keys
- Verify file permissions and access controls
- Test in a safe environment before production use

## 🔍 Troubleshooting

### Common Issues
1. **Command not found**: Verify `.claude/commands/` directory exists and contains files
2. **Permission denied**: Ensure `claude_start.sh` is executable (`chmod +x claude_start.sh`)
3. **Path errors**: Update `$PROJECT_ROOT` placeholders in command files
4. **MCP server failures**: Check MCP server installation and configuration

### Getting Help
- Check command documentation in `.claude/commands/`
- Review CLAUDE.md for operational protocols
- Test commands in isolation before complex workflows
- Adapt paths and configurations for your environment

## 🎯 Next Steps

1. **Install and test basic commands**
2. **Configure MCP servers for your stack**
3. **Adapt project-specific paths and references**
4. **Test workflow with your repository**
5. **Customize commands for your development patterns**

---

**Remember**: These are reference commands from a working project. Claude Code excels at helping you adapt and customize them for your specific workflow and requirements.
