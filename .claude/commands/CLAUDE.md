---
description: Command System Enumerator
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execution Instructions for Claude

**Action Steps:**
When this command is invoked:
1. Read the repository tree under `.claude/commands/`
2. Group `*.md` files by category (execution, planning, testing, git, orchestration, quality, ai, research, review)
3. Print a categorized inventory with brief descriptions and file paths
4. Support optional filtering by category or command name substring

**Primary Rules**: Inherits from [../../CLAUDE.md](../../CLAUDE.md) (complete project protocols)

## 📋 REFERENCE DOCUMENTATION

# Command System Enumerator

**Command Summary**: Executable command that enumerates available commands by category
**Usage**: `/commands [filter]` where filter is optional category or command substring  
**Output**: Categorized command inventory with descriptions and file paths

## 🚨 MODULE-SPECIFIC PROTOCOLS

- Do not duplicate systematic protocols from other .md files; link instead
- Never reimplement existing command functionality; orchestrators must delegate to existing commands (/commentreply, /pushl, /fixpr, etc.)  
- Never duplicate GitHub API calls already implemented by other commands

## Directory Contents Analysis

**Core Command Files** (80+ .md files):
- **Execution**: `execute.md`, `e.md` - Main task execution commands
- **Planning**: `plan.md`, `arch.md`, `design.md` - Architectural and planning workflows
- **Testing**: `test.md`, `tdd.md`, `testui.md`, `testhttpf.md` - Testing command suite
- **Git Operations**: `push.md`, `pushl.md`, `pr.md`, `integrate.md` - Git workflow automation
- **Orchestration**: `orch.md`, `orchestrate.md`, `handoff.md` - Multi-agent coordination
- **Code Quality**: `fake.md`, `fake3.md`, `lint_utils.py` - Code quality validation
- **AI Integration**: `cereb.md`, `cerebras.md`, `qwen.md` - AI service commands
- **Research**: `research.md`, `perp.md` - Information gathering commands
- **Review**: `reviewe.md`, `review-enhanced.md`, `copilot.md` - Code review automation

**Specialized Command Categories**:
- **Debug Commands**: `debug.md`, `debugp.md`, `debug-protocol.md` - Systematic debugging
- **Memory Commands**: `learn.md`, `memory_enhancement_hook.py` - Knowledge management
- **Export Commands**: `exportcommands.md`, `exportcommands.py` - Project export utilities
- **Status Commands**: `gstatus.md`, `context.md`, `header.md` - Project status reporting

**Python Automation Scripts** (12 .py files):
- `orchestrate.py`, `orch.py` - Orchestration system backend
- `push.py`, `pr_utils.py` - Git workflow automation utilities  
- `exportcommands.py` - Project export functionality
- `think.py`, `learn.py` - Cognitive enhancement tools
- `timeout.py` - Command timeout management
- `header_check.py` - Git header validation

**Shell Scripts & Utilities** (8 .sh files):
- `pushl.sh` - Automated labeling and push workflow
- `comprehensive_export_filter.sh` - Export filtering logic
- `cerebras_direct.sh` - Direct Cerebras API integration
- `copilot_inline_reply_example.sh` - Copilot integration example

**Support Modules**:
- `_copilot_modules/` - Copilot command infrastructure (4 Python files)
- `cerebras/` - Cerebras integration with tests (3 files)
- `lib/` - Shared utilities (`fake_detector.py`, `request_optimizer.py`)
- `tests/` - Command system validation tests (8 test files)

## Command Architecture

**Two Command Types**:
1. **Cognitive Commands** (`/think`, `/debug`, `/plan`): Natural language processing and analysis
2. **Operational Commands** (`/orch`, `/execute`, `/push`): Direct system operations and automation

**Execution Patterns**:
- **Markdown Commands**: Claude reads .md file content and executes instructions
- **Python Scripts**: Direct execution for system operations and API integration
- **Shell Scripts**: System-level automation and workflow orchestration

## Command Development Guidelines

**For Markdown Commands**:
- Must be executable instructions, not documentation
- Include clear parameter specifications and usage examples
- Provide error handling and validation logic
- Support composition with other commands

**For Python/Shell Scripts**:
- Follow security best practices (no shell injection)
- Include comprehensive error handling
- Maintain compatibility with CI/CD environments
- Provide logging and debugging capabilities

## Usage Patterns

```bash

# Cognitive Commands (natural language processing):

/think [analysis topic]
/debug [issue description]
/plan [task description]

# Operational Commands (system operations):

/execute [task to perform]
/orch [task for orchestration]
/push [commit and push changes]

# Specialized Workflows:

/cerebras [code generation task]
/reviewe [enhanced code review]
/fake3 [fake code detection]
```

## Module Context

**Purpose**: Provides comprehensive command system for Claude Code operations including task execution, orchestration, code quality, and development workflow automation
**Role**: Command interface layer enabling natural language interaction with development tools, CI/CD systems, and multi-agent orchestration
**Parent Project**: WorldArchitect.AI - AI-powered tabletop RPG platform

## Quick Reference

- **Complete Protocols**: See [../../CLAUDE.md](../../CLAUDE.md)
- **Command Types**: Cognitive (analysis) vs Operational (execution)
- **Usage**: Commands execute via `/commandname [arguments]` syntax
- **Documentation**: Individual .md files contain executable specifications
- **Testing**: Run `../../run_tests.sh` for command system validation
