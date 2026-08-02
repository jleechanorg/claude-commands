# EA Sweep re-delivery: `mcp__slack__conversations_add_message` "text must be a string" hard reject

Channel: `D0AFTLEJGJU` (DM between $USER and the MCP Agent Mail bot, post landed at `ts 1783969555.163109`).
Parent sweep message: `ts 1783969409.999669` (12:00 PT EA sweep delivered via `SLACK_MCP_XOXP_TOKEN` because the bot is locked out of every monitored channel — `mcp_agent_mail` is `member of 0 channels` since the 2026-07-12 rotation).

## What happened

The 12:00 PT EA sweep brief was re-delivered to `D0AFTLEJGJU/1783969409.999669`. I composed a single consolidated re-triage reply (corrections to the brief + autonomous next-30-min list + blocked-on-you list) and tried to post it via `mcp__slack__conversations_add_message`. The tool returned:

```
{"error":"text must be a string"}
```

Tried twice — both attempts rejected with the same error, even though every argument (`channel_id`, `thread_ts`, `text`) was passed as a string-typed value.

## Why this is a NEW failure mode (not in any prior reference)

| Failure | Symptom | Status |
|---|---|---|
| Failure 4 (symbol mangle, `references/2026-07-08-dice-audit-failure4-narration-leak.md`) | Tool returns `ok:True`, post lands, but `[]`/`+`/`:foo`/`!=` symbols are mrkdwn-mangled | Documented 2026-07-08 |
| **NEW (this instance)** | Tool returns `text must be a string` hard error, NO post attempted | Documented 2026-07-13 |
| Failure 5 (wrong thread_ts) | Tool returns `ok:True`, post lands at channel root or in a different thread | Documented 2026-06-14 |

The "text must be a string" failure is a hard pre-flight reject — the underlying `chat.postMessage` is never even called. This is qualitatively different from Failures 4 and 5 (both of which successfully post, just with the wrong content or location). When you see `text must be a string`, do not retry the MCP tool — switch to the curl fallback immediately.

## Diagnostic — how to disambiguate this from Failure 4 vs Failure 5

```python
# Test: is the tool returning a hard error or a soft mangle?
import json
result = mcp__slack__conversations_add_message(channel_id=..., thread_ts=..., text=...)
parsed = json.loads(result)
if "error" in parsed and "text must be a string" in str(parsed):
    # THIS failure mode — switch to curl + SLACK_USER_TOKEN immediately
    fallback()
elif parsed.get("ok") is True:
    # Either a successful post (verify with conversations_replies), Failure 4 mangle, or Failure 5 wrong thread
    verify_with_conversations_replies(parsed.get("ts"))
else:
    # Unknown error — try curl with both HERMES_SLACK_BOT_TOKEN and SLACK_USER_TOKEN
    pass
```

## Root-cause hypothesis (unverified)

The MCP runtime tool wrapper that converts function-call arguments to the underlying JSON-RPC payload has a schema validator that rejects the payload before the server is contacted. Three plausible triggers (none confirmed):

1. **Multi-line `text` with embedded newlines.** The function-call framework may coerce large multi-line strings (e.g., 2400-char consolidated replies with section breaks) into something other than `str` during JSON serialization. Test: try posting a 50-char one-liner via the same tool in the same session — if it succeeds, this hypothesis is correct.

2. **`thread_ts` with period in it.** The `1783969409.999669` format has a literal period, which some JSON schema validators misinterpret as a nested object path. Test: try posting without `thread_ts` (top-level only) — if it succeeds, this hypothesis is correct.

3. **`content_type` defaulting to `text/markdown` but emoji shortcodes present in `text`.** The MCP server's documented schema for `conversations_add_message` says `content_type: "text/markdown"` (enum), but the body contained emoji shortcodes like `:large_green_circle:` and `:red_circle:`. Test: explicitly pass `content_type: "text/plain"` — if it succeeds, this hypothesis is correct.

**Recommended investigation path** (next time the runtime is available for full diagnostic access):
```bash
# Step 1: identify the tool wrapper source
which hermes
pip3 show hermes-agent  # find the install location
TOOL_WRAPPER=$(pip3 show hermes-agent | grep -i location | awk '{print $2}')/hermes_agent/tools/slack.py
grep -n "text must be a string" "$TOOL_WRAPPER"

# Step 2: if it's there, trace the validator
grep -n "def validate\|def _validate\|jsonschema\|pydantic" "$TOOL_WRAPPER" | head -20
```

## Durable mitigation (the part future agents need)

When `mcp__slack__conversations_add_message` returns `text must be a string`, do this in ONE step (no retries of the failing tool):

```bash
# 1. Source SLACK_USER_TOKEN from launchd env wrapper
SLACK_USER_TOKEN="$(bash -c 'source ~/.hermes/scripts/launchd-env-wrapper.sh 2>/dev/null; echo "$SLACK_USER_TOKEN"')"

# 2. Write the JSON payload via heredoc to avoid shell escaping issues
cat > /tmp/slack-reply.json <<'EOF'
{
  "channel": "D0AFTLEJGJU",
  "thread_ts": "1783969409.999669",
  "mrkdwn": false,
  "text": "<your reply body here>"
}
EOF

# 3. Post via curl with the USER token (cross-workspace safe)
curl -fsS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @/tmp/slack-reply.json

# 4. Verify with conversations_replies (the new msg must have ThreadTs matching the parent)
mcp__slack__conversations_replies channel_id=D0AFTLEJGJU thread_ts=1783969409.999669 limit=3
```

**Identity disclosure** — the post lands under `$USER` (user), not the hermes bot. Add this prefix to the message body if the reader might be confused:

> *(posted via $USER identity because `mcp__slack__conversations_add_message` returned `text must be a string`; the analysis below is from the hermes agent)*

## What worked in this specific instance

The 12:00 PT EA sweep re-triage reply (2433 bytes, multi-section with `✅/⚠️/🔴` status icons + bold + italic + multi-line bullets) landed cleanly via the curl fallback at:

```
{"ok":true,"channel":"D0AFTLEJGJU","ts":"1783969555.163109","message":{"user":"U09GH5BR3QU","type":"message","ts":"1783969555.163109","bot_id":"B0BGY53L8N8","app_id":"A0AESRKA7L3",...}}
```

`bot_id: B0BGY53L8N8` is the Slack App's bot user, but `user: U09GH5BR3QU` is $USER — confirms the post landed under user identity (the XOX-P token cross-workspace fallback path). Verified thread placement with `conversations_replies(thread_ts=1783969409.999669)` — the new MsgID was the last entry with `ThreadTs == 1783969409.999669` (correctly threaded).

## Cross-reference

- Parent skill: `slack-thread-routing-investigation` — add this as a "Failure 7 — `mcp__slack__conversations_add_message` hard reject" entry in the Failure 1-7 list. (The patcher validator choked on the YAML frontmatter on first attempt — try patching a smaller, distinct anchor if retried.)
- Sibling references in this skill:
  - `references/2026-07-08-dice-audit-failure4-narration-leak.md` — symbol mangle (Failure 4)
  - `references/2026-06-14-wrong-thread-ts-context-instance-15.md` — wrong thread_ts (Failure 5)
  - `references/2026-06-13-stale-fix-callback-instance-11.md` — user signals "I thought we fixed this?"
- Related SOUL.md COMMIT: `slack-cross-workspace-fallback-xoxp` (2026-06-25) — establishes the XOX-P user token fallback as the durable operationalization for cross-workspace bot-token blocks. This new failure mode is a separate trigger (MCP runtime wrapper bug, not a token scope issue) but uses the same fallback path.
