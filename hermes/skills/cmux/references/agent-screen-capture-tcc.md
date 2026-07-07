# Agent screen capture on macOS — the TCC permission trap

**Class:** any task where the agent (Hermes / Claude / OpenClaw /
launchd-spawned shell / etc.) needs to capture the user's screen
(`screencapture`, `peekaboo image`, browser screenshots, etc.) and the
capture silently returns wallpaper / a blank image / a file that looks
normal but contains none of the target content.

**One-liner root cause:** the agent process does not have macOS
**Screen Recording** TCC permission. Capture tools either fail
loudly (`peekaboo image` returns a `PERMISSION_ERROR_SCREEN_RECORDING`
error) or — worse — fail silently and write a wallpaper PNG to the
output path.

## Quick diagnostic (always run first)

```bash
peekaboo permissions
```

Expected output when working:
```
Source: local runtime
Screen Recording (Required): Granted
Accessibility (Required): Granted
```

If `Screen Recording` shows `Not Granted`, **stop**. Do not try
click/focus/window-targeting workarounds. They will not work. The
capture will be wallpaper no matter which window, region, or app you
target. The TCC denial is a process-level grant, not a per-window
one.

## Two failure modes

### Mode A: loud failure
```
$ peekaboo image --app "cmux DEV may-18" --mode window
Error: Screen recording permission is required. Please grant it in
System Settings > Privacy & Security > Screen Recording.

$ peekaboo image --app "cmux DEV may-18" --mode window --window-title "fable-test" --path /tmp/peek-fable.png
[exit code 1, no file written]
```

`peekaboo` is well-behaved: it refuses to write a fake file.

### Mode B: silent failure (the dangerous one)
```
$ screencapture -x /tmp/shot.png
# exit code 0
$ ls -l /tmp/shot.png
-rw-r--r--  1 $USER  staff  13582976 Jun  9 10:14 /tmp/shot.png
# 13.5 MB — looks legit. Open it. It's wallpaper.
$ file /tmp/shot.png
/tmp/shot.png: PNG image data, 3456 x 2234, 8-bit/color RGBA, non-interlaced
# Resolution and depth look normal. But the content is the macOS desktop
# wallpaper showing through a transparent region of the target window.
```

`/usr/sbin/screencapture` does not validate that it actually captured
the target — it writes whatever the WindowServer gave it. With Screen
Recording denied, the WindowServer returns the desktop composition
(background wallpaper) for any capture. The file size and resolution
match what you'd expect, which makes this trap especially nasty.

**Verification recipe after every capture:**
1. Open the PNG and check the content is what you expect, OR
2. `tesseract /tmp/shot.png - 2>/dev/null | head -20` — should contain
   your target text, not just the macOS menu bar, OR
3. `python3 -c "from PIL import Image; im=Image.open('/tmp/shot.png');
   im.crop((100,100,300,300)).save('/tmp/probe.png')"` and check the
   crop. Wallpaper crops look like brown/green/blue noise.

If the OCR returns only "File Edit View Window Help" or the crop is
solid background color, the capture is wallpaper. Re-verify permissions
and recapture.

## How to fix

1. Open **System Settings → Privacy & Security → Screen Recording**
2. Click the `+` to add an app
3. Navigate to the agent's parent app and add it
   - Hermes-agent runtime → `/Applications/Antigravity.app` or
     whatever wraps the agent
   - Hermes/Claude CLI shells → `/Applications/Claude.app` or the
     launching terminal
   - Launchd-spawned scripts → the script's parent process (rare; you
     may need to manually pick `/usr/bin/zsh` or `/bin/bash`)
4. Toggle the entry **on**
5. **Restart the agent process** — TCC grants do not apply to
   already-running processes
6. Re-run `peekaboo permissions` to confirm `Granted`

## Bridge alternative — when you cannot grant permission

If you cannot or should not grant Screen Recording to the agent's
parent app (e.g., shared kiosk machine, production environment),
`peekaboo` can route through a **bridge host** — a different
already-granted app that exposes its TCC-privileged context over a
Unix socket. Probe order:

```bash
peekaboo bridge status --verbose
# Tries: Peekaboo.app, Claude.app, Clawdis.app, then local in-process
```

If `Claude.app` is running and has Screen Recording granted, peekaboo
will route the capture through it. If none of the bridge candidates
have the grant, the only option is to grant the agent itself.

Observed 2026-06-09: `Claude.app` was installed but only the
`chrome-native-host` helper was running (no main process), so the
bridge socket was absent (`No such file or directory` for
`~/Library/Application Support/Claude/bridge.sock`).

## pre-TCC proof alternatives

For proof that does not need Screen Recording:

- **Terminal buffer proof** (cmux, tmux, iTerm, etc.):
  `cmux read-screen --workspace $ws --surface $surf --scrollback --lines 60`
  — reads the terminal buffer via the cmux/socket, no TCC needed.
- **CLI output proof** for any tool:
  just run the tool, capture stdout/stderr to a file, OCR or quote.
- **File content proof**:
  `cat`, `head`, `xxd` the file directly. No display needed.
- **API proof**:
  curl the data and inspect. No display needed.

Label any such deliverable clearly as "buffer proof" or "CLI proof",
NOT a "screenshot". The user asked for a screenshot for a reason —
visual review, sharing, evidence chain — and a buffer transcript is a
weaker substitute. They deserve to know.

## The cmux-specific trap on top of the TCC trap

Even after TCC is granted, cmux workspaces can still produce
"wallpaper-looking" captures for a different reason: cmux's
Ghostty-backed terminal surfaces occasionally report
`visible=0 inWindow=0 hidden=1` to `cmux debug-terminals` even when
the window is frontmost. In that case the WindowServer composes the
window background but not the terminal glyphs.

The diagnostic order is:
1. `peekaboo permissions` first — if Not Granted, fix TCC and stop
2. After TCC is Granted, if capture still shows wallpaper, run
   `cmux debug-terminals` and check surface state
3. If surfaces report hidden, do NOT try to focus/click the window
   (it does not help). Instead, use `cmux read-screen` for buffer
   proof and note the rendering quirk in the deliverable

## System Settings / System Preferences windows are also TCC-blocked (verified 2026-06-23, PR #7848)

**The TCC blocker is not specific to cmux.** macOS marks **any window whose app is not in the Screen Recording whitelist** as `kCGWindowSharingState=0`, and `screencapture` returns wallpaper for those windows. This includes:
- The cmux window itself (per the section above).
- **System Settings (System Preferences) windows** — including the
  Privacy & Security → Screen Recording pane the user opens to fix
  the grant. Verified 2026-06-23: after `screencapture -x /tmp/sys.png`,
  the captured PNG was the macOS desktop wallpaper, not the System
  Settings window that was frontmost at the time. The vision-analysis
  call on the PNG saw only the desktop background, not the actual
  Privacy & Security list.
- Any 3rd-party app the agent's process does not have explicit TCC for.

**Implication for the diagnostic loop:** you cannot verify a TCC fix
succeeded by capturing the System Settings window. The right verification
chain is:
1. **Tell the user the exact TCC path they need to grant** (the
   caller's binary path, not "Terminal" — see the cmux SKILL.md
   Visual Screenshot of cmux Window section).
2. **Have the user confirm via Slack/Slack-thread that they toggled
   the entry on and relaunched the caller.** This is the only
   verification that works when the System Settings window is itself
   TCC-blocked.
3. **Run `peekaboo permissions` in the next capture attempt** to
   confirm `Screen Recording: Granted` programmatically — this
   itself does not require capturing a window.

**Don't burn 5+ capture attempts on System Settings itself** —
each attempt returns wallpaper, and you'll go in circles. State the
blocker once, give the user the one-time manual fix, and pivot to
buffer/text proof. Bug-ref 2026-06-23 (PR #7848): burned 4 screencapture
attempts on System Settings before realizing the privacy pane was itself
TCC-blocked; the actual grant state had to be confirmed by user-side
toggle + relaunch, not by agent-side capture.

## Related

- `references/screencapture-failure-2026-06-09.md` — the original
  2026-06-09 trace that motivated this file (and that originally
  misdiagnosed the root cause as a cmux surface state issue)
- `~/.hermes_prod/skills/claude-code-installation/SKILL.md` — uses
  `cmux read-screen` for model/version verification proof
- `~/.hermes_prod/skills/cmux/SKILL.md` — main cmux skill, includes
  the inline "screencapture Returns Wallpaper" warning that points
  here
