# Diagnose "the granola thing isn't working" — full transcript recipe

When the user says any of:
- "is the granola thing working?"
- "did we finally get it working?"
- "why aren't I getting my granola emails?"
- "send me my granola notes"
- "the granola pipeline is broken"

Run these three checks in order. Each one takes <2s and identifies the most common failure mode at each layer.

## Check 1: Script exists?

```bash
ls -la $HOME/.hermes/scripts/granola-to-drive.py
```

**PASS expected**: file exists, ~17K, owned by $USER.

**FAIL pattern A — file missing**: launchd will exit 2 ("can't open file") every hour. Restore:
```bash
cp $HOME/Repos/granola-exporter/scripts/granola-to-drive.py \
   $HOME/.hermes/scripts/granola-to-drive.py
python3 -c "import ast; ast.parse(open('$HOME/.hermes/scripts/granola-to-drive.py').read())"
```

The deployed copy occasionally vanishes (seen 2026-07-06 with 2932 broken runs). Cause unknown — could be launchd overlay writes, could be a deploy glitch. After restoring, no launchd bounce needed — next tick picks it up.

**FAIL pattern B — file size ~16K (old version)**: the deployed copy is stale vs the repo. The XML parser + rate-limit retry queue landed in commits `7fd5c9e` + `7646a64` to `feat/email-only-export` on 2026-07-06. If you have not merged that branch to main, the deployed script may be missing these. Re-deploy:
```bash
cd $HOME/Repos/granola-exporter
git checkout origin/feat/email-only-export -- scripts/granola-to-drive.py
cp scripts/granola-to-drive.py $HOME/.hermes/scripts/granola-to-drive.py
```

## Check 2: launchd running cleanly?

```bash
launchctl print gui/$(id -u)/ai.hermes.schedule.granola-to-drive | \
  grep -E "state =|runs =|last exit"
```

**PASS expected**: `state = waiting` or `spawn scheduled`, `runs >= 1`, `last exit code = 0`.

**FAIL pattern A — last exit code = 2 with "can't open file"**: script file missing. Go back to Check 1 pattern A.

**FAIL pattern B — last exit code = 2 with traceback in err log**: paste the traceback into the diagnose; the most common recent causes are:
- Granola MCP rate-limit cooldown running long
- `xml.etree.ElementTree.ParseError` (we fixed this with the email-bracket escape — commit `7fd5c9e`)
- `KeyError: 'raw'` on `extract_text` if MCP response shape changed (re-check tool surface with `mcporter granola`)

**FAIL pattern C — state = not running, no runs**: launchd never started. Check the plist:
```bash
ls -la $HOME/Library/LaunchAgents/ai.hermes.schedule.granola-to-drive.plist
plutil -lint $HOME/Library/LaunchAgents/ai.hermes.schedule.granola-to-drive.plist
# If plist valid but service not loaded:
launchctl bootstrap gui/$(id -u) $HOME/Library/LaunchAgents/ai.hermes.schedule.granola-to-drive.plist
```

**FAIL pattern D — runs = 2932, last exit code = 2 with "can't open file"**: the script-vanished issue from Check 1 pattern A. Restore, no launchd bounce needed.

## Check 3: Which Granola account is bound?

This is THE diagnostic for the most common subtle failure — wrong-account OAuth.

```python
import json, urllib.request as r, urllib.error as e
d = json.load(open('$HOME/.mcporter/credentials.json'))
ent = next(iter(d['entries'].values()))
tok = ent['tokens']['access_token']
req = r.Request('https://mcp.granola.ai/mcp',
  data=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call',
                    'params':{'name':'get_account_info','arguments':{}}}).encode(),
  headers={'Authorization':f'Bearer {tok}','Content-Type':'application/json',
           'Accept':'application/json, text/event-stream'},
  method='POST')
try:
    resp = r.urlopen(req, timeout=30)
    for L in resp.read().decode().splitlines():
        if L.startswith('data:'):
            info = json.loads(json.loads(L[5:].strip())['result']['content'][0]['text'])
            print('email:', info.get('email'))
            print('workspace:', info.get('active_workspace',{}).get('display_name'))
except e.HTTPError as exc:
    print(f"HTTPError: {exc.code} {exc.reason}")
except Exception as exc:
    print(f"probe failed: {type(exc).__name__}: {exc}")
```

**PASS expected**: `email: $USER@your-project.com`, `workspace: Jeffrey's Workspace`

**FAIL pattern A — `email: $USER@gmail.com`**: WRONG ACCOUNT. The user has multiple Google workspaces in Chrome and the cached OAuth grant is for the gmail one. Re-auth flow:

1. Tell the user to open Chrome → https://app.granola.ai/settings/connected-apps → find "mcporter (granola)" → Disconnect
2. Either run `granola auth` in their terminal (browser opens, they sign in as your-project.com), OR drive the OAuth via Aside per the recipe in `aside-browser-default/references/oauth-capture-and-drive.md`
3. Re-run the probe to confirm `email: $USER@your-project.com`

**FAIL pattern B — HTTPError 401 Unauthorized**: token expired or revoked. Same re-auth flow as pattern A.

**FAIL pattern C — "Rate limit exceeded" body**: the probe is being throttled. Wait 30s+ and retry. If persistent, the OAuth grant may be locked — re-auth.

**FAIL pattern D — `email` is empty / `workspace` is empty**: Granola returned malformed JSON. Wait, retry, then if persistent, log to Slack and check Granola status page.

## Combine into status message

After running all three, post a one-line summary to the originating Slack thread:

| Findings | Message |
|---|---|
| All pass | `✅ pipeline healthy — last exit 0, N emailed total, bound to your-project.com` |
| Check 1 fail (file missing) | `🔴 script vanished again — restored from repo` |
| Check 2 fail (exit 2, file gone) | `🔴 launchd exit 2 — script missing, restored` |
| Check 3 fail (gmail) | `⚠️ still bound to $USER@gmail.com — need to revoke + re-auth at app.granola.ai/settings/connected-apps` |
| Check 3 fail (401) | `⚠️ Granola token expired — re-auth needed` |
| Check 3 pass + Check 2 fail (rate limit) | `🟡 throttled — N meetings deferred to retry queue at ~/.hermes/state/granola-rate-limited.json` |

Do NOT include raw command output in the Slack message — translate to one of the above statuses.

## Cron recipe for this diagnose

Auto-watch every 20m with a one-shot cron:

```
hermes cron create "20m" --name 'granola-pipeline status (20m)' \
  --deliver 'slack:<channel>:1783132301.864679' --repeat 1
```

With this prompt body (verbatim):
```
Run the 3-check diagnose sequence (script exists, launchd clean, account-bound).
Post a one-line status to the originating Slack thread:
- All pass → "✅ pipeline healthy ..."
- Check 1 fail → "🔴 script vanished — restored"
- Check 2 fail → "🔴 launchd exit N — ..."
- Check 3 fail with email=gmail → "⚠️ still on gmail — revoke + re-auth"
- Check 3 fail with 401 → "⚠️ token expired — re-auth"
- 4+ meetings in rate-limited.json → "🟡 X meetings throttled — next hourly tick"

Do NOT include raw command output in the Slack message.
```

This is the same recipe referenced from the main skill — duplicated here for self-contained diagnose runs.