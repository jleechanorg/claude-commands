"""Integration test: live HTTP probe of the running slack-mcp-server.

This is a "does the server actually have the tool" check. Skips automatically
if the server isn't reachable on 127.0.0.1:8006.

Run: python3 -m unittest tests.test_integration_live_probe -v
"""
import json
import os
import sys
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import slack_mcp_post as smp


MCP_URL = os.environ.get("SLACK_MCP_URL", "http://127.0.0.1:8006/mcp")


def _server_reachable() -> bool:
    try:
        req = urllib.request.Request(MCP_URL, method="GET")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except (urllib.error.URLError, OSError, ConnectionError):
        return False


@unittest.skipUnless(_server_reachable(),
                     f"slack-mcp-server not reachable at {MCP_URL}")
class TestLiveServerHasSendTool(unittest.TestCase):
    """The /learn lesson from 2026-06-09: slack-mcp-server DOES register
    conversations_add_message. The runtime may not surface it, but the
    server has it. Prove this against the live server."""

    def test_probe_tools_returns_conversations_add_message(self):
        tools, sid = smp.probe_tools()
        self.assertTrue(sid, "server should return a session id")
        self.assertIn("conversations_add_message", tools,
                      f"server must register conversations_add_message; got: {tools}")
        # Also confirm the read tools we depend on for the routing ladder
        self.assertIn("conversations_replies", tools)
        self.assertIn("conversations_history", tools)


@unittest.skipUnless(_server_reachable(),
                     f"slack-mcp-server not reachable at {MCP_URL}")
class TestLiveServerSchema(unittest.TestCase):
    """The schema for conversations_add_message must accept content_type
    so we can pass content_type=text/plain and avoid Block Kit fragmentation."""

    def test_add_message_schema_accepts_markdown(self):
        """The 2026-06-09 /learn finding: the server's content_type enum is
        ONLY ['text/markdown']. There is no text/plain option. To post plain
        text without Block Kit fragmentation, you must fall back to
        chat.postMessage with mrkdwn=False (the slack-api path in this script)."""
        tools, _ = smp.probe_tools()
        # Re-fetch with full schema (probe_tools only returned names; refetch)
        init = smp._http_json_rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "t", "version": "1"}})
        sid = init.get("_session")
        smp._http_json_rpc("notifications/initialized", {}, session_id=sid,
                           expect_response=False)
        resp = smp._http_json_rpc("tools/list", {}, session_id=sid)
        add_msg = next(t for t in resp["result"]["tools"]
                       if t["name"] == "conversations_add_message")
        schema = add_msg["inputSchema"]
        props = schema["properties"]
        self.assertIn("channel_id", props)
        self.assertIn("text", props)
        self.assertIn("thread_ts", props)
        self.assertIn("content_type", props,
                      "schema must include content_type for the script to work")
        # /learn finding: server only accepts text/markdown. Document it
        # so the script + skill can route plain-text posts to the fallback.
        # The live server (slack-mcp-server 0.0.0) may return either an enum
        # or just a default. Accept both shapes.
        ct = props["content_type"]
        ct_enum = ct.get("enum")
        ct_default = ct.get("default")
        if ct_enum is not None:
            self.assertEqual(ct_enum, ["text/markdown"],
                             f"unexpected enum: {ct_enum} — update script if it changed")
        else:
            self.assertEqual(ct_default, "text/markdown",
                             f"unexpected default: {ct_default} — server may have changed")
        # Hard constraint: text/plain is never accepted
        accepted = ct_enum or [ct_default]
        self.assertNotIn("text/plain", accepted,
                         "server must not accept text/plain — if it does, "
                         "update post_via_mcp to use it and drop the chat.postMessage fallback")


if __name__ == "__main__":
    unittest.main()
