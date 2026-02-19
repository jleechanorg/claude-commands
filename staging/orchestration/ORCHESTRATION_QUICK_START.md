# Orchestration Quick Start

## Problem Solved
Previously, spawning an agent took 5+ minutes of manual steps. Now it takes <30 seconds with a single command.

## Quick Usage

### Python Orchestration
```bash
python3 orchestration/orchestrate_unified.py "Your task description here"
```

## Examples

```bash
# Fix code issues
python3 orchestration/orchestrate_unified.py "Find and fix inline imports"

# Run tests
python3 orchestration/orchestrate_unified.py "Run all tests and fix failures"

# Frontend tasks
python3 orchestration/orchestrate_unified.py "Update CSS for dark mode"
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

- `orchestration/orchestrate_unified.py`: Python orchestration system with agent creation
- Creates tmux sessions for easy monitoring
- Agents run with correct token limits from ~/.bashrc

## Troubleshooting

If agent fails with token error:
- Check ~/.bashrc has: `export CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192`
- The orchestration system sets the correct value

Agent not starting:
- Check tmux is installed: `which tmux`
- Verify Claude CLI is accessible: `which claude`
