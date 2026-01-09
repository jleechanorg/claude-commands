# Agent Instructions (Repository Root)

This file applies to the entire repository.

## Cron / Token Safety
- **Leave token configuration alone unless asked**: Do **not** remove, redact, rotate, or otherwise modify any existing `GITHUB_TOKEN=...` lines in the user's **actual system crontab** (output of `crontab -l`) unless the user explicitly requests it.
- If you edit cron schedules, preserve any existing `GITHUB_TOKEN=...` lines exactly as-is. You may warn and suggest safer alternatives, but do not auto-change it.

## More Guidelines
- See `docs/project-files/AGENTS.md` for the full repository guidelines.

