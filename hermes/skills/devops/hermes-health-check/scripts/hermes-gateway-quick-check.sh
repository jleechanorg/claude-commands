#!/bin/bash
# hermes gateway-quick-check — one-shot health snapshot for both profiles
# Usage: bash hermes gateway-quick-check.sh
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo "=== Hermes Dual-Profile Quick Check ($(date '+%Y-%m-%d %H:%M:%S %Z')) ==="
echo ""

# --- Gateway health ---
for PORT in 8643 8644; do
  LABEL="prod (8643)"
  [[ "$PORT" == "8644" ]] && LABEL="staging (8644)"
  STATUS=$(curl -s --max-time 3 "http://localhost:$PORT/health" 2>/dev/null || echo '{"ok":false,"status":"down"}')
  OK=$(echo "$STATUS" | python3 -c "import json,sys; d=json.load(sys.stdin); print('true' if d.get('ok') else 'false')" 2>/dev/null || echo "false")
  if [ "$OK" = "true" ]; then
    echo -e "${GREEN}[OK]${NC}  $LABEL — $(echo "$STATUS" | python3 -m json.tool 2>/dev/null | head -1)"
  else
    echo -e "${RED}[DOWN]${NC} $LABEL — port not responding"
  fi
done
echo ""

# --- Process + port binding ---
echo "--- Process + port bindings ---"
for PID_PROG in "65745:prod" "36394:staging"; do
  PID="${PID_PROG%%:*}"
  LABEL="${PID_PROG##*:}"
  if ps -p "$PID" >/dev/null 2>&1; then
    PORT=$(lsof -p "$PID" -P -n 2>/dev/null | grep -E "8643|8644" | grep LISTEN | awk '{print $9}' | head -1)
    echo -e "${GREEN}[RUN]${NC}  $LABEL PID=$PID listening=$PORT"
  else
    echo -e "${RED}[STOP]${NC} $LABEL PID=$PID not running"
  fi
done
echo ""

# --- Qdrant ---
QDRANT=$(curl -s --max-time 3 http://localhost:6333/collections 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK' if d.get('status')=='ok' else 'DOWN')" 2>/dev/null || echo "DOWN")
if [ "$QDRANT" = "OK" ]; then
  echo -e "${GREEN}[OK]${NC}  Qdrant (6333)"
else
  echo -e "${RED}[DOWN]${NC} Qdrant (6333) — mem0 searches will fail"
fi
echo ""

# --- Ollama (optional — mem0 embedder) ---
OLLAMA=$(curl -s --max-time 3 http://localhost:11434/api/tags 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK' if 'models' in d else 'DOWN')" 2>/dev/null || echo "DOWN")
if [ "$OLLAMA" = "OK" ]; then
  echo -e "${GREEN}[OK]${NC}  Ollama (11434)"
else
  echo -e "${YELLOW}[WARN]${NC} Ollama (11434) — offline; embedder in mem0 OSS config will fail"
fi
echo ""

# --- Memory probe (direct, not from monitor) ---
MEM_OUT=$(timeout 15 bash -lc 'export NVM_DIR="$HOME/.nvm" && export PATH="$NVM_DIR/versions/node/v22.22.0/bin:$PATH" && hermes mem0 search "test" 2>&1' 2>/dev/null || echo "rc=$?")
if echo "$MEM_OUT" | grep -qi "error\|failed\|refused\|MODULE_VERSION"; then
  echo -e "${RED}[FAIL]${NC} Memory lookup — $MEM_OUT" | head -3
elif echo "$MEM_OUT" | grep -qi "no matches\|empty"; then
  echo -e "${GREEN}[OK]${NC}  Memory lookup functional (corpus empty)"
elif [ -z "$MEM_OUT" ]; then
  echo -e "${RED}[FAIL]${NC} Memory lookup — empty output (timeout likely)"
else
  echo -e "${GREEN}[OK]${NC}  Memory lookup — $(echo "$MEM_OUT" | head -2 | tr '\n' ' ')"
fi
echo ""

# --- Shared token warning ---
echo "--- Shared Slack tokens ---"
TOKEN_FILE="$HOME/.hermes_prod/config.yaml"
if [ -f "$TOKEN_FILE" ]; then
  SHARED=$(grep -c "shared" "$HOME/.hermes/scripts/doctor.sh" 2>/dev/null || echo "0")
  echo -e "${YELLOW}[WARN]${NC} Prod + staging both use same botToken/appToken (Socket Mode)"
fi
echo ""

# --- Latest gateway errors (prod) ---
if [ -f "$HOME/.hermes_prod/logs/gateway.err.log" ]; then
  LAST_ERR=$(tail -5 "$HOME/.hermes_prod/logs/gateway.err.log" 2>/dev/null | grep -v "^$" | tail -2 | tr '\n' ' ' | cut -c1-200)
  if [ -n "$LAST_ERR" ]; then
    echo "--- Latest prod gateway errors ---"
    echo "  $LAST_ERR"
  fi
fi