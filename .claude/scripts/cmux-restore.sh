#!/usr/bin/env bash
# cmux-restore.sh — restore cmux workspaces from a backup JSON
#
# Usage:
#   cmux-restore.sh [--backup <file>]   # restore from specific file
#   cmux-restore.sh                     # restore from most recent backup
#   cmux-restore.sh --list              # list available backups
#   cmux-restore.sh --dry-run           # show what would be created, no changes

set -euo pipefail

SOCK="${CMUX_SOCKET:-$HOME/Library/Application Support/cmux/cmux.sock}"
BACKUP_DIR="$HOME/.cmux-backups"
BACKUP_FILE=""
DRY_RUN=false
LIST_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup) BACKUP_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --list) LIST_ONLY=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ "$LIST_ONLY" == true ]]; then
  echo "Available backups in $BACKUP_DIR:"
  ls -lt "$BACKUP_DIR"/cmux-backup-*.json 2>/dev/null | awk '{print $NF}' | head -20 || echo "(none)"
  exit 0
fi

if [[ -z "$BACKUP_FILE" ]]; then
  BACKUP_FILE=$(ls -t "$BACKUP_DIR"/cmux-backup-*.json 2>/dev/null | head -1)
  if [[ -z "$BACKUP_FILE" ]]; then
    echo "ERROR: No backup files found in $BACKUP_DIR. Run cmux-backup.sh first." >&2
    exit 1
  fi
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "ERROR: Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

echo "Restoring from: $BACKUP_FILE"
[[ "$DRY_RUN" == true ]] && echo "[DRY RUN — no changes will be made]"
echo ""

python3 - "$SOCK" "$BACKUP_FILE" "$DRY_RUN" <<'PYEOF'
import sys, json, subprocess, time

SOCK = sys.argv[1]
BACKUP_FILE = sys.argv[2]
DRY_RUN = sys.argv[3] == "True"

def nc(cmd, timeout=5):
    r = subprocess.run(['nc', '-U', SOCK], input=cmd + '\n',
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def nc_json(method, params=None):
    payload = json.dumps({"method": method, "params": params or {}})
    raw = nc(payload)
    try:
        return json.loads(raw)
    except Exception:
        return {}

def send_text(surface_id, text):
    payload = json.dumps({"method": "surface.send_text",
                          "params": {"surface_id": surface_id, "text": text}})
    raw = nc(payload)
    try:
        d = json.loads(raw)
        return d.get("ok", False)
    except Exception:
        return False

with open(BACKUP_FILE) as f:
    backup = json.load(f)

backup_ts = backup.get("timestamp", "?")
backup_count = backup.get("workspace_count", 0)
print(f"Backup timestamp : {backup_ts}")
print(f"Backup workspaces: {backup_count}")
print("")

# Get current workspace titles to detect duplicates
current_data = nc_json("workspace.list")
current_titles = set()
for ws in current_data.get("result", {}).get("workspaces", []):
    current_titles.add(ws.get("title", ""))

created = []
skipped = []
failed = []

for ws in backup.get("workspaces", []):
    title = ws.get("title", "")
    best_cwd = ws.get("best_cwd") or ws.get("current_directory") or "~"
    git_branch = ws.get("git_branch")
    surfaces = ws.get("surfaces", [])

    if title in current_titles:
        skipped.append(title)
        print(f"  SKIP  {title}  (already exists)")
        continue

    print(f"  CREATE {title}  →  {best_cwd}")

    if DRY_RUN:
        created.append(title)
        continue

    # Create workspace
    result = nc_json("workspace.create", {
        "title": title,
        "current_directory": best_cwd,
    })
    if not result.get("ok", False):
        print(f"         ERROR creating workspace: {result}")
        failed.append(title)
        continue

    new_ws_id = result.get("result", {}).get("workspace_id", "")
    time.sleep(0.4)  # let shell initialize

    # Get the auto-created surface
    surf_data = nc_json("surface.list", {"workspace_id": new_ws_id})
    new_surfaces = surf_data.get("result", {}).get("surfaces", [])
    if not new_surfaces:
        failed.append(title)
        continue

    # cd to best_cwd in the first surface (workspace.create sets cwd but
    # the shell may not inherit it — send explicit cd for reliability)
    first_surf_id = new_surfaces[0]["id"]
    send_text(first_surf_id, f"cd {best_cwd}\n")
    time.sleep(0.2)

    # Create additional surfaces if the backup had more than one
    for i, backup_surf in enumerate(surfaces[1:], start=1):
        surf_cwd = backup_surf.get("title_dir") or best_cwd
        surf_result = nc_json("surface.create", {"workspace_id": new_ws_id})
        if surf_result.get("ok"):
            new_surf_id = surf_result.get("result", {}).get("surface_id", "")
            time.sleep(0.3)
            send_text(new_surf_id, f"cd {surf_cwd}\n")
            print(f"         + surface {i}: {backup_surf.get('title','?')[:50]}  →  {surf_cwd}")
        else:
            print(f"         ! surface {i} create failed")

    created.append(title)

print("")
print(f"Done — created: {len(created)}, skipped: {len(skipped)}, failed: {len(failed)}")
if failed:
    print(f"Failed: {failed}")
PYEOF
