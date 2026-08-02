---
name: mcp-agent-mail-no-slack-bridge
description: |
  Canonical reference for the SOUL.md COMMIT `mcp-agent-mail-no-passive-slack-listening`.
  Use when asked to (a) verify MCP Agent Mail is not listening/posting into Slack,
  (b) re-enable the Slack bridge (rare; requires explicit "ENABLE MCP MAIL SLACK BRIDGE"),
  (c) debug why a bot reply landed in a thread, or (d) audit a new MCP mail install.
---

# MCP Agent Mail — No Slack Bridge (default)

## TL;DR

MCP Agent Mail is for **agent-to-agent coordination only**. The Slack bridge (inbound Socket-Mode listener + outbound notifier) is **off by default** and MUST stay off unless the operator explicitly types `ENABLE MCP MAIL SLACK BRIDGE` in the current session.

## What the bridge does (when enabled)

- **Inbound**: Socket-Mode listener on `SLACK_APP_TOKEN=xapp-...` reads every message in any sync-configured channel and creates an MCP message with sender `SlackBridge`. The agent that picks up the MCP message then **posts a full investigation reply back to the originating Slack thread** via `chat.postMessage`.
- **Outbound**: when an MCP message is created (e.g. `mcp__mcp-agent-mail__send_message`), it gets mirrored to Slack via webhook (`SLACK_WEBHOOK_URL`) and/or posted via `chat.postMessage` (`SLACK_BOT_TOKEN`). Replies can land in arbitrary channels depending on `SLACK_DEFAULT_CHANNEL`.

## Why it's off

Incident `C09GRLXF9GR/p1784573557759039` (2026-07-20): a normal operator question in `#all-$USER-ai` triggered the MCP Agent Mail bot (`U0A4G7LDJ4R`) to reply with a 4.5KB investigation (read Slack history, cloned plugin source, parsed install state). The bot had ingested the operator's message as a `SlackBridge` MCP message, and the agent that picked it up posted back to the thread. The same launchd job (`com.mcp.agent.mail`) was also the reason the EA-sweep brief was getting routed into the operator's DM (`D0A418NEHHC`) instead of the configured `#life` channel.

## ⚠️ The `slack_post_message` tool exposure (separate from listener/notifier)

**Critical pitfall the original skill missed:** the MCP Agent Mail server exposes a `slack_post_message` tool (`~/mcp_mail/src/mcp_agent_mail/app.py:8766`) that **posts to Slack as the vendor's own Slack app identity `U0A4G7LDJ4R`** regardless of `SLACK_ENABLED=false`. The `.env.slack-off` overlay disables only the **passive listener + notifier** paths. The `slack_post_message` tool is reachable to any AO worker that has `http://127.0.0.1:8765/mcp/` in its MCP server list.

Result: a worker can deliver Slack posts under `U0A4G7LDJ4R` identity even when the bridge is "off." Incident `C0AH3RY3DK6/p1784596443` (2026-07-20): campaign-design thread got 7 posts from `U0A4G7LDJ4R` interleaving with the operator's own Hermes-bot replies — substantive worker-LLM analysis (L20-keyword density, Aizen-pattern ranking, "HARD-GATE active"), not bot boilerplate. The user explicitly said: *"hermes should be using `<@U0AEZC7RX1Q>` and not `<@U0A4G7LDJ4R>` when im giving it tasks… it should reply using the build in slack integration."*

**Rule for any tool surface that can reach `mcp_agent_mail.slack_post_message`:**
1. The default tool path for Hermes posting to Slack is `mcp__slack__conversations_add_message` (Hermes bot, `U0AEZC7RX1Q`), wired in `~/.hermes/config.yaml` `mcp_servers.slack` and `~/.codex/config.toml` `[mcp_servers.slack]` with `SLACK_MCP_XOXB_TOKEN`.
2. **Never reach `mcp_agent_mail.slack_post_message` from a Hermes-side or AO-worker dispatch** — it posts as the vendor identity, which is wrong for operator-facing threads. Hermes has its own tool path; use that.
3. If a worker reaches for `mcp_agent_mail.slack_post_message` via `mcporter` or direct HTTP, the dispatch is misrouted. Fix the dispatch, not the tool.

**Mitigation checklist (operator-level, in priority order):**
- [ ] Add `disabled_tools: [slack_post_message]` to the MCP Agent Mail server entry in `~/.hermes/config.yaml` so Hermes sessions cannot see the tool at all.
- [ ] Same flag on the Codex config (`~/.codex/config.toml`) so AO Codex workers cannot call it.
- [ ] Verify with `python3 ~/tests/test_mcp_agent_mail_slack_off.py` — extend the test to assert `slack_post_message` is absent from `tools/list`.

See `references/two-identity-slack-routing.md` for the full bot-identity / token / config table.

## How the fix is wired

Three layers (all required):

1. **Env overlay** at `~/mcp_mail/.env.slack-off` with 6 disabling flags. Canonical source of truth.
2. **Server boot path** `~/mcp_mail/scripts/run_server_with_token.sh` sources the overlay BEFORE any other env (including `~/.bashrc` exports) so its `SLACK_ENABLED=false` wins.
3. **Launchd plist** `~/Library/LaunchAgents/com.mcp.agent.mail.plist` does NOT define `SLACK_ENABLED` or `SLACK_SYNC_ENABLED` in `<EnvironmentVariables>`.

## Verification

```bash
# Layer 1+2: file-level
ls -la ~/mcp_mail/.env.slack-off
grep -E '^SLACK_(ENABLED|SYNC_ENABLED|NOTIFY_ON_MESSAGE|NOTIFY_ON_ACK|SLACKBOX_ENABLED|USE_BLOCKS)=' ~/mcp_mail/.env.slack-off
grep -n 'env.slack-off' ~/mcp_mail/scripts/run_server_with_token.sh

# Layer 3: plist-level
grep -E '<key>SLACK_(ENABLED|SYNC_ENABLED)</key>' ~/Library/LaunchAgents/com.mcp.agent.mail.plist  # must be empty

# Runtime: live log + live env + live health
PID=$(pgrep -f "cli serve-http" | head -1)
ps eww -p $PID | tr ' ' '\n' | grep -E '^SLACK_(ENABLED|SYNC_ENABLED)='  # both =false
grep -iE 'Slack client connected|Slack integration initialized' /tmp/mcp_agent_mail_server.log  # empty
curl -s -m 5 -H "Authorization: Bearer ${HTTP_BEARER_TOKEN}" http://127.0.0.1:8765/mcp/ \
  -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' | head -c 300  # 200 with MCP serverInfo

# NEW: tool-surface audit — slack_post_message must be unreachable from
# Hermes / Codex runtimes. Confirm with tools/list (should omit the tool
# once disabled_tools is configured):
curl -s -m 5 -H "Authorization: Bearer ${HTTP_BEARER_TOKEN}" http://127.0.0.1:8765/mcp/ \
  -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); \
      tools=[t['name'] for t in d['result']['tools']]; \
      assert 'slack_post_message' not in tools, 'slack_post_message is still reachable'; \
      print('OK: slack_post_message hidden from tools/list')"
```

Or run the contract test:

```bash
python3 ~/tests/test_mcp_agent_mail_slack_off.py
# (extend the test to assert slack_post_message is absent from tools/list
# once the disabled_tools config lands)
```

## Re-enabling the bridge (operator explicit ask only)

ONLY when the operator types `ENABLE MCP MAIL SLACK BRIDGE` in the current session:

```bash
# 1. Remove the overlay (or comment out the SLACK_* lines)
mv ~/mcp_mail/.env.slack-off{,.disabled-by-operator}

# 2. Optionally set SLACK_BOT_TOKEN / SLACK_APP_TOKEN / SLACK_SYNC_CHANNELS in the plist
#    (defaults are all false / empty).

# 3. Restart the launchd job
launchctl bootout "gui/$(id -u)/com.mcp.agent.mail" 2>&1 | head
sleep 2
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.mcp.agent.mail.plist

# 4. Verify the Slack lines reappear in the log
tail -30 /tmp/mcp_agent_mail_server.log | grep -iE 'slack client connected'
```

After re-enabling, post ONE Slack message confirming what changed and where it now posts — the bridge's silence-to-noise ratio is what made it toxic last time.

## Files

| File | Purpose |
|---|---|
| `~/mcp_mail/.env.slack-off` | env overlay — 6 flags =false |
| `~/mcp_mail/scripts/run_server_with_token.sh` | sources overlay before any other env |
| `~/Library/LaunchAgents/com.mcp.agent.mail.plist` | MUST NOT define SLACK_ENABLED |
| `~/tests/test_mcp_agent_mail_slack_off.py` | 4-layer contract test |
| `~/.hermes/workspace/SOUL.md` `## COMMIT: mcp-agent-mail-no-passive-slack-listening` | the canonical behavioral contract |
| `references/two-identity-slack-routing.md` | Hermes-bot vs mcp_agent_mail Slack identity / token / config table; sub-second interleaving diagnostic fingerprint; three layers to fix routing |
