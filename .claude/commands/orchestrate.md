# Orchestrate Command

**Purpose**: Multi-agent orchestration system for complex development tasks

**Action**: Coordinate multiple specialized agents to work on complex development tasks with proper task distribution and result integration

**Usage**: `/orchestrate [task_description]`

**Implementation**: 
- **Python Script**: `python3 .claude/commands/orchestrate.py [task_description]`
- **Shell Wrapper**: `./claude_command_scripts/orchestrate.sh` (if available)
- **Direct Execution**: Uses real Claude Code CLI agents in separate tmux sessions

**Features**:
- **Real tmux sessions**: Creates separate terminal sessions for each agent
- **Claude Code CLI integration**: Full access to all slash commands in each session
- **Task delegation**: Smart routing based on task content (UI→frontend, API→backend, etc.)
- **Progress monitoring**: Real-time status via `/orchestrate What's the status?`
- **Agent collaboration**: Direct connection to agent sessions for collaboration
- **Natural language**: Understands commands like "Build user authentication urgently"
- **Priority handling**: Recognizes urgent, ASAP, critical keywords

**System Requirements**:
- Redis server running (for coordination)
- Orchestration system started: `./orchestration/start_system.sh start`
- Or started via: `./claude_start.sh`

**Agent Types**:
- **Frontend Agent**: UI, React components, styling (`frontend-agent`)
- **Backend Agent**: APIs, database, server logic (`backend-agent`) 
- **Testing Agent**: Tests, QA, validation (`testing-agent`)
- **Opus Master**: Coordination and oversight (`opus-master`)

**Examples**:
- `/orchestrate implement user authentication with tests and documentation`
- `/orchestrate refactor database layer with migration scripts`
- `/orchestrate add new feature with full test coverage and UI updates`
- `/orchestrate optimize performance across frontend and backend`
- `/orchestrate What's the status?`
- `/orchestrate connect to sonnet 1`
- `/orchestrate monitor agents`
- `/orchestrate help me with connections`

**Natural Language Commands**:
- **Task Delegation**: "Build X", "Create Y", "Implement Z urgently"
- **System Monitoring**: "What's the status?", "monitor agents", "How's the progress?"
- **Agent Connection**: "connect to sonnet 1", "collaborate with sonnet-2"
- **Help**: "help me with connections", "show me connection options"

**Quick Commands**:
- **Start system**: `./orchestration/start_system.sh start`
- **Check status**: `/orchestrate What's the status?`
- **Connect to frontend**: `tmux attach -t frontend-agent`
- **Connect to backend**: `tmux attach -t backend-agent`
- **Connect to testing**: `tmux attach -t testing-agent`
- **Monitor all**: `tmux list-sessions | grep -E '(frontend|backend|testing|opus)'`