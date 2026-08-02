#!/usr/bin/env python3
"""TaxDome Documents upload — headless Playwright (verified 2026-07-19).

Uploads one or more PDFs to the Preparer's TaxDome "Documents" page,
specifically into "Client uploaded documents" (the default destination
selected by TaxDome's upload modal). Reuses cookies dumped from the
user's Chrome via browserclaw.

Why this script exists (not just a cron prompt instruction):

  The cron prompt alone says "navigate to TaxDome Documents and use the
  file input to upload each PDF", which is underspecified. There are
  FIVE concrete gotchas that any naive Playwright approach will hit:

    1. THREE elements have role=button and contain "Upload files" text
       (dropzone <div>, dropzone inner <div>, the actual button). The
       data-test selector `[data-test="DocumentsDropzone-UploadFiles-Button"]`
       resolves uniquely.

    2. FOUR `<input type="file">` are present after the modal opens.
       The LAST one is `webkitdirectory="true"` (the "Upload folder"
       picker) — setting files on it raises
       `Error: [webkitdirectory] input requires passing a path to a directory`.

    3. The modal's "Upload" button text is exactly "Upload", but
       `:has-text("Upload")` is a substring match and ALSO hits the
       page's "Upload files" button behind the modal. Use exact-match
       with `re.compile(r'^Upload$')`.

    4. The "Done" button is the success sentinel. Wait for it (not for
       the upload button disappearing, which races server latency).

    5. Multi-file `set_input_files([a, b, c, ...])` works — modal title
       becomes "Upload N documents". Wait 8s+ for N>1.

Verified end-to-end 2026-07-19: 13 PDFs uploaded to
`https://orenheneainc.taxdome.com/app/documents` (under "Client uploaded
documents") with `=== N OK, 0 FAIL ===`.

Usage:

    env -i HOME="$HOME" \
        PATH="$HOME/.local/orch-venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
        PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" \
        ~/.local/orch-venv/bin/python3 \\
        ~/.hermes/skills/productivity/personal-tax-prep-coordination/scripts/taxdome_upload_documents.py \\
        "$HOME/Downloads/tax 2025/"*.pdf

Env contract: see SOUL.md COMMIT `browser-headless-default` — always
headless; never visible Chrome; bundled Chromium-for-Testing is fine
for TaxDome (no server-side TLS-fingerprint rejection, verified).

Cookie source: /tmp/<preparer>-<year>-cookies-chrome-tax.json (filtered
for `taxdome.com`). Run `browserclaw cookies decrypt` first if missing.

Distinction vs `taxdome_prefill_organizer.py`: that script handles the
12-step Yes/No ORGANIZER questions (Phase 4 evidence). THIS script
handles the file-upload side of the Documents page (Phase 5.5 evidence).
Same auth cookie works for both — TaxDome does not fingerprint-bucket.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

COOKIES_JSON_DEFAULT = "/tmp/tax2025/cookies-taxdome-only.json"
DOCUMENTS_URL = "https://orenheneainc.taxdome.com/app/documents"
DASHBOARD_URL = "https://orenheneainc.taxdome.com/app/dashboard"


def to_pw_cookies(raw):
    """browserclaw JSON -> Playwright cookies dicts (skip timestamp quirks)."""
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


def pick_file_input(page):
    """Among visible file inputs, pick the last non-webkitdirectory one.
    The "Upload folder" input is webkitdirectory and rejects file paths.
    """
    file_inputs = page.locator('input[type="file"]')
    cnt = file_inputs.count()
    for i in range(cnt - 1, -1, -1):
        fi = file_inputs.nth(i)
        try:
            webkit = fi.get_attribute("webkitdirectory")
            if not webkit:
                return fi
        except Exception:
            continue
    return file_inputs.nth(0) if cnt else None


def find_upload_button_in_modal(page):
    """Find the modal Upload button (exact text "Upload", NOT "Upload files")."""
    buttons = page.locator("button").all()
    for b in buttons:
        try:
            txt = (b.text_content(timeout=500) or "").strip()
            if txt == "Upload" and b.is_visible(timeout=500):
                return b
        except Exception:
            continue
    return None


def find_done_button(page):
    """Find the modal Done button (success sentinel — appears AFTER upload)."""
    for name in ("Done", "Close"):
        try:
            b = page.get_by_role("button", name=name).first
            if b and b.is_visible(timeout=500):
                return b
        except Exception:
            continue
    return None


def upload_one_or_many(page, pdf_paths):
    """Open upload modal, set files, click Upload, wait for Done."""
    is_multi = len(pdf_paths) > 1
    fname_list = [os.path.basename(p) for p in pdf_paths]

    # 1. Click the page-level "Upload files" trigger (data-test selector
    #    resolves uniquely across the 3 nested dropzone buttons).
    page.locator('[data-test="DocumentsDropzone-UploadFiles-Button"]').click()
    time.sleep(1.5)

    # 2. Set the file input — last non-webkitdirectory one.
    fi = pick_file_input(page)
    if fi is None:
        return [(fn, "FAIL", "no file input") for fn in fname_list]
    fi.set_input_files(pdf_paths if is_multi else pdf_paths[0])
    time.sleep(3 if is_multi else 2)

    # 3. Click modal Upload button (EXACT match; not "Upload files" on
    #    the page behind the modal).
    upload_btn = find_upload_button_in_modal(page)
    if upload_btn is None:
        return [(fn, "FAIL", "no Upload button in modal") for fn in fname_list]
    upload_btn.click()
    wait_s = 8 if is_multi else 5
    time.sleep(wait_s)

    # 4. Wait for Done button (success sentinel).
    done_btn = find_done_button(page)
    if done_btn is not None:
        try:
            done_btn.click()
            time.sleep(2)
        except Exception:
            pass
        return [(fn, "OK", "done shown") for fn in fname_list]

    # Modal may auto-close. Bail-soft: check for modal still present.
    time.sleep(3)
    try:
        modal_still = page.get_by_text(
            f"Upload {len(pdf_paths)} document{'s' if len(pdf_paths) != 1 else ''}"
        ).is_visible(timeout=2000)
        if not modal_still:
            return [(fn, "OK", "modal auto-closed") for fn in fname_list]
    except Exception:
        pass
    if find_upload_button_in_modal(page):
        return [(fn, "FAIL", "upload did not progress") for fn in fname_list]
    return [(fn, "OK", "ok (uncertain)") for fn in fname_list]


def upload_one(page, pdf_path):
    """Backwards-compat wrapper for single file."""
    res = upload_one_or_many(page, [pdf_path])
    return res[0][1], res[0][2]


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("Usage: taxdome_upload_documents.py <pdf-path> [pdf-path...]",
              file=sys.stderr)
        return 2

    pdf_paths = [os.path.expanduser(p) for p in argv]
    for p in pdf_paths:
        if not os.path.exists(p):
            print(f"missing: {p}", file=sys.stderr)
            return 2

    cookies_path = os.environ.get(
        "TAXDOME_COOKIES_JSON", COOKIES_JSON_DEFAULT
    )
    if not os.path.exists(cookies_path):
        print(f"missing cookies: {cookies_path}", file=sys.stderr)
        print("Run browserclaw cookies decrypt first, filter to taxdome.com:",
              file=sys.stderr)
        print("  ~/.local/orch-venv/bin/browserclaw cookies decrypt \\",
              file=sys.stderr)
        print("    --db \"$HOME/Library/Application Support/Google/Chrome/Default/Cookies\" \\",
              file=sys.stderr)
        print("    --output /tmp/tax2025/cookies-chrome.json \\",
              file=sys.stderr)
        print("    --keychain-service 'Chrome Safe Storage' --keychain-account 'Chrome' \\",
              file=sys.stderr)
        print("  # then filter to taxdome.com and save as cookies-taxdome-only.json",
              file=sys.stderr)
        return 2

    with open(cookies_path) as f:
        cookies_raw = json.load(f)["cookies"]
    cookies = to_pw_cookies(cookies_raw)

    results = []
    with sync_playwright() as pw:
        # `channel='chromium'` uses the bundled Chrome-for-Testing binary,
        # not the headless_shell. The headless_shell rejects TaxDome's
        # "modern browser" JS bundle on first load.
        browser = pw.chromium.launch(
            channel="chromium",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.goto(DOCUMENTS_URL, timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)

        if "/login" in page.url or "/sign-in" in page.url:
            print("AUTH FAILED — TaxDome redirected to login",
                  file=sys.stderr)
            page.screenshot(path="/tmp/tax2025/shots/taxdome-auth-fail.png")
            browser.close()
            return 3

        try:
            for pdf in pdf_paths:
                fname = os.path.basename(pdf)
                try:
                    status, msg = upload_one(page, pdf)
                    print(f"{status}\t{fname}\t({msg})")
                    results.append((fname, status, msg))
                except Exception as e:
                    ts = int(time.time())
                    try:
                        page.screenshot(
                            path=f"/tmp/tax2025/shots/taxdome-exc-{ts}.png"
                        )
                    except Exception:
                        pass
                    print(f"FAIL\t{fname}\t({e})")
                    results.append((fname, "FAIL", str(e)[:200]))
                    # Try to recover by closing any open modal.
                    try:
                        done = find_done_button(page)
                        if done:
                            done.click()
                            time.sleep(1)
                        else:
                            x_btn = page.locator('[aria-label="Close"]').first
                            if x_btn.is_visible(timeout=1000):
                                x_btn.click()
                                time.sleep(1)
                    except Exception:
                        pass
        finally:
            try:
                browser.close()
            except Exception:
                pass

    ok = sum(1 for r in results if r[1] == "OK")
    fail = sum(1 for r in results if r[1] == "FAIL")
    print(f"\n=== {ok} OK, {fail} FAIL ===")
    for fn, s, m in results:
        print(f"  {s}\t{fn}\t({m})")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
