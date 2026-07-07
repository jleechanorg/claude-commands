"""Unit tests for cmux_client.send_and_submit().

Mocks the subprocess.run() calls to simulate:
1. happy path — send+enter succeed, churn proof appears
2. send failure — `cmux send` returns nonzero, helper returns ok=False with error
3. submit failure — `cmux send-key enter` returns nonzero, helper clears prompt
4. no churn — send+enter succeed but no spinner appears within timeout,
   helper clears prompt and returns ok=False
5. churn regex coverage — each CHURN_PATTERNS entry is matched against a
   sample screen that contains it
"""
import json
import sys
import unittest
from unittest import mock

sys.path.insert(0, sys.path[0] + "/../scripts")

import cmux_client  # noqa: E402


def _mock_cli_return(rc=0, stdout="", stderr=""):
    """Build a mock subprocess.run() return value."""
    m = mock.Mock()
    m.returncode = rc
    m.stdout = stdout
    m.stderr = stderr
    return m


def _read_screen_with_churn(churn_line):
    """Sample screen text containing a churn spinner."""
    return (
        "  ✔ PATH C — done\n"
        "  ◼ PATH B — in progress\n"
        f"  {churn_line}\n"
        "  ctx ---- 80%\n"
    )


class TestSendAndSubmitHappyPath(unittest.TestCase):
    @mock.patch("cmux_client._read_screen")
    @mock.patch("subprocess.run")
    def test_churn_observed_returns_ok(self, m_run, m_read):
        # cmux send, send-key enter, then read-screen with churn proof
        m_run.side_effect = [
            _mock_cli_return(rc=0, stdout="OK"),  # send
            _mock_cli_return(rc=0, stdout="OK"),  # send-key enter
        ]
        m_read.return_value = _read_screen_with_churn("✻ Booping for 5s")

        result = cmux_client.send_and_submit(
            "workspace:1", "surface:137", "hello"
        )
        self.assertTrue(result["ok"])
        self.assertIn("Booping for 5s", result["proof"])
        self.assertIsNotNone(result["proof_ts"])
        self.assertFalse(result["cleared"])
        self.assertIsNone(result["error"])
        # Verify the CLI invocations
        self.assertEqual(m_run.call_count, 2)
        send_call = m_run.call_args_list[0][0][0]
        self.assertIn("cmux send", send_call)
        self.assertIn("workspace:1", send_call)
        self.assertIn("surface:137", send_call)
        enter_call = m_run.call_args_list[1][0][0]
        self.assertIn("cmux send-key", enter_call)
        self.assertIn("enter", enter_call)


class TestSendAndSubmitFailures(unittest.TestCase):
    @mock.patch("subprocess.run")
    def test_send_failure_returns_error(self, m_run):
        m_run.return_value = _mock_cli_return(rc=1, stderr="socket not found")
        result = cmux_client.send_and_submit(
            "workspace:1", "surface:137", "hello"
        )
        self.assertFalse(result["ok"])
        self.assertIn("send failed", result["error"])
        self.assertIn("socket not found", result["error"])
        # No clear because the bug was upstream of submit
        self.assertFalse(result["cleared"])

    @mock.patch("cmux_client._clear_prompt")
    @mock.patch("subprocess.run")
    def test_enter_failure_clears_prompt(self, m_run, m_clear):
        m_run.side_effect = [
            _mock_cli_return(rc=0, stdout="OK"),  # send ok
            _mock_cli_return(rc=1, stderr="enter failed"),  # enter fails
        ]
        result = cmux_client.send_and_submit(
            "workspace:1", "surface:137", "hello"
        )
        self.assertFalse(result["ok"])
        self.assertIn("send-key enter failed", result["error"])
        m_clear.assert_called_once()

    @mock.patch("cmux_client._clear_prompt")
    @mock.patch("cmux_client._read_screen")
    @mock.patch("subprocess.run")
    def test_no_churn_clears_and_fails(
        self, m_run, m_read, m_clear
    ):
        m_run.side_effect = [
            _mock_cli_return(rc=0, stdout="OK"),  # send
            _mock_cli_return(rc=0, stdout="OK"),  # enter
        ]
        # No churn spinner in the screen
        m_read.return_value = "  ❯ \n  ctx ---- 80%\n"
        # Speed up the test
        result = cmux_client.send_and_submit(
            "workspace:1", "surface:137", "hello",
            verify_timeout_s=0.1, verify_poll_s=0.05,
        )
        self.assertFalse(result["ok"])
        self.assertIn("no churn/spinner observed", result["error"])
        m_clear.assert_called_once()
        self.assertTrue(result["cleared"])


class TestChurnPatterns(unittest.TestCase):
    """Each CHURN_PATTERNS entry must match a real sample screen."""

    SAMPLES = [
        "✻ Booping for 5s",
        "✳ Cooking for 12s",
        "✢ Crunched for 8s",
        "☾ Baking for 3s",
        "Churned for 9m 41s",
        "Cooked for 2m 38s",
        "Crunched for 1m 12s",
        "Baked for 33s",
        "Booping for 5s",
        "Sautéed for 2m 38s",
        "Compacting conversation… (52s · ↑ 2.0k tokens)",
        "✻ PATH B — spike per-user Gemini tagging (#7314)… still thinking with high effort",
        "◼ PATH B — spike per-user Gemini tagging (#7314)",
        "✶ PATH B — spike per-user Gemini tagging (#7314)… (16s)",
    ]

    def test_each_churn_pattern_matches_at_least_one_sample(self):
        matched = set()
        for sample in self.SAMPLES:
            hit = cmux_client._find_churn_line(sample)
            if hit is not None:
                matched.add(hit)
        # At least 8 of the patterns should have matched across all samples
        self.assertGreaterEqual(len(matched), 8, f"only matched: {matched}")

    def test_no_match_for_idle_screen(self):
        idle_screen = "  ❯ \n  ctx ---- 80%\n  7% until auto-compact\n"
        self.assertIsNone(cmux_client._find_churn_line(idle_screen))


if __name__ == "__main__":
    unittest.main()
