#!/usr/bin/env python3
"""
RED Phase: Matrix-driven TDD tests for PR filtering and actionable counting

Test Matrix Coverage:
- PR Status × Commit Changes × Processing History → Action + Count
- Batch Processing Logic with Skip Exclusion
- Eligible PR Detection and Filtering
"""

import sys
import os
import unittest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add automation directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestPRFilteringMatrix(unittest.TestCase):
    """Matrix testing for PR filtering and actionable counting logic"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = JleechanorgPRMonitor()
        self.monitor.history_storage_path = self.temp_dir

    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    # Matrix 1: PR Status × Commit Changes × Processing History
    def test_matrix_open_pr_new_commit_never_processed_should_be_actionable(self):
        """RED: Open PR with new commit, never processed → Should be actionable"""
        pr_data = {
            'number': 1001,
            'title': 'Test PR',
            'state': 'open',
            'isDraft': False,
            'headRefName': 'feature-branch',
            'repository': 'test-repo',
            'repositoryFullName': 'org/test-repo',
            'headRefOid': 'abc123new'
        }

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertTrue(result)

    def test_matrix_open_pr_same_commit_already_processed_should_not_be_actionable(self):
        """RED: Open PR with same commit, already processed → Should not be actionable"""
        pr_data = {
            'number': 1001,
            'title': 'Test PR',
            'state': 'open',
            'isDraft': False,
            'headRefName': 'feature-branch',
            'repository': 'test-repo',
            'repositoryFullName': 'org/test-repo',
            'headRefOid': 'abc123same'
        }

        # Simulate previous processing
        self.monitor._record_pr_processing('test-repo', 'feature-branch', 1001, 'abc123same')

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertFalse(result)

    def test_matrix_open_pr_new_commit_old_commit_processed_should_be_actionable(self):
        """RED: Open PR with new commit, old commit processed → Should be actionable"""
        pr_data = {
            'number': 1001,
            'title': 'Test PR',
            'state': 'open',
            'isDraft': False,
            'headRefName': 'feature-branch',
            'repository': 'test-repo',
            'repositoryFullName': 'org/test-repo',
            'headRefOid': 'abc123new'
        }

        # Simulate processing of old commit
        self.monitor._record_pr_processing('test-repo', 'feature-branch', 1001, 'abc123old')

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertTrue(result)

    def test_matrix_closed_pr_any_commit_should_not_be_actionable(self):
        """RED: Closed PR with any commit → Should not be actionable"""
        pr_data = {
            'number': 1001,
            'title': 'Test PR',
            'state': 'closed',
            'isDraft': False,
            'headRefName': 'feature-branch',
            'repository': 'test-repo',
            'repositoryFullName': 'org/test-repo',
            'headRefOid': 'abc123new'
        }

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertFalse(result)

    def test_matrix_draft_pr_new_commit_never_processed_should_be_actionable(self):
        """RED: Draft PR with new commit, never processed → Should be actionable"""
        pr_data = {
            'number': 1001,
            'title': 'Test PR',
            'state': 'open',
            'isDraft': True,
            'headRefName': 'feature-branch',
            'repository': 'test-repo',
            'repositoryFullName': 'org/test-repo',
            'headRefOid': 'abc123new'
        }

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertTrue(result)

    def test_matrix_open_pr_no_commits_should_not_be_actionable(self):
        """RED: Open PR with no commits → Should not be actionable"""
        pr_data = {
            'number': 1001,
            'title': 'Test PR',
            'state': 'open',
            'isDraft': False,
            'headRefName': 'feature-branch',
            'repository': 'test-repo',
            'repositoryFullName': 'org/test-repo',
            'headRefOid': None  # No commits
        }

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertFalse(result)

    # Matrix 2: Batch Processing Logic with Skip Exclusion
    def test_matrix_batch_processing_15_eligible_target_10_should_process_10(self):
        """RED: 15 eligible PRs, target 10 → Should process exactly 10"""
        # Create 15 eligible PRs
        eligible_prs = []
        for i in range(15):
            pr = {
                'number': 1000 + i,
                'title': f'Test PR {i}',
                'state': 'open',
                'isDraft': False,
                'headRefName': f'feature-branch-{i}',
                'repository': 'test-repo',
                'repositoryFullName': 'org/test-repo',
                'headRefOid': f'abc123{i:03d}'
            }
            eligible_prs.append(pr)

        # RED: This will fail - no process_actionable_prs method exists
        processed_count = self.monitor.process_actionable_prs(eligible_prs, target_count=10)
        self.assertEqual(processed_count, 10)

    def test_matrix_batch_processing_5_eligible_target_10_should_process_5(self):
        """RED: 5 eligible PRs, target 10 → Should process all 5"""
        # Create 5 eligible PRs
        eligible_prs = []
        for i in range(5):
            pr = {
                'number': 1000 + i,
                'title': f'Test PR {i}',
                'state': 'open',
                'isDraft': False,
                'headRefName': f'feature-branch-{i}',
                'repository': 'test-repo',
                'repositoryFullName': 'org/test-repo',
                'headRefOid': f'abc123{i:03d}'
            }
            eligible_prs.append(pr)

        # RED: This will fail - no process_actionable_prs method exists
        processed_count = self.monitor.process_actionable_prs(eligible_prs, target_count=10)
        self.assertEqual(processed_count, 5)

    def test_matrix_batch_processing_0_eligible_target_10_should_process_0(self):
        """RED: 0 eligible PRs, target 10 → Should process 0"""
        eligible_prs = []

        # RED: This will fail - no process_actionable_prs method exists
        processed_count = self.monitor.process_actionable_prs(eligible_prs, target_count=10)
        self.assertEqual(processed_count, 0)

    def test_matrix_batch_processing_mixed_actionable_and_skipped_should_exclude_skipped_from_count(self):
        """RED: Mixed actionable and skipped PRs → Should exclude skipped from count"""
        # Create mixed PRs - some actionable, some already processed
        all_prs = []

        # 5 actionable PRs
        for i in range(5):
            pr = {
                'number': 1000 + i,
                'title': f'Actionable PR {i}',
                'state': 'open',
                'isDraft': False,
                'headRefName': f'feature-branch-{i}',
                'repository': 'test-repo',
                'repositoryFullName': 'org/test-repo',
                'headRefOid': f'abc123new{i:03d}'
            }
            all_prs.append(pr)

        # 3 already processed PRs (should be skipped)
        for i in range(3):
            pr = {
                'number': 2000 + i,
                'title': f'Processed PR {i}',
                'state': 'open',
                'isDraft': False,
                'headRefName': f'processed-branch-{i}',
                'repository': 'test-repo',
                'repositoryFullName': 'org/test-repo',
                'headRefOid': f'abc123old{i:03d}'
            }
            # Pre-record as processed
            self.monitor._record_pr_processing('test-repo', f'processed-branch-{i}', 2000 + i, f'abc123old{i:03d}')
            all_prs.append(pr)

        # RED: This will fail - no filter_and_process_prs method exists
        processed_count = self.monitor.filter_and_process_prs(all_prs, target_actionable_count=10)
        self.assertEqual(processed_count, 5)  # Only actionable PRs counted

    # Matrix 3: Eligible PR Detection
    def test_matrix_filter_eligible_prs_from_mixed_list(self):
        """RED: Filter eligible PRs from mixed list → Should return only actionable ones"""
        mixed_prs = [
            # Actionable: Open, new commit
            {
                'number': 1001, 'state': 'open', 'isDraft': False,
                'headRefOid': 'new123', 'repository': 'repo1',
                'headRefName': 'branch1', 'repositoryFullName': 'org/repo1'
            },
            # Not actionable: Closed
            {
                'number': 1002, 'state': 'closed', 'isDraft': False,
                'headRefOid': 'new456', 'repository': 'repo2',
                'headRefName': 'branch2', 'repositoryFullName': 'org/repo2'
            },
            # Not actionable: Already processed
            {
                'number': 1003, 'state': 'open', 'isDraft': False,
                'headRefOid': 'old789', 'repository': 'repo3',
                'headRefName': 'branch3', 'repositoryFullName': 'org/repo3'
            },
            # Actionable: Draft but new commit
            {
                'number': 1004, 'state': 'open', 'isDraft': True,
                'headRefOid': 'new999', 'repository': 'repo4',
                'headRefName': 'branch4', 'repositoryFullName': 'org/repo4'
            }
        ]

        # Mark one as already processed
        self.monitor._record_pr_processing('repo3', 'branch3', 1003, 'old789')

        # RED: This will fail - no filter_eligible_prs method exists
        eligible_prs = self.monitor.filter_eligible_prs(mixed_prs)

        # Should return only the 2 actionable PRs
        self.assertEqual(len(eligible_prs), 2)
        actionable_numbers = [pr['number'] for pr in eligible_prs]
        self.assertIn(1001, actionable_numbers)
        self.assertIn(1004, actionable_numbers)
        self.assertNotIn(1002, actionable_numbers)  # Closed
        self.assertNotIn(1003, actionable_numbers)  # Already processed

    def test_matrix_find_5_eligible_prs_from_live_data(self):
        """RED: Find 5 eligible PRs from live GitHub data → Should return 5 actionable PRs"""
        # Mock discover_open_prs to return test data instead of calling GitHub API
        mock_prs = [
            {"number": 1, "state": "open", "isDraft": False, "headRefOid": "abc123", "repository": "repo1", "headRefName": "feature1"},
            {"number": 2, "state": "closed", "isDraft": False, "headRefOid": "def456", "repository": "repo2", "headRefName": "feature2"},
            {"number": 3, "state": "open", "isDraft": False, "headRefOid": "ghi789", "repository": "repo3", "headRefName": "feature3"},
            {"number": 4, "state": "open", "isDraft": True, "headRefOid": "jkl012", "repository": "repo4", "headRefName": "feature4"},
            {"number": 5, "state": "open", "isDraft": False, "headRefOid": "mno345", "repository": "repo5", "headRefName": "feature5"},
            {"number": 6, "state": "open", "isDraft": False, "headRefOid": "pqr678", "repository": "repo6", "headRefName": "feature6"},
            {"number": 7, "state": "open", "isDraft": False, "headRefOid": "stu901", "repository": "repo7", "headRefName": "feature7"}
        ]

        with patch.object(self.monitor, 'discover_open_prs', return_value=mock_prs):
            eligible_prs = self.monitor.find_eligible_prs(limit=5)
            self.assertEqual(len(eligible_prs), 5)
            # All returned PRs should be actionable
            for pr in eligible_prs:
                self.assertTrue(self.monitor.is_pr_actionable(pr))


if __name__ == '__main__':
    # RED Phase: Run tests to confirm they FAIL
    print("🔴 RED Phase: Running failing tests for PR filtering matrix")
    print("Expected: ALL TESTS SHOULD FAIL (no implementation exists)")
    unittest.main(verbosity=2)
