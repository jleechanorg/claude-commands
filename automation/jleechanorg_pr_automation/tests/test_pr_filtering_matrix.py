#!/usr/bin/env python3
"""
RED Phase: Matrix-driven TDD tests for PR filtering and actionable counting

Test Matrix Coverage:
- PR Status × Commit Changes × Processing History → Action + Count
- Batch Processing Logic with Skip Exclusion
- Eligible PR Detection and Filtering
"""

import tempfile
import unittest
from unittest.mock import Mock, patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


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
            "number": 1001,
            "title": "Test PR",
            "state": "open",
            "isDraft": False,
            "headRefName": "feature-branch",
            "repository": "test-repo",
            "repositoryFullName": "org/test-repo",
            "headRefOid": "abc123new"
        }

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertTrue(result)

    def test_matrix_open_pr_same_commit_already_processed_should_not_be_actionable(self):
        """RED: Open PR with same commit, already processed → Should not be actionable"""
        pr_data = {
            "number": 1001,
            "title": "Test PR",
            "state": "open",
            "isDraft": False,
            "headRefName": "feature-branch",
            "repository": "test-repo",
            "repositoryFullName": "org/test-repo",
            "headRefOid": "abc123same"
        }

        # Simulate previous processing
        self.monitor._record_pr_processing("test-repo", "feature-branch", 1001, "abc123same")

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertFalse(result)

    def test_matrix_open_pr_new_commit_old_commit_processed_should_be_actionable(self):
        """RED: Open PR with new commit, old commit processed → Should be actionable"""
        pr_data = {
            "number": 1001,
            "title": "Test PR",
            "state": "open",
            "isDraft": False,
            "headRefName": "feature-branch",
            "repository": "test-repo",
            "repositoryFullName": "org/test-repo",
            "headRefOid": "abc123new"
        }

        # Simulate processing of old commit
        self.monitor._record_pr_processing("test-repo", "feature-branch", 1001, "abc123old")

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertTrue(result)

    def test_matrix_closed_pr_any_commit_should_not_be_actionable(self):
        """RED: Closed PR with any commit → Should not be actionable"""
        pr_data = {
            "number": 1001,
            "title": "Test PR",
            "state": "closed",
            "isDraft": False,
            "headRefName": "feature-branch",
            "repository": "test-repo",
            "repositoryFullName": "org/test-repo",
            "headRefOid": "abc123new"
        }

        # RED: This will fail - no is_pr_actionable method exists
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertFalse(result)

    def test_matrix_draft_pr_new_commit_never_processed_should_be_skipped(self):
        """Draft PRs are skipped even with new commits"""
        pr_data = {
            "number": 1001,
            "title": "Test PR",
            "state": "open",
            "isDraft": True,
            "headRefName": "feature-branch",
            "repository": "test-repo",
            "repositoryFullName": "org/test-repo",
            "headRefOid": "abc123new"
        }

        result = self.monitor.is_pr_actionable(pr_data)
        self.assertFalse(result)

    def test_matrix_open_pr_no_commits_should_not_be_actionable(self):
        """RED: Open PR with no commits → Should not be actionable"""
        pr_data = {
            "number": 1001,
            "title": "Test PR",
            "state": "open",
            "isDraft": False,
            "headRefName": "feature-branch",
            "repository": "test-repo",
            "repositoryFullName": "org/test-repo",
            "headRefOid": None  # No commits
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
                "number": 1000 + i,
                "title": f"Test PR {i}",
                "state": "open",
                "isDraft": False,
                "headRefName": f"feature-branch-{i}",
                "repository": "test-repo",
                "repositoryFullName": "org/test-repo",
                "headRefOid": f"abc123{i:03d}"
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
                "number": 1000 + i,
                "title": f"Test PR {i}",
                "state": "open",
                "isDraft": False,
                "headRefName": f"feature-branch-{i}",
                "repository": "test-repo",
                "repositoryFullName": "org/test-repo",
                "headRefOid": f"abc123{i:03d}"
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
                "number": 1000 + i,
                "title": f"Actionable PR {i}",
                "state": "open",
                "isDraft": False,
                "headRefName": f"feature-branch-{i}",
                "repository": "test-repo",
                "repositoryFullName": "org/test-repo",
                "headRefOid": f"abc123new{i:03d}"
            }
            all_prs.append(pr)

        # 3 already processed PRs (should be skipped)
        for i in range(3):
            pr = {
                "number": 2000 + i,
                "title": f"Processed PR {i}",
                "state": "open",
                "isDraft": False,
                "headRefName": f"processed-branch-{i}",
                "repository": "test-repo",
                "repositoryFullName": "org/test-repo",
                "headRefOid": f"abc123old{i:03d}"
            }
            # Pre-record as processed
            self.monitor._record_pr_processing("test-repo", f"processed-branch-{i}", 2000 + i, f"abc123old{i:03d}")
            all_prs.append(pr)

        # RED: This will fail - no filter_and_process_prs method exists
        processed_count = self.monitor.filter_and_process_prs(all_prs, target_actionable_count=10)
        self.assertEqual(processed_count, 5)  # Only actionable PRs counted

    # Matrix 3: Eligible PR Detection
    def test_matrix_filter_eligible_prs_from_mixed_list(self):
        """Filter eligible PRs from mixed list skips drafts"""
        mixed_prs = [
            # Actionable: Open, new commit
            {
                "number": 1001, "state": "open", "isDraft": False,
                "headRefOid": "new123", "repository": "repo1",
                "headRefName": "branch1", "repositoryFullName": "org/repo1"
            },
            # Not actionable: Closed
            {
                "number": 1002, "state": "closed", "isDraft": False,
                "headRefOid": "new456", "repository": "repo2",
                "headRefName": "branch2", "repositoryFullName": "org/repo2"
            },
            # Not actionable: Already processed
            {
                "number": 1003, "state": "open", "isDraft": False,
                "headRefOid": "old789", "repository": "repo3",
                "headRefName": "branch3", "repositoryFullName": "org/repo3"
            },
            # Skipped: Draft even with new commit
            {
                "number": 1004, "state": "open", "isDraft": True,
                "headRefOid": "new999", "repository": "repo4",
                "headRefName": "branch4", "repositoryFullName": "org/repo4"
            }
        ]

        # Mark one as already processed
        self.monitor._record_pr_processing("repo3", "branch3", 1003, "old789")

        eligible_prs = self.monitor.filter_eligible_prs(mixed_prs)

        # Should return only the 1 actionable PR (draft skipped)
        self.assertEqual(len(eligible_prs), 1)
        actionable_numbers = [pr["number"] for pr in eligible_prs]
        self.assertIn(1001, actionable_numbers)
        self.assertNotIn(1002, actionable_numbers)  # Closed
        self.assertNotIn(1003, actionable_numbers)  # Already processed
        self.assertNotIn(1004, actionable_numbers)  # Draft skipped

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

        with patch.object(self.monitor, "discover_open_prs", return_value=mock_prs):
            eligible_prs = self.monitor.find_eligible_prs(limit=5)
            self.assertEqual(len(eligible_prs), 5)
            # All returned PRs should be actionable
            for pr in eligible_prs:
                self.assertTrue(self.monitor.is_pr_actionable(pr))

    # Matrix 5: Comment Posting Return Values (Bug Fix Tests)
    def test_comment_posting_returns_posted_on_success(self):
        """GREEN: Comment posting should return 'posted' when successful"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_should_skip_pr") as mock_skip, \
             patch.object(self.monitor, "_has_codex_comment_for_commit") as mock_has_comment, \
             patch.object(self.monitor, "_build_codex_comment_body_simple") as mock_build_body, \
             patch.object(self.monitor, "_record_processed_pr") as mock_record, \
             patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout") as mock_subprocess:

            # Setup: PR not skipped, no existing comment, successful command
            mock_state.return_value = ("sha123", [])
            mock_skip.return_value = False
            mock_has_comment.return_value = False
            mock_build_body.return_value = "Test comment body"
            mock_subprocess.return_value = Mock(returncode=0, stdout="success", stderr="")

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }

            result = self.monitor.post_codex_instruction_simple("org/repo", 123, pr_data)
            self.assertEqual(result, "posted")
            mock_record.assert_called_once()

    def test_comment_posting_returns_skipped_when_already_processed(self):
        """GREEN: Comment posting should return 'skipped' when PR already processed"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_should_skip_pr") as mock_skip:

            # Setup: PR should be skipped
            mock_state.return_value = ("sha123", [])
            mock_skip.return_value = True

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }

            result = self.monitor.post_codex_instruction_simple("org/repo", 123, pr_data)
            self.assertEqual(result, "skipped")

    def test_comment_posting_returns_skipped_when_comment_exists(self):
        """GREEN: Comment posting should return 'skipped' when comment already exists for commit"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_should_skip_pr") as mock_skip, \
             patch.object(self.monitor, "_has_codex_comment_for_commit") as mock_has_comment:

            # Setup: PR not skipped but has existing comment
            mock_state.return_value = ("sha123", [])
            mock_skip.return_value = False
            mock_has_comment.return_value = True

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }

            result = self.monitor.post_codex_instruction_simple("org/repo", 123, pr_data)
            self.assertEqual(result, "skipped")

    def test_comment_posting_returns_failed_on_subprocess_error(self):
        """GREEN: Comment posting should return 'failed' when subprocess fails"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_should_skip_pr") as mock_skip, \
             patch.object(self.monitor, "_has_codex_comment_for_commit") as mock_has_comment, \
             patch.object(self.monitor, "_build_codex_comment_body_simple") as mock_build_body, \
             patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout") as mock_subprocess:

            # Setup: PR not skipped, no existing comment, but command fails
            mock_state.return_value = ("sha123", [])
            mock_skip.return_value = False
            mock_has_comment.return_value = False
            mock_build_body.return_value = "Test comment body"
            mock_subprocess.side_effect = Exception("Command failed")

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }

            result = self.monitor.post_codex_instruction_simple("org/repo", 123, pr_data)
            self.assertEqual(result, "failed")

    def test_comment_posting_skips_when_head_commit_from_codex(self):
        """GREEN: post_codex_instruction_simple should skip when head commit is Codex-attributed"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_get_head_commit_details") as mock_head_details, \
             patch.object(self.monitor, "_is_head_commit_from_codex") as mock_is_codex, \
             patch.object(self.monitor, "_should_skip_pr") as mock_should_skip, \
             patch.object(self.monitor, "_has_codex_comment_for_commit") as mock_has_comment, \
             patch.object(self.monitor, "_record_processed_pr") as mock_record_processed, \
             patch.object(self.monitor, "_build_codex_comment_body_simple") as mock_build_body, \
             patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout") as mock_subprocess:

            mock_state.return_value = ("sha123", [])
            mock_head_details.return_value = {"sha": "sha123"}
            mock_is_codex.return_value = True

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature",
            }

            result = self.monitor.post_codex_instruction_simple("org/repo", 456, pr_data)

            self.assertEqual(result, "skipped")
            mock_is_codex.assert_called_once_with({"sha": "sha123"})
            mock_should_skip.assert_not_called()
            mock_has_comment.assert_not_called()
            mock_build_body.assert_not_called()
            mock_subprocess.assert_not_called()
            mock_record_processed.assert_called_once_with("repo", "feature", 456, "sha123")

    def test_process_pr_comment_only_returns_true_for_posted(self):
        """GREEN: _process_pr_comment should only return True when comment actually posted"""
        with patch.object(self.monitor, "post_codex_instruction_simple") as mock_post:

            pr_data = {"repositoryFullName": "org/repo"}

            # Test: Returns True only for 'posted'
            mock_post.return_value = "posted"
            self.assertTrue(self.monitor._process_pr_comment("repo", 123, pr_data))

            # Test: Returns False for 'skipped'
            mock_post.return_value = "skipped"
            self.assertFalse(self.monitor._process_pr_comment("repo", 123, pr_data))

            # Test: Returns False for 'failed'
            mock_post.return_value = "failed"
            self.assertFalse(self.monitor._process_pr_comment("repo", 123, pr_data))

    def test_comment_template_contains_all_ai_assistants(self):
        """GREEN: Comment template should mention all 4 AI assistants"""
        pr_data = {
            "title": "Test PR",
            "author": {"login": "testuser"},
            "headRefName": "test-branch"
        }

        comment_body = self.monitor._build_codex_comment_body_simple(
            "test/repo", 123, pr_data, "abc12345"
        )

        # Verify all 4 AI assistant mentions are present
        self.assertIn("@codex", comment_body, "Comment should mention @codex")
        self.assertIn("@coderabbitai", comment_body, "Comment should mention @coderabbitai")
        self.assertIn("@copilot", comment_body, "Comment should mention @copilot")
        self.assertIn("@cursor", comment_body, "Comment should mention @cursor")

        # Verify they appear at the beginning of the comment
        first_line = comment_body.split("\n")[0]
        self.assertIn("@codex", first_line, "@codex should be in first line")
        self.assertIn("@coderabbitai", first_line, "@coderabbitai should be in first line")
        self.assertIn("@copilot", first_line, "@copilot should be in first line")
        self.assertIn("@cursor", first_line, "@cursor should be in first line")

        # Verify automation marker instructions are documented
        self.assertIn(
            self.monitor.CODEX_COMMIT_MESSAGE_MARKER,
            comment_body,
            "Comment should instruct Codex to include the commit message marker",
        )
        self.assertIn(
            "<!-- codex-automation-commit:",
            comment_body,
            "Comment should remind Codex about the hidden commit marker",
        )


if __name__ == "__main__":
    # RED Phase: Run tests to confirm they FAIL
    print("🔴 RED Phase: Running failing tests for PR filtering matrix")
    print("Expected: ALL TESTS SHOULD FAIL (no implementation exists)")
    unittest.main(verbosity=2)
