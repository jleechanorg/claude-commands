---
name: hermes-health-check
description: Diagnose Hermes gateway health, Hermes monitor issues, and launchd service failures. Run when the user shares a monitor report, says "is everything ok", "check Hermes", "hermes is down", or when a launchd service exits with code 127 (command not found).
triggers:
  - hermes is down
  - check health
  - is everything ok
  - monitor shows problem
  - launchd exited 127
  - phase2 failed
---

# Hermes Health Check

## Diagnostic Order

**Step 1 — Launchd services and process status**
```bash
launchctl list | grep hermes
ps aux | grep hermes | grep -v grep
```

**Step 2 — Gateway ports (prod=8642, staging=8643)**
```bash
curl -s --max-time 3 http://localhost:8642/health  # prod
curl -s --max-time 3 http://localhost:8643/health  # staging
lsof -i :8642 -i :8643 -P | grep LISTEN
```

**Step 3 — launchd exit code meanings**
- `exit 127` = command/script not found (most common: referenced `.sh` doesn't exist)
- `exit -9` = killed (crash or OOM)
- `exit 124` = command timeout (not a real failure of the target service)

**Step 4 — Check plist vs registered**
```bash
# Plist exists but service not registered?
launchctl list | grep <label>
launchctl error <pid> 2>/dev/null  # decode exit code
```

**Step 5 — AO dashboard**
```bash
# Plist location vs registered location
ls -la ~/Library/LaunchAgents/ai.agento.dashboard.plist
launchctl list | grep dashboard
# If plist exists in ~/.hermes/launchd/ but not in ~/Library/LaunchAgents/:
ln -sf ~/.hermes/launchd/ai.agento.dashboard.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/ai.agento.dashboard.plist
```

## Common Fixes

### Missing script (exit 127)
```bash
# Find what script is referenced
grep -A3 ProgramArguments ~/Library/LaunchAgents/<service>.plist
# Create the missing script (see references/hermes-watchdog-template.sh)
```

### Symptom: monitor says "Hermes staging — process down"
Check `launchctl list | grep hermes-staging` — if PID is `-` the process isn't running but may be registered. If the process IS running (`ps aux` shows it), the monitor is checking the wrong port.

**Verified false-positive pattern (2026-05-28):** Monitor reports `process=0 api=1` (meaning process count 0, API check 1) but:
- `launchctl list | grep hermes-staging` shows a real PID (e.g., 54840, state=running)
- `ps -p <PID>` confirms the process is alive
- `curl http://localhost:8643/health` returns `{"status":"ok"}`
- `lsof -p <PID> -i -P -n | grep LISTEN` may show NO listen entries (hermes binds internally)

**Root cause of false positive:** The monitor's process-check heuristic counts hermes staging processes via a pattern that doesn't match the actual running process (e.g., wrong binary name match, wrong PID file, or stale cache). The `api=1` flag confirms the API endpoint IS reachable — when process=0 but api=1, trust the API result over the process counter.

**Diagnostic confirmation:**
```bash
# Quick 3-point check to confirm false positive:
launchctl list | grep hermes-staging  # PID should be non-zero
curl -s --max-time 3 http://localhost:8643/health  # Should return ok
ps -p $(launchctl list | grep hermes-staging | awk '{print $1}') -o pid,stat,command  # Should show S (sleeping/running)
```
If all 3 pass → monitor "process down" is a false positive. No restart needed.

### Phase 2 timeout (rc=124)
The monitor's phase 2 runs `ai_orch run` which can timeout at 180s. This is a **monitor self-timeout**, not an actual service failure. Check the actual service via Steps 1-2 before treating the rc=124 as real.

### Hermes prod gateway alive but HTTP port not responding
If the gateway PID is alive (`ps aux` shows `hermes gateway`) but `curl localhost:8643/health` returns nothing, the HTTP server never initialized. The ECONNRESET storms on the Slack WebSocket (visible in `gateway.err.log`) can leave the process alive but the HTTP listener broken. Fix: `launchctl bootout gui/$(id -u)/ai.hermes.gateway && launchctl load -w ~/Library/LaunchAgents/ai.hermes.gateway.plist`. Full diagnostic in `references/hermes-monitor-checks.md`.

### Gateway Startup Warning: `duplicate plugin id detected`

**Symptom:** Both gateways log on startup:
```
Config warnings:\n- plugins.entries.hermes-mem0: plugin hermes-mem0: duplicate plugin id detected; global plugin will be overridden by config plugin (/Users/$USER/.hermes_prod/extensions/hermes-mem0/index.ts)
```
This is cosmetic — the local extension correctly overrides the global plugin. No action needed. See `references/hermes-monitor-checks.md` for details.

### Qdrant Dual-Provider Conflict (Docker + Native)

**Symptom:** Monitor reports `memory_lookup rc=3` transiently (brief "connection refused" window) then recovers on next cycle. Root cause: both Docker `hermes-mem0-qdrant` and native `~/.local/bin/qdrant` (launchd) target port 6333 on the same storage dir. When the native binary wins the port race, the Docker container exits 255, but a brief gap can cause the probe to fail. **Fix:** Remove the Docker container (`docker rm -f hermes-mem0-qdrant`) and rely on the native launchd service. See `references/hermes-monitor-checks.md` for full diagnostic and recovery steps.

## doctor.sh Output Interpretation

**IMPORTANT — config context:** `doctor.sh` validates the config at `$LIVE_HERMES/config.yaml`. It may be run against the **staging profile** (`.hermes/`) even when the **production gateway** (`.hermes_prod/`) is the live service. The staging `.hermes/config.yaml` is often a **minimal skeleton** with only `plugins` and `channels` top-level keys — no `agents`, `models.providers`, `heartbeat`, etc. Doctor flags these missing fields as FAILs, but this is **expected for a skeleton staging config** and does not indicate the production gateway is unhealthy.

**Diagnostic sequence when doctor.sh shows multiple FAILs:**
```bash
# 1. Confirm which profile doctor is actually validating
grep "Live Hermes dir:" <(bash /Users/$USER/.hermes/scripts/doctor.sh 2>&1)

# 2. Verify the actual prod gateway health separately:
curl -s --max-time 3 http://localhost:8644/health
#    If that returns {"ok":true,"status":"live"} → prod gateway is healthy, doctor FAILs are config-context artifacts.

# 3. Run doctor against prod explicitly to see the true health:
HERMES_STATE_DIR=/Users/$USER/.hermes_prod bash /Users/$USER/.hermes/scripts/doctor.sh 2>&1 | tail -80
```

**Known false-positive FAIL patterns (staging skeleton config):**
- `agents.defaults.workspace drifted` → `agents` section absent from staging skeleton
- `MiniMax runtime provider drift` → `models.providers` absent from staging skeleton
- `heartbeat config: agents.defaults.heartbeat.every must be 5m` → heartbeat section absent from staging skeleton
- `pytest config.yaml validation: 1 test(s) failed` → test file path is relative to validated config dir; not a real config problem
- `gateway token missing/placeholder` → token is in prod config, not staging skeleton
- `Slack socket-mode tokens are shared with prod` → intentional in dual-profile setup; not a failure

### doctor.sh path resolution (rc=127)
`monitor-agent.sh` uses `resolve_doctor_sh_path()` to find `doctor.sh`. If it returns rc=127, the search paths don't include where the file actually lives. As of 2026-05-27, the canonical path is `$HOME/.hermes/scripts/doctor.sh` (NOT `$HOME/.hermes/doctor.sh`). The candidate search order:
1. `$HERMES_MONITOR_DOCTOR_SH_PATH` (env override)
2. `$PWD/doctor.sh`
3. `$MONITOR_REPO_ROOT/doctor.sh`
4. `$MONITOR_REPO_ROOT/scripts/doctor.sh`
5. `$HOME/.hermes/scripts/doctor.sh`
6. `$HOME/.hermes/$ORG/doctor.sh`
7. `$HOME/.hermes/doctor.sh`
8. `command -v doctor.sh`

If you patch the search list, verify the file exists first: `test -f "$HOME/.hermes/scripts/doctor.sh"`.

### Slack E2E DM failures: both dm tests consistently fail (4/6 pattern)

**Pattern (2026-05-28):** `dm_no_mention=failed; dm_with_mention=failed; channel_no_mention=ok; channel_with_mention=ok; thread_no_mention=ok; thread_with_mention=ok` across 20+ consecutive runs. This is NOT mention-gating (that would show `dm_with_mention=ok` passing).

**Root cause — dual-profile DM routing race:**
- Both prod gateway (port 8643) and staging gateway (port 8644) run Slack Socket Mode simultaneously using the **same `botToken`** from `~/.hermes_prod/config.yaml`
- Both receive ALL Slack `message.im` events — including the monitor's DM probe
- The staging gateway (`.hermes/`) has a skeleton config with no `replyToModeByChatType` or `dmPolicy` fields — its DM behavior is unpredictable and may not generate a reply
- The prod gateway (which the monitor watches for replies) may or may not receive the DM event if Slack routes it to staging instead

**Why channel/thread tests pass:** Channel messages are handled reliably by the prod gateway despite both gateways receiving them. The race is specific to DM (`message.im`) events.

**Diagnostic:**
```bash
# Staging config — no DM routing fields set (skeleton)
cat ~/.hermes/config.yaml | jq '.channels.slack | {dmPolicy, replyToMode, replyToModeByChatType}'
# → all null — falls back to unknown defaults

# Prod config — full DM config
cat ~/.hermes_prod/config.yaml | jq '.channels.slack | {dmPolicy, replyToModeByChatType}'
# → dmPolicy="open", replyToModeByChatType.direct="all"

# Both gateways running Socket Mode?
lsof -i :8643 -P  # prod
lsof -i :8644 -P  # staging
```

**Action items:**
1. Determine if staging gateway should have Socket Mode disabled (it currently handles only the memory probe, not Slack event handling)
2. If staging must run Socket Mode, investigate disabling DM event handling in its config
3. Do NOT restart either gateway for this — both are healthy (HTTP 200), this is a routing configuration issue

**Fix location:** Likely in `hermes.staging.json` — add `"mode": "socket"` with a note or disable Socket Mode entirely if staging doesn't need Slack event processing.

**Reference:** `references/slack-dm-routing-diag.md` — diagnostic script for comparing DM reply behavior via Slack API directly.
### `channel_no_mention` intermittent failures (2026-05-27+)

**Pattern:** `channel_no_mention=failed` appears intermittently (~30-40% of runs), often alongside `thread_no_mention=failed`, producing 2/6 or 3/6 pass counts instead of the usual 4/6.

**Root cause:** Recurring Slack WebSocket pong timeouts (5000ms deadline) and periodic `ECONNRESET` disconnections. The Socket Mode WebSocket disconnects and must reconnect; during that window, the gateway may not process incoming channel messages, causing the no-mention probe to timeout before the bot can respond.

**Gateway log markers:**
```
[WARN] socket-mode:SlackWebSocket:N A pong wasn't received from the server before the timeout of 5000ms!
[ERROR] socket-mode:SlackWebSocket:N WebSocket error occurred: read ECONNRESET
[ERROR] socket-mode:SocketModeClient:0 Failed to send a message as the client has no active connection
```

**Diagnostic:**
```bash
# Check for pong timeout frequency
grep "pong wasn't received" ~/.hermes_prod/logs/gateway.err.log | tail -10
# Check for ECONNRESET events
grep "ECONNRESET" ~/.hermes_prod/logs/gateway.err.log | tail -5
# Verify gateway still responsive (HTTP health is independent of WebSocket)
curl -s --max-time 3 http://localhost:8643/health
```

**Severity assessment:** A single `channel_no_mention` failure alongside healthy HTTP health = transient churn, no action needed. Persistent across all cycles = real regression (check `channel_with_mention` and `thread_with_mention` — they will also fail).

**Do not:** Restart the gateway for a single `channel_no_mention` failure with healthy HTTP health. The WebSocket reconnection is automatic and the gateway continues to process messages on reconnect. Restarting adds unnecessary disruption.

**Log format (6/6 pass):**
```
slack_e2e_matrix rc=0 summary=Slack E2E matrix passed=6/6 invalid=0 sender=SLACK_USER_TOKEN channel=C0AKALZ4CKW thread_channel=C0AJ3SD5C79 details: dm_no_mention=ok; dm_with_mention=ok; channel_no_mention=ok; channel_with_mention=ok; thread_no_mention=ok; thread_with_mention=ok
```

**Log format (4/6 pass — intermittent WebSocket churn):**
```
slack_e2e_matrix rc=6 summary=Slack E2E matrix passed=4/6 invalid=0 sender=SLACK_USER_TOKEN channel=C0AKALZ4CKW thread_channel=C0AJ3SD5C79 details: dm_no_mention=ok; dm_with_mention=ok; channel_no_mention=failed; channel_with_mention=ok; thread_no_mention=failed; thread_with_mention=ok
```

### Persistent DM failures (both dm_no_mention AND dm_with_mention)

**Pattern (2026-05-28):** Consistent 4/6 pass — both DM tests fail while all 4 channel/thread tests pass:
```
dm_no_mention=failed; dm_with_mention=failed; channel_no_mention=ok; channel_with_mention=ok; thread_no_mention=ok; thread_with_mention=ok
```
This is NOT the intermittent WebSocket churn pattern (which shows `channel_no_mention=failed` alongside `thread_no_mention=failed`).

**Gateway config analysis:**
- `dmPolicy: "open"` — correct, should allow DMs without mention
- `allowFrom: ["*"]` — correct, allow all users
- `replyToModeByChatType.direct: "all"` — correct
- `requireMention: false` on all channels — correct
- Bot user ID: `U0AEZC7RX1Q`

**Likely root cause — dual-profile DM race:** Both prod (8643) and staging (8644) run Slack Socket Mode simultaneously with the same `botToken`. Slack may deliver DM events to only one WebSocket at a time. The monitor sends the DM probe and watches for a reply from the prod gateway, but the staging gateway (which also receives the DM) may be the one that processes it — or neither receives it if Slack routes to a stale connection. This race is specific to DMs because both gateways have independent WebSocket connections competing for the same `message.im` events.

**Evidence for dual-profile race:**
- `channel_no_mention` passes — channel messages are also routed to both gateways, but the prod gateway handles them reliably
- DM failures are consistent across 20+ consecutive runs — not random timing
- Both gateways have `dmPolicy: "open"` but the staging gateway (`.hermes/`) has only a skeleton config (no `agents` section), making its behavior unpredictable for DM routing

**Diagnostic:**
```bash
# Check if staging gateway is even configured to handle DMs
cat ~/.hermes/config.yaml | jq '.channels.slack | {dmPolicy, replyToMode, replyToModeByChatType}'
# Staging has null for all DM-related fields — falls back to defaults, unknown behavior

# Check prod DM config
cat ~/.hermes_prod/config.yaml | jq '.channels.slack | {dmPolicy, replyToModeByChatType}'

# Confirm both gateways are actually receiving message events
# (requires checking both gateway's internal event logs)
```

**Action items:**
1. Verify whether both prod and staging gateways should be running Socket Mode simultaneously, or if one should be socket-mode disabled
2. If the staging gateway is not meant to handle Slack events, disable its Socket Mode in `hermes.staging.json`
3. If both must run, investigate whether DM events can be routed exclusively to prod via `channels.slack.botToken` scope isolation (unlikely — same token = same events)
4. Check whether the staging gateway's skeleton config causes it to mishandle DM events (no `replyToMode` configured = unpredictable)

**Do not:** Restart the gateway for persistent DM failures — both prod and staging are healthy (HTTP 200). This is a routing configuration issue, not a crash.

**Related:** `references/slack-dm-routing-diag.md` — concrete diagnostic script for comparing DM reply behavior in the Slack API directly.

### MiniMax Token Plan rate-limit (HTTP 429)

**Symptom:** Slack thread shows a "switching to fallback" message but the same MiniMax model is the only configured model. E2E stays at 6/6.

**Log pattern (gateway failover decision):**
```
failoverReason: "rate_limit"
profileFailureReason: "rate_limit"
provider: "minimax"
model: "MiniMax-M2.7"
fallbackConfigured: false   ← no separate fallback model exists
decision: "surface_error"   ← error surfaces to user instead of auto-recovering
```

**What the Slack message actually means:** The gateway tried MiniMax, got rate-limited, found no fallback model configured, and is showing you the error directly. The "switching to fallback" wording is misleading — it's showing the same model name because no distinct fallback exists.

**Token Plan specifics:** The 429 error message reads:
> *"The Token Plan is designed for individual, interactive developer workflows. Traffic is currently high—please retry shortly."*

This is MiniMax's API-level rate limiting, not an Hermes config problem. It typically resolves within minutes.

**Diagnostic:**
```bash
# Check recent failover events in gateway log
grep "embedded_run_failover_decision" /tmp/hermes/hermes-$(date +%Y-%m-%d).log 2>/dev/null | tail -5
```

**Long-term fix:** Add a distinct fallback model (e.g., `minimax/MiniMax-M2.5` or a different provider) to `~/.hermes_prod/config.yaml` under `models.providers`. When `fallbackConfigured: true` and a real fallback exists, the gateway will retry automatically instead of surfacing the 429 to Slack.

**Severity assessment:** 6/6 E2E pass with this message = MiniMax transient rate-limit, not a system failure. The Slack reply still went through. No action needed for single occurrences.

See `references/hermes-monitor-checks.md` for the full diagnostic table including this row and all other check patterns.

## References
- `references/hermes-monitor-checks.md` — detailed diagnostic patterns for each monitor check (doctor.sh, Slack E2E, memory lookup, AO version), including search paths, log formats, and fix history. **Also contains:** Gateway `duplicate plugin id` warning pattern and Qdrant dual-provider conflict (Docker + native) diagnostic.
- `references/additional-monitor-diags.md` — dual-system Slack collision diagnostics (Hermes staging vs Hermes in same channel), WebSocket pong timeout pattern and attribution.
- `references/slack-dm-routing-diag.md` — concrete script + findings for diagnosing the `dm_no_mention` vs `dm_with_mention` split in the Slack E2E matrix.

### Memory lookup: Qdrant backend unavailable (rc=3)

**Two distinct failure modes — diagnose before fixing:**

#### Mode A: Qdrant backend unavailable (rc=3, doctor FAIL "Memory lookup failed")
`curl -s http://localhost:6333/collections` returns nothing or "connection refused". Qdrant is not running at all.

**Root cause possibilities (in order):**
1. **Docker Desktop hung** — `docker ps` times out, `docker info` times out, but `com.docker.backend` process is alive. The Qdrant container (`hermes-mem0-qdrant`) has port 6333 bound but is unresponsive.
2. **Docker Desktop not started** — no Docker processes at all.
3. **Qdrant container stopped/removed** — Docker works but the container doesn't exist.

**Diagnostic sequence:**
```bash
# 1. Is anything listening on 6333?
lsof -i :6333 2>/dev/null | head -5
# 2. Does Qdrant respond?
curl -sf http://localhost:6333/healthz 2>/dev/null && echo "Qdrant UP" || echo "Qdrant DOWN"
# 3. Is Docker functional?
timeout 5 docker info 2>&1 | head -3
# 4. If Docker hangs, is the Docker daemon alive?
ps aux | grep "com.docker.backend" | grep -v grep
# 5. Does the Qdrant container exist?
timeout 5 docker ps -a --filter name=hermes-mem0-qdrant 2>&1
```

**Fix — Run Qdrant natively (no Docker dependency):**

If Docker is hung or unreliable, run Qdrant as a native binary via launchd. This is the recommended approach.

```bash
# 1. Download Qdrant native binary (arm64 macOS)
mkdir -p ~/.local/bin ~/.local/etc/qdrant
curl -sL "https://github.com/qdrant/qdrant/releases/download/v1.14.1/qdrant-aarch64-apple-darwin.tar.gz" -o /tmp/qdrant.tar.gz
cd /tmp && tar xzf qdrant.tar.gz
cp /tmp/qdrant ~/.local/bin/qdrant

# 2. Create config pointing to Hermes's storage directory
cat > ~/.local/etc/qdrant/config.yaml << 'EOF'
log_level: INFO
storage:
  storage_path: /Users/$USER/.hermes/qdrant_storage
service:
  grpc_port: 6334
  http_port: 6333
EOF

# 3. Create launchd plist (survives reboots)
cat > ~/Library/LaunchAgents/ai.hermes.qdrant.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.qdrant</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/$USER/.local/bin/qdrant</string>
        <string>--config-path</string>
        <string>/Users/$USER/.local/etc/qdrant/config.yaml</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$USER/.hermes/logs/qdrant.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$USER/.hermes/logs/qdrant.err.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/$USER/.hermes</string>
</dict>
</plist>
</plist>

EOF

# 4. Load and verify
launchctl unload ~/Library/LaunchAgents/ai.hermes.qdrant.plist 2>/dev/null || true
launchctl load -w ~/Library/LaunchAgents/ai.hermes.qdrant.plist
sleep 3
curl -sf http://localhost:6333/healthz && echo " - Qdrant UP"
```

**If the `hermes_mem0` collection is missing** (empty storage dir, fresh install):
```bash
# Create the collection that mem0 expects (768-dim Cosine, matching nomic-embed-text)
curl -s -X PUT http://localhost:6333/collections/hermes_mem0 \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 768, "distance": "Cosine"}}'
```

**Key config context:** The mem0 plugin in both prod and staging `config.yaml` points to `localhost:6333` with collection `hermes_mem0`, embedder `ollama/nomic-embed-text` (768 dims). The canonical storage path is `~/.hermes/qdrant_storage/` (set by `scripts/install-qdrant-container.sh`).

**Pitfall — port 6333 occupied by dead Docker:** If Docker previously ran the Qdrant container and Docker hangs, port 6333 stays bound by the Docker process but is unresponsive. You must kill Docker (or the specific container process) before starting native Qdrant, otherwise you get "Address already in use". Check with `lsof -i :6333`.

**Pitfall — `--storage-path` is NOT a valid Qdrant flag:** The native Qdrant binary uses `--config-path` (or environment variables like `QDRANT__STORAGE__STORAGE_PATH`) instead of `--storage-path`. The Docker container mapped `~/.hermes/qdrant_storage` to `/qdrant/storage` inside the container, so the native binary needs the config file to set the storage path.

#### Mode B: Memory lookup timeout (intermittent rc=124)
`hermes mem0 search "test"` can hang past the monitor's 30s timeout. This is a **Node.js cold-start issue**, NOT a Qdrant backend failure. Quick diagnostic: `curl -s http://localhost:6333/collections` — if Qdrant responds, the backend is fine.

**Root cause (2026-05-28):** `run_memory_lookup_probe()` in `monitor-agent.sh` uses `bash -lc` to run the `hermes` CLI. Launchd's `bash -lc` subshells lose nvm's PATH additions — `hermes` is invisible even after sourcing `nvm.sh`. This causes timeout (rc=124) → reported as rc=3.

**Fix (applied to monitor-agent.sh lines ~1260-1270):**
```
memory_output="$(timeout "$memory_timeout" bash -lc 'export NVM_DIR="$HOME/.nvm" && export PATH="$NVM_DIR/versions/node/v22.22.0/bin:$PATH" && '"${memory_cmd}"' ' 2>&1)"
```
Sourcing `nvm.sh` alone does NOT reliably add node/bin to PATH in daemon subshells. The direct PATH prepend is deterministic. Fallback uses the full path: `$HOME/.nvm/versions/node/v22.22.0/bin/hermes`. Both branches of the if/else now use `hermes mem0 search` (legacy `memory` subcommand was deprecated).

## Hermes Monitor Log Inspection
```bash
# Check latest cycle results
grep -E "^[0-9]" ~/.hermes/logs/monitor-agent.log | tail -20
# Find specific check failures
grep "rc=[1-9]" ~/.hermes/logs/monitor-agent.log | tail -10
# Verify individual check names match the report
grep -E "doctor_sh|slack_e2e|memory_lookup|ao_doctor" ~/.hermes/logs/monitor-agent.log | tail -10
```

## Key Ports (remember these)
| Service | Port | Config key |
|---------|------|------------|
| Hermes prod | 8642 | `~/.hermes_prod/config.yaml` → `api_server.extra.port` |
| Hermes staging | 8643 | `~/.hermes/config.yaml` → `api_server.extra.port` |
| AO dashboard | 3020 | plist `PORT` env var |
| Hermes prod | 8643 | inferred from `hermes_prod/config.yaml` |
| Hermes staging | 8644 | `HERMES_GATEWAY_PORT` env var, `hermes.staging.json` |
| Qdrant (mem0) | 6333 | native binary via launchd `ai.hermes.qdrant`, config at `~/.local/etc/qdrant/config.yaml` |

## Staging Gateway Restart Procedure

**Symptom:** `ai.hermes.staging` shows PID in `launchctl list` but port 8644 is not listening and `curl localhost:8644/health` returns nothing. Gateway has been down since a SIGTERM / crash cycle.

**Critical distinction — `launchctl load` vs `launchctl bootstrap`:**
- `launchctl load <plist>` → fails with `Load failed: 5: Input/output error` when the service domain isn't fully initialized
- `launchctl bootstrap gui/501 <plist>` → works correctly for user-level GUI apps

```bash
# Step 1: Kill any zombie staging processes
launchctl bootout gui/501/ai.hermes.staging 2>/dev/null

# Step 2: Re-register via bootstrap (not load)
launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.hermes.staging.plist

# Step 3: Verify port binding
sleep 5 && lsof -P -n -i :8644
# Should show: node <pid> ... TCP 127.0.0.1:8644 (LISTEN)

# Step 4: Verify HTTP endpoint
curl -s --max-time 5 http://127.0.0.1:8644/health
# Should return: {"ok":true,"status":"live"}
```

**Why `load` fails with I/O error:** When the launchd user domain (gui/501) isn't fully initialized at the time of the call, `load` can fail with EIO. `bootstrap` forces re-registration from scratch. Both require the plist to be valid XML with no malformed elements.

**Dual-profile architecture context:**
- Staging: `.hermes/` → port **8644** → `hermes.staging.json`
- Prod: `.hermes_prod/` → port **8643** → `config.yaml`
- Both must be healthy for the monitor to show all-clear. Staging gateway handles the memory lookup probe (rc=3 fix); prod gateway handles Slack E2E and core monitoring.

## Memory Probe PATH Fix in monitor-agent.sh

**Root cause:** `monitor-agent.sh` runs via launchd as `bash -lc /path/to/monitor-agent.sh`. The `-lc` flag produces a stripped non-login shell that does NOT inherit nvm's PATH additions. The `hermes` CLI (Node.js binary at `~/.nvm/versions/node/v22.22.0/bin/hermes`) is invisible to these subshells even when `nvm.sh` is sourced.

**Affected probe:** `run_memory_lookup_probe()` — the `bash -lc` subshell used to run `hermes mem0 search "test"` cannot find `hermes` if the PATH doesn't include the nvm bin directory.

**The fix (applied 2026-05-28 to monitor-agent.sh lines ~1260):**
```bash
# BEFORE (broken — hermes invisible in bash -lc subshell):
memory_output="$(timeout "$memory_timeout" bash -lc "$memory_cmd" 2>&1)"

# AFTER (working — explicit PATH prepend inside bash -lc):
memory_output="$(timeout "$memory_timeout" bash -lc 'export NVM_DIR="$HOME/.nvm" && export PATH="$NVM_DIR/versions/node/v22.22.0/bin:$PATH" && '"${memory_cmd}"' ' 2>&1)"
```

**Why sourcing `nvm.sh` alone doesn't work:** nvm's shell function wrapper (`nvm()`) and its effect on `$PATH` are unreliable in daemon/non-interactive subshells. Prepending the path directly is deterministic.

**Fallback (if command still not found):** Try the direct binary path:
```bash
memory_output="$(timeout "$memory_timeout" bash -lc 'export NVM_DIR="$HOME/.nvm" && export PATH="$NVM_DIR/versions/node/v22.22.0/bin:$PATH" && $HOME/.nvm/versions/node/v22.22.0/bin/hermes mem0 search "test"' 2>&1)"
```

**Also unified the memory command:** The `else` branch now also uses `hermes mem0 search` (not `hermes memory search`), since the legacy `memory` subcommand is deprecated.

### Dual-profile architecture (2026-05-28 update)

**File system layout — both are independent directories, NOT a symlink pair:**

```
~/.hermes/         ← staging profile root (HERMES_STATE_DIR for staging gateway)
  agents/            ← staging agent sessions, auth-profiles
  logs/              ← staging gateway logs
  tasks/             ← staging runs.sqlite
  workspace/         ← staging workspace
  hermes.staging.json   ← staging config (minimal skeleton: plugins + channels only)
  config.yaml      ← minimal skeleton config (not the live prod config)
  extensions/        ← staging extensions
  scripts/
  monitor-agent.sh
  scripts/doctor.sh

~/.hermes_prod/    ← prod profile root (HERMES_STATE_DIR for prod gateway)
  agents/            ← prod agent sessions, auth-profiles
  logs/              ← prod gateway logs (gateway.log, gateway.err.log)
  tasks/             ← prod runs.sqlite
  workspace/         ← prod workspace
  config.yaml      ← LIVE PRODUCTION CONFIG (full: agents, models.providers, etc.)
  extensions/
  launchd/           ← prod launchd plists + staging plist template
  scripts/doctor.sh  ← same doctor.sh script
```

**Critical insight:** `~/.hermes/config.yaml` is a **minimal staging skeleton**, NOT the prod config. `doctor.sh` validates the config at the `HERMES_STATE_DIR` of the running gateway. When monitor-agent.sh runs `doctor.sh` against `~/.hermes/`, it's validating the staging skeleton — missing `agents.list`, `models.providers`, etc. are expected absences in a skeleton, not real failures.

**Shared tokens, independent gateways:**
- Both prod (port 8643, PID 65745) and staging (port 8644, PID 36394) use the **same** `botToken` and `appToken` from `~/.hermes_prod/config.yaml`
- Both run Slack Socket Mode WebSocket connections simultaneously
- Both receive ALL Slack events — creating a routing race for DMs and channel messages
- `curl -s http://localhost:8644/health` → staging gateway (36394, `.hermes/` state dir)
- `curl -s http://localhost:8643/health` → prod gateway (65745, `.hermes_prod/` state dir)

**What each gateway owns:**
- **Prod (8643):** Slack E2E probe handling, AO worker spawning, main agent sessions
- **Staging (8644):** Memory lookup probe execution (via `hermes mem0 search`)

**Key diagnostic commands:**
```bash
# Which process owns which port
lsof -i :8643 -P  # prod
lsof -i :8644 -P  # staging

# Staging plist points to .hermes/ state dir
grep "HERMES_STATE_DIR\|HERMES_CONFIG_PATH" ~/.hermes_prod/launchd/ai.hermes.staging.plist
# → HERMES_STATE_DIR=/Users/$USER/.hermes
# → HERMES_CONFIG_PATH=/Users/$USER/.hermes/hermes.staging.json

# Prod plist points to .hermes_prod/ state dir
grep "HERMES_STATE_DIR\|HERMES_CONFIG_PATH" ~/.hermes_prod/launchd/ai.hermes.gateway.plist
# → HERMES_STATE_DIR=/Users/$USER/.hermes_prod
# → HERMES_CONFIG_PATH=/Users/$USER/.hermes_prod/config.yaml
```

**Why shared tokens are a risk:** When both gateways have active Socket Mode WebSockets with the same bot credentials, Slack may deliver events to one or both unpredictably. A DM sent to the bot could be picked up by prod, staging, both, or neither depending on which WebSocket session Slack routes to. The E2E matrix's `dm_no_mention` failures are likely a symptom of this race condition — the monitor sends a DM, but the gateway that picks up the event may not be the one the monitor is watching for a reply.

**Doctor.sh config context summary:**
- `bash doctor.sh` → validates `~/.hermes/hermes.staging.json` (skeleton) → many FAILs
- `HERMES_STATE_DIR=/Users/$USER/.hermes_prod bash doctor.sh` → validates `~/.hermes_prod/config.yaml` (full prod) → true health picture
- Always run doctor against the actual live profile to get real results, not the skeleton staging config.

- `scripts/hermes gateway-quick-check.sh` — one-shot dual-profile health snapshot: both gateway ports, process+port bindings, Qdrant, Ollama, memory probe, latest errors.

## AO Dashboard Plist Gotcha
The plist lives in `~/.hermes/launchd/` (repo-tracked) but launchd only reads from `~/Library/LaunchAgents/`. If you see "AO dashboard plist missing" in doctor output:
```bash
ln -sf ~/.hermes/launchd/ai.agento.dashboard.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/ai.agento.dashboard.plist
launchctl list | grep dashboard  # confirm PID is now registered
```

## Health check commands
```bash
# Fast gateway check (one-liner)
curl -s http://localhost:8642/health && echo "PROD OK" || echo "PROD DOWN"
curl -s http://localhost:8643/health && echo "STAGING OK" || echo "STAGING DOWN"
```

**Rule of thumb:** When the monitor says "process down" but the HTTP `/health` endpoint responds, trust the API result. The monitor's process counter can be stale (wrong pgrep pattern, stale cache). API reachability is the authoritative signal.

## References
- `references/hermes-monitor-checks.md` — detailed diagnostic patterns for each monitor check (doctor.sh, Slack E2E, memory lookup, AO version), including search paths, log formats, and fix history. **Also contains:** Gateway `duplicate plugin id` warning pattern and Qdrant dual-provider conflict (Docker + native) diagnostic.
- `references/additional-monitor-diags.md` — dual-system Slack collision diagnostics (Hermes staging vs Hermes in same channel), WebSocket pong timeout pattern and attribution.
- `references/slack-dm-routing-diag.md` — concrete script + findings for diagnosing the `dm_no_mention` vs `dm_with_mention` split in the Slack E2E matrix.