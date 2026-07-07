#!/usr/bin/env python3
"""
stage_in_aside.py — Open Aside browser tabs for each draft + screenshot.

Reads drafts from --drafts dir (output of draft_social_post.py), opens an Aside
tab on each platform's compose URL, takes a screenshot, and saves it under
screenshots/.

DOES NOT click submit / post. Just stages for human review.

Updated 2026-07-06:
- Reddit compose URL now uses ?selftext=true (lands on text-post form, avoids
  session-re-auth redirect that misclassified Reddit as "login wall").
- Aside `openTab()` returns a Playwright Page object; we screenshot via the
  Page's `screenshot()` method (Buffer → base64) rather than the older
  `annotatedScreenshot(pageObj)` API. Both still work; the Buffer path is
  simpler and less prone to null-snapshot errors.
- Adds `aside_inspect()` for DOM triage via `page.evaluate()`. NOTE: per
  SKILL.md lesson #8, DOM-only detection is unreliable — always vision-verify
  screenshots before declaring any platform compose-ready.

Aside REPL API used (verified 2026-07-06):
  openTab(url)             -> Playwright Page object
  page.screenshot()        -> Buffer (PNG bytes)
  page.waitForLoadState()  -> Promise<void>
  page.evaluate(fn, ...args) -> Promise<json-serializable>
  page.locator(selector)   -> Locator (Playwright)
  page.frameLocator(selector) -> FrameLocator (for iframe clicks)
  listBrowserTabs()        -> Promise<[{url, title, ...}]>
  closeTab(target)         -> Promise

Usage:
  python3 stage_in_aside.py --drafts /tmp/drafts/social-2026-07-06/
  python3 stage_in_aside.py --drafts /tmp/drafts/social-2026-07-06/ --close-tabs
"""
import argparse
import base64
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Compose URLs (mirror of post_approved.py — kept in sync)
# NOTE: Reddit compose URL MUST end with ?selftext=true to land on the text-post
# form. Without it, old.reddit defaults to the link-post tab, which navigates
# through "link vs text" UI and triggers a session-re-auth redirect that LOOKS
# like a login wall in screenshots. Verified 2026-07-06.
COMPOSE_RECIPES = {
    "linkedin": "https://www.linkedin.com/feed/?shareActive=true",
    "linkedin_short": "https://www.linkedin.com/feed/?shareActive=true",
    "hackernews": "https://news.ycombinator.com/submit",
    "twitter": "https://twitter.com/compose/post",
    "threads": "https://www.threads.net/@$USER",
    "facebook": "https://www.facebook.com/",
    "mastodon": "https://mastodon.social/publish",
    "devto": "https://dev.to/new",
    "instagram": "https://www.instagram.com/",  # no compose — surface caption only
}


def aside_repr(code: str, timeout: int = 60) -> str:
    """Run an aside repl snippet, return stdout+stderr."""
    try:
        r = subprocess.run(
            ["aside", "repl", code],
            capture_output=True, text=True, timeout=timeout,
        )
        return (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except FileNotFoundError:
        return "[ASIDE_NOT_FOUND]"


def aside_screenshot(compose_url: str, screenshot_path: Path, timeout: int = 60) -> dict:
    """
    Open compose_url in Aside, take a screenshot, save to screenshot_path.

    Uses the verified Playwright Page-object pattern (2026-07-06):
    openTab(url) -> page; page.waitForLoadState('domcontentloaded'); sleep 4500ms
    to let JS-driven UI mount; page.screenshot() returns a Node Buffer; encode
    as base64 and emit via console.log('B64:...'); decode here.
    """
    code = (
        f"const p = await openTab({json.dumps(compose_url)}); "
        "await p.waitForLoadState('domcontentloaded'); "
        "await new Promise(r => setTimeout(r, 4500)); "
        "const shot = await p.screenshot(); "
        "console.log('B64:' + shot.toString('base64'));"
    )
    try:
        r = subprocess.run(
            ["aside", "repl", code],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "aside timeout"}
    except FileNotFoundError:
        return {"ok": False, "error": "aside CLI not found"}

    out = (r.stdout or "") + (r.stderr or "")
    if "[ASIDE_NOT_FOUND]" in out:
        return {"ok": False, "error": "aside CLI not found"}

    # Find B64: marker
    m = re.search(r"B64:([A-Za-z0-9+/=]+)", out)
    if not m:
        err = next((l.strip() for l in out.split("\n") if l.strip() and "✔" not in l), "(no output)")
        return {"ok": False, "error": err[:200]}

    b64 = m.group(1)
    try:
        png_bytes = base64.b64decode(b64)
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        screenshot_path.write_bytes(png_bytes)
        return {"ok": True, "bytes": len(png_bytes), "path": str(screenshot_path)}
    except Exception as e:
        return {"ok": False, "error": f"base64 decode failed: {e}"}


def aside_inspect(compose_url: str, timeout: int = 30) -> dict:
    """
    Inspect the page via page.evaluate() to check auth state.

    Returns the post-evaluate JSON state (url, username, has_compose_field, etc.).
    Used by callers that want to know whether the page is a compose form or a
    login wall WITHOUT trusting the screenshot alone.

    NOTE: Per SKILL.md lesson #8, DOM-only detection is unreliable — always
    vision-verify the screenshot before declaring a platform compose-ready.
    This function is a quick triage, not the final answer.
    """
    code = (
        f"const p = await openTab({json.dumps(compose_url)}); "
        "await p.waitForLoadState('domcontentloaded'); "
        "await new Promise(r => setTimeout(r, 4000)); "
        "const state = await p.evaluate(() => ({ "
        "  url: window.location.href, "
        "  title: document.title, "
        "  username: document.querySelector('a#me, [data-testid=\"AppTabBar_Profile_Link\"]')?.textContent ?? null, "
        "  has_compose_field: !!(document.querySelector('div[contenteditable=\"true\"]') || "
        "    document.querySelector('textarea[name=\"text\"]') || "
        "    document.querySelector('input[name=\"title\"]') || "
        "    document.querySelector('[data-testid=\"tweetTextarea_0\"]')), "
        "  shows_login_prompt: /log in|sign in|welcome back/i.test(document.body.innerText), "
        "})); "
        "console.log('STATE' + ' ' + JSON.stringify(state));"
    )
    try:
        r = subprocess.run(
            ["aside", "repl", code],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "aside timeout"}
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"STATE\s+(\{.*?\})", out)
    if m:
        try:
            return {"ok": True, **json.loads(m.group(1))}
        except Exception as e:
            return {"ok": False, "error": f"json parse failed: {e}"}
    return {"ok": False, "error": out[-200:]}


def stage_platform(platform_key: str, compose_url: str, screenshot_path: Path,
                   draft_text: str = "", close_tabs: bool = False) -> dict:
    """
    Open a new Aside tab on compose_url, screenshot it, save PNG.

    NOTE: We do NOT paste the draft automatically. Doing so requires
    identifying the specific text-input element via snapshot+ref, which
    varies per platform (LinkedIn's contenteditable, HN's input, Twitter's
    textarea). For the draft-only review, the human sees:
      1. The draft text file (already written by draft_social_post.py)
      2. The empty compose tab in Aside
      3. The screenshot proving the compose UI is loaded
    They paste manually OR run an aside repl paste snippet from
    references/aside-recipes.md.
    """
    shot = aside_screenshot(compose_url, screenshot_path)
    inspect = aside_inspect(compose_url)
    result = {
        "status": "staged" if shot.get("ok") else "failed",
        "platform": platform_key,
        "compose_url": compose_url,
        "screenshot": shot.get("path"),
        "screenshot_bytes": shot.get("bytes"),
        "draft_chars": len(draft_text),
        "inspect": inspect,
    }
    if not shot.get("ok"):
        result["error"] = shot.get("error", "unknown")

    if close_tabs:
        # Best-effort close — silently ignore failures
        try:
            subprocess.run(
                ["aside", "repl", f"const t = await openTab({json.dumps(compose_url)}); await closeTab(t); console.log('closed');"],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pass

    return result


def stage_reddit(sub: str, draft_text: str, title: str, screenshot_path: Path,
                 close_tabs: bool = False) -> dict:
    # CRITICAL: ?selftext=true lands directly on the text-post compose form.
    # Without it, old.reddit defaults to the link-post tab, which navigates
    # through "link vs text" UI and triggers a session re-auth redirect that
    # LOOKS like a login wall in screenshots. Verified 2026-07-06 for
    # r/LocalLLaMA, r/OpenAI, r/Rag — all three compose forms loaded immediately
    # when this param was included. See SKILL.md lesson #7 and
    # references/aside-repl-playwright-pattern.md.
    compose_url = f"https://old.reddit.com/r/{sub}/submit?selftext=true"
    return stage_platform(f"reddit_{sub}", compose_url, screenshot_path,
                          draft_text=draft_text, close_tabs=close_tabs)


def main():
    ap = argparse.ArgumentParser(description="Stage drafts in Aside browser tabs + screenshot")
    ap.add_argument("--drafts", required=True, help="Draft dir (output of draft_social_post.py)")
    ap.add_argument("--close-tabs", action="store_true", help="Close tabs after screenshot")
    ap.add_argument("--only", default="", help="Comma-separated platform allowlist (skip others)")
    args = ap.parse_args()

    drafts_dir = Path(args.drafts).expanduser().resolve()
    if not drafts_dir.exists():
        print(f"ERROR: drafts dir not found: {drafts_dir}")
        return 1

    manifest_path = drafts_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found in {drafts_dir}")
        return 1

    manifest = json.loads(manifest_path.read_text())
    screenshots_dir = drafts_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    only_set = set(p.strip() for p in args.only.split(",") if p.strip()) if args.only else None

    # Aside health check
    health = aside_repr("console.log('ASIDE_OK')", timeout=10)
    if "[ASIDE_NOT_FOUND]" in health:
        print("ERROR: `aside` CLI not found. Install: curl -fsSL https://releases.aside.com/install.sh | bash")
        return 2
    print(f"✓ Aside alive: {health.strip().split(chr(10))[0][:50]}")

    # Stage each draft
    results = {}
    for fname in sorted(drafts_dir.glob("*.md")):
        key = fname.stem
        if key == "manifest":
            continue

        if only_set and key not in only_set:
            continue

        draft_text = fname.read_text()
        shot_path = screenshots_dir / f"{key}.png"

        if key.startswith("reddit_"):
            sub = key.replace("reddit_", "")
            print(f"\n→ Staging reddit/{sub}...")
            r = stage_reddit(sub, draft_text, "", shot_path, close_tabs=args.close_tabs)
            results[key] = r
        elif key == "instagram":
            print(f"\n→ Staging instagram (no web compose, screenshot home page)...")
            r = stage_platform("instagram", COMPOSE_RECIPES["instagram"], shot_path,
                               draft_text=draft_text, close_tabs=args.close_tabs)
            r["note"] = "Instagram has no web compose — copy caption from drafts/instagram.md and paste via mobile app"
            results[key] = r
        elif key in COMPOSE_RECIPES:
            print(f"\n→ Staging {key} ({COMPOSE_RECIPES[key]})...")
            r = stage_platform(key, COMPOSE_RECIPES[key], shot_path,
                               draft_text=draft_text, close_tabs=args.close_tabs)
            results[key] = r
        else:
            print(f"\n→ Skipping {key} (no recipe)")

    # Update manifest
    manifest["stage_results"] = results
    manifest["staged_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2))

    ok = sum(1 for r in results.values() if r.get("status") == "staged")
    fail = sum(1 for r in results.values() if r.get("status") != "staged")
    print(f"\n\n✓ Staged {ok} platforms, ✗ failed {fail}")
    print(f"✓ Screenshots in: {screenshots_dir}")
    for k, r in results.items():
        status = "✓" if r.get("status") == "staged" else "✗"
        size = r.get("screenshot_bytes", "?")
        inspect = r.get("inspect", {})
        # Quick triage marker — but ALWAYS vision-verify
        marker = ""
        if inspect.get("ok"):
            if inspect.get("has_compose_field") and not inspect.get("shows_login_prompt"):
                marker = " [DOM: compose-ready — vision-verify]"
            elif inspect.get("shows_login_prompt"):
                marker = " [DOM: login-wall — vision-verify]"
            else:
                marker = " [DOM: unclear — vision-verify]"
        print(f"  {status} {k}: {r.get('status')} ({size} bytes) {marker}")
    print(f"\n⚠ Always vision-verify the screenshots before declaring any platform compose-ready.")
    print(f"📋 REPLY WITH 'POST APPROVED' to post — or revise any draft first.")

    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())