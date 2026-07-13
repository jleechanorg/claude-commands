---
name: hermes-slack-rotation
description: Rotate or repair Hermes Slack credentials, provision the complete Hermes Slack app permission baseline from the beginning, update macOS shell exports safely, and verify the live gateway path. Use for Hermes Slack token rotation, Slack app reinstall, Socket Mode token replacement, missing Slack scopes, or Slack invalid_auth failures.
---

# Hermes Slack rotation and complete permission baseline

Never print, log, commit, or place a Slack secret in chat. Keep tokens in process memory only, write them only to protected shell files, and redact them in command output.

## 1. Inventory before changing anything

1. Inspect the live app at Slack API `Your Apps`. In the $USER AI workspace, known apps are `hermes`, `hermes_staging`, `hermes_pc`, and `hermes_staging_pc`; rotate only apps the user requested.
2. Identify the target configuration and active service before changing a token. On this Mac, the production token exports are in `~/.bashrc`; `~/.bash_profile` and `~/.profile` source it. `~/.hermes/scripts/launchd-env-wrapper.sh` also re-extracts key variables from `~/.bashrc`, so `.bashrc` is authoritative for the daemon.
3. Back up every edited dotfile with restrictive permissions. Never use broad search-and-replace that can modify unrelated secrets.

## 2. Provision the full Hermes Slack app baseline first

For a full Hermes Slack experience, set the complete baseline in the live app manifest before install/reinstall. Use the workspace-scoped manifest editor:

`https://app.slack.com/app-settings/<team-id>/<app-id>/app-manifest`

Do not use `https://api.slack.com/apps/<app-id>/app-manifest`, which is not the editor for an existing app.

### Bot OAuth scopes

Set these scopes for full Slack Assistant and native slash-command support:

- `app_mentions:read`
- `assistant:write`
- `channels:history`
- `channels:read`
- `chat:write`
- `commands`
- `files:read`
- `files:write`
- `groups:history`
- `groups:read`
- `im:history`
- `im:read`
- `im:write`
- `users:read`

Do not remove existing least-privilege-approved extras such as `reactions:read`, `reactions:write`, `team:read`, or `users:read.email` without confirming no deployed Hermes feature uses them.

### User OAuth scopes, only when Slack MCP or user-context features are enabled

- `channels:history`, `channels:read`, `chat:write`
- `files:read`
- `groups:history`, `groups:read`
- `im:history`, `im:read`, `im:write`
- `mpim:history`, `mpim:read`
- `search:read`
- `usergroups:read`
- `users:read`, `users:read.email`

### App settings and events

- Enable Socket Mode.
- Enable Interactivity.
- Add bot events: `app_mention`, `message.channels`, `message.groups`, `message.im`, `assistant_thread_started`, and `assistant_thread_context_changed`.
- Define native slash commands only after confirming their request URL is publicly reachable. Do not publish a placeholder/local URL such as `https://hermes-agent.local/...`.
- Generate an app-level `xapp-...` token with `connections:write`. Reinstalling an app rotates OAuth tokens but does **not** automatically replace this Socket Mode token.

## 3. Install/reinstall and capture all three token classes

1. In OAuth & Permissions, choose `Install to <workspace>` or `Reinstall to <workspace>` and approve consent.
2. Capture the new bot `xoxb-...` and, if configured, user `xoxp-...` token from the returned OAuth page.
3. In Basic Information → App-Level Tokens, generate or rotate an `xapp-...` token with `connections:write`.
4. Save each token privately. Do not assume token rotation or app reinstall preserved any prior token.

## 4. Update this Mac safely

For the production `hermes` app, synchronize these exports in both `~/.bashrc` and `~/.profile` when they exist:

- Bot token: `SLACK_BOT_TOKEN`, `SLACK_MCP_XOXB_TOKEN`, `HERMES_SLACK_BOT_TOKEN`
- User token: `SLACK_MCP_XOXP_TOKEN` in `.bashrc`; `SLACK_USER_TOKEN` in `.profile`
- App token: `SLACK_APP_TOKEN`

Use literal quoted values, preserve other configuration, then set `chmod 600 ~/.bashrc ~/.profile`.

## 5. Verify the exact runtime path before claiming success

Run token probes from a clean shell that sources the real `.bashrc`, not merely from a copied file or an inherited terminal environment:

```bash
env -i HOME="$HOME" PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin" bash --noprofile --norc -c '
  source "$HOME/.bashrc"
  curl -sS -H "Authorization: Bearer $SLACK_BOT_TOKEN" https://slack.com/api/auth.test
  curl -sS -H "Authorization: Bearer $SLACK_MCP_XOXP_TOKEN" https://slack.com/api/auth.test
  curl -sS -X POST -H "Authorization: Bearer $SLACK_APP_TOKEN" https://slack.com/api/apps.connections.open
'
```

All three responses must return `"ok":true`.

Then verify the actual granted OAuth scopes through `auth.test` response headers, because `apps.permissions.scopes.list` can return `unknown_method`:

```bash
curl -sS -D - -o /dev/null -H "Authorization: Bearer $SLACK_BOT_TOKEN" https://slack.com/api/auth.test | tr -d '\r' | grep -i '^x-oauth-scopes:'
```

Finally run:

```bash
~/.hermes/scripts/doctor.sh
~/.hermes/scripts/hermes-health.sh --json
launchctl print gui/$(id -u)/ai.hermes.prod
```

Separate a token failure from a LaunchAgent/service-registration failure. Valid token probes do not prove a daemon has reloaded them. If restart is blocked by macOS permissions, report that specifically rather than declaring the gateway healthy.
