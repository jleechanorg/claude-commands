# cmux Socket Discovery — Default `$CMUX_SOCKET_PATH` Often Wrong

**Discovered 2026-06-21 on debug socket `/tmp/cmux-debug-may-18.sock`.**
**Status:** A real recurring footgun — the documented default is a placeholder,
not a real path, and the real path has a build-date suffix that changes per install.

## TL;DR

`CMUX_SOCKET_PATH` (or the implicit default `/tmp/cmux.sock`) is **not** where
the cmux socket actually lives. The real socket is at a build-date-suffixed
path like `/tmp/cmux-debug-may-18.sock` or `/private/tmp/cmux-debug-may-18.sock`
on macOS. The `cmux` CLI figures this out automatically, but any
**raw-socket** code (Python `socket.AF_UNIX`, `nc -U`, etc.) and any
**scripts that set `CMUX_SOCKET_PATH` explicitly** will silently fail with
"connection refused" or "Socket not found" if they use the default.

## The reliable recipe — find the real socket, every time

```bash
# 1. Let `cmux` CLI tell you the real socket
cmux identify | python3 -c "import json,sys; print(json.load(sys.stdin)['socket_path'])"
# Returns something like "/private/tmp/cmux-debug-may-18.sock"

# 2. Use the resolved path for raw-socket calls
SOCKET=$(cmux identify | python3 -c "import json,sys; print(json.load(sys.stdin)['socket_path'])")
printf '{"id":"q","method":"workspace.list","params":{}}\n' | nc -U -w 3 "$SOCKET"

# 3. For Python clients, set CMUX_SOCKET_PATH to the resolved path BEFORE import
export CMUX_SOCKET_PATH=$(cmux identify | python3 -c "import json,sys; print(json.load(sys.stdin)['socket_path'])")
```

## Why this happens

- The cmux app embeds its debug socket path with a build-date suffix
  (`cmux-debug-may-18.sock`, `cmux-debug-fix-agy-hook-deny.sock`, etc.).
- The documented default `CMUX_SOCKET_PATH` is a **placeholder**
  (`/tmp/cmux.sock`) that almost never matches the real path.
- The `cmux` CLI itself reads the actual path from the app at startup and
  hides this from you — so all your raw-socket / Python code silently
  breaks unless you resolve the real path first.

## Diagnosis recipe (run in this order)

```bash
# 1. Try the default — almost always fails first time
[ -S "${CMUX_SOCKET_PATH:-/tmp/cmux.sock}" ] && echo "default socket present" || echo "default socket MISSING"
# Typical output: "default socket MISSING"

# 2. List the real sockets
ls -1 /tmp/cmux*.sock /private/tmp/cmux*.sock 2>/dev/null
# Typical output:
#   /private/tmp/cmux-debug-may-18.sock
#   /tmp/cmux-debug-may-18.sock
# (the same socket may appear in both /tmp and /private/tmp — both are valid)

# 3. Resolve via `cmux identify` (canonical)
cmux identify | python3 -c "import json,sys; d=json.load(sys.stdin); print('socket_path:', d['socket_path']); print('caller:', d.get('caller'))"

# 4. Verify the resolved path works
SOCKET=$(cmux identify | python3 -c "import json,sys; print(json.load(sys.stdin)['socket_path'])")
[ -S "$SOCKET" ] && echo "real socket present: $SOCKET" || echo "real socket MISSING: $SOCKET"
```

## Implications for gateway scripts

Any script that does `nc -U "$CMUX_SOCKET_PATH"` or
`socket.connect(os.environ["CMUX_SOCKET_PATH"])` will fail silently on a
fresh setup. Rewrite to:

1. Resolve the real path via `cmux identify` first.
2. Use the resolved path for all raw-socket calls in the same shell.
3. Cache it in a variable, not the env, to avoid surprises.

This also applies to the `cmux-send-submit` skill's `send_and_submit()`
helper (when it's built) — it should resolve the socket on first call and
cache the result.

## Related references

- `references/workspace-routing-trap.md` — ref-vs-index for `select-workspace`
- `references/surface-read-routing-bug.md` — non-focused surface read pitfalls
- `references/screencapture-failure-2026-06-09.md` — TCC blocker for visual capture
