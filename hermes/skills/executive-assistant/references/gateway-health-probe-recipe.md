# Gateway health verification recipe

The 12:01 PT EA sweep on 2026-07-09 fired a false-positive DOWN alert that, if
taken at face value, would have blocked the entire brief. Use this recipe
whenever a `#all-$USER-ai` gateway-DOWN alert appears in the sweep window.

## Why the alert is bogus

`~/.hermes/monitor-agent.sh` runs:

```bash
HTTP_GATEWAY_URL="${HERMES_MONITOR_HTTP_GATEWAY_URL:-http://127.0.0.1:8643/health}"
```

But the prod gateway launches via `ai.hermes.prod.plist` and starts in
**socket-mode Slack mode only** — no HTTP listener is opened on 8643 (or
8642). The probe always 7-errors, the watcher fires a `:rotating_light:`
post to `#all-$USER-ai`, and on-call wakes up for nothing.

Reference: `~/.hermes/launchd/ai.hermes.prod.plist` →
`$HOME/.hermes/scripts/launchd-env-wrapper.sh` → `hermes gateway run`
(no `--port` / no `--bind`).

## Three checks to confirm real gateway health

```bash
# 1. Process up?
ps -A -o pid,command | grep "hermes gateway" | grep -v grep
# Expect: one row with the python interpreter path and `hermes gateway run`.

# 2. launchd loaded?
launchctl print gui/501/ai.hermes.prod | head -8
# Expect: `state = running`, `active count = 1`.

# 3. Recent Slack traffic?
tail -50 ~/.hermes/logs/gateway.log | grep -E "inbound message|Gateway running"
# Expect: at least one `inbound message` line within the last hour, plus the
# startup banner `Gateway running with 1 platform(s)`.
```

If all three pass, the gateway is healthy. Report the alert as a
:white_circle: (monitor-agent probe bug, not a real outage) and surface the
probe-bug as a follow-up item — don't file as a BLOCKED item.

## Quick proof-script (added 2026-07-09)

```bash
verdict=""
ps -A -o pid,command | grep -q "hermes gateway" && verdict="PROC_OK"
launchctl print gui/501/ai.hermes.prod 2>/dev/null | grep -q "state = running" && verdict="${verdict:+${verdict}_}PLIST_OK"
tail -100 ~/.hermes/logs/gateway.log | grep -q "inbound message" && verdict="${verdict:+${verdict}_}TRAFFIC_OK"
echo "gateway_health=$verdict"
```

If all three OK → report healthy. If any missing → real outage, escalate.

## Action item: patch the probe (not yet filed)

`monitor-agent.sh` should be updated to (a) check `pgrep -f "hermes gateway"`
instead of HTTP, OR (b) accept a `--mode socket` flag and use
`launchctl print` as the source of truth. Filed as a follow-up in the
12:01 brief; not yet a PR.
