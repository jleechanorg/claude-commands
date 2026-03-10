# Claude Commands - Command Composition System

⚠️ **REFERENCE EXPORT** - This is a reference export from a working Claude Code project.

## Export Contents

- **0 commands** workflow orchestration commands
- **0 hooks** Claude Code automation hooks
- **3 scripts** reusable automation scripts (scripts/)
- **1 skills** shared knowledge references (.claude/skills/)

## MANUAL INSTALLATION

Run these from the export directory (the one containing the `staging/` folder), targeting your project repository as the current working directory:

Copy the exported commands and hooks to your project's `.claude/` directory:
- Commands → `.claude/commands/`
- Hooks → `.claude/hooks/`
- Agents → `.claude/agents/`
- Scripts → `scripts/` in your project root
- Skills → `.claude/skills/`

## 📊 **Export Contents**

This comprehensive export includes:
- **📋 0 Command Definitions** - Complete workflow orchestration system (.claude/commands/)
- **📎 0 Claude Code Hooks** - Essential workflow automation (.claude/hooks/)
- **🤖 0 Agent Definitions** - Specialized task agents for autonomous workflows (.claude/agents/)
- **🧠 1 Skills** - Knowledge base exports (.claude/skills/)
- **🔧 3 Scripts** - Development environment management (scripts/)
- **🤖 Orchestration System** - Core multi-agent task delegation (project-specific parts excluded)
- **📚 Complete Documentation** - Setup guide with adaptation examples

🚨 **DIRECTORY EXCLUSIONS APPLIED**: This export excludes the following project-specific directories:
- ❌ `analysis/` - Project-specific analytics
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

This export includes **0 Claude Code hooks** that provide essential workflow automation with nested directory support and NUL-delimited processing for whitespace-safe file handling.

## 🔧 Setup & Usage

### Quick Start
```bash
# 1. Clone this repository to your project
git clone https://github.com/jleechanorg/claude-commands.git

# 2. Copy commands and hooks to your .claude directory
cp -r claude-commands/commands/* .claude/commands/
cp -r claude-commands/hooks/* .claude/hooks/
cp -r claude-commands/agents/* .claude/agents/
cp -r claude-commands/skills/* .claude/skills/

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
