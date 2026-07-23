---
name: cmux-socket-control
description: Control cmux tabs, workspaces, and terminal panes via Unix socket. Use when reading terminal output, sending commands to another agent's pane, switching tabs, or monitoring coder progress.
---

# cmux Socket Control

> **REQUIRED (2026-06-09):** For any `cmux send` calls in this skill, use the canonical `send_and_submit()` wrapper at `~/.hermes_prod/skills/cmux/scripts/cmux_client.py` — the bare two-command pattern below has no proof of submission and burned us 3 times in 30 minutes on the cost-workspace agent. This skill is fine for socket discovery, read operations, and tree/walk ops; steering must go through the wrapper. See `~/.hermes_prod/skills/cmux-send-submit/SKILL.md`.

## ⚠️ SUPERSEDED — Use `cmux` CLI, not raw socket protocol

The raw `nc -U $SOCK` examples below still work for low-level access, but they
have a **name → surface resolution gap** that has caused repeated failures
("why do you always get confused when I name a surface"). The canonical recipe
is the `cmux` CLI, which exposes workspace/surface/tab refs directly.

**Always start here when the user names a surface, tab, or workspace:**

```bash
# 1. MY workspace = caller.workspace_ref (NOT focused — focus may be elsewhere).
#    When run inside cmux itself, `caller` is populated; when run from a
#    standalone terminal, use the workspace you already know about or fall
#    back to `cmux identify --json | jq '.focused.workspace_ref'`.
WS=$(cmux identify --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["caller"]["workspace_ref"])')

# 2. Every pane + tab by name; ◀ here = caller surface, ◀ active = focus.
#    Do NOT filter the output — sibling tabs and the ◀ markers are the signal.
cmux tree --all --workspace "$WS"

# 3. Read the target by the surface:N ref shown in the tree.
cmux read-screen --workspace "$WS" --surface surface:N --lines 80
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

---

## Find the socket

```bash
# Release build (main cmux.app)
SOCK="$HOME/Library/Application Support/cmux/cmux.sock"

# Dev builds — each has its own socket, discoverable two ways:
# 1. From the saved last-socket-path files:
ls ~/Library/Application\ Support/cmux/dev-*-last-socket-path
cat ~/Library/Application\ Support/cmux/dev-may-18-last-socket-path
# → /tmp/cmux-debug-may-18.sock

# 2. From the running process:
lsof -p $(pgrep -f "cmux DEV may-18") | grep -E "\.sock"
# → /tmp/cmux-debug-may-18.sock
```

Common paths:
- Release: `~/Library/Application Support/cmux/cmux.sock`
- Tagged debug build: `/tmp/cmux-debug-<tag>.sock` (e.g. `/tmp/cmux-debug-may-18.sock`)
- Untagged debug: `/tmp/cmux-debug.sock`

## Routing CLI commands to a specific build

```bash
# Use CMUX_SOCKET_PATH to target any build
CMUX_SOCKET_PATH=/tmp/cmux-debug-may-18.sock cmux list-workspaces
CMUX_SOCKET_PATH=/tmp/cmux-debug-may-18.sock cmux tree
```

---

## Rule 1: ALWAYS look up workspace by NAME, never by index

The user can switch workspaces at any time — indices shift. UUID stays stable.

```bash
SOCK="/tmp/cmux-debug-appclick.sock"

# 1. Find workspace UUID by name
WS_UUID=$(printf "list_workspaces\n" | nc -U $SOCK | grep "cmux: ubuntu" | grep -oE '[A-F0-9-]{36}')

# 2. List surfaces in that workspace
printf "list_surfaces $WS_UUID\n" | nc -U $SOCK
# Output:
#   * 0: 87DB76A9-...   supervisor (cmux)
#     1: F05FCE84-...   coder (cmux_coder)

# 3. Extract coder UUID
CODER_UUID=$(printf "list_surfaces $WS_UUID\n" | nc -U $SOCK | grep "cmux_coder\|1:" | grep -oE '[A-F0-9-]{36}' | head -1)
```

**Known stable UUIDs (cmux: ubuntu workspace, current session):**

| Surface | UUID | Role |
|---|---|---|
| 0 | `87DB76A9-60A8-43FC-BFC2-51A5DECEA9B8` | supervisor (cmux) |
| 1 | `F05FCE84-ECA7-4944-BCAA-7DFFC105D0D9` | coder (cmux_coder) |

Re-run `list_surfaces` if you get unexpected errors — UUIDs reset on app restart.

---

## Sending to a pane (cross-workspace safe)

`send_surface` works regardless of which workspace the user has focused.
`send_key_surface` sends key chords.

```bash
SOCK="/tmp/cmux-debug-appclick.sock"
UUID="F05FCE84-ECA7-4944-BCAA-7DFFC105D0D9"   # cmux_coder

# Human-simulation pattern: clear → type → submit
printf "send_key_surface $UUID ctrl-a\n" | nc -U $SOCK
printf "send_key_surface $UUID ctrl-k\n" | nc -U $SOCK
printf "send_surface $UUID your message here\n" | nc -U $SOCK
sleep 0.2
printf "send_key_surface $UUID enter\n" | nc -U $SOCK
```

---

## Reading a pane

`read_screen` only works in the **current** workspace (where user is focused).
UUID-based reads fail cross-workspace. Use git log as fallback.

```bash
# Read pane (only if user is in the same workspace)
printf "read_screen 1 --lines 40\n" | nc -U $SOCK
printf "read_screen 1 --lines 60 --scrollback\n" | nc -U $SOCK

# Fallback when cross-workspace: check git for coder progress
git -C $HOME/projects_reference/cmux_ubuntu log --oneline -5
```

---

## Checking if a pane is busy before sending

```bash
result=$(printf "send_surface $UUID probe\n" | nc -U $SOCK)
# "OK"                        → idle at prompt, safe to send
# "ERROR: Failed to send input" → running a command, wait and retry
```

**Wait-until-idle loop:**

```bash
while true; do
  result=$(printf "send_surface $UUID probe\n" | nc -U $SOCK)
  if [ "$result" = "OK" ]; then
    # Clear the probe text, then send the real message
    printf "send_key_surface $UUID ctrl-a\n" | nc -U $SOCK
    printf "send_key_surface $UUID ctrl-k\n" | nc -U $SOCK
    break
  fi
  sleep 2
done
```

---

## Full pattern: find coder + check busy + send task

```bash
SOCK="/tmp/cmux-debug-appclick.sock"

# 1. Find coder by workspace name (index-safe)
WS_UUID=$(printf "list_workspaces\n" | nc -U $SOCK | grep "cmux: ubuntu" | grep -oE '[A-F0-9-]{36}')
CODER_UUID=$(printf "list_surfaces $WS_UUID\n" | nc -U $SOCK | grep "1:" | grep -oE '[A-F0-9-]{36}')

# 2. Check busy
result=$(printf "send_surface $CODER_UUID probe\n" | nc -U $SOCK)
if [ "$result" = "OK" ]; then
  # 3. Clear probe, send task
  printf "send_key_surface $CODER_UUID ctrl-a\n" | nc -U $SOCK
  printf "send_key_surface $CODER_UUID ctrl-k\n" | nc -U $SOCK
  printf "send_surface $CODER_UUID <your task here>\n" | nc -U $SOCK
  sleep 0.2
  printf "send_key_surface $CODER_UUID enter\n" | nc -U $SOCK
else
  echo "Coder busy — checking git for progress"
  git -C $HOME/projects_reference/cmux_ubuntu log --oneline -3
fi
```

---

## Common commands reference

```bash
# Discovery
printf "list_workspaces\n"                    | nc -U $SOCK
printf "list_surfaces <ws-uuid>\n"            | nc -U $SOCK

# Full hierarchy (v2 protocol — windows, workspaces, panes, surfaces in one call)
printf '{"method":"system.tree"}\n'           | nc -U $SOCK
printf '{"method":"system.identify"}\n'       | nc -U $SOCK   # self-location: which pane am I in?

# Read (current workspace only)
printf "read_screen 0 --lines 30\n"           | nc -U $SOCK
printf "read_screen 1 --lines 60 --scrollback\n" | nc -U $SOCK

# Send (cross-workspace, by UUID)
printf "send_surface <uuid> <text>\n"         | nc -U $SOCK
printf "send_key_surface <uuid> ctrl-c\n"     | nc -U $SOCK
printf "send_key_surface <uuid> enter\n"      | nc -U $SOCK
printf "send_key_surface <uuid> ctrl-a\n"     | nc -U $SOCK
printf "send_key_surface <uuid> ctrl-k\n"     | nc -U $SOCK
```

---

## Future: MCP server (PR #3, jleechanorg/cmux)

`scripts/cmux_mcp_server.py` (Python) and `scripts/cmux-mcp-server.mjs` (JS) are thin
MCP adapters over the same socket API. Tool names map to our nc patterns:

| MCP tool | Equivalent nc command |
|---|---|
| `cmux_socket_discover` | `ls /tmp/cmux*.sock` |
| `cmux_system_tree` | `{"method":"system.tree"}` |
| `cmux_list_workspaces` | `list_workspaces` |
| `cmux_list_surfaces` | `list_surfaces <uuid>` |
| `cmux_send_text` | `send_surface <uuid> <text>` + `send_key_surface enter` |
| `cmux_read_text` | `read_screen <index> --lines N` |
| `cmux_socket_call` | raw nc pass-through escape hatch |
| `cmux_select_workspace` | ⚠ maps to `select_workspace` — check focus rules first |

Run: `python scripts/cmux_mcp_server.py --socket /tmp/cmux-debug-appclick.sock`

**Known issues in PR (not yet fixed):** credential leak in error log (mjs:156),
non-loopback HTTP binding (mjs:865). Do not expose HTTP port on non-loopback hosts.

---

## Workspace actions (pin, rename, color, reorder)

Use `workspace-action` — **not** `tab-action` — for workspace-level operations.

```bash
# Pin a workspace in the sidebar
cmux workspace-action --action pin --workspace workspace:4
CMUX_SOCKET_PATH=/tmp/cmux-debug-may-18.sock cmux workspace-action --action pin --workspace workspace:4

# Unpin
cmux workspace-action --action unpin --workspace workspace:4

# Bulk pin (loop over multiple workspaces)
for ws in workspace:4 workspace:6 workspace:7; do
    CMUX_SOCKET_PATH=/tmp/cmux-debug-may-18.sock cmux workspace-action --action pin --workspace $ws
done

# Rename
cmux workspace-action --action rename --workspace workspace:4 --title "new name"

# Set color
cmux workspace-action --action set-color --workspace workspace:4 --color Blue

# Reorder
cmux workspace-action --action move-top --workspace workspace:4
```

**⚠ `tab-action --action pin` is WRONG for workspace pinning** — it pins a surface tab
within a pane's horizontal tab bar, not the workspace in the sidebar. These are different.

| Command | What it pins |
|---|---|
| `workspace-action --action pin` | Workspace row in the sidebar ✅ |
| `tab-action --action pin` | Surface tab in a pane's horizontal tab bar ❌ (not workspaces) |

## Surface (tab) actions within a pane

```bash
# Pin a surface tab in the horizontal tab bar of a pane
cmux tab-action --action pin --surface surface:7 --workspace workspace:2

# Rename a tab
cmux tab-action --action rename --surface surface:7 --title "my label"

# Close other tabs
cmux tab-action --action close-others --surface surface:7
```

## Rules (non-negotiable)

1. **Never `select_workspace`** — it visibly switches the user's active workspace
2. **Always find by workspace NAME** — never hardcode index
3. **Use UUID for sends** — works cross-workspace without focus change
4. **UUID reads fail cross-workspace** — use `read_screen <index>` only when in the right workspace; otherwise use git log / filesystem
5. **send_surface types only** — always follow with `send_key_surface enter` to submit
6. **Clear first** — `ctrl-a` + `ctrl-k` before typing a new message
7. **Check busy before sending** — probe first, clear probe text on OK
