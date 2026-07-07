# Bot read-tracking scope gap — why posting ≠ clearing the unread badge

**Symptom (2026-06-23, screenshot from Slack mobile Activity tab):** the `hermes` bot posts a `Slack thread roadmap` message into a thread every 4h. The thread gets replies from Jeffrey. Slack still shows "9+" unread on the `hermes and you` activity entry, even after the bot's most recent reply lands. The unread counter on `#worldai` and `#all-$USER-ai` never drops to zero.

**Root cause:** the bot has `chat:write` (can post messages) but does **NOT** have `channels:write` (or `groups:write` / `mpim:write` / `im:write` for private channels). Posting a message and clearing the unread badge are **two different API endpoints with two different scopes**:

| Action | Endpoint | Required scope |
|---|---|---|
| Post a message | `chat.postMessage` | `chat:write` |
| Mark channel read up to ts | `conversations.mark` | `channels:write` (public), `groups:write` (private), `mpim:write` (group DM), `im:write` (DM) |

`conversations.mark` returns `{"ok":false,"error":"missing_scope"}` if any of those are missing. Verified 2026-06-23 on `C0AH3RY3DK6` (worldai) with `ts=1782276005.401719` → `missing_scope`.

**`chat.mark_as_read`** is a deprecated 404 endpoint — Slack removed it years ago. `users.markConversation` doesn't exist.

**Two fixes:**

## A. Add scopes to the Slack app (permanent, 30s)

In Slack admin UI: `https://api.slack.com/apps/A0AESRKA7L3/oauth`
1. **OAuth & Permissions** → **Bot Token Scopes** → **Add Scope**: `channels:write`, `groups:write`, `mpim:write`, `im:write`
2. **Reinstall to Workspace** (top of page, after adding scopes — installing without reinstalling does nothing; the bot's currently-issued token does NOT auto-pick up the new scopes)
3. Wait for the new `xoxb-...` token to appear in the "Bot User OAuth Token" field; copy it to `~/.bashrc` (`HERMES_SLACK_BOT_TOKEN`)
4. `launchctl bootout gui/$(id -u)/ai.openclaw.gateway` then `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.openclaw.gateway.plist` (or whichever service holds the env)

**Alternative if no Slack admin UI access:** needs the workspace OWNER or an admin-level Slack API token with `app_configurations:write` scope. The bot itself can't request this — `apps.manifest.update` returns `not_allowed_token_type` for bot tokens, `missing_scope` for the user's normal xoxp token.

## B. Mark-after-post in the dropped-thread cron (after fix A)

Once the scope is added, every `chat.postMessage` in the cron should be followed by:

```bash
LATEST_TS=<ts-from-postMessage-response>
curl -s -X POST "https://slack.com/api/conversations.mark" \
  -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "channel=${CHANNEL_ID}" \
  --data-urlencode "ts=${LATEST_TS}"
```

Note: `ts` must be a real Slack message timestamp (e.g., `1782276005.401719`), NOT a Unix epoch. `invalid_timestamp` if you pass raw seconds. Get it from `conversations.history` or from the response of `chat.postMessage`.

## When this is OK to ignore

- **Bot doesn't post in the channel.** If the bot only listens (`event_subscriptions`) and never posts, no mark is needed.
- **Badge isn't user-facing.** If the badge is only on the bot's own user account (it isn't — `last_read` is per-user, not per-bot), doesn't matter.
- **You don't care about the bot's unread counter.** Some teams treat the bot's badge as noise and ignore it.

## When this is NOT OK to ignore

- **Jeffrey sees the badge on his phone.** This is the failure mode that prompted this doc — the screenshot showed 6 unread `hermes and you` entries with 9+ badges.
- **Other users see the same badge.** Same root cause for anyone the bot DMs or posts in threads with.

## Pattern extension: any "post-and-tracker" agent

This is the same trap for any agent that both posts AND tracks unread state: Linear auto-posting bots, GitHub PR-comment bots that DM the user, Notion automation bots. Post scope ≠ tracking scope. Audit the full scope list when adding a new action.
