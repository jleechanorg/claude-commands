# cmux TUI capture → PNG render pipeline (no Chrome, no TCC)

**Why this exists:** cmux's Electron app sets `sharing=0` (verified 2026-07-21). macOS `screencapture -l <window-id>` returns *"could not create image from window"*. `aside-mcp` browser tools capture browser rendering, not TUI overlays. Playwright + headless Chromium don't capture terminal content.

**Solution:** render the captured terminal text (via `cmux read-screen`) to PNG using PIL/Pillow. Headless by construction. No TCC, no focused window stolen, no Chrome needed.

## Pipeline

### 1. Capture text from cmux

```bash
export CMUX_SOCKET_PATH=$HOME/.local/state/cmux/cmux-501.sock
cmux read-screen --workspace workspace:<N> --surface surface:<M> --lines 60
```

The `--lines` flag controls how many lines back to read. The output is plain text with ANSI codes (escape sequences are stripped — the read-screen output is plain-text).

### 2. Save text to a file

```bash
cmux read-screen --workspace workspace:42 --surface surface:45 --lines 60 > /tmp/capture.txt
```

Or pipe through grep to filter just the picker section:
```bash
cmux read-screen ... | sed -n '/Select model/,/Esc to cancel/p' > /tmp/picker.txt
```

### 3. Render to PNG

Use `render_terminal_png.py` (saved at `~/Downloads/render_terminal_png.py`):

```python
from PIL import Image, ImageDraw, ImageFont
# 18-pt Menlo/Consolas/Monaco, JetBrains Mono preferred
# Picker rows: highlight cursor row with background color (60, 90, 140)
# Picker rows: highlight selected row with background color (40, 80, 120) + ✔ glyph
```

Invocation:
```bash
python3 ~/Downloads/render_terminal_png.py \
  --input /tmp/picker.txt \
  --output ~/Downloads/picker.png \
  --title "Claude Code v2.1.212 — /model picker (dual-model test)" \
  --cols 110 \
  --rows 16
```

### 4. Verify the PNG

```bash
file picker.png
# → PNG image data, 1348 x 419, 8-bit/color RGB, non-interlaced

# Sample colors at known cursor row positions to confirm highlights rendered:
python3 -c "
from PIL import Image
img = Image.open('picker.png')
# scan for non-background pixels
hits = {}
for y in range(img.height):
    for x in range(0, img.width, 50):
        c = img.getpixel((x, y))
        if c != (18, 18, 22):  # bg color
            hits[c] = hits.get(c, 0) + 1
print('unique non-bg colors:', len(hits))
"
```

## Rendering parameters

| Param | Default | Notes |
|---|---|---|
| `--cols` | 110 | Text width in characters |
| `--rows` | 16 | Number of text lines |
| `--font-size` | 16 | Pixel size of monospace font |
| `--padding` | 16 | Pixel padding around text |
| `--bg` | (18, 18, 22) | Background color (dark theme) |
| `--title` | "" | Title bar above text |
| `--highlight` | (60, 90, 140) | Cursor row bg color |
| `--selected` | (40, 80, 120) | Selected row bg color |

## Detecting cursor/selected rows

The picker uses two Unicode markers:
- `❯` (U+276F) — cursor position (always 1 line)
- `✔` (U+2714) — selected/default model (always 1 line)

In the renderer, scan each line for `❯` → highlight that row; for `✔` → highlight that row's last column with a different color.

## Picker-specific capture strategy

The cmux picker opens when you submit `/model` (the slash picker → Enter). After the picker overlay opens, you have a window of ~3-5 seconds before any timer/screen-blur kicks in. Capture immediately.

```bash
cmux send --workspace workspace:42 --surface surface:45 "/model"
sleep 1
cmux send-key --workspace workspace:42 --surface surface:45 enter
sleep 4
cmux read-screen --workspace workspace:42 --surface surface:45 --lines 30 \
  | sed -n '/Select model/,/Esc to cancel/p' > /tmp/picker.txt
```

## Alternatives considered (rejected)

| Method | Why rejected |
|---|---|
| `screencapture -l <window-id>` | cmux Electron app sets `sharing=0` → "could not create image from window" |
| Playwright + headless Chrome | TUI isn't a webpage; Chrome can't capture terminal content |
| `aside-mcp` browser_navigate | Same as Chrome — TUI isn't a webpage |
| `cmux read-screen --screenshot` (hypothetical) | cmux CLI doesn't expose this; only text |
| `vhs` / `terminalizer` | Recording tools, not screenshot tools; produce MP4/GIF not PNG |
| Native macOS `screencapture -i` (region) | Requires user interaction; not headless |

## When to fall back to this pipeline

The cmux TUI render pipeline is the **fallback** when:
- The user asks for "screenshot" of a TUI picker, modal, or interactive element
- Browser-based capture is impossible or restricted
- TCC / Screen Recording permissions are not granted
- The user explicitly says "headless" or "no Chrome window"

For browser/web content, use `aside-mcp` or Playwright MCP (per `browser-headless-default` skill).
