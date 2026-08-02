# user-reports-nothing-happening — 2026-07-26 MiniMax-M3 429 instance

**Channel:** `#needs-jeff` (`C0BGM3A4ZC0`)
**Thread:** `1785115336.318989`
**Symptom:** Jeffrey pinged Hermes at 18:22 PT asking "how come nothing ever showing up in this channel?" and got no automatic reply.

## What was actually happening

The gateway was alive and the Hermes bot is a member of the channel (verified via `conversations.members` returning `["U09GH5BR3QU","U0AEZC7RX1Q","U0BC138QXUJ"]`). The crash was **upstream** of Slack:

```
inbound message: platform=slack user=Jeffrey Lee-Chan chat=C0BGM3A4ZC0
   Rate limited after 3 retries — HTTP 429: Token Plan usage limit reached:
   Upgrade your Token Plan or purchase Credits for more usage. (2056)
   Provider: minimax  Model: MiniMax-M3
```

Both `~/.hermes_prod/config.yaml` and `~/.hermes/config.yaml` are configured with:

```yaml
model:
  default: MiniMax-M3
  provider: minimax
fallback_providers: '[]'
```

i.e. **no fallback** — once the primary rate-limits, every agent run surfaces the error and produces no Slack reply. The user's perception that "nothing is showing up" matches reality: silent inbound → silent outbound.

## Second contributing factor

A separate Slack MCP identity (`mcp_agent_mail` / `B0A4G7LDJ4R`) gets `not_in_channel` on `C0BGM3A4ZC0` even though the canonical Hermes bot (`U0AEZC7RX1Q`) is a member. This breaks automation paths that use the MCP identity instead of the Hermes bot token — and is the second reason the user previously saw "nothing happening" in this channel even when the model was healthy.

## Diagnostic that worked in 90 seconds

1. `launchctl print gui/$(id -u)/ai.hermes.prod | grep -E 'state =|pid =|last exit'` — confirmed `state = running`, `pid = 2024`, `last exit code = (never exited)`. Gateway transport is fine.
2. `grep -E 'C0BGM3A4ZC0|cannot_reply_to_message|Rate limited after 3 retries|Token Plan usage limit reached' ~/.hermes_prod/logs/gateway.log | tail -20` — surfaced the 429 cluster hitting this exact channel. No need to chase `cannot_reply_to_message`; it's downstream noise from queued retries.
3. `grep -nE 'model:|fallback_providers:' ~/.hermes_prod/config.yaml` — proved `fallback_providers: '[]'` and `model.default: MiniMax-M3`, the durable root cause.
4. Slack REST probe (bot token) `conversations.history` for `C0BGM3A4ZC0` — confirmed the user's inbound message arrived and a posted reply landed correctly (verified via `conversations.replies`).

## Recovery recipe

1. **Post the explanation in-thread via direct bot-token `chat.postMessage`** so the user is unblocked and sees the root cause rather than another ghost. Build the JSON payload with `write_file` (heredoc dies in this runtime's terminal wrapper), then `curl --data-binary @<file>`. Identity appears as `U0AEZC7RX1Q` (hermes bot). Verified `ts=1785115630.655709`, `thread_ts=1785115336.318989`.
2. **Create a one-time 20-minute status cron** targeting the originating thread (`deliver: slack:C0BGM3A4ZC0:<thread_ts>`, `--repeat 1`, NOT `--every`). Cron job ID is logged for the operator. Pattern from SOUL.md `COMMIT: one-time-status-cron-after-every-task`.
3. **Do NOT change provider configuration during the diagnostic reply.** The user was asking why the channel was quiet, not requesting a config change. The durable fix (adding a real fallback model, or moving this profile away from MiniMax-only) belongs in a separate `swap-hermes-provider` task with explicit user approval.

## What was NOT the cause (worth recording)

- Channel membership: bot is in the channel.
- Slack transport: `chat.postMessage` succeeded when posted directly.
- Gemini / `GOOGLE_API_KEY` errors visible in thread history: those were a prior incident, not the live failure. The visible channel history contains older failed replies from a separate hermes_pc bot (`B0BBUN50HQB`) that no longer runs in this gateway; do not chase them.

## Why this needs its own reference (not just an inline lesson)

The 2026-07-14 reference (`user-reports-nothing-happening-2026-07-14.md`) covers the older `MiniMax-M3` 429 + `opencode-go/glm-5.1` `GoUsageLimitError` incident where both primary AND fallback were quota-exhausted. The 2026-07-26 instance is the **cleaner** shape: primary 429, fallback list is empty by configuration, no quota race. The diagnostic path is identical but the long-term fix is different — instead of "swap provider across six touchpoints", the answer is "configure a usable fallback". Two cases, two distinct durable fixes; both are useful to future agents.

## Key Slack API responses

```json
// conversations.members?channel=C0BGM3A4ZC0
{"ok":true,"members":["U09GH5BR3QU","U0AEZC7RX1Q","U0BC138QXUJ"]}

// chat.postMessage (Path B with hermes bot token)
{"ok":true,"channel":"C0BGM3A4ZC0","ts":"1785115630.655709","thread_ts":"1785115336.318989","message":{"user":"U09GH5BR3QU", ...}}

// conversations.replies on the thread — post verified in-thread
{"messages":[
  {"ts":"1785115520.017519","thread_ts":"1785115336.318989","user":"U0AEZC7RX1Q","text":":hourglass_flowing_sand: Working — ..."},
  {"ts":"1785115630.655709","thread_ts":"1785115336.318989","user":"U09GH5BR3QU","text":"You're right to flag it. ..."},
  {"ts":"1785115633.312279","thread_ts":"1785115336.318989","user":"U0AEZC7RX1Q","text":":fast_forward: Steered into current run ..."}
]}
```

## Files touched this session

- No skill files mutated; this is a new reference under an existing umbrella.
- No code or config edits.
- No PR opened (intentionally — the durable fix needs user direction).

## Cross-references

- Parent skill: `~/.hermes/skills/devops/hermes-health-check/SKILL.md` — the "User reports 'nothing happening' on Slack" section this reference extends.
- Prior instance: `references/user-reports-nothing-happening-2026-07-14.md` — earlier 429 + `GoUsageLimitError` cluster where the fix was provider removal.
- Companion: `~/.hermes/skills/swap-hermes-provider/SKILL.md` — the correct home for the durable fix when the user is ready to add a fallback.
- SOUL.md `COMMIT: one-time-status-cron-after-every-task` — pattern for the 20-min status follow-up.