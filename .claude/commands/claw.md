---
description: /claw - Send a task to OpenClaw agent via async gateway HTTP dispatch
type: orchestration
execution_mode: immediate
---
# /claw - OpenClaw Agent Dispatch (Async Gateway HTTP)

**Usage**: `/claw <task description>`

**Purpose**: Send a task to the OpenClaw agent asynchronously via the gateway's streaming HTTP endpoint. Returns immediately with a log file path — no blocking, no Slack needed.

## Execution Instructions

When this command is invoked with `$ARGUMENTS`:

### Step 1: Verify gateway is running

```bash
if ! lsof -i :18789 | grep -q LISTEN 2>/dev/null; then
  echo "Gateway not running on port 18789. Start it with: launchctl start gui/$UID/ai.openclaw.gateway"
  exit 1
fi
```

### Step 2: Read Gateway Token

```bash
GATEWAY_TOKEN=$(python3 -c "import json; d=json.load(open('$HOME/.openclaw/openclaw.json')); print(d['gateway']['auth']['token'])" 2>/dev/null)
if [ -z "$GATEWAY_TOKEN" ]; then
  echo "Could not read gateway token from ~/.openclaw/openclaw.json"
  exit 1
fi
```

### Step 3: Build JSON payload safely via python3

```bash
TASK_DESCRIPTION="$ARGUMENTS"
LOGFILE="/tmp/openclaw/claw-$(date +%s).log"
PAYLOAD_FILE="/tmp/openclaw/.claw-payload-$$.json"
mkdir -p /tmp/openclaw

# Build JSON payload entirely in python3 — no shell interpolation of user text into JSON
# This fixes orch-n0n1: the old approach used nested shell quoting that broke when
# task descriptions contained quotes, newlines, or started with certain characters
# (e.g., "Review PR #273" → JSON parse error "Unexpected token 'R'")
python3 -c "
import json, sys
payload = {
    'model': 'openclaw',
    'stream': True,
    'messages': [{'role': 'user', 'content': sys.argv[1]}]
}
with open(sys.argv[2], 'w') as f:
    json.dump(payload, f)
" "$TASK_DESCRIPTION" "$PAYLOAD_FILE"

if [ ! -f "$PAYLOAD_FILE" ]; then
  echo "Failed to build JSON payload"
  exit 1
fi
```

### Step 4: Dispatch async via streaming HTTP

```bash
# Fire streaming request in background — returns immediately
nohup bash -c '
PAYLOAD_FILE="'"$PAYLOAD_FILE"'"
LOGFILE="'"$LOGFILE"'"
GATEWAY_TOKEN="'"$GATEWAY_TOKEN"'"

# Capture raw response first to detect gateway errors (orch-glom)
RAW_RESPONSE=$(curl -s -w "\n__HTTP__%{http_code}" \
  http://127.0.0.1:18789/v1/chat/completions \
  -H "Authorization: Bearer $GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-agent-id: main" \
  --max-time 600 \
  -d @"$PAYLOAD_FILE" 2>/dev/null)

# Clean up payload file
rm -f "$PAYLOAD_FILE"

HTTP_CODE=$(echo "$RAW_RESPONSE" | grep "^__HTTP__" | sed "s/__HTTP__//")
BODY=$(echo "$RAW_RESPONSE" | grep -v "^__HTTP__")

# Check for gateway error response (non-streaming JSON error)
ERROR_MSG=$(echo "$BODY" | head -1 | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if \"error\" in d:
        print(d[\"error\"].get(\"message\", str(d[\"error\"])))
except (json.JSONDecodeError, ValueError):
    pass
" 2>/dev/null)

if [ -n "$ERROR_MSG" ]; then
  echo "GATEWAY ERROR (HTTP $HTTP_CODE): $ERROR_MSG"
else
  # Parse SSE stream and extract content deltas
  echo "$BODY" | grep "^data:" | grep -v "\[DONE\]" | while IFS= read -r line; do
    echo "$line" | sed "s/^data: //" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    delta = d[\"choices\"][0].get(\"delta\", {})
    if \"content\" in delta:
        print(delta[\"content\"], end=\"\", flush=True)
except Exception:
    pass
"
  done
fi

# Completion verification (orch-m6ia): flag empty/minimal output
echo ""
SELF_SIZE=$(wc -c < "'"$LOGFILE"'" 2>/dev/null || echo 0)
if [ "$SELF_SIZE" -lt 100 ]; then
  echo "--- WARNING: task produced minimal output (${SELF_SIZE}B) — likely failed ---"
fi
echo "--- claw task completed $(date) ---"
' > "$LOGFILE" 2>&1 &

CLAW_PID=$!
echo "Task dispatched async to OpenClaw gateway"
echo "PID: $CLAW_PID"
echo "Log: $LOGFILE"
echo ""
echo "Monitor: tail -f $LOGFILE"
echo "Kill: kill $CLAW_PID"
```

### Step 5: Confirm to User

Report:
- Task dispatched (async, non-blocking)
- PID and log file path
- How to monitor: `tail -f <logfile>`
- How to kill: `kill <pid>`

## Requirements

- OpenClaw gateway running on port 18789
- Gateway auth token in `~/.openclaw/openclaw.json`

## Notes

- Tasks run async with a 10-minute timeout (--max-time 600)
- Output streams to `/tmp/openclaw/claw-<timestamp>.log`
- The gateway process handles the task — no tmux session, no Slack
- JSON payload built via python3 (not shell interpolation) to prevent parse errors
- Gateway errors are detected and logged instead of silently swallowed
- Tasks producing <100B output are flagged as likely failures
- For sync (blocking) mode, use: `/claw --sync <task>`
- Beads: orch-n0n1 (JSON parse fix), orch-glom (empty log detection), orch-m6ia (completion verification)
