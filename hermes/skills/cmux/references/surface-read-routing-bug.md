# cmux Surface-Read Routing — What the SKILL.md and Cheatsheet Don't Tell You

**Discovered 2026-06-13 on debug socket `/tmp/cmux-debug-may-18.sock`.**
**Status:** Bugs in current cmux CLI / JSON-RPC; the workarounds below are the
reliable way to read a non-focused surface in this build.

## TL;DR

Neither `cmux read-screen --workspace X --surface Y` nor
`surface.read_text {workspace_ref, surface_ref}` reliably returns the target
surface's content. They return whatever is currently focused. To read a
non-focused surface you must **focus it first, then read the focused surface**.

## Bug #1: `cmux read-screen --surface <ref>` — "Surface is not a terminal"

The CLI's `--surface <ref>` form silently fails for many surfaces with:

```
Error: invalid_params: Surface is not a terminal
```

…but the surface IS a terminal (verified via `cmux tree --all` and
`surface.list`). The bug appears to be in the CLI's internal index routing —
it resolves the ref to a wrong internal handle, then the type check rejects
it as "not a terminal".

`cmux read-screen` (with NO `--surface`) on the currently-focused surface
DOES work — that's what the SKILL.md's "Discovery Recipe" implicitly relies
on (it never tells you to read a non-focused surface).

## Bug #2: `surface.read_text` ignores ref params

Raw socket call to `surface.read_text` with `workspace_ref` and `surface_ref`:

```json
{"id":"q","method":"surface.read_text",
 "params":{"workspace_ref":"workspace:4","surface_ref":"surface:7",
           "scrollback":true,"lines":30}}
```

…returns the **focused** surface's content (workspace:17, surface:41 in the
verified case), even though the `result` echoes back the requested
`workspace_ref` and `surface_ref` as if it worked. The `text` field contains
the focused surface's text, not the target.

Same applies to `surface.list {workspace_ref: ...}` — it returns the
focused workspace's data.

## Workaround: focus-then-read (the recipe that actually works)

```bash
SOCKET=$(cmux identify | python3 -c "import json,sys;print(json.load(sys.stdin)['socket_path'])")
# 1. Discover the target surface's UUID via surface.list on the focused workspace
#    (yes, it only returns the focused workspace — use the tree to find the
#    workspace containing the surface you want, then call surface.list while
#    that workspace is focused)

# 2. To get the surface UUID, you need to call surface.list while the right
#    workspace is focused, OR get it from `cmux tree --all` (which prints tty
#    and titles but not the UUID).

# 3. Easiest: surface.list while your target workspace is focused gives
#    you the UUIDs of all surfaces in it. Then:
TARGET_UUID="EAF6539E-B30D-47E3-B351-8D2765A4DD6C"   # ws:4 surface:7
printf '{"id":"q","method":"surface.focus","params":{"surface_id":"%s"}}\n' "$TARGET_UUID" \
  | nc -U -w 3 "$SOCKET" >/dev/null

# 4. Now read the focused surface (no --surface flag needed)
cmux read-screen --scrollback --lines 50
```

The `cmux read-screen` (with no surface flag) always reads the focused
surface, and it actually works there.

## Discovering surface UUIDs

`cmux tree --all` shows `surface:<ref>` and tty/title but **not** the UUID.
To get the UUID you need to either:

1. `cmux surface.list` — but this currently ignores the `workspace_ref`
   param and returns the focused workspace's data. So focus the workspace
   first (`cmux select-workspace --workspace N`), then call
   `cmux surface.list` (it appears `cmux` CLI may not have this verb —
   the JSON-RPC method is `surface.list`).

2. Call `cmux identify --workspace N --surface surface:M` — the
   `caller` and `focused` sections don't include the target's UUID, but
   the `socket_path` is the real one to use.

3. **Most reliable**: focus the workspace, then raw-socket call
   `surface.list` and read the `surfaces[].id` field for the target
   surface's UUID.

## `surface.focus` param shape

`surface.focus` requires `surface_id` (the UUID), **not** `surface_ref` and
**not** the bare integer.

```jsonc
// WRONG (silently errors or no-op):
{"method":"surface.focus","params":{"surface_ref":"surface:7"}}
{"method":"surface.focus","params":{"ref":"surface:7"}}
{"method":"surface.focus","params":{}}

// RIGHT:
{"method":"surface.focus","params":{"surface_id":"EAF6539E-..."}}
```

`pane.focus` and `tab.action` use different param shapes; check
`cmux capabilities` and probe one at a time.

## When `cmux read-screen` is the right call anyway

For the *focused* surface — yes, just use it. The SKILL.md "Discovery
Recipe" is correct for that. The bug only bites you when you need to
read a non-focused surface (e.g., to scan all `w:*` worker workspaces
for state in one script).

## Implications for "is this worker alive?" diagnosis

The cmux API can't give you a passive read of all surfaces. The
practical options are:

1. **Focus each surface in turn, read it, focus the next.** Slow but
   works. ~1s per surface.
2. **Look for churn labels in the tree pane titles** (e.g., "Churned
   for 9m 41s" / "Flibbertigibbeting… 12m 34s"). A pane WITHOUT an
   active time-on-task label is more likely dead/stalled. The titles
   are in `cmux tree --all` output — no read needed.
3. **Check `tail -f /tmp/cmux-debug-may-18.log`** (or whatever the
   current build's log is) for `workspace.gitProbe.apply` and
   `workspace.prRefresh.apply` lines — these prove the surface is
   producing events.

The session-investigation pattern that worked in 2026-06-13:

```bash
# 1. Tree scan — find worker workspaces by name
cmux tree --all | grep "workspace:.* \"w:" | head -20

# 2. For each worker, focus and read focused surface
for w in 6 8 21 16; do
  cmux select-workspace --workspace $w >/dev/null
  # Now the focused surface is the worker's; read it
  cmux read-screen --scrollback --lines 30
done
```

## Filing the upstream bug

The cmux repo is `manaflow-ai/cmux`. Worth filing:

1. `cmux read-screen --surface <ref>` resolves to wrong internal handle,
   errors as "Surface is not a terminal" when the surface is a terminal.
2. `surface.read_text` and `surface.list` ignore `workspace_ref` /
   `surface_ref` params and return focused-surface data.

Until they're fixed, the focus-then-read recipe is the workaround.
