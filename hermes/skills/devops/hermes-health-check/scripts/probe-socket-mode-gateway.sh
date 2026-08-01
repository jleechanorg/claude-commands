#!/usr/bin/env bash
# probe-socket-mode-gateway.sh — Decide whether a watchdog "port 8643 DOWN" alert
# is a real outage or a false-positive caused by a Socket-Mode-only gateway
# (no api_server binding TCP).
#
# Use when:
#   - Watchdog/agent says gateway is DOWN but the process appears alive
#   - Want to confirm before doing a launchctl restart (which can churn AGENTS)
#
# Reads:
#   $HERMES_HOME/gateway.pid  — written by start_gateway()
#   ~/.hermes/logs/gateway.log — Socket Mode connect log
#   API_SERVER_ENABLED env var in gateway launchd plist
#
# Outputs three diagnoses:
#   REAL OUTAGE — pid missing, no Slack, alert is genuine
#   FALSE POSITIVE — pid alive + Slack connected + port not expected to listen
#   PORT BINDING ISSUE — pid alive but api_server expected, port dead
#
# Run: bash scripts/probe-socket-mode-gateway.sh [HERMES_HOME]
HERMES_HOME="${1:-${HERMES_HOME:-$HOME/.hermes}}"

set +e
echo "=== Socket-Mode Gateway Probe ==="
echo "HERMES_HOME = $HERMES_HOME"
echo

# 1. PID file / process liveness
PID_FILE="$HERMES_HOME/gateway.pid"
if [[ -f "$PID_FILE" ]]; then
  PID=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('pid',''))" "$PID_FILE" 2>/dev/null)
  if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
    echo "[OK] gateway PID $PID is alive"
  else
    echo "[REAL OUTAGE] PID file exists but process $PID is gone"
    exit 1
  fi
else
  echo "[REAL OUTAGE] No PID file at $PID_FILE — gateway never started"
  exit 1
fi

# 2. Slack Socket Mode connected?
GATEWAY_LOG="$HERMES_HOME/logs/gateway.log"
if [[ -f "$GATEWAY_LOG" ]]; then
  if grep -qE "Socket Mode connected|Authenticated as" "$GATEWAY_LOG" 2>/dev/null; then
    LAST_CONNECT=$(grep -E "Socket Mode connected|Authenticated as" "$GATEWAY_LOG" | tail -1)
    echo "[OK] Slack Socket Mode appears connected: $LAST_CONNECT"
  else
    echo "[WARN] No Socket Mode connect log found in $GATEWAY_LOG"
  fi
else
  echo "[WARN] No gateway.log at $GATEWAY_LOG"
fi

# 3. Port 8643 binding — check both process and system
PORT_PID=$(lsof -nP -iTCP:8643 -sTCP:LISTEN -t 2>/dev/null | head -1)
if [[ -n "$PORT_PID" ]]; then
  echo "[OK] Port 8643 is LISTEN (pid $PORT_PID) — api_server is enabled and healthy"
  exit 0
fi

# 4. Is api_server expected? Check launchd plist for API_SERVER_ENABLED.
PLIST="$HOME/Library/LaunchAgents/ai.hermes.gateway.plist"
if [[ -f "$PLIST" ]] && grep -qE "API_SERVER_ENABLED" "$PLIST" 2>/dev/null; then
  PLIST_VAL=$(plutil -extract EnvironmentVariables.API_SERVER_ENABLED raw "$PLIST" 2>/dev/null)
  if [[ "$PLIST_VAL" == "true" ]]; then
    echo "[PORT BINDING ISSUE] api_server expected but nothing on :8643 — PID alive, Slack connected, but api_server failed to bind"
    echo "  Likely: api_server platform not in config.yaml, or it crashed at startup"
    echo "  Action: check gateway.error.log for api_server traceback"
    exit 2
  fi
fi

# 5. Default case: gateway is Socket-Mode-only, watchdog misfired
echo "[FALSE POSITIVE] Gateway alive + Slack connected + NOTHING on :8643"
echo "  This is a Socket-Mode-only deployment. The watchdog's HTTP probe is wrong."
echo "  Fix: patch scripts/hermes-watchdog.sh to use PID-file liveness (primary)"
echo "  See commit 4c8ef8ac7d on jleechanorg/jleechanclaw for the canonical fix."
exit 0
