# Orch Command (Alias for Orchestrate)

**Purpose**: Multi-agent orchestration system for complex development tasks (short alias)

**Action**: Coordinate multiple specialized agents to work on complex development tasks with proper task distribution and result integration

**Usage**: `/orch [task_description]` (alias for `/orchestrate`)

**Implementation**: 
- **Python Script**: `python3 .claude/commands/orchestrate.py [task_description]`
- **Shell Wrapper**: `./claude_command_scripts/orch.sh` (if available)
- **Direct Execution**: Uses real Claude Code CLI agents in separate tmux sessions

**Features**:
- **Real tmux sessions**: Creates separate terminal sessions for each agent
- **Claude Code CLI integration**: Full access to all slash commands in each session
- **Task delegation**: Smart routing based on task content (UI→frontend, API→backend, etc.)
- **Progress monitoring**: Real-time status via `/orch What's the status?`
- **Agent collaboration**: Direct connection to agent sessions for collaboration
- **Natural language**: Understands commands like "Build user authentication urgently"

**System Requirements**:
- Redis server running (for coordination)
- Orchestration system started: `./orchestration/start_system.sh start`
- Or started via: `./claude_start.sh`

**Examples**:
- `/orch implement user authentication with tests and documentation`
- `/orch refactor database layer with migration scripts`
- `/orch add new feature with full test coverage and UI updates`
- `/orch What's the status?`
- `/orch connect to sonnet 1`
- `/orch monitor agents`

**Agent Types**:
- **Frontend Agent**: UI, React components, styling (`frontend-agent`)
- **Backend Agent**: APIs, database, server logic (`backend-agent`) 
- **Testing Agent**: Tests, QA, validation (`testing-agent`)
- **Opus Master**: Coordination and oversight (`opus-master`)

**Quick Commands**:
- **Start system**: `./orchestration/start_system.sh start`
- **Check status**: `/orch What's the status?`
- **Connect to frontend**: `tmux attach -t frontend-agent`
- **Connect to backend**: `tmux attach -t backend-agent`
- **Connect to testing**: `tmux attach -t testing-agent`
- **Monitor all**: `tmux list-sessions | grep -E '(frontend|backend|testing|opus)'`