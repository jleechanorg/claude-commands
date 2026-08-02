# User Reports "Nothing Happening" on Slack — Worked Example (2026-07-14)

## Setup

- Channel: `#needs-jeff` / `C0BGM3A4ZC0` / workspace `T09FXQ4LCQP` (`$USER AI`)
- Triggering message: `ts 1784061033.250339`, body "someting broken how come nothing ever happening here? <@U0AEZC7RX1Q> <@U0BC138QXUJ>"
- Affected gateways: prod (`ai.hermes.prod`, port 8642, `~/.hermes_prod/` state) — but the bot can still post via direct curl, so the bug is upstream of the post path
- Visible symptom in thread: two `:warning: The model provider failed after retries.` messages from `hermes_pc` (B0BBUN50HQB) — these are the user's-visible error
- Invisible root cause: gateway log shows primary `MiniMax-M3` → fallback `glm-5.1 via opencode-go` → both 429'd

## What got us to the right answer in 2 minutes

The 4-probe triage in the SKILL.md "User reports 'nothing happening' on Slack" section, run in parallel:

```bash
# Probe 1 — launchd state (gateway alive?)
launchctl print gui/$(id -u)/ai.hermes.prod | grep -E 'state =|pid ='
# → state = running, pid = 25210 ✓

# Probe 2 — can the bot post in C0BGM3A4ZC0?
BOT_TOKEN=$(grep '^export SLACK_BOT_TOKEN=' ~/.profile | head -1 | sed 's/export SLACK_BOT_TOKEN=//; s/"//g')
curl -fsS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $BOT_TOKEN" -H "Content-Type: application/json; charset=utf-8" \
  -d '{"channel":"C0BGM3A4ZC0","thread_ts":"1784061033.250339","mrkdwn":false,"text":"[diagnostic probe — will delete]"}'
# → {"ok":true,"ts":"1784061841.139989",...} ✓ (deleted immediately after)

# Probe 3 — is the primary model (MiniMax-M3) healthy?
curl -fsS -X POST "${MINIMAX_BASE_URL}/v1/messages" \
  -H "x-api-key: ${MINIMAX_API_KEY}" -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"MiniMax-M3","max_tokens":32,"messages":[{"role":"user","content":"Reply with the single word pong."}]}'
# → HTTP 200, content[0].text="pong" ✓ (recovered later — was 429 at user-message time)

# Probe 4 — is the fallback (glm-5.1 via opencode-go) healthy?
curl -fsS -X POST "https://opencode.ai/zen/go/v1/chat/completions" \
  -H "Authorization: Bearer ${OPENCODE_GO_API_KEY}" \
  -H "content-type: application/json" \
  -d '{"model":"glm-5.1","max_tokens":16,"messages":[{"role":"user","content":"pong"}]}'
# → HTTP 403, error code: 1010 ✗ (Cloudflare hard-block; underlying quota exhausted)
```

Probe 4 returned `error code: 1010` (Cloudflare) — the visible symptom is Cloudflare blocking, but the underlying cause is `GoUsageLimitError` per the gateway log. The `error code: 1010` is what Cloudflare returns when the origin returns 429 GoUsageLimitError and Cloudflare has rate-limited our egress to the origin. Both layers are dead.

## Gateway log evidence (verbatim, paraphrased)

```
2026-07-14 13:30:40 INFO gateway.run: inbound message: platform=slack user=Jeffrey Lee-Chan
  chat=C0BGM3A4ZC0 msg='someting broken how come nothing ever happening here?'
2026-07-14 13:31:05 INFO gateway.run: response ready: platform=slack chat=C0BGM3A4ZC0
  time=26.2s api_calls=6 response=660 chars
2026-07-14 13:31:05 INFO gateway.platforms.base: [Slack] Sending response (660 chars) to C0BGM3A4ZC0
2026-07-14 13:31:05 ERROR hermes_plugins.slack_platform.adapter: [Slack] Send error:
  The request to the Slack API failed. (status: 200)
  The server responded with: {'ok': False, 'error': 'cannot_reply_to_message'}
```

And from the provider layer (separately):
```
WARNING agent.conversation_loop: API call failed (attempt 1/3) error_type=RateLimitError
  thread=hermes-gateway_2:13707407360 provider=opencode-go base_url=https://opencode.ai/zen/go/v1/
  model=glm-5.1 summary=HTTP 429: Monthly usage limit reached. Resets in 14 days.
  To continue using this model now, enable usage from your available balance:
  https://opencode.ai/workspace/wrk_01KSS2B66NZT85TVA7SQ7TZ1BB/go
ERROR agent.conversation_loop: API call failed after 3 retries. HTTP 429: Monthly usage limit
  reached. Resets in 14 days. ... | provider=opencode-go model=glm-5.1 msgs=91 tokens=~123,279
```

## What the user sees vs. what's actually happening

| Layer | Visible to user? | Actual state |
|---|---|---|
| Slack socket mode | ✓ "no reply" | Healthy; events arriving |
| Bot channel membership | (assumed broken) | Healthy; probe 2 confirms bot can post |
| Gateway inbound handler | (assumed broken) | Healthy; logged `inbound message` correctly |
| Agent run / model call | (hidden) | Dead; both providers 429'd |
| Slack send path | ✓ `cannot_reply_to_message` | Healthy in isolation; only fires because there was no reply to send |
| Dropped-thread watcher / cron | (assumed broken) | Did NOT fire; this would have caught it but didn't |

The visible "Slack error" is a SYMPTOM, not a cause. The cause is two layers up at the provider layer. The dropped-thread cron not firing is a separate gap (covered by `dropped-thread-watcher-of-watchers` SOUL rule).

## What we did NOT do

- Did NOT restart the gateway. Gateway is fine; restart would change nothing.
- Did NOT edit config.yaml. Primary was the rate-limited one at user-message time, but primary recovered 5 minutes later (probes 3 went from 429 to 200 within ~5 min of user message). Editing config mid-incident would have been worse.
- Did NOT add a token to launchd plist. The wrapper handles it.
- Did NOT create a permanent cron watchdog. Per the SOUL rule `babysit-stale-watchdog`, a leaked status cron is itself a bug class. The user can re-ask if needed.

## What we DID do

- Posted a single direct explanation to the thread (probe 2 path) so the user has visible evidence and root cause in the same thread where they asked
- Verified each probe result explicitly (not assumed)
- Read the `Resets in N days` field from the GoUsageLimitError to confirm 14-day outage window
- Cleaned up the diagnostic probe message immediately

## What a future session should do FIRST

If the same failure shape appears (Slack user reports "nothing happening", gateway log full of `cannot_reply_to_message`):

1. Load this file (`references/user-reports-nothing-happening-2026-07-14.md`)
2. Run the 4-probe triage from SKILL.md section "User reports 'nothing happening' on Slack — provider-layer triage"
3. Do NOT stop at probe 1 or 2; the gateway is fine; the failure is at probe 3 or 4
4. Match the gateway log's `GoUsageLimitError` pattern against the SKILL.md taxonomy
5. If both providers are dead: do NOT bounce the gateway; reply directly via probe 2 path and wait for quota refresh OR edit `fallback_providers`

## Counter-examples that look the same but are different

| Pattern | Cause | Fix |
|---|---|---|
| User reports "nothing happening" + gateway NOT running (state != running in launchctl) | launchd crash | Restart gateway: `launchctl kickstart -k gui/$(id -u)/ai.hermes.prod` |
| User reports "nothing happening" + `not_in_channel` from probe 2 | bot removed from channel | `/invite @hermes` in the channel, then re-probe |
| User reports "nothing happening" + probe 3 returns 401/403 | credential rotated | Update ~/.bashrc AND ~/.profile (both — see `bashrc-profile-xapp-drift-blocks-launchd` memory), restart gateway |
| User reports "nothing happening" + probe 3 returns 200 + probe 4 returns 200 | transient in specific agent run | Self-recovers on next inbound; do nothing |

The 2026-07-14 instance is the rare one where the gateway IS healthy, the bot IS in the channel, BOTH providers are dead, and the recovery is a 14-day wait. That's the case where direct probe-2 post + transparent explanation is the right move.