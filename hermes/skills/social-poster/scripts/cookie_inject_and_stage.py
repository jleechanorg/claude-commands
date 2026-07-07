#!/usr/bin/env python3
"""
cookie_inject_and_stage.py — Use Aside's decrypted cookies to log into each
social platform in a headless Playwright Chrome, navigate to the compose URL,
paste the draft, and screenshot.

NEVER clicks submit/post. Just stages for human review.

Usage:
  python3 cookie_inject_and_stage.py --drafts /tmp/drafts/social-test-001/
"""
import argparse
import asyncio
import base64
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse


PLATFORMS = {
    "linkedin":          "https://www.linkedin.com/feed/?shareActive=true",
    "twitter":           "https://twitter.com/compose/post",
    "threads":           "https://www.threads.net/@$USER",
    "facebook":          "https://www.facebook.com/",
    "devto":             "https://dev.to/new",
    "reddit_localllama": "https://old.reddit.com/r/LocalLLaMA/submit?selftext=true",
    "reddit_rag":        "https://old.reddit.com/r/Rag/submit?selftext=true",
    "reddit_openai":     "https://old.reddit.com/r/OpenAI/submit?selftext=true",
    "instagram":         "https://www.instagram.com/",
}

# Paste JavaScript recipes — each receives a window + draft, returns "PASTED" / "NO_EDITOR" / "NO_TEXTAREA"
PASTE_RECIPES = {
    "linkedin": """
        const editor = document.querySelector('[data-test-emoji-input]')
                    || document.querySelector('.ql-editor[contenteditable="true"]')
                    || document.querySelector('div[contenteditable="true"][role="textbox"]');
        if (!editor) return 'NO_EDITOR';
        editor.focus();
        editor.innerHTML = DRAFT_TEXT.split('\\n').map(line => '<p>' + line + '</p>').join('');
        editor.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: 'x' }));
        return 'PASTED';
    """,
    "twitter": """
        const ta = document.querySelector('textarea[data-testid="tweetTextarea"]')
                || document.querySelector('[aria-label="Post text"]');
        if (!ta) return 'NO_TEXTAREA';
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(ta, DRAFT_TEXT);
        ta.dispatchEvent(new Event('input', { bubbles: true }));
        return 'PASTED';
    """,
    "hackernews": """
        const titleInput = document.querySelector('input[name="title"]');
        const textArea = document.querySelector('textarea[name="text"]');
        if (!titleInput) return 'NO_TITLE_INPUT';
        const setVal = (el, v) => {
            const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, v);
            el.dispatchEvent(new Event('input', { bubbles: true }));
        };
        setVal(titleInput, TITLE_TEXT);
        if (textArea) setVal(textArea, BODY_TEXT);
        return 'PASTED';
    """,
    "threads": """
        const editor = document.querySelector('[contenteditable="true"][data-lexical-editor]')
                    || document.querySelector('[contenteditable="true"]');
        if (!editor) return 'NO_EDITOR';
        editor.focus();
        editor.innerHTML = DRAFT_TEXT.split('\\n').map(line => '<p>' + line + '</p>').join('');
        editor.dispatchEvent(new InputEvent('input', { bubbles: true }));
        return 'PASTED';
    """,
    "facebook": """
        const editor = document.querySelector('[aria-label*="Create a post"]')
                    || document.querySelector('[contenteditable="true"][role="textbox"]')
                    || document.querySelector('div[contenteditable="true"]');
        if (!editor) return 'NO_EDITOR';
        editor.focus();
        editor.innerHTML = DRAFT_TEXT.split('\\n').map(line => '<p>' + line + '</p>').join('');
        editor.dispatchEvent(new InputEvent('input', { bubbles: true }));
        return 'PASTED';
    """,
    "devto": """
        const titleInput = document.querySelector('input[name="title"]')
                        || document.querySelector('#article_title');
        const bodyTextarea = document.querySelector('textarea[name="body_markdown"]')
                          || document.querySelector('#article_body_markdown');
        const setVal = (el, v) => {
            const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, v);
            el.dispatchEvent(new Event('input', { bubbles: true }));
        };
        if (titleInput && TITLE_TEXT) setVal(titleInput, TITLE_TEXT);
        if (bodyTextarea && BODY_TEXT) setVal(bodyTextarea, BODY_TEXT);
        return 'PASTED';
    """,
    "mastodon": """
        const ta = document.querySelector('textarea#status-emoji-picker')
                || document.querySelector('[data-behavior="auto_resize"]')
                || document.querySelector('textarea[name="status[text]"]');
        if (!ta) return 'NO_TEXTAREA';
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(ta, DRAFT_TEXT);
        ta.dispatchEvent(new Event('input', { bubbles: true }));
        return 'PASTED';
    """,
    "reddit": """
        // We arrived at ?selftext=true so the text form is already shown
        await new Promise(r => setTimeout(r, 1000));
        const setVal = (el, v) => {
            const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, v);
            el.dispatchEvent(new Event('input', { bubbles: true }));
        };
        const titleField = document.querySelector('textarea[name="title"]')
                        || document.querySelector('input[name="title"]');
        const bodyField = document.querySelector('textarea[name="text"]')
                      || document.querySelector('textarea[name="body"]')
                      || document.querySelector('textarea[name="description"]');
        if (titleField) setVal(titleField, TITLE_TEXT);
        if (bodyField) setVal(bodyField, BODY_TEXT);
        return (titleField ? 'TI' : 'NO_TI') + '|' + (bodyField ? 'BT' : 'NO_BT');
    """,
}


def extract_title_and_body(draft_md: str, platform: str) -> tuple[str | None, str]:
    if platform in ("hackernews", "reddit", "devto") or platform.startswith("reddit_"):
        m_title = re.search(r"^## Title\s*\n\n(.+?)\n", draft_md, re.MULTILINE)
        m_body = re.search(r"^## Body\s*\n\n(.+)$", draft_md, re.MULTILINE | re.DOTALL)
        title = m_title.group(1).strip() if m_title else None
        body = m_body.group(1).strip() if m_body else draft_md
        return (title, body)
    return (None, draft_md)


def main():
    ap = argparse.ArgumentParser(description="Inject cookies + stage drafts")
    ap.add_argument("--drafts", required=True, help="Drafts dir")
    ap.add_argument("--cookies", default="/tmp/social-cookies/chrome.json")
    ap.add_argument("--only", default="", help="Comma-separated platform allowlist")
    args = ap.parse_args()

    drafts_dir = Path(args.drafts).expanduser().resolve()
    cookies_path = Path(args.cookies).expanduser().resolve()
    screenshots_dir = drafts_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    if not cookies_path.exists():
        print(f"ERROR: cookies not found: {cookies_path}")
        return 1

    cookies = json.loads(cookies_path.read_text())["cookies"]
    manifest_path = drafts_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found")
        return 1
    manifest = json.loads(manifest_path.read_text())
    only_set = set(p.strip() for p in args.only.split(",") if p.strip()) if args.only else None

    results = {}

    for key, compose_url in PLATFORMS.items():
        if only_set and key not in only_set:
            continue
        if key in ("mastodon", "hackernews", "instagram"):
            # No cookies for these in Aside
            results[key] = {"status": "skipped", "reason": "no session in Aside cookies"}
            continue

        print(f"\n→ {key} :: {compose_url}")

        # Find the draft file
        draft_path = drafts_dir / f"{key}.md"
        if not draft_path.exists():
            results[key] = {"status": "draft_missing"}
            continue

        draft_md = draft_path.read_text()
        title, body = extract_title_and_body(draft_md, key)
        # For platforms that paste the full text
        full_draft = body if not title else body

        # Run Playwright via subprocess
        # Use Python str.format with double braces {{ }} for any literal { in the embedded script.
        script_src = textwrap.dedent("""\
            import asyncio, json, sys
            from pathlib import Path
            from urllib.parse import urlparse
            from playwright.async_api import async_playwright

            async def main():
                cookies_raw = json.load(open('__COOKIES_PATH__'))['cookies']
                goto = '__COMPOSE_URL__'
                platform = '__PLATFORM__'
                title = __TITLE_JSON__
                body = __BODY_JSON__
                full_draft = body if not title else body
                paste_js = __PASTE_JS_JSON__
                empty_shot = '__EMPTY_SHOT__'
                pasted_shot = '__PASTED_SHOT__'

                paste_js = paste_js.replace('DRAFT_TEXT', json.dumps(full_draft))
                if title:
                    paste_js = paste_js.replace('TITLE_TEXT', json.dumps(title))
                if body:
                    paste_js = paste_js.replace('BODY_TEXT', json.dumps(body))

                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True, channel='chrome')
                    ctx = await browser.new_context(
                        viewport={'width': 1440, 'height': 900},
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    )
                    goto_host = urlparse(goto).netloc
                    filtered = []
                    for c in cookies_raw:
                        cdomain = c['domain'].lstrip('.')
                        if cdomain == goto_host or goto_host.endswith('.' + cdomain) or cdomain.endswith('.' + goto_host):
                            filtered.append(c)
                    await ctx.add_cookies(filtered)
                    page = await ctx.new_page()
                    try:
                        await page.goto(goto, wait_until='domcontentloaded', timeout=30000)
                    except Exception as e:
                        print(f'GOTO_ERR:{e}'); await browser.close(); return
                    await asyncio.sleep(4)
                    Path(empty_shot).parent.mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path=empty_shot, full_page=False)
                    # Wrap paste_js in an async IIFE so 'await' works
                    wrapped = '(async () => { ' + paste_js + ' })()'
                    result = await page.evaluate(wrapped)
                    await asyncio.sleep(2)
                    await page.screenshot(path=pasted_shot, full_page=False)
                    print(f'RESULT:{result}')
                    await browser.close()
            asyncio.run(main())
        """)
        # Substitute placeholders
        script = (
            script_src
            .replace("__COOKIES_PATH__", str(cookies_path))
            .replace("__COMPOSE_URL__", compose_url)
            .replace("__PLATFORM__", key)
            .replace("__TITLE_JSON__", "None" if not title else json.dumps(title))
            .replace("__BODY_JSON__", "None" if not body else json.dumps(body))
            .replace("__PASTE_JS_JSON__", json.dumps(PASTE_RECIPES.get("reddit" if key.startswith("reddit_") else key, "")))
            .replace("__EMPTY_SHOT__", str(screenshots_dir / f"{key}_empty.png"))
            .replace("__PASTED_SHOT__", str(screenshots_dir / f"{key}_pasted.png"))
        )

        try:
            r = subprocess.run([sys.executable, "-c", script],
                               capture_output=True, text=True, timeout=60)
            out = (r.stdout or "") + (r.stderr or "")
            m = re.search(r"RESULT:(\w+)", out)
            paste_result = m.group(1) if m else "unknown"
            print(f"  paste: {paste_result}")
            if r.returncode != 0 and "RESULT:" not in out:
                # Show last 20 lines of stderr for debugging
                lines = [l for l in out.split("\n") if l.strip()]
                print(f"  last 3 lines: {lines[-3:] if len(lines) >= 3 else lines}")
            empty_bytes = (screenshots_dir / f"{key}_empty.png").stat().st_size if (screenshots_dir / f"{key}_empty.png").exists() else 0
            pasted_bytes = (screenshots_dir / f"{key}_pasted.png").stat().st_size if (screenshots_dir / f"{key}_pasted.png").exists() else 0
            results[key] = {
                "status": "staged",
                "compose_url": compose_url,
                "empty_screenshot": str(screenshots_dir / f"{key}_empty.png"),
                "pasted_screenshot": str(screenshots_dir / f"{key}_pasted.png"),
                "empty_bytes": empty_bytes,
                "pasted_bytes": pasted_bytes,
                "paste_result": paste_result,
            }
        except subprocess.TimeoutExpired:
            results[key] = {"status": "timeout"}
        except Exception as e:
            results[key] = {"status": "error", "error": str(e)[:200]}

    manifest["cookie_inject_results"] = results
    manifest["cookie_inject_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2))

    ok = sum(1 for r in results.values() if r.get("status") == "staged")
    fail = sum(1 for r in results.values() if r.get("status") not in ("staged", "skipped"))
    print(f"\n\n✓ Staged: {ok}  ✗ Failed: {fail}")
    for k, r in results.items():
        print(f"  {k}: {r.get('status')} paste={r.get('paste_result', 'n/a')}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())