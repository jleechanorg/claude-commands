# Ralph — PRD-Driven Autonomous Workflow Toolkit

Self-contained toolkit for running iterative AI-driven development tasks from a PRD (Product Requirements Document). Ralph loops through user stories, runs an AI agent (`amp` or `claude`) to implement each one, and tracks progress.

## Quick Start

```bash
# From repo root
./ralph/ralph.sh run --tool claude 20   # Run agent loop
./ralph/ralph.sh status --watch         # Monitor progress
./ralph/ralph.sh dashboard --open       # Web dashboard on 127.0.0.1:9450 (local only)

# Shorthand (backwards compatible)
./ralph/ralph.sh --tool claude 20       # Defaults to `run`
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
- **AI runtime**: `amp` or `claude` (Claude Code)

## Usage

```bash
./ralph/ralph.sh run [--tool amp|claude] [max_iterations]
./ralph/ralph.sh status [--watch|-w]
./ralph/ralph.sh dashboard [--open|-o]
./ralph/ralph.sh help

Note: the dashboard binds to `127.0.0.1` and is only accessible from the local machine.
```

## Customizing for Your Project

1. **`prd.json`** — Define your user stories:
   - `project`, `branchName`, `description`
   - `userStories[]` with `id`, `title`, `description`, `acceptanceCriteria`, `passes`, `priority`

2. **`progress.txt`** — Add a `## Codebase Patterns` section at the top with reusable learnings (Ralph reads this before each iteration).

## How It Works

1. Ralph reads `prd.json` and picks the highest-priority story where `passes: false`
2. Runs `amp` or `claude` with `CLAUDE.md` as the prompt
3. Agent implements the story, runs tests, commits with `feat: [ID] - [Title]`, sets `passes: true`, appends to `progress.txt`
4. Loops until all stories pass or max iterations reached
5. On `<promise>COMPLETE</promise>`, Ralph exits successfully

## Self-Contained

All paths use `SCRIPT_DIR`. Place `ralph/` at any project root and customize `prd.json` and `progress.txt`. Scripts are symlink-safe and work when invoked via symlink from `PATH`.
