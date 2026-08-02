# Environment & Channel Mapping

Verified against `~/.bashrc` and the active launchd-env-wrapper on **2026-07-14 16:02 PT**. This is the canonical source for variable lookups in the executive-assistant sweep. Re-verify once per quarter or after a Hermes deploy.

**WARNING — `JLEECHAN_DM_CHANNEL` in `~/.bashrc` is STALE.** As of 2026-07-14 16:02 PT, bashrc still exports `JLEECHAN_DM_CHANNEL=D0AFTLEJGJU`, but that channel is the DM with the **revoked** `hermes` bot (`U0AEZC7RX1Q`) and returns `{"ok":false,"error":"channel_not_found"}` from the live `mcp_agent_mail` bot's token. **The live DM is `D0A418NEHHC`.** Do not trust `$JLEECHAN_DM_CHANNEL` — always re-resolve via `conversations.open()` at the top of every sweep.

## Environment variables (set in `~/.bashrc`, loaded via launchd-env-wrapper)

```bash
# Resolve these once at the top of each run:
bash -lc 'source ~/.bashrc && env | grep -iE "EMAIL|JLEE|HERMES"'
```

| Variable | Status as of 2026-07-14 | Notes |
|---|---|---|
| `EMAIL_USER` | `$USER@gmail.com` ✅ | Primary Gmail for `gog -a` |
| `BACKUP_EMAIL` | `$USER@gmail.com` ✅ | (same) |
| `JLEECHAN_DM_CHANNEL` | **`D0AFTLEJGJU`** ⚠️ **STALE — DO NOT TRUST** | This was the DM with the **revoked** `hermes` bot. The live bot (`mcp_agent_mail` / `U0A4G7LDJ4R`) opens a **different** DM: `D0A418NEHHC`. Re-resolve at sweep start via `conversations.open(users=U09GH5BR3QU)`. |
| `JLEECHAN_SLACK_USER_ID` | `U09GH5BR3QU` ✅ | Jeffrey's user id (filter bot vs human in `conversations_history`) |
| `HERMES_BOT_USER_ID` | unset / stale | **Do not use the bashrc value.** The current live bot user is `U0A4G7LDJ4R`. Resolve via `auth.test` at sweep start; expect this to rotate again. |
| `HERMES_SLACK_BOT_TOKEN` | alive ✅ | Source from `source ~/.bashrc && echo $HERMES_SLACK_BOT_TOKEN`. Verify with `auth.test`; the 2026-07-14 prefix is `xoxb-...`. Cross-validate with `conversations.list` if `auth.test` returns transient `invalid_auth` (see SKILL.md P43). |
| `SLACK_MCP_XOXP_TOKEN` | alive ✅ | `xoxp-9...` for $USER. **This is the cross-workspace + locked-out-bot fallback** (SKILL.md P40, P91, P94, plus `slack-cross-workspace-fallback-xoxp` SOUL.md COMMIT). When the bot is locked out of channels or its token is post-rotation stale, use xoxp for reads AND `chat.postMessage` to the operator DM. The DM post will appear under the live bot's identity because `D0A418NEHHC` is a $USER↔bot DM. |
| `SLACK_MCP_MAIL_WEBHOOK_URL` | (per-bashrc) | For mcp-mail agent — see separate `mcp-mail` skill |
| `GOG_KEYRING_PASSWORD` | `hermes-gog-2026` ✅ | OAuth client — do NOT print; just pass through to gog |
| `TIMEZONE` | (not set) | OS default America/Los_Angeles — confirm with `date` |

**Notably ABSENT** (don't waste time probing):
- `OWNER_NAME` — not set; hardcode "Jeffrey"
- `ASSISTANT_EMAIL` — not set; use `EMAIL_USER`
- `PERSONAL_EMAIL` / `PRIMARY_WORK_EMAIL` — not set; only `$USER@gmail.com` exists in this profile

## Slack channel mapping (verified 2026-07-14 16:02 PT)

| Channel | ID | Why monitor | Bot-in-channel? (2026-07-14) |
|---|---|---|---|
| `#worldai` | `C0AH3RY3DK6` | Primary product PRs + AO babysit threads | ❌ `not_in_channel` — use xoxp or invite bot |
| `#worldai-bugs` | `C0BDEAJH8PK` | Long-running bug investigations (cost consolidation, etc.) | ✅ bot reads fine via xoxb |
| `#ai-slack-test` | `C0AKALZ4CKW` | agento respawn-cap escalations; PR-test failures | varies |
| `#all-$USER-ai` | `C09GRLXF9GR` | Direct operator-Hermes line (per `slack-channel-routing-policy`) | ❌ `not_in_channel` — use xoxp or invite bot |
| `#jleechanclaw` | `C0AJ3SD5C79` | Harness / SOUL.md / skill / workflow work | ✅ bot reads fine via xoxb |
| `#life` | `C0AMM2B4319` | Personal reminders (Cindil protein AM/PM, etc.) | ❌ `not_in_channel` — use xoxp or invite bot |
| `#mcp-mail` | `C0A0AG6EELB` | MCP Agent Mail session-complete updates | ✅ bot reads fine via xoxb |
| `#agent-orchestrator` | `C0ALSKLU9KM` | AO worker reports (usually low-traffic) | ❌ `not_in_channel` — use xoxp or invite bot |
| `#ai-general` | `C0AJQ5M0A0Y` | Home channel — system reports (cmux Surface Report, dropped-thread alerts, etc.) | varies |
| Jeffrey's DM | **`D0A418NEHHC`** ✅ LIVE | Brief destination | ✅ current live DM (2026-07-14) |
| (DEPRECATED) Jeffrey's old DM | ~~`D0AFTLEJGJU`~~ | Revoked `hermes` bot's DM | ❌ `channel_not_found` from current token |

For `@hermes` PR-tag auto-routing per repo, see `hermes-tag-webhook-per-repo-routing` COMMIT — most `jleechanorg/*` repos auto-route to `#worldai`, `#jleechanclaw`, `#agent-orchestrator`, etc., based on repo name.

## Gmail search recipes

```bash
# Starred only
gog gmail search "is:starred" -a $USER@gmail.com --max=20 --json --results-only

# Important unread last 24h
gog gmail search "is:important newer_than:1d" -a $USER@gmail.com --max=20 --json --results-only

# Unread last 24h, human senders only (recommended)
gog gmail search "is:unread newer_than:1d \
  -from:$USER -from:noreply -from:no-reply -from:no_reply \
  -from:donotreply -from:support -from:notifications -from:notification \
  -from:auto-confirm -from:alerts -from:newsletter -from:reports -from:daily -from:bot" \
  -a $USER@gmail.com --max=30 --json --results-only

# Get a specific message body — try thread get first, fall back to get
gog gmail thread get <threadId> -a $USER@gmail.com 2>&1
# If that errors, try:
gog gmail get <messageId> -a $USER@gmail.com --format full
```

**Pitfall — `gog gmail search` returns a top-level JSON ARRAY, not `{threads: [...], nextPageToken}`** (added 2026-07-13, re-verified 2026-07-14): iterate the array directly with `for it in data: ...`. Calling `.get("threads", [])` on the result throws `AttributeError: 'list' object has no attribute 'get'`.

**Pitfall — `--max` is per-thread, not per-message.** A thread with `messageCount: 9` (e.g. Cindil delayed regi…) counts as 1.

## Local probe commands

```bash
uptime                                                     # load avg
df -h / | head -3                                          # disk
ps aux | grep -E '(hermes|agy|claude|cmux)' | grep -v grep | wc -l
launchctl print gui/$(id -u) 2>/dev/null | grep -E '(dropped-thread|ao-notifier|auto-push-llm-wiki)' | head -10
```

## Cron cadence observations

The `ai.hermes.schedule.executive-assistant` cron fires on a schedule. Observed run timestamps in `#jleechanclaw`-operator DM (D0AFTLEJGJU, now DEPRECATED) for 2026-07-04:

| Run | PDT | Type |
|---|---|---|
| 1 | 08:01 | Full morning brief |
| 2 | 11:09 | Full brief |
| 3 | 12:01 | Full mid-day brief |
| 4 | 12:43 | **Delta brief** (this run — verified cadence + new tooling) |

Expected cadence on weekdays is typically 07:00 / 12:00 / 18:00 PDT (3x daily). Weekends observed at ~1.5h intervals.

**2026-07-14 16:04 PT observation:** 1194 min since last brief (~20h gap). The 8:25 PT and 12:07 PT cron firings from the prior day landed in `#life` (delivery target was `slack:C0AMM2B4319` which the new bot can't post to). The 16:04 PT run was the first sweep to land in the live DM `D0A418NEHHC` since the bot rotation. The cron job's `deliver` field still points to `#life` (misroute) — fix is `hermes cron edit <job_id> --deliver slack:D0A418NEHHC` (or recreate with correct deliver).

## Pitfalls

- `gog` requires the keyring password (`GOG_KEYRING_PASSWORD`); if the keyring is locked, `gog` will prompt and block — preflight with `security find-generic-password -s hermes-gog-2026 -w` if uncertain.
- Slack MCP is workspace-scoped to the hermes bot's home workspace. For cross-workspace channels (rare; mostly Vendelux/Riday recruiters), fall back to the `SLACK_USER_TOKEN` XOX-P path per `slack-cross-workspace-fallback-xoxp` COMMIT.
- ~~`JLEECHAN_DM_CHANNEL` is `D0AFTLEJGJU`~~ — **DEPRECATED 2026-07-12, re-confirmed 2026-07-14.** The `hermes` bot (owner `U0AEZC7RX1Q`) was revoked by Slack after its token was found in `jleechanorg/claude-commands` commit `10ca1b09`. Current DM is **`D0A418NEHHC`** with the `mcp_agent_mail` bot (`U0A4G7LDJ4R`). Confirm via `conversations.open(users=U09GH5BR3QU)` — the returned `channel.id` is the live DM for whichever bot is calling. Do NOT trust bashrc's `JLEECHAN_DM_CHANNEL`.
- **Bot identity can rotate between sweeps.** Never hardcode `HERMES_BOT_USER_ID` or `JLEECHAN_DM_CHANNEL`; re-resolve from `auth.test` + `conversations.open()` at the top of every sweep.
- **The new bot is not in all monitored channels.** 2026-07-14 16:02 PT confirmed `not_in_channel` for `#worldai`, `#all-$USER-ai`, `#life`, `#agent-orchestrator`. Use `SLACK_MCP_XOXP_TOKEN` for those reads, OR `/invite @mcp_agent_mail` to fix the underlying problem.

## Bot-identity rotation recovery recipe (2026-07-12 incident, re-verified 2026-07-14)

When the prior sweep failed with `account_inactive` / `token_revoked`, and a cron deliver error shows `live adapter send failed`, follow this recipe **at the very start** of the sweep — before scanning channels:

1. Probe the new token:
   ```bash
   bash -lc 'source ~/.bashrc && curl -fsS -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" https://slack.com/api/auth.test'
   ```
   - `ok=true` → token is alive, proceed.
   - `ok=false` → token is still revoked; write brief to disk + reply with full brief (slack-delivery-dead-recipe.md).
2. Resolve the live operator DM (DO NOT trust bashrc's `JLEECHAN_DM_CHANNEL`):
   ```bash
   bash -lc 'source ~/.bashrc && curl -fsS -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" -H "Content-Type: application/json" \
     -d "{\"users\":\"U09GH5BR3QU\"}" https://slack.com/api/conversations.open'
   ```
   The returned `channel.id` (e.g. `D0A418NEHHC`) is the DM channel for the *current* bot. **Do not trust `JLEECHAN_DM_CHANNEL`** — it is frozen at the moment it was last edited and is currently stale.
3. Verify write path with a one-shot probe before posting the full brief:
   ```python
   import json, urllib.request
   data = json.dumps({"channel": "<DM_ID>", "text": "[ea-probe] <timestamp>"}).encode()
   urllib.request.urlopen(urllib.request.Request(
       "https://slack.com/api/chat.postMessage", data=data,
       headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}))
   ```
4. Verify channel memberships — bot may NOT be in operator-action channels (#worldai, #life, #agent-orchestrator, etc.). If `conversations.history` returns `not_in_channel`, fall back to `SLACK_MCP_XOXP_TOKEN` for those channels (see SKILL.md P40/P91) rather than treating it as a read error.

## Cron deliver target misroute (verified 2026-07-12, persists 2026-07-14)

The cron `clawchief:ea-sweep-hourly` (`a790a5b54e61`) has `deliver: slack:C0AMM2B4319` (#life) — but the current bot isn't a member of #life. The cron engine reports `last_delivery_error: account_inactive` even though the token itself works. **Two failures layered:**
1. Cron targets a channel the bot cannot post to (config drift).
2. Gateway's stored token is pre-rotation (gateway launched 17:47, ~/.bashrc rotated 18:42) → gateway's `apps.connections.open` returns `invalid_auth` even though REST works.

Fix for operator: update the cron job's `deliver` field from `slack:C0AMM2B4319` to `slack:D0A418NEHHC` (the new operator DM). The sweep itself must work around the misroute by posting directly to the resolved DM and relying on the cron reply as a secondary delivery channel. **This is still unfixed as of 2026-07-14 16:04 PT** — the cron continues to misroute to `#life`, and each sweep must manually re-resolve and post to the live DM.

## Cron cadence observations

The `ai.hermes.schedule.executive-assistant` cron fires on a schedule. Observed run timestamps in `#jleechanclaw`-operator DM (D0AFTLEJGJU) for 2026-07-04:

| Run | PDT | Type |
|---|---|---|
| 1 | 08:01 | Full morning brief |
| 2 | 11:09 | Full brief |
| 3 | 12:01 | Full mid-day brief |
| 4 | 12:43 | **Delta brief** (this run — verified cadence + new tooling) |

Expected cadence on weekdays is typically 07:00 / 12:00 / 18:00 PDT (3x daily). Weekends observed at ~1.5h intervals.
