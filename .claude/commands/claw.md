---
description: /claw - Send a task to OpenClaw agent natively via WebSocket (fire-and-forget, no MCP timeout)
type: orchestration
execution_mode: immediate
---
# /claw - OpenClaw Native Agent Dispatch

**Usage**: `/claw <task description>`

**Purpose**: Send a task to the OpenClaw agent via the native `openclaw agent` CLI — the same path as typing a message to OpenClaw directly. Uses WebSocket, respects SOUL.md/memory/skills, and supports up to 20-minute autonomous tasks with no timeout killing the job.

## Execution Instructions

When this command is invoked with `$ARGUMENTS`:

1. Dispatch in background (fire-and-forget):
```bash
TASK_ID="claw-$(date +%s)-$$"
LOG_FILE="/tmp/openclaw-${TASK_ID}.log"

nohup openclaw agent --agent main \
  -m "$ARGUMENTS" \
  --thinking low \
  --timeout 1200 \
  > "$LOG_FILE" 2>&1 &

CLAW_PID=$!
sleep 0.5
if kill -0 "$CLAW_PID" 2>/dev/null; then
  echo "✓ Dispatched to OpenClaw agent (task: $TASK_ID, PID $CLAW_PID)"
  echo "  Output: tail -f $LOG_FILE"
  echo "  Gateway logs: tail -f /tmp/openclaw/openclaw-$(date +%F).log"
else
  echo "✗ OpenClaw agent exited immediately — check $LOG_FILE for errors"
fi
```

2. Confirm to the user:
- Task dispatched via native `openclaw agent` WebSocket path
- Timeout is 1200s (20 min) — long enough for real coding tasks
- Output streams to `/tmp/openclaw-<task-id>.log`
- OpenClaw uses its full agent stack: SOUL.md, memory, skills, tools

## Checking Progress

```bash
# Stream output as it arrives
tail -f /tmp/openclaw-claw-*.log

# Gateway agent activity (use unbuffered python -u for real-time)
tail -f /tmp/openclaw/openclaw-$(date +%F).log | grep -E '"(tool|exec|run)' --line-buffered | python3 -u -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        msg = str(d.get('1', '') or d.get('msg', ''))
        if 'tool' in msg or 'exec' in msg or 'run' in msg:
            print(d.get('time','')[:19], msg[:120])
    except: pass
"
```

## Requirements

- OpenClaw gateway running: `lsof -i :18789 | grep LISTEN`
- `openclaw` CLI in PATH: `which openclaw`
- OpenAI Codex OAuth token valid (refreshes automatically)

## Notes

- This bypasses `openclaw-mcp` entirely — no 30s timeout
- Uses `openclaw agent --agent main` — native WS protocol, same as typing in the OpenClaw UI
- OpenClaw runs with full context: SOUL.md, memory, skills, agent identity
- `--timeout 1200` = 20 minutes; increase for very long tasks
- To wait for result synchronously (blocking): remove `nohup ... &`
