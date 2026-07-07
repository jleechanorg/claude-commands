# cmux surfaces: `screencapture` cannot see hidden terminal surfaces

**Observed:** 2026-06-09, on socket `/private/tmp/cmux-debug-may-18.sock`,
cmux DEV may-18 build.

## Symptom

You ask `screencapture -x -T 0 -o /tmp/shot.png` to capture proof that a
Claude Code session running in cmux workspace:32 is showing version 2.1.170
and the Fable 5 banner. The PNG is saved (3456x2234, full screen, ~13 MB).
You open it expecting to see the cmux window with terminal text. Instead
you see the macOS desktop wallpaper — browns/greens of the default Big Sur
wallpaper, with the macOS menu bar at the top showing "cmux DEV may-18".

OCR of the screenshot returns only:
```
© cmuxDEVmay-18 File Edit View Update Pill Notifications Debug Window Help
```
No terminal text at all.

## Root cause (corrected 2026-06-09 after further investigation)

**The agent process running this session does NOT have macOS Screen Recording TCC permission.**

Confirmed by independent tools on the same machine:
```
$ peekaboo permissions
Screen Recording (Required): Not Granted
Accessibility (Required): Granted

$ peekaboo image --app "cmux DEV may-18" --mode window --window-title "fable-test"
Error: Screen recording permission is required. Please grant it in
System Settings > Privacy & Security > Screen Recording.

$ peekaboo bridge status
Selected: local (in-process) — no remote bridge hosts
```

When Screen Recording is denied, macOS returns a wallpaper-only or
"blank" capture from `screencapture`, `peekaboo image`, and any other
screen-capture tool. The earlier diagnosis ("cmux surfaces report
`visible=0 hidden=1`") is a DOWNSTREAM symptom, not the root cause.
The cmux debug-terminals check was a red herring — `screencapture`
returns wallpaper for ALL windows, not just hidden ones.

**To fix:** Open System Settings → Privacy & Security → Screen
Recording, add the agent's parent app (Hermes/Claude/whatever is
spawning the agent shell), then restart the agent. After that,
`peekaboo image` and `screencapture` will return the actual window
contents and a visual screenshot becomes possible.

The cmux-side state (what `cmux debug-terminals` reports) was:

```
visible=0 inWindow=0 hidden=1
```

The cmux Ghostty-backed terminal surfaces are not being drawn to the display,
even though:
- `osascript` reports the cmux app is `frontmost=true`
- The window is `AXStandardWindow` and visible
- The window title is correct (e.g., "fable-test")
- `cmux select-workspace` was called before capture
- `osascript click at {860, 300}` and `cliclick c:860,300` were tried —
  window `focused` stayed `false` throughout
- `cmux trigger-flash` + `cmux refresh-surfaces` did not change the hidden state
- `cmux` wrapper's `claude` function and the actual TUI banner ARE the right
  version, the user just can't see the rendered output via screen capture

This is a known cmux/Ghostty rendering quirk: the surfaces exist and have
content (in their terminal buffer), but the macOS window backing is not
compositing them. `screencapture` therefore captures the desktop wallpaper
showing through any transparent window region.

## Workaround: prove via `read-screen`, not via screenshot

`cmux read-screen` reads the **terminal buffer** directly via the cmux
socket. It does NOT depend on window focus or screen rendering. The output
includes the full session text:

```bash
$ export CMUX_SOCKET_PATH=/private/tmp/cmux-debug-may-18.sock
$ cmux read-screen --workspace workspace:32 --surface surface:153 --scrollback --lines 60
Last login: Tue Jun  9 10:04:19 on ttys091
$USER@Mac:~/projects_other/user_scope$ cd /tmp && claude --version
2.1.170 (Claude Code)
$USER@Mac:/tmp$ claude "do you see fable? ..."
 ▐▛███▜▌   Claude Code v2.1.170
▝▜█████▛▘  Sonnet 4.6 with high effort · Claude Max
  ▘▘ ▝▝    /private/tmp
...
⏺ Yes. The system context includes:
  ▎ "The most recent Claude models are Fable 5 and the Claude 4.X family.
     Model IDs — Fable 5: claude-fable-5, Opus 4.8: claude-opus-4-8, ..."
```

This proves the version AND the model's response without ever needing a
visual screenshot. The user wanted visual proof, but the read-screen
transcript + a clear "this is the buffer, not a screenshot" caveat is
the most honest deliverable.

## If you actually need a visual screenshot (corrected 2026-06-09)

The original diagnosis said the cmux window needed `focused=true` and
recommended clicking. That was wrong. The real fix is to grant Screen
Recording permission to the agent's parent app in macOS System Settings.

After permission is granted, the following all work without any user
interaction:

```bash
peekaboo image --app "cmux DEV may-18" --mode window \
  --window-title "fable-test" --path /tmp/cmux-fable.png

# Or full screen
screencapture -x /tmp/screen.png

# Or scoped to the cmux window region
screencapture -R 0,178,3442,1836 /tmp/cmux-window.png
```

The focus/click workarounds below are NOT needed once Screen Recording
is granted. They were the wrong tree to bark up.

---

(Original focus-related workarounds, kept for reference but no longer
the recommended path:)

The cmux window MAY need `focused=true` for the surfaces to be drawn.
None of the following reliably forced focus on 2026-06-09:

- `osascript click at {cx, cy}` (window center)
- `cliclick c:860,300`
- `tell application "cmux DEV may-18" to activate`
- `cmux trigger-flash --workspace workspace:32`
- `cmux refresh-surfaces`
- Pressing Space (ASCII 32) via `keystroke`

The only reliable way found was for the user to **manually click the cmux
window on their own display** to give it focus, then re-screenshot. Without
that, `screencapture` shows wallpaper.

## Rule: never claim a screenshot proves something until you inspect it

After taking a screencapture, you MUST do at least one of:
- Open the PNG and check brightness / pixel distribution (PIL)
- Run `tesseract` on it and read the OCR text
- Use the macOS Vision framework via Swift to describe the image
- Run `cmux read-screen` instead and use the buffer transcript

If the screenshot is mostly empty / wallpaper / the menubar only, do NOT
send the file as `MEDIA:` and claim it shows the terminal. Send the
read-screen transcript instead and label it as a buffer capture.

## Related

- `~/.hermes_prod/skills/cmux/SKILL.md` — main cmux skill
- `~/.hermes_prod/skills/claude-code-installation/SKILL.md` — Claude Code
  install/version verification, including the "Fable 5" model check
- `~/.hermes_prod/skills/cmux/scripts/cmux_client.py` — Python wrapper
  for send+submit+verify
