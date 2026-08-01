# xoxp Fallback Recipe — Sweep Reads When Bot Is Lock Out (added 2026-07-13)

Use this recipe when `mcp_agent_mail` bot (`U0A4G7LDJ4R`) is alive (auth.test ok) but **member of zero channels** (`conversations.list` returns empty `channels`). This happens after a Slack bot rotation when the new bot hasn't been re-invited to monitored channels yet.

## Detection — is this your failure mode?

Run these three probes in order. Stop at the first failure mode you confirm.

```bash
# Probe 1: bot alive?
curl -fsS -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  https://slack.com/api/auth.test
# Expected ok+user_id=mcp_agent_mail → alive

# Probe 2: bot member of how many channels?
curl -fsS -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  "https://slack.com/api/conversations.list?types=public_channel,private_channel&limit=200&exclude_archived=true"
# If "channels":[] → bot-locked-out, NOT token-revoked → use xoxp fallback

# Probe 3: xoxp user token works?
for line in ~/.bashrc; do
  [[ "$line" =~ ^export\ SLACK_MCP_XOXP_TOKEN= ]] && break
done
echo "${line#export SLACK_MCP_XOXP_TOKEN=}" | tr -d '"' | tr -d "'"
curl -fsS -H "Authorization: Bearer $SLACK_MCP_XOXP_TOKEN" \
  https://slack.com/api/auth.test
# Expected ok+user_id=U09GH5BR3QU → xoxp usable
```

**DO NOT** conclude "token revoked" from a single `auth.test` returning `invalid_auth`. Retry at least twice; the first call after tool spawn can race. Cross-validate with `conversations.list` (empty vs error).

## Read recipe — scan all 14 Tier-1 channels via xoxp

```python
import json, urllib.request, re

xoxp = "<load from ~/.bashrc SLACK_MCP_XOXP_TOKEN>"

def slack_history(token, channel_id, limit=30, oldest=None):
    url = f"https://slack.com/api/conversations.history?channel={channel_id}&limit={limit}"
    if oldest is not None: url += f"&oldest={oldest}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    raw = urllib.request.urlopen(req, timeout=20).read()
    # Strip raw control chars that break json.loads
    clean = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', raw)
    return json.loads(clean.decode('utf-8','replace'))

tier1 = [
    "D0AFTLEJGJU",   # jeffrey-dm
    "C0AH3RY3DK6",   # #worldai
    "C09GRLXF9GR",   # #all-$USER-ai
    "C0BDEAJH8PK",   # #worldai-bugs
    "C0BCVG4F560",   # #worldai-alerts
    "C0AKALZ4CKW",   # #ai-slack-test
    "C0AMM2B4319",   # #life
    "C0BDAMWQQJK",   # #hermes-pc
    "C0AJQ5M0A0Y",   # #ai-general
    "C0A0AG6EELB",   # #mcp-mail
    "C0ALSKLU9KM",   # #agent-orchestrator
    "C0AJ3SD5C79",   # #jleechanclaw
    "C0BA4MCBPFB",   # #agentf
    "C0AQJT7KSP2",   # #ai-universe
]
```

## DM delivery — post to D0AFTLEJGJU

```python
def post_dm(token, channel, text):
    data = json.dumps({"channel": channel, "text": text}).encode()
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
    )
    raw = urllib.request.urlopen(req, timeout=30).read()
    return json.loads(raw.decode('utf-8','replace'))

post_dm(xoxp, "D0AFTLEJGJU", "<brief body>")
```

**Important quirk:** The post will appear **under the MCP Agent Mail bot identity** in the DM because `D0AFTLEJGJU` is the DM channel between $USER and that bot — Slack always renders the conversation-partner's profile, regardless of which token sent the message. Mention this in the brief so the operator understands why the bot's icon shows up.

## Fix the actual problem — invite bot to channels

Until the bot is re-invited, every cron delivering to those channels (`slack:#worldai`, `slack:#life`, etc.) returns `not_in_channel`. Operator-facing fix:

```
/invite @mcp_agent_mail
```

in each of the 14 Tier-1 channels. After invites, `conversations.list` will return the bot as a member and the cron delivery path self-heals. The Hermes-bot-invite recipe is a separate fix from token rotation — they look the same from the cron side (`not_in_channel` errors) but require different remediation steps.

## Verified 2026-07-13

Confirmed working in the 12:00 PDT EA sweep:
- `mcp_agent_mail` bot → 0 channels member
- `SLACK_MCP_XOXP_TOKEN` ($USER) → all 14 Tier-1 channels readable
- `chat.postMessage` to `D0AFTLEJGJU` via xoxp → delivered, ts `1783969410.028419`
- Brief archived at `~/.hermes/memory/briefings/2026-07-13/1200-ea-sweep.md`

## Companion artifacts
- `~/.hermes/skills/executive-assistant/SKILL.md` — pitfall P40 (bot-locked-out, added 2026-07-13)
- `~/.hermes/skills/executive-assistant/references/slack-delivery-dead-recipe.md` — different failure mode (token revoked, fix by token rotation + secret-purge)