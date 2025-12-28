import unittest

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from automation.jleechanorg_pr_automation import jleechanorg_pr_monitor as mon

FAILED_PR_NUMBER = 2
EXPECTED_ACTIONABLE_COUNT = 2


def codex_marker(monitor: mon.JleechanorgPRMonitor, token: str) -> str:
    return f"{monitor.CODEX_COMMIT_MARKER_PREFIX}{token}{monitor.CODEX_COMMIT_MARKER_SUFFIX}"


def test_list_actionable_prs_conflicts_and_failing(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    monitor = mon.JleechanorgPRMonitor()

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


class TestBotCommentDetection(unittest.TestCase):
    """Validate detection of new GitHub bot comments since last Codex automation comment."""

    def setUp(self) -> None:
        self.monitor = mon.JleechanorgPRMonitor()

    def test_identifies_new_github_actions_bot_comment(self) -> None:
        """Should detect new comment from github-actions[bot] after Codex comment."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix this {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI failed: test_something assertion error",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        assert self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_identifies_new_dependabot_comment(self) -> None:
        """Should detect new comment from dependabot[bot] after Codex comment."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"Fix issue {codex_marker(self.monitor, 'def456')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "dependabot[bot]"},
                "body": "Security vulnerability detected",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        assert self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_no_detection_when_bot_comment_before_codex(self) -> None:
        """Should NOT detect bot comments that came BEFORE Codex comment."""
        comments = [
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI failed",
                "createdAt": "2024-01-01T09:00:00Z",
            },
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
        ]

        assert not self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_identifies_bot_comment_without_prior_codex_comment(self) -> None:
        """Should treat any bot comment as new when no Codex automation comment exists."""
        comments = [
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI failed",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "jleechan"},
                "body": "Regular comment without marker",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        assert self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_excludes_codex_bot_comments(self) -> None:
        """Should NOT count codex[bot] as a new bot comment to process."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "codex[bot]"},
                "body": "Codex summary: fixed the issue",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        assert not self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_identifies_coderabbitai_bot_comments(self) -> None:
        """Should count coderabbitai[bot] as a new bot comment to process."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "coderabbitai[bot]"},
                "body": "Code review completed",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        assert self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_excludes_copilot_bot_comments(self) -> None:
        """Should NOT count copilot[bot] as a new bot comment to process."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "copilot[bot]"},
                "body": "Copilot suggestion",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        assert not self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_ignores_human_comments_after_codex(self) -> None:
        """Human comments after Codex should NOT trigger new bot detection."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "reviewer"},
                "body": "LGTM",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        assert not self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_uses_latest_codex_comment_time(self) -> None:
        """Should use the timestamp of the MOST RECENT Codex comment."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"Fix 1 {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI failed",
                "createdAt": "2024-01-01T11:00:00Z",
            },
            {
                "author": {"login": "jleechan"},
                "body": f"Fix 2 {codex_marker(self.monitor, 'def456')}",
                "createdAt": "2024-01-01T12:00:00Z",
            },
        ]

        # Bot comment at 11:00 is BEFORE latest Codex comment at 12:00
        assert not self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_identifies_bot_comment_after_latest_codex(self) -> None:
        """Should detect bot comment that comes after the latest Codex comment."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"Fix 1 {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "jleechan"},
                "body": f"Fix 2 {codex_marker(self.monitor, 'def456')}",
                "createdAt": "2024-01-01T11:00:00Z",
            },
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI still failing",
                "createdAt": "2024-01-01T12:00:00Z",
            },
        ]

        assert self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001

    def test_handles_empty_comments_list(self) -> None:
        """Should handle empty comments list gracefully."""
        assert not self.monitor._has_new_bot_comments_since_codex([])  # noqa: SLF001

    def test_handles_missing_author(self) -> None:
        """Should handle comments with missing author field."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"Fix {codex_marker(self.monitor, 'abc123')}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "body": "Comment with no author",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        # Should not crash and should return False (no valid bot comment)
        assert not self.monitor._has_new_bot_comments_since_codex(comments)  # noqa: SLF001


class TestIsGithubBotComment(unittest.TestCase):
    """Validate _is_github_bot_comment method."""

    def setUp(self) -> None:
        self.monitor = mon.JleechanorgPRMonitor()

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
        self.monitor = mon.JleechanorgPRMonitor()

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
