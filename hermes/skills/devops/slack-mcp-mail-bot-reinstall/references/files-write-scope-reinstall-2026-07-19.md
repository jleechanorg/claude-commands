# `files:write` scope reinstall — browser-driven OAuth flow

End-to-end transcript of fixing the recurring `files:write` OAuth scope gap on
the `mcp_agent_mail` Slack app (app `A0A3WSV6BM1`, workspace `T09FXQ4LCQP`,
bot `B0A3MS7G08P`). This is the same gap that broke PR #7953, #8139, #8337,
and #8455 attachment uploads between 2026-07-13 and 2026-07-19.

## Root cause in one line

The `mcp_agent_mail` Slack app was granted every standard chat scope but NOT
`files:write`. Without `files:write`, the 3-stage `files.completeUploadExternal`
flow fails with `missing_scope: files:write`. Reinstall does NOT auto-add
scopes — the scope must be added to the app config first, then the OAuth
flow re-run to grant it.

## Three-token rule (critical — easy to miss)

After reinstall, the bot's `xoxb-...` token rotates. Three places need the
new value, not just one:

| Location | Variable | Approx. line |
|---|---|---|
| `~/.bashrc` | `HERMES_SLACK_BOT_TOKEN` | 951 |
| `~/.bashrc` | `SLACK_MCP_XOXB_TOKEN` | 949 |
| `~/.mcp_mail/credentials.json` | `SLACK_BOT_TOKEN` | n/a |

Failure mode: update only one → daemon picks up old token on next restart →
attachments still fail with `missing_scope`. Always update all three and
verify with `hash()` equality before restarting daemons.

## Which daemon reads which token

| Daemon | Process | Port | Token env var used |
|---|---|---|---|
| `mcp_agent_mail` (Python) | `mcp_agent_mail.cli serve-http` | 8765 | `SLACK_BOT_TOKEN` from `~/.bashrc` |
| `slack-mcp-server` (Go, korotovsky) | `slack-mcp-server -transport http` | 8006 | `SLACK_MCP_XOXB_TOKEN` (and `SLACK_MCP_XOXP_TOKEN`) |

Pitfall: `slack-mcp-server` warns
`Both SLACK_MCP_XOXP_TOKEN and SLACK_MCP_XOXB_TOKEN are set. Using User token (xoxp) for full features. Bot token will be ignored.`
If you want the bot (with `files:write`) used, also blank `SLACK_MCP_XOXP_TOKEN` or
remove it from bashrc. Don't trust it to fall back.

## `files:write:user` is NOT a real Slack scope

I tried to add `files:write:user` to the user-token scopes; Slack's scope picker
returned "No options" because the scope doesn't exist. The only valid scope name
is `files:write`. Slack uses ONE scope name regardless of whether the token is
`xoxb` (bot) or `xoxp` (user) — the difference is which app config grants it
(Bot Token Scopes vs User Token Scopes), not the scope name itself.

## OAuth page gotchas (when driving Playwright)

### Two "Reinstall" links exist — click the right one

On `https://app.slack.com/app-settings/<workspace>/<app>/oauth`, the page
contains two reinstall links:

| Link text | Href pattern | Effect |
|---|---|---|
| "reinstall your app" (yellow banner) | `https://api.slack.com/apps/<id>/install-on-team` | **NO-OP** — informational banner link |
| "Reinstall to $USER AI" (green button) | `https://slack.com/oauth/v2/authorize?client_id=...&team=...` | **ACTUAL reinstall** — rotates token |

`browser_console` shows `document.querySelectorAll('a[href*="oauth"]')` returning
both. Use the second. Selecting by text ("Reinstall to $USER AI") works only
in English — selecting by `href` regex `/oauth\/v2\/authorize/` is safer.

### OneTrust consent banner blocks the Allow button

The OAuth authorize page (`slack.com/oauth/v2/authorize?client_id=...`) shows a
OneTrust cookie consent dialog at the bottom with buttons like "Reject All" /
"Accept All" / "Manage Settings". Click **before** clicking Allow:

```python
page.locator("#onetrust-accept-btn-handler").click()  # may need #onetrust-pc-btn-handler too
page.wait_for_load_state("networkidle", timeout=10000)
```

Without this, the click on Allow silently fails (no navigation, no error).

### Scope-search input has a precise placeholder

The "Add permission by Scope or API method..." input is the canonical scope
selector. There's ALSO a documentation-search input near the bottom of the
OAuth page. They both look like text inputs. Target by placeholder:

```python
search_input = page.locator(
    "input[placeholder*='Add permission' i], input[aria-label='Select Scopes']"
).first
```

DO NOT use `input[type='search']` — matches the wrong input.

After typing the scope name (e.g. `files:write`), the dropdown shows the scope
with a clickable option. The scope is added to the requested scopes list
**only after you click the option AND see it appear in the list above the
search**. Then click "Save Changes" / "Update Scopes" before scrolling to the
top to click Reinstall.

## Browser path: Chrome Default cookies + browserclaw injection

Aside REPL is broken in this environment (`No last-focused window` even with
2 Aside windows open — verified via `osascript`, `activate`, window count).
Workaround path that works:

```bash
# 1. Decrypt Chrome's Slack + Google cookies
browserclaw cookies decrypt --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" --domain-filter '%slack.com%' --output /tmp/slack-chrome-cookies.json
browserclaw cookies decrypt --db "$HOME/Library/Application Support/Google/Chrome/Default/Cookies" --domain-filter '%google.com%' --output /tmp/google-chrome-cookies.json

# 2. Combine into a single cookie set
jq -s 'add' /tmp/slack-chrome-cookies.json /tmp/google-chrome-cookies.json > /tmp/all-cookies.json

# 3. Inject into a fresh Playwright Chromium via browserclaw
browserclaw cookies inject --cookies /tmp/all-cookies.json --goto "https://app.slack.com/app-settings/T09FXQ4LCQP/A0A3WSV6BM1/oauth" --headless
```

**Why Chrome not Aside:** Chrome's `d` cookie is legacy `xoxd-...` format that
authenticates against `slack.com/api/auth.test`. Aside's `d` cookie decrypts to
hex strings that return `not_authed`.

**Why not persistent profile copy:** Slack's web client doesn't trust cookies
copied from a Chrome profile dir to a fresh Chromium dir — lands on "Find your
workspace". The `browserclaw`-style fresh-context `add_cookies()` works.

## Verification (real API, not description)

After the OAuth flow lands back on the OAuth & Permissions page, the new token
is shown under "Bot User OAuth Token" / "User OAuth Token". Copy it, update
the three storage locations, then verify:

```bash
NEW_TOK="$(bash -lc 'source ~/.bashrc 2>/dev/null; echo -n "$HERMES_SLACK_BOT_TOKEN"')"

# 1. Scope check
curl -fsSI -X POST https://slack.com/api/auth.test -H "Authorization: Bearer $NEW_TOK" \
  | grep -i '^x-oauth-scopes' | tr ',' '\n' | grep files:write

# 2. Full 3-stage upload flow
UP=$(curl -fsS -X POST https://slack.com/api/files.getUploadURLExternal \
  -H "Authorization: Bearer $NEW_TOK" \
  -F "filename=test.txt" -F "length=4")
URL=$(echo "$UP" | python3 -c "import json,sys; print(json.load(sys.stdin)['upload_url'])")
ID=$(echo "$UP" | python3 -c "import json,sys; print(json.load(sys.stdin)['file_id'])")
echo -n "test" > /tmp/t.txt
curl -fsS -X POST "$URL" -F "file=@/tmp/t.txt"
curl -fsS -X POST https://slack.com/api/files.completeUploadExternal \
  -H "Authorization: Bearer $NEW_TOK" \
  -F "files=[{\"id\":\"$ID\",\"title\":\"OAuth scope fix test\"}]" | head -c 200
# Cleanup
curl -fsS -X POST https://slack.com/api/files.delete \
  -H "Authorization: Bearer $NEW_TOK" -F "file=$ID"
```

Expected: `ok:true` at every step. The bot identity in the response should be
`U0A4G7LDJ4R` (mcp_agent_mail) and team `T09FXQ4LCQP` ($USER AI).

## Restart the daemon

```bash
bash $HOME/.config/mcp-daemon/start-mcp-daemons.sh restart
# OR for soft bounce of just slack-mcp-server:
bash $HOME/.config/mcp-daemon/start-mcp-daemons.sh status  # see "DOWN"
# then wait ~30s — the watch loop restarts it
```

The supervisor process (`start-mcp-daemons.sh watch`, PID 84014) auto-restarts
individual daemons when DOWN. The script-level `restart` action stops ALL
daemons then starts them all — heavier than necessary for a single-token rotation.
For token rotation, just edit bashrc + credentials.json + restart the
specific supervisor (`start-mcp-daemons.sh supervise slack-mcp-server ...`).

## Files updated this session (2026-07-19)

- `/private/tmp/slack_admin_drive.py` — initial abandoned draft (Chrome profile copy failed)
- `/private/tmp/slack_admin_drive_v2.py` — phase 0 (verify auth) + phase 1 (add scope) reusable
- `/private/tmp/slack_admin_phase1b.py` — add user-scope (discovered `files:write:user` doesn't exist)
- `/private/tmp/slack_admin_phase2.py` — click Reinstall, navigate OAuth allow
- `/private/tmp/slack_admin_phase2c.py` — click green Reinstall on Install App page
- `/private/tmp/slack_admin_phase2d.py` — final working version (selects OAuth authorize link by `href` regex, dismisses OneTrust)
- `/private/tmp/update_tokens.py` — updates all three token storage locations

Backups created at `~/.bashrc.bak.<timestamp>` and
`~/.mcp_mail/credentials.json.bak.<timestamp>` — restore from these if
verification fails and you need to roll back.

## Related skills

- `~/.hermes/skills/evidence-attach-to-slack/` — the downstream skill that was
  failing because of this scope gap. Its 3-stage `files.completeUploadExternal`
  flow returns `missing_scope: files:write` until the OAuth reinstall lands.
- `~/.hermes/skills/slackbots-setup/` — earlier scope-and-reinstall flow that
  predates the browser-driven recipe. Use only as historical context.
- `~/.hermes/skills/slack-mcp-mail-bot-reinstall/SKILL.md` §1.1 — read this
  first to confirm bot identity, then come back here for the `files:write`
  upgrade path.