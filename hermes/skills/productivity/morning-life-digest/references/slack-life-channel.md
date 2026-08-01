# Slack #life Channel + Posting

Captured 2026-07-22.

## Channel

- `#life` → `C0AMM2B4319` (per `~/.hermes/cron/jobs.json` `deliver` field)
- Other recurring life crons also use this same channel ID:
  `life:cindil-immigration-daily-9am`, `life:honda-civic-dmv-setup-hourly`,
  `life:renew-car-registration-hourly`,
  `life:mizraim-register-pa-daily-9am`, `cindil-protein-reminder-am/pm`

## Bot identity

Posting via `HERMES_SLACK_BOT_TOKEN` lands as `MCP Agent Mail`
(`U0A4G7LDJ4R`, `B0A3MS7G08P`, app `A0A3WSV6BM1`). This is the operator-facing
identity for the gateway — fine for life-channel routine digests.

## Token sourcing chain

In priority order:

1. **`~/.bashrc`** (sourced in non-interactive shell):
   ```bash
   TOKEN=$(bash -c 'source ~/.bashrc 2>/dev/null; echo -n "$HERMES_SLACK_BOT_TOKEN"' 2>/dev/null | tr -d '"')
   ```
2. **macOS keyring** (fallback if `.bashrc` doesn't export it):
   ```bash
   TOKEN=$(security find-generic-password -s "HERMES_SLACK_BOT_TOKEN" -w)
   ```

Token is `xoxb-...` format, length 58. Confirmed working 2026-07-22.

⚠️ Memory `bashrc-profile-xapp-drift-blocks-launchd` — `.profile` may
overwrite bashrc-sourced values in launchd context. The .bashrc read happens
in the assistant session, which IS interactive, so this should be fine. If
you see "invalid_auth" from Slack, fall back to keyring.

## Full post recipe

```bash
TOKEN=$(bash -c 'source ~/.bashrc 2>/dev/null; echo -n "$HERMES_SLACK_BOT_TOKEN"' 2>/dev/null | tr -d '"')

# /tmp/digest.txt contains the markdown body
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary "$(python3 -c "import json; print(json.dumps({'channel':'C0AMM2B4319','text':open('/tmp/digest.txt').read()}))")"
```

## `deliver: "origin"` semantics

When a cron's `deliver` field is `"origin"` (not `slack:<CHAN>`), the cron
runtime captures the assistant's final reply text and routes it back to the
originating session/thread. For `life:*` crons that's the gateway itself —
so the digest content is also implicitly delivered. BUT the cron prompt
explicitly says "post a concise digest in #life" — meaning you must also
post to Slack as a side effect. Both are required.

## What NOT to do

- Don't use `mcp__slack__conversations_add_message` from a cron context —
  the MCP server isn't reachable inside gateway cron session.
- Don't route to `#all-$USER-ai` (`C09GRLXF9GR`) — that's the operator-Hermes
  DM channel, not the daily-brief channel.
- Don't include `MEDIA:` tokens for screenshot evidence — this digest has
  none, but if extending, use the 3-stage `files.completeUploadExternal`
  recipe per `~/.hermes/skills/evidence-attach-to-slack/`.
