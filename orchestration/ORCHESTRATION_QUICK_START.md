# Orchestration Quick Start

## Problem Solved
Previously, spawning an agent took 5+ minutes of manual steps. Now it takes <30 seconds with a single command.

## Quick Usage

### Method 1: Direct Orchestration (Recommended)
```bash
./scripts/orchestration/orch_direct.sh "Your task description here"
```

### Method 2: Quick Agent Spawner
```bash
./scripts/orchestration/quick_agent.sh "Your task description here"
```

## Examples

```bash
# Fix code issues
./scripts/orchestration/orch_direct.sh "Find and fix inline imports"

# Run tests
./scripts/orchestration/quick_agent.sh "Run all tests and fix failures"

# Frontend tasks
./scripts/orchestration/quick_agent.sh "Update CSS for dark mode"
```

## Monitoring Agents

```bash
# List all agents
tmux ls | grep agent

# Attach to specific agent
tmux attach -t task-direct-5756

# View agent output without attaching
tmux capture-pane -t task-direct-5756 -p | tail -50
```

## Key Improvements

1. **Single Command**: No more navigating directories or setting environment
2. **Proper Token Limits**: Automatically sets CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192
3. **Auto Agent Type**: Detects backend/frontend/testing based on task
4. **Works from Worktrees**: No need to cd to parent directory
5. **Immediate Feedback**: Shows agent session name for monitoring

## Technical Details

- `scripts/orchestration/orch_direct.sh`: Bypasses start_claude_agent.sh, calls claude directly
- `scripts/orchestration/quick_agent.sh`: Quick agent spawner with standard instructions
- Both create tmux sessions for easy monitoring
- Agents run with correct token limits from ~/.bashrc

## Troubleshooting

If agent fails with token error:
- Check ~/.bashrc has: `export CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192`
- Use scripts/orchestration/orch_direct.sh which explicitly sets the correct value

Agent not starting:
- Check tmux is installed: `which tmux`
- Verify Claude CLI is accessible: `which claude`