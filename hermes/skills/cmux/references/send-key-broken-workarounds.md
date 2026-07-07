# cmux `send-key` — historical breakage (2026-06-09) + current verified behavior (2026-06-23)

**Status as of 2026-06-23:** `cmux send-key` works for at least `Return`, `enter`, `escape`,
`ctrl+u`, `ctrl+c`, and other common keys on the `/tmp/cmux-debug-may-18.sock` socket
(verified during the PR #7848 fastembed steering flow). The cheatsheet at
`references/cli-cheatsheet.md` documents the current verified behavior — use that as
the source of truth, NOT this historical document. **The workarounds below are
preserved as a fallback only.**

## Historical symptom (2026-06-09, now resolved)
`cmux send-key` rejected every key name with `invalid_params: Unknown key` on the
socket at `/tmp/cmux-debug-may-18.sock` (the active cmux debug socket on 2026-06-09).

```bash
$ for k in Backspace escape Escape Tab Enter esc ctrl+c ctrl+u; do
    echo "=== $k ==="
    cmux send-key --workspace workspace:16 --pane pane:90 "$k" 2>&1
  done
=== Backspace ===   Error: invalid_params: Unknown key
=== escape ===      Error: invalid_params: Unknown key
=== Escape ===      Error: invalid_params: Unknown key
=== Tab ===         Error: invalid_params: Unknown key
=== Enter ===       Error: invalid_params: Unknown key
=== esc ===         Error: invalid_params: Unknown key
=== ctrl+c ===      (would also fail)
=== ctrl+u ===      (would also fail)
```

## Diagnosis
The CLI help text says: `Usage: cmux send-key [flags] [--] <key>`. The actual
parser is stricter than the help suggests — it doesn't recognize the
canonical key names that have worked on prior cmux builds.

## Workarounds (in order of preference)

### 1. Use the canonical Python wrapper (best)
```python
from cmux_client import send_and_submit
result = send_and_submit("workspace:16", "surface:140", "your prompt here")
# result["proof"] is a churn/spinner screenshot you must paste in your reply
```
The wrapper is at `~/.hermes_prod/skills/cmux/scripts/cmux_client.py::send_and_submit()`.

### 2. Send a literal CR (0x0d) via `cmux send` to submit a staged paste
The Claude Code TUI accepts pasted text as a multi-line paste with no automatic
submit. To submit a staged paste, append a CR:
```bash
cmux send --workspace workspace:16 --pane pane:90 "$(printf '\r')"
```
The TUI's `❯ ` prompt will clear and the agent will start processing the
paste as a single user turn. The agent's first response confirms receipt.

### 3. Clear a half-typed input with literal CTRL-U (0x15)
```bash
cmux send --workspace workspace:16 --pane pane:90 "$(printf '\x15')"
```
The TUI confirms with `Ctrl+Y to paste deleted text` — the line buffer was killed.

### 4. Never call `send-key` on broken CLI builds
Treat the entire `send-key` subcommand as unreliable. If you find yourself
needing a key press and the Python wrapper is unavailable, use workaround #2
or #3 above. Document the broken state in your reply so the user knows.

## Bonus: `cmux send`/`read-screen` without explicit surface ref routes to focused surface
Same session, same build:
```bash
$ cmux send --workspace 16 "test ping from hermes 1"
OK surface:52 workspace:24   # ← focused surface in workspace:24, not target!
```
**Fix:** always pass `--pane` (preferred) or both `--workspace` AND `--surface`
with full refs:
```bash
cmux send --workspace workspace:16 --pane pane:90 "<message>"
# Returns: OK surface:140 workspace:16   ← routed correctly
```

**Note (2026-06-23):** when targeting a Claude Code surface (TUI), the modern
preferred path is `cmux send --workspace <w> --surface <s> "text"` followed by
`cmux send-key --workspace <w> --surface <s> Return` (or `enter`). The bare
`--pane` route is for terminal-only surfaces without a known surface ref; for
Claude Code the `--surface` route has been verified working with `Return`
explicit (not `Enter`) to handle the multi-line paste widget cleanly.
Verified pattern from the 2026-06-23 PR #7848 fastembed followup steering.

## When to investigate vs work around
- If a single socket has the broken `send-key` but other sockets (try
  `/private/tmp/cmux-debug-appclick.sock`, `/private/tmp/cmux.sock`) work, the
  issue is the socket build, not cmux. Reload the cmux app to refresh the
  active socket.
- If ALL sockets reject `send-key`, the CLI build itself is broken. Patch
  the cmux binary or fall back to the Python wrapper. Document in
  `skills/cmux/references/known-bad-builds.md`.

## Related
- `~/.hermes_prod/skills/cmux-send-submit/SKILL.md` — the canonical
  send-and-submit-with-proof pattern
- `~/.hermes_prod/skills/cmux/SKILL.md` — main cmux skill (already patches
  include the workarounds above)
