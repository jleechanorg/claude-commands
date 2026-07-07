---
name: cmux
description: "Control cmux terminal multiplexer via its Unix socket API. Use when needing to: (1) List, create, select, or close workspaces; (2) Split panes and manage surfaces; (3) Send text or key presses to terminals; (4) Read terminal screen text from a surface; (5) Create notifications; (6) Set sidebar status, progress bars, or log entries; (7) Query system state. Requires cmux CLI on PATH or Unix socket at /tmp/cmux.sock (overridable via CMUX_SOCKET_PATH)."
---

# cmux

Control cmux terminal multiplexer programmatically via its Unix socket API or CLI.

**Skill last updated:** 2026-06-26 — added two new launchd-scripting pitfalls: (1) `--socket` is a GLOBAL flag (must come right after `cmux`, not after the subcommand — putting it after `cmux tree` errors with `tree: unknown flag --socket`), and (2) `CMUX_SOCKET_PATH` env var is silently IGNORED by the cmux CLI in launchd-style env without an interactive shell context (CLI falls back to baked-in stale default `/tmp/cmux-debug-fix-agy-hook-deny.sock`). Verified by fixing `scripts/cmux-surface-report-4h.sh` false-positive "RPC wedged" skip alert at 2026-06-26T00:03:51Z. See new "Sub-pattern: cmux CLI flag-order gotchas in launchd scripts" below.
For the canonical command list, see `references/cli-cheatsheet.md` and the upstream contract at
<https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/cli-contract.md>. When in doubt, run
`cmux docs api` or `cmux <command> --help` to confirm.

## ⚠️ Visual Screenshot of cmux Window — macOS TCC Blocker

**The cmux window is not capturable by default.** cmux is built on Electron and marks its window as `kCGWindowSharingState=0` (non-shareable). `screencapture -l <wid>` returns "could not create image from window", and `SCScreenshotManager.captureImage` (ScreenCaptureKit) returns `Error -3801 "The user declined TCCs for application, window, display capture"` because the calling process does not have Screen Recording permission.

**When the user asks for "a screenshot of the message received" or "show me the cmux window":** try cmux's own APIs FIRST (see "When the user asks for visual proof" sub-pattern below) before falling through to macOS screencapture. If those fail, the substitute proof is `cmux capture-pane --scrollback --lines N`, which reads the terminal text via the cmux socket API and bypasses macOS TCC entirely.

**The "Terminal" in "Screen Recording → Terminal" is the WRONG fix for hermes-gateway-driven captures.** macOS TCC grants Screen Recording to a specific process, not to a logical concept like "the terminal". If the capture call originates from a script running under `hermes gateway` (e.g. Python 3.14 from Homebrew), the **caller** is `Python.framework/Versions/3.14/.../Python.app` — granting permission to Terminal.app or iTerm.app will NOT let hermes-gateway-driven captures work. The fix is: System Settings → Privacy & Security → Screen Recording → add the path to the binary that actually calls `screencapture` / `peekaboo image`. For hermes-driven sessions, that's `/opt/homebrew/Cellar/python@3.14/3.14.4/Frameworks/Python.framework/Versions/3.14/Resources/Python.app` (or whatever Python your hermes gateway runs under). After granting, **relaunch the caller process** — TCC grants do not apply to already-running processes.

**Pitfall — `tccutil reset ScreenCapture` alone is NOT enough.** `tccutil reset ScreenCapture` clears the existing grant, but the next call from a process that already tried to capture will still fail (the running process already saw the denial; the reset only affects the NEXT registration). To get the new permission to take effect, the calling process must be relaunched. For hermes gateway, that means killing + relaunching the session, which kills the agent that's trying to capture. **Plan accordingly**: deliver the text-based substitute proof, and offer the user a one-time manual fix that takes effect on the NEXT capture.

**Diagnosis recipe (run in this order)**:
```bash
# 1. Find the cmux window id + sharing state — try swift first
swift -e 'import Cocoa; let wl = CGWindowListCopyWindowInfo([.optionOnScreenOnly], kCGNullWindowID) as? [[String:Any]] ?? []; for w in wl { if (w["kCGWindowOwnerName"] as? String ?? "").lowercased().contains("cmux") { let s = w["kCGWindowSharingState"] as? Int ?? -1; print("wid=\(w["kCGWindowNumber"] ?? 0) sharing=\(s) bounds=\(w["kCGWindowBounds"] ?? [:])") } }'
# Expect: sharing=0 (non-shareable) for the main content window

# 2. Try screencapture
screencapture -x -l <wid> /tmp/test.png
# Expect: "could not create image from window"

# 3. Fall back to cmux capture-pane (always works, no TCC)
cmux capture-pane --workspace <w> --surface <s> --scrollback --lines 30
```

**No-swift fallback (added 2026-06-23):** When the parent shell has no swift (e.g. a non-dev hermes process), use the ctypes + CoreGraphics + Foundation + CoreFoundation recipe to enumerate windows. See `references/macos-window-enumeration-ctypes.md` for the full Python recipe and the AppleScript `count`-on-CFArray pitfall that rules out osascript.

**Reply shape when TCC blocks screencapture**:
1. State the blocker explicitly (don't hand-wave — name the TCC error AND identify the calling process)
2. Show the captured `cmux capture-pane` output as proof substitute
3. Offer the one-time manual fix: name the **caller's** binary path (not "Terminal"), say to grant Screen Recording to that, then relaunch
4. Do NOT claim "screenshot delivered"

**Bug-ref:** 2026-06-19 — `workspace:16 surface:23 "mobile load"` (mobile slow-load investigation). User asked "press send and show me screenshot of msg received." After 4 capture attempts (screencapture -l, -R with bounds, -D with display id, ScreenCaptureKit via swift), confirmed `kCGWindowSharingState=0` for the cmux window. Used `cmux capture-pane --scrollback` as the substitute proof and the user accepted the result. The agent was successfully driven and produced a full root-cause analysis (40.8s slow-load traced to autoscaling queue behind LLM turns pegging 4 vCPUs, fix: lower dev `containerConcurrency` 40 → 8-10 and `minScale` 1 → 2-3).

**Bug-ref:** 2026-06-23 — PR #7848 fastembed. User asked "cmux should already have visual capture, did you try it?" I went straight to `screencapture -x` (4 failed attempts including region capture, window-list, and screencapture -l). The right move was to start with `cmux --help | grep -iE "screenshot|capture|image"` — cmux DOES have `cmux browser screenshot`, but it's Chromium-only (no terminal surface). Knowing that up front would have saved 4 failed capture attempts. The "When the user asks for visual proof" sub-pattern below codifies this.

## Sub-pattern: "User asks for visual proof of cmux (screenshot of message received / show me the cmux window)"

The user wants to SEE what's happening in the cmux window — typically a `❯` prompt, a churn
spinner, or an error message. The temptation is to jump straight to `screencapture`, but
the **right first move is to enumerate cmux's own visual-capture APIs**:

```bash
# 1. Discover what cmux itself offers (verified on 2026-06-23)
cmux --help 2>&1 | grep -iE "screenshot|capture|image|visual|frame|render"
# Known cmux visual subcommands in 2026-06-23:
#   - `browser screenshot [--out <path>]`  ← Chromium browser surfaces ONLY
#   - `feedback --image <path>`            ← attach an image to a feedback report, NOT capture
#   - `capture-pane ...`                   ← text only (the always-works substitute)
#   - NO `cmux screenshot` for terminal surfaces
```

**If `cmux browser screenshot` exists, check the target surface type BEFORE calling.** Surfaces
have types: terminal vs browser. To enumerate:

```bash
cmux list-pane-surfaces --workspace <w> --pane <p> 2>&1
# or via tree
cmux tree --all --window <win> 2>&1 | grep -B1 -A2 "surface:"
# Look for type: terminal | browser annotations in the output
```

If the target surface is **browser** (Chromium), `cmux browser screenshot --out /tmp/cmux.png`
will work — no TCC blocker because the Chromium renderer is in-process. If the target surface
is **terminal** (Ghostty-backed), `browser screenshot` will error with "not a browser surface"
or similar. **Fall through to `screencapture` only after confirming surface type.**

**If `cmux` has no terminal-screenshot API (the 2026-06-23 reality):** the substitute proof is
`cmux capture-pane --scrollback --lines N`. State the TCC blocker explicitly and use the
text capture as proof. **Do not** offer to "try screencapture" again — the window is
non-shareable (`kCGWindowSharingState=0`) and screencapture will fail.

**Bug-ref: 2026-06-23 — PR #7848 fastembed steering.** User asked "cmux should already have
visual capture, did you try it?" I went straight to `screencapture -x -t png` (4 failed
attempts) instead of starting with `cmux --help | grep -iE "screenshot"`. The right answer
came in one grep: cmux has `browser screenshot` (Chromium only) and `capture-pane` (text only)
— no terminal-surface PNG API. Knowing that up front would have saved 4 capture attempts
plus the diagnostic overhead of ctypes + AppleScript + osascript probing.

## Sub-pattern: "Idle-agent prompt contamination (autocompleter poisons pastes)"

When the worker is sitting at an empty `❯ ` prompt (idle, done with previous task), Claude
Code's ghost-text autocompleter can fire on the prompt and inject text into the buffer
when you paste a long message via `cmux send`. Symptom: the prompt at idle `❯ ` is empty,
you `cmux send` your message, but `read-screen` shows the buffer has both your text AND
trailing garbage like `also i always need intent classifier started up` (the autocompleter's
best-guess continuation of your paste). The whole contaminated buffer submits as one message
and the agent parses your text + the garbage together.

**Defense (apply in order):**

1. **Keep idle-agent pastes SHORT (1-2 lines).** The 2026-06-12 coordination-notes pitfall
   applies here too: shorter pastes are less likely to trigger the autocompleter's
   "complete this for you" reflex. Split the task across multiple short sends, or use a
   pointer to a shared artifact (PR comment, bead, Slack thread) where the agent can re-read
   the long form.
2. **Before sending, read-screen and confirm the prompt is empty.** If there's already
   `❯ something`, send `ctrl+u` (multiple times) until read-screen shows empty `❯ `.
3. **After sending, read-screen IMMEDIATELY (don't wait 5-10s).** If the visible buffer
   text is longer than what you sent, abort the submission with `ctrl+c` + clear with
   backspaces, then re-send a shorter version.
4. **If the contaminated message already submitted,** the agent may parse it OR burn context
   trying — in either case, post a follow-up clarification in the surface to anchor the
   agent on the REAL intent and not the autocompleter's hallucination. The Opus session in
   the 2026-06-23 case did parse past the garbage correctly ("always init the classifier,
   gate only the blocking wait") but burned ~12k tokens on the corrupted payload.

**Bug-ref: 2026-06-23 — PR #7848 fastembed revert.** I sent an 816-char operator note into
`workspace:28 surface:60` (idle Opus session). The autocompleter appended
"also i always need invetn clasisifer runs always need intent classifier started up" to the
buffer. The Opus read past the garbage and inferred the right intent, but burned ~12k tokens
on a corrupted payload AND the prompt was contaminated for follow-up steering. The lesson:
when the user says "steer this agent to fix X", the message length budget is 1-2 lines even
when the task description is 5 lines — split the task across multiple short sends, or use a
pointer to a shared artifact.

## ⚠️ Preflight Validation

**The current cmux CLI does NOT support `--json` as a global flag, and `list-surfaces` is NOT a
command.** These were true in older cmux versions and may still appear in older skills / muscle
memory. Always prefer `cmux <command> --help` before assuming a flag exists.

**`$CMUX_SOCKET_PATH` default (`/tmp/cmux.sock`) is a placeholder, not a real path.** The real
cmux socket is at a build-date-suffixed path (e.g. `/private/tmp/cmux-debug-may-18.sock`). The
`cmux` CLI hides this, but any raw-socket code (`nc -U`, Python `socket.AF_UNIX`, etc.) will
silently fail.

**⚠️ `cmux identify` is NOT enough to find the workspace you need.** It returns the canonical
socket for the currently-running production cmux app, which on this machine has only 2
workspaces (both idle bash logins). All the actual agent workspaces live in the **dev build
socket** (`/tmp/cmux-debug-<build-tag>.sock`). For full workspace enumeration across ALL
running cmux sessions (prod + dev + any future builds), use the multi-app probe recipe in
`references/multi-app-socket-probe-recipe-2026-06-24.md` — this is the FIRST move when the
user names a specific workspace, NOT a fallback. See the new sub-pattern below for the
2026-06-25 bug-ref.

### Sub-pattern: `cmux` CLI itself fails with `Socket not found at /tmp/cmux-debug-<X>.sock`

The CLI itself can fail this way even when the user has NOT set `CMUX_SOCKET_PATH` — verified
2026-06-24: `cmux identify` returned
`Error: Socket not found at /tmp/cmux-debug-fix-agy-hook-deny.sock` while a real socket existed at
`/tmp/cmux-debug-may-18.sock`. Cause: a stale socket path is baked into the CLI's launchd-supplied
default (different build's suffix). The CLI is not falling back to discovery.

**Workaround** — bypass the CLI's hardcoded default by passing `--socket` (verified working):

```bash
ls -1 /tmp/cmux*.sock /private/tmp/cmux*.sock 2>/dev/null
# Find the real one, e.g. /private/tmp/cmux-debug-may-18.sock

cmux --socket /private/tmp/cmux-debug-may-18.sock identify
# Or set the env var to the resolved path:
CMUX_SOCKET_PATH=/private/tmp/cmux-debug-may-18.sock cmux list-workspaces --id-format both
```

If `--socket` is also rejected, fall back to raw JSON-RPC over the resolved socket:
```bash
SOCKET=/private/tmp/cmux-debug-may-18.sock
printf '{"id":"q","method":"workspace.list","params":{}}\n' | nc -U -w 3 "$SOCKET"
```

This is a different failure mode from the "your env var is wrong" case in
`references/socket-discovery-2026-06-21.md` — that one covers raw-socket callers using the
placeholder default; this one covers the CLI itself shipping with a stale default.

### ⚠️ Sub-pattern: `cmux identify` succeeds but the workspace you need is NOT there

**This is the trap that wastes the most turns. Read this FIRST when the user names a
specific workspace (e.g. "find the agy workspace", "where is workspace:72").**

`cmux identify` returns the **canonical** socket for the currently-running cmux app —
which on macOS is typically the *production* `/Applications/cmux.app` instance using
`$HOME/.local/state/cmux/cmux.sock`. That instance often has only **2 workspaces**
(both idle bash logins in `~`). All the actual agent workspaces (`workspace:69 hermes`,
`workspace:72 w: misc - agy`, `workspace:70 daily jobs + deploy`, etc.) live in the
**dev build** socket at `/tmp/cmux-debug-<build-tag>.sock` (e.g. `/tmp/cmux-debug-may-18.sock`).

**`cmux identify` is authoritative for "where is the focused surface in the canonical
socket" — NOT for "where are the agent workspaces".** Treating it as the latter leads
to a long sequence of `cmux list-workspaces` calls that return 2 workspaces, then
concluding "the workspace the user named doesn't exist in this cmux session."

**The right first move — always run the multi-app probe before concluding a workspace
doesn't exist.** Even for ONE-shot interactive scripts:

```bash
# Run the multi-app probe from references/multi-app-socket-probe-recipe-2026-06-24.md
# to find ALL live cmux sessions, not just the canonical one:
declare -a CANDIDATES=()
while IFS= read -r s; do
  CANDIDATES+=("$s")
done < <(ls -1t /tmp/cmux*.sock /private/tmp/cmux*.sock \
              ~/.local/state/cmux/cmux.sock 2>/dev/null | awk '!seen[$0]++')

# Probe each. Pick the first one that returns valid JSON from `cmux identify`.
# Then run `cmux --socket <path> list-workspaces --id-format both` to see ALL
# workspaces across that session.
for cand in "${CANDIDATES[@]}"; do
  [ -S "$cand" ] || continue
  probe=$(timeout 5 cmux --socket "$cand" identify 2>/dev/null || true)
  if [ -n "$probe" ]; then
    echo "=== $cand ==="
    cmux --socket "$cand" list-workspaces --id-format both 2>&1 | head -5
  fi
done
```

If you find a workspace in the dev socket that you didn't see in the canonical
socket, that's the dev session your work belongs in. Use `--socket <dev-path>` for
all subsequent `cmux` calls.

**Bug-ref 2026-06-25 — AGY persona-bleed probe sequence.** User asked: "find the cmux
workspace for agy using agy locally for inference." First probe used `cmux.sock`
(canonical) — got 2 workspaces, neither named agy. Concluded "the AGY workspace
doesn't exist in this cmux session" and burned 2-3 turns on the wrong track.
User pushed back: *"find the socket again, it should be working."* Re-ran the
multi-app probe and found the AGY workspace at `workspace:72 "w: misc - agy"` in
the dev socket `/tmp/cmux-debug-may-18.sock` (along with all 28 agent workspaces).
Lesson: when the user names a specific workspace, the multi-app probe is the FIRST
move, not a fallback for when `cmux identify` returns clean JSON.

### Sub-pattern: cmux CLI flag-order gotchas in launchd scripts (verified 2026-06-26)

Two non-obvious footguns hit when scripting cmux from `launchd` jobs (no interactive
shell context):

**1. `--socket` is a GLOBAL flag, not a subcommand flag.**

```bash
# WRONG — errors with "tree: unknown flag '--socket'. Known flags: --all --workspace --window --json"
cmux tree --window window:1 --socket /tmp/cmux-debug-may-18.sock

# CORRECT — global flag, comes right after `cmux`
cmux --socket /tmp/cmux-debug-may-18.sock tree --window window:1
```

Verified 2026-06-26 with `cmux 0.64.16`. If you put `--socket` after the subcommand,
the subcommand's own flag parser rejects it AND the call silently returns empty,
which a defensive script will treat as "no data" rather than "bad invocation." Always
put `--socket` right after `cmux`.

**2. `CMUX_SOCKET_PATH` env var is silently IGNORED by the CLI in launchd-style env.**

```bash
# WRONG — in launchd-style env, the CLI ignores CMUX_SOCKET_PATH and falls back to
# its baked-in stale default (/tmp/cmux-debug-fix-agy-hook-deny.sock).
# cmux tree --window window:1 → empty (no error, just empty)
env CMUX_SOCKET_PATH=/tmp/cmux-debug-may-18.sock cmux tree --window window:1

# CORRECT — use --socket flag explicitly
cmux --socket /tmp/cmux-debug-may-18.sock tree --window window:1
```

Why `CMUX_SOCKET_PATH` doesn't work in launchd: the CLI's resolution algorithm
appears to be (a) read `/tmp/cmux-last-socket-path` if it exists, (b) else fall back
to the baked-in build default. In a launchd tick, that pointer file may be stale
(pointing at the prod socket with 2 idle bash workspaces) or missing entirely.
Setting `CMUX_SOCKET_PATH` in the env does NOT override the pointer file lookup —
verified by setting it explicitly in `env -i PATH=... HOME=...` and still getting
the stale-default error. **For any launchd/cron script: use `--socket <path>`, never
`CMUX_SOCKET_PATH`.**

**Bug-ref 2026-06-26 — cmux-surface-report-4h.sh false-positive skip alert.**
Cron tick at `2026-06-26T00:03:51Z` fired `:warning: cmux RPC wedged (tree --window
AND --all both empty)` to `#home`. Two causes:
- `/tmp/cmux-last-socket-path` pointed at `$HOME/.local/state/cmux/cmux.sock`
  (prod socket, 2 workspaces) while all agent work lives on the dev socket.
- The script used `env CMUX_SOCKET_PATH=$SOCK cmux tree --window window:1`, which
  in launchd-style env falls back to the baked-in stale default and returns empty.

Fix shipped in `scripts/cmux-surface-report-4h.sh` (commit 351e9cf7c8): multi-app
probe at socket-resolve time + `cmux --socket "$SOCK" ...` for every CLI call.
Verified end-to-end: tick at `2026-06-26T00:28:21Z` posted full 35-surface report
to `C0AJQ5M0A0Y` (ts `1782433701.994439`) instead of skipping.

### Sub-pattern: Two cmux sessions can be live at the same time (verified 2026-06-24)

The `cmux-last-socket-path` and the `~/.local/bin/cmux` shim point to **one** session at a time
(usually the most recently launched). But on the same host, **two** cmux host apps can be
running concurrently — e.g. `/Applications/cmux.app` (prod) and `/Applications/cmux DEV
may-18.app` (a debug build) both have IPC sockets listening.

**Diagnostic — enumerate ALL live cmux sessions:**

```bash
ls -1 /tmp/cmux*.sock /private/tmp/cmux*.sock 2>/dev/null
# Plus user-state cmux sockets:
ls -1 ~/.local/state/cmux/cmux.sock 2>/dev/null
ls -1 ~/.local/state/cmux/*-last-socket-path 2>/dev/null

# For each, test if anything is actually listening:
for s in /tmp/cmux-debug-*.sock ~/.local/state/cmux/cmux.sock; do
  if [ -S "$s" ]; then
    r=$(printf '{"id":"q","method":"ping","params":{}}\n' | nc -U -w 2 "$s" 2>&1)
    echo "$s → $r"
  fi
done
# Each entry that returns a JSON response (even `{"error":"method_not_found"}`) is a LIVE session.
# The shim may be pointing at a dead one; the other is the real one.
```

**Bug-ref 2026-06-24 — cmux review of cost/caching workspaces:**
- Session A (debug build): `/private/tmp/cmux-debug-may-18.sock` — 27 workspaces including all
  the cost/caching work (workspace:88 "cost: reviewer", workspace:68 "cost: implicit cache",
  workspace:81 "cost: system inst", workspace:73 "local cache", workspace:84 "proxy: context")
- Session B (prod `cmux.app`): `$HOME/.local/state/cmux/cmux.sock` — 2 workspaces
  (workspace:1 and workspace:2, both idle bash logins)
- The shim was pointing at a *third* dev CLI (`/tmp/cmux-debug-fix-agy-hook-deny.sock`) that
  didn't exist on disk. Every `cmux <verb>` failed with "Socket not found" until I bypassed
  with `--socket` and tried both real sessions.

**Rule:** when the shim fails, enumerate ALL cmux*.sock files and probe each with `nc -U
ping`. Both prod AND dev sessions may be live, with different workspace sets. The user's
"the cost work" might be in the debug session, not the prod one (or vice versa).

**When reporting a "what are the terminals doing" summary, check both sessions** — the
workspaces you care about may be in the non-default one. The `cmux-terminal-review` skill
assumes one socket; for two-session reality, run the inventory against both and merge
the results before categorizing.

**For unattended/launchd jobs that MUST work with any cmux build** (where you can't guarantee
which build will be running), use the multi-app probe recipe that iterates ALL candidate sockets
across `/tmp` + `/private/tmp` + `~/.local/state/cmux/` and picks the first one whose
`cmux --socket <path> identify` returns valid JSON. See
`references/multi-app-socket-probe-recipe-2026-06-24.md` for the full bash template.
Verified 2026-06-24 — supersedes `socket-discovery-2026-06-21.md` for unattended runs.

Common traps (verified 2026-06-11):

- `cmux list-surfaces ...` → **does not exist**. Real options: `cmux tree --all`,
  `cmux list-panes --workspace <id>`, `cmux list-pane-surfaces --workspace <id> --pane <id>`.
- `cmux list-surface` (singular) → wrong subcommand; also doesn't exist.
- `cmux --json <command>` → `--json` is not a global flag. Per-command JSON lives behind
  `cmux <command> --json` (works for some commands like `identify`, `top`, `list-workspaces`,
  `auth status`, `ssh-session-list`).
- `cmux --workspace <id> --surface <id> <command>` → wrong ordering. The actual pattern is
  `cmux <command> --workspace <id> --surface <id>` (flags after the subcommand).
- `cmux send "text"` (bare) → in current CLI `send` requires `--workspace` and `--surface`
  (no default to caller surface). Use `cmux send --workspace <w> --surface <s> "text"`.
- `cmux send-surface --surface <id> "cmd"` → `send-surface` does not exist. Use
  `cmux send --surface <id> "cmd"`.
- `cmux send-key enter` → exists, but keys must match the documented set: `enter`, `tab`,
  `escape`, `backspace`, `delete`, `up`, `down`, `left`, `right`, etc.
- `cmux new-split` → exists but takes a positional direction (`left`/`right`/`up`/`down`),
  not `--direction`. It also needs `--workspace` and a surface to split from
  (e.g. `cmux new-split --workspace <w> --surface <s> right`).
- **`cmux select-workspace --workspace 5` does NOT focus `workspace:5`.** The bare
  integer is interpreted as an **index** (positional, sorted by tab order — NOT by
  `ref` number). The index list is not sorted by `ref`, so `index 5` can map to
  any workspace. Verified 2026-06-13: `select-workspace --workspace 5` returned
  `OK workspace:12` and switched focus there instead of the user's `workspace:5
  "bq logging"`. The trap is silent — it does return `OK workspace:<X>`, just not
  the X you expected. **Always use the explicit ref form** `--workspace workspace:5`
  when you mean a specific ref. If you only have the integer from
  `cmux list-workspaces`, run `cmux list-workspaces --id-format both` first and use
  the ref (`workspace:N`), not the integer. Full recipe (including the
  raw-socket alt when the CLI is misbehaving): see
  `references/workspace-routing-trap.md`.

### ⚠️ `cmux read-screen --workspace 62` (bare integer) FAILS — use `--workspace workspace:62`

Same trap class as `select-workspace` above, but for the read/inspect family.
Verified 2026-06-25 (lvl/cost recap probe): `cmux read-screen --workspace 62` (and
`--workspace 68`, `--workspace 81`, etc.) all returned `Error: Workspace index not
found`, even though `cmux list-workspaces` clearly showed `workspace:62 "lvl:
refactor"`. Same for `--workspace 88`, `--workspace 89` — every bare-integer read
failed silently with that one-line error.

**Why:** the bare integer is parsed as a positional **index**, but `--workspace 62`
triggers a different code path than `select-workspace` does — `select-workspace`
swallows the index-vs-ref ambiguity and silently re-targets to whatever index 62
is, while `read-screen` / `read-pane` / `focus-pane` reject the bare integer with
`Error: Workspace index not found` and never read anything.

**Fix:** always pass the **ref form** `--workspace workspace:62`. Verified working:

```bash
# BAD — all of these fail with "Workspace index not found"
cmux read-screen --workspace 62 --surface 1
cmux tree --workspace 62
cmux list-panes --workspace 62

# GOOD — ref form works
cmux read-screen --workspace workspace:62 --surface surface:1
cmux tree --workspace workspace:62
cmux list-panes --workspace workspace:62
```

**Recipe (always):** copy the `workspace:N` ref straight from `cmux list-workspaces`
output — never type the integer. The same applies to surface refs (`surface:M`,
not `1`) and pane refs (`pane:M`, not `1`). If you only have an integer from a
prior session, run `cmux list-workspaces --id-format both` to get the ref →
index mapping, then use the ref.

**Bug-ref:** 2026-06-25 — lvl/cost recap probe across 6 workspaces
(`lvl: refactor`, `cost: implicit cache`, `cost: system inst`, `cost: reviewer`,
`local cache`, `rag: extended`). First probe batch used `--workspace 62` etc.
and failed with the same error 6 times. Re-ran with `--workspace workspace:62`
and every read succeeded in one call each.

If a command fails with `Error: Unknown command:` or `Usage:` dump, run `cmux <command> --help`
to see the real syntax — do not guess.

**`surface.readScreen` does not exist as a method.** The right
JSON-RPC method is `surface.read_text` — but see the warning in
"Reading a Non-Focused Surface" above: it ignores ref params.
**`surface.focus` requires `surface_id` (UUID), not `surface_ref`.**
**`surface.list` ignores `workspace_ref` — returns the focused
workspace's data.** Full transcript: `references/surface-read-routing-bug.md`.

## ⚠️ Status Bar Interpretation — NOT Frozen

Claude Code status bar states to interpret correctly:
- **`⏵⏵ bypass permissions on`** in status bar = normal Claude Code prompt UI, NOT a blocking dialog — Claude Code is actively working around it
- **Active churning timestamps** (e.g., "Churned for 9m 41s", "Sautéed for 2m 38s") = genuinely working workspace, NOT frozen
- **"Still running" indicator** = work in progress, not stalled
- **Idle bash shell** (fresh login prompt) = workspace is done or waiting for input, NOT frozen
- **ctx XX% progress** = active context usage, workspace is alive

**What IS actually blocked:**
- `bypass permissions on (shift+tab to cycle)` with NO active churning/time-on-task and NO progress indicator = may be a real stall
- "Index error" or "workspace unreachable" = workspace handle drift, genuinely blocked
- Shell at `claude`/`claudem` typed but no Claude Code active = shell-level stall, needs restart
- "Add a follow-up" dialog open in Composer 2 Fast = blocked on human follow-up, not frozen

**Key rule:** A workspace with an active time-on-task label ("Churned for Xm", "Crunched for Xm") is working, regardless of what the status bar shows. Only report as "frozen" when there's evidence of no activity AND no active time-on-task.

## Reading a Non-Focused Surface (verified 2026-06-13)

`cmux read-screen --workspace X --surface Y` and the raw
`surface.read_text {workspace_ref, surface_ref}` JSON-RPC method are
**both broken** in the current build — they return the focused surface's
content, not the target. The CLI also rejects many valid targets with
`Error: invalid_params: Surface is not a terminal` (it routes to a
wrong internal handle before the type check).

**The reliable recipe — focus-then-read:**

```bash
# 1. Discover the target surface's UUID
#    Focus the workspace, then raw-socket call surface.list (the
#    workspace_ref param is ignored, so you must focus first)
cmux select-workspace --workspace N
SOCKET=$(cmux identify | python3 -c "import json,sys;print(json.load(sys.stdin)['socket_path'])")
UUID=$(printf '{"id":"q","method":"surface.list","params":{}}\n' \
  | nc -U -w 3 "$SOCKET" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print([s['id'] for s in d['result']['surfaces'] if s['ref']=='surface:M'][0])")

# 2. Focus the target surface (param is surface_id=UUID, NOT surface_ref)
printf '{"id":"q","method":"surface.focus","params":{"surface_id":"%s"}}\n' "$UUID" \
  | nc -U -w 3 "$SOCKET" >/dev/null

# 3. Read the now-focused surface (no --surface flag)
cmux read-screen --scrollback --lines 50
```

`surface.focus` requires `surface_id` (the UUID). It rejects
`surface_ref` and bare integers. See
`references/surface-read-routing-bug.md` for the full transcript and
upstream-bug filing notes.

**Faster "is this worker alive?" diagnosis without per-surface focus:**

1. `cmux tree --all` — pane titles include active time-on-task labels
   (e.g., "Churned for 9m 41s", "Flibbertigibbeting… 12m 34s",
   "Sautéed for 2m 38s"). A pane WITHOUT such a label is more likely
   dead/stalled. No read needed.
2. `tail -f /tmp/cmux-debug-may-18.log` (or current build's log) — look
   for `workspace.gitProbe.apply` and `workspace.prRefresh.apply`
   lines; their presence proves the surface is producing events.

## "What is this workspace doing?" — The Discovery Recipe

This is the most common cmux task from the gateway: user names a workspace (e.g. "agentf") and
you need to (a) find it, (b) see what surface is focused, (c) read the actual screen text, and
optionally (d) steer. Verified sequence (2026-06-11):

```bash
# 1. Find the workspace by partial title
cmux list-workspaces                       # text output, refs like "workspace:10"
cmux list-workspaces --id-format both      # adds UUIDs

# 2. Get the pane/surface tree (titles + tty + focus state)
cmux tree --all                            # whole window
cmux tree --all --window <win_ref>         # single window

# 3. Confirm focus + identify a specific surface
cmux identify                              # caller context + currently focused
cmux identify --workspace <w> --surface <s>  # one surface's context

# 4. Read the actual terminal text (the critical step) — only works
#    reliably for the FOCUSED surface. For non-focused surfaces see
#    "Reading a Non-Focused Surface" above (focus-then-read recipe).
cmux read-screen --workspace <w> --surface <s>           # visible viewport only
cmux read-screen --workspace <w> --surface <s> --scrollback --lines 200   # last 200 lines of scrollback

## "Should I steer now or wait?" — The In-Flight Worker Decision Rule

When the user says "steer this worker" / "use natural language to fix
[problem X]", the worker may already be in the middle of investigating
or fixing something — possibly the same thing, possibly something else.
Steering without checking risks context bleed and double-work.

**Rule (verified pattern, 2026-06-13; extended 2026-06-21):**

1. **Read the focused surface** of the target workspace
   (`cmux read-screen --scrollback --lines 60`).
2. **Check for active subagents** in the bottom 30 lines of viewport
   — Claude Code shows them as:
   - `✻ Waiting for N background agents to finish`
   - `◯ <subagent-name>  <task>  <time>  <tokens>`
   - `✻ <churn-phrase> (<time>  · ↓ <tokens>)`
3. **Decide:**
   - **Worker is idle and at a prompt** (`❯` with empty input) →
     safe to steer now. Send the natural-language instruction and
     press Enter.
   - **Worker is actively churning** (churn label + time counter
     advancing) → wait. Note the churn time; if it exceeds ~5 min
     with no progress visible, the worker may be stuck and may need
     an Escape + re-steer.
   - **Worker has 1+ in-flight subagents** → do NOT steer. Wait for
     subagents to finish (the parent will then continue). If the
     new task is URGENT and unrelated, ask the user to confirm
     "interrupt the current investigation" before sending Escape +
     new message.
   - **Worker hit a session rate limit** ("You've hit your session
     limit · resets <time>") → can't steer this session. Either
     wait for reset or open a new surface and start fresh.

4. **Before steering: read the worker's recent task context, not just
   its current state** (verified pitfall 2026-06-21). Scroll back
   further than 60 lines — the worker's last 200 lines typically
   contain the "user's request was: …" recap block. **If the worker
   is already working on the same problem the new steering message
   is about, do NOT send a from-scratch instruction.** Instead,
   send a *verification-first* steer that:
   - Quotes the user's exact words and channel context.
   - Asks the worker to (a) confirm whether its current PR/branch
     covers the new request, (b) state what additional work is
     needed if any, (c) report back. **Do not** reissue the
     original task — that re-runs it and risks duplicate PRs.
   - Explicitly tells the worker "Do NOT merge / Do NOT fake-approve
     CR / Do NOT resolve threads" if the existing PR is still
     mid-review.
   - Asks the worker to post a brief in-thread status note so the
     user knows steering landed.

   This pattern preserves the worker's progress (which may be
   hours of design + test work) and converts a "do this from
   scratch" steering into a "verify + amplify" steering. Burned
   once on 2026-06-21: a user said "find the hermes workspace and
   steer it to fix this routing bug" — the worker already had
   PR #665 open covering exactly the same routing bug. A naive
   "fix the routing bug" steer would have either duplicated the
   work or trampled the existing branch. The verification-first
   steer landed cleanly in 6s.

**Steering template (Claude Code worker):**

```bash
WS=4; SURF=45
cmux select-workspace --workspace $WS
cmux send --workspace $WS --surface surface:$SURF "$(cat <<'EOF'
After your current investigation finishes, also start a
<repro|/repro|/root-cause-first/etc.> worker for
<bug description + URL>. Prefer <fix approach> over <anti-pattern>.
Report findings here when done.
EOF
)"
cmux send-key --workspace $WS --surface surface:$SURF enter
# Verify: spinner/churn label should appear within ~5s
sleep 5 && cmux read-screen --scrollback --lines 15
```

**Why this rule exists:** in 2026-06-13 a user asked "investigate
why workers are dead, then steer the ao workspace to fix
<character-creation bug>". The ao worker was already mid-investigation
on the worker-death question (agy failure investigation, 16+ min
running). Steering immediately would have aborted a high-value
investigation and risked context bleed between two different bugs.
The right move was to report findings + ask the user to confirm
"wait for current subagents, or interrupt and steer now?".

## Steer (if appropriate) — Sending the actual message

Once you've decided the worker is safe to steer (see the In-Flight
Worker Decision Rule above), the actual send is straightforward:

```bash
cmux send --workspace <w> --surface <s> "your message"   # types text
cmux send-key --workspace <w> --surface <s> enter         # presses Enter
```

## Multi-surface parallel steering (verified 2026-06-24, 4 steers in one batch)

When the user gives a directive that maps to **N independent workspaces**
("steer all the cost workspaces", "kick off the next steps in
each PR review surface", "fan out the Slack-pivot instructions"),
**send the steers in one parallel batch** then verify each after a
shared settle period. This is faster than serial and safer than
sending all-then-verifying one at a time.

**The pattern:**

```bash
export CMUX_SOCKET_PATH=/private/tmp/cmux-debug-may-18.sock

# 1. Identify all target (ws, surface) pairs from the user's directive
TARGETS=("81 229" "73 139" "84 223" "70 132")  # (workspace surface) tuples

# 2. Filter: only steer surfaces that are SAFE per the In-Flight Worker Rule
#    - empty ❯ prompt
#    - no active churning label
#    - not mid-Edit on a different file
#    Skim each surface's recent output first; skip the busy ones.
SAFE_TARGETS=("81 229" "73 139" "84 223" "70 132")  # after triage

# 3. Send all steers + Enter keys in one batch (parallel-safe: each
#    cmux call is its own short-lived subprocess)
for pair in "${SAFE_TARGETS[@]}"; do
  set -- $pair
  ws=$1; surf=$2
  cmux send --workspace=workspace:$ws --surface=surface:$surf "your steer here"
  cmux send-key --workspace=workspace:$ws --surface=surface:$surf enter
done

# 4. Single settle wait, then verify EACH surface absorbed the steer
sleep 10
for pair in "${SAFE_TARGETS[@]}"; do
  set -- $pair
  ws=$1; surf=$2
  echo "=== w${ws}/s${surf} ==="
  cmux read-screen --workspace=workspace:$ws --surface=surface:$surf --lines 15 \
    2>&1 | grep -vE '^\s*Error:' | tail -8
done
```

**What "absorbed" looks like:**
- An active churning label appears (e.g. `✻ Beboppin'…`, `Brewed for`, `Creating follow-up branch…`)
- The worker's first action matches the steer (new branch name, new commit, new tool call)
- A new task list item appears with the steer's content

**What "stuck" looks like (the steer landed but worker didn't act):**
- Message text is visible at the prompt but no churn label
- An API error appears: `Unable to connect to API (ConnectionRefused)`, `You've hit your session limit`
- Worker reverts to a previous task or context

**Bug-ref 2026-06-24 — parallel steer of 4 cost workspaces** (workspace:88
"cost: reviewer", workspace:68 "cost: implicit cache", workspace:81 "cost:
system inst", workspace:73 "local cache", workspace:84 "proxy: context",
workspace:70 "daily jobs + deploy"):
- 4 of 6 steers absorbed cleanly (w81 began executing the /goal I sent,
  w84 created a new branch + PR within 2 min, w70 sat at the prompt
  holding the operator runbook message)
- 1 was correctly skipped (w88 "cost: reviewer" had 4 active teammates
  on a fan-out — In-Flight Worker Rule fired, no steer)
- 1 surfaced a separate agent-side issue (w73 "local cache" hit
  `API Error: Unable to connect to API (ConnectionRefused)` — Claude
  API auth problem on the worker's CLI, not a steer problem)

**The settle-wait before verify** is critical: 5s is too short for the
worker to react. 10s is the sweet spot for a healthy agent; 30s for
one mid-thought on a 50+ minute run. After verify, if a steer didn't
absorb (no churn, no action, message still visible), DO NOT resend
the same message — that risks double-submission. Instead, treat it
as a separate issue and surface to the user.

**Don't:**
- Don't send 4 steers + 4 separate verify-reads in 4 sequential cmux
  calls — that's 8 round-trips. The batch pattern above is 4 sends
  + 4 enter-keys + 4 verify-reads in 2 batched shells.
- Don't steer a worker that's mid-Edit on a different file (per
  In-Flight Worker Rule) just because the user said "all of them."
  Filter first; surface the skipped ones in your report.
- Don't resend the same message if a steer didn't absorb — that's
  the double-submission anti-pattern. Investigate the surface state
  first.

**Handles:** `workspace:10`, `pane:17`, `surface:19`, `window:1` are all valid refs. UUIDs
work too (`--id-format both`). Indexes (1-based across the window) also work but refs are
unambiguous.

**Default socket path:** the cmux app uses `/tmp/cmux-debug-may-18.sock` or similar (the
filename is build-date-suffixed). `cmux` CLI figures it out automatically. The
`CMUX_SOCKET_PATH` env var is for raw socket access (Python client) — set it to the real
socket path returned by `cmux identify` (field `socket_path`).

## "Find the cmux workspace for X" — Load `cmux-find-workspace-by-topic`

**Before doing anything else when the user says "find the cmux workspace for X":** load the dedicated skill `cmux-find-workspace-by-topic`. It codifies the multi-socket probe + keyword grep recipe that found `workspace:72 "w: misc - agy"` in 3 seconds (2026-06-25) after the shim's dead-default hid it. Don't start from `cmux list-workspaces` — that may be pointed at a dead dev CLI.

## Sub-pattern: "User asks for meta / skillify / audit of cmux workflows" (added 2026-06-26)

When the user asks for **meta work on cmux** (not actual steering/finding):

> "skillify cmux", "improve hermes confusion with cmux workspace finding",
> "audit the cmux skills", "review cmux routing", "/learn cmux workflow",
> "do not do the actual work, do meta work and /skillify"

…**DO NOT propose new cmux skills first.** Three cmux skills already exist and cover the territory:

| Skill | When it fires |
|---|---|
| `cmux` (this one) | CLI/socket reference, multi-session probe, send→submit→proof, focus-then-read, in-flight worker rule, stale-screen trap |
| `cmux-find-workspace-by-topic` | Multi-socket probe + keyword grep (the dead-shim-hides-the-workspace trap) |
| `cmux-mcp-server-options` | Community MCP server list, install recipe, decision guide, "Hermes doesn't need one today" |

**The right first move (verified 2026-06-26):**

1. **Load the 3 existing skills** and audit what's already covered. Most "new" proposals are already addressed (multi-socket probe, focus-then-read, `--socket` global flag, launchd env var ignore, send→submit→proof ritual, parallel steering, in-flight worker rule, stale-screen trap, workspace-routing trap, MCP server list).
2. **Identify the SPECIFIC gap** the user is actually hitting (e.g. "skills don't auto-load" vs "no workspace catalog" vs "skills overlap" — each has a different fix).
3. **Then propose** 1-2 targeted skills or skill patches — not 4 speculative ones.

**Reply shape for meta audits** (per user preference `Reply shape: evidence + 2-4 next-step options + STOP`):
- Lead with evidence: "skills already cover X, Y, Z (verified [date]). Real gap: [specific thing]."
- Don't list every potential new skill — list only the ones that pass the "this would have prevented a real session burn" test.
- End with 2-4 next-step options + STOP, NOT a long speculation list.

**Bug-ref 2026-06-26 — meta audit of cmux confusion.** User said: *"do not do the actual work discussed, do meta work and /skillify and /learn to improve hermes confusion with cmux workspace finding and steering and /research to see if cmux has an mcp server."* I loaded the 3 cmux skills, verified the MCP server registry state, and proposed 4 NEW skills (`cmux-steering-workflow`, `cmux-workspace-catalog`, etc.) before checking the existing skill coverage. Three of those four were already covered by the parent + 2 subs. The real gap was "skills don't auto-load on meta-audit phrasing" — fixed by broadening `cmux-find-workspace-by-topic` description triggers, not by adding new skills. The lesson: **meta audits are mostly skill audits, not skill creation. Lead with coverage check, then propose only the gaps that survive it.**

## MCP servers for cmux (community, not upstream)

cmux itself does NOT ship an MCP server (verified v0.64.17, 2026-06-23). Multiple community MCP servers wrap the cmux CLI/socket — see the dedicated `cmux-mcp-server-options` skill for the verified list, install recipe, and decision guide (`@jsamuel1/cmux-mcp` is the hardened fork most AI agents use).

For Hermes's own automation today, use the CLI over shell — Hermes doesn't currently register MCP clients for itself.

## Socket Connection (raw JSON-RPC)

```bash
# Default socket — confirm with `cmux identify` (look at socket_path field)
SOCKET_PATH="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
```

Send JSON-RPC requests (newline-delimited):
```json
{"id":"req-1","method":"workspace.list","params":{}}
{"id":"req-2","method":"workspace.tree","params":{"all":true}}
{"id":"req-3","method":"surface.readScreen","params":{"workspace_ref":"workspace:10","surface_ref":"surface:19","scrollback":true,"lines":200}}
```

`scripts/cmux_client.py` is a small Python wrapper that does this over a Unix socket
(`CMUX_SOCKET_PATH` env, default `/tmp/cmux.sock`). Use it from inline scripts.

## Error / stderr Handling

```python
# Always emit terminal status even on error
try:
    result = subprocess.run(["cmux", "tree", "--all"], capture_output=True, text=True, timeout=10)
except Exception as exc:
    msg = f":fire: cmux error: `{exc}`"
    slack.post_message(channel_id, msg, thread_ts=thread_ts)
    return

# Truncate large output for Slack display
if len(result.stderr) > 2000 or result.stderr.count("\n") > 20:
    summary = truncate_output(result.stderr)
    slack.post_message(channel_id, f":warning: cmux output truncated:\n```\n{summary}\n```", ...)
```

## CLI Quick Reference (current cmux)

> **The most up-to-date command list lives in `references/cli-cheatsheet.md`.** The tables below
> are the high-traffic subset verified on 2026-06-11.

### Discovery (read-only)

| Action | Command |
| --- | --- |
| List workspaces | `cmux list-workspaces` (add `--id-format both` for UUIDs) |
| Workspace tree | `cmux tree --all` |
| List windows | `cmux list-windows` |
| Current window | `cmux current-window` |
| List panes in a workspace | `cmux list-panes --workspace <w>` |
| List surfaces in a pane | `cmux list-pane-surfaces --workspace <w> --pane <p>` |
| Identify caller/focus | `cmux identify` (add `--workspace <w> --surface <s>`) |
| Read screen text | `cmux read-screen --workspace <w> --surface <s> [--scrollback --lines N]` |
| Surface health | `cmux surface-health [--workspace <w> --surface <s>]` |
| Capabilities | `cmux capabilities` |
| Stream events | `cmux events [--name <name>] [--limit N]` (can block; set a timeout) |

### Workspace / window control

| Action | Command |
| --- | --- |
| Create workspace | `cmux new-workspace` (add `--cwd <path>`, `--command <cmd>`) |
| Select workspace | `cmux select-workspace --workspace <id>` |
| Close workspace | `cmux close-workspace --workspace <id>` |
| Rename workspace | `cmux rename-workspace --workspace <id> "name"` |
| Reorder | `cmux reorder-workspace --workspace <id> --index N` |
| Workspace context menu | `cmux workspace-action --action <name> --workspace <id>` (e.g. `pin`, `set-color`) |
| Open path/URL | `cmux open <path-or-url> [--workspace <id>]` |
| SSH workspace | `cmux ssh user@host [-A]` |

### Panes & surfaces

| Action | Command |
| --- | --- |
| New split | `cmux new-split --workspace <w> --surface <s> <direction>` (`left`/`right`/`up`/`down`) |
| New pane | `cmux new-pane --workspace <w> --surface <s> terminal\|browser` |
| New surface | `cmux new-surface --workspace <w> --pane <p> terminal\|browser` |
| Focus pane | `cmux focus-pane --workspace <w> --pane <p>` |
| Close surface | `cmux close-surface --workspace <w> --surface <s>` |
| Move surface | `cmux move-surface --workspace <w> --surface <s> --to-workspace <w2>` |
| Split off | `cmux split-off --workspace <w> --surface <s> <direction>` |

### Input (steering a terminal)

| Action | Command |
| --- | --- |
| Send text | `cmux send --workspace <w> --surface <s> "echo hello"` |
| Send key | `cmux send-key --workspace <w> --surface <s> enter` |
| Keys | `enter`, `tab`, `escape`, `backspace`, `delete`, `up`, `down`, `left`, `right` (and more — `cmux send-key --help`) |

`cmux send` does NOT auto-press Enter. To execute a command, send the text then `send-key enter`.

### Sidebar & notifications

| Action | Command |
| --- | --- |
| Notify | `cmux notify --title "T" --body "B" [--workspace <w>]` |
| List notifications | `cmux list-notifications` |
| Set status pill | `cmux set-status <key> "<value>"` |
| Clear status pill | `cmux clear-status <key>` |
| Set progress | `cmux set-progress 0.5 --label "Building..."` |
| Clear progress | `cmux clear-progress` |
| Log entry | `cmux log "msg" --level info\|warn\|error` |

### Hooks & agent integration

| Action | Command |
| --- | --- |
| Install agent hooks | `cmux hooks setup [--agent <name>]` |
| Uninstall | `cmux hooks uninstall [--agent <name>]` |
| Feed TUI | `cmux feed tui` |
| Browser automation | `cmux browser <subcommand>` (snapshot, click, type, eval, screenshot, etc.) |

## Python Client

```python
import json
import os
import socket

SOCKET_PATH = os.environ.get("CMUX_SOCKET_PATH", "/tmp/cmux.sock")

def rpc(method, params=None, req_id=1):
    payload = {"id": req_id, "method": method, "params": params or {}}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET_PATH)
        sock.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        return json.loads(sock.recv(65536).decode("utf-8"))

# List workspaces
print(rpc("workspace.list", req_id="ws"))

# Send notification
print(rpc("notification.create", {"title": "Hello", "body": "From Python!"}))
```

The wrapper lives at `scripts/cmux_client.py` (this skill's scripts/ dir).

## Shell Helper

```bash
cmux_cmd() {
    SOCK="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
    printf "%s\n" "$1" | nc -U "$SOCK"
}

cmux_cmd '{"id":"ws","method":"workspace.list","params":{}}'
```

## Check if cmux is Available

```bash
[ -S "${CMUX_SOCKET_PATH:-/tmp/cmux.sock}" ] && echo "cmux socket available"
command -v cmux &>/dev/null && echo "cmux CLI available"
```

## Sub-pattern: "Verify a TUI-only feature works (Claude Code /advisor, /config, /model, etc.)"

**Load the dedicated skill `test-tui-claude-feature-via-cmux` first** when the
user asks "does /feature work." It ships a wrapper script
(`scripts/test-tui-feature.sh`), 6/6 unit tests, and a worked example — using
it is faster and more reliable than re-deriving the recipe from this
sub-pattern. The cmux sub-pattern here is the **primitive** that skill is
built on; the dedicated skill is the right entry point for the user-facing
question.

The summary of why the dedicated skill exists (kept here for the
"load cmux first" path):

> `claude --print "/feature"` will always return
> `/<feature> isn't available in this environment` for TUI slash
> commands, because `--print` is non-interactive mode. That error
> specifically means "I cannot show you this in non-interactive mode,"
> **not** "this feature is broken." Treating it as a feature-gate failure
> leads to 30+ minute rabbit holes reading minified binary strings
> (`isFirstPartyApiBackend`, `xr()`, `VW()`, `oct()`,
> `isFirstPartyAnthropicBaseUrl`) and trying every env-var combination.
> The user's literal words on 2026-06-23, when this happened with
> `/advisor`: *"are you opening claude code itself and typing /advisor?
> … use cmux stop being lazy."*

The full recipe lives in [`references/tui-feature-testing-recipe.md`](./references/tui-feature-testing-recipe.md)
and in the dedicated skill `test-tui-claude-feature-via-cmux`. The
six-step primitive (spawn → discover surface → wait for `❯` → send →
read → cleanup) is the same; the dedicated skill wraps it in a tested
script and adds the `isn't available in this environment` non-interactive
detector that signals a malformed slash command or a not-yet-ready
prompt.

**Surface-rediscovery pitfall (verified 2026-06-23):** `cmux list-pane-surfaces`
returns `surface:N` for the first surface in the first pane of the target
workspace, but a new-workspace spawn can produce a different surface number
than expected. The /advisor verification session used `workspace:31 surface:66`;
a hardcoded `surface:65` from a prior session would have either misrouted or
errored with `Surface is not a terminal`. **Always re-discover the surface
from the spawn output — never hardcode a surface number from a prior
workspace.** The dedicated skill's helper script does this automatically.

**Companion skill note:** the dedicated `test-tui-claude-feature-via-cmux`
skill lives at `~/.hermes_prod/skills/test-tui-claude-feature-via-cmux/`
and is the **preferred entry point** when the user asks "does /feature
work." Load it first; fall back to the inline cmux recipe only when
the dedicated skill's wrapper doesn't fit (e.g. multi-step dialog
navigation that needs a custom key sequence).

### Sub-pattern: "Workspace screen says X, but GitHub says Y" (verified 2026-06-25)

**The trap:** cmux workspace displays are a **stale proxy** for the live source-of-truth
(GitHub PR state, local file state, etc.). When you `cmux read-screen` a workspace
talking about PR #7907, the screen text might say "green/unstable (author churning)"
while GitHub's actual `commits/<sha>/check-runs` shows 4 consecutive Green Gate
SUCCESS runs in the last 3 hours. The screen is a *snapshot of the agent's last
recap message*, which can be 30-90+ minutes old — the agent has been doing real work
since then but hasn't posted an updated summary.

**Bug-ref 2026-06-25 — lvl/cost recap probe** (6 workspaces):
- workspace:88 "cost: reviewer" screen showed:
  - `#7907 — OPEN, head d64d96899, green/unstable (author churning)`
  - `#7920 — OPEN, head 8e0985afc, mergeable=clean (3 blockers fixed)`
- Both screens were STALE. Live GitHub state:
  - `#7907` head `d64d9689` had 4 Green Gate SUCCESS runs in the last 3 hours
    (freshest <https://github.com/$GITHUB_REPOSITORY/actions/runs/28199477760|run 28199477760> 21:12Z) — fully green
  - `#7920` head `8e0985afc` had 3 Green Gate SUCCESS runs in the last 30 min
    (freshest <https://github.com/$GITHUB_REPOSITORY/actions/runs/28199013911|run 28199013911> 20:38Z) — fully green
- The "author churning" label in workspace:88 referred to the local worker's
  activity log, not the PR's check-runs. **The user's recommendation would have
  been wrong** ("#7907 needs more work") if I'd trusted the screen.

**Rule:** when a workspace screen quotes a PR's check status, **always cross-check
against the live GitHub state** before acting on it. The canonical cross-check:

```bash
BR=$(gh pr view <N> --repo <owner>/<repo> --json headRefName -q .headRefName)
SHA=$(git ls-remote https://github.com/<owner>/<repo>.git refs/heads/$BR 2>/dev/null | awk '{print $1}')
echo "branch=$BR head=$SHA"
gh api "repos/<owner>/<repo>/commits/$SHA/check-runs" \
  --jq '[.check_runs[] | {name, conclusion, started_at, html_url}]
        | sort_by(.started_at) | reverse | .[0:8]'
```

**Per CLAUDE.md "7-green verification"** — `gh pr checks` is NOT sufficient for
Green Gate; must read workflow logs for gate-by-gate PASS/FAIL. For a faster
"is this PR fundamentally green?" answer, the `check-runs` API with `.conclusion`
(not `.state` — `.state` is null for Actions and only populated for legacy commit
statuses) is the right primitive. Look for `conclusion: "success"` on the "Green
Gate" named check_run.

**When to trust the screen:** when the workspace screen shows a recent
*churning label with advancing time* (`Churned for 12m 34s`, `Brewed for 5m 12s`)
or an active subagent, the worker IS doing something — the screen reflects
current state. The stale-screen trap fires when the screen shows a *recap line*
that's actually a few hours old.

**Also applies to mergeable state** (`workspace:88` showed `#7920 mergeable=clean`,
live GitHub said `MERGEABLE` — that one happened to match, but `mergeable_state`
in GitHub API can lag too). Always pull `mergeable` via `gh pr view --json mergeable`
as the source-of-truth.

### ⚠️ THE #1 RECURRING FAILURE — Send → Submit → Proof

`cmux send` does NOT press Enter. The user has explicitly flagged this as
"you always forget to send" at least 5 times in the last 30 days (2026-06-09,
2026-06-19, 2026-06-20, 2026-06-23, 2026-06-25). The canonical 4-step ritual
(send → send-key enter → sleep → verify churning label) lives at
**`references/send-submit-proof-2026-06-25.md`** — load it before steering any
idle agent. The user's framing phrase "did you press send" / "show me proof"
maps directly to this reference.

For long task briefs (>200 chars), use the **worktree-pointer strategy** —
write the brief to a file in the worker's cwd and send a short 1-2 line
pointer to it. Documented in the same reference.

## Related references

- **`references/send-submit-proof-2026-06-25.md`** — the canonical 4-step send→submit→proof ritual + worktree-pointer strategy. **Load this before steering any idle agent.**
- **`references/cli-cheatsheet.md`** — full command list grouped by intent (canonical reference).
- **`references/socket-discovery-2026-06-21.md`** — original recipe, `cmux identify` as canonical resolver.
  Use for ONE-shot interactive scripts; **for launchd jobs and any unattended run, use
  `multi-app-socket-probe-recipe-2026-06-24.md` instead** (probes ALL candidate sockets so
  any cmux build/app combo works).
- **`references/surface-read-routing-bug.md`** — non-focused surface read API bugs + focus-then-read workaround (2026-06-13).
- **`references/workspace-routing-trap.md`** — `select-workspace` index-vs-ref footgun + the "find a workspace by partial title" recipe that always works (2026-06-13).
- **`references/tui-feature-testing-recipe.md`** — "does /feature work" verification via cmux (full transcript, surface-discovery pitfall, the `isn't available in this environment` non-interactive-mode detector, 2026-06-23 /advisor Opus 4.8 case).
- **`references/drift-aware-steer-recipe.md`** — "worker is already on it" verification-first pattern with drift-detection (PR body vs code grep) + dual-channel steer (PR comment for detail + short cmux send as pointer). Verified 2026-06-24 driving the daily-GCP-slack-alerts work through `workspace:70 "daily jobs + deploy"`.
- **`scripts/cmux_client.py`** — minimal Python socket client (rpc helper).
- **Companion skill:** `test-tui-claude-feature-via-cmux` (`~/.claude/skills/test-tui-claude-feature-via-cmux/`) — domain-specific test recipe built on cmux; ships `scripts/test-tui-feature.sh` wrapper + 6/6 unit tests. **Load this skill when the user asks "does /feature work" rather than re-deriving the cmux recipe from scratch each time.**
- **Companion skill:** `repo-top5-audit-and-dispatch` (`~/.hermes_prod/skills/devops/repo-top5-audit-and-dispatch/`), reference `references/2026-06-25-workstream-scope-completeness-audit.md` — the "are those all the PRs related to X?" multi-keyword `gh search prs` sweep + live-GitHub cross-check recipe, used after this cmux sub-pattern to verify each PR the screen recap mentioned.
- Upstream contract: <https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/cli-contract.md>
- Upstream skill: <https://raw.githubusercontent.com/manaflow-ai/cmux/main/skills/cmux/SKILL.md>
