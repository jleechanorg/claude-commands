---
name: claw-dispatch
description: Use when dispatching work through the Hermes gateway with /claw, especially when the task may resolve slash commands or hand off into AO worker orchestration.
---

# Claw Dispatch

## Overview

`/claw` routes work through the Hermes gateway. The command file should stay thin; this skill holds the operational behavior.

If the `/claw` task will dispatch or supervise AO workers, also use:
- `~/.claude/commands/ao.md`
- `~/.claude/skills/ao-operator-discipline/SKILL.md`

User-specified AO parameters remain mandatory when `/claw` crosses into AO.

## Requirements

- Hermes gateway must be healthy via `hermes gateway status`
- `config.yaml` must exist and parse at `$HERMES_HOME/config.yaml`
- Slash command resolution must search `.claude/commands` first, then `.claude/skills`

## Execution

When invoked with a task description:

```bash
TASK_DESCRIPTION="$ARGUMENTS"
set -euo pipefail

LOGDIR="/tmp/hermes"
mkdir -p "$LOGDIR"
chmod 700 "$LOGDIR" 2>/dev/null || true
STATUS_LOG="$(mktemp "$LOGDIR/.claw-status-XXXXXXXX")"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/ai.hermes.prod.plist"

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

export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes_prod}"
HERMES_CFG="$HERMES_HOME/config.yaml"

if [ ! -f "$HERMES_CFG" ]; then
  echo "Hermes config not found: $HERMES_CFG"
  exit 1
fi
if ! python3 -c "import yaml; yaml.safe_load(open('$HERMES_CFG'))" 2>/dev/null; then
  echo "Hermes config is not valid YAML: $HERMES_CFG"
  exit 1
fi

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

TASK_WITH_RESOLVED="$TASK_DESCRIPTION"

# PR shorthand expansion: when the task is a bare PR number (e.g. "6976", "PR 6976",
# "#6976"), expand it to the full "bring to 7-green" task with repo auto-detection.
PR_NUMBER=$(printf '%s' "$TASK_DESCRIPTION" | python3 -c "
import sys, re
text = sys.stdin.read().strip()
m = re.match(r'^(?:PR\s*#?|#)\s*(\d+)$', text)
if m:
    print(m.group(1))
" 2>/dev/null)
if [ -n "$PR_NUMBER" ]; then
  # Auto-detect repo from current git remote
  REPO_SLUG=$(git remote get-url origin 2>/dev/null | python3 -c "
import sys, re
url = sys.stdin.read().strip()
m = re.match(r'(?:https?://github\.com/|git@github\.com:)([\w-]+/[\w-]+?)(?:\.git)?$', url)
if m:
    print(m.group(1))
" 2>/dev/null || echo "")
  if [ -n "$REPO_SLUG" ]; then
    PR_URL="https://github.com/${REPO_SLUG}/pull/${PR_NUMBER}"
  else
    PR_URL="PR #${PR_NUMBER}"
  fi
  TASK_WITH_RESOLVED="Bring ${PR_URL} to 7-green. Fix CI failures, resolve review comments, address CodeRabbit issues, resolve merge conflicts, and ensure all checks pass. Use /green ${PR_NUMBER} to verify. Act autonomously — do not ask for permission to fix things."
  TASK_DESCRIPTION="$TASK_WITH_RESOLVED"
fi

# PR URL augmentation: when the task contains a GitHub PR URL, inject an explicit
# autonomy directive so Hermes acts without asking for confirmation.
PR_URL=$(printf '%s' "$TASK_DESCRIPTION" | python3 -c "
import sys, re
m = re.search(r'https://github\.com/[\w-]+/[\w-]+/pull/\d+', sys.stdin.read())
if m:
    print(m.group(0))
" 2>/dev/null)
if [ -n "$PR_URL" ]; then
  TASK_WITH_RESOLVED="${TASK_DESCRIPTION}

IMPORTANT: You are acting as an autonomous agent. If you find that CI checks are failing, review threads are unresolved, or the PR needs remediation, automatically route to AO for remediation (ao spawn --claim-pr N). Do NOT ask 'Would you like me to route to AO?' — just do it. The user invoked /claw to get autonomous action, not a status report."
fi

SLASH_CMD=$(printf '%s' "$TASK_DESCRIPTION" | python3 -c "
import sys, re
text = sys.stdin.read().strip()
clean = re.sub(r'https?://\\S+', '', text)
m = re.search(r'(?:^|\\s)/([\\w-]+)', clean)
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

# Bidi mode: synchronous, streaming output
BIDI_MODE=false
CONTINUE_SESSION=""

if printf '%s' "$TASK_WITH_RESOLVED" | grep -q '^--bidi'; then
  BIDI_MODE=true
  TASK_WITH_RESOLVED=$(printf '%s' "$TASK_WITH_RESOLVED" | sed 's/^--bidi[[:space:]]*//')
fi

if printf '%s' "$TASK_WITH_RESOLVED" | grep -q '^--continue'; then
  CONTINUE_SESSION=$(printf '%s' "$TASK_WITH_RESOLVED" | sed 's/^--continue[[:space:]]*//' | awk '{print $1}')
fi

if [ "$BIDI_MODE" = true ]; then
  echo "Bidi mode: streaming Hermes response (synchronous)"
  hermes chat \
    -q "$TASK_WITH_RESOLVED" \
    --yolo \
    --max-turns 30 \
    --source tool \
    --pass-session-id
  echo ""
  echo "Session ended. To continue: /claw --continue <session_name>"
  exit 0
fi

if [ -n "$CONTINUE_SESSION" ]; then
  echo "Continuing Hermes session: $CONTINUE_SESSION"
  hermes chat \
    --continue "$CONTINUE_SESSION" \
    --yolo \
    --source tool
  exit 0
fi

# --status <logfile>: check on a running/completed claw session
if printf '%s' "$TASK_WITH_RESOLVED" | grep -q '^--status'; then
  STATUS_LOG=$(printf '%s' "$TASK_WITH_RESOLVED" | sed 's/^--status[[:space:]]*//' | awk '{print $1}')
  if [ ! -f "$STATUS_LOG" ]; then
    echo "❌ Log not found: $STATUS_LOG"
    exit 1
  fi
  LOG_LINES=$(wc -l <"$STATUS_LOG")
  LAST_LINE=$(tail -1 "$STATUS_LOG" 2>/dev/null)
  PID_RUNNING=$(pgrep -f "hermes chat" | head -1)
  echo "=== Claw Session Status ==="
  echo "Log: $STATUS_LOG ($LOG_LINES lines)"
  echo "Process: ${PID_RUNNING:-(completed)}"
  echo "Last output: $LAST_LINE"
  echo "--- Tail ---"
  tail -20 "$STATUS_LOG"
  exit 0
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

# Ack detection: wait up to 15s for Hermes to emit first output or fail fast
ACK_STATUS="UNKNOWN"
for i in $(seq 1 15); do
  sleep 1
  # Process died — capture why
  if ! kill -0 "$CLAW_PID" 2>/dev/null; then
    LOG_CONTENT=$(cat "$LOGFILE" 2>/dev/null)
    if printf '%s' "$LOG_CONTENT" | grep -q '429\|rate.limit\|request limit'; then
      ACK_STATUS="RATE_LIMITED"
    elif [ -z "$LOG_CONTENT" ]; then
      ACK_STATUS="FAILED (no output)"
    else
      ACK_STATUS="FAILED"
    fi
    echo "❌ Hermes claw $ACK_STATUS"
    sed -n '1,10p' "$LOGFILE"
    exit 1
  fi
  # Process alive — check if Hermes has started outputting real content
  LOG_LINES=$(wc -l <"$LOGFILE" 2>/dev/null || echo 0)
  if [ "$LOG_LINES" -gt 0 ]; then
    FIRST_LINE=$(head -1 "$LOGFILE" 2>/dev/null)
    if printf '%s' "$FIRST_LINE" | grep -q '429\|rate.limit\|request limit'; then
      ACK_STATUS="RATE_LIMITED"
      echo "❌ Hermes claw RATE_LIMITED — resets at $(grep -oE '[0-9]{2}:[0-9]{2}:[0-9]{2}' "$LOGFILE" | head -1)"
      cat "$LOGFILE"
      kill "$CLAW_PID" 2>/dev/null
      exit 1
    elif printf '%s' "$FIRST_LINE" | grep -qi 'error\|failed\|fatal'; then
      ACK_STATUS="FAILED"
      echo "❌ Hermes claw FAILED"
      sed -n '1,10p' "$LOGFILE"
      kill "$CLAW_PID" 2>/dev/null
      exit 1
    else
      ACK_STATUS="ACK"
      break
    fi
  fi
done

if [ "$ACK_STATUS" = "UNKNOWN" ]; then
  echo "⚠️  Hermes claw TIMEOUT — no output in 15s (PID: $CLAW_PID still alive)"
  echo "Log: $LOGFILE"
  exit 1
fi

echo "✅ Hermes claw ACK (PID: $CLAW_PID)"
echo "Log: $LOGFILE"
echo "Monitor: tail -f $LOGFILE"
echo "Status: /claw --status $LOGFILE"
echo "Kill: kill $CLAW_PID"
```

## Notes

- Hermes replaced OpenClaw as the live gateway agent
- slash commands are resolved before dispatch
- `/claw` sessions are hidden from normal Hermes session lists via `--source tool`
- `--yolo` bypasses tool approvals for autonomous runs
- when `/claw` leads to AO dispatch, spawned AO sessions must still be verified post-spawn

## Modes

| Prefix | Behavior |
|--------|----------|
| *(none)* | Async fire-and-forget with ack detection (✅ ACK / ❌ RATE_LIMITED / ❌ FAILED) |
| `--bidi` | Synchronous streaming — blocks until Hermes finishes, shows session ID for follow-up |
| `--continue <name>` | Resume a previous `--bidi` session interactively |
| `--status <logfile>` | Check tail + completion status of any async claw session |
