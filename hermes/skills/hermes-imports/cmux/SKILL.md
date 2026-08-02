---
name: cmux
description: "Control cmux terminal multiplexer via its Unix socket API. Use when needing to: (1) List, create, select, or close workspaces; (2) Split panes and manage surfaces; (3) Send text or key presses to terminals; (4) Create notifications; (5) Set sidebar status, progress bars, or log entries; (6) Query system state. Requires cmux CLI or Unix socket at /tmp/cmux.sock. ALWAYS validate commands via cmux_validator before execution."
---

## ⚠️ Submit Discipline (MANDATORY — read this before every cmux steer)

`cmux send` does **NOT** press Enter. This is the #1 recurring cmux failure mode
(verified 2026-07-16: user explicitly flagged "you always forget to send" after the
fable iOS pivot bootstrap). The **4-step ritual** below is a hard contract for every
send to a cmux surface. Skip ANY step and the message sits in the input buffer
without ever reaching the agent.

### ⚠️ Output Contract — typed text + terminal response (MANDATORY)

Every reply that reports a `cmux send` action MUST include, in the same reply:

1. **The exact text that was typed** — verbatim copy of the string passed to `cmux send`.
2. **The cmux terminal response** — verbatim transcript of what `cmux capture-pane` /
   `cmux read-screen` returned AFTER the `cmux send-key enter` settle window
   (typically 5-15s). Specifically, the agent's first action after absorption.
3. **Submission status** — explicit verdict: "submitted (churning label X)",
   "not submitted (text still at ❯ prompt)", or "blocked (no churn, retried N times)".

**Treat as not working until we see a response.** A reply that does NOT include
both the typed text AND a terminal response is invalid evidence that the
steer landed. The operator cannot distinguish a successful send from a failed
send that left text in the input buffer.

Canonical contract + echo-back template: `~/.hermes/skills/cmux/references/output-contract-mandatory.md`.

### ⚠️ LLM-Provenance Caveat (MANDATORY footer)

Every reply that quotes cmux output, terminal text, or agent actions produced
by another LLM (the worker agent OR the assistant's own synthesis of agent
output) MUST end with this verbatim footer:

> *This was generated from another LLM and not the actual user, so feel free
> to push back if you disagree and we can discuss.*

Full caveat rules + scope: `~/.hermes/skills/cmux/references/output-contract-mandatory.md` § "LLM-Provenance Caveat".

### The 4-step ritual

```bash
# STEP 1 — Type the text. OK response only proves socket acceptance, NOT submission.
cmux send --workspace workspace:N --surface surface:M "your message"

# STEP 2 — Press Enter. send does NOT auto-press Enter.
cmux send-key --workspace workspace:N --surface surface:M enter

# STEP 3 — Wait 5-15 seconds for the agent to start processing.
sleep 8

# STEP 4 — Verify with churning label (THE ONLY definitive proof).
cmux capture-pane --workspace workspace:N --surface surface:M --lines 25
# Look for one of:
#   - "Working (Xs • esc to interrupt)"
#   - "Forming… (Xs · thinking)"
#   - "Precipitating… (Xs · ↓ tokens)"
#   - "Brewed / Churned / Cooked for Xm"
# If you see ANY active churning label → SUBMITTED.
# If the text is still sitting at the ❯ prompt → NOT submitted, repeat step 2.
# If "Stopped" / "Done" / nothing → no churn, investigate.
```

### Echo-back proof (MANDATORY)

Every cmux steering action MUST be followed by an **echo-back proof** in the same
turn or the immediate next turn to your operator (Slack thread, terminal reply,
or whichever channel triggered the steer):

> ◀ sent to surface:55 (LEFT/claudec) at <HH:MM:SS PT> — 4-step ritual complete;
> churning label "Forming… 9s · ↓ 4.9k tokens" confirmed via capture-pane.

**Banned** (these are the failure modes the user keeps flagging):
- "I sent the message" (no Enter proof)
- "The agent should have received it" (no churning label)
- `cmux send` with no follow-up `cmux send-key enter`
- Sending to a surface that hasn't been focused (the global focus may be on a
  different workspace; use the raw RPC `surface.focus` if needed)

### Worktree-pointer strategy for long briefs

For task briefs >200 chars (e.g. orchestrating iOS app pivot, multi-PR review),
do NOT paste the full text into the input. Write the brief to a file in the
agent's cwd (e.g. `.cmux-<task>-brief.md`) and send a 1-2 line pointer. This
avoids the autocompleter contamination pitfall where shell-style tokens inside
long text trigger tab completion mid-stream.

### Canonical reference

Full recipe + edge cases + the 2026-06-25 worked example live at:
`~/.hermes/skills/cmux/references/send-submit-proof-2026-06-25.md`

This rule was added 2026-07-16 after the fable iOS pivot bootstrap surfaced
"you always forget to send" / "make sure you press submit and the work starts
on the cmux input" (Slack ts 1784185650.528089). Apply it uniformly to every
cmux-touching skill.

# cmux

Control cmux terminal multiplexer programmatically via its Unix socket API or CLI.

## ⚠️ Preflight Validation (REQUIRED before execution)

**Before running any cmux CLI command, you MUST validate it.**

The cmux command validator catches common mistakes before they produce silent help dumps:

```python
from orchestration.cmux_validator import validate, truncate_output

result = validate("cmux list-surfaces --workspace 23 --json")
if not result.valid:
    # Post the rejection to Slack thread immediately
    slack.post_message(channel_id, result.to_slack_message(session_id=ws))
    return  # Stop — do not proceed with invalid command
```

**Known failure modes this prevents:**
- `cmux list-surfaces --workspace 23 --json` → `--json` is not a valid flag for this command
- `cmux list-surface` → wrong subcommand (should be `list-surfaces`)
- `cmux tree` → no such command (use `cmux list-surfaces`)

## ⚠️ Status Bar Interpretation — NOT Frozen

Claude Code status bar states to interpret correctly:
- **`⏵⏵ bypass permissions on`** in status bar = normal Claude Code prompt UI, NOT a blocking dialog — Claude Code is actively working around it
- **Active churning timestamps** (e.g., "Churned for 9m 41s", "Sautéed for 2m 38s") = genuinely working workspace, NOT frozen
- **"Still running" indicator** = work in progress, not stalled
- **Idle bash shell** (fresh login prompt) = workspace is done or waiting for input, NOT frozen
- **ctx XX% progress** = active context usage, workspace is alive

**What IS actually blocked:**
- `bypass permissions on (shift+tab to cycle)` with NO active churning/time-on-task and NO progress indicator = may be a real stall
- "Index error" or "workspace unreachable" = workspace handle drift, genuinely blocked
- Shell at `claude`/`claudem` typed but no Claude Code active = shell-level stall, needs restart
- "Add a follow-up" dialog open in Composer 2 Fast = blocked on human follow-up, not frozen

**Key rule:** A workspace with an active time-on-task label ("Churned for Xm", "Crunched for Xm") is working, regardless of what the status bar shows. Only report as "frozen" when there's evidence of no activity AND no active time-on-task.

## Error / stderr Handling

If cmux fails and emits a large help dump to stderr:

```python
# Always emit terminal status even on error
try:
    result = subprocess.run(...)
except Exception as exc:
    msg = f":fire: cmux error: `{exc}`"
    slack.post_message(channel_id, msg, thread_ts=thread_ts)
    return

# Truncate large output for Slack display
if len(stderr) > 2000 or stderr.count("\n") > 20:
    summary = truncate_output(stderr)
    slack.post_message(channel_id, f":warning: cmux output truncated:\n```\n{summary}\n```", ...)
```

## Socket Connection

```bash
SOCKET_PATH="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
```

Send JSON-RPC requests:
```json
{"id":"req-1","method":"workspace.list","params":{}}
```

## CLI Quick Reference

```bash
# Output as JSON
cmux --json <command>

# Target specific workspace/surface
cmux --workspace <id> --surface <id> <command>
```

## Workspace

| Action | CLI | Socket Method |
|--------|-----|---------------|
| List all | `cmux list-workspaces` | `workspace.list` |
| Create new | `cmux new-workspace` | `workspace.create` |
| Select | `cmux select-workspace --workspace <id>` | `workspace.select` |
| Get current | `cmux current-workspace` | `workspace.current` |
| Close | `cmux close-workspace --workspace <id>` | `workspace.close` |

## Splits & Surfaces

| Action | CLI | Socket Method |
|--------|-----|---------------|
| New split | `cmux new-split <direction>` | `surface.split` (direction: left/right/up/down) |
| List surfaces | `cmux list-surfaces` | `surface.list` |
| Focus surface | `cmux focus-surface --surface <id>` | `surface.focus` |

## Input

| Action | CLI | Socket Method |
|--------|-----|---------------|
| Send text | `cmux send "echo hello"` | `surface.send_text` |
| Send key | `cmux send-key enter` | `surface.send_key` |
| Send to surface | `cmux send-surface --surface <id> "cmd"` | `surface.send_text` (with surface_id) |

Keys: `enter`, `tab`, `escape`, `backspace`, `delete`, `up`, `down`, `left`, `right`

## Notifications

```bash
cmux notify --title "Title" --body "Body"
# Socket: notification.create
```

## Sidebar Metadata

| Action | CLI | Socket Method |
|--------|-----|---------------|
| Set status | `cmux set-status <key> <value>` | (socket only) |
| Clear status | `cmux clear-status <key>` | (socket only) |
| Set progress | `cmux set-progress 0.5 --label "Building..."` | (socket only) |
| Clear progress | `cmux clear-progress` | (socket only) |
| Log entry | `cmux log "message" --level error` | (socket only) |
| Clear log | `cmux clear-log` | (socket only) |

## System

| Action | CLI | Socket Method |
|--------|-----|---------------|
| Ping | `cmux ping` | `system.ping` |
| Capabilities | `cmux capabilities` | `system.capabilities` |
| Identify context | `cmux identify` | `system.identify` |

## Python Client

```python
import json
import os
import socket

SOCKET_PATH = os.environ.get("CMUX_SOCKET_PATH", "/tmp/cmux.sock")

def rpc(method, params=None, req_id=1):
    payload = {"id": req_id, "method": method, "params": params or {}}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET_PATH)
        sock.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        return json.loads(sock.recv(65536).decode("utf-8"))

# List workspaces
print(rpc("workspace.list", req_id="ws"))

# Send notification
print(rpc("notification.create", {"title": "Hello", "body": "From Python!"}))
```

## Shell Helper

```bash
cmux_cmd() {
    SOCK="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
    printf "%s\n" "$1" | nc -U "$SOCK"
}

cmux_cmd '{"id":"ws","method":"workspace.list","params":{}}'
```

## Check if cmux is Available

```bash
[ -S "${CMUX_SOCKET_PATH:-/tmp/cmux.sock}" ] && echo "cmux socket available"
command -v cmux &>/dev/null && echo "cmux CLI available"
```
