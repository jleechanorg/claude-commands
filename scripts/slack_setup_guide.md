# Slack Notifications for Claude Code Setup Guide

This guide explains how to configure Slack notifications for Claude Code hooks, allowing you to receive notifications when Claude Code completes tasks and awaits your next instruction.

## Quick Setup (5 minutes)

### 1. Create Slack App and Webhook

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Name your app (e.g., "Claude Code Notifications") and select your workspace
5. In the app settings, go to "Incoming Webhooks"
6. Toggle "Activate Incoming Webhooks" to ON
7. Click "Add New Webhook to Workspace"
8. Select the channel where you want notifications (e.g., #dev-alerts)
9. Copy the webhook URL that starts with `https://hooks.slack.com/services/...`

### 2. Set Environment Variable

Add the webhook URL to your shell profile (choose one):

**For bash (.bashrc or .bash_profile):**
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**For zsh (.zshrc):**
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**For fish (.config/fish/config.fish):**
```fish
set -gx SLACK_WEBHOOK_URL "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc, etc.
```

### 3. Test the Setup

Make sure the script is executable (run this once):
```bash
chmod +x scripts/slack_notify.sh
```

Test the notification script directly:
```bash
./scripts/slack_notify.sh "Test notification from Claude Code"
```

You should see a message in your Slack channel with repository and branch information.

## How It Works

The Slack notification system is integrated into Claude Code hooks:

- **Stop Hook**: Triggers when Claude Code finishes work and waits for your next command
- **Message Format**: Includes repository name, current branch, and timestamp
- **Automatic Context**: Shows what branch you're working on and when the work completed

## Example Notification

When Claude Code completes a task, you'll receive a Slack message like:

```
✅ Claude Code: Work completed - awaiting next instruction

📁 Repository: worktree_roadmap
🌿 Branch: feature/slack-notifications
⏰ Time: 2024-12-21 14:30:15
```

## Configuration Details

The hook is configured in `.claude/settings.json`:

```json
"Stop": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x \"$ROOT/scripts/slack_notify.sh\" ] && exec \"$ROOT/scripts/slack_notify.sh\" \"✅ Claude Code: Work completed - awaiting next instruction\"; fi; exit 0'",
        "description": "Send Slack notification when Claude Code stops and awaits next command"
      }
    ]
  }
]
```

## Customization

### Custom Messages

You can customize the notification message by modifying the command in `.claude/settings.json` or creating additional hooks for different scenarios.

### Additional Hook Points

You can add Slack notifications to other Claude Code events:

- **PostToolUse**: After major operations
- **PreToolUse**: Before starting work
- **UserPromptSubmit**: When you submit a new command

### Advanced Features

The script supports:
- Automatic repository and branch detection
- Graceful handling when SLACK_WEBHOOK_URL is not set
- JSON escaping for safe message transmission
- Error handling with clear feedback

## Troubleshooting

### No notifications appearing

1. Check that `SLACK_WEBHOOK_URL` is set:
   ```bash
   echo $SLACK_WEBHOOK_URL
   ```

2. Test the webhook directly:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test message"}' \
     $SLACK_WEBHOOK_URL
   ```

3. Verify the script is executable:
   ```bash
   ls -la scripts/slack_notify.sh
   ```

### Script errors

- Ensure `jq` is installed for JSON processing:
  ```bash
  brew install jq  # macOS
  sudo apt install jq  # Ubuntu/Debian
  ```

- Check script permissions:
  ```bash
  chmod +x scripts/slack_notify.sh
  ```

## Security Notes

- Keep your webhook URL secure and never commit it to version control
- The webhook URL has write access to your Slack channel
- Environment variables are the recommended way to store the webhook URL
- The script only sends notifications, it cannot read messages or perform other Slack operations

## Free Tier Limitations

Slack's free tier includes:
- Unlimited apps and integrations
- 10,000 most recent messages visible
- No additional cost for webhook notifications
- Webhooks are rate limited (typically ~1 message/second per webhook). See [Slack's rate limits documentation](https://api.slack.com/docs/rate-limits) for details.
