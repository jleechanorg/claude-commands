---
description: Run Ralph automation in this repo and get setup guidance for other repos
type: llm-orchestration
argument-hint: '[max_iterations] [--tool claude|amp]'
execution_mode: llm-driven
---

# /ralph - Ralph Automation (this repo + cross-repo setup)

Use this command when you need autonomous multi-iteration execution using
`scripts/ralph/ralph.sh` in this repository.

## In THIS repository (your-project.com / this repo)

1. Confirm you are at the repo root:
   ```bash
   pwd
   ls scripts/ralph/ralph.sh
   ```
2. Ensure dependencies are available:
   - `jq`
   - `claude` (if using `--tool claude`) and/or `amp` (if using `--tool amp`)
   - This repo has `scripts/ralph/prd.json` and `scripts/ralph/progress.txt`
3. Run Ralph:
   ```bash
   # Default: amp mode, 10 iterations
   ./scripts/ralph/ralph.sh

   # Explicit: claude mode
   ./scripts/ralph/ralph.sh --tool claude [max_iterations]

   # Explicit: amp mode
   ./scripts/ralph/ralph.sh --tool amp [max_iterations]
   ```
4. Optional pre-run check for required files:
   ```bash
   test -f scripts/ralph/prd.json && echo "prd.json exists"
   test -f scripts/ralph/CLAUDE.md && echo "Ralph prompt exists"
   ```

Note: this repo uses `scripts/ralph/ralph.sh` directly and does **not** require a separate
`prompt.md` for `amp` (it is intentionally wired to the local `CLAUDE.md` instruction file).

## If running Ralph from ANOTHER repository

If `/ralph` is invoked outside this repo, first review the canonical setup instructions in
`jleechanorg/claude-commands`:

- If available locally or via clone:
  - `~/projects/jleechanorg/claude-commands` (or your local path)
  - Check `README.md` and any `ralph`-related command docs in `.claude/commands/`
- If unavailable locally, fetch from GitHub:
  - <https://github.com/jleechanorg/claude-commands>

Use that guidance to install/copy the repository-specific Ralph command and script layout,
then run that repo’s documented equivalent of `scripts/ralph/ralph.sh`.

## Sanity check before handoff

- Confirm the target repo is on a dedicated branch for the task.
- Confirm `progress.txt` is present (or create as needed).
- After completion, verify iteration result and return final PR/story status.

