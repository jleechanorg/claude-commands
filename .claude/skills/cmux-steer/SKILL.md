---
name: cmux-steer
description: Resolve, inspect, and safely steer named cmux workspaces, tabs, and surfaces.
---

> **Terminal-reading rule (canonical):** before any classification, assessment, or steer of a
> cmux surface, read the surface's FULL available history (~10k words when possible;
> `cmux capture-pane --scrollback --lines 1500`), then the last ~15 lines for current state.
> Never decide from a short tail. Canonical text: `~/.codex/AGENTS.md` section
> "Reading a cmux terminal before deciding (full-buffer rule)".

## Headless only (operator rule 2026-10-18)

This section is the single owner of the rule; other cmux skills point here. **Measured** in `/tmp/spicy-search/cmux/focus-test.md` (selection tracked by the `[selected]` marker in `cmux workspace list`).

**Measured to NOT change the selected workspace — all safe to use:**
- **Reads:** `cmux capture-pane --workspace <ws> --surface <surface-uuid-or-ref> --scrollback --lines <n>` and `cmux read-screen --scrollback --lines <n>`.
- **Steers:** `cmux send "<text>"` + `cmux send-key enter`, and the raw socket `surface.send_text` call (type + Enter in one call; the trailing `\n` in `text` is Enter; works cross-workspace; resolve the socket from `$CMUX_SOCKET_PATH`, default below; surface UUIDs come from `cmux surface list`):

  ```bash
  SOCK="${CMUX_SOCKET_PATH:-/Users/jleechan/.local/state/cmux/cmux.sock}"
  printf '{"method":"surface.send_text","params":{"surface_id":"<SURFACE-UUID>","text":"<message>\\n"}}\n' | nc -U -w 3 "$SOCK"
  # -> {"ok":true,...,"queued":false|true}
  ```

- **Creates:** `cmux new-surface ... --focus false` / `cmux new-workspace ... --focus false` (**always pass `--focus false`**).
- **Closes:** `cmux close-surface` (run-2 measured: no selection change).

**The only thing that disturbed the operator's view:** creating or closing **workspaces/surfaces** on the live desktop — the focus test's `cmux workspace close …` teardown switched the operator's selected workspace twice. **Do NOT create or close cmux workspaces/surfaces on the operator's live desktop unless the operator says yes first.**

**Never** use explicit selection/focus commands (`select-workspace`, `workspace.select`, `workspace-action --action focus`, `focus-window`, `focus-surface`, `surface.focus`) — they are never needed for a read/steer and only move the operator's view.

- **Proof of submission:** a later `capture-pane` showing the text accepted (a "Steering:" queued line, or new activity/spinner), never the socket `ok` alone.

## ⚠️ Submit Discipline (MANDATORY — read this before every cmux steer)

The socket `text` must end in `\n` (Enter), or the message sits in the input buffer
without ever reaching the agent (verified 2026-07-16: user flagged "you always forget
to send"). The **3-step ritual** below is a hard contract for every send to a cmux surface.

## ⚠️ SUPERSEDED — Use `cmux` CLI, not raw socket protocol (for name → surface resolution)

The raw `nc -U $SOCK` examples further down still work for low-level access,
but they have a **name → surface resolution gap** that has caused repeated
failures ("why do you always get confused when I name a surface"). The
canonical recipe is the `cmux` CLI, which exposes workspace/surface/tab refs
directly.

**Always start here when the user names a surface, tab, or workspace:**

```bash
# 1. MY workspace = caller.workspace_ref, falling back to focused.
#    `caller` is populated only when this command runs inside cmux itself;
#    from a standalone terminal (and from most skill invocations) it is null,
#    so the defensive form below falls back to the focused workspace.
WS=$(cmux identify --json | python3 -c '
import sys, json
d = json.load(sys.stdin)
c = d.get("caller") or {}
print(c.get("workspace_ref") or d.get("focused", {}).get("workspace_ref"))
')

# 2. Every pane + tab by name; ◀ here = caller surface, ◀ active = focus.
#    Do NOT filter the output — sibling tabs and the ◀ markers are the signal.
cmux tree --all --workspace "$WS"

# 3. Read the target headlessly (see "Headless only"); verify identity by CONTENT:
#      cmux capture-pane --workspace "$WS" --surface <uuid> --scrollback --lines 1500
#    If the read cannot be trusted, read the transcript/STATE.md/checkpoint files
#    (~/.claude/projects/**.jsonl, roadmap STATE files, git worktrees) instead.
```

### Three anti-patterns this skill now warns against

- **Global name search** — `cmux list-pane-surfaces | grep <name>` matches a
  same-named tab in another workspace and you steer the wrong agent.
- **grep-filtering the tree** — `cmux tree --all | grep <name>` hides sibling
  tabs and the `◀ here` / `◀ active` markers you need to disambiguate.
- **`list-pane-surfaces` defaults** — defaults to ONE pane and omits tabs in
  other panes; use `cmux tree --all --workspace "$WS"` for the full picture.

The raw `nc -U $SOCK` blocks below remain useful for low-level debugging
(`system.tree`, `system.identify`, custom JSON-RPC methods).

### The 3-step ritual

```bash
# STEP 1 — Type + Enter in one call (trailing \n). ok:true proves socket acceptance, NOT submission.
printf '{"method":"surface.send_text","params":{"surface_id":"<SURFACE-UUID>","text":"your message\\n"}}\n' | nc -U -w 3 "$SOCK"

# STEP 2 — Wait 5-15 seconds for the agent to start processing.
sleep 8

# STEP 3 — Verify with churning label (THE ONLY definitive proof).
cmux capture-pane --workspace workspace:N --surface <SURFACE-UUID> --lines 25
# Look for one of:
#   - "Working (Xs • esc to interrupt)"
#   - "Forming… (Xs · thinking)"
#   - "Precipitating… (Xs · ↓ tokens)"
#   - "Brewed / Churned / Cooked for Xm"
# If you see ANY active churning label → SUBMITTED.
# If the text is still sitting at the ❯ prompt → NOT submitted; send a bare "\n" via the same socket call.
# If "Stopped" / "Done" / nothing → no churn, investigate.
```

### ⚠️ Output Contract — typed text + terminal response (MANDATORY)

Every reply that reports a steer action MUST include, in the same reply:

1. **The exact text that was typed** — verbatim copy of the `text` sent via `surface.send_text`.
2. **The cmux terminal response** — verbatim transcript of what `cmux capture-pane`
   returned AFTER the send settle window (typically 5-15s). Specifically, the agent's first action after absorption.
3. **Submission status** — explicit verdict: "submitted (churning label X)",
   "not submitted (text still at ❯ prompt)", or "blocked (no churn, retried N times)".

**Treat as not working until we see a response.** A reply that does NOT include
both the typed text AND a terminal response is invalid evidence that the
steer landed. The operator cannot distinguish a successful send from a failed
send that left text in the input buffer.

Canonical contract + echo-back template: `~/.hermes/skills/cmux/references/output-contract-mandatory.md`.

### ⚠️ LLM-Provenance Caveat (MANDATORY footer)

Every reply that quotes cmux output, terminal text, or agent actions produced
by another LLM (the worker agent OR the assistant's own synthesis of agent
output) MUST end with this verbatim footer:

> *This was generated from another LLM and not the actual user, so feel free
> to push back if you disagree and we can discuss.*

Full caveat rules + scope: `~/.hermes/skills/cmux/references/output-contract-mandatory.md` § "LLM-Provenance Caveat".

### Echo-back proof (MANDATORY)

Every cmux steering action MUST be followed by an **echo-back proof** in the same
turn or the immediate next turn to your operator (Slack thread, terminal reply,
or whichever channel triggered the steer). The proof MUST follow the template
in `~/.hermes/skills/cmux/references/output-contract-mandatory.md` and include
the typed text + terminal response + submission status, not just the
churning label.

> ◀ sent to surface:55 (LEFT/claudec) at <HH:MM:SS PT> — typed: "<first 80 chars>";
> response: "<first 80 chars of the churning label or first agent line>"; status:
> submitted (churning label "Forming… 9s · ↓ 4.9k tokens").

**Banned** (these are the failure modes the user keeps flagging):
- "I sent the message" (no Enter proof)
- "The agent should have received it" (no churning label)
- A `surface.send_text` whose `text` lacks the trailing `\n`
- Focusing or selecting a surface before sending (never needed; the socket call works cross-workspace)

### Worktree-pointer strategy for long briefs

For task briefs >200 chars (e.g. orchestrating iOS app pivot, multi-PR review),
do NOT paste the full text into the input. Write the brief to a file in the
agent's cwd (e.g. `.cmux-<task>-brief.md`) and send a 1-2 line pointer. This
avoids the autocompleter contamination pitfall where shell-style tokens inside
long text trigger tab completion mid-stream.

### Canonical reference

Full recipe + edge cases + the 2026-06-25 worked example live at:
`~/.hermes/skills/cmux/references/send-submit-proof-2026-06-25.md`

This rule was added 2026-07-16 after the fable iOS pivot bootstrap surfaced
"you always forget to send" / "make sure you press submit and the work starts
on the cmux input" (Slack ts 1784185650.528089). Apply it uniformly to every
cmux-touching skill.

# cmux-steer — Control another cmux terminal tab via the Unix socket

**Usage**: Read and follow this skill directly; no `/cmux-steer` slash command is defined.

**Purpose**: Read and steer another agent's terminal pane (e.g. a coding agent)
from within cmux, without disrupting the user's active workspace navigation.

---

## Socket path

```bash
ls /tmp/cmux*.sock
# Tagged debug build: /tmp/cmux-debug-<tag>.sock
# Untagged debug:     /tmp/cmux-debug.sock
# Release:            /tmp/cmux.sock
SOCK="/tmp/cmux-debug-appclick.sock"  # update to match your build tag
```

## Rule 1: Always find workspace by NAME, not index

The user can switch workspaces at any time, shifting surface indices. **Never
hardcode an index.** Always look up by the workspace's display name:

```bash
# List all workspaces with names
printf "list_workspaces\n" | nc -U $SOCK
# Example output:
#   0: D267DC10-... cmux: ubuntu
# * 1: 9075D919-... exp: statusline   ← user is here; doesn't matter
#   2: 258EB4B4-... o: mctrl

# Find target workspace UUID by name
WS_UUID=$(printf "list_workspaces\n" | nc -U $SOCK \
  | grep "cmux: ubuntu" | grep -oE '[A-F0-9-]{36}')

# List surfaces in that workspace
printf "list_surfaces $WS_UUID\n" | nc -U $SOCK
# Output:
#   * 0: 87DB76A9-...   supervisor (cmux)
#     1: F05FCE84-...   cmux_coder

# Extract coder surface UUID by label (never by index — indices shift)
CODER_UUID=$(printf "list_surfaces $WS_UUID\n" | nc -U $SOCK \
  | grep "cmux_coder" | grep -oE '[A-F0-9-]{36}')
```

## Rule 2: Use JSON API for headless cross-workspace sends

The plain-text `send_surface` command FAILS cross-workspace. Always use the JSON API:

| Method | Cross-workspace? | Notes |
|---|---|---|
| `surface.send_text` (JSON) | ✅ always works | Include `\n` in text for enter |
| `cmux capture-pane` | ✅ always works | Headless read; the only read method |

## Sending text (headless, cross-workspace)

```bash
# Single command: type + enter (append \n to submit)
printf '{"method":"surface.send_text","params":{"surface_id":"'"$CODER_UUID"'","text":"your instruction here\\n"}}\n' | nc -U $SOCK
```

This works from any workspace without switching focus. The `\n` at end acts as Enter.

## Checking if idle

```bash
# Send a harmless probe — if queued=false and ok=true, surface accepted input
result=$(printf '{"method":"surface.send_text","params":{"surface_id":"'"$CODER_UUID"'","text":""}}\n' | nc -U $SOCK)
# Check result.ok and result.queued
```

## Creating workspaces and surfaces

```bash
cmux new-workspace --focus false --name "my-workspace"   # prints the new workspace ref
cmux new-surface --focus false --workspace <ws> --type terminal   # add a second tab
```

## Special keys

Use `surface.send_text` with the control character in `text` (JSON escapes: `\u0003` ctrl-c, `\u0004` ctrl-d, `\t` tab, `\u001b` escape, `\n` enter):
```bash
printf '{"method":"surface.send_text","params":{"surface_id":"'"$CODER_UUID"'","text":"\\u0003"}}\n' | nc -U -w 3 "$SOCK"
```

## Reading a pane's screen

Read any workspace headlessly with `capture-pane`:

```bash
cmux capture-pane --workspace "$WS_UUID" --surface "$CODER_UUID" --scrollback --lines 1500
```

If the read cannot be trusted, infer state from the filesystem:
```bash
cd /path/to/project && git log --oneline -5
ls -lt src/   # recently modified files
```

## Full headless example

```bash
SOCK="/tmp/cmux-debug-appclick.sock"

# 1. Find coder surface by workspace name
WS_UUID=$(printf "list_workspaces\n" | nc -U $SOCK \
  | grep "cmux: ubuntu" | grep -oE '[A-F0-9-]{36}')
CODER_UUID=$(printf "list_surfaces $WS_UUID\n" | nc -U $SOCK \
  | grep "cmux_coder" | grep -oE '[A-F0-9-]{36}')

# 2. Send task headlessly (no workspace switch needed)
printf '{"method":"surface.send_text","params":{"surface_id":"'"$CODER_UUID"'","text":"cargo build && cargo test\\n"}}\n' | nc -U $SOCK

# 3. Monitor progress via capture-pane
sleep 30
cmux capture-pane --workspace "$WS_UUID" --surface "$CODER_UUID" --lines 25
```

## Creating a fresh workspace with two tabs

```bash
cmux new-workspace --focus false --name "test: a/b"
cmux new-surface --focus false --workspace <ws> --type terminal
# Resolve both surface UUIDs with `cmux surface list`, then send to each via surface.send_text.
```

## Rules summary

1. **Never select or focus anything** — see "Headless only".
2. **Find workspace by NAME** (`list_workspaces` → grep name → get UUID).
3. **Use JSON API for sends** — `surface.send_text` works headlessly cross-workspace.
4. **Append `\n` to text** — acts as Enter key submission.
5. **Read with `cmux capture-pane`** — headless, any workspace.
6. **Create with `--focus false`** — `cmux new-workspace` / `cmux new-surface` for multi-tab setups.
