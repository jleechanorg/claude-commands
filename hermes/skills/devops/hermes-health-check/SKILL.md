---
name: hermes-health-check
description: Diagnose Hermes gateway health, Hermes monitor issues, and launchd service failures. Run when the user shares a monitor report, says "is everything ok", "check Hermes", "hermes is down", "slack-digest failed", "cronjob response failed", or when a launchd service exits with code 127 (command not found). Covers provider-layer triage (MiniMax 429, OpenRouter 402/401, fallback exhaustion), gateway-vs-port confusion, dual-profile DM races, foreign-cron relay (bot this session can't see), and the dead-API-key vs out-of-credits diagnostic probe.
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

### Stale worktree path baked into multiple plists (exit 127, fan-out class)

**Symptom (verified 2026-07-22, GH Actions Cost Monitor + Spend Alert + 3 sibling jobs):**
- `launchctl list` shows multiple `ai.hermes.*` rows with `- 127` in the exit-code column.
- Log tail shows `/bin/bash: /path/to/deleted/worktree/scripts/foo.sh: No such file or directory` written by `bash` itself before any user-script code runs.
- Each scheduled tick fires launchd, launchd forks `/bin/bash`, bash tries to `exec` the first arg (the dead path), bash exits 127. No script-level logging. No Slack notification. **Silent OK from launchd's POV** (exit 127 ≠ non-zero in launchd's "last run" semantic — the job will keep firing on the next interval).

**Root cause — a previous harness install substituted the wrong REPO_ROOT:**
The Hermes launchd plist templates use `@REPO_ROOT@/scripts/<file>` placeholders. When a one-off harness install (e.g. `jleechanclaw-harness-9` worktree) was active at substitution time, every plist rendered to:
```
$HOME/.ao/data/worktrees/jleechanclaw-harness/jleechanclaw-harness-9/scripts/launchd-env-wrapper.sh
```
After that worktree is deleted, every plist that captured the path during install silently breaks. **The fix is the plist path, NOT the script** — `~/.hermes/scripts/<file>.sh` already exists.

**5-minute triage for "launchctl shows 127 on multiple jobs at once":**
```bash
# 1. Confirm the fan-out: how many plists are broken with the same root path?
launchctl list | awk '$2 == 127 {print $3}' | sort -u | head -20
grep -l "jleechanclaw-harness-9\|worktrees/" ~/Library/LaunchAgents/*.plist 2>/dev/null

# 2. Sanity-check the canonical paths exist
ls $HOME/.hermes/scripts/launchd-env-wrapper.sh \
   $HOME/.hermes/scripts/gh-actions-cost-monitor.sh \
   $HOME/.hermes/scripts/spend-alert-daily.sh 2>&1

# 3. Patch each plist: replace the stale worktree prefix with the canonical HERMES_HOME.
# Use the env-var-from-bashrc helper if it exists, otherwise hard-code HOME:
sed -i.bak 's|$HOME/.ao/data/worktrees/jleechanclaw-harness/jleechanclaw-harness-9/scripts|$HOME/.hermes/scripts|g' \
    ~/Library/LaunchAgents/<label>.plist

# 4. Reload and verify — column 2 should be 0 (not 127) after the next tick
launchctl unload ~/Library/LaunchAgents/<label>.plist 2>&1
launchctl load -w ~/Library/LaunchAgents/<label>.plist 2>&1
launchctl list | grep <label>
# Expect: "- 0 ai.hermes.schedule.<label>"
```

**Why this fires silently:** Unlike a script that aborts via `set -e` (which produces log lines), bash's own "no such file" exits immediately at the wrapper layer, before stderr redirection reaches `StandardErrorPath`. So the log file shows only the bash error line, no script-level context, no Slack post. The `dropped-thread-watcher-of-watchers` SOUL.md COMMIT covers the same shape at a higher level — every cron needs a watcher-of-watchers because silent OK exits are launchd's default.

**Auditor recipe — find all plists with stale worktree paths before they bite:**
```bash
# Run this BEFORE any harness install/uninstall to detect the pattern early.
for f in ~/Library/LaunchAgents/*.plist; do
    if grep -q "worktrees/" "$f" 2>/dev/null; then
        echo "STALE: $f"
        grep -A1 ProgramArguments "$f" | head -3
    fi
done
```

**Long-term fix (the durable pattern):**
- All Hermes launchd plist templates MUST live in `~/.hermes/launchd/*.plist` with `@HOME@`/`@REPO_ROOT@` placeholders, per `hermes-deploy-pipeline`.
- The install pipeline (`scripts/setup-launchd.sh`) is the ONLY place that substitutes `@REPO_ROOT@`. If it ever substitutes to a non-canonical path (a worktree, a different machine), it MUST update the canonical plist template and rerun — never write a one-off plist to `~/Library/LaunchAgents/` with a non-canonical REPO_ROOT.
- Add the auditor recipe above as a daily launchd job (`ai.hermes.schedule.launchd-path-audit.plist`) that posts a Slack alert to `#ai-general` if any loaded plist has `worktrees/` or `~/<ephemeral>/` in its ProgramArguments.

**Runnable auditor:** `scripts/audit-launchd-stale-paths.sh` — exits 1 with the offending plist paths when any stale reference is detected. Run it before deleting any harness worktree, or as a daily launchd watcher.

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

### Watchdog "gateway DOWN (port 8643)" false-positive on Socket-Mode-only deployments

**Symptom (2026-07-09):** `hermes-watchdog.sh` fires `:rotating_light: Hermes prod gateway DOWN (port 8643) — sustained 4 checks (~20 min)` despite the gateway being healthy: Socket Mode connected, actively processing inbound Slack messages, agent cache functioning. Alert posts every 5 minutes. Streak counter climbs to 18+ within 90 minutes of gateway startup.

**Root cause:** The watchdog unconditionally probes `http://localhost:8643/health`, but the **prod Hermes gateway is a Slack Socket Mode client that never binds a TCP port by default**. The `api_server` platform is force-disabled by `scripts/launchd-env-wrapper.sh` lines 81-86:
```bash
# Prod path: api_server is not deployed. Force-disable...
unset API_SERVER_ENABLED
unset API_SERVER_PORT
unset API_SERVER_KEY
```
So nothing ever listens on 8643, and the curl probe returns connection-refused forever. The watchdog reports a phantom outage, not a real one.

**How to recognize this in 30 seconds:**
```bash
# 1. Gateway process is alive?
ps aux | grep "hermes gateway" | grep -v grep
# 2. Slack Socket Mode actually connected?
grep -E "Socket Mode connected|Connecting to slack|Authenticated as" \
  ~/.hermes/logs/gateway.log | tail -5
# 3. Is the watchdog probing a port that's expected to listen?
curl -sf -m 3 http://localhost:8643/health
# expected: 7 (connection refused) — NOT a real outage, just an absent api_server
# 4. Is API_SERVER_ENABLED set?
env | grep API_SERVER
# expected: empty (prod force-disables it)
```

**The fix (canonical):** Patch `scripts/hermes-watchdog.sh` to use **PID-file liveness** (`$HERMES_HOME/gateway.pid` + `kill -0`) as the primary health probe, and demote the HTTP `/health` probe to a secondary signal gated on `API_SERVER_ENABLED=true`. See commit `4c8ef8ac7d` on `jleechanorg/jleechanclaw` `dev1783275795` for the full patch.

```bash
# New probe order in hermes-watchdog.sh:
check_pid_alive() {                                  # PRIMARY
  local pid_file="$HERMES_HOME/gateway.pid"
  [[ -f "$pid_file" ]] || return 1
  local pid; pid=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('pid',''))" "$pid_file" 2>/dev/null) || return 1
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

if check_pid_alive "prod"; then
  if [ "${API_SERVER_ENABLED:-false}" = "true" ]; then
    check_gateway "prod" 8643   # probe api_server only when it's enabled
  else
    # Socket-Mode-only deployment — PID liveness IS the health signal
    PROD_HEALTHY=true
  fi
fi
```

**After-streak recovery:** Reset stale counters so the false-positive streak doesn't carry over:
```bash
rm -f /tmp/hermes/watchdog-state/prod.streak /tmp/hermes/watchdog-state/prod.last_alerted_streak
```

**Verify the fix:**
```bash
HERMES_HOME=$HOME/.hermes bash $HOME/.hermes/scripts/hermes-watchdog.sh
# expected: "prod gateway: healthy (pid file, socket-mode)" + streak stays 0
```

**Companion concern — alert channel routing:** Watchdog alerts default to `HERMES_WATCHDOG_ALERT_CHANNEL` (legacy: `C09GRLXF9GR` = #all-$USER-ai) with `HERMES_OPS_SLACK_CHANNEL` as fallback. Per `~/.hermes/config.yaml` `SLACK_HOME_CHANNEL: C0AJQ5M0A0Y` (= #ai-general = the home channel for system-generated messages), the plist should pin both env vars to `C0AJQ5M0A0Y`. After pinning, `launchctl bootout gui/$(id -u)/ai.hermes.watchdog && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes-watchdog.plist` to pick up the new env. Every launchd plist also requires a committed template at `~/.hermes/launchd/<label>.plist.template` per env-preferences.mdc — write the template FIRST, then derive the deployed plist by substituting `@HOME@`.

### Gateway Startup Warning: `duplicate plugin id detected`

**Symptom:** Both gateways log on startup:
```
Config warnings:\n- plugins.entries.hermes-mem0: plugin hermes-mem0: duplicate plugin id detected; global plugin will be overridden by config plugin ($HOME/.hermes_prod/extensions/hermes-mem0/index.ts)
```
This is cosmetic — the local extension correctly overrides the global plugin. No action needed. See `references/hermes-monitor-checks.md` for details.

### Qdrant Dual-Provider Conflict (Docker + Native)

**Symptom:** Monitor reports `memory_lookup rc=3` transiently (brief "connection refused" window) then recovers on next cycle. Root cause: both Docker `hermes-mem0-qdrant` and native `~/.local/bin/qdrant` (launchd) target port 6333 on the same storage dir. When the native binary wins the port race, the Docker container exits 255, but a brief gap can cause the probe to fail. **Fix:** Remove the Docker container (`docker rm -f hermes-mem0-qdrant`) and rely on the native launchd service. See `references/hermes-monitor-checks.md` for full diagnostic and recovery steps.

## doctor.sh Output Interpretation

**IMPORTANT — config context:** `doctor.sh` validates the config at `$LIVE_HERMES/config.yaml`. It may be run against the **staging profile** (`.hermes/`) even when the **production gateway** (`.hermes_prod/`) is the live service. The staging `.hermes/config.yaml` is often a **minimal skeleton** with only `plugins` and `channels` top-level keys — no `agents`, `models.providers`, `heartbeat`, etc. Doctor flags these missing fields as FAILs, but this is **expected for a skeleton staging config** and does not indicate the production gateway is unhealthy.

**Diagnostic sequence when doctor.sh shows multiple FAILs:**
```bash
# 1. Confirm which profile doctor is actually validating
grep "Live Hermes dir:" <(bash $HOME/.hermes/scripts/doctor.sh 2>&1)

# 2. Verify the actual prod gateway health separately:
curl -s --max-time 3 http://localhost:8644/health
#    If that returns {"ok":true,"status":"live"} → prod gateway is healthy, doctor FAILs are config-context artifacts.

# 3. Run doctor against prod explicitly to see the true health:
HERMES_STATE_DIR=$HOME/.hermes_prod bash $HOME/.hermes/scripts/doctor.sh 2>&1 | tail -80
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
6. `$HOME/.hermes/jleechanclaw/doctor.sh`
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
### Canary / SLO / fleet-watchdog alerts from jleechanorg/ez-gh-actions

**This is a DIFFERENT class of alert than the Hermes monitor above.** The `ez-gh-actions` project (Rust daemon + workflow_dispatch canary + bash fleet-watchdog) posts its own `[ez-gh-actions:WARNING]` style Slack messages. When one lands, treat it as "investigate a third-party watchdog claim" — don't trust the framing, validate against the actual run data.

**Trigger phrases you'll see:**
- `[ez-gh-actions:WARNING] ezgha canary SLO breach`
- `[ez-gh-actions:ERROR] fleet below target`
- `[ez-gh-actions:INFO] canary completed` (usually fine, no investigation needed)

**Canonical investigation order (90 seconds to root cause):**

1. **Get the run itself.** From the alert body, extract the `run_id` and hit the run API:
   ```bash
   gh api repos/jleechanorg/ez-gh-actions/actions/runs/<RUN_ID> \
     --jq '{id,status,conclusion,created_at,run_started_at,event,display_title}'
   gh api repos/jleechanorg/ez-gh-actions/actions/runs/<RUN_ID>/jobs \
     --jq '.jobs[] | {id,name,started_at,completed_at,runner_id,runner_name,labels,conclusion}'
   ```
   Compute the actual `time_to_start_seconds = job.started_at - run.created_at`. If it's under the SLO (90s default), the alert is a false positive — confirm by reading the watchdog's own log.

2. **Read `/tmp/ezgha-watchdog.log`** (the bash fleet watchdog — distinct from the Rust canary scheduler). Tail 100 lines:
   ```bash
   tail -100 /tmp/ezgha-watchdog.log
   ```
   Look for `BELOW TARGET`, `WARN: one or more hosts missing`, or `consecutive=N` patterns. The bash watchdog uses `consecutive<=2` before auto-restarting, which means a **persistent drain can sit at `consecutive=1` for hours** if the auto-recovery step keeps resetting the counter (common: COLIMA `state=Stopped` → auto-start → `configured=6 actual=` empty → reset).

3. **Confirm the daemon is up:**
   ```bash
   launchctl list | grep -E 'ezgha|ez-gh'
   # Look for a PID on org.jleechanorg.ezgha (the Rust daemon)
   ```
   Exit code `-15` (SIGTERM) is normal — the daemon self-restarts every ~15 min during the canary scheduler cycle.

**Critical pitfall — the "unmeasured != breached" race in `src/canary.rs:303-305`:**

The canary's `slo_breached` computation has a known anti-pattern:
```rust
let slo_breached = time_to_start_seconds
    .map(|secs| secs > slo_start_seconds as i64)
    .unwrap_or(run.status == "completed");  // <-- the trap
```

When the canary's poll catches the run row already `completed` but the job row's `started_at` is briefly `null` on that snapshot (REST eventual consistency for fast 50s jobs), `time_to_start_seconds` is `None` → `slo_breached` is forced to `true` → `should_alert()` fires with `time_to_start=Nones`. The alert body literally tells you the field is `None` — that's the signature of this false-positive race.

**How to confirm it's the race vs. a real SLO breach:**
- Alert body shows `time_to_start=Nones` → race bug, not a real breach.
- Alert body shows `time_to_start=NNNs` with N > 90 → real SLO breach; investigate runner registration delays.
- Alert body shows `time_to_start=NNNs` with N <= 90 → daemon logic bug; the SLO check itself is wrong.

**Masked real outages — fleet drain hiding behind canary chatter:**

The fleet-watchdog logs are independent of the canary scheduler. A persistent `[ez-gh-actions:WARNING] fleet below target` (Linux `configured=16, managed=0` for 95+ minutes, observed 2026-07-10) can sit silently in `/tmp/ezgha-watchdog.log` while the canary keeps firing false-positive SLO alerts on the **mac fleet** (which is healthy). The mac canary at 50s start vs. 90s SLO looks fine in isolation but the alert payload has `time_to_start=Nones` due to the race bug — masking the real Linux drain.

**Diagnostic commands specific to jleechanorg/ez-gh-actions:**

```bash
# 1. Recent selftest history (canary cadence + success rate)
gh api 'repos/jleechanorg/ez-gh-actions/actions/runs?workflow_file=selftest.yml&per_page=20' \
  --jq '.workflow_runs[] | "\(.id) \(.created_at) \(.status) \(.conclusion // "-") \(.event) \(.display_title)"'

# 2. Linux fleet drain signal (look for long-running "BELOW TARGET" streaks)
grep -E 'BELOW TARGET|WARN.*unreachable|consecutive=' /tmp/ezgha-watchdog.log | tail -20

# 3. COLIMA state on the Linux box (if applicable)
ssh jeff-ubuntu 'systemctl --user status ezgha 2>&1 | head -20'

# 4. Last few daemon restarts (SIGTERM = -15)
grep -E 'ezgha' /var/log/com.apple.xpc.launchd/launchd.log 2>/dev/null | tail -5
# OR for user-level launchd:
log show --predicate 'subsystem == "com.apple.launchd"' --last 1h 2>/dev/null | grep ezgha | tail -10
```

**When you decide to patch the false-positive race:**

The minimal fix is changing `.unwrap_or(run.status == "completed")` to `.unwrap_or(false)`. But that suppresses legitimate "could not measure" alerts too. The recommended fix is to introduce a `measurement: "ok" | "incomplete"` enum in `CanaryResult`, set `slo_breached = false` when measurement is incomplete, and surface the incomplete measurement as a separate (lower-severity) alert category. Don't ship the one-line fix without considering the second case.

**Long-term fixes to land in a follow-up PR (not in the alert-investigation PR):**
- Tighten the `consecutive<=2` guard in `ezgha-fleet-watchdog.sh` — use time-based backoff (1h of < target → restart) instead of tick-based.
- Separate the canary alert channel from the fleet-watchdog alert channel so a canary false positive doesn't drown out a real fleet outage.
- The existing test `result_does_not_accept_wrong_runner_prefix_from_fallback_job` at canary.rs:481 codifies the "missing field = breach" anti-pattern as expected behavior — when you fix the race, fix those tests too.

**References:**
- `references/hermes-monitor-checks.md` — Hermes monitor checks (separate concern).
- `references/ez-gh-actions-watchdog-diag.md` — full investigation script + log-format reference for the ezgha canary/fleet-watchdog alert class.

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

### User reports "nothing happening" on Slack — provider-layer triage (canonical recipe, 2026-07-14)

**Symptom:** A Slack user (typically Jeffrey in a channel like `#needs-jeff` / `C0BGM3A4ZC0`) posts "someting broken how come nothing ever happening here?" or an equivalent "I asked X 30 min ago and got no reply." The gateway log shows repeated `[Slack] Send error: cannot_reply_to_message` errors. The monitor may or may not flag anything — the failure is at the model provider layer, not the gateway transport.

**Anti-pattern (will burn 1-2 hours):** Stop at "Slack returned `cannot_reply_to_message`" and assume it's a channel-membership or token-routing issue. **It is not.** `cannot_reply_to_message` is downstream noise — the agent run failed before producing a reply, the gateway's stale queued response gets retried, and each retry emits this error. The actual cause is upstream of Slack entirely.

**Canonical 90-second triage (run in parallel, not serial):**

1. **launchd state** — `launchctl print gui/$(id -u)/ai.hermes.prod | grep -E 'state =|pid =|last exit'` → confirm gateway is running (state=running, pid > 0). If state != running, restart first; if state == running, the gateway is fine and the issue is downstream.

2. **Slack bot-token probe of the affected channel** — proves whether the bot can post AT ALL, independent of model health:
   ```bash
   BOT_TOKEN=$(grep '^export SLACK_BOT_TOKEN=' ~/.profile | head -1 | sed 's/export SLACK_BOT_TOKEN=//; s/"//g')
   curl -fsS -X POST https://slack.com/api/chat.postMessage \
     -H "Authorization: Bearer $BOT_TOKEN" -H "Content-Type: application/json; charset=utf-8" \
     -d "{\"channel\":\"C0BGM3A4ZC0\",\"thread_ts\":\"<user_msg_ts>\",\"mrkdwn\":false,\"text\":\"[diagnostic probe — will delete]\"}"
   # Then chat.delete on the returned ts.
   ```
   `ok:true` from both → bot CAN post in this channel. The failure is upstream. `not_in_channel` or `missing_scope` → real channel-membership issue, but rare; check `conversations.members` first.

3. **Primary model provider probe** — proves the configured primary is healthy:
   ```bash
   curl -fsS -X POST "${MINIMAX_BASE_URL}/v1/messages" \
     -H "x-api-key: ${MINIMAX_API_KEY}" -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"MiniMax-M3","max_tokens":32,"messages":[{"role":"user","content":"Reply with the single word pong."}]}'
   # Expected: HTTP 200 with content[0].text="pong"
   # 429 → primary rate-limited; check fallback chain
   # 401/403 → primary credential rotated; check ~/.bashrc / ~/.profile drift
   ```

4. **Fallback provider probe** — proves the configured fallback (if any) is healthy. The probe URL depends on whatever the live `~/.hermes/config.yaml` `providers:` block names — substitute as needed:

   ```bash
   # EXAMPLE probe (vendor-specific, NOT a constant). Check the live config first:
   grep -E '^\s+-?\s*(provider|name):' ~/.hermes/config.yaml | head -10
   # Then probe whichever provider is in the fallback_providers list.
   #
   # The historic 2026-07-14 example was:
   #   POST https://opencode.ai/zen/go/v1/chat/completions  /  model: glm-5.1
   # That provider was REMOVED from this config on 2026-07-16 — see swap-hermes-provider.
   # The shape of the probe stays the same; only the URL and model id vary.
   #
   # Response codes:
   #   200 → fallback works.
   #   429 + GoUsageLimitError (or equivalent quota-exhaustion error body) →
   #     vendor-specific MONTHLY workspace quota exhausted; recovers in days/weeks.
   #     Gateway retry loop will hammer this for the entire reset window unless
   #     suppressed (see Long-term fix below).
   #   403 + error code: 1010 → Cloudflare blocking egress; key fine.
   ```

**Reading the gateway error log alongside the probes:**
- `[Slack] Send error: cannot_reply_to_message` → downstream noise from queued retries; ignore as cause.
- `Switching to fallback: <model> via <provider>` → primary failed, fallback chain kicked in.
- `HTTP 429: Monthly usage limit reached. Resets in N days. (GoUsageLimitError)` → fallback quota exhausted; THIS is the real cause. The `Resets in N days` field tells you how long the outage will last.
- `HTTP 429: rate limit exceeded(TPM) (1039)` → transient per-minute rate limit; recovers in seconds.

**Root-cause taxonomy:**

| Probe 2 | Probe 3 | Probe 4 | Root cause |
|---|---|---|---|
| ok | 200 | 200 | Gateway transport fine; transient in the specific agent run. Self-recovers. |
| ok | 429 | 200 | Primary rate-limited, fallback works. Self-recovers. |
| ok | 200 | n/a (no fallback) | Primary works. Transient; self-recovers. |
| ok | 429 | 429 (quota exhausted) | **Both providers quota-exhausted.** Gateway silently retries the dead fallback for the reset window. See Long-term fix. See also `swap-hermes-provider` for the fix-it recipe (drop the dead provider from `fallback_providers`). |
| ok | 401/403 | n/a | Primary credential rotated. Update ~/.bashrc AND ~/.profile (both). Restart gateway. |
| not_in_channel | n/a | n/a | Real channel-membership issue. `/invite @hermes` in channel. |

**Long-term fix (avoid the silent retry trap):** When the fallback hits any quota-exhaustion error class (e.g., `GoUsageLimitError`, vendor-specific 429 with a "Resets in N days" body, Cloudflare `error code: 1010`), the gateway default is to keep retrying for the reset window. Each retry consumes session budget on a dead-end. Suggested patch: `gateway/run.py` `resolve_runtime_provider()` matches on the error body's quota signature and short-circuits to the previous successful provider for 24h, surfacing a startup warning. Not yet shipped as of 2026-07-16; tracked as `$USER-tqy2` followup. Faster alternative when the quota-out is permanent: remove the dead provider from `~/.hermes/config.yaml` `fallback_providers` (see `swap-hermes-provider` skill — the worked example with `opencode-go/glm-5.1` is at `references/rm-opencode-go-glm51.md`).

**Recovery from a quota-exhaustion outage (no fix yet):**
1. Reply to the user in-thread via direct bot-token post (probe 2 path) with the root-cause explanation.
2. Wait for primary quota to refresh, OR temporarily edit `~/.hermes_prod/config.yaml` `fallback_providers` to remove the dead provider (one-line yaml edit; `launchctl kickstart -k gui/$(id -u)/ai.hermes.prod`). For a permanent quota-out, use the `swap-hermes-provider` skill to do the full removal across all six touch-points in `~/.hermes/config.yaml` + `~/.hermes/scripts/launchd-env-wrapper.sh` + the prod mirror.
3. Do NOT bounce the gateway hoping it will start working — gateway is fine; upstream is dead.

**What you should NOT do:**
- Do NOT add `SLACK_BOT_TOKEN` to the launchd plist directly — the wrapper already handles it from ~/.profile/~/.bashrc. Adding it directly can cause drift (see memory `bashrc-profile-xapp-drift-blocks-launchd`).
- Do NOT auto-schedule a "20-min status cron" preemptively. A cron's value is small when the gateway is alive and the user can re-ask — and a leaked status cron is itself a class of bug (see `babysit-stale-watchdog`). If you must schedule a watchdog, schedule a `gh pr view`-style PR-terminal cron, not a Slack status cron.
- Do NOT assume `not_in_channel` from the MCP slack tool means the running gateway can't post. The MCP tool may use a different bot identity than the gateway (verified 2026-07-14: `HERMES_SLACK_BOT_TOKEN` (`mcp_agent_mail` / U0A4G7LDJ4R) is `not_in_channel` on `C0BGM3A4ZC0`, but `SLACK_BOT_TOKEN` (`hermes` / U0AEZC7RX1Q) IS in the channel and posting works).
- Do NOT conclude "token is broken" from a single env probe. launchd jobs don't source `~/.bashrc` by default; the `_extract_bashrc_var` mechanism in `launchd-env-wrapper.sh` is the bridge. Inline sessions have the same trap from the `execute_code` side (clean Python subprocess doesn't source bashrc). For the canonical dual-probe recipe and worked example, see `cli-env-var-verification/references/execute_code-bashrc-env-isolation-dual-probe.md` (verified 2026-07-28).

**Bug-ref:** 2026-07-14 — `#needs-jeff` / `C0BGM3A4ZC0` / `ts 1784061033.250339`. The two `:warning: The model provider failed after retries.` messages from `hermes_pc` (B0BBUN50HQB) are the visible symptom. Root cause: `MiniMax-M3` returned HTTP 429 (Token Plan rate limit), fallback to `glm-5.1` via `opencode-go` hit `GoUsageLimitError` (monthly workspace cap, resets in 14 days). The 4-probe triage pinpointed both providers as dead in ~2 min. Direct bot-token post at `ts 1784061855.393669` confirmed the channel/token path is healthy. See `references/user-reports-nothing-happening-2026-07-14.md` for the full transcript and `swap-hermes-provider/references/rm-opencode-go-glm51.md` for the cleanup that followed on 2026-07-16 (the `opencode-go` provider was removed from `~/.hermes/config.yaml` + `~/.hermes_prod/config.yaml` + `launchd-env-wrapper.sh`, six touch-points, ~10 min wall time).

### Foreign-cron relay — "slack-digest failed" from a bot this session can't see

**Symptom (verified 2026-07-29):** A Slack thread receives a "Cronjob
Response: <name> failed: <error>" message from a bot identity like
`hermes_pc` (or any other foreign instance — different process, different
machine, or a different Hermes profile with its own cron DB). The job_id
in the message (e.g. `dbbbf6a173b5`) is NOT visible in this gateway's
`hermes cron list --all` and the corresponding label is NOT in
`launchctl list`.

**Anti-pattern (will burn 30+ min):** Try to `hermes cron update
<job_id>` or `hermes cron remove <job_id>` from this session. Returns
"job not found". Then try to inspect via `launchctl print
gui/$(id -u)/<label>` — also returns "service not found". Then dig into
the gateway's logs assuming the failure originated here. None of those
diagnostics will resolve anything because **the cron is not running on
this machine under this gateway**.

**How to recognize it in 30 seconds:**

```bash
# 1. Is the cron visible in this gateway's DB?
hermes cron list --all | grep -i <name>
# → empty? it's foreign. move on.

# 2. Is there a launchd plist for the label?
launchctl list | grep -i <label>
ls ~/Library/LaunchAgents/ai.hermes.schedule.<label>.plist 2>/dev/null
# → empty? it's foreign. move on.

# 3. Is the failure message from a bot identity this gateway owns?
mcp__slack__conversations_replies <thread> | grep -E 'BotName|UserName'
# Look for foreign bot names (hermes_pc, another bot) vs. U0AEZC7RX1Q
# (canonical Hermes bot).
```

**The right move:** treat the relay message as **external telemetry**
about an underlying problem (usually a credential, a vendor outage, or a
config drift). Fix the underlying cause in the place this session CAN
reach — typically a key in `~/.hermes/.env`, a config in
`~/.hermes_prod/config.yaml`, or a script under `~/.hermes/scripts/`. Do
NOT try to stop or inspect the foreign cron; this session has no handle
on it.

**Companion pattern** — `recurring-job-notifications` Pitfall 21 (added
2026-07-29) covers the most common relay cause: a dead vendor API key
surfaces as `HTTP 402: Insufficient credits` to the foreign cron,
relayed as a Slack alert that says "vendor out of credits" when the
actual problem is `401 User not found`. Probe the vendor's `/auth/key`
endpoint with the key from `~/.hermes/.env` before chasing the credit
path.

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

**Long-term fix:** Add a distinct fallback model OR drop `fallback_providers: []` so the gateway surfaces the 429 to Slack instead of looping. The historic recipe was "add `minimax/MiniMax-M2.5` or a different vendor" — that advice assumed at least one fallback was configured. As of 2026-07-16 the `opencode-go/glm-5.1` fallback was removed entirely (see `swap-hermes-provider`); if no replacement is added, the gateway will surface any further primary-provider 429 directly to Slack. Pick a fallback (single local + one cloud vendor is the suggested pattern) before relying on this surface-error path.

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
  storage_path: $HOME/.hermes/qdrant_storage
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
        <string>$HOME/.local/bin/qdrant</string>
        <string>--config-path</string>
        <string>$HOME/.local/etc/qdrant/config.yaml</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/.hermes/logs/qdrant.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.hermes/logs/qdrant.err.log</string>
    <key>WorkingDirectory</key>
    <string>$HOME/.hermes</string>
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
# → HERMES_STATE_DIR=$HOME/.hermes
# → HERMES_CONFIG_PATH=$HOME/.hermes/hermes.staging.json

# Prod plist points to .hermes_prod/ state dir
grep "HERMES_STATE_DIR\|HERMES_CONFIG_PATH" ~/.hermes_prod/launchd/ai.hermes.gateway.plist
# → HERMES_STATE_DIR=$HOME/.hermes_prod
# → HERMES_CONFIG_PATH=$HOME/.hermes_prod/config.yaml
```

**Why shared tokens are a risk:** When both gateways have active Socket Mode WebSockets with the same bot credentials, Slack may deliver events to one or both unpredictably. A DM sent to the bot could be picked up by prod, staging, both, or neither depending on which WebSocket session Slack routes to. The E2E matrix's `dm_no_mention` failures are likely a symptom of this race condition — the monitor sends a DM, but the gateway that picks up the event may not be the one the monitor is watching for a reply.

**Doctor.sh config context summary:**
- `bash doctor.sh` → validates `~/.hermes/hermes.staging.json` (skeleton) → many FAILs
- `HERMES_STATE_DIR=$HOME/.hermes_prod bash doctor.sh` → validates `~/.hermes_prod/config.yaml` (full prod) → true health picture
- Always run doctor against the actual live profile to get real results, not the skeleton staging config.

- `scripts/probe-socket-mode-gateway.sh` — 30-second decision script: is the watchdog's "port 8643 DOWN" a real outage or a Socket-Mode-only false-positive? Returns 0 (false positive / port-binding issue / real outage) with explanation. Run before any launchctl restart to avoid unnecessary churn.
- `scripts/hermes-gateway-quick-check.sh` — one-shot dual-profile health snapshot: both gateway ports, process+port bindings, Qdrant, Ollama, memory probe, latest errors.

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