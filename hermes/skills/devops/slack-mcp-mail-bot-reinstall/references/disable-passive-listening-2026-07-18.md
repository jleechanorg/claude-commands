# Disable mcp_agent_mail passive-listening — 2026-07-18 session

Session transcript condensed. The user complaint was a single Slack message:

> I don't want mcp agent mail to be passively listening
> <https://jleechanai.slack.com/archives/C09GRLXF9GR/p1784331425867479>

The link pointed at a top-level message in `#all-$USER-ai` (C09GRLXF9GR) from bot identity `mcp_agent_mail` (Slack user `U0A4G7LDJ4R`, bot `B0A3MS7G08P`, app `A0A3WSV6BM1`). The post was a long unsolicited proof-of-concept summary about cloud-build — Jeffrey had not asked for it.

## Mechanism (verified, not hypothesized)

mcp_agent_mail uses **Socket Mode** when an App-Level Token (`SLACK_APP_TOKEN=xapp-...`) is present. With one, the server opens a WebSocket to Slack and Slack pushes events in real-time without requiring a public URL or webhook receiver. With `SLACK_BOT_TOKEN=xoxb-...` also present, the bot identity uses those events to mirror messages back into Slack channels and to auto-reply to MCP-side messages.

That bidirectional sync is what Jeffrey saw. It is not a webhook (the webhook URL `SLACK_WEBHOOK_URL` is a separate one-way outgoing path for the *mirror* feature). It is not a Slack app manifest gap. It is **the documented Socket Mode integration working as configured.**

## Live state captured 2026-07-18

| What | Where | Evidence |
|---|---|---|
| Server PID | 46265 | `ps -ef \| grep mcp_agent_mail` |
| Up time | 2h43m at time of capture | `ps -o etime` |
| Listen socket | TCP 127.0.0.1:8765 | `lsof -nP -iTCP -sTCP:LISTEN -p 46265` |
| launchd label | `com.mcp.agent.mail` | `launchctl print gui/501/com.mcp.agent.mail` |
| launchd state | running, KeepAlive=true, RunAtLoad=true | plist + launchctl print |
| Plist path | `~/Library/LaunchAgents/com.mcp.agent.mail.plist` | shell `ls` |
| Stdio log | `/tmp/mcp_agent_mail_server.log` (518KB) | shell `ls -la` |
| bashrc tokens | `~/.bashrc:946-947` | `grep -nE '^export SLACK_(APP\|BOT)_TOKEN=' ~/.bashrc` |
| Token values | `SLACK_BOT_TOKEN="[REDACTED_SLACK_TOKEN]"` / `SLACK_APP_TOKEN="xapp-1-A0AESRKA7L3-...d63d"` | bashrc |
| Config source | NOT `~/.mcp_mail/credentials.json` (empty in PyPI installs) | shell `ls ~/.mcp_mail/` |

## Configuration schema (from `mcp_agent_mail/config.py:372-392`)

```python
enabled = _bool(_get_config_value("SLACK_ENABLED", default="false"), default=False)
bot_token = _get_config_value("SLACK_BOT_TOKEN", default="") or None
app_token = _get_config_value("SLACK_APP_TOKEN", default="") or None   # ← Socket Mode listener
signing_secret = _get_config_value("SLACK_SIGNING_SECRET", default="") or None
default_channel = _get_config_value("SLACK_DEFAULT_CHANNEL", default="general")
notify_on_message = _bool(_get_config_value("SLACK_NOTIFY_ON_MESSAGE", default="true"), default=True)
notify_on_ack = _bool(_get_config_value("SLACK_NOTIFY_ON_ACK", default="false"), default=False)
sync_enabled = _bool(_get_config_value("SLACK_SYNC_ENABLED", default="false"), default=False)
sync_project_name = _get_config_value("SLACK_SYNC_PROJECT_NAME", default="Slack Sync")
sync_channels = _csv("SLACK_SYNC_CHANNELS", default="")
sync_thread_replies = _bool(_get_config_value("SLACK_SYNC_THREAD_REPLIES", default="true"), default=True)
sync_reactions = _bool(_get_config_value("SLACK_SYNC_REACTIONS", default="true"), default=True)
webhook_url = _get_config_value("SLACK_WEBHOOK_URL", default="") or None   # ← mirror (outbound)
```

Defaults: `SLACK_ENABLED=false`, `SLACK_SYNC_ENABLED=false`, but `SLACK_NOTIFY_ON_MESSAGE=true`. So enabling Slack by setting `SLACK_BOT_TOKEN` alone is sufficient to start outbound auto-mirroring — sync is opt-in.

## Exact soft-disable commands (Scope A)

```bash
# 1. Stop the running server so step 3 inherits the new env
launchctl bootout gui/$(id -u)/com.mcp.agent.mail

# 2. Comment out the Slack tokens at the source (~/.bashrc lines 946-947).
#    Keep the values — just remove the export so this is reversible.
sed -i.bak -E 's/^export (SLACK_(BOT|APP)_TOKEN=)/#\1/' ~/.bashrc

# 3. Restart under launchd — empty token env → Slack sync code paths short-circuit
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mcp.agent.mail.plist

# 4. Verify Socket Mode didn't reopen
sleep 3
pgrep -fl 'mcp_agent_mail.cli serve-http'
lsof -nP -iTCP -sTCP:LISTEN -p <NEW_PID> | grep TCP    # only 127.0.0.1:8765
grep -E 'slack|bolt|SocketMode' /tmp/mcp_agent_mail_server.log | tail -20   # silent
```

## Lessons for next session

- **Soft disable vs full shutdown is a real choice.** Anyone holding inter-agent MCP integrations will lose them on Scope B. Always offer Scope A first.
- **The `~946-947` line numbers are approximate** — bashrc gets edited. Verify with grep, never assume.
- **Don't `kill` alone.** `KeepAlive=true` respawns within seconds.
- **Verify in the channel**, not just in the log. A silent log with still-arriving bot messages means env didn't take.
- **PyPI installs → bashrc tokens, not credentials.json.** Document this — earlier sessions tripped on this assumption.
