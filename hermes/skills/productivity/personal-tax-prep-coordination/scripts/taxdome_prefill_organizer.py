#!/usr/bin/env python3
"""Drive a TaxDome organizer's Yes/No/Single/etc. radio-questionnaire headlessly.

Reads:
  - /tmp/<preparer>-<year>-cookies-chrome.json — output of `browserclaw cookies decrypt`
    (filtered to taxdome.com domain)
  - /tmp/<preparer>-<year>-organizer-answers.json — answer map: {question_keyphrase: "Yes"|"No"|"Single"|...}

Behavior:
  - Opens organizer URL headlessly via Playwright bundled Chromium-for-Testing
  - Walks all 12 steps; for each question group, finds the matching answer
    and clicks the radio input directly via JS (bypassing label-click issues)
  - Advances via the Next button; verifies step changed; aborts if stuck
  - Does NOT click Submit — caller must approve before final send

Verified 2026-07-19 against TaxDome organizer 6044459 (2025 Oren Hen EA Inc).
Pre-filled 75 questions across 12 steps. Default answers file lives at
/tmp/tax2025/organizer-answers.md — see parent skill `personal-tax-prep-coordination`
for the answer-template convention.

Usage:
  python3 scripts/taxdome_prefill_organizer.py \\
    --url https://orenheneainc.taxdome.com/app/organizers/6044459/edit \\
    --cookies /tmp/tax2025/cookies-chrome-tax.json \\
    --answers /tmp/tax2025/organizer-answers.json \\
    --log /tmp/tax2025/prefill-log.txt

The script handles session cookie normalization:
- Skips `expires` for session cookies (expires_utc=0)
- Converts microsecond timestamps (>1e12) to seconds
- Filters out cookies whose `expires` is in the past
"""

import argparse
import json
import time
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def load_cookies(cookies_path: str, domain_filter: str = "taxdome") -> list[dict]:
    """Read a browserclaw JSON output and normalize cookies for Playwright add_cookies()."""
    data = json.loads(Path(cookies_path).read_text())
    cookies = data.get("cookies", [])
    filtered = [c for c in cookies if domain_filter in c.get("domain", "")]
    norm = []
    for c in filtered:
        nc = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
        }
        exp = c.get("expires", 0)
        # Skip cookies already expired; convert microsecond timestamps
        if exp and exp > 0:
            if exp > 1e12:
                exp = exp / 1_000_000
            if exp > time.time():
                nc["expires"] = int(exp)
        if c.get("httpOnly"):
            nc["httpOnly"] = True
        if c.get("secure"):
            nc["secure"] = True
        ss = c.get("sameSite")
        if ss and ss != "None":
            nc["sameSite"] = ss
        norm.append(nc)
    return norm


def click_radio_js(page, name: str, answer: str) -> bool:
    """Click a radio input by its group `name` attribute, matching the label text."""
    return page.evaluate(
        f"""
        () => {{
            const radios = document.querySelectorAll('input[type=radio][name="{name}"]');
            for (const r of radios) {{
                const label = r.closest('label');
                const text = (label ? label.innerText : '').trim().toLowerCase();
                if (text === '{answer.lower()}' || text.startsWith('{answer.lower()}')) {{
                    r.click();
                    r.dispatchEvent(new Event('change', {{bubbles: true}}));
                    r.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return true;
                }}
            }}
            return false;
        }}
        """
    )


def get_question_groups(page) -> list[dict]:
    """Walk the DOM, return [{name, qText, labels}] for each radio group."""
    return page.evaluate(
        """
        () => {
            const result = [];
            const radios = Array.from(document.querySelectorAll('input[type=radio]'));
            const seen = new Set();
            for (const r of radios) {
                if (seen.has(r.name)) continue;
                seen.add(r.name);
                const groupRadios = Array.from(document.querySelectorAll(`input[type=radio][name="${r.name}"]`));
                const labels = groupRadios.map(rr => (rr.closest('label') ? rr.closest('label').innerText.trim() : ''));
                let walker = r;
                let qText = '';
                for (let i = 0; i < 8 && walker; i++) {
                    walker = walker.parentElement;
                    if (!walker) break;
                    const allText = (walker.innerText || '').trim();
                    const lines = allText.split('\\n');
                    for (const line of lines) {
                        const t = line.trim();
                        if (t.length > 10 && (t.endsWith('?') || t.startsWith('*'))) {
                            qText = t.replace(/^\\*\\s*/, '').slice(0, 200);
                            break;
                        }
                    }
                    if (qText) break;
                }
                result.push({name: r.name, qText: qText, labels: labels});
            }
            return result;
        }
        """
    )


STEPS = [
    "WELCOME",
    "PERSONAL INFORMATION",
    "DEPENDENTS",
    "HEALTH CARE COVERAGE",
    "INCOME",
    "PURCHASES, SALES AND DEBT",
    "RETIREMENT PLANS",
    "EDUCATION",
    "ITEMIZED DEDUCTIONS",
    "ESTIMATED TAXES",
    "MISCELLANEOUS",
    "DOCUMENT UPLOADS",
]


def current_step(page) -> str | None:
    text = page.evaluate("document.body.innerText")
    for s in STEPS:
        if s in text:
            return s
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True, help="Organizer edit URL")
    p.add_argument("--cookies", required=True, help="browserclaw JSON output")
    p.add_argument("--answers", required=True, help="JSON map of question_keyphrase -> answer_label")
    p.add_argument("--log", required=True, help="Where to write the answered log")
    p.add_argument("--domain-filter", default="taxdome")
    p.add_argument("--user-agent", default=(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    ))
    args = p.parse_args()

    cookies = load_cookies(args.cookies, args.domain_filter)
    answers = json.loads(Path(args.answers).read_text())

    answered_log = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent=args.user_agent,
            viewport={"width": 1440, "height": 900},
        )
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto(args.url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(8)

        for it in range(15):
            time.sleep(3)
            step = current_step(page)
            if not step:
                print(f"Iter {it}: unknown step", file=sys.stderr)
                break

            if it > 0:
                print(f"Iter {it}: Step {step}", flush=True)

            groups = get_question_groups(page)
            step_answered = 0
            for q in groups:
                qtext = q["qText"]
                if not qtext:
                    continue
                ans = None
                for pattern, candidate in answers.items():
                    if pattern.lower() in qtext.lower():
                        ans = candidate
                        break
                if not ans:
                    continue
                if not any(ans.lower() in lbl.lower() for lbl in q["labels"]):
                    continue
                if click_radio_js(page, q["name"], ans):
                    answered_log.append((step, qtext[:60], ans))
                    step_answered += 1

            if it > 0:
                print(f"  -> answered {step_answered}", flush=True)

            if step == "DOCUMENT UPLOADS":
                break
            prev = step
            page.locator("button:has-text(\"Next\")").first.click(timeout=5000)
            time.sleep(6)
            if current_step(page) == prev:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                page.locator("button:has-text(\"Next\")").first.click(timeout=5000, force=True)
                time.sleep(6)
                if current_step(page) == prev:
                    print(f"  stuck on {prev}, aborting", flush=True)
                    break

        Path(args.log).write_text(
            "\n".join(f"{s}: {q} -> {a}" for s, q, a in answered_log)
        )
        print(f"\n=== ANSWERED {len(answered_log)} — NOT submitted ===")
        browser.close()


if __name__ == "__main__":
    main()