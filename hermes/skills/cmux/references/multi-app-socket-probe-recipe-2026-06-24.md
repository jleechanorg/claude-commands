# Multi-App cmux Socket Probe — Works For ANY Build

**Discovered 2026-06-24** while diagnosing why the every-4h cmux surface report
had been silently skipping ticks. **Supersedes** `socket-discovery-2026-06-21.md`
for the "any build, any app" case.

## TL;DR

`cmux identify` (the canonical resolver in `socket-discovery-2026-06-21.md`)
**also fails** when the CLI itself ships with a stale hardcoded default that
doesn't match the running build. The verified symptom (2026-06-24):

```bash
$ cmux identify
Error: Socket not found at /tmp/cmux-debug-fix-agy-hook-deny.sock
$ ls /tmp/cmux-debug-fix-agy-hook-deny.sock
ls: cannot access '/tmp/cmux-debug-fix-agy-hook-deny.sock': No such file or directory
```

But a different socket DOES exist and respond:

```bash
$ ls $HOME/.local/state/cmux/cmux.sock
$HOME/.local/state/cmux/cmux.sock
$ cmux --socket $HOME/.local/state/cmux/cmux.sock identify
{
  "app_bundle_path": "/Applications/cmux.app",
  ...
}
```

The CLI ignores `CMUX_SOCKET_PATH` and falls back to a hardcoded
build-suffix path baked into its binary. The **only** way to bypass that
default is to pass `--socket <path>` explicitly.

## The reliable recipe — probe every candidate socket

```bash
# Collect ALL candidate sockets across /tmp + /private/tmp + $HOME
declare -a CANDIDATES=()
SOCK_FILE=/tmp/cmux-last-socket-path
if [ -r "$SOCK_FILE" ]; then
  POINTER=$(cat "$SOCK_FILE" 2>/dev/null || true)
  [ -n "$POINTER" ] && [ -S "$POINTER" ] && CANDIDATES+=("$POINTER")
fi
while IFS= read -r s; do
  CANDIDATES+=("$s")
done < <(
  ls -1t /tmp/cmux*.sock /private/tmp/cmux*.sock ~/.local/state/cmux/cmux.sock 2>/dev/null \
    | grep -v "^$SOCK_FILE$" \
    | awk '!seen[$0]++'
)

# Probe each candidate via `cmux --socket <path> identify` with a 5s timeout.
# Pick the first one that returns valid JSON containing socket_path / version / pid.
SOCK=""
for cand in "${CANDIDATES[@]}"; do
  [ -S "$cand" ] || continue
  probe=$(timeout 5 cmux --socket "$cand" identify 2>/dev/null || true)
  if echo "$probe" | python3 -c '
import json,sys
d = json.loads(sys.stdin.read() or "{}")
assert isinstance(d, dict)
assert d.get("socket_path") or d.get("version") or d.get("pid")
' 2>/dev/null; then
    SOCK="$cand"
    break
  fi
done

if [ -z "$SOCK" ]; then
  echo "No live cmux socket across ${#CANDIDATES[@]} candidates" >&2
  exit 1
fi

export CMUX_SOCKET_PATH="$SOCK"
CMUX="cmux --socket $SOCK"  # pass --socket explicitly on every cmux call
```

This works for:
- **Multiple cmux app builds** running concurrently (DEV may-18 + production cmux.app)
- **Stale build-suffix sockets** that the CLI's hardcoded default points at
- **Stale `/tmp/cmux-last-socket-path`** pointers
- **Brand new installs** where the pointer file doesn't exist yet

## Why the pointer-file approach failed

The original socket-discovery recipe relied on `/tmp/cmux-last-socket-path`
being a recent, accurate pointer. Two ways it goes stale:

1. **CMux app updates** — the build-suffix in the socket path changes
   (e.g. `cmux-debug-may-18` → `cmux-debug-fix-agy-hook-deny`), but the
   pointer file still holds the OLD path. The new app listens on a path
   the script doesn't know to look for.
2. **The CLI's hardcoded default** — verified 2026-06-24, the `cmux` binary
   itself ignores `CMUX_SOCKET_PATH` if a default is compiled in. Only
   `--socket <path>` (verified working) overrides it.

## Pitfall — 5s probe timeout per candidate

Under launchd (non-interactive env), the FIRST `cmux` invocation in a shell
takes ~5-10s due to dyld cache + dynamic loader warm-up. With 4 candidates
this can add 30-40s to the tick. If you have many sockets to probe:

- Run `cmux identify` (no --socket) ONCE early in the script just to "warm up"
  the dyld cache; discard the output. Subsequent `--socket` calls will be <100ms.
- Or bump the per-candidate timeout to 10s.

For the every-4h report the slow path is fine (4h cadence absorbs 30s easily).

## Tested-cmux-versions

| App | Socket | Works with `--socket` |
|-----|--------|-----------------------|
| `/Applications/cmux.app` (production) | `$HOME/.local/state/cmux/cmux.sock` | ✅ 2026-06-24 |
| `/Applications/cmux DEV may-18.app` | `/private/tmp/cmux-debug-may-18.sock` | ✅ 2026-06-22 |
| Older build `cmux-debug-fix-agy-hook-deny` | `/tmp/cmux-debug-fix-agy-hook-deny.sock` | (stale; not running) |

## See also

- `socket-discovery-2026-06-21.md` — original recipe, `cmux identify` as canonical resolver.
  Still useful for ONE-shot interactive scripts; use this multi-app probe recipe
  for launchd jobs and any unattended run.
- `cli-cheatsheet.md` — `--socket` flag documentation
