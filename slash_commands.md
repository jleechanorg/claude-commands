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

For detailed command specifications, see the individual command files in `.claude/commands/`.
