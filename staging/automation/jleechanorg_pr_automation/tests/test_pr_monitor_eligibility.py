import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from automation.jleechanorg_pr_automation import jleechanorg_pr_monitor as mon

FAILED_PR_NUMBER = 2
EXPECTED_ACTIONABLE_COUNT = 2


def codex_marker(monitor: mon.JleechanorgPRMonitor, token: str) -> str:
    return f"{monitor.CODEX_COMMIT_MARKER_PREFIX}{token}{monitor.CODEX_COMMIT_MARKER_SUFFIX}"


def test_list_actionable_prs_conflicts_and_failing(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    monitor = mon.JleechanorgPRMonitor(automation_username="test-automation-user")

    sample_prs = [
        {"repository": "repo/a", "number": 1, "title": "conflict", "mergeable": "CONFLICTING"},
        {"repository": "repo/b", "number": 2, "title": "failing", "mergeable": "MERGEABLE"},
        {"repository": "repo/c", "number": 3, "title": "passing", "mergeable": "MERGEABLE"},
    ]

    monkeypatch.setattr(monitor, "discover_open_prs", lambda: sample_prs)

    def fake_has_failing_checks(repo: str, pr_number: int) -> bool:  # noqa: ARG001
        return pr_number == FAILED_PR_NUMBER

    monkeypatch.setattr(mon, "has_failing_checks", fake_has_failing_checks)

    actionable = monitor.list_actionable_prs(max_prs=10)

    assert len(actionable) == EXPECTED_ACTIONABLE_COUNT
    assert {pr["number"] for pr in actionable} == {1, FAILED_PR_NUMBER}

    captured = capsys.readouterr().out
    assert "Eligible for fixpr: 2" in captured


class TestIsGithubBotComment(unittest.TestCase):
    """Validate _is_github_bot_comment method."""

    def setUp(self) -> None:
        self.monitor = mon.JleechanorgPRMonitor(automation_username="test-automation-user")

    def test_identifies_github_actions_bot(self) -> None:
        comment = {"author": {"login": "github-actions[bot]"}}
        assert self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_identifies_dependabot(self) -> None:
        comment = {"author": {"login": "dependabot[bot]"}}
        assert self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_identifies_renovate_bot(self) -> None:
        comment = {"author": {"login": "renovate[bot]"}}
        assert self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_identifies_coderabbitai_without_bot_suffix(self) -> None:
        comment = {"author": {"login": "coderabbitai"}}
        assert self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_identifies_copilot_swe_agent_without_bot_suffix(self) -> None:
        comment = {"author": {"login": "copilot-swe-agent"}}
        assert self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_identifies_github_actions_without_bot_suffix(self) -> None:
        comment = {"author": {"login": "github-actions"}}
        assert self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_excludes_codex_bot(self) -> None:
        comment = {"author": {"login": "codex[bot]"}}
        assert not self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_identifies_coderabbitai_bot_with_suffix(self) -> None:
        comment = {"author": {"login": "coderabbitai[bot]"}}
        assert self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_excludes_copilot_bot(self) -> None:
        comment = {"author": {"login": "copilot[bot]"}}
        assert not self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_excludes_cursor_bot(self) -> None:
        comment = {"author": {"login": "cursor[bot]"}}
        assert not self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_excludes_human_user(self) -> None:
        comment = {"author": {"login": "jleechan"}}
        assert not self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_handles_user_field_fallback(self) -> None:
        comment = {"user": {"login": "github-actions[bot]"}}
        assert self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_handles_empty_author(self) -> None:
        comment = {"author": {}}
        assert not self.monitor._is_github_bot_comment(comment)  # noqa: SLF001

    def test_handles_missing_author(self) -> None:
        comment = {"body": "no author"}
        assert not self.monitor._is_github_bot_comment(comment)  # noqa: SLF001


class TestGetLastCodexAutomationCommentTime(unittest.TestCase):
    """Validate _get_last_codex_automation_comment_time method."""

    def setUp(self) -> None:
        self.monitor = mon.JleechanorgPRMonitor(automation_username="test-automation-user")

    def test_returns_latest_codex_comment_time(self) -> None:
        comments = [
            {
                "body": f"First {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "body": f"Second {self.monitor.CODEX_COMMIT_MARKER_PREFIX}def{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T12:00:00Z",
            },
        ]

        result = self.monitor._get_last_codex_automation_comment_time(comments)  # noqa: SLF001
        assert result == "2024-01-01T12:00:00Z"

    def test_returns_none_when_no_codex_comments(self) -> None:
        comments = [
            {"body": "Regular comment", "createdAt": "2024-01-01T10:00:00Z"},
        ]

        result = self.monitor._get_last_codex_automation_comment_time(comments)  # noqa: SLF001
        assert result is None

    def test_returns_none_for_empty_list(self) -> None:
        result = self.monitor._get_last_codex_automation_comment_time([])  # noqa: SLF001
        assert result is None

    def test_uses_updated_at_fallback(self) -> None:
        comments = [
            {
                "body": f"Update {self.monitor.CODEX_COMMIT_MARKER_PREFIX}xyz{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "updatedAt": "2024-01-01T15:00:00Z",
            },
        ]

        result = self.monitor._get_last_codex_automation_comment_time(comments)  # noqa: SLF001
        assert result == "2024-01-01T15:00:00Z"


class TestFixCommentCheckpointLogic(unittest.TestCase):
    """Test fix-comment checkpoint logic: completion marker before history."""

    def setUp(self) -> None:
        self.monitor = mon.JleechanorgPRMonitor(automation_username="test-automation-user")

    def test_completion_marker_with_no_unaddressed_comments_skips(self):
        """Test that completion marker + no unaddressed comments skips."""
        head_sha = "abc123def"
        
        # Mock methods
        original_get_state = self.monitor._get_pr_comment_state  # noqa: SLF001
        original_count = self.monitor._count_workflow_comments  # noqa: SLF001
        original_has_marker = self.monitor._has_fix_comment_comment_for_commit  # noqa: SLF001
        original_has_unaddressed = self.monitor._has_unaddressed_comments  # noqa: SLF001
        original_should_skip = self.monitor._should_skip_pr  # noqa: SLF001
        
        def mock_get_state(*_):  # noqa: ARG001
            return (head_sha, [])
        
        def mock_count(*_):  # noqa: ARG001
            return 0
        
        def mock_has_marker(c, s):  # noqa: ARG001
            return s == head_sha
        
        def mock_has_unaddressed(*_):  # noqa: ARG001
            return False
        
        def mock_should_skip(*_):  # noqa: ARG001
            return False
        
        self.monitor._get_pr_comment_state = mock_get_state  # noqa: SLF001
        self.monitor._count_workflow_comments = mock_count  # noqa: SLF001
        self.monitor._has_fix_comment_comment_for_commit = mock_has_marker  # noqa: SLF001
        self.monitor._has_unaddressed_comments = mock_has_unaddressed  # noqa: SLF001
        self.monitor._should_skip_pr = mock_should_skip  # noqa: SLF001
        
        try:
            result = self.monitor._process_pr_fix_comment(  # noqa: SLF001
                "test/repo",
                123,
                {"headRefOid": head_sha, "headRefName": "test-branch"},
                "claude",
            )
            assert result == "skipped"
        finally:
            # Restore original methods
            self.monitor._get_pr_comment_state = original_get_state  # noqa: SLF001
            self.monitor._count_workflow_comments = original_count  # noqa: SLF001
            self.monitor._has_fix_comment_comment_for_commit = original_has_marker  # noqa: SLF001
            self.monitor._has_unaddressed_comments = original_has_unaddressed  # noqa: SLF001
            self.monitor._should_skip_pr = original_should_skip  # noqa: SLF001

    def test_completion_marker_with_unaddressed_comments_reprocesses(self):
        """Test that completion marker + unaddressed comments reprocesses."""
        head_sha = "abc123def"
        
        original_get_state = self.monitor._get_pr_comment_state  # noqa: SLF001
        original_count = self.monitor._count_workflow_comments  # noqa: SLF001
        original_has_marker = self.monitor._has_fix_comment_comment_for_commit  # noqa: SLF001
        original_has_unaddressed = self.monitor._has_unaddressed_comments  # noqa: SLF001
        original_should_skip = self.monitor._should_skip_pr  # noqa: SLF001
        original_cleanup = self.monitor._cleanup_pending_reviews  # noqa: SLF001
        original_dispatch = self.monitor.dispatch_fix_comment_agent
        original_post = self.monitor._post_fix_comment_queued  # noqa: SLF001
        
        def mock_get_state(*_):  # noqa: ARG001
            return (head_sha, [])
        
        def mock_count(*_):  # noqa: ARG001
            return 0
        
        def mock_has_marker(c, s):  # noqa: ARG001
            return s == head_sha
        
        def mock_has_unaddressed(*_):  # noqa: ARG001
            return True  # Has unaddressed comments
        
        def mock_should_skip(*_):  # noqa: ARG001
            return False
        
        def mock_cleanup(*_):  # noqa: ARG001
            pass
        
        def mock_dispatch(*_, **__):  # noqa: ARG001
            return False  # Agent fails to prevent full execution
        
        def mock_post(*_, **__):  # noqa: ARG001
            return True
        
        self.monitor._get_pr_comment_state = mock_get_state  # noqa: SLF001
        self.monitor._count_workflow_comments = mock_count  # noqa: SLF001
        self.monitor._has_fix_comment_comment_for_commit = mock_has_marker  # noqa: SLF001
        self.monitor._has_unaddressed_comments = mock_has_unaddressed  # noqa: SLF001
        self.monitor._should_skip_pr = mock_should_skip  # noqa: SLF001
        self.monitor._cleanup_pending_reviews = mock_cleanup  # noqa: SLF001
        self.monitor.dispatch_fix_comment_agent = mock_dispatch
        self.monitor._post_fix_comment_queued = mock_post  # noqa: SLF001
        
        try:
            result = self.monitor._process_pr_fix_comment(  # noqa: SLF001
                "test/repo",
                123,
                {"headRefOid": head_sha, "headRefName": "test-branch"},
                "claude",
            )
            assert result == "failed"  # Agent dispatched (not skipped)
        finally:
            # Restore original methods
            self.monitor._get_pr_comment_state = original_get_state  # noqa: SLF001
            self.monitor._count_workflow_comments = original_count  # noqa: SLF001
            self.monitor._has_fix_comment_comment_for_commit = original_has_marker  # noqa: SLF001
            self.monitor._has_unaddressed_comments = original_has_unaddressed  # noqa: SLF001
            self.monitor._should_skip_pr = original_should_skip  # noqa: SLF001
            self.monitor._cleanup_pending_reviews = original_cleanup  # noqa: SLF001
            self.monitor.dispatch_fix_comment_agent = original_dispatch
            self.monitor._post_fix_comment_queued = original_post  # noqa: SLF001

    def test_no_completion_marker_history_no_unaddressed_skips(self):
        """Test that no completion marker + history + no unaddressed skips."""
        head_sha = "abc123def"
        
        original_get_state = self.monitor._get_pr_comment_state  # noqa: SLF001
        original_count = self.monitor._count_workflow_comments  # noqa: SLF001
        original_has_marker = self.monitor._has_fix_comment_comment_for_commit  # noqa: SLF001
        original_has_unaddressed = self.monitor._has_unaddressed_comments  # noqa: SLF001
        original_should_skip = self.monitor._should_skip_pr  # noqa: SLF001
        
        def mock_get_state(*_):  # noqa: ARG001
            return (head_sha, [])
        
        def mock_count(*_):  # noqa: ARG001
            return 0
        
        def mock_has_marker(*_):  # noqa: ARG001
            return False  # No completion marker
        
        def mock_has_unaddressed(*_):  # noqa: ARG001
            return False  # No unaddressed comments
        
        def mock_should_skip(*_):  # noqa: ARG001
            return True  # In history
        
        self.monitor._get_pr_comment_state = mock_get_state  # noqa: SLF001
        self.monitor._count_workflow_comments = mock_count  # noqa: SLF001
        self.monitor._has_fix_comment_comment_for_commit = mock_has_marker  # noqa: SLF001
        self.monitor._has_unaddressed_comments = mock_has_unaddressed  # noqa: SLF001
        self.monitor._should_skip_pr = mock_should_skip  # noqa: SLF001
        
        try:
            result = self.monitor._process_pr_fix_comment(  # noqa: SLF001
                "test/repo",
                123,
                {"headRefOid": head_sha, "headRefName": "test-branch"},
                "claude",
            )
            assert result == "skipped"
        finally:
            # Restore original methods
            self.monitor._get_pr_comment_state = original_get_state  # noqa: SLF001
            self.monitor._count_workflow_comments = original_count  # noqa: SLF001
            self.monitor._has_fix_comment_comment_for_commit = original_has_marker  # noqa: SLF001
            self.monitor._has_unaddressed_comments = original_has_unaddressed  # noqa: SLF001
            self.monitor._should_skip_pr = original_should_skip  # noqa: SLF001

    def test_no_completion_marker_history_with_unaddressed_reprocesses(self):
        """Test that no completion marker + history + unaddressed reprocesses."""
        head_sha = "abc123def"
        
        original_get_state = self.monitor._get_pr_comment_state  # noqa: SLF001
        original_count = self.monitor._count_workflow_comments  # noqa: SLF001
        original_has_marker = self.monitor._has_fix_comment_comment_for_commit  # noqa: SLF001
        original_has_unaddressed = self.monitor._has_unaddressed_comments  # noqa: SLF001
        original_should_skip = self.monitor._should_skip_pr  # noqa: SLF001
        original_cleanup = self.monitor._cleanup_pending_reviews  # noqa: SLF001
        original_dispatch = self.monitor.dispatch_fix_comment_agent
        original_post = self.monitor._post_fix_comment_queued  # noqa: SLF001
        
        def mock_get_state(*_):  # noqa: ARG001
            return (head_sha, [])
        
        def mock_count(*_):  # noqa: ARG001
            return 0
        
        def mock_has_marker(*_):  # noqa: ARG001
            return False  # No completion marker
        
        def mock_has_unaddressed(*_):  # noqa: ARG001
            return True  # Has unaddressed comments
        
        def mock_should_skip(*_):  # noqa: ARG001
            return True  # In history
        
        def mock_cleanup(*_):  # noqa: ARG001
            pass
        
        def mock_dispatch(*_, **__):  # noqa: ARG001
            return False
        
        def mock_post(*_, **__):  # noqa: ARG001
            return True
        
        self.monitor._get_pr_comment_state = mock_get_state  # noqa: SLF001
        self.monitor._count_workflow_comments = mock_count  # noqa: SLF001
        self.monitor._has_fix_comment_comment_for_commit = mock_has_marker  # noqa: SLF001
        self.monitor._has_unaddressed_comments = mock_has_unaddressed  # noqa: SLF001
        self.monitor._should_skip_pr = mock_should_skip  # noqa: SLF001
        self.monitor._cleanup_pending_reviews = mock_cleanup  # noqa: SLF001
        self.monitor.dispatch_fix_comment_agent = mock_dispatch
        self.monitor._post_fix_comment_queued = mock_post  # noqa: SLF001
        
        try:
            result = self.monitor._process_pr_fix_comment(  # noqa: SLF001
                "test/repo",
                123,
                {"headRefOid": head_sha, "headRefName": "test-branch"},
                "claude",
            )
            assert result == "failed"  # Agent dispatched (not skipped)
        finally:
            # Restore original methods
            self.monitor._get_pr_comment_state = original_get_state  # noqa: SLF001
            self.monitor._count_workflow_comments = original_count  # noqa: SLF001
            self.monitor._has_fix_comment_comment_for_commit = original_has_marker  # noqa: SLF001
            self.monitor._has_unaddressed_comments = original_has_unaddressed  # noqa: SLF001
            self.monitor._should_skip_pr = original_should_skip  # noqa: SLF001
            self.monitor._cleanup_pending_reviews = original_cleanup  # noqa: SLF001
            self.monitor.dispatch_fix_comment_agent = original_dispatch
            self.monitor._post_fix_comment_queued = original_post  # noqa: SLF001

    def test_no_completion_marker_no_history_no_unaddressed_skips(self):
        """Test that no completion marker + no history + no unaddressed skips."""
        head_sha = "abc123def"
        
        original_get_state = self.monitor._get_pr_comment_state  # noqa: SLF001
        original_count = self.monitor._count_workflow_comments  # noqa: SLF001
        original_has_marker = self.monitor._has_fix_comment_comment_for_commit  # noqa: SLF001
        original_has_unaddressed = self.monitor._has_unaddressed_comments  # noqa: SLF001
        original_should_skip = self.monitor._should_skip_pr  # noqa: SLF001
        
        def mock_get_state(*_):  # noqa: ARG001
            return (head_sha, [])
        
        def mock_count(*_):  # noqa: ARG001
            return 0
        
        def mock_has_marker(*_):  # noqa: ARG001
            return False
        
        def mock_has_unaddressed(*_):  # noqa: ARG001
            return False
        
        def mock_should_skip(*_):  # noqa: ARG001
            return False  # Not in history
        
        self.monitor._get_pr_comment_state = mock_get_state  # noqa: SLF001
        self.monitor._count_workflow_comments = mock_count  # noqa: SLF001
        self.monitor._has_fix_comment_comment_for_commit = mock_has_marker  # noqa: SLF001
        self.monitor._has_unaddressed_comments = mock_has_unaddressed  # noqa: SLF001
        self.monitor._should_skip_pr = mock_should_skip  # noqa: SLF001
        
        try:
            result = self.monitor._process_pr_fix_comment(  # noqa: SLF001
                "test/repo",
                123,
                {"headRefOid": head_sha, "headRefName": "test-branch"},
                "claude",
            )
            assert result == "skipped"
        finally:
            # Restore original methods
            self.monitor._get_pr_comment_state = original_get_state  # noqa: SLF001
            self.monitor._count_workflow_comments = original_count  # noqa: SLF001
            self.monitor._has_fix_comment_comment_for_commit = original_has_marker  # noqa: SLF001
            self.monitor._has_unaddressed_comments = original_has_unaddressed  # noqa: SLF001
            self.monitor._should_skip_pr = original_should_skip  # noqa: SLF001

class TestRaceConditionFix(unittest.TestCase):
    """Test that queued comments are detected before agent dispatch."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = mon.JleechanorgPRMonitor(automation_username="test-automation-user")
        self.head_sha = "feedface1234567890abcdef"

    def test_extract_fix_comment_run_marker(self):
        """Test extraction of commit SHA from queued run markers."""
        # New format: <!-- fix-comment-run-automation-commit:agent:sha -->
        comment_body = (
            "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
            f"<!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->"
        )
        extracted_sha = self.monitor._extract_fix_comment_run_marker(comment_body)  # noqa: SLF001
        self.assertEqual(extracted_sha, self.head_sha)

    def test_extract_fix_comment_run_marker_handles_unknown_sha(self):
        """Test extraction handles 'unknown' SHA value."""
        comment_body = (
            "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
            "<!-- fix-comment-run-automation-commit:gemini:unknown-->"
        )
        extracted_sha = self.monitor._extract_fix_comment_run_marker(comment_body)  # noqa: SLF001
        self.assertEqual(extracted_sha, "unknown")

    def test_extract_fix_comment_run_marker_returns_none_for_missing_marker(self):
        """Test extraction returns None when marker is missing."""
        comment_body = "Just a regular comment without any markers."
        extracted_sha = self.monitor._extract_fix_comment_run_marker(comment_body)  # noqa: SLF001
        self.assertIsNone(extracted_sha)

    def test_has_fix_comment_queued_for_commit_detects_queued_comment(self):
        """Test that queued comments are detected for the correct commit."""
        comments = [
            {
                "body": (
                    "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
                    f"<!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->"
                ),
                "author": {"login": "test-automation-user"},
            }
        ]
        result = self.monitor._has_fix_comment_queued_for_commit(comments, self.head_sha)  # noqa: SLF001
        self.assertTrue(result, "Should detect queued comment for matching commit")

    def test_has_fix_comment_queued_for_commit_ignores_wrong_commit(self):
        """Test that queued comments for different commits are ignored."""
        different_sha = "different1234567890abcdef"
        comments = [
            {
                "body": (
                    "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
                    f"<!-- fix-comment-run-automation-commit:gemini:{different_sha}-->"
                ),
                "author": {"login": "test-automation-user"},
            }
        ]
        result = self.monitor._has_fix_comment_queued_for_commit(comments, self.head_sha)  # noqa: SLF001
        self.assertFalse(result, "Should ignore queued comment for different commit")

    def test_has_fix_comment_queued_for_commit_ignores_non_automation_user(self):
        """Test that queued comments from non-automation users are ignored."""
        comments = [
            {
                "body": (
                    "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
                    f"<!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->"
                ),
                "author": {"login": "other-user"},
            }
        ]
        result = self.monitor._has_fix_comment_queued_for_commit(comments, self.head_sha)  # noqa: SLF001
        self.assertFalse(result, "Should ignore queued comment from non-automation user")

    def test_has_fix_comment_queued_for_commit_returns_false_for_no_head_sha(self):
        """Test that function returns False when head_sha is None."""
        comments = [
            {
                "body": (
                    "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
                    "<!-- fix-comment-run-automation-commit:gemini:abc123-->"
                ),
                "author": {"login": "test-automation-user"},
            }
        ]
        result = self.monitor._has_fix_comment_queued_for_commit(comments, None)  # noqa: SLF001
        self.assertFalse(result, "Should return False when head_sha is None")

    @patch.object(mon.JleechanorgPRMonitor, "_get_pr_comment_state")
    @patch.object(mon.JleechanorgPRMonitor, "_count_workflow_comments", return_value=0)
    @patch.object(mon.JleechanorgPRMonitor, "_has_unaddressed_comments", return_value=True)
    @patch.object(mon.JleechanorgPRMonitor, "_has_fix_comment_comment_for_commit", return_value=False)
    @patch.object(mon.JleechanorgPRMonitor, "_should_skip_pr", return_value=False)
    @patch.object(mon.JleechanorgPRMonitor, "_cleanup_pending_reviews")
    @patch.object(mon.JleechanorgPRMonitor, "dispatch_fix_comment_agent")
    @patch.object(mon.JleechanorgPRMonitor, "_post_fix_comment_queued")
    @patch.object(mon.JleechanorgPRMonitor, "_start_fix_comment_review_watcher", return_value=True)
    def test_process_pr_fix_comment_skips_when_queued_comment_exists(
        self,
        mock_watcher,
        mock_post_queued,
        mock_dispatch,
        mock_cleanup,
        mock_skip_pr,
        mock_has_completion,
        mock_has_unaddressed,
        mock_count,
        mock_get_state,
    ):
        """Test that agent dispatch is skipped when queued comment exists (no completion marker)."""
        # Setup: queued comment exists for this commit, but NO completion marker
        comments = [
            {
                "body": (
                    "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
                    f"<!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->"
                ),
                "author": {"login": "test-automation-user"},
            }
        ]

        pr_data = {
            "title": "Test PR",
            "headRefName": "test-branch",
            "headRefOid": self.head_sha,
        }

        # Mock _get_pr_comment_state to return comments
        mock_get_state.return_value = (self.head_sha, comments)

        result = self.monitor._process_pr_fix_comment(  # noqa: SLF001
            "test-org/test-repo",
            123,
            pr_data,
            agent_cli="gemini",
        )

        # Should skip without dispatching agent (queued marker exists, no completion marker)
        self.assertEqual(result, "skipped")
        mock_dispatch.assert_not_called()
        mock_post_queued.assert_not_called()

    @patch.object(mon.JleechanorgPRMonitor, "_get_pr_comment_state")
    @patch.object(mon.JleechanorgPRMonitor, "_count_workflow_comments", return_value=0)
    @patch.object(mon.JleechanorgPRMonitor, "_has_unaddressed_comments", return_value=True)
    @patch.object(mon.JleechanorgPRMonitor, "_has_fix_comment_comment_for_commit", return_value=True)
    @patch.object(mon.JleechanorgPRMonitor, "_should_skip_pr", return_value=False)
    @patch.object(mon.JleechanorgPRMonitor, "_cleanup_pending_reviews")
    @patch.object(mon.JleechanorgPRMonitor, "dispatch_fix_comment_agent", return_value=True)
    @patch.object(mon.JleechanorgPRMonitor, "_post_fix_comment_queued", return_value=True)
    @patch.object(mon.JleechanorgPRMonitor, "_start_fix_comment_review_watcher", return_value=True)
    def test_process_pr_fix_comment_reprocesses_with_completion_marker_and_stale_queued_marker(
        self,
        mock_watcher,
        mock_post_queued,
        mock_dispatch,
        mock_cleanup,
        mock_skip_pr,
        mock_has_completion,
        mock_has_unaddressed,
        mock_count,
        mock_get_state,
    ):
        """Test that reprocessing works when completion marker exists, even with stale queued marker.
        
        This tests the fix for the bug where stale queued markers blocked legitimate reprocessing.
        """
        # Setup: completion marker exists + stale queued marker + unaddressed comments
        comments = [
            {
                "body": (
                    "[AI automation] Fix-comment automation complete. Please review.\n\n"
                    f"<!-- fix-comment-automation-commit:gemini:{self.head_sha}-->"
                ),
                "author": {"login": "test-automation-user"},
            },
            {
                "body": (
                    "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
                    f"<!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->"
                ),
                "author": {"login": "test-automation-user"},
            },
        ]

        pr_data = {
            "title": "Test PR",
            "headRefName": "test-branch",
            "headRefOid": self.head_sha,
        }

        # Mock _get_pr_comment_state to return comments
        mock_get_state.return_value = (self.head_sha, comments)

        result = self.monitor._process_pr_fix_comment(  # noqa: SLF001
            "test-org/test-repo",
            123,
            pr_data,
            agent_cli="gemini",
        )

        # Should dispatch agent (completion marker exists, so stale queued marker is ignored)
        self.assertEqual(result, "posted")
        mock_dispatch.assert_called_once()
        mock_post_queued.assert_called_once()

    @patch.object(mon.JleechanorgPRMonitor, "_get_pr_comment_state")
    @patch.object(mon.JleechanorgPRMonitor, "_count_workflow_comments", return_value=0)
    @patch.object(mon.JleechanorgPRMonitor, "_has_unaddressed_comments", return_value=True)
    @patch.object(mon.JleechanorgPRMonitor, "_has_fix_comment_comment_for_commit", return_value=False)
    @patch.object(mon.JleechanorgPRMonitor, "_should_skip_pr", return_value=False)
    @patch.object(mon.JleechanorgPRMonitor, "_cleanup_pending_reviews")
    @patch.object(mon.JleechanorgPRMonitor, "dispatch_fix_comment_agent", return_value=True)
    @patch.object(mon.JleechanorgPRMonitor, "_post_fix_comment_queued", return_value=True)
    @patch.object(mon.JleechanorgPRMonitor, "_start_fix_comment_review_watcher", return_value=True)
    def test_process_pr_fix_comment_dispatches_when_no_queued_comment(
        self,
        mock_watcher,
        mock_post_queued,
        mock_dispatch,
        mock_cleanup,
        mock_skip_pr,
        mock_has_completion,
        mock_has_unaddressed,
        mock_count,
        mock_get_state,
    ):
        """Test that agent dispatch proceeds when no queued comment exists."""
        # Setup: no queued comment exists
        comments = []

        pr_data = {
            "title": "Test PR",
            "headRefName": "test-branch",
            "headRefOid": self.head_sha,
        }

        # Mock _get_pr_comment_state to return empty comments
        mock_get_state.return_value = (self.head_sha, comments)

        result = self.monitor._process_pr_fix_comment(  # noqa: SLF001
            "test-org/test-repo",
            123,
            pr_data,
            agent_cli="gemini",
        )

        # Should dispatch agent
        self.assertEqual(result, "posted")
        mock_dispatch.assert_called_once()
        mock_post_queued.assert_called_once()

    def test_process_pr_fix_comment_allows_rerun_when_stale_queued_comment_exists(self):
        """Test that agent dispatch is allowed when STALE queued comment exists."""
        # Setup: queued comment exists but is OLD (stale)
        stale_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        comments = [
            {
                "body": (
                    "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
                    f"<!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->"
                ),
                "author": {"login": "test-automation-user"},
                "createdAt": stale_time,
            }
        ]

        pr_data = {
            "title": "Test PR",
            "headRefName": "test-branch",
            "headRefOid": self.head_sha,
        }

        # Mock dependencies
        with patch.object(self.monitor, "_get_pr_comment_state", return_value=(self.head_sha, comments)), \
             patch.object(self.monitor, "_count_workflow_comments", return_value=0), \
             patch.object(self.monitor, "_has_unaddressed_comments", return_value=True), \
             patch.object(self.monitor, "_has_fix_comment_comment_for_commit", return_value=False), \
             patch.object(self.monitor, "_should_skip_pr", return_value=False), \
             patch.object(self.monitor, "_cleanup_pending_reviews"), \
             patch.object(self.monitor, "dispatch_fix_comment_agent", return_value=True) as mock_dispatch, \
             patch.object(self.monitor, "_post_fix_comment_queued", return_value=True) as mock_post_queued, \
             patch.object(self.monitor, "_start_fix_comment_review_watcher", return_value=True):
            
            result = self.monitor._process_pr_fix_comment(
                "test-org/test-repo",
                123,
                pr_data,
                agent_cli="gemini",
            )

            # Should dispatch agent because queued comment is stale
            self.assertEqual(result, "posted")
            mock_dispatch.assert_called_once()
            mock_post_queued.assert_called_once()

    def test_process_pr_fix_comment_skips_when_recent_queued_comment_exists(self):
        """Test that agent dispatch is skipped when RECENT queued comment exists."""
        # Setup: queued comment exists and is RECENT
        recent_time = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
        comments = [
            {
                "body": (
                    "[AI automation - gemini] Fix-comment run queued for this PR.\n\n"
                    f"<!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->"
                ),
                "author": {"login": "test-automation-user"},
                "createdAt": recent_time,
            }
        ]

        pr_data = {
            "title": "Test PR",
            "headRefName": "test-branch",
            "headRefOid": self.head_sha,
        }

        # Mock dependencies
        with patch.object(self.monitor, "_get_pr_comment_state", return_value=(self.head_sha, comments)), \
             patch.object(self.monitor, "_count_workflow_comments", return_value=0), \
             patch.object(self.monitor, "_has_unaddressed_comments", return_value=True), \
             patch.object(self.monitor, "_has_fix_comment_comment_for_commit", return_value=False), \
             patch.object(self.monitor, "_should_skip_pr", return_value=False), \
             patch.object(self.monitor, "_cleanup_pending_reviews"), \
             patch.object(self.monitor, "dispatch_fix_comment_agent") as mock_dispatch, \
             patch.object(self.monitor, "_post_fix_comment_queued") as mock_post_queued:
            
            result = self.monitor._process_pr_fix_comment(
                "test-org/test-repo",
                123,
                pr_data,
                agent_cli="gemini",
            )

            # Should skip
            self.assertEqual(result, "skipped")
            mock_dispatch.assert_not_called()

    def test_get_fix_comment_queued_info_uses_newest_comment(self):
        """Test that _get_fix_comment_queued_info picks the NEWEST queued marker."""
        old_time = (datetime.now(UTC) - timedelta(hours=5)).isoformat()
        new_time = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
        
        comments = [
            {
                "body": f"Old queued run <!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->",
                "author": {"login": "test-automation-user"},
                "createdAt": old_time,
            },
            {
                "body": f"New queued run <!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->",
                "author": {"login": "test-automation-user"},
                "createdAt": new_time,
            },
        ]
        
        # Should pick the new one (10 mins old = ~0.16 hours)
        info = self.monitor._get_fix_comment_queued_info(comments, self.head_sha)
        self.assertIsNotNone(info)
        self.assertLess(info["age_hours"], 1.0)
        self.assertEqual(info["created_at"], new_time)

    def test_get_fix_comment_queued_info_handles_unparseable_timestamp(self):
        """Test that unparseable timestamp results in 0.0 age."""
        comments = [
            {
                "body": f"Queued run <!-- fix-comment-run-automation-commit:gemini:{self.head_sha}-->",
                "author": {"login": "test-automation-user"},
                "createdAt": "invalid-date",
            }
        ]
        
        info = self.monitor._get_fix_comment_queued_info(comments, self.head_sha)
        self.assertIsNotNone(info)
        self.assertEqual(info["age_hours"], 0.0)
