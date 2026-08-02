---
title: "Read a Gemini / ChatGPT / Google-Doc share link as the user"
type: reference
date: 2026-07-20
verified_against: Gemini Flash share `Td7fA4pzuvMs` ("God of Murder Campaign Design")
---

# Reading auth-gated AI share links as the user

When the user gives you a `share.gemini.google/...`, `chatgpt.com/share/...`, or "anyone with the link" Google Doc URL and asks you to read the content, anonymous fetch (`curl`, `web_extract`, even headless `browser_navigate`) returns a **sign-in shell** with the conversation body loaded client-side only after Google / vendor auth.

The wrong move is to declare the task blocked and ask the user to paste the content. The right move is to read the page *as the user* by decrypting their Chrome cookies and injecting them into a headless Chromium session.

This is what "use /browser or /browserclaw headless next time without asking" means — reach for the auth-aware recipe on the **first refusal**, not after being told.

## Verified recipe (5 steps)

```bash
# 1. Decrypt Chrome Default cookies for the target auth domain
env -i HOME="$HOME" \
  PATH="$HOME/.local/orch-venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  browserclaw cookies decrypt \
    --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" \
    --output /tmp/google-cookies.json \
    --domain-filter '%.google.com%' \
    --summary
# Expected: "Wrote 79 cookies to /tmp/google-cookies.json" (or similar)

# 2. Inject + navigate headless, dump the full page text
env -i HOME="$HOME" \
  PATH="$HOME/.local/orch-venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  browserclaw cookies inject \
    --cookies /tmp/google-cookies.json \
    --goto "https://gemini.google.com/share/<share-id>" \
    --browser-channel chromium \
    --headless \
    --wait-after-load 12 \
    --screenshot /tmp/share_authed.png \
    --print-text 100000 > /tmp/share_page.txt
# Expected: "cookies_injected: 79, page text captured"
```

The redirect (`/share/<id>` → `gemini.google.com/share/<daf9bcee379e>?skid=…`) is normal — the `skid` query parameter carries the conversation token. Pass the final redirected URL to `--goto` if you want to skip the redirect.

## Why headless Chromium (not `channel=chrome`)

`channel=chrome` spawns the system Chrome binary which:
1. Briefly opens a visible window before transitioning to headless.
2. Can pollute the user's existing Chrome session with new tabs.

`channel=chromium` (bundled Chromium-for-Testing) is always headless, never opens a visible window, and is the right default for this workflow. **Verified 2026-07-18 multi-portal tax drive**: `channel=chrome --headless` opened a visible window despite the flag, so the user's #1 complaint ("use headless browser, stop doing normal browser") applies here.

## Truncation pitfall — scroll-to-bottom re-extraction

Gemini's share UI lazy-loads conversation history as the user scrolls. `--print-text 100000` captures the visible viewport but can **truncate mid-sentence** for long conversations (verified 2026-07-20: v7 truncated at "replaced by somethi").

**Fix:** re-extract with Playwright's scroll-to-bottom pattern, then grab the full `document.body.innerText`:

```python
from playwright.sync_api import sync_playwright
import json, pathlib

with open("/tmp/google-cookies.json") as f:
    state = {"cookies": json.load(f)["cookies"], "origins": []}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=state, viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto("https://gemini.google.com/share/<id>", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(10000)
    for _ in range(12):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1500)
    full_text = page.evaluate("document.body.innerText")
    pathlib.Path("/tmp/share_full.txt").write_text(full_text, encoding="utf-8")
    print(f"len={len(full_text)}")
    browser.close()
```

Use the orch-venv Python (has Playwright + browsers installed): `$HOME/.local/orch-venv/bin/python`. The system `python3` does NOT have Playwright browsers cached and will fail with `Executable doesn't exist at $HOME/Library/Caches/ms-playwright/chromium_headless_shell-1208/...`.

## Multi-turn conversation recovery (THE FINAL THING)

Gemini share pages render the full back-and-forth between the user and Gemini as `You said` / response pairs. When the user asks "make sure the final thing didn't miss anything I asked," the **last `You said` block** is what they want captured — not any of the intermediate drafts.

Detection recipe:

```bash
grep -nE "^You said|^REVISED|^Campaign Design|^System:" /tmp/share_full.txt
```

This prints every revision boundary. The final content to save is whatever comes **after the last `You said`** block in the file. Preserve intermediate drafts at `/tmp/share_full.txt` for archival; only the final state lands in the user's artifact (wiki, world_reference, etc.).

## What this works for (verified or expected to work)

| Source | Auth domain | Notes |
|---|---|---|
| Gemini share links | `%.google.com%` | Verified 2026-07-20 — 79 cookies, 169KB page text |
| ChatGPT shared chats | `%.openai.com%` | Same pattern; inject against `chatgpt.com/share/...` |
| Google Docs (with your account added, share-on) | `%.google.com%` | Same Google cookies; export via `gog docs export` instead if you just need the text |
| Notion shared pages | `%.notion.so%` + `%.notion.com%` | Decrypt both filters; Notion auth spans subdomains |
| Figma shared files | `%.figma.com%` | Same pattern; `figma.com/file/...` requires Figma session cookie |
| Linear shared issues | `%.linear.app%` | Same pattern; Linear session cookie is the auth |

## What this DOES NOT bypass

- **2FA / WebAuthn / passkey-only accounts** — the cookies decrypt, but the session might require re-prompt after N hours idle. Fix: user must have logged in within the cookie's lifetime.
- **Cloudflare Turnstile / DataDome / fingerprint challenges** — these check JS-side fingerprint, not cookies. Sites that reject headless Chromium's fingerprint (LinkedIn, X/Twitter, Facebook — observed 2026-07-05) will still bounce even with valid session cookies.
- **MFA-gated Google accounts with no Chrome session** — if the user has never logged into Google in Chrome, there are no cookies to decrypt. Fall back to `gog`/`gws` CLI auth (separate Google OAuth flow) or ask the user to log into Chrome once.

## Anti-pattern: declaring blocked and asking the user to paste

The failure mode this recipe prevents:

> User: "Read this campaign and make a PR to save it in world_reference: https://share.gemini.google/Td7fA4pzuvMs"
> Agent (wrong): "Stopped at a blocker. The Gemini share link redirects to a sign-in page... Please paste the text."
> User: "use /browser or /browserclaw headless next time without asking"

`web_extract` returns "DDGS is a search-only backend and cannot extract URL content" (verified 2026-07-10, current behavior). `curl` returns the empty sign-in shell. `browser_navigate` returns the same. None of these are blockers — they're signals that the auth-aware recipe applies.

## Related

- Parent skill: `~/.hermes/skills/browserclaw/SKILL.md` (cookies decrypt + inject + CDP v20 bypass recipes)
- Sibling policy: `~/.hermes/skills/browser-headless-default/SKILL.md` (headless-only mandate; this recipe is the canonical "headless + auth" answer)
- `~/.claude/skills/google-credentials-fallback/SKILL.md` (fallback to `gog`/`gws` for Google Docs when the user has no Chrome session)
- SOUL.md `## COMMIT: finish-the-job` — declaring blocked without trying the auth-aware recipe is a finish-the-job violation