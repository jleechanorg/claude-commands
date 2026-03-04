# Ralph — PRD-Driven Autonomous Workflow Toolkit

Self-contained toolkit for running iterative AI-driven development tasks from a PRD (Product Requirements Document). Ralph loops through user stories, runs an AI agent (`claude`, `codex`, or `amp`) to implement each one, and tracks progress.

## Quick Start

```bash
# From repo root
./ralph/ralph.sh run --tool claude 20    # Run with Claude Code CLI
./ralph/ralph.sh run --tool minimax 20   # Run Claude via MiniMax (requires MINIMAX_API_KEY)
./ralph/ralph.sh run --tool codex 20     # Run with Codex CLI (codex exec --full-auto)
./ralph/ralph.sh run --tool amp 20       # Run with Amp CLI
./ralph/ralph.sh status --watch         # Monitor progress
./ralph/ralph.sh dashboard --open       # Web dashboard on 127.0.0.1:9450 (local only)

# Shorthand (backwards compatible)
./ralph/ralph.sh --tool codex 20        # Defaults to `run`
./ralph/ralph.sh 20                     # Uses RALPH_TOOL env var (default: claude)
```

## Contents

| File | Purpose |
|------|---------|
| `ralph.sh` | Single entry point: `run`, `status`, `dashboard` subcommands |
| `dashboard.html` | Dashboard UI (phases, commits, next story) |
| `CLAUDE.md` | Agent instructions (read by `ralph.sh run`) |
| `prd.json` | PRD with user stories — **customize for your project** |
| `progress.txt` | Progress log (append-only, codebase patterns at top) |
| `.last-branch` | Runtime state (branch tracking, gitignored) |
| `archive/` | Archived runs when PRD `branchName` changes (gitignored) |

## Requirements

- **Parent directory** must be a git repository (for commits, git log)
- **System**: `jq`, `python3`, `git`, `lsof`, `pgrep`
- **AI runtime**: one of `claude` (Claude Code), `minimax` (Claude via MiniMax API), `codex` (Codex CLI), or `amp`

## Usage

```bash
./ralph/ralph.sh run [--tool claude|minimax|codex|amp] [max_iterations]
./ralph/ralph.sh status [--watch|-w]
./ralph/ralph.sh dashboard [--open|-o]
./ralph/ralph.sh help

# Tool commands used internally:
#   claude   → claude --dangerously-skip-permissions -p
#   minimax  → claude --dangerously-skip-permissions --print (MiniMax env bridge)
#   codex    → codex exec --full-auto
#   amp      → amp -x
#
# ⚠️  WARNING: The --dangerously-skip-permissions flag bypasses permission checks.
#   Only use in trusted local repositories. Never use against untrusted code
#   or on shared/public repositories.

# Override default tool via env var:
RALPH_TOOL=codex ./ralph/ralph.sh run 20

Note: the dashboard binds to `127.0.0.1` and is only accessible from the local machine.
```

## Customizing for Your Project

1. **`prd.json`** — Define your user stories:
   - `project`, `branchName`, `description`
   - `userStories[]` with `id`, `title`, `description`, `acceptanceCriteria`, `passes`, `priority`

2. **`progress.txt`** — Add a `## Codebase Patterns` section at the top with reusable learnings (Ralph reads this before each iteration).

## How It Works

1. Ralph reads `prd.json` and picks the highest-priority story where `passes: false`
2. Runs the selected agent (`claude`, `codex`, or `amp`) with `CLAUDE.md` as the prompt (shared prompt filename retained for backward compatibility)
3. Agent implements the story, runs tests, commits with `feat: [ID] - [Title]`, sets `passes: true`, appends to `progress.txt`
4. Loops until all stories pass or max iterations reached
5. On `<promise>COMPLETE</promise>`, Ralph exits successfully
6. If all stories are `passes: true`, Ralph exits successfully even without `<promise>COMPLETE</promise>`

## Self-Contained

All paths use `SCRIPT_DIR`. Place `ralph/` at any project root and customize `prd.json` and `progress.txt`. Scripts are symlink-safe and work when invoked via symlink from `PATH`.
