# Orchestrate Command

**Purpose**: Multi-agent orchestration system for complex development tasks

**Action**: Coordinate multiple specialized agents to work on complex development tasks with proper task distribution and result integration

**Usage**: `/orchestrate [task_description]`

**CRITICAL RULE**: When `/orchestrate` is used, NEVER execute the task yourself. ALWAYS delegate to the orchestration agents. The orchestration system will handle all task execution through specialized agents.

**Implementation**: 
- **Python Script**: `python3 .claude/commands/orchestrate.py [task_description]`
- **Shell Wrapper**: `./claude_command_scripts/orchestrate.sh` (if available)
- **Direct Execution**: Uses real Claude Code CLI agents in separate tmux sessions
- **System Check**: ALWAYS checks system status first before executing tasks

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
- Or started via: `./claude_start.sh` (auto-starts orchestration when not running git hooks)

**Automatic Behavior**:
- `/orch` commands automatically check if the orchestration system is running
- If not running, attempts to start it before executing the task
- Shows clear status messages about system state
- **Memory Integration**: Automatically queries Memory MCP for:
  - Past mistakes and learnings related to the task
  - Previous similar orchestration patterns
  - Known issues and their solutions
  - This helps agents avoid repeating past errors
  - **Note**: If Memory MCP is unavailable, tasks proceed without memory context (non-blocking)

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

## Important Notes

- **Working Directory**: The orchestration system creates agent workspaces as subdirectories. Always ensure you're in the main project directory when running orchestration commands, not inside an agent workspace
- **Monitoring**: Use `tmux attach -t [agent-name]` to watch agent progress
- **Results**: Check `/tmp/orchestration_results/` for agent completion status
- **Cleanup**: Run `orchestration/cleanup_agents.sh` to remove completed agent worktrees
- **Branch Context**: Agents inherit from your current branch, so their changes build on your work

## 🚨 AGENT TASK PATIENCE

Agent tasks require TIME - wait for completion before ANY declaration:
- ⚠️ Orchestrate agents work autonomously and may take 5-10+ minutes
- ❌ NEVER declare success OR failure without checking completion status
- ❌ NEVER make declarations based on quick checks (10s, 30s, 60s too soon)
- ✅ ALWAYS check tmux output for "Task completed" message
- ✅ ALWAYS verify PR creation in agent output before declaring results
- 🔍 Evidence: Agent task-agent-5819 succeeded with PR #851 after 270 seconds
- 📋 Proper verification: tmux output → "Task completed" → PR URL → verify PR exists
- ⚠️ Status warnings like "agent may still be working" mean WAIT, don't declare