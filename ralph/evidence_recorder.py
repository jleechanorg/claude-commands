#!/usr/bin/env python3
"""Ralph Evidence Recorder — Browser Proof Video with Burned-In Captions.

Uses Python Playwright to record a WebM video of the webapp with visible
caption overlays burned directly into each frame. Also generates per-step
screenshots, an SRT file, and a markdown report.

Usage: python3 evidence_recorder.py [--url URL] [--evidence-dir DIR]
"""
import argparse, os, sys, time, urllib.request
from pathlib import Path

CAPTION_CSS = """
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 999999;
  background: rgba(0,0,0,0.85); color: #fff; font-family: 'SF Mono', monospace;
  font-size: 18px; padding: 12px 20px; text-align: center;
  border-top: 2px solid #ffd700;
"""

RESULT_CSS = """
  position: fixed; top: 0; right: 0; z-index: 999999;
  background: rgba(0,0,0,0.85); color: #fff; font-family: 'SF Mono', monospace;
  font-size: 14px; padding: 8px 16px; border-bottom-left-radius: 8px;
"""

def check_server(url: str) -> bool:
    try:
        urllib.request.urlopen(url, timeout=5)
        return True
    except Exception:
        return False

def show_caption(page, text, color="#ffd700"):
    """Inject a visible caption overlay into the page."""
    page.evaluate(f"""() => {{
        let el = document.getElementById('ralph-caption');
        if (!el) {{
            el = document.createElement('div');
            el.id = 'ralph-caption';
            el.style.cssText = `{CAPTION_CSS}`;
            document.body.appendChild(el);
        }}
        el.innerHTML = `<span style="color:{color};font-weight:bold">{text}</span>`;
    }}""")
    time.sleep(0.5)  # Let video capture the frame

def show_result(page, passed, total):
    """Show running pass/total counter in top-right."""
    pct = passed * 100 // total if total else 0
    page.evaluate(f"""() => {{
        let el = document.getElementById('ralph-result');
        if (!el) {{
            el = document.createElement('div');
            el.id = 'ralph-result';
            el.style.cssText = `{RESULT_CSS}`;
            document.body.appendChild(el);
        }}
        el.innerHTML = `✅ {passed}/{total} ({pct}%)`;
    }}""")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=f"http://localhost:{os.environ.get('RALPH_APP_PORT', '5555')}")
    ap.add_argument("--evidence-dir", default="/tmp/ralph-run/evidence")
    args = ap.parse_args()

    base_url = args.url
    edir = Path(args.evidence_dir)
    ssdir = edir / "screenshots"
    ssdir.mkdir(parents=True, exist_ok=True)
    (edir / "captions").mkdir(exist_ok=True)

    print("🎬 Ralph Browser Proof Recorder (with burned-in captions)")
    print(f"   URL: {base_url}")
    print(f"   Evidence: {edir}")
    print()

    if not check_server(base_url):
        print(f"❌ Server not reachable at {base_url}")
        sys.exit(1)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ playwright not installed (pip install playwright)")
        sys.exit(1)

    results = []
    srt_entries = []
    passed = 0
    total = 0
    sec = 0

    def mark(page, test_id, caption, ok):
        nonlocal passed, total, sec
        total += 1
        tag = "PASS" if ok else "FAIL"
        color = "#00ff88" if ok else "#ff4444"
        icon = "✅" if ok else "❌"
        if ok:
            passed += 1

        # Show result on page (burned into video)
        show_caption(page, f"{icon} [{total}] {test_id}: {caption}", color)
        show_result(page, passed, total)
        time.sleep(1.5)  # Show caption for 1.5s in video

        # Screenshot with caption visible
        ss_path = ssdir / f"browser_{total:02d}_{test_id}.png"
        page.screenshot(path=str(ss_path))

        # SRT + console output
        a, b = sec, sec + 3
        sec = b
        at = f"{a//3600:02d}:{a%3600//60:02d}:{a%60:02d},000"
        bt = f"{b//3600:02d}:{b%3600//60:02d}:{b%60:02d},000"
        print(f"  [{total}] {icon} {test_id}: {caption}")
        srt_entries.append(f"{total}\n{at} --> {bt}\n[{tag}] {test_id}: {caption}\n")
        results.append(f"| {total} | {test_id} | {caption} | {icon} |")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir=str(edir),
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        # --- INTRO CAPTION ---
        page.goto(base_url, timeout=15000)
        page.wait_for_load_state("domcontentloaded")
        show_caption(page, "🎬 RALPH BROWSER PROOF — Starting Tests", "#ffd700")
        time.sleep(2)

        # --- Test 1: Homepage loads ---
        show_caption(page, "📋 Test 1: Checking homepage...", "#87ceeb")
        time.sleep(1)
        try:
            title = page.title()
            ok = bool(title)
            mark(page, "HOMEPAGE", f"Homepage loads — title: {title}", ok)
        except Exception as e:
            mark(page, "HOMEPAGE", f"Failed: {e}", False)

        time.sleep(1)

        # --- Test 2: Page has content ---
        show_caption(page, "📋 Test 2: Checking page content...", "#87ceeb")
        time.sleep(1)
        try:
            count = page.locator("body *").count()
            mark(page, "CONTENT", f"Page has {count} elements", count > 5)
        except Exception as e:
            mark(page, "CONTENT", f"Element count failed: {e}", False)

        time.sleep(1)

        # --- Test 3: Full page screenshot ---
        show_caption(page, "📋 Test 3: Capturing full page...", "#87ceeb")
        time.sleep(1)
        try:
            page.screenshot(path=str(ssdir / "browser_fullpage.png"), full_page=True)
            mark(page, "FULLPAGE", "Full page screenshot captured", True)
        except Exception as e:
            mark(page, "FULLPAGE", f"Screenshot failed: {e}", False)

        time.sleep(1)

        # --- FINAL SUMMARY ---
        pct = passed * 100 // total if total else 0
        color = "#00ff88" if passed == total else "#ff4444"
        show_caption(page, f"📊 FINAL: {passed}/{total} ({pct}%) — {'ALL PASSED' if passed == total else 'SOME FAILED'}", color)
        show_result(page, passed, total)
        time.sleep(3)  # Hold final result for 3 seconds

        # Close and save video
        context.close()
        browser.close()

    # Rename video file (Playwright generates a random name)
    vids = sorted(edir.glob("*.webm"), key=lambda f: f.stat().st_mtime, reverse=True)
    video_path = None
    if vids:
        newest = vids[0]
        video_path = edir / "app_flow.webm"
        if video_path.exists() and video_path != newest:
            video_path.unlink()
        if newest != video_path:
            newest.rename(video_path)
        size_kb = video_path.stat().st_size / 1024
        print(f"  🎬 Video: {video_path} ({size_kb:.0f}KB)")

    # Write SRT
    srt_path = edir / "captions" / "browser_proof.srt"
    srt_path.write_text("\n".join(srt_entries))
    print(f"  📝 SRT: {srt_path}")

    # Write report
    pct = passed * 100 // total if total else 0
    report = edir / "browser_proof.md"
    report.write_text(
        f"# Browser Proof Report\n\n"
        f"**Date:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"**URL:** {base_url}\n"
        f"**Result:** {passed}/{total} ({pct}%)\n\n"
        f"| # | Test | Caption | Result |\n"
        f"|---|------|---------|--------|\n"
        + "\n".join(results) + "\n\n"
        f"**Video:** {video_path.name if video_path else 'not captured'}\n"
        f"**Captions:** Burned into video + SRT file\n"
    )
    print(f"  📋 Report: {report}")
    print(f"\n  📊 Result: {passed}/{total} ({pct}%)")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
