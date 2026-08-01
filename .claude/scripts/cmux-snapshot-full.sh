#!/usr/bin/env bash
# cmux-snapshot-full.sh — READ-ONLY deep snapshot of every cmux workspace/pane/surface,
# including each surface's resume_binding (exact CLI command, cwd, env, session checkpoint)
# and its live process tree.
#
# Extends ~/.claude/scripts/cmux-backup.sh, which only captures workspace-level cwd.
# Output: ~/.cmux-backups/cmux-snapshot-<timestamp>.json  (+ .md human summary)
#
# Read-only guarantees: only calls workspace.list / surface.list / tree / top.
# Never calls select_workspace, focus, send, or any mutating RPC.

set -euo pipefail

resolve_cmux_bin() {
  if [[ -n "${CMUX_BIN:-}" ]]; then echo "$CMUX_BIN"; return; fi
  if [[ -n "${CMUX_BUNDLED_CLI_PATH:-}" && -x "${CMUX_BUNDLED_CLI_PATH}" ]]; then
    echo "$CMUX_BUNDLED_CLI_PATH"; return
  fi
  command -v cmux
}

CMUX_BIN_RESOLVED=$(resolve_cmux_bin)
SOCK="${CMUX_SOCKET_PATH:-${CMUX_SOCKET:-}}"
OUTDIR="$HOME/.cmux-backups"
TIMESTAMP=$(date +%Y-%m-%dT%H-%M-%S)
OUTFILE="$OUTDIR/cmux-snapshot-$TIMESTAMP.json"
MDFILE="$OUTDIR/cmux-snapshot-$TIMESTAMP.md"

mkdir -p "$OUTDIR"

SOCK_ARGS=()
[[ -n "$SOCK" ]] && SOCK_ARGS=(--socket "$SOCK")

if ! "$CMUX_BIN_RESOLVED" "${SOCK_ARGS[@]}" ping >/dev/null 2>&1; then
  echo "ERROR: cmux socket unreachable via: $CMUX_BIN_RESOLVED ${SOCK_ARGS[*]}" >&2
  exit 1
fi

"$CMUX_BIN_RESOLVED" "${SOCK_ARGS[@]}" tree --all               > "$OUTDIR/.snap-tree-$TIMESTAMP.txt" 2>&1 || true
"$CMUX_BIN_RESOLVED" "${SOCK_ARGS[@]}" top --all --processes --format tsv \
                                                                > "$OUTDIR/.snap-top-$TIMESTAMP.tsv"  2>&1 || true

python3 - "$CMUX_BIN_RESOLVED" "$OUTFILE" "$MDFILE" "$TIMESTAMP" \
         "$OUTDIR/.snap-tree-$TIMESTAMP.txt" "$OUTDIR/.snap-top-$TIMESTAMP.tsv" "${SOCK_ARGS[@]}" <<'PYEOF'
import sys, json, subprocess, os, collections

CMUX_BIN, OUTFILE, MDFILE, TIMESTAMP, TREEFILE, TOPFILE = sys.argv[1:7]
SOCK_ARGS = sys.argv[7:]

def rpc(method, params=None):
    cmd = [CMUX_BIN, *SOCK_ARGS, "rpc", method, json.dumps(params or {})]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}

# --- live process tree per surface, from `top --processes --format tsv` ---
# columns: cpu, mem, count, kind, ref, parent_ref, name
procs_by_surface = collections.defaultdict(list)
proc_by_pid = {}
try:
    with open(TOPFILE) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 7:
                continue
            cpu, mem, cnt, kind, ref, parent, name = parts[:7]
            if kind != "process":
                continue
            proc_by_pid[ref] = {"pid": ref, "name": name, "parent": parent, "cpu": cpu}
            if parent.startswith("surface:"):
                procs_by_surface[parent].append({"pid": ref, "name": name, "cpu": cpu})
except FileNotFoundError:
    pass

# children of a surface-rooted pid (e.g. bash -> claude.exe -> node)
def descendants(pid, depth=0):
    out = []
    for p in proc_by_pid.values():
        if p["parent"] == pid:
            out.append({"pid": p["pid"], "name": p["name"], "cpu": p["cpu"], "depth": depth + 1})
            out.extend(descendants(p["pid"], depth + 1))
    return out

ws_data = rpc("workspace.list")
workspaces_raw = ws_data.get("workspaces", [])

workspaces = []
for ws in workspaces_raw:
    ws_uuid = ws.get("id", "")
    ws_ref = ws.get("ref", "")
    surf_data = rpc("surface.list", {"workspace_id": ws_uuid or ws_ref})
    surfaces = []
    for s in surf_data.get("surfaces", []):
        rb = s.get("resume_binding") or {}
        sref = s.get("ref", "")
        roots = procs_by_surface.get(sref, [])
        tree = []
        for r in roots:
            tree.append({"pid": r["pid"], "name": r["name"], "cpu": r["cpu"], "depth": 0})
            tree.extend(descendants(r["pid"]))
        surfaces.append({
            "ref": sref,
            "id": s.get("id", ""),
            "title": s.get("title", ""),
            "type": s.get("type", "terminal"),
            "pane_ref": s.get("pane_ref"),
            "index_in_pane": s.get("index_in_pane"),
            "focused": s.get("focused", False),
            "initial_command": s.get("initial_command"),
            "requested_working_directory": s.get("requested_working_directory"),
            "resume": {
                "kind": rb.get("kind"),
                "name": rb.get("name"),
                "cwd": rb.get("cwd"),
                "command": rb.get("command"),
                "checkpoint_id": rb.get("checkpoint_id"),
                "auto_resume": rb.get("auto_resume"),
                "source": rb.get("source"),
                "environment": rb.get("environment"),
            } if rb else None,
            "live_processes": tree,
        })
    workspaces.append({
        "ref": ws_ref,
        "id": ws_uuid,
        "index": ws.get("index", -1),
        "title": ws.get("title", ""),
        "pinned": ws.get("pinned", False),
        "selected": ws.get("selected", False),
        "custom_color": ws.get("custom_color"),
        "description": ws.get("description"),
        "current_directory": ws.get("current_directory"),
        "surfaces": surfaces,
    })

tree_txt = ""
try:
    tree_txt = open(TREEFILE).read()
except FileNotFoundError:
    pass

snapshot = {
    "timestamp": TIMESTAMP,
    "cmux_bin": CMUX_BIN,
    "app_bundle_id": os.environ.get("CMUX_BUNDLE_ID"),
    "app_tag": os.environ.get("CMUX_TAG"),
    "socket": os.environ.get("CMUX_SOCKET_PATH"),
    "workspace_count": len(workspaces),
    "surface_count": sum(len(w["surfaces"]) for w in workspaces),
    "topology_tree": tree_txt,
    "workspaces": workspaces,
}

with open(OUTFILE, "w") as f:
    json.dump(snapshot, f, indent=2)

# --- human-readable summary ---
NOISE = {"bash", "zsh", "sh", "node", "Python", "caffeinate", "head", "grep"}
lines = [f"# cmux snapshot {TIMESTAMP}", ""]
lines.append(f"- workspaces: {len(workspaces)}  surfaces: {snapshot['surface_count']}")
lines.append(f"- app: {snapshot['app_bundle_id']} (tag `{snapshot['app_tag']}`)")
lines.append("")
lines.append("| ws | workspace | surface | cwd | CLI (resume) | live procs |")
lines.append("|---:|---|---|---|---|---|")
for w in workspaces:
    for s in w["surfaces"]:
        r = s["resume"] or {}
        cwd = r.get("cwd") or s.get("requested_working_directory") or w.get("current_directory") or ""
        kind = r.get("kind") or ""
        ck = (r.get("checkpoint_id") or "")[:8]
        cli = f"{kind}" + (f" ({ck})" if ck else "")
        live = ",".join(sorted({p["name"] for p in s["live_processes"] if p["name"] not in NOISE})) or "-"
        lines.append(f"| {w['index']} | {w['title']} | {s['ref']} | {cwd} | {cli or '-'} | {live} |")
with open(MDFILE, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"snapshot -> {OUTFILE}")
print(f"summary  -> {MDFILE}")
print(f"{len(workspaces)} workspaces / {snapshot['surface_count']} surfaces")
resumable = sum(1 for w in workspaces for s in w["surfaces"] if s["resume"] and s["resume"].get("command"))
print(f"{resumable} surfaces carry a resume_binding command")
PYEOF
