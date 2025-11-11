#!/usr/bin/env python3
"""
RED Phase: Matrix tests for actionable PR counting logic

Test Matrix: Actionable PR counting should exclude skipped PRs and only count
PRs that actually get processed with comments.
"""

import tempfile
import unittest
from unittest.mock import patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestActionableCountingMatrix(unittest.TestCase):
    """Matrix testing for actionable PR counting with skip exclusion"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = JleechanorgPRMonitor()
        self.monitor.history_storage_path = self.temp_dir

    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_run_monitoring_cycle_should_process_exactly_target_actionable_prs(self):
        """RED: run_monitoring_cycle should process exactly target actionable PRs, not counting skipped"""

        # Create a mix of PRs - some actionable, some should be skipped
        mock_prs = [
            # 3 actionable PRs (new commits)
            {"number": 1001, "state": "open", "isDraft": False, "headRefOid": "new001",
             "repository": "repo1", "headRefName": "feature1", "repositoryFullName": "org/repo1",
             "title": "Actionable PR 1", "updatedAt": "2025-09-28T21:00:00Z"},
            {"number": 1002, "state": "open", "isDraft": False, "headRefOid": "new002",
             "repository": "repo2", "headRefName": "feature2", "repositoryFullName": "org/repo2",
             "title": "Actionable PR 2", "updatedAt": "2025-09-28T20:59:00Z"},
            {"number": 1003, "state": "open", "isDraft": False, "headRefOid": "new003",
             "repository": "repo3", "headRefName": "feature3", "repositoryFullName": "org/repo3",
             "title": "Actionable PR 3", "updatedAt": "2025-09-28T20:58:00Z"},

            # 2 PRs that should be skipped (already processed)
            {"number": 2001, "state": "open", "isDraft": False, "headRefOid": "old001",
             "repository": "repo4", "headRefName": "processed1", "repositoryFullName": "org/repo4",
             "title": "Already Processed PR 1", "updatedAt": "2025-09-28T20:57:00Z"},
            {"number": 2002, "state": "open", "isDraft": False, "headRefOid": "old002",
             "repository": "repo5", "headRefName": "processed2", "repositoryFullName": "org/repo5",
             "title": "Already Processed PR 2", "updatedAt": "2025-09-28T20:56:00Z"}
        ]

        # Pre-record the "processed" PRs as already handled
        self.monitor._record_pr_processing("repo4", "processed1", 2001, "old001")
        self.monitor._record_pr_processing("repo5", "processed2", 2002, "old002")

        # Mock the PR discovery to return our test data
        with patch.object(self.monitor, "discover_open_prs", return_value=mock_prs):
            with patch.object(self.monitor, "_process_pr_comment", return_value=True) as mock_process:

                # RED: This should fail - current implementation counts all PRs, not just actionable ones
                result = self.monitor.run_monitoring_cycle_with_actionable_count(target_actionable_count=3)

                # Should process exactly 3 actionable PRs, not counting the 2 skipped ones
                self.assertEqual(result["actionable_processed"], 3)
                self.assertEqual(result["total_discovered"], 5)
                self.assertEqual(result["skipped_count"], 2)

                # Verify that _process_pr_comment was called exactly 3 times (only for actionable PRs)
                self.assertEqual(mock_process.call_count, 3)

    def test_monitoring_cycle_with_insufficient_actionable_prs_should_process_all_available(self):
        """RED: When fewer actionable PRs than target, should process all available actionable PRs"""

        # Create only 2 actionable PRs, but set target to 5
        mock_prs = [
            {"number": 1001, "state": "open", "isDraft": False, "headRefOid": "new001",
             "repository": "repo1", "headRefName": "feature1", "repositoryFullName": "org/repo1",
             "title": "Actionable PR 1", "updatedAt": "2025-09-28T21:00:00Z"},
            {"number": 1002, "state": "open", "isDraft": False, "headRefOid": "new002",
             "repository": "repo2", "headRefName": "feature2", "repositoryFullName": "org/repo2",
             "title": "Actionable PR 2", "updatedAt": "2025-09-28T20:59:00Z"},

            # 3 closed/processed PRs (not actionable)
            {"number": 2001, "state": "closed", "isDraft": False, "headRefOid": "any001",
             "repository": "repo3", "headRefName": "closed1", "repositoryFullName": "org/repo3",
             "title": "Closed PR", "updatedAt": "2025-09-28T20:58:00Z"},
            {"number": 2002, "state": "open", "isDraft": False, "headRefOid": "old002",
             "repository": "repo4", "headRefName": "processed2", "repositoryFullName": "org/repo4",
             "title": "Processed PR", "updatedAt": "2025-09-28T20:57:00Z"}
        ]

        # Pre-record one as processed
        self.monitor._record_pr_processing("repo4", "processed2", 2002, "old002")

        with patch.object(self.monitor, "discover_open_prs", return_value=mock_prs):
            with patch.object(self.monitor, "_process_pr_comment", return_value=True) as mock_process:

                # RED: This should fail - method doesn't exist yet
                result = self.monitor.run_monitoring_cycle_with_actionable_count(target_actionable_count=5)

                # Should process only the 2 available actionable PRs
                self.assertEqual(result["actionable_processed"], 2)
                self.assertEqual(result["total_discovered"], 4)
                self.assertEqual(result["skipped_count"], 2)  # 1 closed + 1 processed

                # Verify processing was called only for actionable PRs
                self.assertEqual(mock_process.call_count, 2)

    def test_monitoring_cycle_with_zero_actionable_prs_should_process_none(self):
        """RED: When no actionable PRs available, should process 0"""

        # Create only non-actionable PRs
        mock_prs = [
            # All closed or already processed
            {"number": 2001, "state": "closed", "isDraft": False, "headRefOid": "any001",
             "repository": "repo1", "headRefName": "closed1", "repositoryFullName": "org/repo1",
             "title": "Closed PR 1", "updatedAt": "2025-09-28T21:00:00Z"},
            {"number": 2002, "state": "closed", "isDraft": False, "headRefOid": "any002",
             "repository": "repo2", "headRefName": "closed2", "repositoryFullName": "org/repo2",
             "title": "Closed PR 2", "updatedAt": "2025-09-28T20:59:00Z"},
            {"number": 2003, "state": "open", "isDraft": False, "headRefOid": "old003",
             "repository": "repo3", "headRefName": "processed3", "repositoryFullName": "org/repo3",
             "title": "Processed PR", "updatedAt": "2025-09-28T20:58:00Z"}
        ]

        # Mark the open one as already processed
        self.monitor._record_pr_processing("repo3", "processed3", 2003, "old003")

        with patch.object(self.monitor, "discover_open_prs", return_value=mock_prs):
            with patch.object(self.monitor, "_process_pr_comment", return_value=True) as mock_process:

                # RED: This should fail - method doesn't exist yet
                result = self.monitor.run_monitoring_cycle_with_actionable_count(target_actionable_count=10)

                # Should process 0 PRs
                self.assertEqual(result["actionable_processed"], 0)
                self.assertEqual(result["total_discovered"], 3)
                self.assertEqual(result["skipped_count"], 3)  # All skipped

                # Verify no processing was attempted
                self.assertEqual(mock_process.call_count, 0)

    def test_actionable_counter_should_track_actual_successful_processing(self):
        """RED: Actionable counter should only count PRs that successfully get processed"""

        mock_prs = [
            {"number": 1001, "state": "open", "isDraft": False, "headRefOid": "new001",
             "repository": "repo1", "headRefName": "feature1", "repositoryFullName": "org/repo1",
             "title": "Success PR", "updatedAt": "2025-09-28T21:00:00Z"},
            {"number": 1002, "state": "open", "isDraft": False, "headRefOid": "new002",
             "repository": "repo2", "headRefName": "feature2", "repositoryFullName": "org/repo2",
             "title": "Failure PR", "updatedAt": "2025-09-28T20:59:00Z"},
            {"number": 1003, "state": "open", "isDraft": False, "headRefOid": "new003",
             "repository": "repo3", "headRefName": "feature3", "repositoryFullName": "org/repo3",
             "title": "Success PR 2", "updatedAt": "2025-09-28T20:58:00Z"}
        ]

        def mock_process_side_effect(repo_name, pr_number, pr_data):
            # Simulate: First PR succeeds, second fails, third succeeds
            if pr_number == 1002:
                return False  # Processing failed
            return True  # Processing succeeded

        with patch.object(self.monitor, "discover_open_prs", return_value=mock_prs):
            with patch.object(self.monitor, "_process_pr_comment", side_effect=mock_process_side_effect) as mock_process:

                # RED: This should fail - method doesn't exist yet
                result = self.monitor.run_monitoring_cycle_with_actionable_count(target_actionable_count=10)

                # Should count only successful processing (2 out of 3 attempts)
                self.assertEqual(result["actionable_processed"], 2)
                self.assertEqual(result["total_discovered"], 3)
                self.assertEqual(result["processing_failures"], 1)

                # Verify all 3 were attempted
                self.assertEqual(mock_process.call_count, 3)

    def test_enhanced_run_monitoring_cycle_should_replace_old_max_prs_logic(self):
        """RED: Enhanced monitoring cycle should replace old max_prs with actionable counting"""

        mock_prs = [
            # Create 15 total PRs, but only 8 should be actionable
            *[
                {"number": 1000 + i, "state": "open", "isDraft": False, "headRefOid": f"new{i:03d}",
                 "repository": f"repo{i}", "headRefName": f"feature{i}", "repositoryFullName": f"org/repo{i}",
                 "title": f"Actionable PR {i}", "updatedAt": f"2025-09-28T{21-i//10}:{59-(i%10)*5}:00Z"}
                for i in range(8)  # 8 actionable PRs
            ],
            *[
                {"number": 2000 + i, "state": "closed", "isDraft": False, "headRefOid": f"any{i:03d}",
                 "repository": f"closed_repo{i}", "headRefName": f"closed{i}", "repositoryFullName": f"org/closed_repo{i}",
                 "title": f"Closed PR {i}", "updatedAt": f"2025-09-28T20:{50-i}:00Z"}
                for i in range(7)  # 7 closed PRs (not actionable)
            ]
        ]

        with patch.object(self.monitor, "discover_open_prs", return_value=mock_prs):
            with patch.object(self.monitor, "_process_pr_comment", return_value=True) as mock_process:

                # RED: This should fail - enhanced method doesn't exist
                # Should process exactly 5 actionable PRs, ignoring the 7 closed ones
                result = self.monitor.run_monitoring_cycle_with_actionable_count(target_actionable_count=5)

                self.assertEqual(result["actionable_processed"], 5)
                self.assertEqual(result["total_discovered"], 15)
                self.assertEqual(result["skipped_count"], 7)  # Closed PRs

                # Should have attempted processing exactly 5 times
                self.assertEqual(mock_process.call_count, 5)


if __name__ == "__main__":
    # RED Phase: Run tests to confirm they FAIL
    print("🔴 RED Phase: Running failing tests for actionable PR counting")
    print("Expected: ALL TESTS SHOULD FAIL (no implementation exists)")
    unittest.main(verbosity=2)
