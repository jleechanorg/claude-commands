---
name: mp4-caption-burn
version: 1.1.0
description: |
  Capture screen activity to a captioned MP4 video — the full pipeline from
  screen-recording to a publishable, captioned video. Triggers when the user
  asks for "captioned MP4 proof", "MP4 with subtitles", "screen recording
  with captions", "video walkthrough", "show me a video", or any request that
  names MP4 + captions/subtitles/burned-in-text as the deliverable. Class-level
  skill: covers screen capture (macOS screencapture with window-scoped capture
  via CGWindowID), frame selection, ffmpeg drawtext caption burn (with its
  parser pitfalls), h264 encoding, and the verification loop (vision_analyze
  on extracted frames).

  Anti-trigger: plain-text transcripts (use a markdown/code-block skill).
  Anti-trigger: GIF animations (use the gif-search or p5js skills — different
  pipeline). Anti-trigger: asciinema recordings (use asciinema + agg, not
  MP4). Anti-trigger: video editing from existing footage (use manim-video
  or ffmpeg directly without going through this skill's capture pipeline).
metadata:
  hermes:
    tags: [video, ffmpeg, screen-recording, mp4, drawtext, captions, proof]
    verified: "2026-07-16 v1.1.0 -- two reference runs: v1.0.0 initial: 935 frames @ 2fps full-screen, 1920x1240, 58s, 3.6 MiB, SHA-256 4825b98d0aff1e659b43f6db5c3ac6d7b936363072f8854e34252de9e281ed57 -- user called out that the underlying footage was the cmux IDE, not the Terminal where the work ran. v1.1.0 fix: 145 frames @ 2fps window-scoped (screencapture -l 443), 1280x770, 75s, 930 KiB, SHA-256 e0338b4108c9b8051a3e8b011eea49321e076fd20d7d30c85de03877eb21909a -- Terminal-only footage matching captions."
---

# MP4 caption-burn pipeline

End-to-end recipe: macOS screen recording → frame selection → ffmpeg drawtext caption burn → h264 MP4 → verification via vision_analyze on extracted frames.

## When to use

When the user wants a **publishable video** with text captions burned in (not separate SRT files, not YouTube auto-captions, not open-captioned VTT). Common phrasings:

- "give me a captioned MP4 / video walkthrough / screen capture with labels"
- "show me /es-level proof" (often paired with `/es`-style proof requirements)
- "burn subtitles into the video"
- "produce a demo video"
- "make a captioned demo" / "step-by-step video"

The end deliverable is an MP4 file that **renders inline in Slack and GitHub PRs without external captions** — viewers see the text in the video itself.

## When NOT to use

- The user wants raw screen recording without captions (use macOS QuickTime or `screencapture -V` directly).
- The user wants GIFs (different pipeline; use p5js or terminal-record).
- The user has a video they want to add captions to later (use ffmpeg drawtext directly with `subtitles=...` filter, not this full pipeline).
- The "video" is a single still image with text overlay (use vision_analyze + image_generate, not MP4).
- The user wants auto-generated captions from speech (use Whisper → SRT → ffmpeg, not drawtext).

## The pipeline — 6 stages

### Stage 1 — Record screen at 2fps via macOS `screencapture`

**Use the macOS built-in `screencapture` CLI in a tight loop, NOT QuickTime.** QuickTime's CLI requires UI prompts; `screencapture -x -t png -C` runs silently.

**Pitfall 1.0 — full-screen captures include whatever background is behind the foreground app, and users WILL notice.** When your work is happening in one Terminal pane inside a larger IDE/agent UI, `-x -C` (full screen) captures the dominant window (your IDE) and only a sliver of the Terminal. The user will watch a captioned MP4 whose underlying footage is unrelated screens. Symptom: "That demo is wrong, it's not related to what i asked for" (Cloud Build E2E re-capture, 2026-07-16). The fix is **window-scoped capture**, not full-screen:

```bash
# 1. Discover the target window's CGWindowID via Swift.
#    System Events "id of window" fails (-1728); use Quartz directly.
#    Helper script in this skill: scripts/list-window-ids.swift
#      swift scripts/list-window-ids.swift                 # default: Terminal
#      swift scripts/list-window-ids.swift "Google Chrome" # any owner name
#    Inline if you prefer (or if the helper is unavailable):
#
swift - <<'EOF'
import Cocoa; import CoreGraphics
let info = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
for i in info {
  if (i[kCGWindowOwnerName as String] as? String) == "Terminal" {
    print(i[kCGWindowNumber as String] as? Int ?? 0)
  }
}
EOF
# Output: 443

# 2. Capture ONLY that window, no other apps visible:
screencapture -x -l 443 -t png "$PROOF_DIR/frame_$(printf '%05d' $n).png"
```

Why this matters: the captioned MP4's value comes from the *underlying footage matching the captions*. If captions say "HAND-OFF to cloud.superpowers.build" and the screen shows IDE panes, the video is misleading regardless of how nice the captions look. Re-record before posting — never post a video you haven't vision-verified against the actual work it claims to document.

**Pitfall 1.1 — `$(date)` doesn't expand inside double-quoted heredoc commands.** If you build the loop with `frame_$(date +%s%N).png`, the literal `$()` is captured by bash because of single-quote context. Use `printf '%05d'` or a counter variable.

```bash
PROOF_DIR="$HOME/cb-demo/proof"
mkdir -p "$PROOF_DIR"
n=0
# Window-scoped (clean capture of single app, no background bleed):
#   screencapture -x -l <CGWindowID> -t png "<out>"
# Full-screen (legacy, bleeds in background apps):
#   screencapture -x -t png -C "<out>"
while true; do
  screencapture -x -l 443 -t png "$PROOF_DIR/frame_$(printf '%05d' $n).png"
  n=$((n+1))
  sleep 0.5   # 2fps
done
```

**Pitfall 1.2 — the screencap will pollute git status** if the project dir is a git repo. Add the proof dir to `.gitignore` BEFORE starting, or use `~/...` outside the repo. Verified: 935 screencap frames at 2fps = 7.8 min of screen at 1.8 GiB total before downsampling.

**Pitfall 1.3 — `screencapture` requires Screen Recording permission** on macOS Mojave+. First run will fail silently. Open System Settings → Privacy & Security → Screen Recording, grant your terminal. Re-run the loop.

**Pitfall 1.4 — `screencapture -l <CGWindowID>` captures the wrong (or empty) window when the window ID changes.** CGWindowIDs are volatile across app reactivation, focus changes, and `cmd-w` close/reopen. Re-fetch the ID via the Swift snippet above immediately before the demo run. If the capture starts producing blank frames (size ~1 MB but only the window chrome, no content), the window ID is stale — re-run the discovery script. Verify a single frame with `vision_analyze` before committing to a 90s capture.

### Stage 2 — Downsample frames

2fps is fine for proof but burns disk fast. For a ~2 min capture, keep 1 in every 4 frames (≈30s of video). Use symlinks (not copies) to save disk:

```bash
SRC="$HOME/cb-demo/proof"
DST="$HOME/cb-demo/proof/video_src"
rm -rf "$DST"; mkdir -p "$DST"
i=0
for src in $(ls "$SRC"/frame_*.png | sort); do
  if [ $((i % 4)) -eq 0 ]; then
    ln -sf "$src" "$DST/f$(printf '%05d' $i).png"
  fi
  i=$((i+1))
done
```

### Stage 3 — Build the caption timeline

Decide which caption appears at which time. Keep each caption's text to **alphanumeric + spaces + hyphens only**. See Pitfall 3.1.

```python
captions = [
    (0.0, 5.0,  "STEP 1 / 6 - DOWNLOAD"),
    (5.0, 11.0, "STEP 2 / 6 - STATIC REVIEW"),
    ...
]
```

For 2fps video, frame N corresponds to time N/2. For longer videos (>1 min), downsample to 1fps and rewrite the timestamps.

### Stage 4 — ffmpeg drawtext, per-segment + concat

**Pitfall 4.1 — ffmpeg's drawtext filter parser treats ANY text matching an option name as an option key.** Symptom: `Error applying option 'state' to filter 'drawtext': Option not found` when your caption text contains the literal word `state`. Same trap for `enable`, `time`, `rate`, `text`, `font`, `color`, etc. — any string that matches a known drawtext option name. Fix: **avoid all drawtext option names in your caption text**. Replace `state=done` with `DONE`, `enable` with `on`, `text` with `caption`, etc.

**Pitfall 4.2 — `:` inside `text='...'` is parsed as an option separator.** `text='RESULT: DONE'` triggers the same option-parser failure because the parser sees `RESULT` as a key and ` DONE` as the value. Fix: replace `:` with `-` or ` - `. Or build the filter via `-filter_complex_script <file>` (see Stage 5) where the parser is more lenient.

**Pitfall 4.3 — the giant `-vf` chain with all drawtext instances in one ffmpeg invocation often fails for non-obvious reasons** (the literal-text collisions above are the common case, but there are other parser quirks). The reliable pattern is **one drawtext per ffmpeg invocation, then concat**:

```bash
font_path="/System/Library/Fonts/Helvetica.ttc"
font_size=42
seg_dir="$HOME/cb-demo/proof/segs"
mkdir -p "$seg_dir"

for i in "${!captions[@]}"; do
  IFS=' ' read -r start end text <<< "${captions[$i]}"
  s_idx=$((start * 2))    # 2fps
  e_idx=$((end * 2 - 1))
  sub_dir="$seg_dir/seg$i"
  mkdir -p "$sub_dir"
  for j in $(seq "$s_idx" "$e_idx"); do
    [ -f "$DST/f$(printf '%05d' $j).png" ] && \
      ln -sf "$DST/f$(printf '%05d' $j).png" "$sub_dir/f$(printf '%05d' $j).png"
  done
  vf="drawtext=fontfile=${font_path}:text='${text}':fontsize=${font_size}:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=18:x=(w-text_w)/2:y=h-th-50"
  ffmpeg -y -framerate 2 -i "$sub_dir/f%05d.png" \
    -vf "$vf" -c:v libx264 -pix_fmt yuv420p \
    -preset veryfast -crf 26 -r 2 "$seg_dir/seg$i.mp4"
done
```

### Stage 5 — Concat + downscale

```bash
concat_list="$seg_dir/concat.txt"
for i in "${!captions[@]}"; do
  echo "file 'seg$i.mp4'" >> "$concat_list"
done
ffmpeg -y -f concat -safe 0 -i "$concat_list" \
  -c copy -movflags +faststart "$HOME/cb-demo/proof/cb-demo.mp4"

# Downscale for posting
ffmpeg -y -i "$HOME/cb-demo/proof/cb-demo.mp4" \
  -vf "scale=1920:1240" -c:v libx264 -preset veryfast -crf 28 \
  -pix_fmt yuv420p -movflags +faststart "$HOME/cb-demo/proof/cb-demo-small.mp4"
```

**Pitfall 5.1 — Retina displays produce 3456×2234 frames at full resolution.** That's 7.7 MPx per frame. Without `-vf scale=1920:1240`, the MP4 is 30+ MiB and unwieldy for Slack threads / PR comments. Downscale before posting.

**Pitfall 5.2 — `-c copy` on the concat demuxer requires all segments to have identical codec, resolution, framerate, pix_fmt.** If one segment fails to encode (Stage 4 fallback path leaving the caption off), the concat will fail with "Non-monotonous DTS" or similar. Verify each segment MP4 plays independently before concat.

### Stage 6 — Verify with vision_analyze

Extract 3-5 frames at known caption-time boundaries and run vision_analyze to confirm the captions actually appear in the rendered MP4:

```bash
out_dir="$HOME/cb-demo/proof/verify_frames"
mkdir -p "$out_dir"
for t in 3 15 30 42 55; do
  ffmpeg -y -ss "$t" -i "$HOME/cb-demo/proof/cb-demo-small.mp4" \
    -frames:v 1 -q:v 2 "$out_dir/frame_t$(printf '%02d' $t).jpg"
done
```

Then call `vision_analyze(image_url=<each_path>, question="What text caption is visible at the bottom? Is it the exact caption I expected?")`.

**This is mandatory.** ffmpeg returns exit 0 even when drawtext silently no-ops (e.g. the filter was parsed but text was empty due to the option-name collision). The only ground truth is the rendered pixels.

## Pitfalls summary

| Pitfall | Symptom | Fix |
|---|---|---|
| Vision-verify passes but user complains "wrong demo" | Full-screen screencapture captured the dominant background window (IDE / cmux panes), not the Terminal where the work ran. Captions say HAND-OFF but screen shows unrelated panes | Re-capture with `screencapture -l <CGWindowID>` per Pitfall 1.0; re-vision-verify. Never post without confirming the footage matches the captions' claims |
| `screencapture -l` produces blank/empty frames | Stale `CGWindowID` — IDs change across focus events and `cmd-w` close/reopen | Re-run the Swift discovery script right before capture; verify one frame via `vision_analyze` before committing to a long capture |
| `$(date)` not expanding in screencap loop | All frames named `frame_$(date +%s%N).png` literally | Use `printf '%05d' $n` with a counter variable |
| Screencap frames polluting git status | Untracked `.png` files in the project dir | Add `proof/` to `.gitignore` BEFORE starting; or run from `~/...` outside any repo |
| `screencapture` permission denied | No frames captured, exit 0 with empty output | Grant Screen Recording in System Settings → Privacy & Security |
| drawtext `Error applying option 'state'` | The literal word `state` (or any drawtext option name) appears in your caption text | Replace with a synonym: `state` → `DONE`, `enable` → `on`, `time` → `minute`, etc. |
| drawtext `Error parsing filterchain` | Caption text contains `:` | Replace `:` with `-` or ` - ` |
| Concat "Non-monotonous DTS" | One segment failed to encode | Run each `seg$i.mp4` independently; the failed one will be much shorter than expected. Re-encode or remove it. |
| MP4 is 30+ MiB | No downscale applied | Add `-vf "scale=1920:1240"` to the final encode |
| vision_analyze shows wrong caption | The drawtext filter ran but on the wrong segment | Verify the `s_idx` / `e_idx` math: `start * 2` and `end * 2 - 1` for 2fps video |

## Posting the MP4

Once you have a small MP4, follow the `evidence-attach-to-slack` skill (v1.10+) for the post path. On the jleechanai.slack.com workspace both bot and xoxp tokens lack `files:write` (verified 2026-07-16), so the canonical path is **gist clone-and-replace → gist raw URL → embed in chat.postMessage with `unfurl_media: true`**. The gist raw URL serves `content-type: application/octet-stream` for MP4 — Slack still renders inline because the URL unfurler detects `.mp4` from the extension.

## End-to-end reference run (verified 2026-07-16)

Cloud Build E2E proof:
- 935 screencap frames @ 2fps captured during install + enroll + hand-off + status polling + land
- Downsampled to 233 frames (1 in 4) → 116s raw video
- 8 caption segments (DOWNLOAD → STATIC REVIEW → TEST REPO → INSTALL → RUN → LIBRARY-DRIVEN → RESULT DONE → PROOF)
- Output: 1920×1240, h264, 58s, 3.6 MiB
- SHA-256: `4825b98d0aff1e659b43f6db5c3ac6d7b936363072f8854e34252de9e281ed57`
- Gist: https://gist.github.com/jleechan2015/77dd5406ec125ccb2a916c3a98787a4a
- Slack thread: C09GRLXF9GR / ts=1784230762.399999
- vision_analyze confirmed all 8 caption segments burned in correctly

Total elapsed time: ~5 min for capture + ~3 min for encode + ~1 min for upload + post.