# Aside REPL Session State — Corrected 2026-07-06

**This file SUPERSEDES the 2026-07-05 Playwright Chrome probe in `references/platform-session-status.md`.** The 2026-07-05 conclusions about LinkedIn / Twitter / Facebook / Threads being "login wall" apply ONLY to Playwright Chrome (which is fingerprinted as a bot). They do NOT apply to `aside repl`, which uses Aside's persistent daemon with a real Chrome fingerprint and survives long-lived cookie sessions.

## Verified auth state per platform (via `aside repl listBrowserTabs()` + visual screenshot inspection, 2026-07-06)

| Platform | Aside signed in? | Compose reachable via `openTab(compose-url)`? | Action needed |
|---|---|---|---|
| **LinkedIn** | ✅ Yes (Jeffrey Lee-Chan) | ⚠️ `feed/?shareActive=true` shows compose modal in screenshot. Some sessions trigger re-auth redirect to login modal. | If login wall shows: navigate to `/feed/` then click "Start a post". Paste via contentEditable. |
| **Twitter/X** | ✅ Yes (@jleechan2015) | ✅ `compose/post` opens compose modal with empty textarea, ready for paste. | Paste directly. For threads, click "Add post" button between tweets. |
| **Facebook** | ✅ Yes (Jeffrey Lee-Chan) | ⚠️ `/` shows feed + "What's on your mind, [Name]?" compose box at top. | Click compose box → paste → Share. |
| **Instagram** | ✅ Yes ($USER.2015) | ❌ Web compose blocked by Instagram. | Surface caption + hashtags for mobile app paste. |
| **Threads** | ⚠️ Partial — login wall shown but IG session alive | ⚠️ Click "Continue with Instagram" → auto-completes OAuth via IG. | One-click sign-in, then paste. |
| **Mastodon** | ❌ No — login wall with Create account / Login buttons | ❌ | Manual login required. |
| **Hacker News** | ⚠️ Partial — username pre-filled as ileechan2015 | ❌ | Enter password → /submit → paste title + body. |
| **Reddit (old.reddit)** | ⚠️ Partial — Google "Continue as Jeffrey" button visible | ❌ | One-click OAuth via Gmail session, then fill title (textarea[name="title"]) + body (textarea[name="text"]). Use `?selftext=true` URL param to land on text-post form. |
| **Dev.to** | ❌ No — login wall (Continue with GitHub/Google/Twitter) | ❌ | Manual login required. |

## How to verify auth state without trusting screenshots

```bash
# List all live tabs (works even if you've never opened them — Aside has them as recently-closed)
aside repl "const tabs = await listBrowserTabs(); console.log(tabs.map(t => t.url).join(' | '))"
```

On 2026-07-06 this returned 17 tabs including:
- `https://www.linkedin.com/feed/` → signed in
- `https://x.com/home` → signed in
- `https://www.facebook.com/` → signed in
- `https://www.instagram.com/` → signed in
- `https://www.threads.com/login/` → login wall (no session)
- `https://langfuse.com/cloud` → signed in

**Lesson:** When `stage_in_aside.py` opens a fresh `openTab(compose_url)` and gets a login-wall screenshot, **do NOT conclude the platform isn't signed in.** Check `listBrowserTabs()` first — if a signed-in tab on the same platform exists, the session IS valid; the compose-URL navigation just hit a session-revalidation redirect.

## Anti-pattern: trusting `aside account list` for per-platform auth

```bash
$ aside account list
* u0  $USER@gmail.com  signed in  profiles: Profile 0
  provider: google
```

This command shows the active Google account, NOT per-platform auth state. Twitter/FB/IG/LinkedIn are all signed in via this Google account's cookie session, but `account list` doesn't surface that. **Use `listBrowserTabs()` instead.**

## Pitfalls of programmatic paste via `aside repl`

1. **`document` scope does NOT persist across REPL calls.** Each `aside repl <code>` runs in a fresh JS context. Multi-step workflows like "open tab → click button → paste text → verify" do NOT compose across calls. Bundle everything in ONE async IIFE in a single call:

   ```javascript
   (async () => {
     const sleep = ms => new Promise(r => setTimeout(r, ms));
     const p = await openTab('https://twitter.com/compose/post');
     await sleep(4500);
     // Find the textarea, set value via React-friendly setter
     const ta = document.querySelector('textarea[data-testid="tweetTextarea_0"]');
     const proto = window.HTMLTextAreaElement.prototype;
     const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
     setter.call(ta, 'Your tweet text');
     ta.dispatchEvent(new Event('input', { bubbles: true }));
     await sleep(500);
     const shot = await annotatedScreenshot(p);
     console.log('B64:' + shot.base64Image);
   })()
   ```

2. **LinkedIn's compose uses contentEditable, not textarea** — the `setter.call(el, v)` trick doesn't work for `<div contenteditable="true">`. Use `el.innerHTML = text` + dispatch `input` event. Even so, React may not pick up the change reliably.

3. **Facebook's "What's on your mind" box requires a click first** to open a full modal — direct paste into the feed's small compose box doesn't work. Click + then paste.

## Verification: how to confirm the draft text actually landed in the compose field

Same-call bundle only — `document` doesn't persist:

```javascript
(async () => {
  const p = await openTab('https://twitter.com/compose/post');
  await new Promise(r => setTimeout(r, 4500));
  const ta = document.querySelector('textarea[data-testid="tweetTextarea_0"]');
  console.log('FIELD_LEN', ta ? ta.value.length : 'NO_FIELD');
  console.log('FIELD_HEAD', ta ? ta.value.slice(0, 80) : '');
})()
```

## Cross-references

- `references/platform-session-status.md` — 2026-07-05 Playwright Chrome probe (DO NOT use for `aside repl` workflows; keep for Playwright-only contexts)
- `references/aside-recipes.md` — `aside repl` snippets per platform
- `scripts/stage_in_aside.py` — the staging script; reads `drafts/*.md`, opens tabs, screenshots. Known bug: skips `reddit_<sub>` files with lowercase sub names (e.g., `reddit-localllama.md` won't match `reddit_LocalLLaMA`).