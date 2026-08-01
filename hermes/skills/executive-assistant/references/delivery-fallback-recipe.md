# Delivery Fallback Recipe — Bot-Locked-Out Channels

**Use when:** the destination channel is one the bot is NOT a member of (e.g. `#ai-general` `C0AJQ5M0A0Y`, `#worldai-alerts` `C0BCVG4F560`, any non-home-workspace channel) and `mcp__slack__conversations_add_message` returns `{"error": "not_in_channel"}`.

**Source session:** 2026-07-20 20:01 PT executive-assistant sweep. User explicitly asked to deliver to `#ai-general` (NOT the operator's DM). Bot was locked out. Fallback via xoxp user-token worked end-to-end and posted ts `1784603066.611469` to channel `C0AJQ5M0A0Y`.

---

## Why the bot is locked out (channel scope)

The hermes Slack bot (`HERMES_SLACK_BOT_TOKEN`) is added to channels only when explicitly invited. `not_in_channel` on a `chat.postMessage` attempt means the bot token's `chat:write` scope is workspace-wide but the channel itself is outside the bot's `conversations.connect` scope. The xoxp user token (`SLACK_MCP_XOXP_TOKEN`) is per-user and crosses channel boundaries the bot cannot.

## The verified recipe

```bash
# Step 1: write the payload to a file (avoids shell-quote hell with newlines/quotes/markdown)
python3 -c "
import json
payload = {
    'channel': 'C0AJQ5M0A0Y',   # <channel-id>
    'text': '''<the markdown brief text>'''
}
with open('/tmp/ea_payload.json', 'w') as f:
    json.dump(payload, f)
"

# Step 2: post via login-shell-sourced xoxp token
bash -lc '
TOKEN="${SLACK_MCP_XOXP_TOKEN:-${SLACK_USER_TOKEN:-}}"
if [ -z "$TOKEN" ]; then echo "MISSING_TOKEN"; exit 1; fi
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @/tmp/ea_payload.json
'
```

## Critical env-var trap

`SLACK_USER_TOKEN` is **NOT** exported by a plain `bash -c` invocation — `~/.bashrc` and `~/.profile` are not sourced. The hermes-skill environment uses these token names:

| Env var | Source | What it is |
|---|---|---|
| `SLACK_MCP_XOXP_TOKEN` | `~/.bashrc` | xoxp user token ($USER) — use for cross-channel delivery |
| `SLACK_MCP_XOXB_TOKEN` | `~/.bashrc` | xoxp user token variant (different scopes) |
| `SLACK_BOT_TOKEN` | `~/.bashrc` | hermes Slack bot token — workspace-scoped, will hit `not_in_channel` for non-member channels |
| `HERMES_SLACK_BOT_TOKEN` | `~/.bashrc` | duplicate of SLACK_BOT_TOKEN under different name |
| `SLACK_USER_TOKEN` | not exported | legacy name — `~/.profile` clobbers it; do NOT trust |

**Use `bash -l` (login shell) so `~/.bashrc` + `~/.profile` source correctly.** Verified env from a real login shell on 2026-07-20: 21 SLACK/HERMES vars are exported; in a non-login `bash -c` shell, only `HERMES_HOME`, `HERMES_RPC_SOCKET`, `HERMES_REAL_HOME` survive.

This is the same trap the SOUL.md `bashrc-profile-xapp-drift-blocks-launchd` memory documents. Curl commands that work in the user's interactive shell will silently fail with `MISSING_TOKEN` in cron/agent contexts.

## Pitfall: double JSON-stringifying

A common mistake is to embed `{"channel": ..., "text": ...}` inside a heredoc that then gets `-d` parsed by curl — curl sees a string of literal braces, not JSON, and returns `{"ok":false,"error":"json_not_object"}`. **Always** write the payload to a file with `json.dump()` and use `--data-binary @file.json`. The `--data-binary` flag preserves newlines and unicode (`→` etc.) that `-d "$VAR"` would mangle.

## What the message looks like

The [REDACTED_SLACK_TOKEN] post appears under the workspace's MCP Agent Mail bot identity (`bot_id: B0A450AF9NF` in the jleechanorg workspace, `app_id: A0A3WSV6BM1`) — NOT under your hermes-bot identity. That's fine; the operator knows this is a cron sweep. If you want a clearer visual cue, prefix the brief with a `[Hermes EA Sweep]` tag so the operator can tell at a glance.

## Verification

After post, the response includes `{"ok":true,"channel":"<id>","ts":"<ts>"}` on success. Extract the `ts` for any follow-up cross-checks (`conversations.replies` or threading). On failure, Slack returns `{"ok":false,"error":"<reason>"}` — common reasons:

| Error | Cause | Fix |
|---|---|---|
| `not_in_channel` | bot token not member of channel | use xoxp fallback (this recipe) |
| `not_authed` | token empty or wrong | check `bash -l` sourcing |
| `invalid_auth` | token revoked | rotate via launchd-env-wrapper |
| `channel_not_found` | wrong channel ID | re-resolve via `channels_list` |
| `msg_too_long` | text >40000 chars | split into threaded reply chain |
| `rate_limited` | too many posts | back off; use `Retry-After` header |

## Companion references

- SOUL.md `slack-cross-workspace-fallback-xoxp` COMMIT — canonical rule this recipe implements
- SOUL.md `slack-channel-routing-policy` COMMIT — channel selection rules for cron vs user-originated briefs
- SOUL.md `bashrc-profile-xapp-drift-blocks-launchd` memory — why `bash -l` matters for cron
- `references/asymmetric-bot-channel-access.md` — bot-locked-out read-side companion (this file is the write-side)
- `references/bot-locked-out-dedup-probe.md` — distinguish "no prior brief" from "bot can't read DM"
