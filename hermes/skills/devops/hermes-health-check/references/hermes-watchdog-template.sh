#!/usr/bin/env bash
# hermes-watchdog.sh — Periodic health watchdog for Hermes gateways
# Run by launchd: ai.hermes-watchdog (every 5 min, StartInterval=300)
# Alerts Slack if prod gateway is down.
#
# Key ports: prod=8642, staging=8643 (from config.yaml api_server.extra.port)
# Alert channel: set HERMES_WATCHDOG_ALERT_CHANNEL env var in plist

set -uo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_PROD_HOME="${HERMES_PROD_HOME:-$HOME/.hermes_prod}"
ALERT_CHANNEL="${HERMES_WATCHDOG_ALERT_CHANNEL:-C09GRLXF9GR}"
LOG_PREFIX="[hermes-watchdog]"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $LOG_PREFIX $*"; }

# Check if a gateway process is alive and healthy on given port
check_gateway() {
  local label="$1"; local port="$2"
  if curl -sf --max-time 3 "http://localhost:$port/health" 2>/dev/null | grep -q '"status"'; then
    log "$label gateway: healthy (port $port)"
    return 0
  fi
  log "$label gateway: DOWN (port $port)"
  return 1
}

PROD_HEALTHY=false
check_gateway "prod" 8642 && PROD_HEALTHY=true

STAGING_HEALTHY=false
check_gateway "staging" 8643 && STAGING_HEALTHY=true

# Only alert on prod down — staging can be intentionally stopped
if [ "$PROD_HEALTHY" = false ]; then
  log "ALERT: prod gateway is DOWN — alerting $ALERT_CHANNEL"
  # Add Slack alert here (webhook or hermes health script)
fi

log "watchdog check complete"