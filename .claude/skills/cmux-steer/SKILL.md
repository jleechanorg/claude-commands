# cmux-steer — Control another cmux terminal tab via the Unix socket

**Usage**: Read and follow this skill directly; no `/cmux-steer` slash command is defined.

**Purpose**: Read and steer another agent's terminal pane (e.g. a coding agent)
from within cmux, without disrupting the user's active workspace navigation.

---

## Socket path

```bash
ls /tmp/cmux*.sock
# Tagged debug build: /tmp/cmux-debug-<tag>.sock
# Untagged debug:     /tmp/cmux-debug.sock
# Release:            /tmp/cmux.sock
SOCK="/tmp/cmux-debug-appclick.sock"  # update to match your build tag
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
