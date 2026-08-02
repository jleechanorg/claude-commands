---
name: verify-deployed-frontend-fix
description: Verify that a claimed frontend-fix (CSS, JS behavior, layout, scroll, click handler, asset, computed style) is actually live on a deployed URL. Produces a yes/no verdict with three layers of proof — (1) merged code on origin/main, (2) fix-markers present in the deployed hashed bundle, (3) headless runtime computed-style / DOM behavior on the live URL. Trigger when the user asks "is X fixed now?", "is X live?", "is X in production?", "verify X shipped", "did X actually deploy?", or shares a deployed URL alongside a bug-fix PR/number and asks for proof of fix.
version: 1.0.0
metadata:
  hermes:
    tags: [verification, frontend, deploy, evidence, proof, ui, css, computed-style, bundle-hash, fix-claim]
    related_skills: [verify-telemetry-alert, repro, web-page-screenshots, evidence-attach-to-slack, pr-triage-and-next-steps]
---

# Verify a Claimed Frontend Fix on a Deployed URL

## Why this skill exists

When a user reports a UI bug, the bug fix lands in a PR, the PR merges, and the user comes back days or weeks later asking "is X actually fixed?" The naive answer is "yes, we merged PR #N." That answer is **incomplete**: there's a large gap between "code merged on origin/main" and "the live deployed bundle on the URL the user pasted contains the fix." Real failure modes:

- **Wrong bundle hash served.** Cloud Run / Vercel / Netlify may serve a stale hashed bundle if a CDN edge cached the previous one.
- **Old CSS still applied.** A separate stylesheet (loaded by `<link>`, not the bundle) was missed in the fix and still applies `position: sticky` etc.
- **Fix rolled back or never fully landed.** A subsequent revert PR or a follow-up fix that contradicts the original landed between merge and now.
- **Auth gate blocks full load.** Without the user's signed-in session, the SPA never initializes and `getComputedStyle` can't run — but you can still do layers 1, 2, and a partial layer 3.

The 3-layer protocol below closes all four gaps with one toolset (curl + headless Chromium via Playwright).

## When to invoke

Trigger phrases (any):
- "is X proven fixed now?" / "is X actually fixed?" / "is X live?"
- "verify X shipped" / "did X deploy?" / "is X in production?"
- User pastes a deployed URL + bug-fix PR number/branch and asks for proof
- Bugbot / CodeRabbit reports a regression on a fix that "should be merged"
- mcp_agent_mail, dropped-thread cron, or verifier cron posts "X should be fixed" with a PR number

Do NOT invoke:
- For backend / API claims (`verify-telemetry-alert` covers those)
- For "/repro" requests where the user is **reporting** a new bug, not verifying an existing fix
- For local-only changes that haven't deployed

## The 3-layer protocol

Produce a yes/no verdict. Each layer is independent — pass all three to claim "fixed and live." If any layer fails, name which one and what it showed.

### Layer 1 — Code shipped (origin/main)

Confirm the fix landed on the default branch. This is the *necessary* layer; nothing else matters if the code isn't in.

```bash
gh pr view <N> --repo <OWNER>/<REPO> --json state,mergedAt,headRefName,title,closingIssuesReferences,body
```

Pass criteria: `state == "MERGED"`, `mergedAt` is a real timestamp, `closingIssuesReferences` includes the issue (if there is one).

Belt-and-suspenders — confirm the file actually contains the fix on `origin/main`, not just on the PR's branch:

```bash
cd <repo>
git fetch origin
git show origin/main:<path/to/file> | grep -n "<fix_marker>" || echo "MISSING"
```

Replace `<path/to/file>` and `<fix_marker>` with the file + identifier from the PR diff (function name, constant, comment, CSS rule).

### Layer 2 — Deployed bundle carries the fix

**Find the current bundle hash.** Cloud Run / Vercel-style deploys use content-hashed filenames (`app.58c74e97.js`). The hash changes per deploy — never trust the hash from the PR or a stale Slack message.

```bash
# 1. Fetch the live HTML
curl -fsSL "<deployed_url>" -o /tmp/probe_page.html

# 2. Find every <script src="..."> and <link href="...css">
grep -oE 'src="[^"]*"' /tmp/probe_page.html | grep -E '\.(js|css)'
grep -oE 'href="[^"]*\.css"' /tmp/probe_page.html
```

For each script with a content-hash filename (`app.<hash>.js`) and each CSS file:
```bash
curl -fsSL "<deployed_origin><script_path>" -o /tmp/probe_bundle.js
# Then grep:
grep -n "<fix_marker_1>\|<fix_marker_2>\|<fix_marker_3>" /tmp/probe_bundle.js
```

Pick markers that are **unique to the fix** and absent in the previous version — function names introduced by the fix, new constant values, new CSS class selectors, new `addEventListener` strings, new comment blocks referencing the bug.

**Pass criteria:** all 5-10 markers present in the served bytes.

**Pitfall:** the fix may live in a chunk file (`chunk.<hash>.js`) loaded from the main bundle, not in the main bundle itself. Walk the import graph.

### Layer 3 — Runtime behavior verified headless

This is the **load-bearing** layer. Layer 1+2 only prove the deployed bytes contain the fix; layer 3 proves the fix actually affects the DOM as expected.

```python
from playwright.sync_api import sync_playwright

CHROME = "$HOME/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=CHROME, args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 390, "height": 844})  # match user's viewport
    page = ctx.new_page()
    page.goto("<deployed_url>", wait_until="domcontentloaded", timeout=45000)
    
    # A) Confirm the right bundle is attached to the document
    attached = page.evaluate("""() => {
      const scripts = Array.from(document.scripts).map(s => s.src);
      const css = Array.from(document.styleSheets).map(s => s.href);
      return { scripts: scripts.filter(s => s.includes('app.')), css };
    }""")
    
    # B) Walk live stylesheets for any BAD rule applying to the fixed element
    bad_rules = page.evaluate("""(selector) => {
      const out = [];
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule.selectorText && rule.selectorText.includes(selector)) {
              out.push({ href: sheet.href || '(inline)', cssText: rule.cssText });
            }
          }
        } catch (e) { /* cross-origin sheets throw SecurityError */ }
      }
      return out;
    }""", "<fixed-element-selector>")
    
    # C) Computed-style probe — inject the element in an isolated iframe so
    #    no other CSS affects it, OR query it from the live DOM if it exists.
    style_probe = page.evaluate("""() => {
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      document.body.appendChild(iframe);
      const doc = iframe.contentDocument;
      const el = doc.createElement('button');
      el.id = '<fixed-element-id>';
      doc.body.appendChild(el);
      const cs = getComputedStyle(el);
      const result = { position: cs.position, display: cs.display, top: cs.top, zIndex: cs.zIndex };
      iframe.remove();
      return result;
    }""")
    
    browser.close()
```

**Pass criteria depend on the bug class:**
- *Visibility / layout fix:* `position === 'static'`, not `sticky`. `display === 'block'` (or correct value). `top === 'auto'`.
- *Scroll-fix (button hides when scrolled):* inject the button + container in a styled iframe, programmatically `scrollTop=0`, check `display`, then `scrollTop=N>threshold`, check `display === 'none'`. Run the actual scroll listener if reachable.
- *Click handler fix:* bind the handler to a stub element, click, verify the side effect.
- *Network call fix:* route the relevant `/api/...` URL, verify `page.route()` saw the call.

**Auth gate pitfall:** Layer 3-C (live DOM) may fail if the SPA is auth-gated and redirected. Workarounds in priority order:
1. Inject the element into a hidden iframe (independent document, no SPA code). You can still verify CSS rules from step B apply / computed-style resolution without the SPA running. The iframe inherits the page's loaded CSS via cascade but doesn't need the SPA's JS.
2. Walk `document.styleSheets` (step B) — sheets load before the SPA gates the body. If a stale bad rule is in there, you'll catch it.
3. Skip layer 3 if both workarounds fail and say so explicitly in the verdict — "Layers 1+2 pass; layer 3 skipped because deployed URL is auth-gated; recommend the user manually confirm by visiting `<url>`."

## Output template

After running the 3 layers, post the verdict in this shape:

```
:white_check_mark: *Yes — <feature> is proven fixed and live.*

:white_check_mark: *Code shipped*
- [PR #N](url) merged <date> — <one-line behavioral change>.
- Issue [#N](url) closed.

:white_check_mark: *Deployed bundle carries the fix*
- Bundle served today: `<filename.<hash>.js>` (HTTP 200, <size> bytes).
- All N fix markers present in the served JS:
  - <marker 1>
  - <marker 2>
  - <marker N>

:white_check_mark: *Runtime behavior verified headless*
- Headless Chromium navigated the live URL; bundle attached = true.
- `document.styleSheets` walk: <N> rules apply to `<selector>` — <pass/fail breakdown>.
- `getComputedStyle` on injected element: `<key properties>` — <verdict>.

End state: <one-sentence behavioral summary>.
```

If any layer fails, mark that layer :red_circle: instead and name what it showed. Don't claim overall "fixed and live" if any layer is red.

Always include `🧠 Memories used:` at the end per the always-on guardrail.

## Pitfalls observed

- **Hash drift.** The bundle hash from a PR description or older Slack message will be wrong after a subsequent deploy. Always re-derive the current hash from the live HTML each verification.
- **CSS lives outside the bundle.** `position: sticky` (or the bad CSS the fix removed) may live in a `<link rel="stylesheet">` file, not in the hashed JS chunk. Walk both. The pattern from #8250: 22 separate `<link rel="stylesheet">` CSS files were loaded, none in the bundle. Layer 2 alone would have missed the fix.
- **Same-name-different-file selector.** `getComputedStyle` on a freshly-injected `<button id="load-older-btn">` returns `position: static`, but a *real* instance in the DOM may carry inline styles overriding the cascade. When probing a real instance, check `style.cssText` before `getComputedStyle`. When probing in an iframe, you get pure cascade resolution — usually what you want.
- **Cross-origin stylesheets throw.** `sheet.cssRules` on a `<link>` from a different origin throws `SecurityError`. Wrap in try/except; you'll skip those, but the in-page / same-origin sheets give the answer.
- **Playwright browsers need install.** `playwright install` may fail in restricted envs. Fall back to the cached `chromium-1223` at `~/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing` and pass `executable_path=` explicitly. This path was verified 2026-07-14.
- **Defer `document.styleSheets` walk too early.** Some SPAs inject stylesheets after `domcontentloaded`. Add `page.wait_for_timeout(2000)` before walking if you're seeing empty results.
- **Don't confuse "merged" with "deployed."** A merged PR may not be in production — Cloud Run revisions, Vercel deployments, and Fly machines all have their own lag. Layer 1 is necessary, not sufficient.

## Pair-with skills

- `repro` (`~/.hermes/skills/repro/SKILL.md`) — thin pointer to canonical WA workflow; load when reporting *new* bugs.
- `repro/references/auth-gate-fallback-repro.md` — fallback to local Flask + `X-Test-Bypass-Auth` when deployed URL auth-gates block live probing and the bug is API-shape or server-side. Different from layer 3 here, which is frontend-side.
- `verify-telemetry-alert` — for automated alerts (cron / BQ / billing), not user-asked "is X fixed now?" questions.
- `web-page-screenshots` — for capturing BEFORE/AFTER visual evidence for PRs (different use case; that skill is about *producing* screenshots, this one is about *consuming* a deployed state).
- `evidence-attach-to-slack` — for getting the verdict PNG/JSON attached to the Slack thread (not just path-mentioned).

## Reference

- `references/pagination-load-older-2026-07-14.md` — verified worked example. WA "Load older entries" pagination fix (issue #8250, PRs #8251 closed → #8256 merged → #8269 merged top-only rewrite). Demonstrates the iframe-injected `getComputedStyle` workaround for Firebase-auth-gated URLs and the "hash drift" pitfall (a comment in the served bundle still mentions "sticky" even though the implementation is top-only).

## Verification checklist

Before posting the verdict:
- [ ] PR view confirmed MERGED, with mergedAt timestamp
- [ ] `git show origin/main:<file>` confirms the fix is on main, not just the PR branch
- [ ] Live HTML re-derived the bundle hash; did not trust a stale hash
- [ ] All fix markers grepped from served JS bytes — not from local checkout
- [ ] `document.styleSheets` walk done against the live document
- [ ] `getComputedStyle` probe done in an isolated iframe (or live DOM with style override check)
- [ ] Result matches the expected pass criteria for the bug class (visibility / scroll / click / network)
- [ ] If any layer skipped, name the layer and the reason in the verdict
- [ ] `🧠 Memories used:` line included
