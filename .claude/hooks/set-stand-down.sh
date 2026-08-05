#!/bin/bash
# set-stand-down.sh — Helper to manage stand-down targets (branch/PR/path)
# Usage:
#   set-stand-down.sh add <target> "<reason>"
#   set-stand-down.sh remove <target>
#   set-stand-down.sh clear
#   set-stand-down.sh list

TARGETS_FILE="${STAND_DOWN_FILE:-/tmp/claude_stand_down_targets.json}"

case "${1:-}" in
  add|set)
    TARGET="${2:?Usage: set-stand-down.sh add <target> \"<reason>\"}"
    REASON="${3:-Operator stand-down order}"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    python3 -c "
import json, sys, os

targets_file = sys.argv[4]
target = sys.argv[1].strip()
reason = sys.argv[2].strip()
timestamp = sys.argv[3]

data = {'targets': {}}
if os.path.exists(targets_file):
    try:
        with open(targets_file) as f:
            loaded = json.load(f)
            if isinstance(loaded, dict) and 'targets' in loaded:
                data = loaded
    except Exception:
        pass

data['targets'][target] = {
    'target': target,
    'reason': reason,
    'timestamp': timestamp
}

with open(targets_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f'Stand-down order recorded: target=\"{target}\", reason=\"{reason}\"')
" "$TARGET" "$REASON" "$TIMESTAMP" "$TARGETS_FILE"
    ;;

  remove|rm|delete)
    TARGET="${2:?Usage: set-stand-down.sh remove <target>}"
    python3 -c "
import json, sys, os

targets_file = sys.argv[2]
target = sys.argv[1].strip()

if not os.path.exists(targets_file):
    print('No active stand-down targets.')
    sys.exit(0)

try:
    with open(targets_file) as f:
        data = json.load(f)
except Exception:
    data = {'targets': {}}

if 'targets' in data and target in data['targets']:
    del data['targets'][target]
    with open(targets_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'Stand-down order removed for target \"{target}\".')
else:
    print(f'Target \"{target}\" was not in active stand-down list.')
" "$TARGET" "$TARGETS_FILE"
    ;;

  clear)
    if [ -f "$TARGETS_FILE" ]; then
      rm -f "$TARGETS_FILE"
      echo "All stand-down orders cleared."
    else
      echo "No active stand-down orders."
    fi
    ;;

  list|status)
    if [ ! -f "$TARGETS_FILE" ] || [ ! -s "$TARGETS_FILE" ]; then
      echo "No active stand-down orders."
    else
      python3 -c "
import json, sys, os
targets_file = sys.argv[1]
try:
    if not os.path.exists(targets_file) or os.path.getsize(targets_file) == 0:
        print('No active stand-down orders.')
        sys.exit(0)
    with open(targets_file) as f:
        data = json.load(f)
    targets = data.get('targets', {})
    if not targets:
        print('No active stand-down orders.')
    else:
        print(f'Active stand-down targets ({len(targets)}):')
        for t, info in targets.items():
            print(f'  - {t}: \"{info.get(\"reason\")}\" (added {info.get(\"timestamp\")})')
except Exception as e:
    print(f'Error reading stand-down targets: {e}')
" "$TARGETS_FILE"
    fi
    ;;

  *)
    echo "Usage: set-stand-down.sh {add|remove|clear|list} [target] [\"reason\"]"
    echo ""
    echo "Commands:"
    echo "  add <target> \"<reason>\"  — Record a stand-down target (branch, PR, path)"
    echo "  remove <target>          — Remove stand-down target"
    echo "  clear                    — Clear all active stand-down targets"
    echo "  list                     — Show all active stand-down targets"
    exit 1
    ;;
esac
