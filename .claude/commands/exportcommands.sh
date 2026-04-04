#!/usr/bin/env bash
# Primary entry for /exportcommands — delegates to exportcommands.py (clone, copy, filter, PR).
# Same flags as Python (e.g. --dry-run skips commit, push, and gh pr create).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/exportcommands.py" "$@"
