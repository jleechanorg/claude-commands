# Claude Commands - Command Composition System

⚠️ **REFERENCE EXPORT** - This is a reference export from a working Claude Code project. These commands have been tested in production but may require adaptation for your specific environment. Claude Code excels at helping you customize them for your workflow.

Transform Claude Code into an autonomous development powerhouse through simple command hooks that enable complex workflow orchestration.

## 🚀 ONE-CLICK INSTALL

```bash
./install.sh
```

Auto-installs **104 commands** + **12 hooks** + **infrastructure scripts** to your `.claude/` directory and copies `claude_start.sh` for immediate use.

## 📊 **Export Contents**

This comprehensive export includes:
- **📋 104 Command Definitions** - Complete workflow orchestration system (.claude/commands/)
- **📎 12 Claude Code Hooks** - Essential workflow automation (.claude/hooks/)
- **🔧 5 Infrastructure Scripts** - Development environment management
- **🤖 Orchestration System** - Core multi-agent task delegation (project-specific parts excluded)
- **📚 Complete Documentation** - Installation guide with adaptation examples

🚨 **DIRECTORY EXCLUSIONS APPLIED**: This export excludes the following project-specific directories:
- ❌ `analysis/` - Project-specific analytics
- ❌ `automation/` - Project-specific automation
- ❌ `claude-bot-commands/` - Project-specific bot implementation
- ❌ `coding_prompts/` - Project-specific AI prompting templates
- ❌ `prototype/` - Project-specific experimental code

## 🎯 The Magic: Simple Hooks → Powerful Workflows

### Command Chaining Examples
```bash
# Multi-command composition
"/arch /thinku /devilsadvocate /diligent"  # → comprehensive code analysis

# Sequential workflow chains
"/think about auth then /execute the solution"  # → analysis → implementation

# Conditional execution flows
"/test login flow and if fails /fix then /pr"  # → test → fix → create PR
```

## 📎 **Enhanced Hook System**

This export includes **12 Claude Code hooks** that provide essential workflow automation with nested directory support and NUL-delimited processing for whitespace-safe file handling.

## 🔧 Installation & Setup

### Quick Start
```bash
# 1. Clone this repository to your project
git clone https://github.com/jleechanorg/claude-commands.git

# 2. Run one-click install
cd claude-commands
./install.sh

# 3. Start Claude Code with MCP servers
./claude_start.sh

# 4. Begin using composition commands
/execute "implement user authentication"
/pr "fix performance issues"
/copilot  # Fix any PR issues
```

## 🎯 Adaptation Guide

### Project-Specific Placeholders

Commands contain placeholders that need adaptation:
- `$PROJECT_ROOT/` → Your project's main directory
- `your-project.com` → Your domain/project name
- `$USER` → Your username
- `TESTING=true python` → Your test execution pattern

### Example Adaptations

**Before** (exported):
```bash
TESTING=true python $PROJECT_ROOT/test_file.py
```

**After** (adapted):
```bash
npm test src/components/test_file.js
```

## ⚠️ Important Notes

### Reference Export
This is a filtered reference export from a working Claude Code project. Commands may need adaptation for your specific environment, but Claude Code excels at helping you customize them.

### Requirements
- **Claude Code CLI** - Primary requirement for command execution
- **Git Repository Context** - Commands operate within git repositories
- **MCP Server Setup** - Some commands require MCP (Model Context Protocol) servers
- **Project-Specific Adaptation** - Paths and commands need customization for your environment

---

🚀 **Generated with [Claude Code](https://claude.ai/code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
