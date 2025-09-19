# Slash Commands Documentation

This document provides comprehensive documentation for all available slash commands in the WorldArchitect.AI project.

## Available Commands

### Performance Optimization

⚡ **TIMEOUT COMMAND**: Performance optimization for preventing API timeouts
- ✅ **Purpose**: Reduce CLI timeout rate from 10% to <2% through automatic optimizations
- ✅ **Three Modes**: `/timeout` (standard), `/timeout strict`, `/timeout emergency`
- ✅ **Automatic Optimizations**: Tool batching, response limits, thinking constraints, file operation limits
- ✅ **Performance Impact**: -40-60% response time, -50-70% token usage
- ✅ **Disable**: `/timeout off` to turn off all optimizations
- ✅ **Status**: `/timeout status` to check current mode
- ✅ **Chainable**: `/timeout /execute large-task`, `/timeout strict /debug complex-issue`
- 🔍 **Implementation**: Modifies behavior for entire session until disabled

### Command Execution

**Key Commands**: `/execute` (no approval) | `/plan` (requires approval) | `/replicate` (PR analysis)
**Universal Composition**: ANY combination works via Claude's NLP
**Unified Learning**: ONE `/learn` command with Memory MCP integration
**Memory Enhancement**: Commands `/think`, `/learn`, `/debug`, `/analyze`, `/fix`, `/plan`, `/execute`, `/arch`, `/test`, `/pr`, `/perp`, `/research` automatically integrate memory context (see CLAUDE.md)

## Command Architecture

Commands are implemented in the `.claude/commands/` directory with both markdown documentation and Python implementation files where applicable.

### Documentation Standards

All slash commands must be documented in:
1. Individual command files in `.claude/commands/`
2. This `slash_commands.md` file
3. `CLAUDE.md` main protocol file

### Universal Command Composition

The system supports arbitrary command combinations using Claude's natural language processing capabilities, allowing for creative and contextual command interpretation.

## Slash Commands

### `/cerebras`

**Description**: Generate large amounts of code using Cerebras API for high-speed, high-quality code generation.

**Usage Syntax**: 
- `/cerebras [task description]`
- `/c [task description]` (short alias)
- `/qwen [task description]` (legacy alias)
- `/cereb [task description]` (alternative alias)

**Parameters**:
- `task description` (string): Description of the code generation task to perform

**Examples**:
```bash
/cerebras Create a React component for user authentication
/c Implement a REST API for user management
/cerebras Generate unit tests for the calculateTotal function
```

**Safety Notes**:
- Tasks >10 delta lines should preferentially use Cerebras per CLAUDE.md protocols
- Cerebras provides 19.6x faster code generation compared to Claude
- Best suited for well-defined code generation tasks, templates, and algorithms
- Review generated code before integration into production systems

### `/header`

**Description**: Generate and display the mandatory branch header for CLAUDE.md compliance with full git status and intelligent PR inference.

**Usage Syntax**:
- `/header`
- `/usage` (alias)

**Parameters**: None (automatic detection)

**Examples**:
```bash
/header
# Output: [Local: feature-branch | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]

/usage  
# Same output with additional API usage statistics
```

**Safety Notes**:
- Required by CLAUDE.md protocols - must be included at end of every response
- Automatically detects current branch, upstream, and associated PR
- Includes Claude API usage statistics (remaining sessions out of 50)
- Fallback mechanisms for missing git configuration or network issues

### `/deploy`

**Description**: Execute the repository's `deploy.sh` workflow regardless of whether the script lives in the project root or the `scripts/` directory.

**Usage Syntax**:
- `/deploy`
- `/deploy staging`
- `/deploy stable`

**Implementation Notes**:
- Uses `./claude_command_scripts/commands/deploy.sh` to locate and run `deploy.sh`
- Forwards all arguments directly to the underlying deploy script
- Prints the resolved script path for transparency before execution
- Exits with a clear error if `deploy.sh` cannot be found in expected locations

For detailed command specifications, see the individual command files in `.claude/commands/`.
