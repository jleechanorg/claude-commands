# Claude Commands

Command composition system for Claude AI using natural language processing to combine slash commands.

## Problem Statement

Claude AI lacks native command composition. Users cannot combine multiple slash commands like `/think /debug /optimize` in a single invocation. Each command must be executed individually, losing context and requiring manual coordination between different analytical approaches.

## Solution: Command Composition

This system enables arbitrary command combination through meta-prompt generation. Instead of modifying Claude's underlying architecture, it preprocesses combined commands into natural language instructions that Claude can interpret natively.

### Technical Approach

**Command Parsing**: Regular expressions extract slash commands from user input
**Behavior Mapping**: Known commands map to documented behaviors, unknown commands default to "approach" patterns
**Meta-Prompt Generation**: System constructs natural language instructions combining all specified behaviors
**Context Preservation**: Original task context flows through to the combined execution

### Value Proposition

1. **Cognitive Multiplication**: Combine different thinking approaches (analytical + creative + systematic)
2. **Workflow Integration**: Chain related operations without losing context between steps  
3. **Emergent Behaviors**: Command combinations produce capabilities not available individually
4. **Extensibility**: New combinations work without hardcoded definitions

### Example Transformations

```bash
# Single command limitation
/think analyze performance → Sequential thinking only
/debug analyze performance → Debugging methodology only

# Composition capability  
/think /debug analyze performance → Sequential thinking + systematic debugging + analysis
```

**Generated Meta-Prompt**:
```
Use sequential thinking methodology for systematic debugging approach: analyze performance
```

Claude processes this as natural language instructions, accessing both thinking patterns simultaneously.

## Core Commands

### Cognitive
- **`/think [level]`** - Sequential thinking (light/medium/deep/ultra depth levels)
- **`/arch`** - Architecture analysis and design patterns
- **`/debug`** - Systematic debugging methodology with evidence collection

### Operational
- **`/orchestrate`** - Multi-agent task delegation *(WIP - requires Redis/tmux)*
- **`/execute`** - Task execution with safety checks and approval gates
- **`/plan`** - Strategic planning with structured decomposition

### Analysis
- **`/fake`** - Placeholder/demo code detection across codebases
- **`/learn`** - Learning capture with Memory MCP integration
- **`/test`** - Testing automation (UI/HTTP/integration workflows)

### Communication
- **`/commentreply`** - Intelligent GitHub PR comment generation
- **`/copilot`** - Automated PR analysis and issue resolution

### Meta
- **`/combinations`** - Command composition engine documentation and examples

## Composition Examples

### Analytical Depth
```bash
/think deep /arch /security → Deep architectural thinking with security analysis
```
Produces comprehensive security-focused architectural analysis using extended thinking methodology.

### Problem Solving
```bash
/debug /test /learn → Systematic debugging + testing validation + learning capture
```
Combines debugging methodology with test-driven validation and automatic learning documentation.

### Creative Technical
```bash
/arch /optimize /unconventional → Architecture analysis + optimization + creative approaches
```
Standard architectural analysis enhanced with optimization focus and non-conventional thinking patterns.

## Implementation Details

**Command Processing**: Markdown files contain command specifications with behavior descriptions. Hook scripts parse input and generate meta-prompts.

**Composition Algorithm**:
1. Parse slash commands using regex: `/(\w+)/g`
2. Map known commands to behavior descriptions from markdown files
3. Handle unknown commands with generic "approach" pattern
4. Concatenate behaviors with natural language connectors
5. Append original task context
6. Execute through existing command infrastructure

**Extensibility**: New commands work immediately through pattern matching. No system updates required for novel combinations.

## Architecture

```
claude/commands/           # Command specifications (markdown)
├── cognitive/            # Analysis and thinking commands
├── operational/          # Task execution commands  
├── quality/             # Code analysis and validation
├── communication/       # PR and comment management
└── meta/                # System and composition commands

.claude/hooks/            # Preprocessing hooks
├── compose-commands.sh   # Main composition engine
└── command-parser.py     # Command extraction logic

orchestration/           # Multi-agent system (WIP)
├── task_dispatcher.py  # Agent routing and load balancing
├── message_broker.py   # Redis-based coordination
└── agent_system.py     # tmux session management
```

## Dependencies

**Core System**: None (pure prompt engineering approach)
**Orchestration**: Redis 6.0+, tmux, Python 3.8+
**Optional Integrations**: Memory MCP, GitHub API, various testing frameworks

## Usage

1. Clone repository and reference command specifications
2. Configure hooks in Claude environment  
3. Use arbitrary command combinations:
   ```
   /think ultra /arch /security Analyze microservices for vulnerabilities
   /debug /test /optimize Find and fix performance bottlenecks
   /plan /execute /learn Implement feature with learning capture
   ```

**Orchestration Setup** *(WIP)*:
```bash
redis-server                              # Start coordination backend
./orchestration/start_system.sh start    # Initialize agent system
/orchestrate implement authentication     # Delegate to specialized agents
```

## Technical Limitations

- Requires preprocessing integration with Claude interface
- Meta-prompt quality depends on command specification completeness
- No runtime validation of command compatibility
- Orchestration system requires external infrastructure
- Performance scales with number of combined commands

## Status

- **Command System**: Production ready, 50+ commands available
- **Composition Engine**: Stable, handles arbitrary combinations
- **Orchestration**: Experimental, requires Redis/tmux infrastructure