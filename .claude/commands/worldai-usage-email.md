---
description: Send daily/weekly Your Project usage report email to $USER@gmail.com
type: git
execution_mode: manual
---
# WorldAI Usage Email - Send Daily/Weekly Report

Sends the Your Project daily + weekly usage report email to $USER@gmail.com.

## Command

```bash
EMAIL_PASS=$(grep "EMAIL_PASS=" ~/.bashrc | head -1 | cut -d'"' -f2) && \
source ${PROJECT_VENV:-$(find $HOME/projects -name activate -path "*/venv/*" | head -1)} && \
EMAIL_APP_PASSWORD="$EMAIL_PASS" EMAIL_USER="$USER@gmail.com" \
WORLDAI_DEV_MODE=true GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python3 ${PROJECT_ROOT:-$(git rev-parse --show-toplevel)}/scripts/daily_campaign_report.py --send-email
```

## Notes

- **Script**: `scripts/daily_campaign_report.py` in any your-project.com worktree
- **Password**: Stored in `~/.bashrc` as `EMAIL_PASS` (Gmail App Password)
- **Venv**: Uses `$PROJECT_VENV` if set; otherwise auto-detects first venv under `$HOME/projects`
- **Output**: Saves report to `~/Downloads/campaign-activity-report-YYYY-MM-DD.txt`
- **Contains**: Last week DAU stats + Last 4 weeks DAU/WAU stats + top users + cost

## Setup

Set these before running to avoid auto-detection:
```bash
export PROJECT_ROOT=$(git rev-parse --show-toplevel)
export PROJECT_VENV=$PROJECT_ROOT/venv
```
