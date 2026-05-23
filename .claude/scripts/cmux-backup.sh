#!/usr/bin/env bash
# cmux-backup.sh — snapshot all cmux workspaces + surfaces + cwds via socket API
# Output: ~/.cmux-backups/cmux-backup-<timestamp>.json

set -euo pipefail

SOCK="${CMUX_SOCKET:-$HOME/Library/Application Support/cmux/cmux.sock}"
OUTDIR="$HOME/.cmux-backups"
TIMESTAMP=$(date +%Y-%m-%dT%H-%M-%S)
OUTFILE="$OUTDIR/cmux-backup-$TIMESTAMP.json"

mkdir -p "$OUTDIR"

if [[ ! -S "$SOCK" ]]; then
  echo "ERROR: cmux socket not found at: $SOCK" >&2
  exit 1
fi

python3 - "$SOCK" "$OUTFILE" "$TIMESTAMP" <<'PYEOF'
import sys, json, subprocess, re, os

SOCK = sys.argv[1]
OUTFILE = sys.argv[2]
TIMESTAMP = sys.argv[3]

def nc(cmd, timeout=5):
    result = subprocess.run(
        ['nc', '-U', SOCK],
        input=cmd + '\n',
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip()

def nc_json(method, params=None):
    payload = json.dumps({"method": method, "params": params or {}})
    raw = nc(payload)
    try:
        return json.loads(raw)
    except Exception:
        return {}

def parse_sidebar_state(raw):
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if '=' in line and not line.startswith(' '):
            k, _, v = line.partition('=')
            result[k.strip()] = v.strip() if v.strip() != 'none' else None
    return result

def parse_dir_from_title(title):
    """Extract directory from terminal titles like 'user@host: ~/path/to/dir'."""
    m = re.search(r':\s*(~[^\s]*/[^\s]*|~/|~$|/[^\s]+)', title)
    if m:
        path = m.group(1)
        # Expand ~ to home
        if path.startswith('~'):
            path = os.path.expanduser(path)
        return path
    return None

# 1. Get all workspaces
ws_data = nc_json("workspace.list")
workspaces_raw = ws_data.get("result", {}).get("workspaces", [])

workspaces = []
for ws in workspaces_raw:
    ws_id = ws.get("id", "")
    ws_title = ws.get("title", "")
    ws_index = ws.get("index", -1)
    ws_selected = ws.get("selected", False)
    ws_curdir = ws.get("current_directory", None)

    # 2. sidebar_state for cwd + git info (workspace-level)
    sidebar_raw = nc(f"sidebar_state --tab={ws_id}")
    sidebar = parse_sidebar_state(sidebar_raw)
    cwd = sidebar.get("cwd") or ws_curdir
    focused_cwd = sidebar.get("focused_cwd")
    git_branch = sidebar.get("git_branch")
    pr = sidebar.get("pr")
    pr_label = sidebar.get("pr_label")

    # 3. Get surfaces for this workspace
    surf_data = nc_json("surface.list", {"workspace_id": ws_id})
    surfaces_raw = surf_data.get("result", {}).get("surfaces", [])
    surfaces = []
    for s in surfaces_raw:
        title = s.get("title", "")
        title_dir = parse_dir_from_title(title)
        surfaces.append({
            "id": s.get("id", ""),
            "title": title,
            "type": s.get("type", "terminal"),
            "pane_id": s.get("pane_id", ""),
            "index": s.get("index", -1),
            "focused": s.get("focused", False),
            "title_dir": title_dir,  # dir parsed from terminal title
        })

    # Best cwd: prefer focused surface's title_dir if sidebar cwd is just ~
    home = os.path.expanduser("~")
    best_cwd = cwd
    if cwd in (home, None):
        # Try focused surface's title_dir
        focused_id = sidebar.get("focused_panel")
        for s in surfaces:
            if s.get("focused") or s.get("id") == focused_id:
                if s.get("title_dir") and s["title_dir"] != home:
                    best_cwd = s["title_dir"]
                    break
        # Fallback: any surface with a non-home title_dir
        if best_cwd in (home, None):
            for s in surfaces:
                if s.get("title_dir") and s["title_dir"] != home:
                    best_cwd = s["title_dir"]
                    break

    workspaces.append({
        "id": ws_id,
        "title": ws_title,
        "index": ws_index,
        "selected": ws_selected,
        "current_directory": ws_curdir,
        "cwd": cwd,
        "best_cwd": best_cwd,
        "focused_cwd": focused_cwd,
        "git_branch": git_branch,
        "pr": pr,
        "pr_label": pr_label,
        "surfaces": surfaces,
    })

backup = {
    "timestamp": TIMESTAMP,
    "socket": SOCK,
    "workspace_count": len(workspaces),
    "workspaces": workspaces,
}

with open(OUTFILE, 'w') as f:
    json.dump(backup, f, indent=2)

# Print summary table
print(f"cmux backup → {OUTFILE}")
print(f"{'#':<4} {'Title':<38} {'Best CWD':<43} {'Branch'}")
print('-' * 108)
for ws in workspaces:
    idx = str(ws['index'])
    title = (ws['title'] or '')[:37]
    cwd_str = (ws['best_cwd'] or ws['current_directory'] or '')[:42]
    branch = (ws['git_branch'] or '')[:22]
    sel = '*' if ws['selected'] else ' '
    print(f"{sel}{idx:<3} {title:<38} {cwd_str:<43} {branch}")

print(f"\n{len(workspaces)} workspaces backed up → {OUTFILE}")
PYEOF
