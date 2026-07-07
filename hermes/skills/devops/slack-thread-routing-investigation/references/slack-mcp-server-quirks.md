# slack-mcp-server quirks (127.0.0.1:8006)

Concrete behaviors observed against the running server, validated by
`tests/test_integration_live_probe.py` and `tests/test_slack_mcp_post.py`.
This is the session-specific knowledge bank; the `SKILL.md` body and the
helper script `scripts/slack_mcp_post.py` are the canonical implementation.

If you only remember one thing: **probe the server before assuming what
it can do.** The runtime's tool manifest is not authoritative. The server is.

## Server handshake (verified 2026-06-09)

```
POST http://127.0.0.1:8006/mcp
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc":"2.0","id":1,"method":"initialize",
 "params":{"protocolVersion":"2024-11-05","capabilities":{},
           "clientInfo":{"name":"probe","version":"1"}}}
```

Returns:
- Response body: `{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"logging":{},"resources":{},"tools":{"listChanged":true}},"serverInfo":{"name":"Slack MCP Server","version":"0.0.0"}}}`
- Response header: `Mcp-Session-Id: mcp-session-<uuid>` — **case-insensitive header lookup needed** (urllib normalizes to `Mcp-session-id`; real HTTP headers are case-insensitive; mocks often store them in plain dicts).

## Registered tools (13, verified 2026-06-09)

| Tool | Purpose |
|---|---|
| `channels_list` | List public + private channels |
| `conversations_add_message` | **Send a message** (the one the runtime often hides) |
| `conversations_history` | Channel timeline |
| `conversations_mark` | Mark channel/DM as read |
| `conversations_replies` | Thread contents (the routing diagnostic) |
| `conversations_search_messages` | Workspace search |
| `conversations_unreads` | Unread summary |
| `usergroups_create` | Mention groups |
| `usergroups_list` | List mention groups |
| `usergroups_me` | Self membership in mention groups |
| `usergroups_update` | Update group metadata |
| `usergroups_users_update` | Replace group members |
| `users_search` | Look up users |

The 5 that the user-facing skills depend on for routing: `conversations_replies`, `conversations_history`, `conversations_add_message`, `channels_list`, `users_search`.

## `conversations_add_message` schema (verified 2026-06-09)

```json
{
  "channel_id": "Cxxxxxxxxxx or #name or @user_dm",
  "text": "Message text",
  "thread_ts": "1234567890.123456 — optional; inherits parent thread",
  "content_type": "text/markdown"  // ONLY value the server accepts
}
```

**CORRECTION 2026-06-10 (verified live):** the server actually accepts BOTH
`text/markdown` AND `text/plain` in practice, even though the schema's
`enum` field lists only `text/markdown`. The live `conversations_add_message`
call with `content_type: "text/plain"` returned a CSV header (post accepted)
and the post landed in the right thread. **Use `content_type: "text/plain"`
for any reply that contains emoji shortcodes, mixed formatting, or anything
that fragments in Block Kit** — the 2026-06-09 "formatting broken" complaint
(Block Kit rendering `:large_green_circle:` as char-by-char, bullets split
into multiple text segments) was caused by `text/markdown` going through
Block Kit `rich_text` parsing. `text/plain` bypasses that.

**Why the schema claim was wrong:** the 2026-06-09 /learn finding looked at
the schema's `enum` field but didn't account for the runtime accepting
additional values. When the live call sends a different value, the server
does NOT reject it — it just falls through to a plain rendering. The real
rule: **the server accepts `text/plain` even though the documented schema
says otherwise; prefer `text/plain` for user-facing posts that contain emoji
or formatting that fragments in Block Kit.**

**When to still use the `chat.postMessage` fallback with `mrkdwn=False`:**
when you specifically want a Slack API response with a real message `ts`
and not just the MCP CSV header. The MCP path returns a CSV header — to get
the actual posted `ts`, query `conversations_replies` afterward.

## Quirk: `notifications/initialized` returns empty body

After `initialize` returns a session id, you MUST send:

```
POST /mcp
Mcp-Session-Id: <session>
{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}
```

The server replies with `202 Accepted` and **no JSON-RPC body**. If you call
`json.loads(payload)` on the empty body, you get `JSONDecodeError`. Pass
`expect_response=False` (the helper does this) or check for empty payload
before parsing.

## Quirk: urllib header normalization

```python
import urllib.request
req = urllib.request.Request("http://x/", headers={"Mcp-Session-Id": "abc"})
list(req.header_items())
# [('Mcp-session-id', 'abc')]  # only the M is capitalized
```

Implications:
- Outgoing: `dict(req.headers)` shows `Mcp-session-id` (lowercase rest).
- Incoming real response: `resp.headers` is an `email.message.Message`; case-insensitive lookup via `resp.headers.get("Mcp-Session-Id")` works.
- Incoming test mock: if you build a plain dict `{"Mcp-Session-Id": "abc"}` and pass it to `FakeHTTPResponse`, the script's `resp.headers.get("Mcp-Session-Id")` will work only if your fake also case-normalizes — or do a lowercase scan.

## Quirk: streamable-HTTP framing

Some server responses are framed as `event: message\ndata: {<json>}\n\n`.
The helper script's `_http_json_rpc` strips the framing and parses the last
`data:` line. If you see JSON parse errors and the body starts with `event:`,
that's why.

## Live probe recipe (the 5-second check)

```bash
SID=$(curl -sS -D - -X POST http://127.0.0.1:8006/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",
       "params":{"protocolVersion":"2024-11-05","capabilities":{},
                 "clientInfo":{"name":"probe","version":"1"}}}' \
  | grep -i "^mcp-session-id" | awk '{print $2}' | tr -d '\r\n')
echo "Session: $SID"

curl -sS -X POST http://127.0.0.1:8006/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python3 -c "import sys,json; print('\n'.join(t['name'] for t in json.loads(sys.stdin.read())['result']['tools']))"
```

The helper script does this in one shot: `python3 scripts/slack_mcp_post.py --probe-tools`.

## Fallback ladder (priority order)

1. `mcp__slack__conversations_add_message` — runtime surfaces it, use it.
2. HTTP-direct via `scripts/slack_mcp_post.py --fallback auto` (default) — initialize session, call tool via JSON-RPC. **Same text/markdown limitation as (1).**
3. `chat.postMessage` via `--fallback slack-api` with `mrkdwn=False` — only path that renders plain text without Block Kit fragmentation. Requires `HERMES_SLACK_BOT_TOKEN` in env.

The skill's `slack_mcp_post.py` wraps all three. Default `--fallback auto`
tries MCP first, falls back to chat.postMessage on error.

## `invalid_blocks` failure on multi-section emoji briefings (2026-06-10 8 AM)

**Symptom (verified 8 AM Wed Jun 10 in `executive-assistant` cron):** Posting
a 4634-char executive briefing to `D0AFTLEJGJU` via the default
`slack_mcp_post.py` MCP-direct path returned:

```json
{"path": "mcp", "result": {"isError": true, "content": [{"type": "text", "text": "invalid_blocks"}]}}
```

The text contained: `*Executive Briefing*` (bold markers), `🟢/🟡/🔴` (emoji shortcodes), Slack mrkdwn, `:rotating_light:`, etc. The MCP server's Block Kit rendering rejected the multi-section composition.

**Workaround that worked (8 AM Wed Jun 10):**

```bash
HERMES_SLACK_BOT_TOKEN="$(bash -lc 'source ~/.bashrc; source ~/.profile; echo $HERMES_SLACK_BOT_TOKEN')" \
python3 scripts/slack_mcp_post.py --channel D0AFTLEJGJU \
  --text "$(cat /tmp/briefing.txt)" --fallback slack-api
```

Returns `ok: true` with a real Slack `ts`. **But** the 4634-char text gets
split into 2 top-level messages in the DM (verified `ts=1781104149.481149`
= 4075 chars + `ts=1781104149.503059` = 846 chars, both `user=U0AEZC7RX1Q`).

**Pattern:** when a briefing exceeds ~4000 chars, the `chat.postMessage`
fallback path returns ONE ack but Slack renders TWO messages. The split
point is roughly at the 4000-char mark, which is the historic Slack text
size threshold for some auth/scope configurations.

**Implication for briefings:**
- Briefings >4000 chars will land as 2 consecutive top-level messages in the DM. Both have the correct bot user_id and the same content. The user reads them in order from oldest to newest.
- This is NOT a failure — verify with `conversations.history(limit=2)` and check that BOTH messages have `user=U0AEZC7RX1Q` and the content covers the full briefing.
- If the second message's text is missing or shows different content, treat as a post failure and retry with a smaller message.

**Diagnostic command to detect split-vs-actual-failure:**

```python
import subprocess, json
token = "<slack-token>"
r = subprocess.run(["curl","-s","-H",f"Authorization: Bearer {token}",
                    "https://slack.com/api/conversations.history?channel=D0AFTLEJGJU&limit=2"],
                   capture_output=True, text=True, timeout=15)
msgs = json.loads(r.stdout)["messages"]
total_chars = sum(len(m.get("text","")) for m in msgs)
both_bot = all(m.get("user") == "U0AEZC7RX1Q" for m in msgs)
print(f"split_msgs={len(msgs)} total_chars={total_chars} all_bot={both_bot}")
# split_msgs=1 total_chars=4634 → single message posted (good)
# split_msgs=2 total_chars=4634 all_bot=True → split, OK
# split_msgs=2 total_chars=500  → second message is a different post, alert
```

**Updated briefing length cap implication:** the executive-assistant skill's
"5 action prompts max" cap (added 2026-06-08) keeps briefings under 4000 chars
in most cases. If a briefing is going to exceed 4000 chars, expect a 2-message
split. Do not try to "fix" the split by editing the text — accept the split
as expected behavior.

## What the unit tests assert (so you know what drift to look for)

- `test_envelope_includes_session_header_on_subsequent_calls` — every call after `initialize` must carry the session id header
- `test_tools_call_uses_initialize_session` — `tools/call` must use the same session
- `test_default_content_type_is_text_markdown` — `DEFAULT_CONTENT_TYPE` is `text/markdown` (the only enum value the server accepts)
- `test_add_message_schema_accepts_markdown` — live integration: the server's `content_type` enum is `["text/markdown"]` (or just a default of `text/markdown` with no enum)
- `test_add_message_schema_accepts_content_type` — `content_type` key is in the input schema at all
- `TestThreadTsInheritanceRule.*` — outgoing `thread_ts` MUST equal incoming's `thread_ts` (or incoming's own `ts` if it's a top-level message); never the outgoing post's own ts (that's the self-rooted bug)

Run them: `cd ~/.hermes_prod/skills/devops/slack-thread-routing-investigation && python3 -m unittest discover -s tests -p "test_*.py" -v`
