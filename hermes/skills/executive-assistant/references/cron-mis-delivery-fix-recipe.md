# Cron Mis-Delivery Fix Recipe

**Context:** A `hermes cron` job is delivering to the wrong Slack channel. Common case: an EA-sweep or status cron was set up to deliver to a low-traffic channel (`#life`, `#general`, etc.) but the operator actually wants the brief in their DM.

## Verify the mis-wiring

```bash
hermes cron list
```

Find the cron by name or id. Read the `Deliver:` line:

```
  a790a5b54e61 [active]
    Name:      clawchief:ea-sweep-hourly
    Schedule:  0 8,12,16,20 * * *
    Repeat:    ∞
    Deliver:   slack:C0AMM2B4319    ← WRONG (this is #life, not the DM)
    Last run:  2026-07-15T08:04:19.003295-07:00  ok
```

If `Deliver:` doesn't start with `slack:D` (a DM channel id), it's mis-wired.

## Resolve the live DM channel id

```bash
# Re-resolve every time — bashrc JLEECHAN_DM_CHANNEL is stale (frozen at revoked hermes bot DM)
curl -sS -X POST -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"users":"U09GH5BR3QU"}' \
  https://slack.com/api/conversations.open | jq .channel.id
```

Live DM id (verified 2026-07-14 → 2026-07-15): `D0A418NEHHC`. If this ever changes, re-resolve and update this file.

## Fix in place — DO NOT recreate

```bash
hermes cron edit <JOB_ID> --deliver slack:D<DM_CHANNEL_ID>
```

Concrete worked example (2026-07-15 12:04 PT sweep):

```bash
hermes cron edit a790a5b54e61 --deliver slack:D0A418NEHHC
```

Output:
```
Updated job: a790a5b54e61
  Name: clawchief:ea-sweep-hourly
  Schedule: 0 8,12,16,20 * * *
  Skills: none
```

## Verify

```bash
hermes cron list | grep -A 8 <JOB_ID>
```

`Deliver:` line should now read `slack:D<DM_CHANNEL_ID>`. Wait for the next scheduled tick (visible in `Next run:` line) and confirm the message lands in DM, not the wrong channel.

## Why not just recreate the cron?

`hermes cron create` accepts `--name`, `--schedule`, `--deliver`, `--repeat`, `--skill`, `--script`, etc. — but if the original cron had a complex `--prompt` (multi-line instruction) or `--skill` attachments, recreating from scratch is lossy. `hermes cron edit` preserves the prompt/skills/script and only swaps the flagged fields. **Always prefer `edit` over `create + remove`** for delivery-target fixes.

## When DM channel id itself is the problem

If `conversations.open` returns a different DM id than expected, the bot may have been rotated. Cross-check:
- `auth.test` returns `ok=true` and `team=$USER AI`
- The bot identity (`mcp_agent_mail`, user_id `U0A4G7LDJ4R`) can post to DMs (DMs are user-to-bot, not channel-scoped, so `not_in_channel` does not apply)
- If `chat.postMessage` to the resolved DM returns `account_inactive` / `token_revoked`, the bot token is dead — fall back to xoxp user token (`SLACK_MCP_XOXP_TOKEN`) per `slack-cross-workspace-fallback-xoxp` SOUL.md commit. Verify the post landed via `conversations.history` regardless of which token was used.

## Related pitfalls

- SOUL.md `slack-channel-routing-policy` — home channel vs operator-direct channel routing
- SOUL.md `slack-cross-workspace-fallback-xoxp` — xoxp fallback when bot token is dead
- Executive-assistant SKILL.md P40/P41 — token-revoked dead-DM recipe
- Executive-assistant SKILL.md P37 — original mis-delivery bug (now superseded by this recipe)