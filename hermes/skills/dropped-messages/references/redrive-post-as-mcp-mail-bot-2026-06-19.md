---
name: dropped-messages/redrive-post-as-mcp-mail-bot-2026-06-19
description: Redrive / dropped-thread summary replies MUST post as MCP mail bot (U0A4G7LDJ4R), NOT Hermes (U0AEZC7RX1Q) — hard user preference. Token resolution, posting recipe, identity verification.
type: reference
---

# Redrive replies MUST post as MCP mail bot (`U0A4G7LDJ4R`), NOT Hermes (`U0AEZC7RX1Q`) — hard user preference (added 2026-06-19)

> **Verified 2026-06-19, `C0AJ3SD5C79/1781868563.343059` "Redrive dropped threads":** Jeffrey's instruction was verbatim: *"remember you can't send meesage as `<@U0AEZC7RX1Q>` because Hermes will not reply. Send as me or `<@U0A4G7LDJ4R>`"*. This is a **hard user preference**, not a one-off routing hint.

## Why this is a class-level rule, not a one-off

Every dropped-thread redrive has the same shape:
- The user is asking for a recovery sweep.
- The thread has been cold for 30+ minutes.
- Hermes is the very identity that's been failing (or that's been silent).

Posting the recovery reply as Hermes (`U0AEZC7RX1Q`) is circular: the user is asking for *non-Hermes* output in a thread where Hermes hasn't replied. Even if the curl succeeds, posting through `HERMES_SLACK_BOT_TOKEN` re-introduces the routing path the user just told you was broken. The MCP mail bot identity (`U0A4G7LDJ4R`) is the canonical "recovery sweeper" identity used by the cron and approved by the user for this exact purpose.

## The rule, encoded

1. **All redrive / dropped-thread summary / "top-N actionable" replies MUST post as MCP mail bot** (`U0A4G7LDJ4R`, bot_id `B0A3MS7G08P`).
2. **Use `MCP_MAIL_BOT_TOKEN` from `~/.mcp_mail/credentials.json`** — NOT `HERMES_SLACK_BOT_TOKEN`, NOT `send_message`.
3. **Use curl `chat.postMessage`** with the MCP mail bot token and explicit `channel` + `thread_ts` in the JSON payload. NOT the `send_message` helper (which routes through Hermes).
4. **The other acceptable identity is `SLACK_USER_TOKEN` (Jeffrey's, `U09GH5BR3QU`)** per Jeffrey's "send as me" wording. Default to MCP mail bot unless the user specifically asks for "as me."

## Identity resolution — verify once per session

```bash
# Map each available token to its Slack identity
echo "=== Hermes ==="
curl -s -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'ok={d.get(\"ok\")} user_id={d.get(\"user_id\")} user={d.get(\"user\")} bot_id={d.get(\"bot_id\")}')"

echo "=== MCP mail ==="
MCP_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.mcp_mail/credentials.json'))['SLACK_BOT_TOKEN'])")
curl -s -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $MCP_TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'ok={d.get(\"ok\")} user_id={d.get(\"user_id\")} user={d.get(\"user\")} bot_id={d.get(\"bot_id\")}')"

echo "=== Jeffrey ==="
curl -s -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'ok={d.get(\"ok\")} user_id={d.get(\"user_id\")} user={d.get(\"user\")} bot_id={d.get(\"bot_id\")}')"
```

Expected:
- Hermes → `user_id=U0AEZC7RX1Q`, `user=hermes`, `bot_id=B0AEHUEA0JK`
- MCP mail → `user_id=U0A4G7LDJ4R`, `user=mcp_agent_mail`, `bot_id=B0A3MS7G08P`
- Jeffrey → `user_id=U09GH5BR3QU`, `user=$USER`, `bot_id=null` (real user, not a bot)

## Posting recipe — curl `chat.postMessage` with explicit `thread_ts`

```python
import subprocess, json, os

creds = json.load(open(os.path.expanduser("~/.mcp_mail/credentials.json")))
token = creds["SLACK_BOT_TOKEN"]   # MCP mail bot, NOT HERMES_SLACK_BOT_TOKEN

payload = {
    "channel": "<chan_id>",
    "thread_ts": "<thread_ts>",
    "text": "<reply_text>",
}

result = subprocess.run([
    "curl", "-s", "-X", "POST", "https://slack.com/api/chat.postMessage",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json; charset=utf-8",
    "-d", json.dumps(payload),
], capture_output=True, text=True, timeout=30)

# Verify: result.stdout should contain `"ok":true`
assert '"ok":true' in result.stdout, f"Slack API error: {result.stdout}"
# Extract ts to confirm where it landed
import re
m = re.search(r'"ts":"([0-9.]+)"', result.stdout)
posted_ts = m.group(1) if m else None
print(f"Posted as MCP mail bot to {payload['channel']} thread={payload['thread_ts']} ts={posted_ts}")
```

## What "send as MCP mail bot" actually means under the hood

The Slack API treats `chat.postMessage` auth as the posting identity. `Authorization: Bearer <MCP_MAIL_BOT_TOKEN>` posts AS `U0A4G7LDJ4R`, regardless of what channel the call originates from. The `username` field in the payload is decorative (it overrides the display name but not the auth identity). Use the auth token, not the `username` field.

## Anti-patterns (don't do)

- **Use `send_message target="slack:C0AJ3SD5C79:1781868563.343059"`** — this routes through Hermes (`U0AEZC7RX1Q`), the very identity the user said won't reply. The `send_message` 3-part-target misroute is documented separately in `slack-messaging`, but for redrive replies the identity is the blocker, not the routing.
- **Use `HERMES_SLACK_BOT_TOKEN` directly with curl** — same identity failure.
- **Use `SLACK_USER_TOKEN` (Jeffrey's) by default** — posts as the human, not the bot. Acceptable per Jeffrey's instruction ("send as me") but default to MCP mail bot for cron-consistent attribution.
- **Set `username=Jeffrey` or `username=me` in the curl payload** — this only changes the display name; the auth identity is still whatever token you used.

## Verified 2026-06-19

The redrive reply for `C0AJ3SD5C79/1781868563.343059` posted at `ts=1781869211.259489` as `U0A4G7LDJ4R` (MCP Agent Mail, bot_id `B0A3MS7G08P`). Verified via `conversations_replies` — the post shows `bot_id=B0A3MS7G08P` in the message metadata. A narration-leak sibling from Hermes (`ts=1781869211.255039`) was unavoidable from the gateway side but the canonical redrive is the MCP mail bot post.

## Cross-reference

- `slack-messaging` → "Pitfall: `send_message` helper's `target` ignored thread_ts" — separate failure mode (routing), but the redrive reply also must NOT use `send_message` for the identity reason above.
- `slack-thread-routing-investigation` — Failure 4 (narration-leak) explains why the Hermes sibling post lands. Mitigation for redrive: post via MCP mail bot from the start so the canonical post is non-Hermes.

## When to use which identity (decision table)

| Use case | Identity | Token |
|---|---|---|
| Redrive / dropped-thread sweep reply | MCP mail bot (`U0A4G7LDJ4R`) | `~/.mcp_mail/credentials.json` |
| `mcp_agent_mail` cron notifications | MCP mail bot (`U0A4G7LDJ4R`) | same |
| Normal Hermes reply (in-thread, non-redrive) | Hermes (`U0AEZC7RX1Q`) | `$HERMES_SLACK_BOT_TOKEN` |
| User explicitly says "send as me" / "post as Jeffrey" | Jeffrey (`U09GH5BR3QU`) | `$SLACK_USER_TOKEN` |
| Cross-post / mirror to other channel | Match the source context (Hermes for normal, MCP for redrive) | match source |