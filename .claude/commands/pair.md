---
description: Launch ralph-pair (coder + deterministic verifier)
argument-hint: 'run [max_iterations]'
---

# /pair — Ralph with Deterministic Verification

Runs `ralph-pair.sh`, which is ralph.sh with an added verification step after each coder iteration.

## Claude Code vs Non-CLI Routing

**Important**: This command detects how it's being invoked and routes accordingly:

- **`run` command**: Uses `/loop` for iteration - Claude handles coder + verifier phases in each iteration
- **Other commands** (`status`, etc.): Falls back to `ralph-pair.sh` script for compatibility
- **Non-Claude CLI**: Always falls back to `ralph-pair.sh` script

The detection works by checking for `CLAUDE_SESSION_ID` environment variable (set by Claude Code).

### Routing Table

| Command | From Claude Code | From Other CLI |
|---------|------------------|----------------|
| `run` | `/loop N /e ralph_pair_iteration` | `ralph-pair.sh run` |
| `status` | `ralph-pair.sh status` | `ralph-pair.sh status` |

This allows Claude Code to handle iteration loops natively while preserving all other Ralph-Pair functionality.

## What it does

1. **Coder phase** — same as ralph: pipe PRD + CLAUDE.md to the agent
2. **Verifier phase** — runs `verifyCommand` for every unpassed story
3. Auto-marks stories as `passes: true` when their verifyCommand succeeds
4. When verify story VN passes, also marks paired implement story SN
5. Repeats until ALL stories verified or max iterations reached

## Routing

When `/pair` is invoked, execute:

```bash
# Parse the command
COMMAND="${1:-run}"

# Route based on command and invocation context
if [ -n "${CLAUDE_SESSION_ID:-}" ]; then
    # Claude Code invocation
    case "$COMMAND" in
        run)
            # Use /loop for iteration. Only consume arg 2 when it is numeric.
            case "${2:-}" in
                ''|*[!0-9]*)
                    MAX_ITERATIONS="10"
                    /loop "$MAX_ITERATIONS" /e ralph_pair_iteration "${@:2}"
                    ;;
                *)
                    MAX_ITERATIONS="$2"
                    /loop "$MAX_ITERATIONS" /e ralph_pair_iteration "${@:3}"
                    ;;
            esac
            ;;
        status)
            # Use shell script for other commands
            bash ~/ralph/ralph-pair.sh "$@"
            ;;
        *)
            bash ~/ralph/ralph-pair.sh "$@"
            ;;
    esac
else
    # Non-Claude CLI: use shell script for everything
    bash ~/ralph/ralph-pair.sh "$@"
fi
```

## Usage

```bash
# Default: 10 iterations with claude
bash ralph/ralph-pair.sh run

# Custom: 3 iterations
bash ralph/ralph-pair.sh run 3

# With a different tool
bash ralph/ralph-pair.sh run --tool codex

# Check status
bash ralph/ralph-pair.sh status
bash ralph/ralph-pair.sh status --watch
```

## Claude Code Execution (via /loop)

When invoked from Claude Code, this command uses `/loop` for iteration:

**Default (10 iterations)**:
```bash
/loop 10 /e ralph_pair_iteration
```

Each iteration:
1. Coder phase: Claude implements unpassed stories
2. Verifier phase: Claude runs `verifyCommand` for each unpassed story
3. Auto-marks stories as passed when verification succeeds

## How it differs from ralph.sh

| | ralph.sh | ralph-pair.sh |
|---|---|---|
| Completion check | Trusts `<promise>COMPLETE</promise>` | Runs verifyCommand per story |
| Verification | None | Deterministic (pytest, etc.) |
| Auto-marking | Coder must update prd_state.json | Verifier auto-marks on pass |
