# cmux Workspace Routing — `select-workspace` Index-vs-Ref Trap

**Discovered 2026-06-13 on debug socket `/tmp/cmux-debug-may-18.sock`.**
**Status:** The bare-integer-vs-ref ambiguity is in current cmux CLI behavior.
The recipes below are the workarounds.

## TL;DR

`cmux select-workspace --workspace 5` does **not** focus `workspace:5`. It treats
`5` as an **index** (positional, sorted by tab order — NOT by `ref` number).
Since the index list is not sorted by `ref`, `index 5` can map to any workspace,
and the CLI silently returns `OK workspace:<X>` for whichever workspace index 5
actually points to. This is a real footgun and a silent one at that.

**Always use the explicit ref form** `--workspace workspace:5` when you mean a
specific workspace. If you only have the integer from `cmux list-workspaces`,
run `cmux list-workspaces --id-format both` first and use the ref, not the
integer.

## What went wrong (the actual 2026-06-13 case)

The user asked about the "bq logging" workspace. `cmux list-workspaces` showed:

```
workspace:1  cost
workspace:20  disk_magician
workspace:2  lvl: refactor
workspace:4  ao
workspace:5  bq logging            ← this is what we wanted
workspace:12  ---- roadmap
...
```

The natural read of "5" was the `5` after the colon in `workspace:5`. But
`cmux select-workspace --workspace 5` returned:

```
OK workspace:12
```

…because index 5 in tab order is `workspace:12 ---- roadmap`, not
`workspace:5 bq logging`. The focus silently jumped to the wrong workspace, and
`cmux identify` then returned `workspace_ref: workspace:12`. Reading the screen
on the focused surface showed the roadmap shell, not the bq-logging worker.

The user noticed and would have been rightly confused — "look at the bq logging
workspace" would have returned a roadmap shell transcript.

## Why this is silent

The CLI does NOT error. It just resolves the integer to the workspace at that
positional index (sorted by tab order, which is the order workspaces were
created / last focused, not by `ref` number) and returns
`OK workspace:<actual_ref>`. The string `OK workspace:12` looks like a success
ack, not a misroute.

## The reliable recipe — find a workspace by partial title, every time

```bash
# 1. Get the full ref list with current_directory (lets you sanity-check)
cmux list-workspaces --id-format both
# Or for compact ref + index + title + cwd, raw socket:
printf '{"id":"q","method":"workspace.list","params":{}}\n' \
  | nc -U -w 3 "$(cmux identify | python3 -c 'import json,sys;print(json.load(sys.stdin)["socket_path"])')" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
for w in d['result']['workspaces']:
    print(f\"  ref={w['ref']:14}  index={w['index']:3}  title={w['title']!r:30}  cwd={w.get('current_directory')}\")
"
```

**Cross-check `ref` against `index` and `title`**. The `ref` is stable; the
`index` is positional and changes as you reorder / close / open workspaces.

## 2. Use the ref form, never the bare integer

```bash
# WRONG — silently misroutes to whichever workspace is at index 5 today:
cmux select-workspace --workspace 5

# RIGHT — unambiguous:
cmux select-workspace --workspace workspace:5
```

For UUIDs, `cmux list-workspaces --id-format both` shows both; the UUID form is
also stable.

## 3. Verify the focus actually landed

```bash
cmux identify | jq '.focused.workspace_ref, .focused.surface_ref'
# Should print the workspace:ref and surface:ref you intended
```

If it doesn't match, re-check step 1 — the index may have shifted.

## 4. Read the focused surface

```bash
cmux read-screen --scrollback --lines 200
# (no --workspace / --surface flag — read-screen always reads the focused surface)
```

This works for the focused surface. For **non-focused** surfaces, see
`references/surface-read-routing-bug.md` — `read-screen --workspace X --surface Y`
is broken in the current build, and you must focus-then-read.

## 5. (Optional) Find the right surface in the workspace

```bash
cmux list-pane-surfaces --workspace workspace:5
# Lists the surfaces in the focused pane of that workspace.
# For other panes, pass --pane <ref>.
```

Then `cmux identify --workspace workspace:5 --surface surface:N` confirms
the surface details (workspace_ref, surface_ref, surface_type, tty).

## Why "always use refs" is the rule

The cmux CLI accepts three forms for `--workspace`:

- `workspace:5` (ref) — **stable, unambiguous, recommended**
- `5` (integer index) — positional, changes as workspaces are added/removed
- UUID (e.g. `F64513A5-35CC-4C2A-95D0-7FD749200B77`) — stable, unambiguous, verbose

The positional form is convenient in scripts that have just enumerated
`cmux list-workspaces` with `--json` and want to select "the third one", but it
breaks down for any flow that involves a known workspace by name/title (the
common gateway case). Refs are stable across reorder, close, and reopen.

## Implications for gateway scripts

Any code that does `cmux select-workspace --workspace $N` where `$N` comes from
a user message, a list-workspace parse, or a config file should be rewritten
to:

1. Resolve the user-named workspace via `list-workspaces --id-format both`
2. Use the `workspace:N` ref form, not the bare integer
3. Verify with `cmux identify` after focus

This is also the right pattern for `cmux send --workspace N --surface M`,
`cmux read-screen --workspace N --surface M`, `cmux notify --workspace N`,
etc. — the integer-vs-ref ambiguity applies to every flag that takes a
workspace handle.

## Filing the upstream bug

The cmux repo is `manaflow-ai/cmux`. Worth filing:

1. `select-workspace --workspace 5` should prefer the ref form when an
   integer matches a known `ref` (workspace:5), and fall back to index only
   if no ref matches. Or, simpler: warn when the integer matches a ref
   ("workspace:5" exists; did you mean `--workspace workspace:5`?).
2. Document the ref-vs-index behavior in `cmux docs api`.

Until the CLI is fixed, **never use the bare integer for `select-workspace` in
scripts that reference a specific workspace** — always resolve to the ref
first.
