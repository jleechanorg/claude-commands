#!/usr/bin/env bash
# cmux-backup.sh — snapshot all cmux workspaces + surfaces + cwds via the cmux CLI's rpc socket API
# Output: ~/.cmux-backups/cmux-backup-<timestamp>.json
#
# Uses the `cmux` binary's `rpc` subcommand (not raw nc) because the binary handles
# framing/auth and auto-discovers tagged debug sockets; hand-rolled nc JSON against a
# hardcoded socket path silently returns 0 workspaces when that socket is stale.

set -euo pipefail

resolve_cmux_bin() {
  if [[ -n "${CMUX_BIN:-}" ]]; then
    echo "$CMUX_BIN"
    return
  fi
  # Prefer the binary belonging to the currently-running cmux app (matches its socket).
  local running_bin
  running_bin=$(ps aux | grep -o '/Applications/cmux[^/]*\.app/Contents/MacOS/cmux[^ ]*' | head -1 || true)
  if [[ -n "$running_bin" ]]; then
    local app_dir
    app_dir=$(dirname "$(dirname "$running_bin")")
    echo "$app_dir/Resources/bin/cmux"
    return
  fi
  command -v cmux
}

CMUX_BIN_RESOLVED=$(resolve_cmux_bin)
SOCK="${CMUX_SOCKET_PATH:-${CMUX_SOCKET:-}}"
OUTDIR="$HOME/.cmux-backups"
TIMESTAMP=$(date +%Y-%m-%dT%H-%M-%S)
OUTFILE="$OUTDIR/cmux-backup-$TIMESTAMP.json"

mkdir -p "$OUTDIR"

SOCK_ARGS=()
if [[ -n "$SOCK" ]]; then
  SOCK_ARGS=(--socket "$SOCK")
fi

if ! "$CMUX_BIN_RESOLVED" "${SOCK_ARGS[@]}" ping >/dev/null 2>&1; then
  echo "ERROR: cmux socket unreachable via: $CMUX_BIN_RESOLVED ${SOCK_ARGS[*]}" >&2
  exit 1
fi

python3 - "$CMUX_BIN_RESOLVED" "$OUTFILE" "$TIMESTAMP" "${SOCK_ARGS[@]}" <<'PYEOF'
import sys, json, subprocess

CMUX_BIN = sys.argv[1]
OUTFILE = sys.argv[2]
TIMESTAMP = sys.argv[3]
SOCK_ARGS = sys.argv[4:]

def rpc(method, params=None):
    cmd = [CMUX_BIN, *SOCK_ARGS, "rpc", method, json.dumps(params or {})]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except Exception:
        return {}

ws_data = rpc("workspace.list")
workspaces_raw = ws_data.get("workspaces", [])

workspaces = []
for ws in workspaces_raw:
    ws_ref = ws.get("ref", "")
    surf_data = rpc("surface.list", {"workspace_id": ws_ref})
    surfaces_raw = surf_data.get("surfaces", [])
    surfaces = [
        {
            "id": s.get("id", ""),
            "ref": s.get("ref", ""),
            "title": s.get("title", ""),
            "type": s.get("type", "terminal"),
            "focused": s.get("focused", False),
        }
        for s in surfaces_raw
    ]
    workspaces.append({
        "ref": ws_ref,
        "id": ws.get("id", ""),
        "index": ws.get("index", -1),
        "title": ws.get("title", ""),
        "pinned": ws.get("pinned", False),
        "selected": ws.get("selected", False),
        "custom_color": ws.get("custom_color"),
        "description": ws.get("description"),
        "current_directory": ws.get("current_directory"),
        "surfaces": surfaces,
    })

backup = {
    "timestamp": TIMESTAMP,
    "cmux_bin": CMUX_BIN,
    "workspace_count": len(workspaces),
    "workspaces": workspaces,
}

with open(OUTFILE, 'w') as f:
    json.dump(backup, f, indent=2)

print(f"cmux backup -> {OUTFILE}")
print(f"{'#':<4} {'Title':<38} {'Dir':<43} {'Pinned'}")
print('-' * 100)
for ws in workspaces:
    idx = str(ws['index'])
    title = (ws['title'] or '')[:37]
    cwd_str = (ws['current_directory'] or '')[:42]
    pin = 'pin' if ws['pinned'] else ''
    sel = '*' if ws['selected'] else ' '
    print(f"{sel}{idx:<3} {title:<38} {cwd_str:<43} {pin}")

print(f"\n{len(workspaces)} workspaces backed up -> {OUTFILE}")
PYEOF
