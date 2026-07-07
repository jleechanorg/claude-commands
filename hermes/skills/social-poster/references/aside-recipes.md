# Platform Character Limits + Aside Recipes

## Character Limits (hard + recommended)

| Platform | Hard limit | Recommended | "See more" cutoff |
|----------|-----------|-------------|-------------------|
| LinkedIn body | 3,000 | 1,300-1,500 | ~210 chars |
| LinkedIn comment | 1,250 | — | — |
| LinkedIn short (pre-comment) | 300 | 300 | full visible |
| Hacker News title | 80 | ≤70 | full visible |
| Hacker News body | ~10,000 | 400-800 (first paragraph) | ~400 chars |
| Twitter single tweet | 280 | 240 | full visible |
| Twitter thread | no limit | ≤7 tweets | — |
| Reddit title | 300 | ≤80 | full visible |
| Reddit body | 40,000 | 800-1,500 | varies |
| Reddit comment | 10,000 | — | — |
| Threads | 500 | 300-450 | full visible |
| Facebook | 63,206 | 80-150 (engagement) / 1,000-2,500 (thought-leadership) | ~480 chars |
| Instagram caption | 2,200 | 1,500-2,000 | ~125 chars |
| Instagram hashtags | 30 | 8-15 | — |
| Mastodon | 500 (default) / 5,000 | 500 | full visible |
| Dev.to title | 80 | ≤70 | full visible |
| Dev.to description | 140 | 140 | OG card |
| Dev.to body | 100,000 | 1,500-4,000 | first 200 chars |

## Aside Recipes (per-platform compose URL)

Use `aside repl` to open a new tab and navigate to the compose URL. The user must be signed in (Aside handles cookie persistence via the `$USER@gmail.com` Google profile).

### LinkedIn

```js
// open compose modal
const p = await openTab('https://www.linkedin.com/feed/?shareActive=true');
// fill the post — requires text input ref from snapshot
const s = await snapshot(p, { interactive: true });
// find the contenteditable div with the post textarea, then:
// await type(ref, draftText);
```

### Hacker News

```js
const p = await openTab('https://news.ycombinator.com/submit');
// fill `title` (input ref) with title
// fill `url` (input ref) with link OR `text` (textarea ref) with body
// DO NOT submit
```

### Twitter / X

```js
const p = await openTab('https://twitter.com/compose/post');
// fill the tweet textarea
// DO NOT click "Post"
// for threads, use the "+" button to add tweets
```

### Reddit (per sub)

**CRITICAL:** Use `?selftext=true` URL param to land directly on the text-post form. Without it, old.reddit defaults to the link-post tab, which navigates through the "link vs text" UI and triggers a session re-auth redirect that LOOKS like a login wall in screenshots. Verified 2026-07-06 for r/LocalLLaMA, r/OpenAI, r/Rag.

```js
const sub = 'LocalLLaMA';
const p = await openTab(`https://old.reddit.com/r/${sub}/submit?selftext=true`);
await new Promise(r => setTimeout(r, 4500));
// fill title (textarea on old.reddit) + body (textarea[name="text"])
// DO NOT submit
```

Title selector: `textarea[name="title"]` (NOT input — it's a TEXTAREA on old.reddit)
Body selector:   `textarea[name="text"]`

### Threads

```js
const p = await openTab('https://www.threads.net/@$USER');
// click "What's new?" composer
// fill textarea
// DO NOT submit
```

### Facebook

```js
const p = await openTab('https://www.facebook.com/');
// click "Create post" → "Create post"
// fill contenteditable div
// DO NOT submit
```

### Instagram

```js
// Instagram has NO web compose. Surface draft + mobile instructions:
// 1. Open the profile / home page so the user can see context
const p = await openTab('https://www.instagram.com/');
// 2. Print the draft caption + alt text for manual paste on mobile
```

### Mastodon

```js
const instance = 'mastodon.social'; // configurable
const p = await openTab(`https://${instance}/publish`);
// fill textarea, optional CW field
// DO NOT submit
```

### Dev.to

```js
const p = await openTab('https://dev.to/new');
// fill title, description, body markdown
// DO NOT click "Publish"
```

## Screenshot Pattern (Playwright Page-object, verified 2026-07-06)

The simplest, most reliable screenshot recipe uses `page.screenshot()` returning a Node Buffer:

```js
const p = await openTab('https://twitter.com/compose/post');
await p.waitForLoadState('domcontentloaded');
await new Promise(r => setTimeout(r, 4500));  // let JS-driven UI mount
const shot = await p.screenshot();
console.log('B64:' + shot.toString('base64'));
```

The older `annotatedScreenshot(pageObj)` API still works but throws on `annotatedScreenshot(null)`. Prefer `page.screenshot()`. See `references/aside-repl-playwright-pattern.md` for 6 verified idioms (paste into compose fields, click submit buttons, iframe access via frameLocator, list live tabs, etc.).

For DOM inspection (which text input is present, username, etc.):

```js
const state = await p.evaluate(() => ({
  url: window.location.href,
  hasTitleField: !!document.querySelector('input[name="title"]'),
  hasBodyField: !!document.querySelector('textarea[name="text"]'),
  hasComposeDiv: !!document.querySelector('div[contenteditable="true"]'),
  username: document.querySelector('a#me')?.textContent ?? null,
}));
console.log('STATE', JSON.stringify(state));
```

⚠ **DOM-only detection is unreliable for compose-vs-login classification.** Always vision-verify the screenshot before declaring a platform compose-ready. SKILL.md lesson #8. User feedback 2026-07-06: "Many of these screenshots are login screens I wanna find the draft post screen / Still not good enough."

## Closing Tabs (cleanup)

```js
await closeTab(p);
// or
await closeAllTabs();
```

Default behavior: leave tabs open for human inspection. Use `--close-tabs` flag in `stage_in_aside.py` to auto-close after screenshot.