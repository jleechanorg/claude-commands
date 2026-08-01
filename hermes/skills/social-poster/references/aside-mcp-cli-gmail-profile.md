---
name: aside-mcp-cli-gmail-profile
description: Aside browser automation via HTTP MCP at 127.0.0.1:8013/mcp + the gmail (u0) profile. The most reliable automation path when the Chrome extension bridge is alive.
---

# Aside MCP + gmail profile — automation recipe

## Why this path

The Aside GUI app's Chrome extension bridge can die after daemon restarts (skill Lesson #9: "Aside daemon restart = sessions break"). When it's dead:
- `aside repl "await openTab(...)"` fails with `Chrome extension not connected for the requested browser profile`
- `aside "Open X"` NL agent fails identically
- Only the GUI works for manual browsing

When the bridge IS alive (which it usually is on a fresh GUI launch + first user interaction), the HTTP MCP at 127.0.0.1:8013/mcp is the cleanest automation entry point — better than `aside repl` because:
- Single persistent session (no per-call CLI spawn overhead)
- `fs` module available via `node:fs/promises` (CLI REPL blocks `require`)
- `display()` for inline image preview in tool results
- `sleep(ms)` helper instead of `new Promise(r => setTimeout(r, ms))`

## Active profile: use gmail (u0)

Default active account on this machine is `u1` ($USER@your-project.com). The gmail profile (u0) has a more reliable extension bridge handshake. User directive 2026-07-11: "use $USER@gmail.com profile next time".

For CLI:
```bash
aside --account u0 repl "..."
```

For MCP: the MCP server is account-agnostic — it drives whichever profile the active Aside GUI has loaded. To switch profiles: open Aside GUI → click profile switcher → select $USER@gmail.com → wait 3s → MCP calls now drive that profile.

## ⚠ Critical pitfalls (verified 2026-07-11)

1. **Do NOT send `notifications/initialized` between `initialize` and `tools/call`.** This kills the session: subsequent `tools/call` requests return `Bad Request: No valid session ID provided` even with the session-id header attached. The working pattern is: init → read `mcp-session-id` header → call `tools/call` immediately. Skip step 2 (the `notifications/initialized` notification).
2. **Top-level `await` IS allowed in the MCP REPL** — the REPL is in module mode. Earlier docs said "wrap in `(async () => { ... })();`" but that IIFE pattern swallows `console.log` output via the SSE stream (verified 2026-07-11 — IIFE-wrapped code returned empty content; top-level `await` + `console.log` returns data correctly).
3. **Session-id header is lowercase**: `mcp-session-id: <uuid>`. Sending `Mcp-Session-Id` returns `No valid session ID provided`.
4. **One init per session — reuse it.** If you re-init before every tool call, the response is empty (no error, no output). Persist the session-id from the first init and reuse it for all subsequent calls within the same workflow.

## MCP HTTP request flow (verified working)

### Step 1: Initialize → get session ID

```bash
curl -sS -i -X POST http://127.0.0.1:8013/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",
       "params":{"protocolVersion":"2024-11-05","capabilities":{},
                 "clientInfo":{"name":"social-poster","version":"1.0"}}}'
```

Response header includes `mcp-session-id: <uuid>` (lowercase). Extract it. Body is SSE:
```
event: message
data: {"result":{"protocolVersion":"2024-11-05",...},"jsonrpc":"2.0","id":1}
```

### Step 2: SKIP — do NOT send `notifications/initialized`

Sending this notification breaks subsequent `tools/call` requests with `Bad Request: No valid session ID provided`. Go directly to Step 3.

### Step 3: tools/list (optional)

```bash
curl -sS -X POST http://127.0.0.1:8013/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Aside MCP exposes a single tool: `repl` (wrapping the persistent JS REPL). Its inputSchema is `{title: string, code: string}`.

### Step 4: tools/call with `repl`

```bash
curl -sS -X POST http://127.0.0.1:8013/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call",
       "params":{"name":"repl","arguments":{
         "title":"Open Reddit + paste + screenshot",
         "code":"<JS code as string>"}}}'
```

The `code` arg can be 1000s of chars. The response is SSE with the captured console.log output + any image bytes passed to `display()`.

## REPL environment reference (from the MCP tool spec, verbatim)

- **Functions in scope:** `console.log`, `display` (image preview), `sleep(ms)`, `fetch(url)` (with user cookies)
- **Modules:** `fs` = `node:fs/promises`, `path` = `node:path`, `Buffer` = `node:buffer`. NO `require()` / `import` — use `fs.readFile` etc. directly.
- **Browser:** `page` = last opened tab, `tabs` = all open tabs (Playwright Page[]), `listBrowserTabs()` returns `OpenBrowserTab[]`
- **Persistent scope:** `const`/`let` variables persist across calls. Use different names each call to avoid collisions.
- **Top-level `await` works** (the REPL is in module mode). Do NOT wrap in `(async () => { ... })();` — IIFEs swallow `console.log` output via the SSE stream. Use top-level `await fetch(...)` then `console.log(await r.text())`.
- **`return` doesn't work** — use `console.log` to return data.
- **Image inspection:** `await display(Buffer)` shows the image inline in the tool result (don't write to disk first).

## Verified working patterns (2026-07-11)

### Sync console.log (sanity check)

```bash
curl -sS -X POST http://127.0.0.1:8013/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call",
       "params":{"name":"repl","arguments":{
         "title":"sanity",
         "code":"console.log(\"HELLO_FROM_MCP\");"}}}'
```

Returns: `data: {"result":{"content":[{"type":"text","text":"HELLO_FROM_MCP"}],...}}`

### Top-level await + console.log (async work)

```bash
curl -sS -X POST http://127.0.0.1:8013/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call",
       "params":{"name":"repl","arguments":{
         "title":"fetch",
         "code":"const r = await fetch(\"https://api.ipify.org\"); console.log(\"IP:\" + await r.text());"}}}'
```

Returns: `data: {"result":{"content":[{"type":"text","text":"IP:47.151.147.179"}],...}}`

### Reading + writing a draft file

```bash
curl -sS -X POST http://127.0.0.1:8013/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call",
       "params":{"name":"repl","arguments":{
         "title":"read draft",
         "code":"const txt = await fs.readFile(\"/tmp/drafts/foo/linkedin.md\",\"utf8\"); console.log(\"LEN:\" + txt.length);"}}}'
```

## Reusable Python client snippet (verified working 2026-07-11)

```python
import subprocess, json, re

def aside_mcp(code: str, title: str = "social-poster step", timeout: int = 120) -> str:
    """Drive Aside via HTTP MCP. SKIP notifications/initialized. Reuse session across calls.

    Returns the captured console.log output as a single string.
    """
    r = subprocess.run(
        ['curl', '-sS', '-i', '-X', 'POST', 'http://127.0.0.1:8013/mcp',
         '-H', 'Content-Type: application/json',
         '-H', 'Accept: application/json, text/event-stream',
         '-d', json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize",
             "params":{"protocolVersion":"2024-11-05","capabilities":{},
                       "clientInfo":{"name":"social-poster","version":"1.0"}}})],
        capture_output=True, text=True, timeout=10)
    # Extract lowercase mcp-session-id header
    session = None
    for line in r.stdout.split('\n'):
        if line.lower().startswith('mcp-session-id'):
            session = line.split(':', 1)[1].strip()
            break
    if not session:
        return f"NO_SESSION: {r.stdout[:200]}"
    # DO NOT send notifications/initialized — it kills the session

    body = json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/call",
        "params":{"name":"repl","arguments":{"title":title,"code":code}}})
    r = subprocess.run(['curl', '-sS', '-X', 'POST', 'http://127.0.0.1:8013/mcp',
        '-H', 'Content-Type: application/json',
        '-H', 'Accept: application/json, text/event-stream',
        '-H', f'mcp-session-id: {session}',  # lowercase header name
        '-d', body], capture_output=True, text=True, timeout=timeout)
    output = ""
    for line in r.stdout.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if 'result' in data and 'content' in data.get('result', {}):
                    for c in data['result']['content']:
                        if c.get('type') == 'text':
                            output += c['text'] + '\n'
                elif 'error' in data:
                    output += f"ERROR: {data['error']}\n"
            except json.JSONDecodeError:
                pass
    return output

def aside_mcp_session():
    """Return a reusable session_id. Call once per workflow, reuse across calls."""
    r = subprocess.run(
        ['curl', '-sS', '-i', '-X', 'POST', 'http://127.0.0.1:8013/mcp',
         '-H', 'Content-Type: application/json',
         '-H', 'Accept: application/json, text/event-stream',
         '-d', json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize",
             "params":{"protocolVersion":"2024-11-05","capabilities":{},
                       "clientInfo":{"name":"social-poster","version":"1.0"}}})],
        capture_output=True, text=True, timeout=10)
    for line in r.stdout.split('\n'):
        if line.lower().startswith('mcp-session-id'):
            return line.split(':', 1)[1].strip()
    return None

def aside_mcp_with_session(session: str, code: str, title: str = "social-poster", id_: int = 2, timeout: int = 120) -> str:
    """Call tools/call reusing an existing session_id (more efficient than re-init per call)."""
    body = json.dumps({"jsonrpc":"2.0","id":id_,"method":"tools/call",
        "params":{"name":"repl","arguments":{"title":title,"code":code}}})
    r = subprocess.run(['curl', '-sS', '-X', 'POST', 'http://127.0.0.1:8013/mcp',
        '-H', 'Content-Type: application/json',
        '-H', 'Accept: application/json, text/event-stream',
        '-H', f'mcp-session-id: {session}',
        '-d', body], capture_output=True, text=True, timeout=timeout)
    output = ""
    for line in r.stdout.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if 'result' in data and 'content' in data.get('result', {}):
                    for c in data['result']['content']:
                        if c.get('type') == 'text':
                            output += c['text'] + '\n'
                elif 'error' in data:
                    output += f"ERROR: {data['error']}\n"
            except json.JSONDecodeError:
                pass
    return output
```

## Stage-in-browser paste recipe (verified 2026-07-17)

Once the session is alive, this is the verified pattern for opening a platform's compose form and pasting draft text via Playwright's `locator().fill()`:

```js
const pg = await openTab('https://news.ycombinator.com/submit');
await pg.waitForLoadState('domcontentloaded');
await sleep(4500);
// detect login wall
const open = await pg.evaluate(() => ({
    url: location.href,
    login_prompt: /log in|sign in|welcome back|please log in/i.test(document.body.innerText),
}));
if (open.login_prompt) { console.log('LOGIN_WALL'); return; }
const loc = pg.locator("textarea[name='text']").first();
await loc.waitFor({state:'visible', timeout:10000});
await loc.click(); await sleep(300);
await loc.fill('paste content here');
await sleep(1500);
// verify
const v = await pg.evaluate(() => document.querySelector("textarea[name='text']")?.value?.length || 0);
console.log('VERIFIED len=' + v);
```

Verified selectors per platform (2026-07-17 with Chrome profile u0 = $USER@gmail.com):
- HN submit: `input[name='title']` + `textarea[name='text']` (no login required)
- Twitter compose: `div[contenteditable='true'][data-testid='tweetTextarea_0']` (signed in)
- Mastodon publish: `textarea` (first one — has placeholder "What's on your mind?") (signed in)
- Reddit /r/X/submit: `textarea[name='title']` + `textarea[name='text']` (old.reddit — no login required)
- Dev.to /new: `input#article-form-title` + `textarea#article_body_markdown` (REQUIRES LOGIN — often shows email/password form when u0 cookies stale)
- LinkedIn /feed: `div[contenteditable='true']` (REQUIRES LOGIN — clicking "Start a post" may be needed first)
- Facebook /: `div[contenteditable='true']` (REQUIRES LOGIN)
- Threads /: `div[contenteditable='true']` (REQUIRES LOGIN)

## Stage pitfalls (verified 2026-07-17)

1. **Each call MUST open the tab AND paste + verify + screenshot in ONE bundle.** Splitting across multiple MCP calls reopens a fresh tab and resets the form, so the paste text is lost.
2. **Screenshot via `await pg.screenshot()` then `console.log('SHOT_' + ss.toString('base64'))`** — base64 of ~85KB PNG. Put on its OWN console.log line so the JSON.stringify(result) for the RESULT marker is not bloated. Save from regex `SHOT_<var>:([A-Za-z0-9+/=]+)` separately from `RESULT_<var>=<json>`.
3. **MCP server degrades after ~6-8 bundled calls** with no response (subprocess returns 0 bytes). Symptom: `aside repl` returns `No last-focused window`. Recovery: `pkill -9 -f aside` (or wait 10s for MCP auto-recovery); restart Aside GUI; `aside account use u0`; `openTab` one warm-up tab; re-run.
4. **Reddit's old.reddit.com form is fragile** — pasting into the body textarea sometimes hangs Chrome entirely (no MCP response, 60s+ timeout). Workaround: run Reddit in a fresh MCP session per subreddit with title-only fill first, then body in a separate call.
5. **Cookies for LinkedIn / Facebook / Threads / Dev.to** in Chrome profile u0 (gmail) may have rotated between sessions. The page will show the login form (visible inputs `user_email`, `user_password` for Dev.to; `LinkedIn Login` page for LI). Fix: one-time manual login via Aside GUI to refresh cookies, then re-run.
6. **Don't re-initialize the MCP session between calls.** Re-init drops the prior session and the new one may have stale chrome context. Initialize ONCE at workflow start, reuse the session-id for all calls.
7. **Python subprocess capture buffer:** use `subprocess.Popen` with explicit `stdout=PIPE, stderr=PIPE, text=True` and `proc.communicate(timeout=...)` rather than `subprocess.run(..., timeout=...)`. The latter silently drops output if the subprocess writes after Python's timeout fires but before the process exits.

## Stage script template (verified working)

See `social-poster/scripts/stage_in_aside.py` and `/tmp/drafts/social-kimi-k3-2026-07-17/stage_v4.py` for a full implementation. Key points:
- One MCP call per platform; bundle open + paste + verify + screenshot in a single IIFE.
- Per-platform field selectors as table above.
- Retry once on empty response with a 2s sleep before re-init.
- Detect login_wall early and skip the paste step.

## When to fall back to Playwright + browserclaw / headless Stage-and-paste

Aside MCP path fails when:
- Chrome extension bridge is dead (no fix from this side — user must click the Aside dock icon to revive it)
- Reddit's network-security ban blocks the navigation (`You've been blocked by network security`)
- Platform requires fingerprint that Aside's Chromium doesn't have (rare)

Fallbacks (in priority order):
1. **Headless Playwright + Chrome/Aside cookies** (works for LinkedIn, Twitter, Facebook, Mastodon, Dev.to, Threads when valid cookies are available). See `social-poster/scripts/headless_stage_paste.py` for a self-contained script. Cookies decrypt via `browserclaw cookies decrypt` — BUT NOTE: `browserclaw` CLI is broken if its editable worktree at `$HOME/.worktrees/browserclaw-cookies` was deleted. Symptom: `ModuleNotFoundError: No module named 'browserclaw.cli'`. Fix: `pip install -e /path/to/repo --force-reinstall --no-deps` or recreate the worktree.
2. **Playwright + browserclaw cookie inject** — verified 2026-07-11 working for LinkedIn (signed in as Jeffrey Lee-Chan). Reddit blocks this path; LinkedIn / Twitter / Facebook / Threads / Dev.to / Mastodon should work.
3. **Manual paste** — user copies text from `.md` draft files into each platform's compose UI in their real browser.

## Provenance

- 2026-07-11: discovered HTTP MCP at 127.0.0.1:8013/mcp is alive and exposes `repl` tool with persistent scope + `fs` + `display()`. Session: Slack thread `C09GRLXF9GR/p1783809934.098269`.
- User directive: "aside browser is working now, and remember how to get it working and use $USER@gmail.com profile next time and use the mcp or cli its supposed dto work".
- MCP server path + session-id header pattern verified 2026-07-11 by sending init → reading `mcp-session-id` header → tools/call immediately (skipping notifications/initialized, which kills the session).
- Top-level `await` working pattern verified 2026-07-11: `const r = await fetch('https://api.ipify.org'); console.log('IP:' + await r.text());` returned the public IP correctly. Earlier "wrap in IIFE" guidance was wrong — IIFE wrapping causes empty console.log output via SSE.