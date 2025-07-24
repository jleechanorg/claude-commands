# Claude Commands

Command composition system for Claude AI using natural language processing to combine slash commands.

## Command Composition

The system parses arbitrary command combinations and generates meta-prompts for Claude interpretation:

```bash
/think /debug /optimize     # Sequential thinking + debugging + optimization
/arch /security /deploy     # Architecture analysis + security + deployment  
/custom /nonexistent /test  # Handles undefined commands via approach patterns
```

Implementation uses simple string parsing and prompt templating rather than hardcoded command mappings.

## Core Commands

### Cognitive
- **`/think [level]`** - Sequential thinking (light/medium/deep/ultra depth levels)
- **`/arch`** - Architecture analysis
- **`/debug`** - Systematic debugging methodology

### Operational
- **`/orchestrate`** - Multi-agent task delegation *(WIP - requires Redis/tmux)*
- **`/execute`** - Task execution with approval gates
- **`/plan`** - Planning workflows

### Analysis
- **`/fake`** - Placeholder/demo code detection
- **`/learn`** - Learning capture with Memory MCP
- **`/test`** - Testing automation (UI/HTTP/integration)

### Meta
- **`/combinations`** - Command composition engine documentation

## Implementation

**Command Processing**: Markdown files contain command specifications. Hook scripts parse combinations and generate natural language instructions.

**Composition Algorithm**:
1. Parse slash commands from input
2. Map known commands to behaviors, unknown to "approach" patterns  
3. Generate meta-prompt combining all behaviors
4. Execute via existing command infrastructure

**Example Transformation**:
```
Input:  /think /debug analyze memory leak
Output: Use sequential thinking for systematic debugging: analyze memory leak
```

## Architecture

```
claude/commands/           # Command specifications (markdown)
├── cognitive/            # Analysis and thinking commands
├── operational/          # Task execution commands  
├── quality/             # Code analysis commands
└── meta/                # System and composition commands

orchestration/           # Multi-agent system (WIP)
├── task_dispatcher.py  # Agent routing
├── message_broker.py   # Redis coordination
└── agent_system.py     # tmux session management
```

## Dependencies

**Core System**: None (pure prompt engineering)
**Orchestration**: Redis, tmux, Python 3.8+
**Integrations**: Memory MCP, GitHub API (optional)

## Usage

1. Clone repository
2. Reference command files in `claude/commands/*.md`  
3. Use combinations in Claude interface:
   ```
   /think deep /arch What's the optimal database design?
   /debug /test /learn Why are integration tests failing?
   ```

**Orchestration Setup** *(WIP)*:
```bash
# Start Redis
redis-server

# Initialize orchestration
./orchestration/start_system.sh start

# Use orchestration
/orchestrate implement user authentication
```

## Technical Notes

- Commands are markdown specifications, not executable code
- Composition works through prompt engineering, not program logic
- Unknown commands default to generic "approach" interpretation
- System designed for Claude AI but adaptable to other LLMs
- Orchestration requires external infrastructure (Redis, tmux)

## Status

- **Command System**: Production ready
- **Composition Engine**: Stable  
- **Orchestration**: Work in progress, experimental