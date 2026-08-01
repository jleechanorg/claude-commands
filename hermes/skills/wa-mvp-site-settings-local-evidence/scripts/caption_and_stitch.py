"""
Burn step captions onto each PNG frame, then stitch into a captioned MP4
via ffmpeg concat (NOT ffmpeg drawtext — colons in PR URLs confuse the
filter parser).

Usage:
  $HOME/worldarchitect-main-origin/venv/bin/python caption_and_stitch.py \
      --frames /tmp/pr8512_proof/frames \
      --out /tmp/pr8512_proof/pr8512_proof.mp4
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT = ImageFont.truetype(FONT_PATH, 26)
FONT_SMALL = ImageFont.truetype(FONT_PATH, 18)


def caption(src_path: Path, dst_path: Path, big: str, small: str, footer: str) -> None:
    img = Image.open(src_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Top banner
    band_h = 90
    draw.rectangle([(0, 0), (W, band_h)], fill=(0, 0, 0))
    bbox1 = draw.textbbox((0, 0), big, font=FONT)
    tw1 = bbox1[2] - bbox1[0]
    draw.text(((W - tw1) / 2, 12), big, fill=(255, 255, 255), font=FONT)

    bbox2 = draw.textbbox((0, 0), small, font=FONT_SMALL)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((W - tw2) / 2, 52), small, fill=(255, 212, 0), font=FONT_SMALL)

    # Bottom PR stamp
    bbox3 = draw.textbbox((0, 0), footer, font=FONT_SMALL)
    tw3 = bbox3[2] - bbox3[0]
    draw.rectangle([(0, H - 36), (W, H)], fill=(255, 212, 0))
    draw.text(((W - tw3) / 2, H - 30), footer, fill=(0, 0, 0), font=FONT_SMALL)

    img.save(dst_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True, help="dir containing 0[1-9]_*.png frames")
    ap.add_argument("--out", required=True, help="output .mp4 path")
    ap.add_argument("--footer", default="$GITHUB_REPOSITORY  |  PR #8512  |  feat/gemini-3-5-flash-lite-3-6-flash")
    ap.add_argument("--fps", type=int, default=1, help="frames per second (1 = 1 sec per frame)")
    args = ap.parse_args()

    frames_dir = Path(args.frames)
    out_path = Path(args.out)
    captioned_dir = out_path.parent / "captioned"
    captioned_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(frames_dir.glob("*.png"))
    assert pngs, f"no PNGs found in {frames_dir}"

    for i, f in enumerate(pngs, start=1):
        big = f"Step {i}/{len(pngs)}: {f.stem}"
        small = f"Captured at PR HEAD: {args.footer}"
        caption(f, captioned_dir / f.name, big, small, args.footer)
        print("captioned", f.name)

    # Build ffmpeg concat list with explicit durations
    concat_list = out_path.parent / "concat_list.txt"
    with open(concat_list, "w") as cl:
        for f in pngs:
            cl.write(f"file 'captioned/{f.name}'\n")
            cl.write(f"duration {args.fps}\n")
        # Last file must be repeated (ffmpeg concat quirk)
        cl.write(f"file 'captioned/{pngs[-1].name}'\n")

    # ffmpeg concat. Height must be divisible by 16 for libx264.
    # Full-page screenshot of 1280x1809 fails; use 1280:1808.
    import subprocess
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-vf", "scale=1280:1808,setsar=1,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-r", "30",
        "-movflags", "+faststart",
        str(out_path),
    ]
    print("ffmpeg:", " ".join(cmd))
    rc = subprocess.run(cmd, capture_output=True, text=True)
    print(rc.stdout[-500:] if rc.stdout else "")
    if rc.returncode != 0:
        print("FFMPEG STDERR:", rc.stderr[-1500:])
        raise SystemExit(rc.returncode)
    print(f"DONE: {out_path} ({out_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
