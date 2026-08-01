# Bot-Locked-Out Dedup Probe Recipe

## Trigger

`conversations.history(channel_id=D0AFTLEJGJU, limit=5)` returns `{"ok":false,"error":"channel_not_found"}` — and you are about to conclude "no prior brief, post now". **Do not.** That response is a bot-lockout signal, not a clean dedup hit. The same empty-bucket shape is produced by both "no recent brief" and "bot can't see DM" — they look identical to a naive `if not msgs` check.

## Symptom signature

```json
{"ok": false, "error": "channel_not_found", "warning": "missing_charset"}
```

This is the same lockout class as SKILL.md P40 (bot in workspace, member of zero channels), but applied to the **DM** specifically. `conversations.list` will also return `{"ok":true,"channels":[]}` (empty). All `conversations.history` calls return `not_in_channel` for public channels too.

## Why the naive check fails

```python
# WRONG — does not distinguish "no brief" from "bot locked out"
dm_hist = call_slack('conversations.history', {'channel': DM, 'limit': 5})
if not dm_hist.get('messages'):
    post_brief()  # ← blindly re-posts even if xoxp delivered 3 min ago
```

A cron tick that just delivered via xoxp (because the bot couldn't see the DM) will see `messages=[]` and the bot view too — and dutifully post a duplicate.

## The correct probe

```python
import subprocess, json, urllib.request, re

BOT_TOKEN  = subprocess.run(['bash','-lc','source ~/.bashrc && echo "$HERMES_SLACK_BOT_TOKEN"'], capture_output=True, text=True).stdout.strip()
XOXP_TOKEN = subprocess.run(['bash','-lc','source ~/.bashrc && echo "$SLACK_MCP_XOXP_TOKEN"'],    capture_output=True, text=True).stdout.strip()
DM = 'D0AFTLEJGJU'

def call_slack(method, body, token):
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type":"application/json"},
    )
    raw = urllib.request.urlopen(req, timeout=30).read()
    clean = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', raw)
    return json.loads(clean.decode('utf-8','replace'))

# Step 1: probe with bot token
bot_dm = call_slack('conversations.history', {'channel': DM, 'limit': 5}, BOT_TOKEN)

if bot_dm.get('ok') and not bot_dm.get('error'):
    # Bot can read the DM — normal path
    last_brief = bot_dm.get('messages', [{}])[0]
    age_min = (now_ts - last_brief.get('ts', '0')) / 60
    if age_min < 30 and 'brief-like markers' in last_brief.get('text', ''):
        return 'SILENT'  # dedup hit
elif bot_dm.get('error') == 'channel_not_found':
    # Step 2: bot locked out — re-probe with xoxp
    xoxp_dm = call_slack('conversations.history', {'channel': DM, 'limit': 5}, XOXP_TOKEN)
    if xoxp_dm.get('ok'):
        last_brief = xoxp_dm.get('messages', [{}])[0]
        # xoxp sees what the bot can't — trust this for dedup
        # and use xoxp for the post itself
        return post_brief(token=XOXP_TOKEN, note='xoxp fallback: bot locked out of DM')
    else:
        # Both tokens dead — fall back to cron-reply delivery
        return write_brief_to_file_and_return_as_cron_reply()
```

## What to put in the brief footer

Always include a `Dedup:` line so the operator can verify independently:

```
Dedup: last_brief=4.2min ago via xoxp | this run = new (bot → DM returned channel_not_found, xoxp probe OK)
```

If xoxp fallback was used, also surface the lockout problem so the operator knows the bot still needs `/invite` in each monitored channel:

```
Bot note — mcp_agent_mail bot cannot read DM D0AFTLEJGJU (channel_not_found). This brief is being delivered via xoxp fallback ($USER user token) so it appears under your identity, not the bot's. The bot-invite problem is still open.
```

## Worked example: 2026-07-14 08:02 PT sweep

1. `conversations.history(D0AFTLEJGJU, limit=5)` with `$HERMES_SLACK_BOT_TOKEN` → `{"ok":false,"error":"channel_not_found"}`
2. Re-probe with `$SLACK_MCP_XOXP_TOKEN` → `{"ok":true,"messages":[]}` (clean — actually no prior brief in the window)
3. Post the brief via xoxp `chat.postMessage` to `D0AFTLEJGJU` — message appears under bot identity in the DM (because `D0AFTLEJGJU` is the $USER↔mcp_agent_mail DM; Slack renders the bot's profile in that DM regardless of which token sent the message)
4. Footer: `Dedup: last_brief=none in 30min window via xoxp | this run = new (bot → DM returned channel_not_found, xoxp probe clean)`

## Why this matters

Without the `ok` + `error` check, the cron will double-post on every tick that the bot is locked out — 4 ticks per day at the current `0 8,12,16,20 * * *` schedule = 4 duplicate briefs/day, each one a 2-4 KB DM message diluting the signal of the canonical brief. Verified 2026-07-14 08:02 PT: the probe caught the lockout cleanly, the xoxp fallback worked, and the brief landed once.

## Related pitfalls

- SKILL.md P40 — bot locked out of all channels (general case)
- SKILL.md P41 — this specific case for the DM channel + dedup probe
- SKILL.md P37 — Slack API JSON control-char workaround (needed for any curl path)
- SKILL.md P44 — always cite the dedup result in the brief footer
- `references/slack-delivery-dead-recipe.md` — full token-revocation fallback (distinct failure mode from lockout)
