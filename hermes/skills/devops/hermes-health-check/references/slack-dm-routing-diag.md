---
name: slack-dm-routing-diag
description: Diagnostic script and findings for Slack E2E DM routing failures in the Hermes monitor report.
tags: [monitor, slack, dm, hermes]
references:
  - hermes-health-check
---

# Slack DM Routing Diagnostic (2026-05-28)

Concrete technique for diagnosing the Slack E2E DM failures in the monitor report.

## The Problem

Monitor consistently shows `dm_no_mention=failed; dm_with_mention=failed; channel_no_mention=ok; channel_with_mention=ok; thread_no_mention=ok; thread_with_mention=ok` across 20+ consecutive runs (4/6 pass pattern). Both DM tests fail while all channel and thread tests pass.

**Important distinction:** This is NOT the mention-gating pattern (which would show `dm_with_mention=ok` passing). Both DM tests failing means the bot is not processing DMs at all through its normal routing.

## Root Cause: Dual-Profile DM Routing Race

Both prod gateway (port 8643) and staging gateway (port 8644) run Slack Socket Mode simultaneously using the **same `botToken`** from `~/.hermes_prod/config.yaml`. Both receive ALL Slack `message.im` events — including the monitor's DM probe.

The staging gateway (`.hermes/`) has a **skeleton config** (minimal `plugins` + `channels` keys, no `agents`, `models.providers`, `replyToModeByChatType`, or `dmPolicy`). Its DM behavior falls back to unknown defaults and may not generate a reply. The prod gateway — which the monitor watches for replies — may not receive the DM if Slack routes the event to staging first.

**Why channel/thread tests pass:** Channel messages (`message.channels` events) are handled reliably by the prod gateway despite both gateways receiving them. The race is specific to DM (`message.im`) events.

## Diagnostic Script

```bash
#!/bin/bash
# Slack DM routing diagnostic — compare replies to dm_with_mention vs dm_no_mention
# Usage: bash slack-dm-routing-diag.sh

BOT_TOKEN=$(cat ~/.hermes_prod/config.yaml | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['channels']['slack']['botToken'])")

echo "=== STAGING CONFIG (skeleton — no DM routing fields) ==="
cat ~/.hermes/config.yaml | python3 -c "import json,sys; d=json.load(sys.stdin); s=d.get('channels',{}).get('slack',{}); print('dmPolicy:', s.get('dmPolicy')); print('replyToMode:', s.get('replyToMode')); print('replyToModeByChatType:', s.get('replyToModeByChatType'))"

echo ""
echo "=== PROD CONFIG (full — has DM routing) ==="
cat ~/.hermes_prod/config.yaml | python3 -c "import json,sys; d=json.load(sys.stdin); s=d.get('channels',{}).get('slack',{}); print('dmPolicy:', s.get('dmPolicy')); print('replyToModeByChatType:', s.get('replyToModeByChatType'))"

echo ""
echo "=== BOTH GATEWAYS RUNNING SOCKET MODE? ==="
lsof -i :8643 -P 2>/dev/null && echo "prod gateway: UP" || echo "prod gateway: DOWN"
lsof -i :8644 -P 2>/dev/null && echo "staging gateway: UP" || echo "staging gateway: DOWN"

echo ""
echo "=== PROD GATEWAY HEALTH ==="
curl -s --max-time 3 http://localhost:8643/health

echo ""
echo "=== STAGING GATEWAY HEALTH ==="
curl -s --max-time 3 http://localhost:8644/health
```

## Expected Output

| Check | Result | Indicates |
|-------|--------|-----------|
| Staging `dmPolicy` = `null` | ✅ confirmed | Skeleton config — no explicit DM routing |
| Prod `dmPolicy` = `"open"` | ✅ confirmed | Proper DM config |
| Both `lsof` show listeners | ✅ confirmed | Both running Socket Mode |
| Both health endpoints return 200 | ✅ confirmed | Both healthy (not a crash) |

**Conclusion:** Both gateways running Socket Mode with same bot token + staging has no DM config = routing race causing DM probe failures.

## What to Look For in Gateway Logs

```bash
# Prod gateway DM activity
grep -E "im\.|message.im|DM" ~/.hermes_prod/logs/gateway.log 2>/dev/null | tail -20

# Staging gateway DM activity (if any)
grep -E "im\.|message.im|DM" ~/.hermes/logs/gateway.log 2>/dev/null | tail -20

# Check if staging gateway is even logging DM events
grep "message.im" ~/.hermes/logs/gateway.log | wc -l
```

## Action Plan

1. **Disable Socket Mode on staging gateway** if staging doesn't need Slack event handling (it currently only runs the memory lookup probe)
2. In `~/.hermes/hermes.staging.json`, set `channels.slack.mode` to something other than `"socket"`, or add a `disabled: true` flag under `channels.slack`
3. Restart staging gateway: `launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.hermes.staging.plist`
4. Re-run the E2E matrix — expect 6/6 pass once the routing race is eliminated

**Do NOT restart either gateway as a first response** — both are healthy (HTTP 200). This is a routing configuration issue.

## Related

- Main skill: `hermes-health-check` → `### Slack E2E DM failures: both dm tests consistently fail (4/6 pattern)`
- Full check table: `references/hermes-monitor-checks.md` → `Slack E2E Matrix`