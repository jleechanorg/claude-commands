# 2026-06-10 — /repro vNU3 PCD-schema-spread, 5th confirmed `send_message` mis-route

## Channel + thread

- Channel: `C0AH3RY3DK6` (worldai dev)
- Original incoming message ts: `1781159702.086799`
- Original incoming `thread_ts`: `1781159702.086799` (top-level — i.e. the user posted a new thread, not a reply)

## What happened

Reached for `target=slack:C0AH3RY3DK6:1781159702.086799` first (the 3-part form that matches the cron `deliver` syntax). Tool result:

```json
{"success": true, "platform": "slack", "chat_id": "C0AJQ5M0A0Y", "message_id": "1781160760.999869", "note": "Sent to slack home channel (chat_id: C0AJQ5M0A0Y)", "mirrored": true}
```

That's **Failure 1** (gateway self-roots / strips `:thread_ts` and falls back to the bot's home channel). Confirmed 5th time across 2 user channels + the home fallback.

## What I tried next (avoid this in future)

1. Re-issued with the same 3-part form: same home-channel fallback. ❌
2. Re-issued with `target=slack:C0AH3RY3DK6:1781159702.086799`: **same home-channel fallback** (it took 2 attempts before I switched strategy). ❌
3. Re-issued with `target=slack:C0AH3RY3DK6` (2-part, no `:thread_ts`): **landed in-thread correctly** at `1781160794.071969` (verified via `conversations_replies`, `ThreadTs=1781159702.086799`). ✓

But — and this is the second lesson — by the time I got to the 2-part form, **3-4 meta-reasoning messages had leaked into the thread** ("send_message is defaulting to home channel", "let me try without the colon format", etc.). The user can see those interleaved with the real answer. The 2-part form worked, but with collateral noise.

## The right recovery (when you see the home-channel fallback on the FIRST send_message call)

```bash
# 1) STOP calling send_message. Each additional call leaks another message into the thread.
# 2) Switch directly to Path A or B curl.
# 3) Post ONCE.
# 4) Verify with conversations_replies.

SID=$(curl -sS -i -X POST http://127.0.0.1:8006/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}' \
  | grep -i "^mcp-session-id:" | awk '{print $2}' | tr -d '\r')

curl -sS -X POST http://127.0.0.1:8006/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  -o /dev/null

python3 -c "
import json
print(json.dumps({
  'jsonrpc':'2.0','id':3,
  'method':'tools/call',
  'params':{
    'name':'conversations_add_message',
    'arguments':{
      'channel_id':'C0AH3RY3DK6',
      'thread_ts':'1781159702.086799',
      'content_type':'text/plain',
      'text': '...'
    }
  }
}))" > /tmp/post.json

curl -sS -X POST http://127.0.0.1:8006/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SID" \
  --data-binary @/tmp/post.json

# Verify
mcp__slack__conversations_replies channel_id=C0AH3RY3DK6 thread_ts=1781159702.086799 limit=3
```

## Why the 2-part form happened to work

The 2-part `target=slack:CHAN` form (no `:thread_ts`) auto-threads to the **incoming message's thread** (the gateway's auto-threading logic kicks in when no explicit thread_ts is given). This is the one workaround that doesn't require switching to curl. But it's not a documented feature — it just happens to work in the current gateway. The canonical recovery is still Path A or B curl.

## Lessons layered onto the SKILL.md

1. **3-part form (`target=slack:CHAN:thread_ts`) reliably mis-routes to the bot's home channel** — confirmed 5 times across 3 distinct user channels. Do not use.
2. **2-part form (`target=slack:CHAN`) auto-threads to incoming message's thread** — works, but not documented; rely on curl for anything load-bearing.
3. **Do not retry send_message with different `target` formats to "fix" a mis-route.** Each retry adds another message to the thread (either home or in-thread meta-noise). Switch to curl on the second attempt, not the third.
4. **The 1-post + 1-verify minimum-recovery applies when the mis-route is caught on the FIRST send_message call** (no preceding scratch-leak from MCP probing). If you've already issued 2-3 mis-routed `send_message` calls, you need the full 3-step recovery (post + delete duplicates).

## Cross-references

- 4th instance: `references/2026-06-10-wa-2289-godmode-l6-instance-4.md`
- 3rd instance: `references/2026-06-10-dropped-thread-followup.md`
- 2nd instance: `references/2026-06-09-worked-example.md`
- SOUL rule: `COMMIT: slack-reply-inherit-thread-ts`
