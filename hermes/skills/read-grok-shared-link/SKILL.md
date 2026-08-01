---
name: read-grok-shared-link
description: Read grok.com/share/* via Aside REPL openTab.
allowed-tools:
  - Bash
  - Read
context: inline
---

# Reading Grok Shared Conversation Links

The Grok share page (`https://grok.com/share/<shareLinkId>`) is a Next.js / Turbopack
React app. The conversation is held in client-side React state, NOT in the initial
HTML. All "normal" extraction paths return an empty / nearly-empty document:

| Path | What you get | Why it fails |
|---|---|---|
| `terminal: curl <share-url>` | HTML shell only (Next.js bundle, GTM, Sentry, no conversation body) | React app needs hydration |
| `web_extract(<share-url>)` | Empty / error — DDGS is search-only in this runtime; Firecrawl not configured | Same root cause |
| `browser_navigate(<share-url>)` | Returns `(empty page)` with `element_count: 0` | The browser tool snapshots BEFORE the React app hydrates; first response is the empty shell |
| **`aside repl openTab(<share-url>) + 8s wait + body.innerText`** | **Full conversation text** | Works — Aside waits for the page to settle, then the JS DOM has the messages |

## When to fire

Trigger this skill when **all three** of these hold:

1. The user pastes a `grok.com/share/<shareLinkId>` URL.
2. `terminal: curl <url>` returns the Next.js shell (Next.js chunks, GTM, Sentry
   baggage, React server-component scripts) without any conversation body.
3. `web_extract(<url>)` and `browser_navigate(<url>)` both return empty / `(empty
   page)`.

If the user has already pasted the conversation text in the chat, skip this skill.

## Recipe (Aside browser, headless)

```bash
# 1. Confirm Aside is alive
aside --version                     # 1.26.709.1533+
aside account list                 # should show * u0 $USER@gmail.com signed in

# 2. Open the share page in Aside
cat > /tmp/grok_fetch.js <<'JS'
const p = await openTab('https://grok.com/share/<shareLinkId>');
// Wait 6-10 seconds for React to hydrate and the conversation DOM to populate
await new Promise(r => setTimeout(r, 8000));
const text = await page.evaluate(() =>
  document.body ? document.body.innerText : 'NO BODY'
);
console.log('TEXT_LEN:', text.length);
console.log('---FULL TEXT---');
console.log(text);
JS
aside repl "$(cat /tmp/grok_fetch.js)"
```

Multi-line JS in `aside repl` MUST go through `$(cat file)` or a quoted heredoc — bash
tokenizes parens / template literals before Aside sees them. See
`~/.hermes/skills/aside-browser-default/references/aside-repl-api-gotchas.md` §
"Multi-line REPL scripts" for the full pattern.

## Recipe (Aside browser, scrolling for long threads)

If the conversation is longer than ~10K characters, the messages may be in a virtualized
list. The default `body.innerText` returns the rendered viewport only. To get the full
thread:

```bash
cat > /tmp/grok_fetch_long.js <<'JS'
const p = await openTab('https://grok.com/share/<shareLinkId>');
await new Promise(r => setTimeout(r, 6000));
// Scroll the message container to the bottom several times to force virtualized list to render
for (let i = 0; i < 6; i++) {
  await page.evaluate(() => {
    const sc = document.querySelector('main, [class*="scroll"], [class*="conversation"]')
               || document.scrollingElement;
    sc.scrollTop = sc.scrollHeight;
  });
  await new Promise(r => setTimeout(r, 1500));
}
const text = await page.evaluate(() => document.body.innerText);
console.log('TEXT_LEN:', text.length);
console.log('---FULL TEXT---');
console.log(text);
JS
aside repl "$(cat /tmp/grok_fetch_long.js)"
```

For very long threads (>50K chars), the output may be truncated by terminal capture. In
that case, dump the text to a file via the page-side `evaluate` → return as a base64
string → decode locally:

```bash
cat > /tmp/grok_dump.js <<'JS'
const p = await openTab('https://grok.com/share/<shareLinkId>');
await new Promise(r => setTimeout(r, 8000));
for (let i = 0; i < 6; i++) {
  await page.evaluate(() => {
    const sc = document.querySelector('main, [class*="scroll"], [class*="conversation"]')
               || document.scrollingElement;
    sc.scrollTop = sc.scrollHeight;
  });
  await new Promise(r => setTimeout(r, 1500));
}
const text = await page.evaluate(() => document.body.innerText);
console.log(Buffer.from(text).toString('base64'));
JS
aside repl "$(cat /tmp/grok_dump.js)" | tail -n +2 | base64 -d > /tmp/grok_thread.txt
wc -l /tmp/grok_thread.txt
```

## What you get

- The full conversation as plain text — every user message, every assistant response,
  with the timing metadata ("Worked for 16s") inline.
- The page sidebar (history list, profile info) is also in `body.innerText`. Use
  `String.split('Toggle Sidebar')[1]` to strip it, or filter the text you need.
- The conversation is in chronological order from the first user message.

## Pitfalls

- **No `closeAllTabs()` in the REPL** (verified 2026-07-31). Don't try to call it —
  wrap in `try/catch` if cleanup matters, or accept the tab stays open.
- **Aside REPL is stateless** — every `aside repl` call is a fresh process. Variables
  declared in one invocation don't persist. This is fine for the read-only fetch
  pattern, just be aware.
- **Stealth warning** — Aside may show a "Running WITHOUT residential proxies" warning.
  This is informational only.
- **Bot detection / auth wall** — if the body.innerText returns the sign-in wall
  content (not the conversation), the active Aside profile doesn't have access.
  Switch profiles with `aside --account u0` if needed. The user's `Profile 0 =
  $USER@gmail.com` is the default.
- **Don't try `browser_click` / `browser_type` from `aside repl`** — they don't exist
  in the REPL. The REPL is read-only. For OAuth or interactive flows, drop to the
  full `mcp__aside-mcp__*` tools if your runtime exposes them.

## When to skip this skill

- The user has pasted the conversation text directly in the chat, no fetch needed.
- The URL is a non-Grok share link (ChatGPT, Gemini, Claude, etc.) → different
  mechanism. For ChatGPT shared chats try `chatgpt.com/share/<id>` curl with a
  normal user-agent; for Gemini try `web_extract`; for Claude there's no public share
  mechanism.
- The user wants a screenshot, not the text → use `annotatedScreenshot()` in the
  Aside REPL after the page hydrates.

## Verification (quick)

```bash
aside --version                              # 1.26.x
aside account list | head -3                  # signed-in profile
aside repl "console.log('ok')"                # REPL works
```

If any fails, fall back to the next-most-likely path:

| Failure | Fallback |
|---|---|
| Aside not installed | `curl -fsSL https://releases.aside.com/install.sh \| bash` |
| Aside signed out | `aside account list` to confirm; user signs in via Aside GUI |
| Page returns auth wall | Report to user, ask for plain-text paste |
| `body.innerText` returns sidebar only | Conversation is virtualized — use the scrolling recipe above |
| Still empty after 8s | Wait longer (15s) or check if the shareLinkId is valid |

## Cross-references

- **Aside skill (canonical):** `~/.hermes/skills/aside-browser-default/SKILL.md` — full
  Aside CLI / REPL / MCP surface, headless default, OAuth capture pattern.
- **Aside REPL gotchas:** `~/.hermes/skills/aside-browser-default/references/aside-repl-api-gotchas.md`
  — why multi-line JS needs `$(cat file)`, why `screenshot()` doesn't exist, etc.
- **Browser-headless default:** `~/.claude/skills/browser-headless-default/SKILL.md` —
  broader headless policy; this skill is the Grok-specific instance.
- **Tavily-disabled rule:** `~/.claude/CLAUDE.md` section "Tavily is disabled" — DDGS is
  search-only, can't extract Grok share pages.

## Provenance

- v1.0.0 (2026-07-31): Created per Jeffrey's explicit request in Slack
  C0AUXSVFSA2/1785551502.183539 — "Use /skillify to remember how to read grok threads
  and shared links in general too in parallel." Triggered by the campaign-bible task
  where 4 prior extraction paths (curl, web_extract, browser_navigate, OG metadata)
  all returned 0-N chars of usable content, and Aside REPL with `openTab` + 8s wait +
  `body.innerText` returned the full 60K-character thread in one shot.
