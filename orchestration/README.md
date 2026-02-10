# Orchestration Library (`jleechanorg-orchestration`)

Python package and CLI for task-driven agent orchestration.

## Table of Contents

- [Install from PyPI](#install-from-pypi)
- [Verify Install and Version](#verify-install-and-version)
- [CLI Entry Points](#cli-entry-points)
- [Primary Usage: Task Dispatching](#primary-usage-task-dispatching)
- [Task Dispatcher Python Interface](#task-dispatcher-python-interface)
- [Legacy Interactive Mode (`live`)](#legacy-interactive-mode-live)
- [Design Summary](#design-summary)
- [Tech Stack (Summary)](#tech-stack-summary)
- [Local Development (Package Source)](#local-development-package-source)

## Install from PyPI

```bash
python3 -m pip install jleechanorg-orchestration
```

Upgrade:

```bash
python3 -m pip install --upgrade jleechanorg-orchestration
```

Install a specific version:

```bash
python3 -m pip install "jleechanorg-orchestration==0.1.40"  # omit version for latest
```

## Verify Install and Version

```bash
python3 -m pip show jleechanorg-orchestration
ai_orch --version
```

## CLI Entry Points

Console scripts installed by the package:

- `ai_orch`
- `orch` (alias)

Both map to `orchestration.live_mode:main`.

## Primary Usage: Task Dispatching

### 1. Unified orchestration (`run`)

```bash
ai_orch run --agent-cli gemini,claude "Fix flaky integration tests and open/update PR"
```

Shorthand (defaults to `run`):

```bash
ai_orch --agent-cli claude "Implement task dispatcher retry metrics"
```

Useful flags:

- `--agent-cli`: force CLI or fallback chain (`claude`, `codex`, `gemini`, `cursor`)
- `--context`: inject markdown context file
- `--branch`: force branch checkout
- `--pr`: update an existing PR
- `--no-new-pr`, `--no-new-branch`: hard guardrails
- `--validate`: post-run validation command
- `--model`: model override for supported CLIs

### 2. Task Dispatcher Interface

Analyze task only:

```bash
ai_orch dispatcher analyze --agent-cli codex --json "Refactor auth middleware"
```

Create agents from task:

```bash
ai_orch dispatcher create --agent-cli gemini --model gemini-3-flash-preview "Fix PR #123 review blockers"
```

Dry-run planned agent specs:

```bash
ai_orch dispatcher create --agent-cli claude --dry-run "Investigate failing CI"
```

## Task Dispatcher Python Interface

```python
from orchestration.task_dispatcher import TaskDispatcher

dispatcher = TaskDispatcher()

agent_specs = dispatcher.analyze_task_and_create_agents(
    "Fix failing tests in PR #123 and push updates",
    forced_cli="claude",
)

for spec in agent_specs:
    ok = dispatcher.create_dynamic_agent(spec)
    print(spec["name"], ok)
```

### Core methods

- `TaskDispatcher.analyze_task_and_create_agents(task_description: str, forced_cli: str | None = None) -> list[dict]`
- `TaskDispatcher.create_dynamic_agent(agent_spec: dict) -> bool`

### Agent spec fields used by `create_dynamic_agent`

- `name`: unique agent/session name
- `task`: full task instructions
- `cli` or `cli_chain`: selected CLI or fallback chain
- `workspace_config` (optional): workspace placement/settings
- `model` (optional): model override

## Legacy Interactive Mode (`live`)

Interactive tmux mode is still available:

```bash
ai_orch live --cli codex
ai_orch list
ai_orch attach <session>
ai_orch kill <session>
```

Use this when you explicitly want a persistent manual CLI session. For automated task execution, prefer `run` or `dispatcher`.

## Design Summary

Full design details live in [`orchestration/design.md`](./design.md).

High-level design:

- Entry point is `ai_orch`/`orch` (mapped to `orchestration.live_mode:main`).
- Default flow is unified `run` mode, which delegates orchestration to `UnifiedOrchestration`.
- `dispatcher` mode exposes task planning and agent creation directly via `TaskDispatcher`.
- Agent execution is isolated via tmux sessions and workspace-specific execution context.
- Coordination uses file-backed A2A/task state under `/tmp` (no Redis dependency).

## Tech Stack (Summary)

- Runtime: Python 3.11+
- Session/process isolation: `tmux`
- VCS/PR operations: `git`, `gh`
- Agent CLIs: `claude`, `codex`, `gemini`, `cursor-agent`
- Coordination: file-backed A2A/task state under `/tmp` (no Redis requirement)

Detailed architecture and implementation docs:

- `orchestration/design.md`
- `orchestration/A2A_DESIGN.md`
- `orchestration/AGENT_SESSION_CONFIG.md`

## Local Development (Package Source)

```bash
cd orchestration
python3 -m pip install -e .
python3 -m pytest tests -q
```

Use editable installs only for local package development.
