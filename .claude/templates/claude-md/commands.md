# CLAUDE.md - Claude Command System

**Primary Rules**: Inherits from [{{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md]({{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md) (complete project protocols)

**Module Type**: Command System & Automation ({{COMMAND_TECHNOLOGY_STACK}})

## 🚨 MODULE-SPECIFIC PROTOCOLS
- All commands must be executable prompt templates, not documentation
- Commands execute via Claude reading `.md` files and implementing functionality
- Python/shell scripts provide direct tool execution capabilities
- Command documentation must include usage examples and parameter specifications

## Directory Contents Analysis
**Core Command Files** ({{COMMAND_COUNT}}+ .md files):
{{COMMAND_CATEGORIES}}

**Specialized Command Categories**:
{{SPECIALIZED_COMMANDS}}

**Python Automation Scripts** ({{SCRIPT_COUNT}} .py files):
{{PYTHON_SCRIPTS}}

**Shell Scripts & Utilities** ({{SHELL_COUNT}} .sh files):
{{SHELL_SCRIPTS}}

**Support Modules**:
{{SUPPORT_MODULES}}

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
{{SPECIALIZED_USAGE}}
```

## Module Context
**Purpose**: Provides comprehensive command system for Claude Code operations including {{COMMAND_SCOPE}}
**Role**: Command interface layer enabling natural language interaction with development tools, CI/CD systems, and multi-agent orchestration
**Parent Project**: {{PARENT_PROJECT}}

## Quick Reference
- **Complete Protocols**: See [{{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md]({{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md)
- **Command Types**: Cognitive (analysis) vs Operational (execution)
- **Usage**: Commands execute via `/commandname [arguments]` syntax
- **Documentation**: Individual .md files contain executable specifications
- **Testing**: Run `tests/run_tests.sh` for command system validation