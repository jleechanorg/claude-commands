# OAuth Capture-and-Drive — Agent-driven consent via Aside

**When to use this**: An MCP server / CLI tool initiates an OAuth flow that:
1. Spawns `open <url>` (macOS) or `xdg-open <url>` (Linux) to launch the system browser
2. Waits on `127.0.0.1:<port>/callback` for the auth code
3. Returns control after the callback is captured

…and the user has the relevant Google/Microsoft/GitHub account already signed in to **Aside's Chrome profile** (verify with `aside account list`).

The pattern: **shadow `open` with a wrapper that logs the URL** → capture → **drive Aside Chrome to that URL** → the callback server (still listening) catches the code → MCP persists tokens → done.

Verified recipe from the 2026-07-06 Granola OAuth re-bind (Slack thread `C09GRLXF9GR/1783132301.864679`). The MCP server's OAuth endpoint was `https://mcp-auth.granola.ai/oauth2/authorize?...` and the callback was at `127.0.0.1:61200/callback`.

## Why the pattern works

- `mcporter` (and most Node.js OAuth clients) calls `spawn('open', [url])` — this resolves via `$PATH`. If we put a wrapper earlier on PATH, it intercepts.
- The wrapper logs the URL to a file, then `exec /usr/bin/open "$@"` so the wrapper is invisible to anything else.
- The actual URL mcporter tries to open often is NOT what you'd guess from the server URL. For Granola: server is `mcp.granola.ai` but OAuth authorize endpoint is `mcp-auth.granola.ai/oauth2/authorize` (subdomain + path different). Reading the captured URL avoids wrong-host debugging.
- Aside Chrome shares the user's signed-in Google account — the consent screen auto-completes because the user is already authenticated to the upstream IdP.

## Step-by-step

### 1. Wipe stale tokens (so OAuth actually re-runs)

```python
import json
d = json.load(open('$HOME/.mcporter/credentials.json'))
for k in d.get('entries', {}):
    d['entries'][k]['tokens'] = {}
    d['entries'][k]['state'] = None
    d['entries'][k]['codeVerifier'] = None
    d['entries'][k]['updatedAt'] = None
json.dump(d, open('$HOME/.mcporter/credentials.json','w'), indent=2)
```

If you skip this, the MCP client may use the cached grant and skip opening the URL entirely.

### 2. Create the wrapper directory + capture script

```bash
mkdir -p /tmp/<svc>-oauth-capture
cat > /tmp/<svc>-oauth-capture/open-wrapper.sh <<'EOF'
#!/bin/bash
# Capture the URL that mcporter (or other MCP client) passes to `open`
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> /tmp/<svc>-oauth-capture/captured-urls.log
exec /usr/bin/open "$@"
EOF
chmod +x /tmp/<svc>-oauth-capture/open-wrapper.sh
ln -sf /tmp/<svc>-oauth-capture/open-wrapper.sh /tmp/<svc>-oauth-capture/open
```

The `open` symlink is what matters — `mcporter` will resolve `open` from PATH and find the wrapper first.

### 3. Start the OAuth client in BACKGROUND

```bash
PATH="/tmp/<svc>-oauth-capture:$PATH" mcporter auth <server> \
    --config "$HOME/.config/<svc>-cli/mcporter.json" \
    --oauth-timeout 300000 > /tmp/<svc>-oauth-capture/mcporter.log 2>&1 &
```

Background is critical — the OAuth callback server (e.g. on port 61200) must stay listening while we drive the browser to the captured URL. `--oauth-timeout 300000` gives 5 min for the agent + user flow.

Wait 3-5 seconds, then verify the callback server is listening:

```bash
lsof -i :61200 -sTCP:LISTEN | head -3
```

### 4. Read the captured URL

```bash
cat /tmp/<svc>-oauth-capture/captured-urls.log | tail -1
```

This will look something like:
```
2026-07-06T19:18:04Z https://mcp-auth.granola.ai/oauth2/authorize?response_type=code&client_id=client_01KTWZ8YDNRS6Y7W4GG5777J4P&code_challenge=...&redirect_uri=http%3A%2F%2F127.0.0.1%3A61200%2Fcallback&state=8a62ef0d-...&scope=mcp&resource=https%3A%2F%2Fmcp.granola.ai%2Fmcp
```

Note: the actual host (`mcp-auth.granola.ai`) is NOT necessarily the same as the MCP server host (`mcp.granola.ai`). Don't guess — always read.

### 5. Drive Aside Chrome to the URL

```bash
aside repl "const p = await openTab('https://<captured-url>');
await new Promise(r => setTimeout(r, 6000));
const s = await snapshot(p, { interactive: true });
console.log('URL:', s.url);
console.log('TITLE:', s.title);
console.log('TREE:', s.tree);
await closeTab(p);"
```

The 6s wait is for the OAuth page + consent screen to render. If Chrome was already signed in to the relevant IdP (Google/MS/GitHub), the consent screen shows "Allow <app> to access your account?" and the user (or auto-sign-in) clicks "Allow".

**In our verified run**, the consent completed automatically because Chrome was already signed in as `$USER@your-project.com` and the OAuth requested that exact account.

### 6. Verify

The MCP client (mcporter) should print "Authorization complete" or similar to its stderr. Probe the new token via the MCP API:

```python
import json, urllib.request as r
d = json.load(open('$HOME/.mcporter/credentials.json'))
ent = next(iter(d['entries'].values()))
tok = ent['tokens']['access_token']
# call get_account_info or similar
```

If the probe returns the desired account, the OAuth succeeded.

### 7. Cleanup

```bash
rm -rf /tmp/<svc>-oauth-capture
```

The wrapper directory served its purpose; leaving it doesn't hurt but adds stale files.

## Common pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| `aside exec` returns "Codex usage limit" | The Codex-backed NL agent can't plan OAuth | Drop to `aside repl openTab(url)` — deterministic JS doesn't need Codex |
| CloudFront 403 on the captured URL | You reconstructed the URL wrong | Re-read the captured log; OAuth URL host is often different from MCP server host |
| Chrome doesn't auto-sign-in to the IdP | Consent screen asks for password | User must be signed in to that IdP in the Aside Chrome profile before the flow starts. `aside account list` confirms the Google account; for non-Google IdPs check Chrome profile manually. |
| The wrapper logs nothing | `open` resolved to `/usr/bin/open` instead of wrapper | Confirm `PATH` was actually overridden; check `which open` from the same shell the bg process spawned |
| mcporter prints "Authorization complete" but token probe shows old account | Re-used cached grant | Repeat step 1 (wipe stale tokens) before retrying |
| Callback server didn't start (no `LISTEN` on the port) | mcporter exited too fast | Run `mcporter auth` without backgrounding briefly to see why; or wait 10s and recheck |

## When NOT to use this pattern

- **No browser is signed in to the needed IdP**: User has to log in interactively before the agent can drive. Surface as a blocking question, not as agent work.
- **OAuth requires a confirmation code from email/SMS**: Step-up auth flows that need a code in another channel — agent can't retrieve those.
- **The service uses device code flow or app-link instead of browser redirect**: Different mechanism entirely.
- **The CLI doesn't call `open`/`xdg-open` but uses a library function**: Wrap at a different layer (e.g. monkey-patch the Node.js child_process spawn).

## Anti-patterns to avoid

- ❌ **Don't guess the OAuth URL** — always capture from the wrapper. Hosts and paths vary per-service.
- ❌ **Don't skip the wipe-stale-tokens step** — MCP clients re-use cached grants.
- ❌ **Don't run `mcporter auth` in foreground without a long timeout** — the wrapper intercept is async.
- ❌ **Don't leave the wrapper directory around permanently** — could accidentally intercept real `open` calls for other tools.
- ❌ **Don't try `aside exec` for OAuth flows** — Codex usage limits block the planning model.

## Verification checklist after the dance

1. `cat $HOME/.mcporter/credentials.json | jq '.entries.<service>.<id>.updatedAt'` shows a fresh timestamp
2. `get_account_info` MCP probe returns the desired account (e.g. `$USER@your-project.com`)
3. The MCP client (mcporter background process) logs "Authorization complete" or equivalent
4. The wrapper log file shows exactly one URL captured (if multiple, something went wrong and re-ran)
5. `/tmp/<svc>-oauth-capture/` is cleaned up

## Provenance

Captured 2026-07-06 during Granola OAuth re-bind to `$USER@your-project.com` workspace. Prior session's `granola-email-only-pipeline` skill claimed "Aside browser cannot do this OAuth" — that was incorrect for `aside repl` + URL capture; only `aside exec` is blocked by Codex usage limits.