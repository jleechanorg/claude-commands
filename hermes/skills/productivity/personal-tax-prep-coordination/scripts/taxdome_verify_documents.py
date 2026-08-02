#!/usr/bin/env python3
"""TaxDome Documents verification — confirm uploads are queryable in folder list.

Why this exists: the `taxdome_upload_documents.py` script detects success
via the modal's "Done" button. That's an HTTP-POST-received signal from
the server, but it does NOT prove the file is queryable in the
"Client uploaded documents" subfolder later (which is what the user
will actually see). This script reads back the folder listing via
Playwright and prints every PDF found. Use it after a cron tick to
verify the upload actually persisted.

Usage:

    env -i HOME="$HOME" \\
        PATH="$HOME/.local/orch-venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \\
        PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" \\
        ~/.local/orch-venv/bin/python3 \\
        ~/.hermes/skills/productivity/personal-tax-prep-coordination/scripts/taxdome_verify_documents.py

Outputs the count and basenames to stdout; saves the full page text
to /tmp/tax2025/taxdome-verify-<timestamp>.txt and a screenshot to
/tmp/tax2025/shots/taxdome-verify-<timestamp>.png for diff-debug.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter

from playwright.sync_api import sync_playwright

COOKIES_JSON_DEFAULT = "/tmp/tax2025/cookies-taxdome-only.json"
DOCUMENTS_URL = "https://orenheneainc.taxdome.com/app/documents"


def to_pw_cookies(raw):
    out = []
    for c in raw:
        out.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
            "sameSite": c.get("sameSite", "Lax"),
        })
    return out


def main():
    cookies_path = os.environ.get("TAXDOME_COOKIES_JSON", COOKIES_JSON_DEFAULT)
    if not os.path.exists(cookies_path):
        print(f"missing cookies: {cookies_path}", file=sys.stderr)
        return 2
    with open(cookies_path) as f:
        cookies_raw = json.load(f)["cookies"]

    with sync_playwright() as pw:
        b = pw.chromium.launch(
            channel="chromium",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_cookies(to_pw_cookies(cookies_raw))
        p = ctx.new_page()

        # Walk: Documents root -> "Client uploaded documents" folder
        p.goto(DOCUMENTS_URL, timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)
        if "/login" in p.url or "/sign-in" in p.url:
            print("AUTH FAILED", file=sys.stderr)
            b.close()
            return 3

        # Try clicking into "Client uploaded documents" to list its contents
        try:
            p.locator('text=Client uploaded documents').first.click()
            time.sleep(3)
        except Exception as e:
            print(f"folder-click warn: {e}", file=sys.stderr)

        ts = int(time.time())
        text = p.text_content("body") or ""
        try:
            p.screenshot(
                path=f"/tmp/tax2025/shots/taxdome-verify-{ts}.png",
                full_page=True,
            )
        except Exception:
            pass
        with open(f"/tmp/tax2025/taxdome-verify-{ts}.txt", "w") as f:
            f.write(text)
        b.close()

    pdfs = re.findall(r'[\w\.\-\(\)/ ]+\.pdf', text)
    c = Counter()
    for p in pdfs:
        m = re.search(r'([\w\.\-\(\) ]+\.pdf)$', p.strip())
        if m:
            c[m.group(1)] += 1

    distinct = sum(1 for v in c.values() if v >= 1)
    duplicates = sum(v - 1 for v in c.values() if v > 1)
    print(f"Distinct PDFs: {distinct}   Duplicates: {duplicates}")
    for f, n in sorted(c.items()):
        marker = " (dup)" if n > 1 else ""
        print(f"  {n}x  {f}{marker}")

    print(f"\nFull text: /tmp/tax2025/taxdome-verify-{ts}.txt")
    print(f"Screenshot: /tmp/tax2025/shots/taxdome-verify-{ts}.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
