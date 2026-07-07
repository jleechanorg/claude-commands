---
name: granola-email-only-pipeline
description: Operate the jleechanorg/granola-exporter email-only pipeline — fetch Granola meeting notes via MCP, send ONE consolidated email per run to $USER@gmail.com ONLY when new notes exist, silent exit otherwise. No Google Docs, no Slack. Use when user says "granola export", "send me my granola notes", "the granola pipeline", "is the granola thing working", "did we finally get it working", or mentions notes/email from the granola-exporter repo.
---

# Granola Email-Only Pipeline

Single-purpose: every hour, pull the latest Granola meetings from MCP, and if any have NEW notes (not already emailed), send one consolidated email to `$USER@gmail.com` with the notes inline. Silent exit otherwise. No Google Docs. No Slack.

## Canonical path

- Repo: `jleechanorg/granola-exporter` (local: `$HOME/Repos/granola-exporter`)
- Script: `scripts/granola-to-drive.py`
- Deployed copy: `~/.hermes/scripts/granola-to-drive.py`
- Plist template: `launchd/ai.hermes.schedule.granola-to-drive.plist`
- Deployed plist: `~/Library/LaunchAgents/ai.hermes.schedule.granola-to-drive.plist`
- State file: `~/.hermes/state/granola-uploaded.json` (key: `emailed`)
- Logs: `~/.hermes/logs/granola-to-drive.launchd.{out,err}.log`

## Two-account model (THE foot-gun — read carefully)

The pipeline reads from one Granola workspace and emails from another Gmail account. They are DIFFERENT and easy to confuse:

| Purpose | Account | Notes |
|---|---|---|
| Granola MCP source (where notes come from) | `$USER@your-project.com` | Browser OAuth, browser-only flow, CANNOT be done from agent. Currently often wrong-account. |
| Gmail sender + recipient (where notes go) | `$USER@gmail.com` | The ONLY `gog` account that works — `$USER@your-project.com` has no DWD configured for service-account `115856862775645064959`. |
| Slack home channel | (none) | Pipeline does NOT post to Slack. If user asks for Slack post, push back. |

If the wrong Granola workspace is bound, the pipeline returns 0 meetings and silently exits. **That is correct behavior, not a bug.** The "email only when notes exist" contract is what the user asked for.

## Diagnose "the granola thing isn't working" (run all three)

```bash
# 1. Is the script even deployed? (Most common failure mode — file vanishes.)
ls -la $HOME/.hermes/scripts/granola-to-drive.py
# If missing → restore from $HOME/Repos/granola-exporter/scripts/granola-to-drive.py
#   cp $HOME/Repos/granola-exporter/scripts/granola-to-drive.py \
#      $HOME/.hermes/scripts/granola-to-drive.py

# 2. Is launchd running and exiting cleanly?
launchctl print gui/$(id -u)/ai.hermes.schedule.granola-to-drive | grep -E "state =|runs =|last exit"

# 3. Which Granola account is bound? (THE diagnostic that catches the wrong-account foot-gun)
python3 -c "
import json, urllib.request as r, urllib.error as e
d = json.load(open('$HOME/.mcporter/credentials.json'))
e = next(iter(d['entries'].values()))
tok = e['tokens']['access_token']
req = r.Request('https://mcp.granola.ai/mcp',
  data=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'get_account_info','arguments':{}}}).encode(),
  headers={'Authorization':f'Bearer {tok}','Content-Type':'application/json','Accept':'application/json, text/event-stream'},
  method='POST')
resp = r.urlopen(req, timeout=30)
for L in resp.read().decode().splitlines():
    if L.startswith('data:'):
        info = json.loads(json.loads(L[5:].strip())['result']['content'][0]['text'])
        print('email:', info.get('email'))
        print('workspace:', info.get('active_workspace',{}).get('display_name'))
"
# Expected: email: $USER@your-project.com
# If $USER@gmail.com instead → re-auth needed (see below).
```

## Re-auth Granola to your-project.com — TWO-STEP (revoke first, then auth)

**Critical pitfall (verified 2026-07-06):** Re-running `granola auth` does NOT switch accounts if a valid OAuth grant already exists for the OTHER workspace. The MCP client re-uses the cached `client_01KTWZ8YDNRS6Y7W4GG5777J4P` grant. **You must revoke the existing grant first.**

Step 1 (user action in Chrome):
```
1. Visit https://app.granola.ai/settings/connected-apps
2. Find "mcporter (granola)" → click Disconnect
```

Step 2 (user action in their terminal — agent CANNOT do this):
```bash
granola auth    # browser opens → user signs in as $USER@your-project.com
```

Step 3 (agent — verify):
```bash
# Re-run the get_account_info probe above. Expected: email: $USER@your-project.com
```

## Aside `exec` cannot do this OAuth (verified 2026-07-06)

`aside exec` for OAuth flows returns `Codex error: The usage limit has reached` — the Codex model backs `aside exec` and is rate-limited.

**But `aside repl` CAN** — see "OAuth re-auth via Aside browser" below for the full 7-step recipe. The wrapper-around-`open` pattern + `aside repl openTab(url)` works whenever the user is already signed in to the relevant IdP in the Aside Chrome profile.

Workaround when `aside repl` also doesn't help: copy the `~/.mcporter/credentials.json` from a machine that already has the right OAuth. Otherwise this is a hard blocker.

## Manual run (test)

```bash
# Preview what would be emailed (no email sent, no state written)
python3 $HOME/.hermes/scripts/granola-to-drive.py --preview

# Dry-run (same as --preview, kept for back-compat)
python3 $HOME/.hermes/scripts/granola-to-drive.py --dry-run

# Force re-email everything (ignores state file)
python3 $HOME/.hermes/scripts/granola-to-drive.py --force

# Override recipient for one-off test
GRANOLA_RECIPIENT_EMAIL=someone@example.com python3 $HOME/.hermes/scripts/granola-to-drive.py --preview
```

## After editing the script

```bash
cd $HOME/Repos/granola-exporter
# Edit on a fresh worktree from origin/main per pr-branch-from-main.mdc
git fetch origin
git checkout -B feat/<name> origin/main
# ... edit ...
plutil -lint launchd/ai.hermes.schedule.granola-to-drive.plist  # plist sanity
python3 -c "import ast; ast.parse(open('scripts/granola-to-drive.py').read())"  # py syntax
python3 scripts/granola-to-drive.py --preview  # smoke test
git commit -am "..." && git push -u origin HEAD
gh pr create --base main --title "..." --body "..."
# After PR merged (or for self-deploy):
cp scripts/granola-to-drive.py $HOME/.hermes/scripts/granola-to-drive.py
launchctl bootout gui/$(id -u)/ai.hermes.schedule.granola-to-drive 2>&1 | head
launchctl bootstrap gui/$(id -u) $HOME/Library/LaunchAgents/ai.hermes.schedule.granola-to-drive.plist
launchctl kickstart -k gui/$(id -u)/ai.hermes.schedule.granola-to-drive
```

## What "fixed" looks like

A healthy pipeline run produces ONE of these in the err log:

- `[ts] start; recipient=$USER@gmail.com sender=$USER@gmail.com lookback=N limit=25 dry_run=False preview=False force=False` then `[ts] sweep: N meetings total, M with notes, K new, J previously emailed` then either `[ts] emailed K new note(s) to $USER@gmail.com` OR `[ts] no new notes to email; exiting silently`.
- Exit code 0.
- If N meetings were rate-limited: `[ts] skipping <uuid> — rate limited (will retry next hourly tick)` for each, then `[ts] recorded X rate-limited meeting(s) for retry`. State file at `~/.hermes/state/granola-rate-limited.json` will list the deferred IDs and the next run will pick them up.

## Rate-limit recovery pattern (added 2026-07-06)

Granola MCP rate-limits aggressively — ~30s+ cooldown after a burst of detail fetches. The pipeline handles this via:

1. `meeting_has_notes()` returns False when `get_meetings` returns `"Rate limit exceeded"` body
2. `detail_rate_limited()` returns True for those
3. The script saves the rate-limited IDs to `~/.hermes/state/granola-rate-limited.json` (does NOT mark as `emailed`)
4. Next hourly tick picks them up automatically — no manual intervention
5. `clear_rl_state(ids)` removes successfully-emailed IDs from the retry queue on next send
6. Throttle: `time.sleep(2.0)` between detail fetches to avoid triggering the limiter

**Optimal cadence:** ≤5 meetings per run (`--limit 5`), 2s sleep between fetches. Cron default of 25 meetings per hour always trips the limit; either lower the cron limit or accept that 19/21 will land on retry tick #2 ~2 hours later.

## What "broken" looks like

- `last exit code = 2` — unhandled exception. Check err log for traceback.
- `last exit code = 126` — script file missing from `~/.hermes/scripts/` (the `cp` step wasn't run after the PR).
- `can't open file '$HOME/.hermes/scripts/granola-to-drive.py'` — same as 126. Re-copy from repo.
- `sweep: 0 meetings total` with a known-good Granola account (>= 1 meeting visible in app) → likely wrong-account OAuth. Run `mcporter auth granola` (browser will open) or use Aside to drive the OAuth flow.
- `sweep: N meetings total, 0 with notes` but `<summary>` content visible in `get_meetings` response → bug: `_extract_xml_text` not walking into `<meeting><summary>` (PATCHED in repo). Symptom: every meeting has notes but `meeting_has_notes(merged)` returns False.

## Granola MCP responses are XML, not JSON

Every MCP tool returns XML in the inner `result.content[*].text` field, not JSON. Real shape:

- `list_meetings`: `<meetings_data from="..." to="..." count="N"><meeting id="..." title="..." date="..."><known_participants>...</known_participants></meeting>...</meetings_data>` — DOES NOT carry notes content.
- `get_meetings`: `<meetings_data>...<meeting>...<known_participants>...</known_participants><summary>### Notes content here...</summary></meeting></meetings_data>` — carries notes in `<summary>` element.
- `get_meeting_transcript`: returns `"Transcripts are only available to paid Granola tiers"` for free accounts.

So the script must:
1. Detect XML vs JSON (starts with `<` vs `{`)
2. Parse XML with `xml.etree.ElementTree`
3. Escape bare `<email@domain>` patterns INSIDE text content before parsing (`<$USER@your-project.com>` looks like a tag)
4. Walk one level deeper for notes: `root.iter("meeting")` then `meeting_el.find("summary")`

## OAuth re-auth via Aside browser (Granola-specific application)

The full 7-step recipe (shadow `open` on PATH, capture URL mcporter tries to open, drive Aside Chrome to that URL via `aside repl openTab(url)`, verify callback landed in mcporter) lives in the **`aside-browser-default` skill** at `~/.hermes/skills/aside-browser-default/references/oauth-capture-and-drive.md`. Use that reference as the primary doc; the Granola-specific steps below are only the deltas.

**Granola deltas** (in addition to the generic recipe):

- The captured OAuth URL host is `mcp-auth.granola.ai/oauth2/authorize?...` — **NOT** `mcp.granola.ai/authorize` (the latter returns 403 from CloudFront even with valid client_id + state).
- The captured URL contains `code_challenge` (PKCE S256) and `state` — DO NOT try to reconstruct these from `~/.mcporter/credentials.json`. The values written there BEFORE mcporter starts the auth flow are correct; once mcporter starts, the running process owns them. Use the URL from the captured log verbatim.
- After the OAuth completes, verify via `get_account_info` MCP tool:
  ```python
  # see "Diagnose "the granola thing isn't working"" section above for full probe
  ```
- Expected post-auth state: `email: $USER@your-project.com`, `workspace: 'Jeffrey's Workspace'`.
- The callback server listens on `127.0.0.1:61200`. After OAuth completes, mcporter persists tokens and the process exits — lsof on the port will go from LISTEN to empty.

**Granola-specific gotcha**: even with a successful OAuth, the script's first run will show `0 meetings total` if the user has another workspace (e.g. `$USER@gmail.com`) in the same browser session. Cross-check `get_account_info` — if it shows `email: $USER@gmail.com` instead of `$USER@your-project.com`, re-do the OAuth or revoke the gmail-side grant at https://app.granola.ai/settings/connected-apps.

**End-state**: `get_account_info` MCP tool returns `{email: $USER@your-project.com, workspace: 'Jeffrey's Workspace'}`.

## Status cron recipe (auto-watch the wrong-account trap)

When reporting status or watching this pipeline, attach a one-time 20m cron that runs the 3-check diagnose sequence and posts a single line to the originating thread. Use `deliver: origin` and `repeat: once` so it doesn't pollute with cron loops. Suggested prompt:

```
1. `ls -la $HOME/.hermes/scripts/granola-to-drive.py` — flag if missing
2. `launchctl print gui/$(id -u)/ai.hermes.schedule.granola-to-drive 2>/dev/null | grep -E "state =|runs =|last exit code"` — capture runs + last exit code
3. Run the get_account_info probe. If email == $USER@gmail.com: post "still on gmail — run `granola auth` in your terminal". If your-project.com: post "bound to your-project.com — notes flowing to $USER@gmail.com".
```

Post one-line status to the Slack thread via `mcp__slack__conversations_add_message`. Do NOT include raw command output in the Slack message.

See `references/diagnose-granola-pipeline.md` for the full 3-check recipe with FAIL patterns (A through D for each check) and the canonical status-message format.

## Provenance

Built 2026-07-04 from jleechanorg/granola-exporter PR #1 by AO worker. User request: Slack thread `C09GRLXF9GR/1783132301.864679` ("just email $USER@gmail.com only when there are notes to export") + correction `1783132813.934959` ("Dont be stupid this is the account to use $USER@your-project.com"). Prior 3-output pipeline (Google Docs + Email + Slack) collapsed to email-only.

**Patched 2026-07-06:** Added 3-check diagnose recipe, OAuth-revoke-first foot-gun (verified — re-running `granola auth` does NOT switch accounts), `aside exec` cannot do OAuth (Codex usage limit) BUT `aside repl` CAN drive OAuth via the captured-URL dance (recipe in `aside-browser-default` skill's `references/oauth-capture-and-drive.md`), most-common-failure = script-vanished (exit 126, 2932 broken runs), Gmail sender = `$USER@gmail.com` (not your-project.com — your-project.com has no DWD for service-account `115856862775645064959`), status cron recipe, Granola MCP returns XML (not JSON) with notes inside `<meeting><summary>` wrapper.