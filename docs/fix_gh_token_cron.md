# Fix: GitHub Token Authentication for Cron Jobs

## Problem
The jleechanorg PR automation was failing with "API rate limit exceeded" errors every 30 minutes since 17:30 on 2025-09-30. The issue was NOT actual rate limiting (4769/5000 API calls remaining), but rather **unauthenticated API requests** from the cron job.

## Root Cause
Cron jobs don't inherit the user's shell environment. The `gh` CLI was executing without the `GITHUB_TOKEN` environment variable, causing it to make unauthenticated requests which have a much lower rate limit (60 requests/hour vs 5000/hour for authenticated).

## Solution
Updated the crontab to source the `~/.token` file before executing the automation script:

**Before:**
```bash
*/30 * * * * /Users/jleechan/projects/worktree_worker1/automation/.venv/bin/jleechanorg-pr-monitor >> /Users/jleechan/Library/Logs/worldarchitect-automation/jleechanorg_pr_monitor.log 2>&1
```

**After:**
```bash
*/30 * * * * . $HOME/.token && /Users/jleechan/projects/worktree_worker1/automation/.venv/bin/jleechanorg-pr-monitor >> /Users/jleechan/Library/Logs/worldarchitect-automation/jleechanorg_pr_monitor.log 2>&1
```

## Verification
Manual test with sourced token file successfully discovered and processed 17 PRs:
- ✅ 8 PRs from ai_universe
- ✅ 2 PRs from ai_universe_frontend
- ✅ 3 PRs from worldarchitect.ai
- ✅ 2 PRs from codex_plus
- ✅ 1 PR from worldai_ralph
- ✅ 1 PR from worldai_genesis

The automation posted Codex instruction comments on each PR successfully.

## Testing Timeline
- **Manual test**: 2025-09-30 23:02:01 - ✅ Success (17 PRs processed)
- **Next cron run**: 2025-09-30 23:30:00 (will verify automatic execution)

## Related Files
- Crontab entry: `crontab -l`
- Token file: `~/.token` (contains `export GITHUB_TOKEN="..."`)
- Logs: `~/Library/Logs/worldarchitect-automation/jleechanorg_pr_monitor.log`
