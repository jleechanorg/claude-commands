---
name: cmux-steer
description: Read and steer another cmux terminal tab through the Unix socket.
---

# cmux-steer — Control another cmux terminal tab via the Unix socket

> **REQUIRED (2026-06-09):** This skill is **deprecated for runtime steering**. The bare `cmux send` + `cmux send-key enter` pattern documented here does NOT include proof of submission. Use the canonical wrapper instead: `python3 -c "from cmux_client import send_and_submit; print(send_and_submit('workspace:N', 'surface:M', 'text'))"` and include the returned `proof` + `proof_ts` in your reply. See `~/.hermes_prod/skills/cmux-send-submit/SKILL.md`. This skill is preserved for socket read operations (`workspace.list`, `surface.read_text`, `tree`, `system.ping`) only.

## ⚠️ SUPERSEDED — Use `cmux` CLI, not raw socket protocol

The raw `nc -U $SOCK` examples below still work for low-level access, but they
have a **name → surface resolution gap** that has caused repeated failures
("why do you always get confused when I name a surface"). The canonical recipe
is the `cmux` CLI, which exposes workspace/surface/tab refs directly.

**Always start here when the user names a surface, tab, or workspace:**

```bash
# 1. MY workspace = caller.workspace_ref, falling back to focused.
#    `caller` is populated only when this command runs inside cmux itself;
#    from a standalone terminal (and from most skill invocations) it is null,
#    and a naive `["caller"]["workspace_ref"]` lookup will KeyError. The
#    defensive form below silently falls back to the focused workspace.
WS=$(cmux identify --json | python3 -c '
import sys, json
d = json.load(sys.stdin)
c = d.get("caller") or {}
print(c.get("workspace_ref") or d.get("focused", {}).get("workspace_ref"))
')

# 2. Every pane + tab by name; ◀ here = caller surface, ◀ active = focus.
#    Do NOT filter the output — sibling tabs and the ◀ markers are the signal.
cmux tree --all --workspace "$WS"

# 3. Read the target surface. ⚠ Cross-workspace `cmux read-screen
#    --workspace X --surface Y` is NOT reliable in current cmux (verified
#    bug — see ~/.hermes/skills/cmux/references/surface-read-routing-bug.md):
#    it can silently return the currently-focused surface's content even
#    when the `result` echoes the requested refs. The reliable recipe for
#    reading a non-focused surface is **focus-then-read**:
#      a. `cmux focus-surface --workspace "$WS" --surface surface:N` (or the
#         JSON-RPC `surface.focus` equivalent) to make surface:N the focused
#         surface, then
#      b. `cmux read-screen --lines 80` (no --workspace / --surface args —
#         the bare invocation reads the focused surface).
#    For an already-focused surface, the bare `cmux read-screen --lines N`
#    is sufficient and matches what you see on screen.
```

### Three anti-patterns this skill now warns against

- **Global name search** — `cmux list-pane-surfaces | grep <name>` matches a
  same-named tab in another workspace and you steer the wrong agent.
- **grep-filtering the tree** — `cmux tree --all | grep <name>` hides sibling
  tabs and the `◀ here` / `◀ active` markers you need to disambiguate.
- **`list-pane-surfaces` defaults** — defaults to ONE pane and omits tabs in
  other panes; use `cmux tree --all --workspace "$WS"` for the full picture.

### What this skill still does well

The raw `nc -U $SOCK` blocks below remain useful for low-level debugging
(`system.tree`, `system.identify`, custom JSON-RPC methods) and for
environments where the `cmux` CLI binary is not on PATH. The CLI recipes
above are the **default**; fall back to the raw socket blocks only when the
CLI fails or is unavailable.

### Known cmux CLI bugs (verified)

- **`cmux read-screen --workspace <ws> --surface <surface>`** can silently
  return the focused surface's content instead of the named one (see
  `~/.hermes/skills/cmux/references/surface-read-routing-bug.md`). Use the
  focus-then-read recipe above for any non-focused surface.
- **`surface.read_text` with `workspace_ref`/`surface_ref`** ignores the ref
  params and returns the focused surface's text. Same focus-then-read fix.

---

**Usage**: Read and follow this skill directly; no `/cmux-steer` slash command is defined.

**Purpose**: Read and steer another agent's terminal pane (e.g. a coding agent)
from within cmux, without disrupting the user's active workspace navigation.

---

## Socket path

```bash
# Release build
SOCK="$HOME/Library/Application Support/cmux/cmux.sock"

# Dev builds — find via saved path files or lsof:
cat ~/Library/Application\ Support/cmux/dev-may-18-last-socket-path
# → /tmp/cmux-debug-may-18.sock

lsof -p $(pgrep -f "cmux DEV may-18") | grep -E "\.sock"

# Use CMUX_SOCKET_PATH to target a specific build with the CLI:
CMUX_SOCKET_PATH=/tmp/cmux-debug-may-18.sock cmux list-workspaces
```

## Rule 1: Always find workspace by NAME, not index

The user can switch workspaces at any time, shifting surface indices. **Never
hardcode an index.** Always look up by the workspace's display name:

```bash
# List all workspaces with names
printf "list_workspaces\n" | nc -U $SOCK
# Example output:
#   0: D267DC10-... cmux: ubuntu
# * 1: 9075D919-... exp: statusline   ← user is here; doesn't matter
#   2: 258EB4B4-... o: mctrl

# Find target workspace UUID by name
WS_UUID=$(printf "list_workspaces\n" | nc -U $SOCK \
  | grep "cmux: ubuntu" | grep -oE '[A-F0-9-]{36}')

# List surfaces in that workspace
printf "list_surfaces $WS_UUID\n" | nc -U $SOCK
# Output:
#   * 0: 87DB76A9-...   supervisor (cmux)
#     1: F05FCE84-...   cmux_coder

# Extract coder surface UUID by label (never by index — indices shift)
CODER_UUID=$(printf "list_surfaces $WS_UUID\n" | nc -U $SOCK \
  | grep "cmux_coder" | grep -oE '[A-F0-9-]{36}')
```

## Rule 2: Use JSON API for headless cross-workspace sends

The plain-text `send_surface` command FAILS cross-workspace. Always use the JSON API:

| Method | Cross-workspace? | Notes |
|---|---|---|
| `surface.send_text` (JSON) | ✅ always works | Include `\n` in text for enter |
| `send_surface` (plain text) | ❌ fails cross-workspace | Only works if workspace is selected |
| `read_screen` | ❌ current workspace only | Use index, not UUID |

## Sending text (headless, cross-workspace)

```bash
# Single command: type + enter (append \n to submit)
printf '{"method":"surface.send_text","params":{"surface_id":"'"$CODER_UUID"'","text":"your instruction here\\n"}}\n' | nc -U $SOCK
```

This works from any workspace without switching focus. The `\n` at end acts as Enter.

## Checking if idle

```bash
# Send a harmless probe — if queued=false and ok=true, surface accepted input
result=$(printf '{"method":"surface.send_text","params":{"surface_id":"'"$CODER_UUID"'","text":""}}\n' | nc -U $SOCK)
# Check result.ok and result.queued
```

## Creating workspaces and surfaces

```bash
# Create workspace
printf '{"method":"workspace.create","params":{"title":"my-workspace"}}\n' | nc -U $SOCK
# Returns workspace_id

# Rename workspace
printf '{"method":"workspace.rename","params":{"workspace_id":"UUID","title":"new name"}}\n' | nc -U $SOCK

# Add a second tab/surface
printf '{"method":"surface.create","params":{"workspace_id":"UUID"}}\n' | nc -U $SOCK
# Returns surface_id
```

## Special keys (when \n in text isn't enough)

For key combos, fall back to plain text protocol (requires workspace focus):
```bash
printf "send_key_surface $CODER_UUID ctrl-c\n" | nc -U $SOCK
printf "send_key_surface $CODER_UUID ctrl-a\n" | nc -U $SOCK
printf "send_key_surface $CODER_UUID ctrl-k\n" | nc -U $SOCK
```

Available: `ctrl-c`, `ctrl-d`, `enter`, `tab`, `escape`, `up`, `down`, `left`, `right`

## Reading a pane's screen (current workspace only)

`read_screen` requires a surface **index** (not UUID) and only works when the target is in the user's currently focused workspace. Obtain the index from `list_surfaces` output (e.g. `1: F05FCE84-... cmux_coder` → index is `1`).

```bash
# IDX = index from list_surfaces for the focused workspace (replace with actual value)
IDX=1
printf "read_screen $IDX --lines 40\n" | nc -U $SOCK
printf "read_screen $IDX --lines 80 --scrollback\n" | nc -U $SOCK
```

If the user is in a different workspace, infer state from the filesystem instead:
```bash
cd /path/to/project && git log --oneline -5
ls -lt src/   # recently modified files
```

## Full headless example

```bash
SOCK="/tmp/cmux-debug-appclick.sock"

# 1. Find coder surface by workspace name
WS_UUID=$(printf "list_workspaces\n" | nc -U $SOCK \
  | grep "cmux: ubuntu" | grep -oE '[A-F0-9-]{36}')
CODER_UUID=$(printf "list_surfaces $WS_UUID\n" | nc -U $SOCK \
  | grep "cmux_coder" | grep -oE '[A-F0-9-]{36}')

# 2. Send task headlessly (no workspace switch needed)
printf '{"method":"surface.send_text","params":{"surface_id":"'"$CODER_UUID"'","text":"cargo build && cargo test\\n"}}\n' | nc -U $SOCK

# 3. Monitor progress via filesystem (no read_screen needed)
sleep 30
cd /path/to/project && git log --oneline -3
```

## Creating a fresh workspace with two tabs

```bash
SOCK="/tmp/cmux-debug-appclick.sock"

# Create workspace
WS=$(printf '{"method":"workspace.create","params":{"title":"my-test"}}\n' | nc -U $SOCK \
  | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['result']['workspace_id'])")

# Rename it
printf '{"method":"workspace.rename","params":{"workspace_id":"'"$WS"'","title":"test: a/b"}}\n' | nc -U $SOCK

# Add second tab
TAB2=$(printf '{"method":"surface.create","params":{"workspace_id":"'"$WS"'"}}\n' | nc -U $SOCK \
  | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['result']['surface_id'])")

# Get first tab
TAB1=$(printf "list_surfaces $WS\n" | nc -U $SOCK | grep "0:" | grep -oE '[A-F0-9-]{36}')

# Send commands to both tabs headlessly
printf '{"method":"surface.send_text","params":{"surface_id":"'"$TAB1"'","text":"echo tab1\\n"}}\n' | nc -U $SOCK
printf '{"method":"surface.send_text","params":{"surface_id":"'"$TAB2"'","text":"echo tab2\\n"}}\n' | nc -U $SOCK
```

## Rules summary

1. **Never use `select_workspace`** — it switches the user's visible workspace.
2. **Find workspace by NAME** (`list_workspaces` → grep name → get UUID).
3. **Use JSON API for sends** — `surface.send_text` works headlessly cross-workspace.
4. **Append `\n` to text** — acts as Enter key submission.
5. **Read by index only** — `read_screen` requires being in the right workspace; use git/filesystem for cross-workspace monitoring.
6. **Create workspaces via JSON** — `workspace.create` + `surface.create` for multi-tab setups.
