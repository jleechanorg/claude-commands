# `aside repl` + Playwright Page Object — Verified Patterns (2026-07-06)

**Why this file exists:** The first round of social-poster staging used naive `document.querySelector(...)` calls at the REPL top level. That doesn't work — `document` is NOT scoped to the page returned by `openTab()`. This file captures the correct idioms, verified end-to-end against a live Aside daemon.

## Core fact: `openTab(url)` returns a Playwright `Page` object

```javascript
const p = await openTab('https://example.com');
// typeof p === 'object'
// Object.keys(p) includes: ['cdp', 'frameManager', 'targetId', 'keyboard', 'mouse', 'browser']
// Object.getOwnPropertyNames(Object.getPrototypeOf(p)).filter(k => typeof p[k] === 'function')
//   → ['goto', 'goBack', 'reload', 'waitForLoadState', 'waitForURL', 'waitForSelector',
//      'locator', '$', '$$', '$$eval', 'getByRole', 'getByLabel', 'getByText',
//      'frameLocator', 'evaluate', 'evaluateInFrame', 'url', 'title', 'content', 'screenshot']
```

This is the Playwright `Page` class. Use its methods.

## Pattern 1 — screenshot via `p.screenshot()` (preferred)

```javascript
const p = await openTab('https://example.com');
await p.waitForLoadState('domcontentloaded');
await new Promise(r => setTimeout(r, 3500));
const shot = await p.screenshot();           // returns Buffer
console.log('B64:' + shot.toString('base64'));
```

**Why preferred over `annotatedScreenshot(p)`:** simpler, returns a Node Buffer directly, `toString('base64')` works without manual decoding. `annotatedScreenshot(p)` works too but the old `annotatedScreenshot(null)` throws `Cannot read properties of null (reading 'snapshot')`.

## Pattern 2 — DOM inspection via `p.evaluate(() => ...)`

```javascript
const state = await p.evaluate(() => ({
  url: window.location.href,
  title: document.title,
  hasTitleField: !!document.querySelector('input[name="title"]'),
  hasBodyField: !!document.querySelector('textarea[name="text"]'),
  hasComposeDiv: !!document.querySelector('div[contenteditable="true"]'),
  // Twitter-specific
  hasTweetTextarea: !!document.querySelector('[data-testid="tweetTextarea_0"]'),
  // LinkedIn-specific
  username: document.querySelector('a#me')?.textContent ?? null,
}));
console.log('STATE', JSON.stringify(state));
```

`p.evaluate(fn)` serializes the result back to the REPL context. JSON-stringify it for stdout.

## Pattern 3 — click + wait + screenshot (login bypass attempt)

```javascript
const p = await openTab('https://news.ycombinator.com/login');
await p.waitForLoadState('domcontentloaded');
await new Promise(r => setTimeout(r, 2000));
// Click the submit button via Playwright locator
await p.locator('input[type="submit"][value="login"]').click();
await p.waitForLoadState('domcontentloaded');
await new Promise(r => setTimeout(r, 3000));
const post = await p.evaluate(() => ({ url: window.location.href }));
console.log('AFTER_CLICK', JSON.stringify(post));
const shot = await p.screenshot();
console.log('B64:' + shot.toString('base64'));
```

## Pattern 4 — iframe access (LinkedIn Google One-Tap etc.)

```javascript
const p = await openTab('https://www.linkedin.com/feed/');
await p.waitForLoadState('domcontentloaded');
await new Promise(r => setTimeout(r, 4000));
// frameLocator finds the iframe by selector, then click inside it
const fl = p.frameLocator('iframe[title="Sign in with Google Button"]');
await fl.locator('div[role="button"]').first().click({ timeout: 3000 });
```

**Pitfall:** `p.frame(...)` is NOT a method (different Playwright version). Use `p.frameLocator(selector)` instead.

## Pattern 5 — paste text into a compose field (Reddit example)

```javascript
const title = 'disk_magician: snapshot your dev Mac to git';
const body = 'I built disk_magician because...';
const p = await openTab('https://old.reddit.com/r/LocalLLaMA/submit?selftext=true');
await p.waitForLoadState('domcontentloaded');
await new Promise(r => setTimeout(r, 3000));
await p.evaluate((t, b) => {
  const setVal = (el, v) => {
    const proto = el.tagName === 'TEXTAREA'
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    setter.call(el, v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  };
  setVal(document.querySelector('textarea[name="title"]'), t);
  setVal(document.querySelector('textarea[name="text"]'), b);
}, title, body);
await new Promise(r => setTimeout(r, 1000));
const shot = await p.screenshot();
console.log('B64:' + shot.toString('base64'));
```

**Note:** `p.evaluate(fn, arg1, arg2)` passes extra args positionally. The fn is `(arg1, arg2) => {...}`, not `(args) => {...}`.

## Pattern 6 — list live Aside tabs

```javascript
const tabs = await listBrowserTabs();
console.log('TOTAL', tabs.length);
tabs.forEach(t => console.log(' -', t.url));
```

A signed-in tab on the platform = the session is valid, even if a fresh `openTab(compose-url)` hits a login wall (because compose-URL navigation sometimes triggers session re-validation).

## Why naive `document.querySelector(...)` at REPL top level fails

The REPL runs in Aside's daemon context, not in the page context. `document` there refers to the Aside UI itself, not the page returned by `openTab()`. Top-level `await openTab(url); await new Promise(r => setTimeout(r, 4500)); document.querySelector(...)` throws `ReferenceError: document is not defined`.

**Workarounds:**
- Wrap in IIFE: `(async () => { const p = await openTab(...); await sleep(4500); const x = document.querySelector(...); })()` — but IIFE return values don't reach stdout via `console.log` reliably in async contexts.
- **Best:** use `p.evaluate(() => document.querySelector(...))` — this serializes the result back to REPL.

## Cross-references

- `references/aside-repl-session-state.md` — verified auth state per platform, login-vs-compose detection
- `references/platform-session-status.md` — 2026-07-05 Playwright Chrome probe (DO NOT use for `aside repl` workflows)
- `scripts/stage_in_aside.py` — staging script; needs patch to use `p.screenshot()` and `?selftext=true` for Reddit