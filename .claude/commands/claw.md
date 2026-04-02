---
description: /claw - Send a task to ao spawn (parallel tmux) for coding, gateway HTTP for read-only
type: orchestration
execution_mode: immediate
---
# /claw - OpenClaw Agent Dispatch (Parallel AO Sessions for Coding)

**Usage**: `/claw <task description>`

**Purpose**: Routes to the right execution path:
- **Coding tasks** (fix, implement, write code, create PR, update code, etc.) → `ao spawn` + `ao send` for parallel tmux sessions
- **Non-coding tasks** (summarize, read-only, explain, etc.) → OpenClaw gateway HTTP (existing behavior)

This replaces sequential single-agent processing with parallel multi-session execution.

## ⚠️ OPENCLAW AGENT — MANDATORY ROUTING RULE (orch-nkg)

If you are the **OpenClaw embedded agent** receiving this task from the gateway:

**DO NOT run this task inline.** Inline execution has no worktree, no PR, no branch.

**INSTEAD — follow the `dispatch-task` skill** (in this repo: `skills/dispatch-task/SKILL.md`):
1. Create/claim a bead (`br create ...` or `br update ... --status in_progress`; see CLAUDE.md for `br` examples)
2. Determine the ao project ID: `ao projects list`
3. Spawn: `ao spawn ORCH-xxx -p <project-id>`
4. Send: write task to tmp file, `ao send <session-name> --file <file>`

This applies to ALL tasks involving code, files, or PRs — see SOUL.md "Agent Dispatch Policy."

**How this interacts with Path A / Path B below:** Path A already runs `ao spawn` from this shell for classified **coding** tasks. This rule still applies when coding work reaches you through **Path B** (gateway HTTP), a misclassified task, or any non-`/claw` gateway traffic—use `dispatch-task` instead of executing inline.

## Execution Instructions

When this command is invoked with `$ARGUMENTS`:

### Step 0: Parse task

```bash
TASK_DESCRIPTION="$ARGUMENTS"
```

### Step 1: Classify task type

```bash
# Detect coding tasks (require parallel ao spawn)
# Matches keywords that indicate real code changes
is_coding_task() {
  printf '%s' "$1" | python3 -c "
import sys, re
text = sys.stdin.read().lower()
coding_patterns = [
    r'\b(fix|resolve|patch)\s+(bug|issue|pr|code|test|error|problem|regression|failure)\b',
    r'\bimplement\b', r'\bcreate\s+pr\b', r'\bwrite\b.*\bcode\b',
    r'\bupdate\b.*\bcode\b', r'\brefactor\b', r'\badd\b.*\bfeature\b',
    r'\bpatch\b', r'\b(add|write|create|implement|update|fix)\s+.*\btest',
    r'\b(fix|setup|configure|update)\s+.*\bbuild\b', r'\bdeploy\b',
    r'\bconfigure\b', r'\bset\s*up\b', r'\brewrite\b', r'\benhance\b',
    r'\boptimize\b', r'\bclean\s*up\b', r'\bremove\b.*\bcode\b',
    r'\bwork\s*on\b.*\b(bead|issue|pr|branch)\b',
    r'\bao\s*spawn\b', r'\bdispatch\b',
    r'\b(?:orch|wa|ao|ra|cc|wc|mt|mm)-[a-z0-9]+\b',  # issue reference (all project prefixes)
    r'\bpr\s*#?\d+\b',      # PR reference
    r'\bbranch\b.*\b(feat|fix|bug|orch)\b',
    r'\bbead\b.*\b(orch|wa|jc|ao)\b',
]
for pat in coding_patterns:
    if re.search(pat, text):
        sys.exit(0)
sys.exit(1)
" 2>/dev/null
}

if is_coding_task "$TASK_DESCRIPTION"; then
  TASK_TYPE="coding"
else
  TASK_TYPE="read_only"
fi
echo "Task classified as: $TASK_TYPE"
```

### Step 2: Route

#### Path A — Coding Tasks: ao spawn (parallel)

```bash
if [ "$TASK_TYPE" = "coding" ]; then
  echo "=== PATH A: ao spawn (parallel coding sessions) ==="

  # Step A1: Extract issue ID from task (e.g. "orch-sq2", "ORCH-sq2", "fix orch-sq2")
  ISSUE_ID=$(printf '%s' "$TASK_DESCRIPTION" | python3 -c "
import sys, re
text = sys.stdin.read().strip()
# Match bead/issue IDs for all ao project prefixes (see case map below)
m = re.search(
    r'\b((?:orch|wa|ao|ra|cc|wc|mt|mm)-[a-z0-9]+)\b',
    text,
    re.IGNORECASE,
)
if m:
    print(m.group(1).lower())
" 2>/dev/null)

  # Step A2: Resolve project from issue ID prefix or default to jleechanclaw
  case "$ISSUE_ID" in
    orch-*) PROJECT_ID="jleechanclaw" ;;
    wa-*)   PROJECT_ID="worldarchitect" ;;
    ao-*)   PROJECT_ID="agent-orchestrator" ;;
    ra-*)   PROJECT_ID="ralph" ;;
    cc-*)   PROJECT_ID="claude-commands" ;;
    wc-*)   PROJECT_ID="worldai-claw" ;;
    mt-*)   PROJECT_ID="mctrl-test" ;;
    mm-*)   PROJECT_ID="mcp-mail" ;;
    *)      PROJECT_ID="jleechanclaw" ;;
  esac
  echo "Project: $PROJECT_ID  Issue: ${ISSUE_ID:-<none — will be created>}"

  # Step A2.5: Detect runtime override (e.g., "antig" = antigravity runtime)
  RUNTIME_FLAG=""
  if printf '%s' "$TASK_DESCRIPTION" | python3 -c "
import sys, re
text = sys.stdin.read().lower()
# 'antig' or 'antigravity orchestrator' means use runtime-antigravity
if re.search(r'\bantig(?:ravity)?\b', text):
    sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
    RUNTIME_FLAG="--runtime antigravity"
    echo "Runtime override detected: antigravity (via 'antig' keyword)"
  fi

  # Step A3: Verify ao is available
  if ! command -v ao &>/dev/null; then
    echo "ERROR: 'ao' command not found. Is agent-orchestrator installed?"
    echo "Install: npm install -g @agent-orchestrator/core  (or pip install agent-orchestrator)"
    exit 1
  fi

  # Step A4: Verify ao is configured (common locations; ao may still use defaults)
  AO_CONFIG=""
  for _cand in "$HOME/agent-orchestrator.yaml" "$HOME/project_jleechanclaw/jleechanclaw/agent-orchestrator.yaml" "./agent-orchestrator.yaml"; do
    if [ -f "$_cand" ]; then
      AO_CONFIG="$_cand"
      break
    fi
  done
  if [ -z "$AO_CONFIG" ]; then
    echo "WARNING: agent-orchestrator.yaml not found in usual paths — ao spawn may still work if ao is configured elsewhere"
  fi

  # Step A5: Resolve slash commands (same as original /claw)
  # (inline the slash command resolution from Step 2.5 of the original)
  TASK_WITH_RESOLVED_COMMANDS="$TASK_DESCRIPTION"

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
      TASK_WITH_RESOLVED_COMMANDS="The user asked: $TASK_DESCRIPTION

Below is the full definition of /$SLASH_CMD (resolved from $RESOLVED_SOURCE). Execute it as instructed:

---
$RESOLVED_CONTENT
---"
    fi
  fi

  # Step A5.5: Learning-loop gate
  # Any coding task dispatched via /claw that does NOT go through /integrate must
  # explicitly include /learn at the end — otherwise the learning loop is silently broken.
  # Check if task already has /learn, /integrate, or an explicit "learning N/A" reason.
  HAS_LEARN=$(printf '%s' "$TASK_WITH_RESOLVED_COMMANDS" | python3 -c "
import sys, re
text = sys.stdin.read().lower()
has_integrate = bool(re.search(r'/integrate\b', text))
has_learn = bool(re.search(r'/learn\b', text))
# Flexible N/A separator: matches 'learning n/a', 'learning: n/a', 'learning - n/a'
has_na = bool(re.search(r'\blearning(?:\s*[-_:]\s*|\s+)n/?a\b|\bskip[-_\s]*learn\b', text))
print('yes' if (has_integrate or has_learn or has_na) else 'no')
" 2>/dev/null)
  # Treat empty HAS_LEARN (python3 error) as 'no' — fail closed (append /learn)
  if [ "${HAS_LEARN:-no}" != "yes" ]; then
    echo "Learning-loop gate: appending /learn step (no /integrate or /learn found in task)"
    TASK_WITH_RESOLVED_COMMANDS="${TASK_WITH_RESOLVED_COMMANDS}

After completing all work and creating the PR, run /learn to capture any reusable patterns."
  fi

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
    if ! command -v br &>/dev/null; then
      echo "ERROR: 'br' command not found. Install beads or provide an issue ID."
      rm -f "$TASK_FILE" "$SPAWN_OUTPUT_FILE"
      exit 1
    fi
    BEAD_TITLE=$(printf '%s' "$TASK_DESCRIPTION" | cut -c1-80)
    BEAD_OUTPUT=$(br create "$BEAD_TITLE" --type task --priority 2 2>&1)
    echo "Bead creation: $BEAD_OUTPUT"
    ISSUE_ID=$(echo "$BEAD_OUTPUT" | python3 -c "import sys,re; t=sys.stdin.read(); m=re.search(r'ORCH-[A-Za-z0-9]+', t, re.IGNORECASE); print(m.group(0).lower() if m else '')" 2>/dev/null)
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
  if [ -z "$SESSION_NAME" ] && [ -n "$ISSUE_ID" ]; then
    # Filter ao session ls by issue ID suffix — avoid picking an unrelated session
    SESSION_NAME=$(ao session ls 2>/dev/null | grep -oE '[a-z]+-[0-9]+' | grep -F "$(echo "$ISSUE_ID" | cut -d- -f2-)" | tail -1 || true)
    [ -n "$SESSION_NAME" ] && echo "Session detected via ao session ls filter: $SESSION_NAME"
  fi
  if [ -z "$SESSION_NAME" ]; then
    echo "ERROR: Could not detect session name for ${ISSUE_ID:-task} — task will not be delivered"
    echo "  Check: ao status --project $PROJECT_ID"
    echo "  Send manually: ao send <session> --file $TASK_FILE"
    rm -f "$SPAWN_OUTPUT_FILE"
    exit 1
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
      # Derive tmux target by scanning for a session containing SESSION_NAME — avoids
      # a hardcoded host-specific prefix (ao session names include a device prefix).
      sleep 5
      TMUX_FULL_TARGET=$(tmux list-sessions -F '#{session_name}' 2>/dev/null | grep -F "${SESSION_NAME}" | head -1)
      TMUX_FULL_TARGET="${TMUX_FULL_TARGET:-${SESSION_NAME}}"
      TMUX_PANE_OUTPUT=$(tmux capture-pane -t "$TMUX_FULL_TARGET" -p -S -5 2>/dev/null | tail -5)
      if echo "$TMUX_PANE_OUTPUT" | grep -qE "Press up to edit|queued messages"; then
        echo "WARNING: task appears queued but not submitted — sending Enter to trigger"
        tmux send-keys -t "$TMUX_FULL_TARGET" "" Enter 2>/dev/null || true
        sleep 3
      fi
    else
      echo "ERROR: ao send failed with exit code $SEND_EXIT — task not delivered"
      echo "  Session: $SESSION_NAME  |  Task file kept: $TASK_FILE"
      rm -f "$SPAWN_OUTPUT_FILE"
      exit 1
    fi
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

# Dispatch async — all token handling stays inside the subshell (no parent-shell env/argv leak)
# Note: no parent-shell trap needed — the subshell's cleanup trap handles PAYLOAD_FILE removal
# on any exit (including if the nohup itself fails to start).
PAYLOAD_FILE="$PAYLOAD_FILE" LOGFILE="$LOGFILE" nohup bash -c '
# Read token inside subshell — never visible as parent-shell variable or Python argv
GATEWAY_TOKEN=$(python3 -c "
import json, sys
try:
    d=json.load(open(sys.argv[1]))
    print(d[\"gateway\"][\"auth\"][\"token\"])
except Exception:
    sys.exit(1)
" "$HOME/.openclaw/openclaw.json" 2>/dev/null)
if [ -z "$GATEWAY_TOKEN" ]; then
    echo "TOKEN ERROR: could not read gateway token" >&2
    exit 1
fi

# Token validation guard — reject empty or too-short tokens
# (length-only check; openclaw token format is opaque, so we avoid
# restricting the character class and breaking valid tokens with . + / etc.)
if [ ${#GATEWAY_TOKEN} -lt 20 ]; then
    echo "TOKEN ERROR: token is too short or empty" >&2
    exit 1
fi

# All temp files use mktemp with random suffix — no predictable paths
BODY_FILE="$(mktemp /tmp/openclaw/.claw-body-XXXXXXXX)"
HTTP_CODE_FILE="$(mktemp /tmp/openclaw/.claw-http-XXXXXXXX)"

# Ensure cleanup on any exit from this subshell
cleanup() { rm -f "$BODY_FILE" "$HTTP_CODE_FILE" "$PAYLOAD_FILE" 2>/dev/null; }
trap cleanup EXIT INT TERM HUP

curl -sS -N \
  http://127.0.0.1:18789/v1/chat/completions \
  -H "Authorization: Bearer $GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-agent-id: main" \
  --max-time 600 \
  -d @"$PAYLOAD_FILE" \
  -o "$BODY_FILE" \
  -w "%{http_code}" >"$HTTP_CODE_FILE" 2>/dev/null

CURL_EXIT=$?
if [ $CURL_EXIT -ne 0 ]; then
  echo "CURL ERROR: request failed with exit code $CURL_EXIT" >&2
  exit 1
fi

HTTP_CODE=$(cat "$HTTP_CODE_FILE" 2>/dev/null || echo "")

# HTTP 4xx/5xx detection — check status code before attempting JSON parse
if [[ -n "$HTTP_CODE" && "$HTTP_CODE" =~ ^[4-5][0-9][0-9]$ ]]; then
  BODY_PREVIEW=$(head -c 512 "$BODY_FILE" 2>/dev/null || echo "")
  # Try to extract JSON error message; if not JSON, show raw preview
  JSON_ERR=$(printf "%s" "$BODY_PREVIEW" | python3 -c "
import sys, json
try:
    d=json.loads(sys.stdin.read())
    if \"error\" in d:
        e=d[\"error\"]
        print(e.get(\"message\", str(e)) if isinstance(e,dict) else str(e))
except Exception:
    pass
" 2>/dev/null)
  if [ -n "$JSON_ERR" ]; then
    echo "GATEWAY ERROR (HTTP $HTTP_CODE): $JSON_ERR" >&2
  else
    echo "GATEWAY ERROR: HTTP $HTTP_CODE" >&2
    echo "$BODY_PREVIEW" >&2
  fi
  exit 1
fi

# SSE multi-line parser via Python heredoc — no process substitution, no shell variable buffering
python3 - "$BODY_FILE" <<SSEOF
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
                    delta = d.get("choices", [{}])[0].get("delta", {})
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
                delta = d.get("choices", [{}])[0].get("delta", {})
                if "content" in delta:
                    print(delta["content"], end="", flush=True)
            except Exception:
                pass
SSEOF

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
| Contains issue ID like `orch-xxxx`, `wa-xxxx` | **ao spawn** (Path A) |
| Contains PR reference like `PR #123` | **ao spawn** (Path A) |
| Contains `summarize`, `explain`, `read-only`, `what is`, `list` | **Gateway HTTP** (Path B) |
| No coding keywords detected | **Gateway HTTP** (Path B) |

## Requirements

- **ao spawn path**: `ao` CLI installed, `agent-orchestrator.yaml` configured, `br` CLI for bead creation
- **Gateway HTTP path**: OpenClaw gateway running on port 18789, auth token in `~/.openclaw/openclaw.json`

## Notes

- **Parallelism**: Multiple `/claw` invocations with coding tasks each spawn independent `ao` sessions in parallel tmux windows — no longer sequential through the gateway
- **Slash commands**: Resolved before dispatch in both paths (command definition inlined into task)
- **Task file cleanup**: Temp task files are kept at `/tmp/openclaw/.claw-task-*` for manual resend if needed
- **Bead creation**: If no issue ID is detected in a coding task, a bead is created automatically via `br create`
- **Beads**: orch-sq2 (parallel ao spawn routing)
- **Antigravity runtime**: If the task mentions `antig` or `antigravity`, Path A adds `--runtime antigravity` to `ao spawn`
