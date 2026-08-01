---
name: slackbots-setup
description: Recover prior Slack MCP Mail bot setup from history, run browserclaw-guided OAuth/reinstall flow, and verify userscope/bot tokens.
type: workflow
scope: user
---

# Slackbots Setup (MCP Mail)

> **Triage pointer (added 2026-07-13):** This skill is for **scope repair** — reinstalling the Slack app to add missing OAuth scopes. If your sweep symptom is "bot is in 0 channels" but `chat.postMessage` still succeeds (e.g. the bot can post in DMs but can't read any channel), the issue is **channel-membership, not scope**. Load `~/.hermes/skills/devops/slack-mcp-mail-bot-reinstall/SKILL.md` §6 for the `slack.getClient()` re-invite recipe — reinstalling will NOT auto-rejoin the bot to channels it was removed from.

## 1) Recover prior setup context via `/history`

Before changing anything, gather prior context:

- `/history "A0A3WSV6BM1"`
- `/history "mcp mail"`
- `/history "SLACK_MCP_XOXP_TOKEN"`
- `/history "Slack bot reinstall"`

Use the results to confirm whether this is a new install, scope refresh, or token drift.

## 2) Pull latest identity state

```bash
TOKEN=$(python3 - <<'PY'
import json
with open('$HOME/.mcp_mail/credentials.json') as f:
    print(json.load(f).get('SLACK_BOT_TOKEN',''))
PY)

curl -s https://slack.com/api/auth.test -H "Authorization: Bearer ${TOKEN}"
```

## 3) Browser flow with `/browserclaw`

Use headless browserclaw capture first (for a reproducible auth path):

```bash
browserclaw learn --url https://api.slack.com/apps/A0A3WSV6BM1/oauth \
  --output-dir /tmp/slackbots-browserclaw \
  --headless \
  --manual \
  --goal "Capture OAuth + permissions surfaces for MCP Mail reinstall"
```

Then perform the real reinstall in the interactive browser flow from that session output:

1. Open `https://api.slack.com/apps/A0A3WSV6BM1/oauth`
2. In **OAuth & Permissions**, ensure these bot scopes are present:
   - `channels:write`, `groups:write`, `mpim:write`, `im:write`
3. In **User Token Scopes**, include any required user scopes for your flows (current profile includes channels/groups/ims/mpim read/write/history + chat:write + users:read).
4. Click **Reinstall to Workspace** and allow the OAuth prompt.

## 4) Verify userscope/bot behavior

Run:

- `chat.postMessage` against `#ai-slack-test` and your DM target.
- `conversations.mark` to validate read-state scope path.
- `conversations.history` against a visible channel.

Success criteria:

- Existing `slack_post` path still posts as `mcp_agent_mail`.
- Mark/read and history/permission checks succeed with current userscope.

## 5) Persist evidence

Store the verification snippet and timestamp in `~/roadmap` or a daily memory note before closing the setup task.
