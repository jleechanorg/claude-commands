# Fail-loud pattern: "ok: True but no echoed field" is a silent-success bug

When you call an external API that returns `ok: True` for a request that included a "please set field X" argument, you cannot trust success unless the response **echoes the field back** on the resulting resource. This is a class of bug that:

1. **Silently mis-routes** — the user (or calling agent) sees `success: True` and proceeds as if the post landed correctly.
2. **Surfaces only via side-effect audit** — comparing the response payload to the request argument, or running an independent `conversations_replies` to confirm where the post actually landed.
3. **Recurs under load** — the API may strip the field under rate-limit pressure, partial-write conditions, or auth-scope mismatches that the `ok` field does not surface.

The general fix is **fail-loud on absent-echo**: in the client, after the API returns `ok: True`, check that the field you asked to be set is actually present in the response, and return an error result if it isn't. The error result must name both the request (so the agent can retry) and the actual outcome (so the agent can recover).

## Slack-specific shape (2026-06-14, AO #684 misroute)

The `chat.postMessage` API takes an optional `thread_ts` argument. The response on success is:

```json
{
  "ok": true,
  "ts": "1781462111.465060",
  "message": {
    "ts": "1781462111.465060",
    "thread_ts": "1781465902.728229",   // ← present IFF the post threaded
    "text": "echo of reply"
  }
}
```

When the caller asked for `thread_ts` but the post actually landed at the channel root, Slack returns `ok: true` with `message.thread_ts` **absent** (or the response may include the top-level `thread_ts` field set to the same value as the post's own `ts`, depending on the API version and the path that stripped it). The 10+ AO #684 misroutes (2026-06-09 → 2026-06-14) all had this shape: `ok: true`, no `message.thread_ts` echo, the post landed at channel root.

**The fail-loud recipe in `tools/send_message_tool.py` (`_send_slack` in `jleechanorg/hermes-agent`):**

```python
async def _send_slack(token, chat_id, message, thread_id=None):
    # ... build payload, send request ...
    if data.get("ok"):
        posted_message = data.get("message") or {}
        actual_thread_ts = (
            posted_message.get("thread_ts") or data.get("thread_ts")
        )
        if thread_id and not actual_thread_ts:
            return _error(
                "Slack honored chat.postMessage with `ok: True` but "
                f"the posted message has no `thread_ts` (target attempted: "
                f"slack:{chat_id}:{thread_id}; actual channel: {chat_id}). "
                "This is the AO #684 misroute shape — do not treat the "
                "post as successful. Fall back to Path A/B "
                "(slack_mcp_post.sh or direct chat.postMessage with thread_ts)."
            )
        return {"success": True, "platform": "slack", "chat_id": chat_id, "message_id": data.get("ts")}
```

**Two non-obvious things about the recipe:**

1. **The error message names BOTH the request and the outcome.** It includes `slack:{chat_id}:{thread_id}` (the 3-part target attempted) and `{chat_id}` (the channel landed in, which is the same here but in the general case could differ if the API rewrote `chat_id`). An agent receiving this error can decide to retry via a different transport (Path A curl) without re-deriving the request shape.

2. **`data.get("message") or {}` handles the response shape variation.** Some `chat.postMessage` responses put the echoed post under the top-level `message` key; older responses put it at the top level. Checking `posted_message.get("thread_ts") or data.get("thread_ts")` covers both. (A more careful implementation would also detect `data.get("thread_ts") == data.get("ts")` as the self-rooted shape, but the absent-echo check is sufficient for the common case.)

## Where the pattern applies (non-Slack examples)

The "request X, verify response echoes X" pattern is general. Other APIs where the same shape has bitten users:

- **GitHub Issues API**: PATCH `/repos/:owner/:repo/issues/:n` with `labels: [...]` may return `200 OK` with the labels unchanged if the token lacks `issues:write` scope. Detect: response's `labels` field should contain the new labels.
- **Google Calendar API**: `events.insert` with `conferenceData` may return a 200 with `conferenceData` absent if the calendar is not a Google Workspace calendar. Detect: response's `conferenceData.entryPoints` should be non-empty.
- **Stripe webhooks**: a `charge.succeeded` event may be delivered but the metadata field absent if the original charge was created without it. Detect: webhook payload's `data.object.metadata` should contain the expected key.

For each, the fail-loud recipe is identical: after the API returns success, check the response for the field you asked to be set, and return an error result if it isn't. The error result must name both the request and the outcome so the caller can retry via a different path.

## When NOT to use this pattern

- **The API explicitly documents the success shape** and the field is part of the documented response. If the API contract says "200 OK means the field is set", don't double-check — it adds cost and the response-time shape is the spec. Use the recipe only when the field is **optional** and the API may legitimately return success with the field absent.
- **The check is more expensive than the side-effect**. Don't add a 50ms `GET` after every `POST` to verify the field. Use the recipe only when the response already carries the echoed field (so the check is free).
- **The caller doesn't need the field to be set**. If the agent is OK with a partial success (e.g. "best effort" label), the check is overhead. The recipe is for hard requirements, not soft preferences.

## Test shape

The test that catches this class of bug is **"ok-True, no-echo" → error result**, paired with **"ok-True, with-echo" → success result**. Mock the API to return both shapes and assert the client code makes the right call:

```python
def test_fail_loud_when_slack_omits_thread_ts_in_response(self):
    """The misroute shape: ok=True, no message.thread_ts → error result."""
    ok_payload = {
        "ok": True,
        "ts": "1781462111.465060",
        "message": {"ts": "1781462111.465060", "text": "echo"},
        # NO message.thread_ts — this is the misroute.
    }
    # ... mock aiohttp, call _send_slack with thread_id="..." ...
    # Assert: result has "error", not "success"
    # Assert: error message names the 3-part target attempted
    # Assert: error message names the channel landed in

def test_no_fail_loud_when_slack_echoes_thread_ts(self):
    """Correct path: ok=True with message.thread_ts echoing back → success."""
    ok_payload = {
        "ok": True,
        "ts": "1781462111.465060",
        "message": {
            "ts": "1781462111.465060",
            "thread_ts": "1781465902.728229",  # echoed
            "text": "echo",
        },
    }
    # ... assert result["success"] is True, no "error" key ...
```

Verified patterns in `jleechanorg/hermes-agent`:
- `tests/gateway/test_delivery.py::TestSlackThreePartTargetEndToEnd::test_3part_slack_target_fail_loud_when_slack_strips_thread_ts` — the integration test (DeliveryTarget → send_message_tool → chat.postMessage).
- `tests/tools/test_send_message_tool.py::TestSendSlackFailLoud::test_fail_loud_when_slack_omits_thread_ts_in_response` — the unit test on `_send_slack` directly.

Both tests pass on the patched code, both fail on the original code (RED→GREEN verified 2026-06-14).

## PR cross-reference

The fix landed in `jleechanorg/hermes-agent` as part of the AO #684 5th-misroute-class work. The PR title and branch should match `fix/send-message-thread-ts` (or equivalent). The fail-loud invariant is now load-bearing for any future "post to Slack via the LLM-callable tool" path — do not regress it.
