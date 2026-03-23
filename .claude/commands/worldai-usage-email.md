# WorldAI Usage Email - Send Daily/Weekly Report

Sends the Your Project daily + weekly usage report email to jleechan@gmail.com.

## Command

```bash
EMAIL_PASS=$(grep "EMAIL_PASS=" ~/.bashrc | head -1 | cut -d'"' -f2) && \
source /Users/jleechan/projects/worktree_livingw3/venv/bin/activate && \
EMAIL_APP_PASSWORD="$EMAIL_PASS" EMAIL_USER="jleechan@gmail.com" \
WORLDAI_DEV_MODE=true GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python3 /Users/jleechan/projects/worktree_rlimit4/scripts/daily_campaign_report.py --send-email
```

## Notes

- **Script**: `scripts/daily_campaign_report.py` in any your-project.com worktree
- **Password**: Stored in `~/.bashrc` as `EMAIL_PASS` (Gmail App Password)
- **Venv**: Uses `worktree_livingw3/venv` since the current worktree may not have one
- **Output**: Saves report to `~/Downloads/campaign-activity-report-YYYY-MM-DD.txt`
- **Contains**: Last week DAU stats + Last 4 weeks DAU/WAU stats + top users + cost

## Alternate worktrees

If `worktree_livingw3` is gone, find another venv:
```bash
find /Users/jleechan/projects -name "activate" -path "*/venv/*" | head -5
```
Then substitute the path in the `source` command above.
