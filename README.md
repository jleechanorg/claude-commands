# Claude Commands Export Repository

## 🚨 WARNING AND DISCLAIMER

### **REFERENCE-ONLY REPOSITORY**
This repository contains commands and configurations extracted from the WorldArchitect.AI project as reference material. These commands are:

- **⚠️ UNTESTED** in isolation outside their original environment
- **⚠️ PROJECT-SPECIFIC** with configurations tailored to WorldArchitect.AI workflows
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

orchestration/           # Multi-agent system (requires Redis/tmux)
├── agent_system.py     # Agent management
├── task_dispatcher.py  # Load balancing
└── redis_a2a_bridge.py # Agent communication

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
| `/orchestrate` | Multi-agent task delegation | Redis, tmux |
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
redis-server           # Orchestration backend (optional)
tmux                   # Multi-session management (optional)
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

### Advanced Orchestration
```bash
# Multi-agent task delegation (requires Redis/tmux setup)
/orchestrate implement user authentication system
/orchestrate analyze performance bottlenecks across codebase
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
   # Add other configuration as needed
   ```

3. **Install Python dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt  # If available
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

**Redis Connection (for orchestration)**
```bash
# Start Redis server
redis-server

# Test connection
redis-cli ping  # Should return: PONG
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
- **Orchestration system** - Requires complete Redis/tmux infrastructure
- **GitHub workflows** - Needs API reconfiguration for your repositories
- **Testing commands** - Framework-specific modifications required

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
- **Environment Coupling**: Contains WorldArchitect.AI-specific assumptions
- **Dependency Complexity**: Heavy reliance on specific MCP servers and tools
- **Testing Status**: Many commands are experimental/untested in isolation
- **Performance**: Command composition can generate very long prompts

### Migration Considerations
**High-Effort**: Orchestration system, GitHub workflows, Memory integration
**Medium-Effort**: Testing commands, project workflows, composition patterns  
**Low-Effort**: Basic cognitive commands, simple utilities

---

## 📄 LICENSE AND USAGE

This repository contains reference implementations extracted from the WorldArchitect.AI project. 

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

---

*Repository Status: Reference/Educational Use Only*
*Last Updated: July 25, 2025*