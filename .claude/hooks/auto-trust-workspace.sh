#!/usr/bin/env bash
# auto-trust-workspace.sh — SessionStart hook
# Pre-accepts the workspace trust dialog for the current working directory
# by setting `projects.<cwd>.hasTrustDialogAccepted = true` in ~/.claude.json.
#
# The trust dialog is a per-path security gate; this hook makes the answer
# always "yes" for whatever dir claude was launched in. Designed to be a
# no-op for non-interactive (-p) sessions and for paths already trusted.
set -euo pipefail

CLAUDE_JSON="$HOME/.claude.json"
CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Skip silently if the state file is missing or unreadable.
if [[ ! -f "$CLAUDE_JSON" ]]; then
    exit 0
fi

python3 - "$CLAUDE_JSON" "$CWD" <<'PY'
import json, os, sys, tempfile, shutil

claude_json, cwd = sys.argv[1], sys.argv[2]
if not os.path.exists(claude_json):
    sys.exit(0)

try:
    with open(claude_json, "r", encoding="utf-8") as f:
        data = json.load(f)
except (OSError, json.JSONDecodeError):
    # If the file is malformed, do not crash the session.
    sys.exit(0)

projects = data.setdefault("projects", {})
entry = projects.setdefault(cwd, {})

if entry.get("hasTrustDialogAccepted") is True:
    # Already trusted; nothing to do (avoid touching mtime unnecessarily).
    sys.exit(0)

entry["hasTrustDialogAccepted"] = True

# Atomic write: write to temp file in the same dir, then rename.
dir_name = os.path.dirname(os.path.abspath(claude_json))
fd, tmp_path = tempfile.mkstemp(prefix=".claude.json.", dir=dir_name)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, claude_json)
except Exception:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    raise
PY
