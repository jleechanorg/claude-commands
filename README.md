# Claude Commands Reference System

# ⚠️ REFERENCE ONLY - REQUIRES ADAPTATION

**WARNING**: This is a reference export from a specific project. These configurations require significant adaptation for your environment.

## 🚨 Important Notice

This export contains:
- Project-specific paths and configurations (`$PROJECT_ROOT/`, database configs)
- Hardcoded assumptions and dependencies
- Personal GitHub repository references 
- Setup-specific requirements

**Use as inspiration and reference, not direct implementation.**

## 🏗️ System Architecture

This is a comprehensive command system built for Claude Code CLI that provides:

- **Command Definitions**: Categorized by function (cognitive, operational, testing, development)
- **Command Composition**: Natural language execution of markdown-defined workflows  
- **Multi-Agent Orchestration**: WIP prototype system for autonomous task delegation
- **Memory Integration**: MCP-based learning and knowledge persistence
- **Git Workflow Integration**: Automated PR creation, testing, and deployment

### Command Categories

**🧠 Cognitive Commands** (Semantic Composition):
- `/think`, `/arch`, `/debug`, `/learn`, `/analyze`, `/fix` 
- Natural language understanding with automatic tool integration

**⚙️ Operational Commands** (Protocol Enforcement):
- `/headless`, `/handoff`, `/orchestrate` 
- Modify execution environment with mandatory workflow execution

**🔧 Tool Commands** (Direct Execution):
- `/execute`, `/test`, `/pr` 
- Immediate task execution with optional parameters

## 🚨 Orchestration System (WIP Prototype)

**Multi-agent task delegation system with Redis coordination**

### Architecture
- **tmux-based agents**: frontend, backend, testing, opus-master with A2A communication
- **Redis coordination**: Task routing and inter-agent communication
- **Autonomous workflow**: task creation → agent assignment → execution → PR creation
- **Cost metrics**: $0.003-$0.050 per task
- **Real-world verification**: Successful task completion with PR generation

### Usage Examples
```bash
/orch "fix failing tests"           # Autonomous test fixing
/orch "implement feature X"         # End-to-end feature development
/orch monitor agents               # System monitoring
```

### Setup Requirements
- Redis server running locally
- tmux installed and configured
- Python virtual environment
- Specialized agent workspaces
- GitHub CLI and token setup

## 📋 Installation Guide

### Prerequisites
```bash
# Required tools
brew install gh tmux redis jq
pip install mcp python-sdk anthropic

# Optional but recommended
pip install rg fd-find
```

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/your-project
cd your-project

# Set up virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
export PROJECT_ROOT=$(pwd)
export WORKSPACE_ROOT=$(dirname $(pwd))
export GITHUB_TOKEN="your_token_here"
```

### Claude Code Configuration
1. Copy `CLAUDE.md` to your project root
2. Adapt project-specific paths in CLAUDE.md:
   - Replace `$PROJECT_ROOT/` with your actual project paths
   - Update GitHub repository references
   - Modify test commands for your setup
3. Install commands in `.claude/commands/` directory
4. Update script paths in command files

### MCP Server Setup
```bash
# Memory MCP for learning integration
npm install @modelcontextprotocol/memory-server

# GitHub MCP for repository operations  
npm install @modelcontextprotocol/github-server

# Configure in Claude Code MCP settings
```

## 🎯 Key Commands

### Development Workflow
- `/execute [task]` - Direct task execution with TodoWrite tracking
- `/plan [task]` - Plan presentation requiring user approval
- `/think [topic]` - Enhanced thinking with memory integration
- `/test` - Comprehensive testing with real/mock modes

### Code Quality & Review
- `/fake` - Code authenticity audit and fake code detection
- `/review` - Comprehensive PR review with multi-source comment extraction
- `/arch` - Architecture analysis and design recommendations
- `/debug` - Evidence-based debugging with systematic approach

### Git & Deployment
- `/pr` - Automated PR creation with comprehensive descriptions
- `/push` - Smart push with conflict detection and resolution
- `/header` - Mandatory branch header for context tracking

### Orchestration & Scaling
- `/orch [task]` - Multi-agent task delegation (WIP prototype)
- `/handoff` - Agent coordination and task handoffs
- `/headless` - Background execution for long-running tasks

## 🔧 Adaptation Guide

### Path Configuration
Replace in all files:
```bash
# Update paths
sed -i 's|$PROJECT_ROOT|/your/actual/project/path|g' **/*.md
sed -i 's|$WORKSPACE_ROOT|/your/workspace/root|g' **/*.md
sed -i 's|$USER|yourusername|g' **/*.md
```

### Testing Setup
```bash
# Adapt test commands for your framework
# Replace references to:
TESTING=true python    # Your test runner
./run_tests.sh        # Your test script
./coverage.sh         # Your coverage tool
```

### Database & Services
```bash
# Replace service references:
Database              # Your database system
Web Framework         # Your web framework
your-project.com      # Your domain
```

## 📊 Performance Metrics

### Command Execution
- **Simple commands**: <2 seconds response time
- **Complex workflows**: 30-120 seconds with progress tracking
- **Multi-agent tasks**: 2-10 minutes with autonomous execution
- **Memory integration**: <500ms additional overhead

### Cost Analysis
- **Basic commands**: $0.001-$0.005 per execution
- **Orchestration tasks**: $0.003-$0.050 per task
- **Memory MCP**: $0.0001-$0.001 per search/create
- **GitHub API**: Rate limited, minimal cost impact

## 🔍 Troubleshooting

### Common Issues

**Command Not Found**
```bash
# Verify command installation
ls .claude/commands/
# Check command syntax
/list
```

**Path Errors**
```bash
# Verify environment variables
echo $PROJECT_ROOT
echo $WORKSPACE_ROOT
# Update CLAUDE.md paths
```

**MCP Connection Issues**
```bash
# Check MCP server status
npx @modelcontextprotocol/memory-server --help
# Verify Claude Code MCP configuration
```

**Orchestration Failures**
```bash
# Check Redis status
redis-cli ping
# Verify tmux installation
tmux --version
# Check agent workspace setup
```

### Performance Issues

**Slow Response Times**
- Check context length in CLAUDE.md (impacts performance)
- Reduce command complexity
- Use batch operations for multiple files

**Memory Usage**
- Monitor system resources during orchestration
- Limit concurrent agents (<3 recommended)
- Use lightweight commands for simple tasks

## 📚 Documentation Structure

```
claude-commands/
├── README.md              # This file
├── CLAUDE.md             # Primary configuration with warnings
├── commands/             # Command definitions
│   ├── execute.md        # Task execution framework
│   ├── orchestrate.md    # Multi-agent coordination
│   ├── think.md          # Enhanced reasoning
│   └── ...              # Additional commands
├── scripts/              # Implementation scripts
│   ├── orch.sh          # Orchestration runner
│   ├── git-header.sh     # Branch header generation
│   └── ...              # Supporting utilities
└── orchestration/       # Multi-agent system
    ├── README.md        # System overview
    ├── agent_system.py  # Core agent framework
    └── ...              # Implementation files
```

## 🔗 Resources

### External Documentation
- [Claude Code Overview](https://docs.anthropic.com/en/docs/claude-code/overview)
- [MCP Documentation](https://modelcontextprotocol.io/introduction)
- [Multi-Agent Systems Research](https://arxiv.org/html/2504.21030v1)

### Community
- [GitHub Issues](https://github.com/jleechanorg/claude-commands/issues)
- [Discussions](https://github.com/jleechanorg/claude-commands/discussions)

## 📄 License

Reference export for educational and development purposes. Adapt as needed for your environment.

## 🚀 Contributing

This is a reference export. For contributions:
1. Fork the repository
2. Adapt for your environment  
3. Share improvements via pull requests
4. Document your adaptations and lessons learned

---

**⚠️ Remember**: This system requires significant adaptation for your specific environment. Use as reference and inspiration, not direct implementation.