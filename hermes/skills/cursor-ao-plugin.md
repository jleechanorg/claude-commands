# Cursor Agent Plugin Integration

Agent Orchestrator (AO) supports `cursor-agent` as an agent plugin, enabling Cursor's AI coding assistant to be used as an orchestrated agent within AO workflows.

## Plugin Overview

The `agent-cursor` plugin (`@composio/ao-plugin-agent-cursor`) provides:

- **Process management**: Launches `cursor-agent` processes via tmux or direct process execution
- **Activity detection**: Monitors terminal output to determine if the agent is active, idle, or waiting for input
- **Session introspection**: Reads Cursor's JSONL session files to extract summaries, costs, and token usage
- **Session resumption**: Supports resuming previous Cursor sessions via `--resume` flag
- **Metadata hooks**: Automatically tracks PR creation and branch switches in session metadata

## Using cursor-agent with ao spawn

To spawn a Cursor agent instead of Claude Code:

```bash
# Spawn with cursor-agent as the agent type
ao spawn <project> --agent cursor

# With custom model
ao spawn <project> --agent cursor --model claude-opus-4-6

# Resume a specific session
ao spawn <project> --agent cursor --resume <session-id>
```

## Project Configuration

Add a cursor-based project to `~/.hermes/agent-orchestrator.yaml`:

```yaml
projects:
  my-project-cursor:
    name: my-project (Cursor)
    repo: owner/my-repo
    path: ~/projects/my-repo
    defaultBranch: main
    sessionPrefix: mc
    workspace: worktree
    worktreeDir: ~/.worktrees/my-repo-main
    agent: cursor  # Use cursor-agent instead of claude-code

    agentConfig:
      permissions: skip   # --dangerously-skip-permissions
      model: claude-sonnet-4-6  # Optional: specify model
```

## Permissions Modes

The plugin maps AO permissions to Cursor CLI flags:

| AO Permission | Cursor Flag |
|---------------|-------------|
| `permissionless` | `--dangerously-skip-permissions` |
| `auto-edit` | `--dangerously-skip-permissions` |
| `default` | (no flag) |
| `skip` (legacy) | `--dangerously-skip-permissions` |

## Activity States

The plugin detects these activity states from terminal output:

- **active**: Agent is processing, waiting for output, or showing content
- **idle**: Shell prompt visible (`>`, `$`, `❯`)
- **waiting_input**: Permission prompts or user input required
- **blocked**: Error state detected
- **exited**: Process no longer running

## Session Metadata Hooks

When enabled, the plugin automatically updates session metadata:

- **PR creation**: Detects `gh pr create` and records PR URL
- **Branch switches**: Tracks `git checkout -b` / `git switch -c`
- **PR merges**: Updates status to `merged` on `gh pr merge`

This works via a `.cursor/metadata-updater.sh` hook script in the workspace. This file is not provided by this repo — create it in your Cursor project directory to enable metadata tracking (similar to the `.claude/metadata-updater.sh` hook used by Claude Code).

## Environment Variables

The plugin sets these environment variables for spawned agents:

- `CLAUDECODE=""` - Set to empty string to prevent nested agent conflicts
- `AO_SESSION_ID` - Current session ID for introspection
- `AO_ISSUE_ID` - Issue ID if provided in launch config

## Requirements

- `cursor-agent` CLI installed and in PATH
- For session introspection: access to `~/.cursor/projects/` directory
- For tmux runtime: tmux installed
