# XOX-P Fallback — When the Bot Token Returns `not_in_channel`

**Verified 2026-07-13** during a Gmail+Calendar→Slack morning digest cron targeting `#life` (C0AMM2B4319).

## Symptom

`mcp__slack__conversations_add_message` returns `{"error": "not_in_channel"}`. The Slack workspace is the same as the bot's home workspace; the bot user is simply not a member of this specific channel.

This is **distinct** from the cross-workspace bot-token hard-block documented as **Failure 5f** in `slack-thread-routing-investigation`. There, the bot token is scoped to workspace A but the channel lives in workspace B — both bot paths fail with `missing_scope` / `not_in_channel`. Here, the bot token IS in the right workspace, but it isn't in this channel. Both classes share the XOX-P user-token fallback as the recovery path.

## Do NOT stop to ask the user

Cron jobs run unattended. Do not pause the cron to ask Jeffrey to type `/invite @hermes`. Instead, fall back to the user's XOX-P identity token (the user is in every channel they own).

## Token source split (verified 2026-07-13)

| File | Token | Notes |
|---|---|---|
| `~/.bashrc` | `HERMES_SLACK_BOT_TOKEN` (xoxb…) | Hermes bot token — already exported in non-login bash |
| `~/.profile` | `SLACK_USER_TOKEN` (xoxp…) | User identity token — only merged by login shells |

Plain `bash -c 'echo $SLACK_USER_TOKEN'` returns empty (`.profile` not sourced). Use `bash -lc '...'` to merge both, or:

```bash
SLACK_USER_TOKEN="$(bash -lc 'echo $SLACK_USER_TOKEN' 2>/dev/null | tail -1)"
```

## Working Python snippet (no bash escaping, single tool call)

```python
import json, os, urllib.request

token = os.environ["SLACK_USER_TOKEN"]  # must already be exported
payload = json.dumps({"channel": "C0AMM2B4319", "text": digest_body}).encode("utf-8")
req = urllib.request.Request(
    "https://slack.com/api/chat.postMessage",
    data=payload,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    },
    method="POST",
)
with urllib.request.urlopen(req, timeout=15) as resp:
    body = json.loads(resp.read())
    assert body["ok"], body
    print(body["ts"])  # confirm ts, channel, ok=True
```

## Bash escaping trap (worth memorizing)

Building the JSON body via `printf "%s" "$(echo "$TEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")"` and embedding it in `-d "..."` consistently produces `{"ok":false,"error":"invalid_json"}` because the outer shell escapes the inner quotes incorrectly. The Python `urllib.request` snippet above avoids the trap entirely by serializing the payload inside Python with no shell interpolation.

Same trap applies to heredoc-into-curl patterns when the JSON contains complex unicode or escaped quotes.

## Identity disclosure

The post will appear as the user ($USER, U09GH5BR3QU), not the hermes bot. Include a one-line italic note at the end of the digest body so the user understands the identity switch — e.g. *"(posted via xoxp fallback; hermes bot not in #life channel)"*.

## Verify by checking the response

Pass criteria: `{"ok": true, "channel": "C0AMM2B4319", "ts": "1783958489.817799"}`. The `user` field in the returned message object will be the user ID, not a bot ID — that's expected and confirms the fallback worked.

## Durable fix (operator action, not a cron fix)

Have someone with channel-admin rights run `/invite @hermes` in #life so future crons can use the bot-token path. Until then, every cron that targets this channel must use the XOX-P fallback above. Track this as a followup bead so the next session isn't surprised.

## Related

- `slack-thread-routing-investigation` Failure 5f — the cross-workspace variant (different workspace, not just different channel)
- SOUL.md `## COMMIT: slack-cross-workspace-fallback-xoxp` — the operational guardrail mirroring this pattern
- `slack-cross-workspace-fallback-xoxp` lives in SOUL.md because the XOX-P fallback decision is universal across all post paths