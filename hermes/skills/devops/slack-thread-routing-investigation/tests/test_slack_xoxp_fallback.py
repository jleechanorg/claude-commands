"""Unit tests for slack_mcp_post.py post_via_xoxp path (Failure 5f).

These tests do NOT hit Slack. They verify:
  1. post_via_xoxp raises RuntimeError when SLACK_USER_TOKEN is unset
  2. post_via_xoxp raises RuntimeError when neither env var nor ~/.profile has the token
  3. post_via_xoxp builds the correct chat.postMessage body (channel + thread_ts + text)
  4. post_via_xoxp prepends the identity-disclosure note by default
  5. post_via_xoxp skips identity-disclosure when identity_disclosure=False
  6. post_via_xoxp parses a successful Slack response
  7. post_via_xoxp with content_type=text/plain sets mrkdwn=False
  8. post_via_xoxp reads SLACK_USER_TOKEN from ~/.bashrc when env + ~/.profile both empty
     (covers the launchd-env-wrapper _extract_bashrc_var pattern)
  9. post_via_xoxp strips surrounding quotes from bashrc export
 10. _is_slack_ok helper: {"ok": False} → False, {"ok": True} → True, no "ok" + ts → True
 11. CLI --fallback auto: slack-api ok=false path auto-falls-through to xoxp successfully

Run: python3 -m unittest tests.test_slack_xoxp_fallback -v
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import slack_mcp_post as smp


class XoxpFallbackTests(unittest.TestCase):

    def setUp(self) -> None:
        # Save and clear SLACK_USER_TOKEN for clean test state
        self._saved_token = os.environ.pop("SLACK_USER_TOKEN", None)

    def tearDown(self) -> None:
        if self._saved_token is not None:
            os.environ["SLACK_USER_TOKEN"] = self._saved_token

    def _fake_response(self, payload: dict) -> MagicMock:
        resp = MagicMock()
        resp.read.return_value = json.dumps(payload).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = lambda s, *a: None
        return resp

    def test_raises_when_token_missing_and_profile_missing(self) -> None:
        """No SLACK_USER_TOKEN env + no ~/.profile + no ~/.bashrc → RuntimeError."""
        # Both source files must report as not-existing. Note: the new scan order
        # tries ~/.bashrc FIRST (per launchd-env-wrapper:_extract_bashrc_var), so
        # both must be missing for RuntimeError to fire.
        with patch("os.path.exists", return_value=False):
            with self.assertRaises(RuntimeError) as cm:
                smp.post_via_xoxp("C0AH3RY3DK6", "1782265612.317549", "test reply")
            self.assertIn("SLACK_USER_TOKEN", str(cm.exception))
            self.assertIn("xoxp", str(cm.exception))

    def test_builds_correct_body_with_token_from_env(self) -> None:
        """SLACK_USER_TOKEN set → body has channel + thread_ts + identity-disclosed text."""
        os.environ["SLACK_USER_TOKEN"] = "xoxp-test-token-1234"
        captured = {}
        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.headers)
            captured["body"] = json.loads(req.data.decode())
            return self._fake_response({"ok": True, "ts": "1782400000.000100"})
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = smp.post_via_xoxp(
                "C0AH3RY3DK6", "1782265612.317549", "test reply body"
            )
        self.assertEqual(captured["url"], "https://slack.com/api/chat.postMessage")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer xoxp-test-token-1234")
        self.assertEqual(captured["body"]["channel"], "C0AH3RY3DK6")
        self.assertEqual(captured["body"]["thread_ts"], "1782265612.317549")
        self.assertIn("cross-workspace bot-token hard-block", captured["body"]["text"])
        self.assertIn("test reply body", captured["body"]["text"])
        self.assertEqual(result["ok"], True)

    def test_identity_disclosure_off(self) -> None:
        """identity_disclosure=False → no (posted via ...) prefix in text."""
        os.environ["SLACK_USER_TOKEN"] = "xoxp-test-token-1234"
        captured = {}
        def fake_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode())
            return self._fake_response({"ok": True, "ts": "1782400000.000100"})
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            smp.post_via_xoxp(
                "C0AH3RY3DK6", "1782265612.317549", "test reply body",
                identity_disclosure=False,
            )
        self.assertNotIn("posted via", captured["body"]["text"])
        self.assertEqual(captured["body"]["text"], "test reply body")

    def test_top_level_post_omits_thread_ts(self) -> None:
        """thread_ts=None → no thread_ts in body (top-level channel post)."""
        os.environ["SLACK_USER_TOKEN"] = "xoxp-test-token-1234"
        captured = {}
        def fake_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode())
            return self._fake_response({"ok": True, "ts": "1782400000.000100"})
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            smp.post_via_xoxp("C0AH3RY3DK6", None, "top-level post")
        self.assertNotIn("thread_ts", captured["body"])

    def test_text_plain_sets_mrkdwn_false(self) -> None:
        """content_type=text/plain → mrkdwn=False in body."""
        os.environ["SLACK_USER_TOKEN"] = "xoxp-test-token-1234"
        captured = {}
        def fake_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode())
            return self._fake_response({"ok": True, "ts": "1782400000.000100"})
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            smp.post_via_xoxp(
                "C0AH3RY3DK6", "1782265612.317549", "plain text reply",
                content_type="text/plain",
            )
        self.assertEqual(captured["body"]["mrkdwn"], False)

    def test_falls_back_to_profile_when_env_unset(self) -> None:
        """SLACK_USER_TOKEN env unset but ~/.profile has it → uses profile token."""
        # Don't set env
        captured = {}
        profile_content = (
            "# some stuff\nexport SLACK_USER_TOKEN=\"xoxp-from-profile-9999\"\n"
        )
        def fake_urlopen(req, timeout):
            captured["headers"] = dict(req.headers)
            captured["body"] = json.loads(req.data.decode())
            return self._fake_response({"ok": True, "ts": "1782400000.000100"})
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data=profile_content)), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen):
            smp.post_via_xoxp("C0AH3RY3DK6", "1782265612.317549", "test")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer xoxp-from-profile-9999")

    def test_cli_accepts_xoxp_fallback_arg(self) -> None:
        """Verify --fallback xoxp is accepted by the production parser, not a
        freshly-constructed one. The point is to catch the case where the real
        choices list accidentally drops "xoxp" — a fresh parser with the same
        choices would pass even if the production parser was broken.
        """
        parser = smp._build_parser()
        args = parser.parse_args(["--fallback", "xoxp"])
        self.assertEqual(args.fallback, "xoxp")
        # Also assert the production choices list contains xoxp
        for action in parser._actions:
            if "--fallback" in action.option_strings:
                self.assertIn("xoxp", action.choices or [])
                break

    # ---- New tests: bashrc sourcing + auto-fallthrough (Codex Gate 5 threads) ----

    def test_falls_back_to_bashrc_when_env_and_profile_empty(self) -> None:
        """Env unset + ~/.profile empty + ~/.bashrc has export SLACK_USER_TOKEN=xoxp-...
        → uses the .bashrc value. Mirrors launchd-env-wrapper.sh _extract_bashrc_var.
        """
        bashrc_content = (
            "# auto-sourced guard\n"
            "if [ -z \"$PS1\" ]; then return; fi\n"
            "export PATH=/usr/local/bin:$PATH\n"
            "export SLACK_USER_TOKEN=\"xoxp-bashrc-7777\"\n"
        )
        captured = {}
        def fake_urlopen(req, timeout):
            captured["headers"] = dict(req.headers)
            return self._fake_response({"ok": True, "ts": "1782400000.000200"})
        # ~/.profile does NOT exist; ~/.bashrc does
        def fake_exists(p):
            return p.endswith(".bashrc")
        with patch("os.path.exists", side_effect=fake_exists), \
             patch("builtins.open", unittest.mock.mock_open(read_data=bashrc_content)), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen):
            smp.post_via_xoxp("C0AH3RY3DK6", "1782265612.317549", "test from bashrc")
        self.assertEqual(captured["headers"]["Authorization"],
                         "Bearer xoxp-bashrc-7777")

    def test_bashrc_single_quotes_stripped(self) -> None:
        """bashrc export SLACK_USER_TOKEN='xoxp-...' (single quotes) → token unquoted."""
        bashrc_content = "export SLACK_USER_TOKEN='xoxp-single-quote-8888'\n"
        captured = {}
        def fake_urlopen(req, timeout):
            captured["headers"] = dict(req.headers)
            return self._fake_response({"ok": True, "ts": "1782400000.000300"})
        def fake_exists(p):
            return p.endswith(".bashrc")
        with patch("os.path.exists", side_effect=fake_exists), \
             patch("builtins.open", unittest.mock.mock_open(read_data=bashrc_content)), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen):
            smp.post_via_xoxp("C0AH3RY3DK6", "1782265612.317549", "test")
        self.assertEqual(captured["headers"]["Authorization"],
                         "Bearer xoxp-single-quote-8888")

    def test_bashrc_wins_over_profile_when_both_present(self) -> None:
        """Both ~/.bashrc and ~/.profile have SLACK_USER_TOKEN → .bashrc wins
        (mirrors launchd-env-wrapper.sh:_extract_bashrc_var preferring the live
        shell value, preventing stale-profile shadow after token rotation).
        """
        bashrc_content = 'export SLACK_USER_TOKEN="xoxp-bashrc-NEW-1111"\n'
        profile_content = 'export SLACK_USER_TOKEN="xoxp-profile-OLD-2222"\n'
        captured = {}
        def fake_urlopen(req, timeout):
            captured["headers"] = dict(req.headers)
            return self._fake_response({"ok": True, "ts": "1782400000.000400"})
        def fake_exists(p):
            return True  # both files exist
        def fake_open(path, *args, **kwargs):
            if path.endswith(".bashrc"):
                return unittest.mock.mock_open(read_data=bashrc_content)()
            if path.endswith(".profile"):
                return unittest.mock.mock_open(read_data=profile_content)()
            raise FileNotFoundError(path)
        with patch("os.path.exists", side_effect=fake_exists), \
             patch("builtins.open", side_effect=fake_open), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen):
            smp.post_via_xoxp("C0AH3RY3DK6", "1782265612.317549", "test")
        self.assertEqual(captured["headers"]["Authorization"],
                         "Bearer xoxp-bashrc-NEW-1111",
                         "Must prefer ~/.bashrc over ~/.profile (live over stale)")

    def test_auto_fallback_does_not_fire_on_non_cross_workspace_error(self) -> None:
        """--fallback auto: bot token returns {"ok": false, "error": "invalid_auth"}
        → must NOT fall through to xoxp; must return exit 3 (caller detects error).
        Auto-fallback is reserved for cross-workspace bot-token hard-block signatures
        (not_in_channel, channel_not_found, restricted_action, team_access_not_granted,
        missing_scope). A token rotation gap or wrong-channel typo should surface.
        """
        BOT_TOKEN = "xoxb-bot-fake-bbbb"
        XOXP_TOKEN = "xoxp-should-not-be-used-3333"
        def fake_urlopen(req, timeout):
            auth = req.headers.get("Authorization", "")
            if auth == f"Bearer {BOT_TOKEN}":
                return self._fake_response({"ok": False, "error": "invalid_auth"})
            if auth == f"Bearer {XOXP_TOKEN}":
                # Should never be called in this test
                self.fail("XOX-P path should not fire on invalid_auth (non-cross-workspace error)")
            return self._fake_response({"jsonrpc": "2.0", "id": 1,
                                        "result": {"tools": [], "sessionId": "x"}})
        with patch.dict(os.environ, {"HERMES_SLACK_BOT_TOKEN": BOT_TOKEN,
                                      "SLACK_USER_TOKEN": XOXP_TOKEN}), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen), \
             patch.object(smp, "post_via_mcp",
                          side_effect=RuntimeError("mcp tool missing in test")):
            rc = smp.main([
                "--channel", "C0AH3RY3DK6",
                "--thread-ts", "1782265612.317549",
                "--text", "auto fallback should NOT fire",
                "--fallback", "auto",
            ])
        self.assertEqual(rc, 3,
                         "Non-cross-workspace errors must exit 3, not 0 via xoxp")

    def test_is_slack_ok_helper(self) -> None:
        """_is_slack_ok: ok=False → False, ok=True → True, no ok + ts → True."""
        self.assertFalse(smp._is_slack_ok({"ok": False, "error": "not_in_channel"}))
        self.assertFalse(smp._is_slack_ok({"ok": False, "error": "channel_not_found"}))
        self.assertTrue(smp._is_slack_ok({"ok": True, "ts": "1782.000100"}))
        self.assertTrue(smp._is_slack_ok({"ok": True, "ts": "1782.000200",
                                          "warning": "superfluous_charset"}))
        self.assertTrue(smp._is_slack_ok({"ts": "1782.000300"}))  # no ok field, has ts
        self.assertFalse(smp._is_slack_ok({}))  # empty dict
        self.assertFalse(smp._is_slack_ok("not a dict"))  # not a dict

    def test_auto_fallback_promotes_slack_api_ok_false_to_xoxp(self) -> None:
        """--fallback auto: bot token returns {"ok": False, "error": "not_in_channel"}
        → falls through to xoxp and posts successfully.
        """
        # Count by Authorization header to disambiguate from MCP probe calls (no auth)
        call_count = {"slack_api": 0, "xoxp": 0}
        captured = {"xoxp_headers": None, "xoxp_body": None}
        BOT_TOKEN = "xoxb-bot-fake-aaaa"
        XOXP_TOKEN = "xoxp-auto-fallback-5555"
        def fake_urlopen(req, timeout):
            auth = req.headers.get("Authorization", "")
            body = json.loads(req.data.decode()) if req.data else {}
            if auth == f"Bearer {BOT_TOKEN}":
                call_count["slack_api"] += 1
                return self._fake_response({"ok": False, "error": "not_in_channel"})
            if auth == f"Bearer {XOXP_TOKEN}":
                call_count["xoxp"] += 1
                captured["xoxp_headers"] = dict(req.headers)
                captured["xoxp_body"] = body
                return self._fake_response({"ok": True, "ts": "1782400000.000999"})
            # MCP probe (no auth) or notifications — return non-empty JSON-RPC ack
            return self._fake_response(
                {"jsonrpc": "2.0", "id": 1, "result": {"tools": [], "sessionId": "x"}}
            )
        # Also stub probe_tools so post_via_mcp returns a clean MCP result
        # (we want the mcp path to FAIL so we reach the slack-api branch)
        with patch.dict(os.environ, {"HERMES_SLACK_BOT_TOKEN": BOT_TOKEN,
                                      "SLACK_USER_TOKEN": XOXP_TOKEN}), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen), \
             patch.object(smp, "post_via_mcp",
                          side_effect=RuntimeError("mcp tool missing in test")):
            from io import StringIO
            captured_stdout = StringIO()
            with patch("sys.stdout", captured_stdout):
                rc = smp.main([
                    "--channel", "C0AH3RY3DK6",
                    "--thread-ts", "1782265612.317549",
                    "--text", "auto fallback test",
                    "--fallback", "auto",
                ])
        self.assertEqual(rc, 0, "auto fallback should exit 0 on xoxp success")
        self.assertEqual(call_count["slack_api"], 1, "should have tried slack-api first")
        self.assertEqual(call_count["xoxp"], 1, "should have fallen through to xoxp")
        self.assertEqual(captured["xoxp_headers"]["Authorization"],
                         f"Bearer {XOXP_TOKEN}")
        self.assertEqual(captured["xoxp_body"]["channel"], "C0AH3RY3DK6")
        self.assertEqual(captured["xoxp_body"]["thread_ts"], "1782265612.317549")
        # Output JSON should report the path as "xoxp"
        out = captured_stdout.getvalue()
        self.assertIn('"path": "xoxp"', out)


if __name__ == "__main__":
    unittest.main()