# cmux CLI Cheatsheet

**Last verified:** 2026-06-23 on current cmux build (debug socket: `/tmp/cmux-debug-may-18.sock`). Added `cmux capture-pane --pane pane:N` row — verified working without workspace/surface args.
Source of truth: <https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/cli-contract.md>.
Run `cmux docs api` or `cmux <command> --help` to confirm against your local build.

## Global flags

| Flag | Notes |
| --- | --- |
| `--json` | **NOT a global flag.** Per-command only — works on `identify`, `top`, `list-workspaces`, `auth status`, `ssh-session-list`, etc. |
| `--id-format <refs\|uuids\|both>` | Display format. `both` is the most useful for scripting + human eyes. |
| `--window <id\|ref\|index>` | Route through a specific window when supported. |
| `--socket <path>` | Override socket path. |
| `--password <value>` | Explicit socket password (takes precedence over `CMUX_SOCKET_PASSWORD`). |

## Environment

| Var | Purpose |
| --- | --- |
| `CMUX_SOCKET_PATH` | Canonical socket path override (used by Python client). |
| `CMUX_SOCKET` | Deprecated alias for `CMUX_SOCKET_PATH`. |
| `CMUX_SOCKET_PASSWORD` | Password fallback. |
| `CMUX_WORKSPACE_ID` | Default workspace for in-app terminals. |
| `CMUX_SURFACE_ID` | Default surface for in-app terminals. |
| `CMUX_TAB_ID` | Default tab for tab commands. |

## Discovery

| Command | Purpose |
| --- | --- |
| `cmux list-workspaces` | All workspaces. Add `--id-format both` for UUIDs. |
| `cmux list-windows` | All windows. |
| `cmux current-window` | Selected window ref. |
| `cmux tree --all` | Full window → workspace → pane → surface tree (with tty + focus state). |
| `cmux list-panes --workspace <w>` | Panes in a workspace. |
| `cmux list-pane-surfaces --workspace <w> --pane <p>` | Surfaces in a pane. |
| `cmux identify [--workspace <w> --surface <s>]` | Caller context + focused surface. Returns the actual `socket_path`. |
| `cmux read-screen --workspace <w> --surface <s> [--scrollback --lines N]` | Read terminal text. **`--scrollback --lines N` is the recipe for seeing what a session is doing.** |
| `cmux capture-pane [--workspace <w>] [--surface <s>] [--pane <p>] [--window <win>] [--lines N] [--scrollback] [--json]` | tmux-style capture. Accepts `--pane pane:N` directly (no surface resolution) — faster than `read-screen` because it skips the focus-then-read path. Verified 2026-06-23 (misroute triage on `workspace:8` pane `pane:44`): `cmux capture-pane --pane pane:44 --lines 80 --scrollback` returned the Claude Code `/clarify` menu + 80 lines of scrollback in one call, no `--workspace` or `--surface` needed. **Important:** calling `cmux capture-pane` with NO positional args dumps CLI help text instead of pane content — always pass at least one of `--pane`, `--surface`, `--workspace`, or `--window`. Use `--pane` when you only know the pane; use `--surface` when you know the surface directly. **`--json` returns a structured envelope** with `text` (same as plain output), `base64` (raw bytes — useful for binary-safe round-trip), and `surface_id` / `surface_ref` (UUID + `surface:N` form). Best for "is this worker doing what I think" audit — pipe through `python3 -c "import json,sys; d=json.load(sys.stdin); print(d['text'])"` to get the same text as plain output, with metadata for audit. Verified 2026-06-23 (PR #7848 fastembed steering): captured Opus worker state including long-form reasoning without re-typing. |
| `cmux surface-health [--workspace <w> --surface <s>]` | Terminal surface health. |
| `cmux capabilities` | Server capabilities JSON. |
| `cmux events [--name <name>] [--limit N]` | Stream events. **Can block — set a timeout.** |
| `cmux top` | Per-window/workspace/pane/surface resource usage. |
| `cmux ping` | Socket liveness. |

## Workspace / window control

| Command | Purpose |
| --- | --- |
| `cmux new-workspace` | Create. `--cwd <path>`, `--command <cmd>`, `--description <text>`. |
| `cmux select-workspace --workspace <id>` | Focus. |
| `cmux close-workspace --workspace <id>` | Close. |
| `cmux rename-workspace --workspace <id> "name"` | Rename. |
| `cmux reorder-workspace --workspace <id> --index N` | Move position. |
| `cmux workspace-action --action <name> --workspace <id>` | Context-menu actions: `pin`, `unpin`, `rename`, `clear-name`, `set-description`, `clear-description`, `move-up/down/top`, `close-others/above/below`, `mark-read/unread`, `set-color`, `clear-color`. |
| `cmux move-workspace-to-window --workspace <id> --window <id>` | Cross-window. |
| `cmux open <path-or-url> [--workspace <id>]` | Open path/URL in a workspace. |
| `cmux ssh user@host [-A]` | SSH-backed workspace. |
| `cmux new-window` / `cmux focus-window --window <id>` / `cmux close-window --window <id>` | Window ops. |
| `cmux window displays` / `cmux window display <name\|index>` / `cmux window default-display [<name>\|--clear]` | Display routing. |

## Panes & surfaces

| Command | Purpose |
| --- | --- |
| `cmux new-split --workspace <w> --surface <s> <direction>` | New split (direction: `left`/`right`/`up`/`down`). |
| `cmux new-pane --workspace <w> --surface <s> terminal\|browser` | New pane. |
| `cmux new-surface --workspace <w> --pane <p> terminal\|browser` | New surface in pane. |
| `cmux focus-pane --workspace <w> --pane <p>` | Focus pane. |
| `cmux close-surface --workspace <w> --surface <s>` | Close surface. |
| `cmux move-surface --workspace <w> --surface <s> --to-workspace <w2>` | Move. |
| `cmux split-off --workspace <w> --surface <s> <direction>` | Move to a new split. |
| `cmux reorder-surface ...` | Reorder within pane. |
| `cmux drag-surface-to-split ...` | Drag-style move. |
| `cmux move-tab-to-new-workspace` | Move tab. |
| `cmux tab-action --action <name> ...` | Tab context menu: `rename`, `clear-name`, `close-left/right/others`, `new-terminal-right`, `new-browser-right`, `reload`, `duplicate`, `pin`, `unpin`, `mark-unread`. |

## Input (steering)

| Command | Purpose |
| --- | --- |
| `cmux send --workspace <w> --surface <s> "text"` | Type text. **Does NOT auto-press Enter.** |
| `cmux send-key --workspace <w> --surface <s> <key>` | Press a key. Keys: `enter`, `tab`, `escape`, `backspace`, `delete`, `up`, `down`, `left`, `right` (and more — see `--help`). |
| `cmux respawn-pane` | Restart the command in a surface. |

To execute a command in a terminal: `cmux send ... "ls -la" && cmux send-key ... enter`. For
Claude Code sessions, prefer `cmux send ... "your message" && cmux send-key ... enter` and
then verify with `cmux read-screen ... --scrollback --lines 30` to see the spinner / churn
label appear.

## Sidebar & notifications

| Command | Purpose |
| --- | --- |
| `cmux notify --title "T" --body "B" [--workspace <w>]` | Create notification. |
| `cmux list-notifications` | List queued. |
| `cmux dismiss-notification [--all-read]` | Dismiss. |
| `cmux mark-notification-read` | Mark read. |
| `cmux open-notification` / `cmux jump-to-unread` | Focus the notification's surface. |
| `cmux clear-notifications` | Clear all. |
| `cmux set-status <key> "<value>"` / `cmux clear-status <key>` / `cmux list-status` | Sidebar status pills. |
| `cmux set-progress <0.0-1.0> --label "..."` / `cmux clear-progress` | Progress bar. |
| `cmux log "msg" --level info\|warn\|error` / `cmux clear-log` / `cmux list-log` | Log entries. |
| `cmux sidebar-state` | Dump all sidebar state. |
| `cmux right-sidebar ...` | Visibility / mode / focus. |

## Hooks & agent integration

| Command | Purpose |
| --- | --- |
| `cmux hooks setup [--agent <name>]` | Install hooks for all/specific agents. |
| `cmux hooks uninstall [--agent <name>]` | Remove. |
| `cmux hooks <agent> <event>` | Per-agent hook event. |
| `cmux hooks feed --source <agent>` | Convert agent events to Feed context. |
| `cmux feed tui` / `cmux feed clear` | Keyboard-first Feed TUI / clear history. |
| `cmux browser <subcommand>` | Browser automation (open, goto, snapshot, click, type, eval, screenshot, etc.). |
| `cmux claude-teams [args]` / `cmux codex-teams [args]` / `cmux omo [args]` / `cmux omx [args]` / `cmux omc [args]` | Agent team launchers. |

## System

| Command | Purpose |
| --- | --- |
| `cmux ping` | Socket liveness. |
| `cmux version` | Version. |
| `cmux capabilities` | Server features. |
| `cmux identify` | Context. |
| `cmux auth <status\|login\|logout>` | Auth. |
| `cmux rpc <method> [json-params]` | Raw socket call. |
| `cmux config <doctor\|check\|validate\|path\|paths\|docs\|reload>` | Config validation. |
| `cmux settings <open\|path\|docs\|target>` | Settings. |
| `cmux reload-config` | Hot-reload Ghostty + cmux.json. |
| `cmux restore-session` | Restore last session. |
| `cmux disable-browser` / `cmux enable-browser` / `cmux browser-status` | Browser interception. |
| `cmux agent-hibernation` | Enable/disable hibernation. |
| `cmux themes <list\|set\|clear>` | Ghostty themes. |
| `cmux feedback [--email ... --body ... [--image ...]]` | Send feedback. |

## Common mistakes (do NOT do these)

- `cmux list-surfaces` — does not exist. Use `tree --all` or `list-pane-surfaces`.
- `cmux --json list-workspaces` — `--json` is not global. Per-command: `cmux list-workspaces --json` does work.
- `cmux --workspace 10 --surface 19 read-screen` — flags after the subcommand: `cmux read-screen --workspace 10 --surface 19`.
- `cmux send-surface --surface 19 "ls"` — `send-surface` does not exist. Use `cmux send --workspace <w> --surface 19 "ls"`.
- `cmux new-split right` — needs workspace + surface context. Use `cmux new-split --workspace <w> --surface <s> right`.
- Assuming `cmux send` presses Enter. It does not. Always follow with `cmux send-key enter` for command execution.
- `cmux select-workspace --workspace 5` is **NOT** `workspace:5` — the bare integer is a positional
  index (sorted by tab order, not by ref number), and the index list isn't sorted by ref.
  Verified 2026-06-13: `--workspace 5` returned `OK workspace:12` (the workspace at index 5 in
  tab order), silently misrouting. Use the explicit ref form `--workspace workspace:5`, or
  look up the ref first with `cmux list-workspaces --id-format both`. Full trap + always-works
  recipe: see `references/workspace-routing-trap.md`.

## Socket path reality

The "default" socket at `/tmp/cmux.sock` is **a legacy assumption**. Real cmux builds create
debug sockets with build-date suffixes (e.g. `/tmp/cmux-debug-may-18.sock`). Always run
`cmux identify` and read the `socket_path` field before pointing a raw socket client at it.
The `cmux` CLI itself figures this out automatically — only the Python client needs the
override.
