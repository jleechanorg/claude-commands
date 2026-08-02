---
date: 2026-07-20
incident_id: gemini-share-link-auth-gate-stopping-pattern
severity: medium
session: slack_C0AH3RY3DK6/1784580748.125749
proves_the_recipe: pr_$GITHUB_REPOSITORY#8483
fix_landed_in:
  - skill: ~/.hermes/skills/browserclaw/SKILL.md (patched, §"AUTH-GATED SHARE LINK — FIRE THIS ON FIRST REFUSAL")
  - skill: ~/.hermes/skills/browser-headless-default (cross-reference)
  - SOUL.md: ~/.hermes/workspace/SOUL.md (53rd COMMIT `read-auth-gated-share-links-with-browserclaw`)
  - jleechanclaw: PR jleechanorg/jleechanclaw#788 (`.claude/commands/browser.md` + contract test, 7 tests green)
  - user_scope: ~/.claude/commands/browser.md (rewritten with the auth-gate recipe pointer)
---

# 2026-07-20 — Gemini share-link auth-gate stopping pattern (the failure mode this section exists to prevent)

## What happened (one paragraph)

User asked Hermes in Slack thread `C0AH3RY3DK6/1784580748.125749` to read a Gemini share link (`https://share.gemini.google/Td7fA4pzuvMs`) and save the campaign as a PR on `$GITHUB_REPOSITORY`. The share link is auth-gated — anonymous fetch returns the Google sign-in shell. Hermes ran 4 anonymous fetch attempts (browser_navigate, curl with Chrome UA, curl with default UA, redirect-follow via HEAD), all returned the sign-in shell. Hermes then **posted a 4-option unblock menu** to the Slack thread: paste text / re-share publicly / Doc export / proceed from title alone. User reply (verbatim):

> *use /browser or /browserclaw headless next time without asking*

Hermes then ran the `browserclaw cookies decrypt + cookies inject` recipe end-to-end. 79 Google cookies decrypted, full 169KB page text extracted, 7 design iterations + 1 final 3,422-word self-contained campaign captured, PR `$GITHUB_REPOSITORY#8483` opened and merged at 22:02 UTC.

## The failure mode (what NOT to do)

**Anti-pattern: posting a multi-option unblock menu on first auth-gate refusal.** This is a soft-block that:

1. Costs the user a full reply round-trip
2. Breaks the user's flow (they already know what they want saved)
3. Surfaces the wrong mental model ("we can't access this") when the right model is ("we can access this as the user, headless, in ~5 seconds")
4. Predictably triggers user frustration (the verbatim correction above)

The same anti-pattern shows up in slightly different forms:

- "Can you paste the content?"
- "Can you re-share with public access?"
- "Can you export to a Google Doc?"
- "I can proceed from the title alone"

**All four of these are wrong defaults.** The recipe below is faster, works for the user, and matches the user's stated intent.

## The recipe (verified 2026-07-20 on Gemini share Td7fA4pzuvMs)

```bash
# Step 1 — Decrypt Chrome Default cookies for the vendor auth domain.
# Run inside env -i so the .bashrc exports don't pollute the path
# (per the bashrc-profile-xapp-drift-blocks-launchd memory).
env -i HOME="$HOME" \
  PATH="$HOME/.local/orch-venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  browserclaw cookies decrypt \
    --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" \
    --output /tmp/google-cookies.json \
    --domain-filter '%.google.com%' \
    --summary
# Expected: "Wrote 79 cookies to /tmp/google-cookies.json" (or similar)

# Step 2 — If 0 cookies for the vendor domain, sweep Profile 1 / Profile 2 /
# Aside / Brave / Edge per ~/.hermes/skills/browserclaw/references/multi-profile-cookie-scan.md.
# If still 0, post ONE-LINE BLOCKER naming the missing-cookie domain;
# do NOT silently give up.

# Step 3 — Inject + navigate headless Chromium + dump page text.
# IMPORTANT: use --browser-channel chromium (NOT chrome) to avoid the
# visible-window leak documented in this SKILL.md (channel=chrome briefly
# opens a visible Chrome window before transitioning to headless).
env -i HOME="$HOME" \
  PATH="$HOME/.local/orch-venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  browserclaw cookies inject \
    --cookies /tmp/google-cookies.json \
    --goto "https://gemini.google.com/share/<share-id>?skid=<skid>" \
    --browser-channel chromium \
    --headless \
    --wait-after-load 12 \
    --screenshot /tmp/share_authed.png \
    --print-text 100000 > /tmp/share_page.txt

# Step 4 — If --print-text truncates mid-sentence (Gemini share pages lazy-
# load sections), re-extract with Playwright + scroll-to-bottom:
python3 -c "
from playwright.sync_api import sync_playwright
import json, pathlib

cookies = json.loads(pathlib.Path('/tmp/google-cookies.json').read_text())
cookies_for_pw = cookies.get('cookies', cookies)  # handle both shapes

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    ctx.add_cookies(cookies_for_pw)
    page = ctx.new_page()
    page.goto('https://gemini.google.com/share/<share-id>?skid=<skid>',
              wait_until='domcontentloaded')
    # Scroll to bottom in chunks to trigger lazy-loading
    for _ in range(20):
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(500)
    text = page.evaluate('document.body.innerText')
    pathlib.Path('/tmp/share_page.txt').write_text(text)
    browser.close()
"

# Step 5 — Read the captured text end-to-end (NOT a 500-line preview).
# Verify the expected first-user message appears (NOT the vendor sign-in form).
# Proceed with the user's actual ask against the captured content.
```

## Why this recipe works (the credentials and the fingerprint)

The recipe reuses the user's own Chrome session. The cookie decryption unlocks v10/v11 cookies with PBKDF2-HMAC-SHA1 (1003 iterations, salt `saltysalt`). v20 (App-Bound Encryption, Chrome v120+) needs the CDP-via-headless fallback documented in `references/cdp-decrypt-via-headless-browser.md` — but Gemini's auth cookies are still on v10/v11 as of 2026-07-20. If you hit empty cookie values, that's the v20 signal — switch to the CDP recipe.

The `--browser-channel chromium` choice matters because:
- `channel=chrome` spawns the system Chrome binary which briefly opens a visible window before transitioning to headless (verified bug 2026-07-18, user's #1 complaint).
- `channel=chromium` is Playwright's bundled Chromium-for-Testing — always headless, never opens a visible window.
- The bundled Chromium-for-Testing has a different TLS fingerprint than system Chrome; some bot-detection sites reject it. For Gemini / ChatGPT / Notion share links, it works. For LinkedIn / Twitter / Threads, it does not (different failure class — not the auth-gate class).

## The three-layer closeout (what was shipped after this session)

1. **Skill layer:** `~/.hermes/skills/browserclaw/SKILL.md` patched with the new §"AUTH-GATED SHARE LINK — FIRE THIS ON FIRST REFUSAL" section. This file (the reference) carries the verified recipe + failure mode + cross-modal context.
2. **SOUL.md layer:** 53rd COMMIT `read-auth-gated-share-links-with-browserclaw` added to `~/.hermes/workspace/SOUL.md`. Trigger-based, applies every session.
3. **Contract test layer:** jleechanorg/jleechanclaw PR #788 added `.claude/commands/browser.md` (canonical source) + `tests/test_browser_command_mentions_browserclaw.py` (7 tests, all green). If anyone edits the /browser skill and drops the `browserclaw` reference or the auth-gate recipe pointer, the test fails.

The contract test is the **enforcement point** — it locks the user-scope `~/.claude/commands/browser.md` to mention `browserclaw` and the auth-gate recipe pointer, so an agent that loads the /browser skill in the future hits the contract before having to remember it.

## Where the pieces live

| Artifact | Location | Status |
|---|---|---|
| Verified recipe (this file) | `~/.hermes/skills/browserclaw/references/gemini-share-link-stopping-pattern.md` | ✅ Written |
| Companion recipe (env-block + 5 steps) | `~/.hermes/skills/browserclaw/references/gemini-share-link-as-user.md` | ✅ Existing |
| SKILL.md trigger section | `~/.hermes/skills/browserclaw/SKILL.md` §"AUTH-GATED SHARE LINK — FIRE THIS ON FIRST REFUSAL" | ✅ Patched 2026-07-20 |
| SOUL.md 53rd COMMIT | `~/.hermes/workspace/SOUL.md` (line 534) | ✅ Live (52 → 53 COMMITs) |
| /browser canonical skill | `jleechanorg/jleechanclaw` `.claude/commands/browser.md` (PR #788) | ✅ PR open, ready to merge |
| Contract test (7 tests) | `jleechanorg/jleechanclaw` `tests/test_browser_command_mentions_browserclaw.py` (PR #788) | ✅ All 7 green |
| User-scope /browser skill | `~/.claude/commands/browser.md` (mirrors canonical, fallback path) | ✅ Updated |
| Bead | `br show orch-icad` | ✅ Created |
| Daily note | `~/.hermes/workspace/memory/2026-07-20-gemini-share-link-stopping-pattern.md` | ✅ Written |
| Claude auto-memory | `~/.claude/projects/-Users-$USER/memory/feedback_2026-07-20_stopping-at-auth-gate.md` | ✅ Written |
| Worked-example PR | `$GITHUB_REPOSITORY#8483` | ✅ Merged 2026-07-20 22:02 UTC |

## What to do next time you hit this pattern

1. **Don't post an unblock menu.** The recipe below is the canonical action.
2. Run the 5-step recipe.
3. Read the captured text end-to-end. Verify it loaded as the user (first-user message in the dump, NOT the vendor sign-in form).
4. Proceed with the user's actual ask against the captured content.
5. If the recipe fails (0 cookies after multi-profile sweep, v20 ABE bypass needed, etc.), surface ONE-LINE BLOCKER with the specific failure mode — never a multi-option menu.

## Cross-references

- Slack thread: https://jleechanai.slack.com/archives/C0AH3RY3DK6/p1784580748.125749
- Worked-example PR (proves the recipe works): https://github.com/$GITHUB_REPOSITORY/pull/8483
- Harness PR (lands the contract test): https://github.com/jleechanorg/jleechanclaw/pull/788
- Companion recipe (env-block + 5 steps): `~/.hermes/skills/browserclaw/references/gemini-share-link-as-user.md`
- Multi-profile sweep: `~/.hermes/skills/browserclaw/references/multi-profile-cookie-scan.md`
- v20 ABE bypass: `~/.hermes/skills/browserclaw/references/cdp-decrypt-via-headless-browser.md`
- Sibling skill: `~/.hermes/skills/browser-headless-default` (already references browserclaw, the contract test locks it)
