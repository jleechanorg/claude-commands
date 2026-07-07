# Additional Monitor Diagnostic Reference

## Dual-System Slack Collisions (Hermes staging vs Hermes prod)

**Symptom:** Monitor probe in `#ai-slack-test` (C0AKALZ4CKW) triggers a "Primary model failed — switching to fallback: MiniMax-M2.7 via minimax" response that appears in the same channel/thread as the failing Hermes monitor test.

**Root cause:** Both Hermes staging (port 8643) AND Hermes prod (port 8643) are subscribed to `#ai-slack-test` (C0AKALZ4CKW). The "Primary model failed" message is **Hermes staging's own CircuitBreaker fallback** (`~/.hermes/logs/gateway.log`), not an Hermes issue. Hermes staging replies to the channel message but its reply is not in the Hermes thread session — so the Hermes `channel_no_mention` probe times out.

**Log attribution matrix:**
| System | Log file | Look for |
|--------|----------|----------|
| Hermes staging | `~/.hermes/logs/gateway.log` | `🔄 Primary model failed — switching to fallback` |
| Hermes prod | `~/.hermes_prod/logs/gateway.err.log` | `socket-mode:SlackWebSocket` pong timeouts |

**Diagnostic commands:**
```bash
# Confirm which system is processing a given channel/thread
grep "C0AKALZ4CKW\|1779925741" ~/.hermes/logs/gateway.log | head -3   # Hermes staging
grep "C0AKALZ4CKW\|1779925741" ~/.hermes_prod/logs/gateway.log | head -3  # Hermes

# Check which PIDs own which ports
lsof -i :8642 -i :8643 -i :8643 -P | grep LISTEN

# Verify gateway health (HTTP is independent of WebSocket state)
curl -s --max-time 3 http://localhost:8643/health
```

**Severity assessment:** The Hermes staging fallback message in the channel does NOT satisfy the Hermes E2E probe — they are independent sessions. A `channel_no_mention` failure during a Hermes staging fallback event is a timing coincidence, not a causal failure. Hermes gateway itself is healthy if HTTP health returns `{"ok":true,"status":"live"}`.

**When to act vs when to ignore:**
- ✅ Ignore: `channel_no_mention=failed` with healthy HTTP 200 and Hermes staging showing fallback activity
- ⚠️ Investigate: `channel_with_mention` also failing (real regression, not WebSocket churn)
- ⚠️ Investigate: HTTP health non-200 even after waiting 30s

## WebSocket Pong Timeout Pattern (2026-05-27)

**Observed behavior:** Hermes prod gateway (`~/.hermes_prod/logs/gateway.err.log`) shows recurring pong timeouts and periodic ECONNRESET disconnections throughout the day. These are Slack server-side/network-level events, not code bugs.

**Typical sequence:**
1. `[WARN] socket-mode:SlackWebSocket:N A pong wasn't received from the server before the timeout of 5000ms!` — counter increments
2. After several consecutive misses: `[ERROR] socket-mode:SlackWebSocket:N WebSocket error occurred: read ECONNRESET` — connection drops
3. Auto-reconnect begins; during reconnect window, incoming message processing may be delayed
4. `[ERROR] socket-mode:SocketModeClient:0 Failed to send a message as the client is not ready` — gateway is reconnecting

**Impact on monitor:** The E2E probe's 180s window may fall entirely within a reconnect window, causing `channel_no_mention` to timeout even though the bot is healthy and processing other messages normally.

**Frequency:** Multiple per minute (not an anomaly — this has been the pattern all day on 2026-05-27).

**Root cause investigation:** Check if VPN, network middleware, or Slack server status is contributing. Also check `HERMES_WS_PING_TIMEOUT_MS` or equivalent Socket Mode config if exposed.

## Hermes Staging Config Warnings (recurring)

**Pattern in `~/.hermes/logs/gateway.error.log`:**
```
⚠ Config issues detected in config.yaml:
  ⚠ custom_providers[0] is missing 'name' field
  Run 'hermes doctor' for fix suggestions.
```

**Severity:** Low. This warning appears on every staging gateway startup/restart. It indicates a missing `name` field in the first entry of `custom_providers` in `~/.hermes/config.yaml`. The staging gateway still starts and functions — this is a validation lint, not a runtime error. Fix by adding `name: <provider_name>` to the custom_providers entry, or ignore if the provider works without it.

## Monitor "process=0 api=1" Stale Process Count (2026-05-28)

**Symptom:** Monitor reports `process=0 api=1` for Hermes staging, meaning it counts 0 running processes but the API health check succeeds.

**Confirmed state:** PID 54840 is alive (`ps -p 54840` shows `/opt/homebrew/bin/hermes gateway run`), `launchctl list | grep hermes-staging` shows PID registered with state=running, and `curl http://localhost:8643/health` returns `{"status":"ok"}`.

**Why `lsof -p <PID> -i` shows no LISTEN:** The hermes Python process may bind via an internal socket not visible to `lsof -i`, or the port is bound before the `lsof` snapshot. The health check via HTTP is the authoritative signal — if the API responds, the process IS serving.

**Monitor heuristic mismatch:** The monitor likely counts processes via a `pgrep`/`ps` pattern that doesn't match the actual command line of the running hermes process. When `api=1` confirms reachability, treat `process=0` as a stale counter, not a real failure.