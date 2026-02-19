---
description: Launch dual-agent pair programming with coder + verifier
argument-hint: '"task description"'
type: llm-orchestration
execution_mode: llm-driven
---

---

# /pair - Dual-Agent Pair Programming

**⚠️ MANDATORY: NEVER implement the task yourself. Launch TWO agents.**

## Logging Convention

All pair agents MUST write timestamped logs throughout their session:

**Log directory:** `/tmp/{repo_name}/{branch}/pair_logs/`

Example: `/tmp/worktree_pair2/pair_followup/pair_logs/`

| Agent | Log file | Contents |
|-------|----------|----------|
| Coder | `coder.log` | Task start, RED phase (tests written), GREEN phase (impl done), test results, IMPLEMENTATION_READY sent |
| Verifier | `verifier.log` | Waiting start, IMPLEMENTATION_READY received, checks run (tests, lint, review), verdict, messages sent |

**Format:** `[YYYY-MM-DD HH:MM:SS] [PHASE] message`

The leader MUST include the log directory path in the prompt when spawning agents. Agents create the directory if it doesn't exist. This provides a persistent audit trail for debugging pair sessions.

## Default: Claude Teams (Recommended)

When `/pair` is invoked, use Claude Teams to spawn a coder and a verifier:

### Step 1: Create the team

```
Teammate({
  operation: "spawnTeam",
  team_name: "pair-<short-task-slug>",
  description: "Pair programming: <task>"
})
```

### Step 2: Create tasks

Create two tasks:
1. **Implementation task** - The actual work (assigned to coder)
2. **Verification task** - Review and test the work (assigned to verifier, blocked by task 1)

### Step 3: Spawn coder agent

```
Task({
  subagent_type: "pair-coder",
  team_name: "<team-name>",
  name: "coder",
  prompt: "<task description with full context>",
  mode: "bypassPermissions"
})
```

### Step 4: Spawn verifier agent (Codex-powered by default)

```
Task({
  subagent_type: "codex-pair-verifier",
  team_name: "<team-name>",
  name: "verifier",
  prompt: "Wait for coder's IMPLEMENTATION_READY message, then verify the implementation.",
  mode: "bypassPermissions"
})
```

> Uses Codex CLI (`codex exec --yolo`) for independent verification, falls back to Claude if Codex is unavailable. To use Claude-only verifier instead, use `subagent_type: "pair-verifier"`.

### CLI-Specific Agents

To use a specific CLI for coder or verifier, swap the `subagent_type`:

| CLI | Coder subagent_type | Verifier subagent_type |
|-----|---------------------|----------------------|
| Claude (native) | `pair-coder` | `pair-verifier` |
| Claude (CLI) | `claude-pair-coder` | `claude-pair-verifier` |
| Codex | `codex-pair-coder` | `codex-pair-verifier` |
| Gemini | `gemini-pair-coder` | `gemini-pair-verifier` |
| Cursor | `cursor-pair-coder` | `cursor-pair-verifier` |
| MiniMax | `minimax-pair-coder` | `minimax-pair-verifier` |

CLI-specific agents delegate work to the external CLI binary (commands from `orchestration/task_dispatcher.py` CLI_PROFILES). If the CLI is unavailable, they fall back to native Claude Code tools.

Example: Cross-CLI pair (Gemini coder + Codex verifier):
```
Task({ subagent_type: "gemini-pair-coder", ... })
Task({ subagent_type: "codex-pair-verifier", ... })
```

### Step 5: Coordinate

- Assign tasks to agents via TaskUpdate
- Wait for both to complete
- Report results to user
- Shut down teammates and clean up team

## Script Mode (Only When Explicitly Requested)

Use `pair_execute.py` ONLY when the user explicitly asks for:
- Multi-CLI sessions (e.g., `--coder-cli minimax --verifier-cli codex`)
- tmux-based observability (`tmux attach` to watch agents)
- Background monitoring with pair_monitor.py

```bash
python3 .claude/scripts/pair_execute.py --no-worktree "Your task description here"
```

### Script Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `task` | (required) | Task description in quotes |
| `--coder-cli` | claude | CLI for coder (claude/codex/gemini/cursor/minimax) |
| `--verifier-cli` | codex | CLI for verifier |
| `--claude-provider` | (none) | Override claude-family backend |
| `--no-worktree` | false | Run in current directory |
| `--max-iterations` | 60 | Monitor safety ceiling (60 x 60s = 1h max) |
| `--interval` | 60 | Monitor check interval (seconds) |

## Success Criteria

Session completes when:
- ✅ Coder completes implementation with tests passing
- ✅ Verifier independently verifies code quality and test coverage
- ✅ Both agents agree work is done (VERIFICATION_COMPLETE)

## Troubleshooting

**Claude Teams mode:**
- Check TaskList for stuck tasks
- Send messages to agents via SendMessage
- Shut down via shutdown_request if stuck

**Script mode:**
```bash
tmux ls | grep pair          # Check agent sessions
tmux kill-session -t <name>  # Kill stuck session
```

**Protocol Version:** 5.0 (Claude Teams default)
