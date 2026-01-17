#!/usr/bin/env python3
"""
Test for fixpr workflow return value handling.

Regression test for cursor[bot] bug report (Comment ID 2674134633):
"FixPR workflow ignores queued comment posting failure"

Tests that _process_pr_fixpr correctly captures and handles the return value
from _post_fixpr_queued, matching the behavior of _process_pr_fix_comment.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch, MagicMock, call

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestFixprReturnValue(unittest.TestCase):
    """Test fixpr workflow return value handling"""

    def setUp(self):
        """Set up test environment with comprehensive mocking"""
        # Patch AutomationSafetyManager during JleechanorgPRMonitor initialization
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            self.monitor.safety_manager.fixpr_limit = 10

        # Mock logger to avoid logging issues
        self.monitor.logger = MagicMock()

    # Patch decorators apply bottom-to-top; parameter order follows that application order.
    # Order: has_failing_checks, execute_subprocess_with_timeout, dispatch_agent_for_pr, ensure_base_clone, chdir, TaskDispatcher
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher')
    def test_fixpr_returns_partial_when_queued_comment_fails(
        self,
        mock_dispatcher,
        mock_chdir,
        mock_clone,
        mock_dispatch_agent,
        mock_subprocess,
        mock_has_failing_checks,
    ):
        """
        Test that _process_pr_fixpr returns 'partial' when _post_fixpr_queued fails.

        Regression test for cursor[bot] bug: Method was ignoring return value and
        always returning 'posted' even when comment posting failed.
        """
        # Setup mocks
        mock_clone.return_value = "/tmp/fake/repo"
        mock_dispatch_agent.return_value = True  # Agent dispatch succeeds

        # Mock subprocess to return MERGEABLE (no conflicts)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"mergeable": "MERGEABLE"}'
        mock_subprocess.return_value = mock_result

        # Mock FAILING checks so fixpr processes the PR (doesn't skip)
        mock_has_failing_checks.return_value = True

        pr_data = {
            "number": 1234,
            "title": "Test PR",
            "headRefName": "test-branch",
            "baseRefName": "main",
            "url": "https://github.com/test/repo/pull/1234",
            "headRepository": {"owner": {"login": "test"}},
            "headRefOid": "abc123",
            "statusCheckRollup": [],
            "mergeable": "MERGEABLE",
        }

        # Comprehensive mocking to avoid all side effects
        # dispatch_agent_for_pr is already mocked at module level via @patch decorator
        with patch.object(self.monitor, '_normalize_repository_name', return_value="test/repo"):
            with patch.object(self.monitor, '_get_pr_comment_state', return_value=("abc123", [])):
                with patch.object(self.monitor, '_should_skip_pr', return_value=False):
                    with patch.object(self.monitor, '_count_workflow_comments', return_value=5):  # Under limit
                        with patch.object(self.monitor, '_cleanup_pending_reviews'):
                            with patch.object(self.monitor, '_post_fixpr_queued', return_value=False) as mock_post_queued:  # FAILS
                                with patch.object(self.monitor, '_record_processed_pr'):
                                    result = self.monitor._process_pr_fixpr(
                                        repository="test/repo",
                                        pr_number=1234,
                                        pr_data=pr_data,
                                    )

        # CRITICAL: Should return "partial" when queued comment fails
        self.assertEqual(
            result,
            "partial",
            "REGRESSION BUG: _process_pr_fixpr should return 'partial' when _post_fixpr_queued fails, "
            "not ignore the return value. This causes failed marker posts to not count against fixpr_limit."
        )
        # Verify _post_fixpr_queued was called
        mock_post_queued.assert_called_once()

    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher')
    def test_fixpr_returns_posted_when_queued_comment_succeeds(
        self,
        mock_dispatcher,
        mock_chdir,
        mock_clone,
        mock_dispatch_agent,
        mock_subprocess,
        mock_has_failing_checks,
    ):
        """
        Test that _process_pr_fixpr returns 'posted' when _post_fixpr_queued succeeds.

        This is the happy path - verifies correct behavior when comment posting works.
        """
        # Setup mocks
        mock_clone.return_value = "/tmp/fake/repo"
        mock_dispatch_agent.return_value = True  # Agent dispatch succeeds

        # Mock subprocess to return MERGEABLE (no conflicts)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"mergeable": "MERGEABLE"}'
        mock_subprocess.return_value = mock_result

        # Mock FAILING checks so fixpr processes the PR (doesn't skip)
        mock_has_failing_checks.return_value = True

        pr_data = {
            "number": 1234,
            "title": "Test PR",
            "headRefName": "test-branch",
            "baseRefName": "main",
            "url": "https://github.com/test/repo/pull/1234",
            "headRepository": {"owner": {"login": "test"}},
            "headRefOid": "abc123",
            "statusCheckRollup": [],
            "mergeable": "MERGEABLE",
        }

        # Comprehensive mocking to avoid all side effects
        # dispatch_agent_for_pr is already mocked at module level via @patch decorator
        with patch.object(self.monitor, '_normalize_repository_name', return_value="test/repo"):
            with patch.object(self.monitor, '_get_pr_comment_state', return_value=("abc123", [])):
                with patch.object(self.monitor, '_should_skip_pr', return_value=False):
                    with patch.object(self.monitor, '_count_workflow_comments', return_value=5):  # Under limit
                        with patch.object(self.monitor, '_cleanup_pending_reviews'):
                            with patch.object(self.monitor, '_post_fixpr_queued', return_value=True) as mock_post_queued:  # SUCCEEDS
                                with patch.object(self.monitor, '_record_processed_pr'):
                                    result = self.monitor._process_pr_fixpr(
                                        repository="test/repo",
                                        pr_number=1234,
                                        pr_data=pr_data,
                                    )

        # Should return "posted" when everything succeeds
        self.assertEqual(result, "posted")
        # Verify _post_fixpr_queued was called
        mock_post_queued.assert_called_once()



class TestFixprSkipsCleanPRs(unittest.TestCase):
    """Test that fixpr skips PRs with no conflicts or failing checks"""

    def setUp(self):
        """Set up test environment with comprehensive mocking"""
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            self.monitor.safety_manager.fixpr_limit = 10

        self.monitor.logger = MagicMock()

    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone')
    def test_fixpr_skips_clean_pr_no_conflicts_no_failing_checks(
        self,
        mock_clone,
        mock_dispatch_agent,
        mock_subprocess,
        mock_has_failing_checks,
    ):
        """
        Test that _process_pr_fixpr returns 'skipped' for a clean PR.

        A clean PR is one that:
        - Has no merge conflicts (mergeable != CONFLICTING)
        - Has no failing checks

        Bug fix: Previously, fixpr would run on clean PRs if they were new
        (not in processing history), wasting automation resources.
        """
        # Mock subprocess to return MERGEABLE (no conflicts)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"mergeable": "MERGEABLE"}'
        mock_subprocess.return_value = mock_result

        # Mock no failing checks
        mock_has_failing_checks.return_value = False

        pr_data = {
            "number": 3682,
            "title": "Clean PR - No Issues",
            "headRefName": "clean-branch",
            "baseRefName": "main",
            "url": "https://github.com/test/repo/pull/3682",
            "headRefOid": "abc123def456",
            "mergeable": "MERGEABLE",
        }

        with patch.object(self.monitor, '_normalize_repository_name', return_value="test/repo"):
            with patch.object(self.monitor, '_get_pr_comment_state', return_value=("abc123def456", [])):
                with patch.object(self.monitor, '_count_workflow_comments', return_value=0):
                    result = self.monitor._process_pr_fixpr(
                        repository="test/repo",
                        pr_number=3682,
                        pr_data=pr_data,
                    )

        # CRITICAL: Should return "skipped" for clean PRs
        self.assertEqual(
            result,
            "skipped",
            "BUG: _process_pr_fixpr should skip clean PRs (no conflicts, no failing checks). "
            "Running fixpr on clean PRs wastes automation resources and spams PRs."
        )

        # Verify agent was NOT dispatched
        mock_dispatch_agent.assert_not_called()
        mock_clone.assert_not_called()

    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher')
    def test_fixpr_processes_pr_with_failing_checks(
        self,
        mock_dispatcher,
        mock_chdir,
        mock_clone,
        mock_dispatch_agent,
        mock_subprocess,
        mock_has_failing_checks,
    ):
        """
        Test that _process_pr_fixpr processes PRs with failing checks.
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"mergeable": "MERGEABLE"}'
        mock_subprocess.return_value = mock_result

        # Mock FAILING checks
        mock_has_failing_checks.return_value = True

        mock_clone.return_value = "/tmp/fake/repo"
        mock_dispatch_agent.return_value = True

        pr_data = {
            "number": 1234,
            "title": "PR with Failing Checks",
            "headRefName": "failing-branch",
            "baseRefName": "main",
            "url": "https://github.com/test/repo/pull/1234",
            "headRefOid": "abc123",
            "mergeable": "MERGEABLE",
        }

        with patch.object(self.monitor, '_normalize_repository_name', return_value="test/repo"):
            with patch.object(self.monitor, '_get_pr_comment_state', return_value=("abc123", [])):
                with patch.object(self.monitor, '_count_workflow_comments', return_value=0):
                    with patch.object(self.monitor, '_should_skip_pr', return_value=False):
                        with patch.object(self.monitor, '_cleanup_pending_reviews'):
                            # dispatch_agent_for_pr is already mocked at module level via @patch decorator
                            with patch.object(self.monitor, '_post_fixpr_queued', return_value=True):
                                with patch.object(self.monitor, '_record_processed_pr'):
                                    result = self.monitor._process_pr_fixpr(
                                        repository="test/repo",
                                        pr_number=1234,
                                        pr_data=pr_data,
                                    )

        # Should process PRs with failing checks
        self.assertEqual(result, "posted")
        mock_dispatch_agent.assert_called_once()

    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher')
    def test_fixpr_processes_pr_with_conflicts(
        self,
        mock_dispatcher,
        mock_chdir,
        mock_clone,
        mock_dispatch_agent,
        mock_subprocess,
        mock_has_failing_checks,
    ):
        """
        Test that _process_pr_fixpr processes PRs with merge conflicts.
        """
        # Mock CONFLICTING merge status
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"mergeable": "CONFLICTING"}'
        mock_subprocess.return_value = mock_result

        # No failing checks (conflict alone should trigger processing)
        mock_has_failing_checks.return_value = False

        mock_clone.return_value = "/tmp/fake/repo"
        mock_dispatch_agent.return_value = True

        pr_data = {
            "number": 5678,
            "title": "PR with Conflicts",
            "headRefName": "conflict-branch",
            "baseRefName": "main",
            "url": "https://github.com/test/repo/pull/5678",
            "headRefOid": "def456",
            "mergeable": "CONFLICTING",
        }

        with patch.object(self.monitor, '_normalize_repository_name', return_value="test/repo"):
            with patch.object(self.monitor, '_get_pr_comment_state', return_value=("def456", [])):
                with patch.object(self.monitor, '_count_workflow_comments', return_value=0):
                    with patch.object(self.monitor, '_should_skip_pr', return_value=False):
                        with patch.object(self.monitor, '_cleanup_pending_reviews'):
                            # dispatch_agent_for_pr is already mocked at module level via @patch decorator
                            with patch.object(self.monitor, '_post_fixpr_queued', return_value=True):
                                with patch.object(self.monitor, '_record_processed_pr'):
                                    result = self.monitor._process_pr_fixpr(
                                        repository="test/repo",
                                        pr_number=5678,
                                        pr_data=pr_data,
                                    )

        # Should process PRs with conflicts
        self.assertEqual(result, "posted")
        mock_dispatch_agent.assert_called_once()


class TestFixprAPIUnknownAndReprocess(unittest.TestCase):
    def setUp(self):
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            self.monitor.safety_manager.fixpr_limit = 10
            self.monitor.logger = MagicMock()

    def _base_pr(self):
        return {
            "number": 123,
            "title": "Test PR",
            "headRefName": "feature/test",
            "repository": "test/repo",
            "repositoryFullName": "test/repo",
            "headRefOid": "abc12345",
        }

    def test_fixpr_status_unknown_processes_when_new_commit(self):
        pr = self._base_pr()
        
        # Patch dependencies
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks", side_effect=RuntimeError("boom")):
            # gh pr view failure
            mock_subprocess_result = SimpleNamespace(returncode=1, stdout="", stderr="fail")
            with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout", return_value=mock_subprocess_result):
                # History says NOT processed → should proceed
                with patch.object(self.monitor, "_should_skip_pr", return_value=False):
                    with patch.object(self.monitor, "_get_pr_comment_state", return_value=("abc12345", [])):
                        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone", return_value="/tmp/fake/repo"):
                            with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir"):
                                with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher"):
                                    with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr", return_value=True) as mock_dispatch:
                                        with patch.object(self.monitor, "_post_fixpr_queued", return_value=True):
                                            with patch.object(self.monitor, "_record_processed_pr"):
                                                with patch.object(self.monitor, "_cleanup_pending_reviews"):
                                                    with patch.object(self.monitor, "_count_workflow_comments", return_value=0):
                                                        res = self.monitor._process_pr_fixpr("test/repo", 123, pr, agent_cli="claude", model="sonnet")

        self.assertEqual(res, "posted")
        mock_dispatch.assert_called_once()

    def test_fixpr_status_unknown_skips_when_already_processed(self):
        pr = self._base_pr()
        
        # Unknown status path again (e.g. failing checks throws exception)
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks", side_effect=Exception("API Fail")):
            # gh pr view failure
            mock_subprocess_result = SimpleNamespace(returncode=1, stdout="", stderr="fail")
            with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout", return_value=mock_subprocess_result):
                with patch.object(self.monitor, "_get_pr_comment_state", return_value=("abc12345", [])):
                    # History says processed → should skip because status is unknown (cannot confirm issues exist)
                    with patch.object(self.monitor, "_should_skip_pr", return_value=True):
                        with patch.object(self.monitor, "_count_workflow_comments", return_value=0):
                            res = self.monitor._process_pr_fixpr("test/repo", 123, pr, agent_cli="claude", model=None)
        
        self.assertEqual(res, "skipped")
    def test_fixpr_reprocess_when_issues_persist_even_if_processed(self):
        pr = self._base_pr()
        
        # Issues present (e.g., failing checks)
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks", return_value=True):
            mock_subprocess_result = SimpleNamespace(returncode=0, stdout='{"mergeable":"MERGEABLE"}', stderr="")
            with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout", return_value=mock_subprocess_result):
                # Even if history says processed, we should reprocess because has_failing_checks is True
                with patch.object(self.monitor, "_should_skip_pr", return_value=True):
                    with patch.object(self.monitor, "_get_pr_comment_state", return_value=("abc12345", [])):
                        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone", return_value="/tmp/fake/repo"):
                            with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir"):
                                with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher"):
                                    with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr", return_value=True):
                                        with patch.object(self.monitor, "_post_fixpr_queued", return_value=True):
                                            with patch.object(self.monitor, "_record_processed_pr"):
                                                with patch.object(self.monitor, "_cleanup_pending_reviews"):
                                                    with patch.object(self.monitor, "_count_workflow_comments", return_value=0):
                                                        res = self.monitor._process_pr_fixpr("test/repo", 123, pr, agent_cli="claude", model=None)

        self.assertEqual(res, "posted")


class TestFixprUsesCorrectDispatchFunction(unittest.TestCase):
    """
    Regression test for critical bug: fixpr must use dispatch_agent_for_pr (FIXPR prompt),
    NOT dispatch_fix_comment_agent (FIX-COMMENT prompt).

    Bug discovered: _process_pr_fixpr was calling dispatch_fix_comment_agent() which builds
    a task description for addressing review comments, not for fixing conflicts/failing checks.
    """

    def setUp(self):
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            self.monitor.safety_manager.fixpr_limit = 10

    def _base_pr(self):
        return {
            "number": 123,
            "title": "Test PR",
            "headRefName": "test-branch",
            "baseRefName": "main",
            "url": "https://github.com/test/repo/pull/123",
            "headRefOid": "abc12345",
            "mergeable": "CONFLICTING",
        }

    def test_fixpr_calls_dispatch_agent_for_pr_not_dispatch_fix_comment_agent(self):
        """
        REGRESSION TEST: Verify _process_pr_fixpr uses dispatch_agent_for_pr
        which builds FIXPR prompt, not dispatch_fix_comment_agent which builds
        FIX-COMMENT prompt.
        """
        pr = self._base_pr()

        # Mock conflicting status so fixpr processes (doesn't skip)
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks", return_value=False):
            mock_subprocess_result = SimpleNamespace(returncode=0, stdout='{"mergeable":"CONFLICTING"}', stderr="")
            with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout", return_value=mock_subprocess_result):
                with patch.object(self.monitor, "_should_skip_pr", return_value=False):
                    with patch.object(self.monitor, "_get_pr_comment_state", return_value=("abc12345", [])):
                        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone", return_value="/tmp/fake/repo"):
                            with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir"):
                                with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher") as mock_dispatcher_class:
                                    # This is the CORRECT function that should be called
                                    with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr", return_value=True) as mock_correct_dispatch:
                                        # This is the WRONG function that should NOT be called
                                        with patch.object(self.monitor, "dispatch_fix_comment_agent", return_value=True) as mock_wrong_dispatch:
                                            with patch.object(self.monitor, "_post_fixpr_queued", return_value=True):
                                                with patch.object(self.monitor, "_record_processed_pr"):
                                                    with patch.object(self.monitor, "_cleanup_pending_reviews"):
                                                        with patch.object(self.monitor, "_count_workflow_comments", return_value=0):
                                                            res = self.monitor._process_pr_fixpr("test/repo", 123, pr, agent_cli="claude", model=None)

        # CRITICAL ASSERTIONS:
        # 1. The correct function (dispatch_agent_for_pr) MUST be called
        mock_correct_dispatch.assert_called_once()

        # 2. The wrong function (dispatch_fix_comment_agent) MUST NOT be called
        mock_wrong_dispatch.assert_not_called()

        # 3. TaskDispatcher must be instantiated (used by dispatch_agent_for_pr)
        mock_dispatcher_class.assert_called_once()

        # 4. Result should be "posted"
        self.assertEqual(res, "posted")


if __name__ == "__main__":
    unittest.main()
