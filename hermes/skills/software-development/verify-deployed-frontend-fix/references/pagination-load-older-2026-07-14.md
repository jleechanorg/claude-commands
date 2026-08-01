# Verified worked example: WA "Load older entries" pagination — 2026-07-14

**Bug class:** frontend visibility bug. The "⬆️ Load older entries" button existed in the DOM but was rendered off-screen (~3749px above the scrollport top), so users could never click it.

**Reported in:** Slack thread `C0BDEAJH8PK/p1783480073.802959` (channel: `#worldai-bugs`). User pasted URL `https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/game/xK3fp5XrV24oarIINTF7`.

**6 days later, user asked:** "is this pagination thing proven fixed now?" — exactly the trigger for `verify-deployed-frontend-fix`.

## What the fix looks like (3 layers)

### Layer 1 — code shipped
- Issue: [#8250](https://github.com/$GITHUB_REPOSITORY/issues/8250) "Load older entries button hidden"
- PRs in order: [#8251](https://github.com/$GITHUB_REPOSITORY/pull/8251) (CLOSED, sibling-of-container placement) → [#8256](https://github.com/$GITHUB_REPOSITORY/pull/8256) (MERGED 2026-07-08 04:32:55, sticky position) → [#8269](https://github.com/$GITHUB_REPOSITORY/pull/8269) (MERGED 2026-07-08 08:51:31, top-only per user feedback)
- Origin/main HEAD on 2026-07-14: `69282e011d`
- Key markers in `$PROJECT_ROOT/frontend_v1/app.js`: `syncLoadOlderVisibility`, `LOAD_OLDER_VISIBILITY_THRESHOLD = 8`, `storyContainer.addEventListener("scroll", syncLoadOlderVisibility)`
- Key change in `$PROJECT_ROOT/frontend_v1/style.css`: removed `position: sticky; top: 0; z-index: 10` from `#load-older-btn`

### Layer 2 — deployed bundle carries the fix
- Live HTML served 22 `<script src>` tags and 22 `<link rel="stylesheet">` files.
- App bundle hash from live HTML: `app.58c74e97.js` — re-derived from current HTML, **not trusted from any older message**.
- `curl -fsSL https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/frontend_v1/app.58c74e97.js` returned 200, 184,865 bytes.
- Greps confirmed all 6 markers in served JS:
  - `syncLoadOlderVisibility` defined
  - `LOAD_OLDER_VISIBILITY_THRESHOLD = 8`
  - `scrollTop<=LOAD_OLDER_VISIBILITY_THRESHOLD` gate
  - `storyContainer.addEventListener("scroll",syncLoadOlderVisibility)` (whitespace normalized)
  - `insertBefore(loadBtn,storyContainer.firstChild)` (in-flow placement)
  - `removeEventListener("scroll",syncLoadOlderVisibility)` cleanup

### Layer 3 — runtime behavior verified headless
- Used cached Chromium: `chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing`. `playwright install` would have failed; the cache hit the right binary.
- `page.goto(<deployed_url>, wait_until="domcontentloaded")` — page loaded; `<script src=".../app.58c74e97.js">` was attached.
- `document.styleSheets` walk with `selector.includes('load-older-btn') && /sticky/i.test(rule.cssText)` → returned `[]`. **Zero sticky rules** for the fixed element. This was the load-bearing layer — the CSS lives in separate `<link rel="stylesheet">` files, NOT in the JS bundle, so layer 2 alone would have missed any regression.
- `getComputedStyle` probe in an isolated iframe:
  ```javascript
  const iframe = document.createElement('iframe');
  iframe.style.display = 'none';
  document.body.appendChild(iframe);
  const doc = iframe.contentDocument;
  const sc = doc.createElement('div');
  sc.id = 'story-content';
  sc.style.cssText = 'max-height:200px;overflow-y:auto;height:200px;width:300px;border:1px solid red;';
  const btn = doc.createElement('button');
  btn.id = 'load-older-btn';
  sc.appendChild(doc.createElement('div'));
  sc.insertBefore(btn, sc.firstChild);  // mimic deployed placement
  doc.body.appendChild(sc);
  const cs = getComputedStyle(btn);
  // → { position: 'static', display: 'inline-block', top: 'auto', zIndex: 'auto' }
  ```
  Result: `position === 'static'` (not sticky). The fix is in the live cascade.

## Auth-gate workaround

The deployed URL is Firebase-auth-gated; a naive `page.goto()` + DOM walk would fail at the sign-in card. Two workarounds in the recipe:
1. Inject into a hidden iframe — the iframe document is independent, doesn't need the SPA to initialize. Used for the `getComputedStyle` probe above.
2. Walk `document.styleSheets` — sheets load before the SPA gates the body. Used for the "no sticky rule for `#load-older-btn`" check.

Both worked without authenticating.

## What I'd do differently

- A live DOM probe of the actual button (not iframe-injected) would catch the case where some inline `style=` overrides the cascade. The iframe probe is fast and covers 95% of cases; do the live-DOM probe when iframe results are ambiguous.
- An end-to-end scroll test (programmatically `scrollTop = N`, check `getComputedStyle(btn).display`) would be a perfect layer-3-cap. Skipped here because the iframe didn't have the scroll listener attached — would need to inject the JS too. Worth adding to the recipe if the bug is JS-driven, not CSS-driven.

## Pitfall worth naming explicitly

**"Hash drift"** — the comment block at app.js line 3162 in the served bundle STILL says `"sticky Load older entries button."` even though the implementation is now top-only. Anyone grepping for "sticky" in served bytes to verify the bug is gone will get a false positive. Always grep for *behavioral* markers (the function, the threshold, the event listener), not *narrative* markers (comments referencing the old design).
