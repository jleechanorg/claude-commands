---
description: Send daily/weekly WorldArchitect.AI usage report email to jleechan@gmail.com
type: git
execution_mode: manual
---
# WorldAI Usage Email - Send Daily/Weekly Report

Sends the WorldArchitect.AI daily + weekly usage report email to jleechan@gmail.com.

## Command

```bash
EMAIL_PASS=$(grep "EMAIL_PASS=" ~/.bashrc | head -1 | cut -d'"' -f2) && \
VENV_ACTIVATE=${PROJECT_VENV:-$(find "$HOME/projects" -name activate -path "*/venv/*" 2>/dev/null | head -1)} && \
[[ -n "$VENV_ACTIVATE" ]] || { echo "Error: No venv found. Set PROJECT_VENV or ensure a venv exists under $HOME/projects"; exit 1; } && \
source "$VENV_ACTIVATE" && \
SCRIPT_ROOT=${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null)} && \
[[ -n "$SCRIPT_ROOT" ]] || { echo "Error: Not in a git repository. Set PROJECT_ROOT or run from within the worldarchitect.ai repo"; exit 1; } && \
EMAIL_APP_PASSWORD="$EMAIL_PASS" EMAIL_USER="jleechan@gmail.com" \
WORLDAI_DEV_MODE=true GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
python3 "$SCRIPT_ROOT/scripts/daily_campaign_report.py" --send-email
```

## Notes

- **Script**: `scripts/daily_campaign_report.py` in any worldarchitect.ai worktree
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
