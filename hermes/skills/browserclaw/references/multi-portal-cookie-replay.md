# Multi-portal cookie replay — driving many sites with one decrypt

When the task is "use my saved logins to drive N portals" (e.g., a tax-return drive: 10 brokerages + 1 tax-prep portal + 1 Drive folder mirror), the pattern is:

1. **Decrypt once per browser** — Chrome Default + Aside Default
2. **Filter to task-relevant domains**
3. **Save a Playwright `storage_state` per source**
4. **Drive each portal as a one-shot Playwright session**, capturing screenshot + page text + downloaded PDFs

This file documents the verified pattern from a 10-portal tax return drive on 2026-07-18.

## Step 1 — Decrypt both browsers, save full cookie dumps

```bash
mkdir -p /tmp/<job>/raw /tmp/<job>/shots

~/.local/orch-venv/bin/browserclaw cookies decrypt \
  --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" \
  --output /tmp/<job>/cookies-chrome.json \
  --keychain-service 'Chrome Safe Storage' \
  --keychain-account 'Chrome' \
  --summary 2>&1 | tail -3

~/.local/orch-venv/bin/browserclaw cookies decrypt \
  --db "$HOME/Library/Application Support/Aside/Default/Cookies" \
  --output /tmp/<job>/cookies-aside.json \
  --keychain-service 'Aside Safe Storage' \
  --keychain-account 'Aside' \
  --summary 2>&1 | tail -3
```

Verify both contain non-empty `value` fields. If `value=""` for everything, fall back to the CDP recipe in `references/cdp-decrypt-via-headless-browser.md`.

## Step 2 — Filter to task domains

```python
import json
from pathlib import Path

task_domains = ['taxdome','fidelity','schwab','morganstanley','wealthfront',
                'wellsfargo','etrade','snapchat','gemini','scotiabank']

def filter_cookies(path):
    cookies = json.loads(Path(path).read_text())['cookies']
    return [c for c in cookies if any(t in c['domain'] for t in task_domains)]

chrome_tax = filter_cookies('/tmp/<job>/cookies-chrome.json')
aside_tax = filter_cookies('/tmp/<job>/cookies-aside.json')

# Playwright storage_state format: {cookies:[...], origins:[]}
json.dump({'cookies': chrome_tax, 'origins': []},
          open('/tmp/<job>/cookies-chrome-tax.json','w'))
json.dump({'cookies': aside_tax, 'origins': []},
          open('/tmp/<job>/cookies-aside-tax.json','w'))

print(f'Chrome task cookies: {len(chrome_tax)}', flush=True)
print(f'Aside task cookies:  {len(aside_tax)}', flush=True)
```

## Step 3 — Drive each portal

**Critical constraint (verified 2026-07-18):** use Playwright bundled Chromium-for-Testing, NOT `channel='chrome'`. The user explicitly said "stop doing normal browser" and "use headless chrome, it keeps opening up" — `channel='chrome'` opens a visible window briefly during launch even with `--headless`.

```python
# /tmp/<job>/drive.py
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROME = json.load(open('/tmp/<job>/cookies-chrome-tax.json'))['cookies']
ASIDE  = json.load(open('/tmp/<job>/cookies-aside-tax.json'))['cookies']

def normalize(cookies):
    """Convert CDP/browserclaw shape → Playwright add_cookies shape."""
    norm = []
    for c in cookies:
        nc = {'name': c['name'], 'value': c['value'],
              'domain': c['domain'], 'path': c.get('path', '/')}
        if c.get('expires') and c['expires'] > 0:
            nc['expires'] = int(c['expires'])
        if c.get('httpOnly'): nc['httpOnly'] = True
        if c.get('secure'):    nc['secure'] = True
        ss = c.get('sameSite')
        if ss and ss != 'None':
            nc['sameSite'] = ss
        norm.append(nc)
    return norm

def drive(label, url, source, post_wait=10, headless=True):
    cookies = CHROME if source == 'chrome' else ASIDE
    norm = normalize(cookies)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=['--no-sandbox'])
        ctx = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/147.0.0.0 Safari/537.36',
            viewport={'width': 1440, 'height': 900},
            accept_downloads=True,
        )
        ctx.add_cookies(norm)
        page = ctx.new_page()
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=45000)
            time.sleep(post_wait)
            page.screenshot(path=f'/tmp/<job>/shots/{label}-01.png')
            text = page.evaluate('document.body.innerText || ""')
            return {'ok': True, 'url': page.url, 'title': page.title(),
                    'text': text[:3000], 'cookies': len(norm)}
        except Exception as e:
            return {'ok': False, 'err': str(e), 'cookies': len(norm)}
        finally:
            browser.close()

# Pick source per portal: Chrome has fidelity/schwab/ms/wf, Aside has etrade/wf/snap
PORTALS = [
    ('taxdome',       'https://orenheneainc.taxdome.com/app/dashboard?after_signing_in=1', 'chrome'),
    ('fidelity',      'https://digital.fidelity.com/ftgw/digital/portfolio/summary',       'chrome'),
    ('schwab',        'https://client.schwab.com/app/accounts/summary/',                    'chrome'),
    ('morganstanley', 'https://login.morganstanleyclientserv.com/atrium/#/documents',       'chrome'),
    ('wealthfront',   'https://www.wealthfront.com/documents',                             'aside'),
    ('wellsfargo',    'https://connect.secure.wellsfargo.com/auth/home/documents',          'chrome'),
    ('etrade',        'https://us.etrade.com/etx/tax/taxForms',                             'aside'),
    ('snap',          'https://accounts.snapchat.com/v2/login',                             'chrome'),
]

for label, url, source in PORTALS:
    r = drive(label, url, source)
    status = 'OK' if r['ok'] else 'FAIL'
    print(f'{status:4} {label:15} url={r.get("url","?")[:60]}', flush=True)
```

## Expected results (per-portal bot detection pattern)

Verified 2026-07-18, 10-portal tax return drive:

| Portal | Bundled Chromium-for-Testing result |
|---|---|
| TaxDome | ✅ Signed in, dashboard loaded |
| Schwab | ⚠️ First run signed-in with fresh cookies; later runs got `SessionExpired` because cookies flush async |
| Fidelity, Morgan Stanley, Wells Fargo | ❌ HTTP/2 bot fingerprint detection — these sites reject Playwright Chromium TLS fingerprint even with valid cookies |
| Wealthfront, E*TRADE | ⚠️ Cookies exist but redirect to login (cookies are stale) |
| Snap, Gemini, Scotiabank | ❌ No cookies at all (user never logged in) |

**Decision tree for portals that fail:**

1. Cookies exist + session expired → user must re-login, then re-decrypt immediately
2. No cookies at all → user must log in for the first time
3. Bot detection blocks bundled Chromium → either (a) accept manual download, or (b) drive via `aside repl` which has the real Chrome fingerprint

## Step 4 — Asynchronous fallback: 5-min poll

If many portals need re-login and you can't get the user to do them all at once, register a `hermes cron` to poll every 5 min:

```bash
hermes cron create "5m" \
  --name "<job>-cookies-poll" \
  --deliver "slack:<thread-id>" \
  --model MiniMax-M3 --provider minimax \
  --prompt 'You are a polling watcher. Every tick: run browserclaw cookies decrypt --domain-filter %<portal>% --summary; if N>30 cookies present, drive the portal headlessly via Playwright bundled Chromium, save PDFs to /tmp/<job>/raw/, mirror to Drive, post ONE line to Slack, then `hermes cron remove $CRON_JOB_ID`. Cap at 2h. ALWAYS env -i HOME=... PATH=... wrapper. NEVER use channel=chrome. NEVER post full cookie values.'
```

The cron self-cancels on first successful download or after 2h (whichever comes first). See SOUL.md `## COMMIT: followup-promise-requires-cron` and `## COMMIT: one-time-status-cron-on-request`.

## What works / doesn't (tax-portal matrix, 2026-07-18)

| Portal | Decrypt | Headless login | Why |
|---|---|---|---|
| TaxDome (`orenheneainc.taxdome.com`) | ✅ 22 cookies | ✅ | No bot detection, all SPAs work |
| Schwab (`client.schwab.com`) | ✅ 40-50 cookies | ⚠️ Race | Session tokens rotate; re-decrypt after each navigation |
| Fidelity (`digital.fidelity.com`) | ✅ 41 cookies | ❌ HTTP/2 fingerprint | Bot fingerprint check at TLS layer |
| Morgan Stanley (`login.morganstanleyclientserv.com`) | ✅ 42 cookies | ❌ HTTP/2 fingerprint | Same |
| Wealthfront (`www.wealthfront.com`) | ✅ 17 cookies | ⚠️ Login redirect | Cookies in DB but server session expired |
| Wells Fargo (`connect.secure.wellsfargo.com`) | ✅ 32 cookies | ⚠️ Login redirect | Same |
| E*TRADE (`us.etrade.com`) | ✅ 11 cookies | ⚠️ Login redirect | Same |
| Snap Workday (`accounts.snapchat.com`) | ⚠️ 16 cookies | ❌ No session | Cookies present but never logged in to Workday SSO |
| Gemini exchange (`account.gemini.com`) | ❌ 0 cookies | n/a | Only gemini.google.com (AI chat) cookies in DB |

## TaxDome-specific path (the one that worked end-to-end)

TaxDome doesn't fingerprint-detect Playwright Chromium, so this is the only multi-step end-to-end path that was verified working:

1. **Dashboard load:** `https://orenheneainc.taxdome.com/app/dashboard?after_signing_in=1` → load 10s → screenshot → text dump
2. **2025 Organizer:** dashboard shows "Pending organizer — 2025 Organizer Questions" with a "Complete organizer" button. Click → navigates to `/app/organizers/<id>/edit`
3. **Organizer navigation:** 12 steps (Personal Info → Dependents → Healthcare → Income → Purchases → Retirement → Education → Deductions → Estimated Taxes → Miscellaneous → Document Uploads → Submit). Click "Next" to advance, capture text at each step.
4. **Documents upload:** `/app/documents` page has drag-and-drop + per-section uploads. Use Playwright's `set_input_files()` with the PDF paths.
5. **Billing:** `/app/billing` shows outstanding balance ($0 in this case) and invoice 1002418 ($80 extension fee). Payment requires the user to click "Pay" because of MFA / saved payment method.
6. **All changes auto-saved** as you advance — the form is a SPA, no Submit needed except the final step.

## Cleanup

```bash
# Kill any headless Chrome zombies
lsof -iTCP:9222 -sTCP:LISTEN -P -n -t 2>/dev/null | xargs -I{} kill -TERM {} 2>/dev/null
lsof -iTCP:9333 -sTCP:LISTEN -P -n -t 2>/dev/null | xargs -I{} kill -TERM {} 2>/dev/null

# Confirm no visible Chrome windows
osascript -e 'tell application "System Events" to count windows of process "Google Chrome"' 2>&1

# Remove temp profile copies (may have been mutated by headless launch)
rm -rf /tmp/<job>-chrome-debug

# Shred decrypted cookie dumps after use
shred -u /tmp/<job>/cookies-chrome.json /tmp/<job>/cookies-aside.json \
      /tmp/<job>/cookies-chrome-tax.json /tmp/<job>/cookies-aside-tax.json
```

## Cross-references

- `references/cdp-decrypt-via-headless-browser.md` — when `cookies decrypt` returns empty values (v20 ABE)
- `references/multi-profile-cookie-scan.md` — sweep Chrome Profile 1/3, Brave, Edge, Aside, Codex before declaring "no session"
- SKILL.md "Poll-until-cookies-appear pattern" — async fallback when cookies are 0
- SOUL.md `## COMMIT: browser-headless-default` — always-headless default
- SOUL.md `## COMMIT: bashrc-profile-xapp-drift-blocks-launchd` — env -i wrapper for browserclaw