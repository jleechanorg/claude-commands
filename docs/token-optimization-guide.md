# Token Optimization Guide (Claude Code CLI)

## Goal
Reduce token usage in long-running coding sessions by:
- Keeping conversation history small (use `/clear` proactively).
- Reducing large tool payloads (targeted reads, minimal diffs).

## When to use `/clear`
- After merging a PR (or finishing a major review round).
- At the end of the work day.
- When switching to a different feature/bug/area of the codebase.
- After completing a “checkpoint” run (tests/lint pass) and you want a clean context for the next step.

## Preserve context before clearing
Do one (or more) of these before `/clear`:
- Commit a checkpoint: `git add -A && git commit -m "wip: checkpoint"` (or a real message if ready).
- Write/refresh Beads issues for follow-ups (so TODOs aren’t trapped in chat history).
- Leave a short state note in the PR (what changed, what’s next, what commands were run).
- Save the exact commands + outputs you’ll need to resume (e.g., failing test name, stack trace excerpt).

## What’s automated in this repo
These hooks are registered in `.claude/settings.json`:
- `PreToolUse`: modifies tool requests to reduce payload size.
  - `Read`: for files >500 lines, injects `offset`/`limit` (500-line window for 501–2000 lines, 2000-line window for >2000 lines).
  - `Bash`: injects `--minimal --unified=0` into `git diff` commands (when missing).
- `UserPromptSubmit`: warns when a session grows large (500/1000/2000 message thresholds).

All hooks are designed to be non-blocking: if a lookup or optimization fails, they fall back without breaking the workflow.

## Logs / troubleshooting
Hooks log to per-branch files under `/tmp/worldarchitect.ai/<branch>/`:
- `hook_modifications.log`
- `session_warnings.log`

If you don’t see logs, it usually means:
- The hook didn’t run (wrong CLI config / not inside a git worktree).
- The optimization didn’t apply (e.g., file is small, `offset`/`limit` already provided).
- The local environment is missing a dependency (e.g., `jq`); the hook will still be non-blocking.
