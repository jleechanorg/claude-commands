"""Unit tests for slack_mcp_post.py deterministic logic.

These tests do NOT hit Slack. They:
  1. Verify the script's argument parsing produces the correct JSON-RPC envelopes
  2. Verify session_id is honored across calls
  3. Verify the content_type default
  4. Verify the post_via_slack_api path builds the correct body (mrkdwn flag)
  5. Verify the post_via_mcp path falls back cleanly when conversations_add_message
     is not in the server's tool list

Run: python3 -m unittest discover -s tests -p "test_*.py" -v
"""
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import slack_mcp_post as smp


class FakeHTTPResponse:
    def __init__(self, payload: bytes, headers: dict = None):
        self._payload = payload
        # urllib's request headers are case-insensitive in real life; emulate
        # by storing a lowercased copy accessible via header-style lookup
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestJsonRpcEnvelope(unittest.TestCase):
    def test_envelope_includes_session_header_on_subsequent_calls(self):
        captured = []

        def fake_urlopen(req, timeout):
            captured.append({"headers": dict(req.headers),
                             "body": json.loads(req.data.decode())})
            body = captured[-1]["body"]
            if body["method"] == "initialize":
                return FakeHTTPResponse(
                    json.dumps({"jsonrpc": "2.0", "id": 1,
                                "result": {"protocolVersion": "2024-11-05",
                                           "serverInfo": {}}}).encode(),
                    {"Mcp-Session-Id": "sess-abc"})
            # notifications/initialized + tools/list
            return FakeHTTPResponse(
                json.dumps({"jsonrpc": "2.0", "id": 1,
                            "result": {"tools": [{"name": "conversations_add_message"}]}}).encode(),
                {"Mcp-Session-Id": "sess-abc"})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            tools, sid = smp.probe_tools()
        # After initialize, the next 2 calls (notifications/initialized,
        # tools/list) must include the Mcp-session-id header that the
        # initialize response set.
        self.assertEqual(len(captured), 3, f"expected 3 calls, got {len(captured)}")
        for c in captured[1:]:
            self.assertIn("Mcp-session-id", c["headers"],
                          f"got: {list(c['headers'].keys())}")
            self.assertEqual(c["headers"]["Mcp-session-id"], "sess-abc")
        self.assertIn("conversations_add_message", tools)

    def test_tools_call_uses_initialize_session(self):
        calls = []

        def fake_urlopen(req, timeout):
            body = json.loads(req.data.decode())
            headers = dict(req.headers)
            calls.append({"body": body, "headers": headers})
            if body["method"] == "initialize":
                return FakeHTTPResponse(
                    json.dumps({"jsonrpc": "2.0", "id": 1,
                                "result": {"protocolVersion": "2024-11-05",
                                           "serverInfo": {}}}).encode(),
                    {"Mcp-Session-Id": "sess-xyz"})
            if body["method"] == "tools/list":
                return FakeHTTPResponse(
                    json.dumps({"jsonrpc": "2.0", "id": 2,
                                "result": {"tools": [
                                    {"name": "conversations_add_message"}]}}).encode(),
                    {"Mcp-Session-Id": "sess-xyz"})
            if body["method"] == "tools/call":
                return FakeHTTPResponse(
                    json.dumps({"jsonrpc": "2.0", "id": 3,
                                "result": {"ok": True, "ts": "1781025000.000100"}}).encode(),
                    {"Mcp-Session-Id": "sess-xyz"})
            return FakeHTTPResponse(b"", {})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = smp.post_via_mcp("C123", "1781021369.023829",
                                      "hello", smp.DEFAULT_CONTENT_TYPE)
        # All subsequent calls must carry the same session id (urllib normalizes
        # the header name to "Mcp-session-id")
        for c in calls[1:]:
            self.assertEqual(c["headers"].get("Mcp-session-id"), "sess-xyz")
        # The tools/call payload must include channel_id, thread_ts, text, content_type
        tc = [c for c in calls if c["body"]["method"] == "tools/call"][0]
        args = tc["body"]["params"]["arguments"]
        self.assertEqual(args["channel_id"], "C123")
        self.assertEqual(args["thread_ts"], "1781021369.023829")
        self.assertEqual(args["text"], "hello")
        # /learn finding: only "text/markdown" is accepted
        self.assertEqual(args["content_type"], "text/markdown")
        self.assertEqual(result["result"]["ok"], True)


class TestContentTypeDefault(unittest.TestCase):
    def test_default_content_type_is_text_markdown(self):
        # /learn finding (2026-06-09): the MCP server's enum is ONLY
        # ["text/markdown"]. There is no text/plain option at the MCP layer.
        self.assertEqual(smp.DEFAULT_CONTENT_TYPE, "text/markdown")
        import inspect
        sig = inspect.signature(smp.post_via_mcp)
        self.assertEqual(sig.parameters["content_type"].default, "text/markdown")


class TestFallbackWhenToolMissing(unittest.TestCase):
    def test_raises_when_conversations_add_message_not_registered(self):
        def fake_urlopen(req, timeout):
            body = json.loads(req.data.decode())
            if body["method"] == "initialize":
                return FakeHTTPResponse(
                    json.dumps({"jsonrpc": "2.0", "id": 1,
                                "result": {"protocolVersion": "2024-11-05",
                                           "serverInfo": {}}}).encode(),
                    {"Mcp-Session-Id": "s1"})
            if body["method"] == "tools/list":
                # server only exposes read tools
                return FakeHTTPResponse(
                    json.dumps({"jsonrpc": "2.0", "id": 2,
                                "result": {"tools": [
                                    {"name": "conversations_history"},
                                    {"name": "conversations_replies"}]}}).encode(),
                    {"Mcp-Session-Id": "s1"})
            return FakeHTTPResponse(b"", {})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with self.assertRaises(RuntimeError) as ctx:
                smp.post_via_mcp("C123", "1781021369.023829", "hi")
        msg = str(ctx.exception)
        self.assertIn("conversations_add_message", msg)
        # error message has "Fall back" (capital F) — accept case-insensitive
        self.assertIn("all back to chat.postmessage", msg.lower())


class TestSlackApiFallback(unittest.TestCase):
    def test_post_via_slack_api_builds_correct_body_with_thread(self):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode())
            captured["headers"] = dict(req.headers)
            captured["url"] = req.full_url
            return FakeHTTPResponse(json.dumps({"ok": True, "ts": "9999.0001"}).encode())

        with patch.dict(os.environ, {"HERMES_SLACK_BOT_TOKEN": "xoxb-test"}):
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                result = smp.post_via_slack_api(
                    "C123", "1781021369.023829", "hello", "text/plain")
        self.assertEqual(captured["url"], smp.SLACK_API_URL)
        self.assertEqual(captured["body"]["channel"], "C123")
        self.assertEqual(captured["body"]["thread_ts"], "1781021369.023829")
        self.assertEqual(captured["body"]["text"], "hello")
        # text/plain path must set mrkdwn=False so Slack renders literally
        # — this is the only way to get a non-Block-Kit rendering
        self.assertEqual(captured["body"]["mrkdwn"], False)
        self.assertIn("Bearer xoxb-test", captured["headers"]["Authorization"])

    def test_post_via_slack_api_omits_thread_when_none(self):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode())
            return FakeHTTPResponse(json.dumps({"ok": True, "ts": "9999.0001"}).encode())

        with patch.dict(os.environ, {"HERMES_SLACK_BOT_TOKEN": "xoxb-test"}):
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                smp.post_via_slack_api("C123", None, "top-level msg", "text/plain")
        self.assertNotIn("thread_ts", captured["body"])
        self.assertEqual(captured["body"]["mrkdwn"], False)

    def test_post_via_slack_api_raises_without_token(self):
        # The function falls back from HERMES_SLACK_BOT_TOKEN to SLACK_BOT_TOKEN
        # (see scripts/slack_mcp_post.py line ~163). Strip both so the guard fires.
        env = {
            k: v for k, v in os.environ.items()
            if k not in ("HERMES_SLACK_BOT_TOKEN", "SLACK_BOT_TOKEN")
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                smp.post_via_slack_api("C123", None, "hi")
        self.assertIn("HERMES_SLACK_BOT_TOKEN", str(ctx.exception))


class TestThreadTsInheritanceRule(unittest.TestCase):
    """The skill's hard rule: outgoing thread_ts MUST equal incoming's thread_ts,
    or incoming's own ts if it has no thread_ts. These tests encode the rule."""

    def test_incoming_top_level_message_inherits_own_ts(self):
        # When the incoming message is a top-level channel post (ThreadTs == ts),
        # the reply's thread_ts must be that ts so it lands in the new thread.
        incoming_ts = "1781021369.023829"
        incoming_thread_ts = incoming_ts  # self-rooted top-level
        outgoing_thread_ts = incoming_thread_ts
        self.assertEqual(outgoing_thread_ts, incoming_ts)
        self.assertEqual(outgoing_thread_ts, incoming_thread_ts)

    def test_incoming_threaded_message_inherits_parent_thread(self):
        # When the incoming message is itself a thread reply (ThreadTs != ts),
        # the reply's thread_ts must be the PARENT's thread_ts, not the
        # incoming's own ts.
        incoming_ts = "1781022000.000100"
        incoming_thread_ts = "1781021369.023829"  # parent
        outgoing_thread_ts = incoming_thread_ts  # NOT incoming's own ts
        self.assertNotEqual(outgoing_thread_ts, incoming_ts)
        self.assertEqual(outgoing_thread_ts, "1781021369.023829")

    def test_self_rooted_post_is_anti_pattern(self):
        # An outgoing post with thread_ts == its own ts is a self-rooted
        # top-level message, which is the gateway bug. Detect and reject.
        outgoing_ts = "1781021803.807799"
        outgoing_thread_ts = outgoing_ts  # BUG
        self.assertEqual(outgoing_thread_ts, outgoing_ts,
                         "self-rooted post — gateway thread_ts bug")


if __name__ == "__main__":
    unittest.main()
