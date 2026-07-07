# Platform Session Status — Cookie Injection Results

Verified 2026-07-05 via `browserclaw cookies decrypt` + Playwright Chrome `--browser-channel chrome --headless` + `cookie_inject_and_stage.py`.

## Summary Table

| Platform | Chrome cookies? | Aside cookies? | Playwright Chrome inject works? | Paste works? | Notes |
|---|---|---|---|---|---|
| **Reddit (old.reddit)** | ✅ `token_v2` + `reddit_session` | ✅ `token_v2` | ✅ Yes | ✅ Title + body | Use `?selftext=true` URL param to land on text-post form directly. Title is `textarea[name="title"]`, body is `textarea[name="text"]`. |
| **Dev.to** | ✅ `_Devto_Forem_Session` | ✅ `_Devto_Forem_Session` | ✅ Yes | ✅ Title + body | Title: `input[name="title"]`, body: `textarea[name="body_markdown"]`. |
| **LinkedIn** | ✅ `li_at` | ✅ `li_at` | ❌ Login wall | ❌ | `li_at` cookie is present but LinkedIn redirects to "Welcome back" password re-auth screen. Browser fingerprinting rejects Playwright Chrome even with valid session cookies. |
| **Twitter/X** | ✅ `guest_id` + `personalization_id` | ✅ `guest_id` | ❌ Login wall | ❌ | Twitter requires fresh auth — `guest_id` is not a session cookie, just a tracking cookie. No `auth_token` in Chrome or Aside cookies. |
| **Threads** | ✅ `csrftoken` + `ig_did` | ✅ `csrftoken` + `ig_did` | ❌ Login wall | ❌ | Threads requires Instagram auth — session cookies not sufficient for Playwright Chrome. |
| **Facebook** | ✅ `fr` + `wd` | ✅ `fr` + `wd` | ❌ Login wall | ❌ | `fr` + `wd` are tracking/localization cookies, not session cookies. No `xs` or `c_user` in the DB. |
| **Hacker News** | ❌ No HN cookies | ❌ No HN cookies | N/A | N/A | User never signed into HN in Chrome or Aside. |
| **Instagram** | ✅ `csrftoken` + `ig_did` + `mid` | ✅ same | N/A | N/A | No web compose flow — Instagram intentionally blocks web posting. Must use mobile app. |
| **Mastodon** | ❌ No Mastodon cookies | ❌ No Mastodon cookies | N/A | N/A | User not signed into Mastodon in any browser. |

## Cookie Sources

- **Chrome**: `~/Library/Application Support/Google/Chrome/Default/Cookies` — 637 cookies total, decrypted with `browserclaw cookies decrypt --keychain-service 'Chrome Safe Storage' --keychain-account 'Chrome'`
- **Aside**: `~/Library/Application Support/Aside/Default/Cookies` — 426 cookies total, decrypted with `browserclaw cookies decrypt --keychain-service 'Aside Safe Storage' --keychain-account 'Aside'`

Both DBs have overlapping social platform cookies (LinkedIn `li_at`, Reddit `token_v2`, etc.) because the user is signed into both browsers. However, **cookie presence ≠ session validity** — social platforms increasingly use browser fingerprinting to validate sessions, and Playwright Chrome (even `--browser-channel chrome`) is fingerprinted as a bot by LinkedIn, Twitter, Threads, and Facebook.

## Platform-Specific Paste Recipes (verified)

### Reddit (old.reddit.com — text post)

```
Compose URL: https://old.reddit.com/r/<sub>/submit?selftext=true
Title selector: textarea[name="title"]  (NOT input — it's a TEXTAREA on old.reddit)
Body selector:   textarea[name="text"]
```

The `?selftext=true` URL param is critical — without it, old.reddit defaults to the "link" tab (URL + title, no body textarea). Clicking the "text" tab via JS causes a navigation that destroys the Playwright execution context, so navigate directly to `?selftext=true` instead.

```javascript
// Paste JS (async IIFE — needs 'await' for the setTimeout):
const setVal = (el, v) => {
    const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    setter.call(el, v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
};
const titleField = document.querySelector('textarea[name="title"]') || document.querySelector('input[name="title"]');
const bodyField = document.querySelector('textarea[name="text"]');
if (titleField) setVal(titleField, TITLE_TEXT);
if (bodyField) setVal(bodyField, BODY_TEXT);
return (titleField ? 'TI' : 'NO_TI') + '|' + (bodyField ? 'BT' : 'NO_BT');
```

**Pitfall:** Playwright's `page.evaluate()` does NOT support top-level `await` in the evaluated string. Wrap the paste JS in an async IIFE: `'(async () => { ' + pasteJs + ' })()'`. Without this, `await new Promise(...)` inside the paste JS throws a syntax error.

### Dev.to

```
Compose URL: https://dev.to/new
Title selector:       input[name="title"]  (or #article_title)
Body selector:        textarea[name="body_markdown"]  (or #article_body_markdown)
```

Same `setVal` pattern as Reddit. Dev.to does NOT fingerprint-reject Playwright Chrome — cookies are accepted and the new-post page loads directly.

## Failure Modes (anti-bot fingerprinting)

The following platforms reject Playwright Chrome even with valid session cookies:

1. **LinkedIn** — redirects to `linkedin.com/login/?session_redirect=...` despite `li_at` cookie being present. The redirect happens at the JS layer (client-side anti-bot), not the HTTP layer. The cookie IS sent, but LinkedIn's fingerprinting script detects Playwright and redirects.
2. **Twitter/X** — shows login page. `guest_id` is NOT a session token (it's a tracking cookie). Twitter's `auth_token` cookie is NOT stored in Chrome/Aside — Twitter uses `localStorage` + `sessionStorage` for auth, not cookies.
3. **Threads** — shows login page. Threads auth is tied to Instagram's `sessionid` cookie which is NOT in the Chrome/Aside cookie DB (Instagram stores it in `localStorage`).
4. **Facebook** — shows login page. `fr` + `wd` are tracking/localization cookies. Facebook's `xs` + `c_user` session cookies are NOT in the Chrome/Aside cookie DB (Facebook stores them with `httpOnly` + `Secure` and they may be in a different profile or expired).

**Workarounds for fingerprint-rejected platforms:**
1. Use `aside repl` instead of Playwright — Aside's persistent daemon has a real Chrome fingerprint and may pass anti-bot checks (verified: LinkedIn compose modal loads in Aside, but requires the user to be signed in to LinkedIn in the Aside profile specifically).
2. Use `browserclaw cookies inject --headed` (visible Chrome) — sometimes headed mode passes fingerprinting where headless fails.
3. User manually logs in to the platform in Chrome/Aside, then re-decrypt cookies and re-inject.
4. Accept that some platforms require manual login and surface the draft text for copy-paste instead of automated staging.

## Cross-References

- `references/aside-recipes.md` — Aside REPL compose URLs + paste snippets
- `references/subreddit-rules.md` — per-subreddit spam rules (live-verified 2026-07-05)
- `~/.hermes/skills/browserclaw/SKILL.md` — cookie decrypt/inject skill (edge-case table now includes fingerprint-rejection row)