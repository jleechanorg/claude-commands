# Slack delivery is DEAD — fallback playbook

When the EA sweep's only delivery target (DM `D0AFTLEJGJU`) cannot be reached,
this recipe defines what to do instead. First seen: **2026-07-12 16:01 PDT** —
Slack proactively revoked the bot token after detecting it in a public GitHub
commit. The brief could not be delivered through any known Slack path.

## Symptoms (in order of appearance)

| # | Probe | Expected result when dead |
|---|---|---|
| 1 | `mcp__slack__conversations_history channel_id=D0AFTLEJGJU limit=3` | `account_inactive` |
| 2 | `mcp__slack__conversations_add_message channel_id=D0AFTLEJGJU text=test` | `account_inactive` |
| 3 | `curl -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" https://slack.com/api/auth.test` | `{"ok":false,"error":"token_revoked"}` |
| 4 | `curl -H "Authorization: Bearer $SLACK_USER_TOKEN" https://slack.com/api/auth.test` | `{"ok":false,"error":"token_revoked"}` |
| 5 | `curl -X POST "$SLACK_WEBHOOK_URL" -d '{"text":"test"}'` | 404 / 403 |
| 6 | `curl -X POST "$SLACK_MCP_MAIL_WEBHOOK_URL" -d '{"text":"test"}'` | 403 |
| 7 | `tail -50 ~/.hermes/logs/gateway.error.log \| grep -i invalid_auth` | matches present |

If 1–2 fail AND 3–6 also fail, the entire inbound + outbound Slack surface is
dead. The brief cannot be delivered. Skip step 6 of SKILL.md (post to DM) and
run the fallback below.

## Fallback delivery — write brief to disk + return as cron reply

```bash
mkdir -p ~/.hermes/memory/briefings/$(date +%Y-%m-%d)/
brief_path=~/.hermes/memory/briefings/$(date +%Y-%m-%d)/$(date +%H%M)-ea-sweep.md
cat > "$brief_path" << 'BRIEF_EOF'
# EA Sweep — YYYY-MM-DD HH:MM TZ

## CRITICAL: Slack delivery DEAD — brief NOT posted to DM
<one-line: which token failed, which email/scan triggered revocation>

## Calendar / Email / System / Slack action items
<standard brief sections, omitting Slack channel reads since they cannot be done>

## BLOCKED
This brief could NOT post to DM D0AFTLEJGJU. Restoration checklist:
1. Regenerate Slack bot token at https://api.slack.com/apps/<APP_ID>
2. Regenerate webhook at https://jleechanai.slack.com/services/<SERVICE_ID>
3. Rotate/install any third-party tokens revoked in the same incident
4. Purge leaked secrets from public GitHub history (`git filter-repo` +
   force-push) — otherwise re-issued tokens get re-revoked within hours

Brief archived to: <brief_path>
BRIEF_EOF
```

Then return the brief **as your cron reply** (cron delivery is automatic and
will reach the operator's mailbox/feed even when Slack is dead). This is
already the platform contract for cron jobs.

## Diagnostic script (one-shot)

```bash
bash -lc 'source ~/.bashrc && python3 << PY
import json, urllib.request, urllib.parse, os, sys

def slack_get(url, token=None):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    raw = urllib.request.urlopen(req, timeout=10).read()
    return json.loads(raw)

print("=== auth probes ===")
for label, env in [("bot", "HERMES_SLACK_BOT_TOKEN"), ("user", "SLACK_USER_TOKEN")]:
    t = os.environ.get(env, "")
    if not t:
        print(f"  {label}: {env} NOT SET")
        continue
    d = slack_get("https://slack.com/api/auth.test", t)
    print(f"  {label}: ok={d.get(\"ok\")} error={d.get(\"error\",\"-\")} team={d.get(\"team\",\"-\")}")

print("=== webhook probes ===")
for label, env in [("general-webhook", "SLACK_WEBHOOK_URL"),
                   ("mail-webhook", "SLACK_MCP_MAIL_WEBHOOK_URL")]:
    url = os.environ.get(env, "")
    if not url:
        print(f"  {label}: {env} NOT SET")
        continue
    try:
        req = urllib.request.Request(url, data=b"{\"text\":\"test\"}",
            headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req, timeout=10)
        print(f"  {label}: OK")
    except urllib.error.HTTPError as e:
        print(f"  {label}: HTTP {e.code} (token revoked or webhook invalidated)")
    except Exception as e:
        print(f"  {label}: {type(e).__name__}: {e}")

print("=== mcp slack probe ===")
PY'
```

## Restoration checklist (post to DM when user confirms tokens regenerated)

When the operator says tokens are back, **do not** skip the dedup check — a
brief delivered while tokens were dead should still get a follow-up that
covers the *actual* Slack state at delivery time. The archival file in
`~/.hermes/memory/briefings/YYYY-MM-DD/HHMM-ea-sweep.md` is the source of
truth for what was prepared but not delivered.

## Root cause of 2026-07-12 16:01 PDT incident

A `backup/jeffreys-macbook-pro/` directory inside the public
`jleechanorg/claude-commands` repo contained three secret-bearing files
committed at SHA `10ca1b09`. Slack and Notion security scanners detected them
within minutes of each other and auto-revoked:

1. Slack bot token (App `A0APZAC659P`, owner `U09GH5BR3QU`) — found in
   `backup/jeffreys-macbook-pro/openclaw/openclaw.staging.json`
2. Slack webhook URL `B0A0GUCQ934/peE5jpdZRMTwc9yTBMkD8Aqv` — found in
   `backup/jeffreys-macbook-pro/cursor/chats/0b13d4f30c45c04038f5935bf12f68d8/.../store.db`
3. Notion API key (workspace "Claude mcp access") — found in same store.db path

**Critical follow-up**: the leaked file is still live at
`https://github.com/jleechanorg/claude-commands/blob/10ca1b09de2c19b581d41903326f0985c1e5a2b0/backup/jeffreys-macbook-pro/...`.
Re-issuing the same tokens without purging will trigger an immediate re-revoke
loop. Use `git filter-repo --path backup/jeffreys-macbook-pro/ --invert-paths`
on a fresh worktree and force-push, then rotate any other secrets that ever
lived in that directory.

## Pitfalls

- **Don't assume Slack is healthy just because the gateway is up.** The
  gateway can run perfectly while the bot token is revoked. Always probe
  `auth.test` or attempt one read+one write before declaring Slack delivery
  healthy.
- **Don't silently swallow the failure.** If the brief cannot be delivered,
  the cron reply itself IS the delivery channel. Make the un-delivered state
  explicit at the top of the reply so the operator knows to investigate.
- **Don't try webhook URLs as a "free" fallback.** They were invalidated in
  this incident; other webhooks may have been too. Always probe before
  posting, never trust the env var is still alive.
- **Don't forget the cron silent-window check.** If a brief DID deliver in
  the last 30 min and the next sweep hits Slack-dead, do not double-post.
  Write the brief to disk and reply [SILENT] — the dedup is about *brief
  content reaching the operator*, not about *exactly one Slack post*.

## Partial-recovery case: token rotated, cron deliver misrouted (2026-07-12)

The 2026-07-12 20:01 PDT sweep hit a THIRD failure mode that's between
"Slack dead" and "Slack healthy" — partial recovery where:

1. The bot token in `~/.bashrc` was rotated (new prefix `xoxb-95418…`,
   bot identity `U0A4G7LDJ4R` `mcp_agent_mail`).
2. The cron job `clawchief:ea-sweep-hourly` (`a790a5b54e61`) still has
   `deliver: slack:C0AMM2B4319` (#life) — a channel the new bot is NOT in.
3. The gateway's stored token (loaded at launch 17:47 PDT) is the OLD
   revoked token, so gateway.outbound socket-mode fails with `invalid_auth`
   even though gateway.outbound REST works for newly-spawned shells.
4. The prior sweep's `last_delivery_error` reads `account_inactive` — this
   misleads operators into thinking "Slack still dead" when in fact the
   token IS alive, the config is just stale.

**Recipe (run at the top of the sweep):**

```bash
# 1. Token alive?
curl -fsS -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  https://slack.com/api/auth.test
# If ok=true → token works. Proceed.

# 2. Resolve the CURRENT operator DM (the old one belongs to the revoked bot).
curl -fsS -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"users":"U09GH5BR3QU"}' \
  https://slack.com/api/conversations.open
# Use the returned channel.id (e.g. D0A418NEHHC). NOT $JLEECHAN_DM_CHANNEL.

# 3. Verify write path with a tiny probe.
curl -fsS -X POST -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"channel\":\"<DM_ID>\",\"text\":\"[ea-probe] $(date)\"}" \
  https://slack.com/api/chat.postMessage

# 4. Post the full brief to the resolved DM.
```

**Then in the brief itself, surface the layered failures** so the operator
sees both the recovery AND the remaining config drift:
- ✅ Bot token recovered to `mcp_agent_mail` (U0A4G7LDJ4R).
- 🟡 Cron `clawchief:ea-sweep-hourly` `deliver` is stale → still `slack:C0AMM2B4319`.
  Update to `slack:D0A418NEHHC` so future sweeps deliver cleanly.
- 🟡 Gateway `ai.hermes.prod` has pre-rotation token in env (started 17:47,
  `~/.bashrc` rotated 18:42). Restart to pick up new tokens.
- 🔴 Bot is NOT a member of `#all-$USER-ai`, `#worldai`, `#life`,
  `#agent-orchestrator`, `#worldai-alerts`, etc. → operator asks in those
  channels are invisible until the bot is invited.

**Diagnostic shell one-liner** (combine all probes):

```bash
bash -lc 'source ~/.bashrc && python3 << PY
import json, urllib.request, os
token = os.environ["HERMES_SLACK_BOT_TOKEN"]
def call(method, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        f"https://slack.com/api/{method}", data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())
print("auth.test:", call("auth.test").get("ok"))
dm = call("conversations.open", {"users": "U09GH5BR3QU"}).get("channel", {}).get("id", "-")
print("operator DM:", dm)
probe = call("chat.postMessage", {"channel": dm, "text": "[ea-probe] " + __import__("datetime").datetime.now().isoformat()})
print("write probe:", probe.get("ok"), "ts=", probe.get("ts","-"))
PY'
```

**Why this case matters:** the canonical `slack-delivery-dead-recipe.md`
flow assumes `auth.test` returns `ok=false`. If the sweep sees `ok=true`
but the cron deliver still fails, the fix is NOT the dead-Slack playbook
— it's (a) post to the resolved DM directly, and (b) flag the cron config
drift for operator action.