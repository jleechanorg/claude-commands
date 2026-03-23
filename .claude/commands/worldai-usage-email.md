---
description: Send daily/weekly project usage report email to project owner
type: git
execution_mode: manual
---
# Project Usage Email - Send Daily/Weekly Report

Sends the daily + weekly usage report email.

## Command

```bash
EMAIL_PASS=$(grep "EMAIL_PASS=" ~/.bashrc | head -1 | cut -d'"' -f2) && source ${PROJECT_VENV:-$HOME/projects/your-project/venv}/bin/activate && EMAIL_APP_PASSWORD="$EMAIL_PASS" EMAIL_USER="$USER@gmail.com" WORLDAI_DEV_MODE=true GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json python3 ${PROJECT_ROOT:-$HOME/projects/your-project}/scripts/daily_campaign_report.py --send-email
```

## Notes

- **Script**: `scripts/daily_campaign_report.py` in your project root
- **Password**: Stored in `~/.bashrc` as `EMAIL_PASS` (Gmail App Password)
- **Venv**: Uses `$PROJECT_VENV` (set before running); defaults to `$HOME/projects/your-project/venv`
- **Output**: Saves report to `~/Downloads/campaign-activity-report-YYYY-MM-DD.txt`

## Setup

Set these env vars before running:
```bash
export PROJECT_ROOT="$HOME/projects/your-project"
export PROJECT_VENV="$PROJECT_ROOT/venv"
```
