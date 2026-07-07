# Hermes Monitor Check Reference

Detailed diagnostic patterns for each monitor check, based on real debugging sessions.

## doctor.sh (rc=127)

**Function:** `resolve_doctor_sh_path()` in `monitor-agent.sh`

**Search path candidates (in order):**
1. `$HERMES_MONITOR_DOCTOR_SH_PATH` env override
2. `$PWD/doctor.sh`
3. `$MONITOR_REPO_ROOT/doctor.sh`
4. `$MONITOR_REPO_ROOT/scripts/doctor.sh`
5. `$HOME/.hermes/scripts/doctor.sh`
6. `$HOME/.hermes/jleechanclaw/doctor.sh`
7. `$HOME/.hermes/doctor.sh`
8. `command -v doctor.sh`

**Canonical location:** `$HOME/.hermes/scripts/doctor.sh`

**Fix history:** 2026-05-27 — items 4 and 5 were missing from the search list, causing persistent rc=127. Patched into `monitor-agent.sh`.

## `hermes gateway health` RPC — rc=127 from launchd context

Even when doctor.sh is found and runs, its internal call to `hermes gateway health --timeout N` can independently return rc=127. **Root cause:** The monitor launchd job (`ai.hermes.monitor-agent`) uses:
```
/bin/bash -lc $HOME/.hermes/monitor-agent.sh
```
The `-l` flag suppresses most profile loading. The NVM-managed node path (`~/.nvm/versions/node/v22.22.0/bin`) is not inherited. The `hermes` binary lives there but is not on the resulting PATH.

**Fix:** Add `HERMES_BIN` to the monitor-agent plist's EnvironmentVariables:
```
HERMES_BIN=$HOME/.nvm/versions/node/v22.22.0/bin/hermes
```
Then patch `monitor-agent.sh` to use `$HERMES_BIN` directly instead of `$(command -v hermes)`.

**Diagnostic:**
```bash
# Returns nothing from a bare bash -lc (the launchd context):
/bin/bash -lc 'command -v hermes; echo "rc=$?"'
# But works in an interactive/login shell:
bash -l -c 'command -v hermes; echo "rc=$?"'
```

## Prod Gateway PID Alive but HTTP Port Not Listening

**Symptom:** PID alive (ps shows `hermes gateway`), but `curl localhost:8643/health` returns nothing. Gateway.err.log shows no startup errors — HTTP server never bound the port.

**Diagnostic sequence:**
```bash
# Confirm process alive
ps aux | grep hermes gateway | grep -v grep
# Check if port is actually listening
lsof -i :8643 -P
# Check gateway.err.log for startup sequence
grep -E "ready|starting HTTP|error" ~/.hermes_prod/logs/gateway.err.log | tail -10
# If port not listening but process alive: hard restart
launchctl bootout gui/$(id -u)/ai.hermes.gateway
launchctl load -w ~/Library/LaunchAgents/ai.hermes.gateway.plist
sleep 5 && curl -s --max-time 3 http://localhost:8643/health
```

**Known trigger:** ECONNRESET storms on the Slack WebSocket can leave the gateway process alive but the HTTP server in a broken state. Process doesn't crash but stops accepting new connections.

## Slack E2E Matrix (rc=6 when 2+ failures)

**6 sub-checks:**
| Check | Typical result | Notes |
|-------|---------------|-------|
| `dm_no_mention` | ✅ ok | DM routing now working (2026-05-28 fix) |
| `dm_with_mention` | ✅ ok | |
| `channel_no_mention` | ✅ ok (usually) | Can intermittently fail — see below |
| `channel_with_mention` | ✅ ok | |
| `thread_no_mention` | ✅ ok | |
| `thread_with_mention` | ✅ ok | |

**Current typical result (2026-05-28+):** 6/6 pass. DM routing fixed; all 6 now pass consistently. If DM tests drop back to 2/6, the DM routing regression has recurred.

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

## Memory Lookup (rc=3 when timeout)

**Command:** `timeout 30 hermes mem0 search "test"`

**Backend:** Qdrant at `localhost:6333` (Docker)

**Root cause pattern (2026-05-28 update):**
The `run_memory_lookup_probe()` function uses `bash -lc` to run the `hermes` CLI. Launchd's `bash -lc` subshells lose nvm's PATH additions — `hermes` is invisible even after sourcing `nvm.sh`. This causes the command to timeout (rc=124), which the monitor reports as rc=3.

**Correct fix (applied to monitor-agent.sh lines ~1260-1270):**
```bash
# Explicitly prepend the nvm bin path inside the bash -lc subshell
memory_output="$(timeout "$memory_timeout" bash -lc 'export NVM_DIR="$HOME/.nvm" && export PATH="$NVM_DIR/versions/node/v22.22.0/bin:$PATH" && '"${memory_cmd}"' ' 2>&1)"
```
Sourcing `nvm.sh` alone does NOT reliably add node/bin to PATH in daemon subshells. The direct PATH prepend is deterministic.

**Fallback if still not found:**
```bash
memory_output="$(timeout "$memory_timeout" bash -lc 'export NVM_DIR="$HOME/.nvm" && export PATH="$NVM_DIR/versions/node/v22.22.0/bin:$PATH" && $HOME/.nvm/versions/node/v22.22.0/bin/hermes mem0 search "test"' 2>&1)"
```

**Also unified to `hermes mem0 search`:** The legacy `hermes memory search` subcommand was deprecated; both branches of the if/else now use `mem0`.

**Diagnostic steps:**
1. `curl -s http://localhost:6333/collections` — confirm Qdrant is healthy (not the problem)
2. `timeout 15 bash -lc 'export NVM_DIR="$HOME/.nvm" && export PATH="$NVM_DIR/versions/node/v22.22.0/bin:$PATH" && hermes mem0 search "test"'` — confirms bash -lc can find hermes with explicit PATH
3. If both Qdrant AND the explicit PATH bash -lc work but monitor still fails → monitor-agent.sh not patched with the fix yet

**Log pattern (intermittent):**
```
memory_lookup rc=0 summary=memory lookup returned results
memory_lookup rc=3 summary=memory lookup command failed (rc=124)
```

## `hermes` CLI Hangs Independently (rc=124)

**Symptom:** `hermes message send`, `hermes status --json`, `hermes health`, `hermes config get` all hang indefinitely — the CLI doesn't even reach the gateway. Gateway itself is healthy (`curl localhost:8644/health` returns `{"ok":true,"status":"live"}`).

**Root cause:** The `hermes` CLI (Node.js binary at `~/.nvm/versions/node/v22.22.0/bin/hermes`) hangs on startup or an internal auth/session step when invoked in certain shell contexts. This is **not a gateway failure** — the gateway is running fine. The hang is in the CLI-to-gateway handshake or a blocking session init.

**Diagnostic:**
```bash
# This hangs:
timeout 10 hermes status --json  # → rc=124 (timeout)

# But the gateway is fine:
curl -s --max-time 3 http://localhost:8644/health
# → {"ok":true,"status":"live"}

# And the CLI binary is present:
ls ~/.nvm/versions/node/v22.22.0/bin/hermes
# → file exists
```

**Impact on monitor:** Both the **Slack E2E** probe (`hermes message send`) and the **Memory** probe (`hermes mem0 search`) use the `hermes` CLI and fail/hang identically. This means a single root cause (`hermes` CLI hangs) can produce two independent red failures in the monitor report.

**Does NOT affect:** The gateway's own Slack WebSocket and HTTP health — those are independent of the CLI.

**When to investigate:** If `curl localhost:8644/health` is healthy but `hermes status` hangs, the CLI itself is the problem, not the gateway.

## AO Version Warning

**Check:** Compares running `ao --version` against `npm view @jleechanorg/ao-cli version`

**Stale warning pattern (2026-05-27):** Monitor reported 0.1.0 vs 0.1.3, but both `~/bin/ao` and npm global were already 0.1.3. The monitor may cache or read a stale binary path. Verify with:
```bash
which -a ao
ao --version
npm list -g @jleechanorg/ao-cli
```

## Token Probes

**WARN:mem0.openai.apiKey:missing/placeholder** — This is optional if using a different embedding provider (e.g., local embeddings or a proxy). Not a health issue unless mem0 search actually fails with auth errors.

## Staging Gateway (8644) Restart

**Symptom:** `ai.hermes.staging` registered in launchctl but port 8644 not listening.

**Fix (2026-05-28):**
```bash
# Use bootstrap, not load — load fails with I/O error on user-level GUI services
launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.hermes.staging.plist

# Verify
sleep 5 && lsof -P -n -i :8644 && curl -s --max-time 5 http://127.0.0.1:8644/health
```

**Dual-profile architecture:** Staging (8644) and prod (8643) are independent. Staging handles the memory probe; prod handles Slack E2E and core monitoring. Both must be healthy for all-clear.

## MiniMax Token Plan rate-limit spike (HTTP 429)

**Symptom:** Slack thread shows `:arrows_counterclockwise: Primary model failed — switching to fallback: MiniMax-M2.7 via minimax` — but the same MiniMax model is the only configured model (no distinct fallback exists). E2E stays at 6/6.

**Root cause:** MiniMax's Token Plan hit HTTP 429 with:
```
"The Token Plan is designed for individual, interactive developer workflows.
Traffic is currently high—please retry shortly. For higher concurrency or
automated workloads, consider upgrading to a higher-tier plan or using the
pay-as-you-go API. (2062)"
```

**What the Slack message actually means:** The gateway tried MiniMax, got rate-limited, found no fallback model, and surfaced the error directly. The "switching to fallback" wording is misleading — `fallbackConfigured: false` means no separate fallback exists. The error surfaced, not was recovered from.

**Diagnostic:**
```bash
grep "embedded_run_failover_decision" /tmp/hermes/hermes-$(date +%Y-%m-%d).log 2>/dev/null | tail -5
```

Key fields to extract from the event JSON:
```
failoverReason: "rate_limit"
profileFailureReason: "rate_limit"
fallbackConfigured: false   ← no separate fallback model
decision: "surface_error"   ← error surfaced to user, not auto-recovered
httpCode: "429"
providerRuntimeFailureKind: "rate_limit"
```

**Severity:** 6/6 E2E pass + this message = transient MiniMax rate-limit, not a system failure. The Slack reply still went through. No action needed for single occurrences.

**Long-term fix:** Add a distinct fallback model to `~/.hermes_prod/config.yaml` under `models.providers`. With `fallbackConfigured: true`, the gateway will retry automatically on 429 instead of surfacing the error.

## Gateway Startup Warning: `duplicate plugin id detected`

**Symptom:** Both prod and staging gateways log on startup:
```
Config warnings:\n- plugins.entries.hermes-mem0: plugin hermes-mem0: duplicate plugin id detected; global plugin will be overridden by config plugin ($HOME/.hermes_prod/extensions/hermes-mem0/index.ts)
```

**Root cause:** The `hermes-mem0` plugin is registered both as a global plugin (bundled with Hermes) and as a local extension in `~/.hermes_prod/extensions/hermes-mem0/`. The local config entry overrides the global one, which is the correct behavior. The warning is cosmetic and does not affect functionality.

**Action:** None required. If the warning is undesirable, remove the duplicate entry from `config.yaml` `plugins.entries` — but the local override is intentional for version control, so leaving it is fine.

## Qdrant Dual-Provider Conflict (Docker + Native)

**Symptom:** Monitor reports `memory_lookup rc=3` with "Qdrant connection refused" during a brief window, then recovers on next cycle.

**Root cause:** Two Qdrant providers target the same port 6333 and storage directory (`~/.hermes/qdrant_storage/`):
1. Native binary (`~/.local/bin/qdrant`, PID via `ai.hermes.qdrant` launchd) — started first
2. Docker container (`hermes-mem0-qdrant`) — started second, lost the port race, exited 255

When the native binary starts and binds port 6333 first, the Docker container's port bind fails and it exits. If the memory probe fires during the ~13-second gap (native just starting, Docker already dead), the probe gets `connection refused` (rc=3).

**Diagnostic:**
```bash
# Check which Qdrant is running
lsof -i :6333 -P -n | head -5
# Should show: qdrant <PID> (native binary), not Docker
# Check if Docker container exists (may be stopped)
timeout 5 docker ps -a --filter name=hermes-mem0-qdrant 2>&1
```

**Latent risk:** If Docker Desktop restarts and the native binary is down (e.g., after a reboot race), the Docker container could win the port race and bind 6333 with different storage semantics. Conversely, if both try to start simultaneously, one loses and the probe may catch the gap.

**Recommended fix:** Remove the Docker Qdrant container permanently since the native binary via launchd is the canonical provider:
```bash
docker rm -f hermes-mem0-qdrant 2>/dev/null || true
# The install script at scripts/install-qdrant-container.sh is superseded
# by the native binary at ~/.local/bin/qdrant with ai.hermes.qdrant launchd plist
```

**Recovery:** If the monitor flags rc=3, check `lsof -i :6333` first. If the native binary is listening, the failure was transient and will self-resolve on the next cycle.