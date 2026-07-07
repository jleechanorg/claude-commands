# Gemini Agent Plugin Integration

Agent Orchestrator (AO) supports `gemini` as an agent plugin, enabling Google's Gemini CLI to be used as an orchestrated agent within AO workflows.

## Plugin Overview

The `agent-gemini` plugin provides:

- **Process management**: Launches `gemini` CLI processes via tmux or direct process execution
- **Activity detection**: Monitors terminal output to determine if the agent is active, idle, or waiting for input
- **Session introspection**: Reads Gemini CLI output to extract summaries and completion state
- **Model selection**: Supports all Gemini models via `--model` flag (defaults to `gemini-2.5-pro-preview`)
- **Yolo mode**: Runs non-interactively with `--yolo` for autonomous task execution

## Using gemini with ao spawn

To spawn a Gemini agent instead of Claude Code:

```bash
# Spawn with gemini as the agent type
ao spawn <project> --agent gemini

# With specific model
ao spawn <project> --agent gemini --model gemini-2.5-pro-preview

# Fast flash model for lighter tasks
ao spawn <project> --agent gemini --model gemini-2.5-flash-preview
```

## CLI Invocation

The plugin invokes Gemini CLI as:

```bash
gemini -m ${GEMINI_MODEL:-gemini-2.5-pro-preview} --yolo
```

The `--yolo` flag enables non-interactive autonomous execution — equivalent to `--dangerously-skip-permissions` in Claude Code.

## Project Configuration

Add a Gemini-based project to `~/.hermes/agent-orchestrator.yaml`:

```yaml
projects:
  my-project-gemini:
    name: my-project (Gemini)
    repo: owner/my-repo
    path: ~/projects/my-repo
    defaultBranch: main
    sessionPrefix: mg
    workspace: worktree
    worktreeDir: ~/.worktrees/my-repo-main
    agent: gemini  # Use gemini CLI instead of claude-code

    agentConfig:
      permissions: skip   # maps to --yolo
      model: gemini-2.5-pro-preview  # Optional: override default model
```

## Permissions Modes

| AO Permission | Gemini Flag |
|---------------|-------------|
| `permissionless` | `--yolo` |
| `auto-edit` | `--yolo` |
| `default` | (no flag — interactive) |
| `skip` (legacy) | `--yolo` |

## Activity States

The plugin detects these activity states from terminal output:

- **active**: Agent is processing or generating output
- **idle**: Shell prompt visible (`>`, `$`, `❯`)
- **waiting_input**: Permission prompts or user confirmation required
- **blocked**: Error state detected
- **exited**: Process no longer running

## When to Use Gemini vs Cursor vs Codex

| Agent | Best for |
|-------|----------|
| `gemini` | Large context tasks (1M token window), multimodal, Google ecosystem |
| `cursor` | IDE-integrated edits, Cursor-native workflows |
| `codex` | OpenAI Codex OAuth, GPT-model tasks |
| `claude` | Default; best general-purpose coding and reasoning |

Use Gemini when tasks require very large context windows or when you want a second opinion from a different model family.

## Environment Variables

- `GEMINI_MODEL` — override the default model (e.g. `gemini-2.5-flash-preview` for speed)
- `GEMINI_API_KEY` — required if not authenticated via `gemini auth`

## Requirements

- `gemini` CLI installed: `npm install -g @google/gemini-cli` or via Homebrew
- Authenticated: `gemini auth` (Google account OAuth)
- For tmux runtime: tmux installed
