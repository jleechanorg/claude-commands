---
description: /claw - Route tasks through Hermes gateway inference
type: orchestration
execution_mode: immediate
---
# /claw - Hermes Gateway Inference

**Usage**: `/claw <task description>`

`/claw` is a thin wrapper. The operational behavior lives in:

- `~/.claude/skills/claw-dispatch/SKILL.md`

If the `/claw` task dispatches or supervises AO workers, also follow:

- `~/.claude/commands/ao.md`
- `~/.claude/skills/ao-operator-discipline/SKILL.md`

## Rules

- User-specified AO parameters are mandatory and must not be weakened or ignored.
- Post-spawn AO verification is required when `/claw` crosses into AO.
- Keep this command file thin; update the skill for behavioral changes.

## Execution

When invoked with `$ARGUMENTS`, read `~/.claude/skills/claw-dispatch/SKILL.md` and execute that workflow with the provided task description.
.7). OpenClaw is dead.

## Execution

When this command is invoked with `$ARGUMENTS`:

```bash
TASK_DESCRIPTION="$ARGUMENTS"
set -euo pipefail

LOGDIR="/tmp/hermes"
mkdir -p "$LOGDIR"
chmod 700 "$LOGDIR" 2>/dev/null || true
STATUS_LOG="$(mktemp "$LOGDIR/.claw-status-XXXXXXXX")"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/ai.hermes.prod.plist"

# If a launchd gateway is installed, prefer its env over CLI defaults.
# This keeps /claw aligned with the actual running service.
if [ -f "$LAUNCHD_PLIST" ]; then
  while IFS='=' read -r key value; do
    [ -n "$key" ] || continue
    export "$key=$value"
  done < <(
    python3 - "$LAUNCHD_PLIST" <<'PY'
import plistlib
import sys

path = sys.argv[1]
try:
    with open(path, "rb") as fh:
        data = plistlib.load(fh)
except FileNotFoundError:
    raise SystemExit(0)

env = data.get("EnvironmentVariables") or {}
for key in ("HERMES_HOME", "HERMES_LOG_LEVEL"):
    value = env.get(key)
    if value:
        print(f"{key}={value}")
PY
  )
fi

# Ensure HERMES_HOME is set (prod by default)
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes_prod}"

# Verify config.yaml exists and is valid YAML
HERMES_CFG="$HERMES_HOME/config.yaml"
if [ ! -f "$HERMES_CFG" ]; then
  echo "Hermes config not found: $HERMES_CFG"
  exit 1
fi
if ! python3 -c "import yaml; yaml.safe_load(open('$HERMES_CFG'))" 2>/dev/null; then
  echo "Hermes config is not valid YAML: $HERMES_CFG"
  exit 1
fi

# Verify the gateway is running
if ! HERMES_HOME="$HERMES_HOME" hermes gateway status >"$STATUS_LOG" 2>&1; then
  echo "Hermes gateway is not running."
  sed -n '1,80p' "$STATUS_LOG"
  exit 1
fi
if ! grep -q 'Gateway is running' "$STATUS_LOG"; then
  echo "Hermes gateway is not healthy."
  sed -n '1,80p' "$STATUS_LOG"
  exit 1
fi

# Resolve slash commands
TASK_WITH_RESOLVED="$TASK_DESCRIPTION"

SLASH_CMD=$(printf '%s' "$TASK_DESCRIPTION" | python3 -c "
import sys, re
text = sys.stdin.read().strip()
clean = re.sub(r'https?://\S+', '', text)
m = re.search(r'(?:^|\s)/([\w-]+)', clean)
if m:
    print(m.group(1))
" 2>/dev/null)

if [ -n "$SLASH_CMD" ]; then
  RESOLVED_CONTENT=""
  RESOLVED_SOURCE=""
  for search_dir in ".claude/commands" "$HOME/.claude/commands"; do
    if [ -f "$search_dir/$SLASH_CMD.md" ]; then
      RESOLVED_CONTENT=$(cat "$search_dir/$SLASH_CMD.md" 2>/dev/null)
      RESOLVED_SOURCE="$search_dir/$SLASH_CMD.md"
      break
    fi
  done
  if [ -z "$RESOLVED_CONTENT" ]; then
    for search_dir in ".claude/skills" "$HOME/.claude/skills"; do
      if [ -f "$search_dir/$SLASH_CMD/SKILL.md" ]; then
        RESOLVED_CONTENT=$(cat "$search_dir/$SLASH_CMD/SKILL.md" 2>/dev/null)
        RESOLVED_SOURCE="$search_dir/$SLASH_CMD/SKILL.md"
        break
      elif [ -f "$search_dir/$SLASH_CMD.md" ]; then
        RESOLVED_CONTENT=$(cat "$search_dir/$SLASH_CMD.md" 2>/dev/null)
        RESOLVED_SOURCE="$search_dir/$SLASH_CMD.md"
        break
      fi
    done
  fi
  if [ -n "$RESOLVED_CONTENT" ]; then
    echo "Resolved /$SLASH_CMD from $RESOLVED_SOURCE"
    TASK_WITH_RESOLVED="The user asked: $TASK_DESCRIPTION

Below is the full definition of /$SLASH_CMD (resolved from $RESOLVED_SOURCE). Execute it as instructed:

---
$RESOLVED_CONTENT
---"
  fi
fi

TASK_FILE="$(mktemp "$LOGDIR/.claw-task-XXXXXXXX")"
chmod 600 "$TASK_FILE" 2>/dev/null || true
printf '%s' "$TASK_WITH_RESOLVED" >"$TASK_FILE"
if [ ! -s "$TASK_FILE" ]; then
  echo "Failed to build Hermes task file"
  exit 1
fi

LOGFILE="$LOGDIR/claw-$(date +%s).log"
nohup hermes chat \
  -q "$(cat "$TASK_FILE")" \
  --yolo \
  --max-turns 90 \
  -Q \
  --source tool \
  >"$LOGFILE" 2>&1 &

CLAW_PID=$!
sleep 3
if ! kill -0 "$CLAW_PID" 2>/dev/null; then
  echo "Hermes agent exited immediately."
  sed -n '1,80p' "$LOGFILE"
  exit 1
fi

echo "Task dispatched to Hermes gateway (PID: $CLAW_PID)"
echo "Log: $LOGFILE"
echo "Monitor: tail -f $LOGFILE"
echo "Kill: kill $CLAW_PID"
```

## Requirements

- Hermes gateway running via `hermes gateway status`
- `config.yaml` valid at `$HERMES_HOME/config.yaml`
- Slash command resolution: looks up `.claude/commands/` and `.claude/skills/` directories

## Notes

- All tasks route through Hermes agent inference (MiniMax M2.7 default).
- Hermes replaced OpenClaw as THE agent (2026-04-12).
- Slash commands are resolved before dispatch.
- When `/claw` leads to AO worker dispatch, AO session metadata and launch commands must be verified after spawn. A spawned worker is not valid proof unless it matches the requested agent/runtime.
- Log file written to `/tmp/hermes/claw-<timestamp>.log`
- `--source tool` tag hides /claw sessions from `hermes sessions` user lists.
- `--yolo` bypasses tool approval prompts for autonomous execution.
- `-Q` (quiet) suppresses banner/spinner for clean log output.
medium",
            "--json",
            "--message",
            message,
        ]
    )
)
PY

CLAW_PID=$!
sleep 2
if ! kill -0 "$CLAW_PID" 2>/dev/null; then
  echo "OpenClaw agent exited immediately."
  sed -n '1,80p' "$LOGFILE"
  exit 1
fi
if grep -Eq 'gateway connect failed|falling back to embedded|unauthorized:' "$LOGFILE"; then
  kill "$CLAW_PID" 2>/dev/null || true
  echo "OpenClaw gateway path failed; refusing to continue via degraded fallback."
  sed -n '1,80p' "$LOGFILE"
  exit 1
fi

echo "Task dispatched to OpenClaw gateway (PID: $CLAW_PID)"
echo "Log: $LOGFILE"
echo "Monitor: tail -f $LOGFILE"
echo "Kill: kill $CLAW_PID"
```

## Requirements

- OpenClaw gateway healthy via `openclaw gateway status`
- `gateway.remote.token` must match `gateway.auth.token`
- Slash command resolution: looks up `.claude/commands/` and `.claude/skills/` directories

## Notes

- All tasks route through OpenClaw gateway inference.
- If an OpenClaw session needs to spawn an AO sub-task, it calls the `dispatch-task` skill internally — NOT directly from `/claw`.
- `/claw` fails closed if the OpenClaw CLI tries to degrade into embedded mode instead of using the gateway path.
- Slash commands are resolved before dispatch.
- Log file written to `/tmp/openclaw/claw-<timestamp>.log`
ing if you are unsure), append the /learn instruction below.
  # FAIL-CLOSED: omission = append. Only skip when you are confident /learn is covered.
  TASK_WITH_RESOLVED_COMMANDS="${TASK_WITH_RESOLVED_COMMANDS}

After completing all work and creating the PR, run /learn to capture any reusable patterns."
  # (Remove the appended /learn line above only if you judged the task already includes it)

  # Step A6: Write task to temp file for ao send
  mkdir -p /tmp/openclaw
  chmod 700 /tmp/openclaw 2>/dev/null || true
  TASK_FILE="$(mktemp /tmp/openclaw/.claw-task-XXXXXXXX)" || true
  if [ -z "$TASK_FILE" ] || [ ! -f "$TASK_FILE" ]; then
    echo "ERROR: mktemp failed for task file under /tmp/openclaw"
    exit 1
  fi
  chmod 600 "$TASK_FILE" 2>/dev/null || true
  if ! printf '%s' "$TASK_WITH_RESOLVED_COMMANDS" > "$TASK_FILE"; then
    echo "ERROR: could not write task file $TASK_FILE"
    rm -f "$TASK_FILE"
    exit 1
  fi

  # Step A7: Spawn ao session
  echo ""
  echo "Spawning ao session..."
  echo "  Issue: ${ISSUE_ID:-auto}"
  echo "  Project: $PROJECT_ID"

  # Capture ao spawn output; PIPESTATUS[0] is ao spawn exit (bash), not tee
  SPAWN_OUTPUT_FILE="$(mktemp /tmp/openclaw/.claw-spawn-XXXXXXXX)" || true
  if [ -z "$SPAWN_OUTPUT_FILE" ] || [ ! -f "$SPAWN_OUTPUT_FILE" ]; then
    echo "ERROR: mktemp failed for spawn log file"
    rm -f "$TASK_FILE"
    exit 1
  fi
  chmod 600 "$SPAWN_OUTPUT_FILE" 2>/dev/null || true

  if [ -n "$ISSUE_ID" ]; then
    # Spawn for existing issue
    ao spawn "$ISSUE_ID" -p "$PROJECT_ID" $RUNTIME_FLAG 2>&1 | tee "$SPAWN_OUTPUT_FILE"
    SPAWN_EXIT="${PIPESTATUS[0]}"
  else
    # No issue ID — create a bead first, then spawn
    echo "No issue ID detected — creating a bead..."
    BEAD_TITLE=$(printf '%s' "$TASK_DESCRIPTION" | cut -c1-80)
    BEAD_OUTPUT=$(br create "$BEAD_TITLE" --type task --priority 2 2>&1)
    echo "Bead creation: $BEAD_OUTPUT"
    # Parse first bead/issue id from br output (common shapes: bd-*, orch-*; extend regex if your br uses other prefixes)
    ISSUE_ID=$(echo "$BEAD_OUTPUT" | python3 -c "import sys,re; t=sys.stdin.read(); m=re.search(r'\b((?:bd|orch)-[a-z0-9]+)\b', t, re.I); print(m.group(1).lower() if m else '')" 2>/dev/null)
    if [ -z "$ISSUE_ID" ]; then
      echo "ERROR: Failed to create bead from task"
      rm -f "$TASK_FILE" "$SPAWN_OUTPUT_FILE"
      exit 1
    fi
    echo "Created bead: $ISSUE_ID"
    ao spawn "$ISSUE_ID" -p "$PROJECT_ID" $RUNTIME_FLAG 2>&1 | tee "$SPAWN_OUTPUT_FILE"
    SPAWN_EXIT="${PIPESTATUS[0]}"
  fi

  if [ "${SPAWN_EXIT:-1}" -ne 0 ]; then
    echo "ERROR: ao spawn failed with exit code ${SPAWN_EXIT}"
    echo "--- spawn output (head) ---"
    head -40 "$SPAWN_OUTPUT_FILE" 2>/dev/null || true
    rm -f "$TASK_FILE" "$SPAWN_OUTPUT_FILE"
    exit 1
  fi

  # Step A8: Session name — SESSION= from spawn log, then ao status JSON, then ao session ls
  SESSION_NAME=""
  SESSION_NAME=$(grep -E '^SESSION=' "$SPAWN_OUTPUT_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '\r' || true)
  if [ -z "$SESSION_NAME" ] && [ -n "$ISSUE_ID" ]; then
    SESSION_NAME=$(ao status --json --project "$PROJECT_ID" 2>/dev/null | ISSUE_ID="$ISSUE_ID" python3 -c 'import json, os, sys
want = os.environ.get("ISSUE_ID", "").lower().strip()
try:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    data = json.loads(raw)
    if isinstance(data, dict) and "sessions" in data:
        data = data["sessions"]
    if not isinstance(data, list):
        data = [data]
    for s in reversed(data):
        if not isinstance(s, dict):
            continue
        if str(s.get("issue", "")).lower() == want:
            n = s.get("name")
            if n:
                print(n)
            break
except Exception:
    pass
' 2>/dev/null || true)
  fi
  if [ -z "$SESSION_NAME" ]; then
    # DO NOT guess via tail -1 — in parallel mode this matches unrelated sessions.
    # Leave SESSION_NAME empty; the warning below will prompt manual recovery.
    echo "WARNING: Could not identify session name from spawn log or ao status"
  fi

  echo ""
  echo "Session name: ${SESSION_NAME:-<detecting...>}"
  echo "Task file: $TASK_FILE"

  # Step A9: Send task to session via file
  # NOTE: do NOT use --no-wait. ao send --no-wait queues the message in the Claude Code
  # REPL's "Press up to edit queued messages" buffer but does NOT submit it — the session
  # waits for a manual Enter. Without --no-wait, ao send blocks until the message is
  # actually submitted and the session starts processing.
  if [ -n "$SESSION_NAME" ]; then
    echo ""
    echo "Sending task to session $SESSION_NAME..."
    ao send "$SESSION_NAME" --file "$TASK_FILE" 2>&1
    SEND_EXIT=$?
    if [ $SEND_EXIT -eq 0 ]; then
      echo "Task sent successfully to $SESSION_NAME"
      # Verify delivery: peek at tmux to confirm session is actively processing (not idle)
      sleep 5
      TMUX_PANE_OUTPUT=$(tmux capture-pane -t "bb5e6b7f8db3-${SESSION_NAME}" -p -S -5 2>/dev/null | tail -5)
      if echo "$TMUX_PANE_OUTPUT" | grep -qE "Press up to edit|queued messages"; then
        echo "WARNING: task appears queued but not submitted — sending Enter to trigger"
        tmux send-keys -t "bb5e6b7f8db3-${SESSION_NAME}" "" Enter 2>/dev/null || true
        sleep 3
      fi
    else
      echo "WARNING: ao send exited with code $SEND_EXIT"
    fi
  else
    echo "WARNING: Could not detect session name — task may not be delivered"
    echo "To send manually: ao send <session> --file $TASK_FILE"
  fi

  # Step A10: Report to user
  echo ""
  echo "============================================"
  echo "  ao session spawned: ${SESSION_NAME:-unknown}"
  echo "  Project: $PROJECT_ID"
  echo "  Issue: ${ISSUE_ID:-auto-created bead}"
  echo "============================================"
  echo ""
  if [ -n "$SESSION_NAME" ]; then
    echo "  Attach: ao session attach $SESSION_NAME"
    echo "  Send more: ao send $SESSION_NAME '<message>'"
    echo "  Status: ao status"
  fi
  echo ""
  echo "Task dispatched in parallel — multiple PRs can be worked on simultaneously."
  echo "Note: multiple /claw invocations now run in parallel, not sequentially."

  # Clean up temp files (keep task file for manual send if needed)
  rm -f "$SPAWN_OUTPUT_FILE"

  # Step A11: Delivery tracking — verify session produces output
  # Write a tracking marker so the calling agent can verify delivery later
  TRACKING_FILE="/tmp/openclaw/.claw-track-${ISSUE_ID:-unknown}"
  cat > "$TRACKING_FILE" <<TRACK_EOF
ISSUE_ID=${ISSUE_ID:-unknown}
SESSION_NAME=${SESSION_NAME:-unknown}
PROJECT_ID=$PROJECT_ID
SPAWNED_AT=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
TASK_FILE=$TASK_FILE
STATUS=spawned
TRACK_EOF
  chmod 600 "$TRACKING_FILE" 2>/dev/null || true

  echo ""
  echo "Tracking: $TRACKING_FILE"
  echo ""
  echo "IMPORTANT: Verify delivery before reporting done:"
  echo "  1. tmux has-session -t bb5e6b7f8db3-${SESSION_NAME} 2>/dev/null  # session alive?"
  echo "  2. gh pr list -R <repo> --search '${ISSUE_ID}' --json number     # PR created?"
  echo "  If session died with no PR: respawn immediately or flag to user."

  exit 0
fi
```

#### Path B — Non-Coding Tasks: Gateway HTTP (original behavior)

```bash
# === PATH B: Gateway HTTP (read-only / summarize tasks) ===
echo "=== PATH B: Gateway HTTP (non-coding tasks) ==="

# Verify gateway is running
if ! lsof -i :18789 2>/dev/null | grep -q LISTEN; then
  echo "Gateway not running on port 18789. Start it with: launchctl start gui/$UID/ai.openclaw.gateway"
  exit 1
fi

# Read Gateway Token
GATEWAY_TOKEN=$(python3 -c "import json; d=json.load(open('$HOME/.openclaw/openclaw.json')); print(d['gateway']['auth']['token'])" 2>/dev/null)
if [ -z "$GATEWAY_TOKEN" ]; then
  echo "Could not read gateway token from ~/.openclaw/openclaw.json"
  exit 1
fi

# Resolve slash commands (same resolution as Path A)
TASK_WITH_RESOLVED="$TASK_DESCRIPTION"

SLASH_CMD=$(printf '%s' "$TASK_DESCRIPTION" | python3 -c "
import sys, re
text = sys.stdin.read().strip()
clean = re.sub(r'https?://\S+', '', text)
m = re.search(r'(?:^|\s)/([\w-]+)', clean)
if m:
    print(m.group(1))
" 2>/dev/null)

if [ -n "$SLASH_CMD" ]; then
  RESOLVED_CONTENT=""
  RESOLVED_SOURCE=""
  for search_dir in ".claude/commands" "$HOME/.claude/commands"; do
    if [ -f "$search_dir/$SLASH_CMD.md" ]; then
      RESOLVED_CONTENT=$(cat "$search_dir/$SLASH_CMD.md" 2>/dev/null)
      RESOLVED_SOURCE="$search_dir/$SLASH_CMD.md"
      break
    fi
  done
  if [ -z "$RESOLVED_CONTENT" ]; then
    for search_dir in ".claude/skills" "$HOME/.claude/skills"; do
      if [ -f "$search_dir/$SLASH_CMD/SKILL.md" ]; then
        RESOLVED_CONTENT=$(cat "$search_dir/$SLASH_CMD/SKILL.md" 2>/dev/null)
        RESOLVED_SOURCE="$search_dir/$SLASH_CMD/SKILL.md"
        break
      elif [ -f "$search_dir/$SLASH_CMD.md" ]; then
        RESOLVED_CONTENT=$(cat "$search_dir/$SLASH_CMD.md" 2>/dev/null)
        RESOLVED_SOURCE="$search_dir/$SLASH_CMD.md"
        break
      fi
    done
  fi
  if [ -n "$RESOLVED_CONTENT" ]; then
    echo "Resolved /$SLASH_CMD from $RESOLVED_SOURCE"
    TASK_WITH_RESOLVED="The user asked: $TASK_DESCRIPTION

Below is the full definition of /$SLASH_CMD (resolved from $RESOLVED_SOURCE). Execute it as instructed:

---
$RESOLVED_CONTENT
---"
  fi
fi

# Build JSON payload
LOGFILE="/tmp/openclaw/claw-$(date +%s).log"
mkdir -p /tmp/openclaw
chmod 700 /tmp/openclaw 2>/dev/null || true
PAYLOAD_FILE="$(mktemp /tmp/openclaw/.claw-payload-XXXXXXXX)"
chmod 600 "$PAYLOAD_FILE" 2>/dev/null || true

python3 -c "
import json, sys
payload = {
    'model': 'openclaw',
    'stream': True,
    'messages': [{'role': 'user', 'content': sys.argv[1]}]
}
with open(sys.argv[2], 'w') as f:
    json.dump(payload, f)
" "$TASK_WITH_RESOLVED" "$PAYLOAD_FILE"
py_rc=$?

if [ $py_rc -ne 0 ] || [ ! -s "$PAYLOAD_FILE" ]; then
  echo "Failed to build JSON payload"
  rm -f "$PAYLOAD_FILE"
  exit 1
fi

# Dispatch async
TOKEN_FILE="$(mktemp /tmp/openclaw/.claw-token-XXXXXXXX)"
chmod 600 "$TOKEN_FILE" 2>/dev/null || true
printf '%s' "$GATEWAY_TOKEN" > "$TOKEN_FILE"
unset GATEWAY_TOKEN

# Pass paths into nohup child (inner bash -c does not inherit unexported parent vars reliably)
PAYLOAD_FILE="$PAYLOAD_FILE" LOGFILE="$LOGFILE" TOKEN_FILE="$TOKEN_FILE" nohup bash -c '
GATEWAY_TOKEN=$(cat "$TOKEN_FILE" 2>/dev/null)
rm -f "$TOKEN_FILE"
if [ -z "$GATEWAY_TOKEN" ]; then echo "TOKEN ERROR"; exit 1; fi

RAW_BODY_FILE="$(mktemp /tmp/openclaw/.claw-body-XXXXXXXX)"
HTTP_META_FILE="$(mktemp /tmp/openclaw/.claw-http-XXXXXXXX)"

curl -sS -N \
  http://127.0.0.1:18789/v1/chat/completions \
  -H "Authorization: Bearer $GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-agent-id: main" \
  --max-time 600 \
  -d @"$PAYLOAD_FILE" \
  -o "$RAW_BODY_FILE" \
  -w "%{http_code}" >"$HTTP_META_FILE" 2>/dev/null

CURL_EXIT=$?
if [ $CURL_EXIT -ne 0 ]; then
  echo "CURL ERROR: request failed with exit code $CURL_EXIT"
  rm -f "$PAYLOAD_FILE" "$RAW_BODY_FILE" "$HTTP_META_FILE"
  unset GATEWAY_TOKEN
  exit 1
fi

rm -f "$PAYLOAD_FILE"
unset GATEWAY_TOKEN

HTTP_CODE=$(cat "$HTTP_META_FILE" 2>/dev/null || echo "")

ERROR_MSG=$(head -1 "$RAW_BODY_FILE" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    if \"error\" in d:
        err = d[\"error\"]
        if isinstance(err, dict):
            print(err.get(\"message\", str(err)))
        else:
            print(str(err))
except Exception:
    pass
" 2>/dev/null)

if [ -n "$ERROR_MSG" ]; then
  echo "GATEWAY ERROR (HTTP $HTTP_CODE): $ERROR_MSG"
elif [[ -n "$HTTP_CODE" && "$HTTP_CODE" =~ ^[4-5][0-9][0-9]$ ]]; then
  echo "GATEWAY ERROR: HTTP $HTTP_CODE"
  head -5 "$RAW_BODY_FILE" 2>/dev/null
else
  python3 - "$RAW_BODY_FILE" <<SSEOF
import json, sys
buf = []
with open(sys.argv[1], "r", errors="replace") as f:
    for raw in f:
        line = raw.rstrip("\n")
        if line == "":
            if buf:
                payload = "\n".join(buf)
                buf = []
                if payload.strip() == "[DONE]":
                    continue
                try:
                    d = json.loads(payload)
                    delta = d["choices"][0].get("delta", {})
                    if "content" in delta:
                        print(delta["content"], end="", flush=True)
                except Exception:
                    pass
            continue
        if line.startswith("data:"):
            buf.append(line[5:].lstrip())
    if buf:
        payload = "\n".join(buf)
        if payload.strip() != "[DONE]":
            try:
                d = json.loads(payload)
                delta = d["choices"][0].get("delta", {})
                if "content" in delta:
                    print(delta["content"], end="", flush=True)
            except Exception:
                pass
SSEOF
fi
rm -f "$HTTP_META_FILE" "$RAW_BODY_FILE"
echo ""
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

## Task Classification Reference

| Pattern | Route |
|---------|-------|
| Contains `fix`, `implement`, `write code`, `create PR`, `refactor` | **ao spawn** (Path A) |
| Contains issue ID like `orch-xxxx`, `wa-xxxx`, or other tracker ids | **ao spawn** (Path A) |
| Contains PR reference like `PR #123` | **ao spawn** (Path A) |
| Contains `summarize`, `explain`, `read-only`, `what is`, `list` | **Gateway HTTP** (Path B) |
| No coding keywords detected | **Gateway HTTP** (Path B) |

## Requirements

- **ao spawn path**: `ao` CLI installed, `agent-orchestrator.yaml` configured, `br` CLI for bead creation
- **Gateway HTTP path**: OpenClaw gateway running on port 18789, auth token in `~/.openclaw/openclaw.json`

## Notes

- **Parallelism**: Multiple `/claw` invocations with coding tasks each spawn independent `ao` sessions in parallel tmux windows — no longer sequential through the gateway
- **Slash commands**: Resolved before dispatch in both paths (command definition inlined into task)
- **Task file cleanup**: Temp task files are kept at `/tmp/openclaw/.claw-task-*.txt` for manual resend if needed
- **Bead creation**: If no issue ID is detected in a coding task, a bead is created automatically via `br create`
- **Per-repo / per-machine overrides**: The prefix → `PROJECT_ID` map is **example data**. Do **not** fork this file for every repository — add a **`bd-*)` → your-project** arm (or change the default `*)`) in **user scope** `~/.claude/commands/claw.md`, or rely on **`ao spawn` from the repo root** so AO picks the project from config/cwd. Same for tmux session name prefix if your namespace differs from `bb5e6b7f8db3-`.
- **Bead routing reference**: see bead **orch-sq2** (parallel `ao spawn` routing) in your tracker if used.
