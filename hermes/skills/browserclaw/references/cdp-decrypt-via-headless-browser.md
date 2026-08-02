# Decrypting Chrome v20 cookies via headless Chrome + CDP

## When `browserclaw cookies decrypt` returns 0-cookie (or all-empty) output

Chrome v120+ uses **App-Bound Encryption (ABE)** for cookie values in addition to Safe Storage. Safe Storage alone is no longer sufficient to decrypt values when read directly from the SQLite DB by an external Python process — the key derivation requires Chrome's running process and v20 prefix.

**Symptom:** `browserclaw cookies decrypt` runs successfully but writes a JSON with every `value: ""` (or fails silently for v20). Length fields show non-zero, but `value` is empty.

**Why:** `cookies.py` decrypts `v10`/`v11` (PBKDF2 + AES-128-CBC, see `os_crypt_mac.mm` in Chromium source) but Chrome v120+ writes `v20` with App-Bound Encryption that only the running browser can decrypt. `browserclaw` was last verified against v11.

**Workaround (verified 2026-07-18, TaxDome cookie dump, 247 unique tax-domain cookies recovered):** launch a fresh headless Chrome with `--remote-debugging-port=N` pointing at a copy of the user's profile, then ask Chrome itself to dump cookies via CDP `Network.getAllCookies` — Chrome's in-process decryptor fills the values.

## The recipe

### Step 1 — Prepare a temporary profile copy

The user's running Chrome locks its `SingletonLock` and `Cookies` SQLite. Make a separate user-data-dir for the headless instance:

```bash
TMPDATA=/tmp/<job>-chrome-debug
rm -rf "$TMPDATA"
mkdir -p "$TMPDATA/Default"
SRC="$HOME/Library/Application Support/Google/Chrome/Default"
for f in Cookies 'Local State' Preferences 'Secure Preferences' 'Web Data' 'Login Data'; do
  cp -L "$SRC/$f" "$TMPDATA/Default/$f" 2>/dev/null
done
```

(Do **NOT** copy `SingletonLock`, `SingletonSocket`, or `SingletonCookie` — those are runtime lock files.)

### Step 2 — Launch headless Chrome with remote debugging

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless=new --disable-gpu --no-sandbox \
  --remote-debugging-port=9222 \
  --user-data-dir="$TMPDATA" --profile-directory=Default \
  about:blank > /tmp/<job>/chrome-cdp.log 2>&1 &
```

Verify CDP is up:

```bash
sleep 4
curl -fsS http://127.0.0.1:9222/json/version | head -10
```

### Step 3 — Dump decrypted cookies via CDP `Network.getAllCookies`

```js
// /tmp/<job>/cdp-cookies.mjs  (Node 18+, deps: ws)
import WebSocket from 'ws';

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page');
if (!page) { console.error('no page target'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0;
const send = (method, params = {}) => new Promise((resolve) => {
  const cmd = { id: ++id, method, params };
  function listener(data) {
    const msg = JSON.parse(data.toString());
    if (msg.id === cmd.id) { ws.off('message', listener); resolve(msg.result); }
  }
  ws.on('message', listener);
  ws.send(JSON.stringify(cmd));
});
ws.on('open', async () => {
  const result = await send('Network.getAllCookies');
  const tax_domains = /(<your-domain-list>)/i;
  const filtered = (result.cookies || []).filter(c => tax_domains.test(c.domain));
  console.log('TOTAL_TAX_COOKIES=' + filtered.length);
  for (const c of filtered) {
    console.log(JSON.stringify({
      domain: c.domain, name: c.name, path: c.path, value: c.value,
      expires: c.expires, httpOnly: c.httpOnly, secure: c.secure,
      sameSite: c.sameSite, session: c.session,
    }));
  }
  ws.close();
});
```

```bash
cd /tmp/<job> && npm install ws --silent
node /tmp/<job>/cdp-cookies.mjs > /tmp/<job>/cookies-decrypted.jsonl
```

### Step 4 — Reuse the cookies

The JSON Lines output is in CDP shape, not Playwright storage_state. Convert it:

```python
import json
cookies = [json.loads(line) for line in open('/tmp/<job>/cookies-decrypted.jsonl')
            if line.strip() and not line.startswith('TOTAL_')]
state = {'cookies': [
    {'name': c['name'], 'value': c['value'], 'domain': c['domain'],
     'path': c['path'], 'expires': c['expires'], 'httpOnly': c['httpOnly'],
     'secure': c['secure'], 'sameSite': c['sameSite']}
    for c in cookies
], 'origins': []}
json.dump(state, open('/tmp/<job>/storage_state.json', 'w'))
```

Then drive via `browserclaw cookies inject --cookies /tmp/<job>/storage_state.json --goto <portal-url>` — or just `curl` with `--cookie-jar` / `--cookie` built from the JSON.

## What this gets you that `browserclaw cookies decrypt` doesn't

| Aspect | `browserclaw cookies decrypt` (v11 path) | CDP-via-headless (v20 path) |
|---|---|---|
| Cookie *names* visible | ✅ Yes | ✅ Yes |
| Cookie `length(value)` | ✅ Yes | ✅ Yes |
| Decrypted `value` for v10/v11 cookies | ✅ Yes | ✅ Yes |
| Decrypted `value` for v20 (ABE) cookies | ❌ Returns empty | ✅ Yes (Chrome decrypts in-process) |
| Works without launching a browser | ✅ Yes | ❌ Needs a headless Chrome instance |
| Cost | ~50ms | ~4s launch + 200ms CDP |

## Aside / Brave / Edge

Same recipe, swap:

| Browser | Path | CDP port |
|---|---|---|
| Google Chrome | `~/Library/Application Support/Google/Chrome/Default/` | 9222 (default) |
| Aside | `~/Library/Application Support/Aside/Default/` | 9223+ |
| Brave | `~/Library/Application Support/BraveSoftware/Brave-Browser/Default/` | 9224+ |
| Edge | `~/Library/Application Support/Microsoft Edge/Default/` | 9225+ |

Each can run headless in parallel — Chrome and Aside simultaneously confirmed (TaxDome drive, 2026-07-18). Just use distinct `--remote-debugging-port=N` and distinct `--user-data-dir=`.

## Verified worked example (2026-07-18, TaxDome drive)

109 decrypted tax-domain cookies from Chrome Default + 138 from Aside Default = **247 unique** cookies across fidelity.com, schwab.com, morganstanleyclientserv.com, etrade.com/us.etrade.com (Aside only), wellsfargo.com, wealthfront.com (Aside only), snapchat.com/accounts.snapchat.com, gemini.google.com, taxdome.com (incl. orenheneainc.taxdome.com).

**Important timing caveat:** Cloudflare `_abck` / `bm_sz` / Akamai `_abck` are rotated every 5-10 minutes per session. Drive portals within that window after the CDP dump, or re-dump if you pause.

## What this does NOT solve

- Cloudflare Turnstile on the *initial* page load — headless UA is on their deny list. Once you've got the decrypted session cookies, use a normal visible Chrome (or `chrome --remote-debugging-port=9222` to keep the user's existing tabs) and inject cookies via CDP `Network.setCookie` rather than launching a fresh headless instance.
- Fingerprint-auth sites (LinkedIn, Twitter/X, Threads, Facebook) — see the existing skill's "Edge cases / failure modes" row for that.

## Cleanup

When done:

```bash
# Kill the headless Chrome(s)
lsof -iTCP:9222 -sTCP:LISTEN -P -n -t 2>/dev/null | xargs -I{} kill -TERM {} 2>/dev/null
lsof -iTCP:9223 -sTCP:LISTEN -P -n -t 2>/dev/null | xargs -I{} kill -TERM {} 2>/dev/null

# Remove the temp profile (it may have been mutated)
rm -rf /tmp/<job>-chrome-debug

# Shred the cookies dump
shred -u /tmp/<job>/cookies-decrypted.jsonl /tmp/<job>/storage_state.json
```