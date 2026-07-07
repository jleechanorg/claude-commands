#!/usr/bin/env python3
"""
Tests for the merged-PR short-circuit added 2026-07-03.

Bug: babysit.py poll() never recognized "PR is MERGED on GitHub" as a terminal
state. The babysit-wa-2403-PR7711 cron ran 251 polls over 11 days after the
PR merged, spamming Slack with "TERMINAL: merged" messages.

Fix: is_pr_terminal(task_summary) extracts PR refs and calls `gh pr view` to
check state. Returns (True, info) if any PR is MERGED/CLOSED, causing poll()
to post a single terminal message and exit.

These tests stub out subprocess calls so they don't require gh / network.
"""
import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import babysit  # noqa: E402


class TestExtractPRRefs(unittest.TestCase):
    def test_url_extraction(self):
        text = "PR https://github.com/$GITHUB_REPOSITORY/pull/7711 should be done"
        refs = babysit.extract_pr_refs(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["number"], 7711)
        self.assertEqual(refs[0]["owner"], "jleechanorg")
        self.assertEqual(refs[0]["repo"], "your-project.com")
        self.assertEqual(refs[0]["via"], "url")

    def test_bare_ref_extraction(self):
        text = "Worker is fixing PR #7711 - char creation banner bug"
        refs = babysit.extract_pr_refs(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["number"], 7711)
        self.assertIsNone(refs[0]["owner"])
        self.assertIsNone(refs[0]["repo"])

    def test_dedup(self):
        text = "PR https://github.com/$GITHUB_REPOSITORY/pull/7711 and PR #7711 same"
        refs = babysit.extract_pr_refs(text)
        self.assertEqual(len(refs), 1)

    def test_no_refs(self):
        self.assertEqual(babysit.extract_pr_refs("no prs here"), [])

    def test_multiple_urls(self):
        text = "PR https://github.com/owner/repo/pull/100 and https://github.com/other/repo/pull/200"
        refs = babysit.extract_pr_refs(text)
        self.assertEqual({r["number"] for r in refs}, {100, 200})


class TestCheckPRTerminalState(unittest.TestCase):
    @patch("babysit.subprocess.run")
    def test_returns_merged(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"state": "MERGED"})
        )
        state = babysit.check_pr_terminal_state({
            "owner": "jleechanorg", "repo": "your-project.com", "number": 7711
        })
        self.assertEqual(state, "MERGED")

    @patch("babysit.subprocess.run")
    def test_returns_closed(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"state": "CLOSED"})
        )
        state = babysit.check_pr_terminal_state({
            "owner": "x", "repo": "y", "number": 1
        })
        self.assertEqual(state, "CLOSED")

    @patch("babysit.subprocess.run")
    def test_returns_open(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"state": "OPEN"})
        )
        state = babysit.check_pr_terminal_state({
            "owner": "x", "repo": "y", "number": 1
        })
        self.assertEqual(state, "OPEN")

    @patch("babysit.subprocess.run")
    def test_handles_gh_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        state = babysit.check_pr_terminal_state({
            "owner": "x", "repo": "y", "number": 1
        })
        self.assertIsNone(state)

    def test_defaults_to_jleechanorg_repo(self):
        # No owner/repo → defaults to $GITHUB_REPOSITORY
        with patch("babysit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=json.dumps({"state": "OPEN"})
            )
            babysit.check_pr_terminal_state({"number": 1, "owner": None, "repo": None})
            call_args = mock_run.call_args[0][0]
            self.assertIn("$GITHUB_REPOSITORY", call_args)
            self.assertIn("1", call_args)


class TestIsPRTerminal(unittest.TestCase):
    @patch("babysit.check_pr_terminal_state")
    def test_returns_true_on_merged(self, mock_check):
        mock_check.return_value = "MERGED"
        is_terminal, info = babysit.is_pr_terminal(
            "PR https://github.com/$GITHUB_REPOSITORY/pull/7711"
        )
        self.assertTrue(is_terminal)
        self.assertEqual(info["state"], "MERGED")
        self.assertEqual(info["ref"]["number"], 7711)

    @patch("babysit.check_pr_terminal_state")
    def test_returns_true_on_closed(self, mock_check):
        mock_check.return_value = "CLOSED"
        is_terminal, info = babysit.is_pr_terminal(
            "PR https://github.com/owner/repo/pull/100"
        )
        self.assertTrue(is_terminal)
        self.assertEqual(info["state"], "CLOSED")

    @patch("babysit.check_pr_terminal_state")
    def test_returns_false_when_open(self, mock_check):
        mock_check.return_value = "OPEN"
        is_terminal, info = babysit.is_pr_terminal(
            "PR https://github.com/owner/repo/pull/100"
        )
        self.assertFalse(is_terminal)
        self.assertIsNone(info)

    def test_no_refs_returns_false(self):
        is_terminal, info = babysit.is_pr_terminal("nothing about prs here")
        self.assertFalse(is_terminal)
        self.assertIsNone(info)


class TestPollShortCircuit(unittest.TestCase):
    """End-to-end: poll() should exit early when PR is MERGED."""

    @patch("babysit.slack_post")
    @patch("babysit.find_tmux_session")
    @patch("babysit.is_pr_terminal")
    def test_poll_exits_on_merged_pr(self, mock_term, mock_tmux, mock_slack):
        mock_term.return_value = (
            True,
            {"ref": {"owner": "jleechanorg", "repo": "your-project.com",
                     "number": 7711, "via": "url"},
             "state": "MERGED"},
        )
        mock_tmux.return_value = "fake-tmux"  # would otherwise be probed

        result = babysit.poll(
            session_id="wa-2403",
            slack_channel="C0AH3RY3DK6",
            slack_thread_ts="1781868745.233079",
            task_summary="babysit PR https://github.com/$GITHUB_REPOSITORY/pull/7711",
        )

        self.assertEqual(result["status"], "terminal_pr")
        # tmux was NOT probed (short-circuit happened first)
        mock_tmux.assert_not_called()
        # A single slack message was posted
        mock_slack.assert_called_once()
        # And the message contains the PR number + MERGED
        msg_text = mock_slack.call_args[0][1]
        self.assertIn("7711", msg_text)
        self.assertIn("MERGED", msg_text)

    @patch("babysit.slack_post")
    @patch("babysit.find_tmux_session")
    @patch("babysit.is_pr_terminal")
    def test_poll_proceeds_normally_when_pr_open(self, mock_term, mock_tmux, mock_slack):
        mock_term.return_value = (False, None)
        mock_tmux.return_value = None  # dead worker
        # When tmux is None, poll() posts a "[alarm] died" message
        # The key assertion: is_pr_terminal was called and returned False
        babysit.poll(
            session_id="wa-2403",
            slack_channel="C0AH3RY3DK6",
            slack_thread_ts="x",
            task_summary="PR https://github.com/$GITHUB_REPOSITORY/pull/7711",
        )
        mock_term.assert_called_once()


class TestBabysitLoopExits(unittest.TestCase):
    @patch("babysit.poll")
    def test_loop_exits_on_terminal_pr(self, mock_poll):
        # Return terminal_pr on first call — loop should exit without further polls
        mock_poll.return_value = {
            "status": "terminal_pr", "state": {}, "terminal_pr": {"state": "MERGED"}
        }
        babysit.babysit_loop(
            session_id="wa-x", slack_channel="C", slack_thread_ts="t",
            task_summary="PR https://github.com/o/r/pull/1",
        )
        # Only ONE poll call — the loop must break on terminal_pr, not loop
        self.assertEqual(mock_poll.call_count, 1)

    @patch("babysit.poll")
    def test_loop_exits_on_done(self, mock_poll):
        mock_poll.return_value = {"status": "done", "state": {}}
        babysit.babysit_loop(
            session_id="wa-x", slack_channel="C", slack_thread_ts="t",
            task_summary="no prs here",
        )
        self.assertEqual(mock_poll.call_count, 1)

    @patch("babysit.poll")
    def test_loop_exits_on_dead(self, mock_poll):
        mock_poll.return_value = {"status": "dead", "state": {}}
        babysit.babysit_loop(
            session_id="wa-x", slack_channel="C", slack_thread_ts="t",
            task_summary="no prs here",
        )
        self.assertEqual(mock_poll.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)