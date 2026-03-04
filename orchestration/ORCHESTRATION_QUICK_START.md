# Orchestration Quick Start

## Problem Solved

Previously, spawning an agent took 5+ minutes of manual steps. Now it takes <30 seconds with a single command.

## Quick Usage

### ai_orch (recommended)

```bash
# Passthrough: run directly, stream output
ai_orch "Your task description here"

# Async: detached tmux, return immediately
ai_orch --async "Find and fix inline imports"
```

## Examples

```bash
# Fix code issues
ai_orch "Find and fix inline imports"

# Run tests
ai_orch "Run all tests and fix failures"

# Frontend tasks
ai_orch "Update CSS for dark mode"

# Use codex
ai_orch --agent-cli codex "Implement feature X"

# Async with worktree
ai_orch --async --worktree "refactor auth module"
```

## Monitoring Agents

```bash
# List tmux sessions
tmux ls | grep ai-

# Attach to specific session (session name printed when started)
tmux attach -t ai-claude-abc123

# View agent output without attaching
tmux capture-pane -t ai-claude-abc123 -p | tail -50
```

## Key Improvements

1. **Single Command**: No more navigating directories or setting environment
2. **Passthrough by default**: Direct CLI invocation, stream output
3. **Opt-in async**: `--async` for detached tmux when needed
4. **Resume support**: `--async --resume` reuses existing session for same directory
5. **Immediate Feedback**: Shows session name for monitoring

## Technical Details

- `ai_orch` entry point: `orchestration.runner:main`
- Passthrough: invokes claude/codex/gemini directly
- Async: creates tmux session under `~/.ai_orch_sessions.json` for resume

## Troubleshooting

Agent not starting:
- Check tmux is installed: `which tmux`
- Verify CLI is accessible: `which claude` or `which codex`

MiniMax auth:
- Set `MINIMAX_API_KEY` in env or `~/.bashrc` or `~/.automation_env`
