#!/usr/bin/env python3
"""Tests for GraphQL API error handling in head commit detection."""

import json
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestGraphQLErrorHandling(unittest.TestCase):
    """Validate robust error handling for GraphQL API failures."""

    def setUp(self) -> None:
        self.monitor = JleechanorgPRMonitor()

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_handles_api_timeout(self, mock_exec) -> None:
        """Should return None when GraphQL API times out"""
        mock_exec.side_effect = subprocess.TimeoutExpired(["gh"], 30)

        result = self.monitor._get_head_commit_details("org/repo", 123)

        self.assertIsNone(result, "Should return None on API timeout")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_handles_malformed_json(self, mock_exec) -> None:
        """Should return None when GraphQL returns invalid JSON"""
        mock_exec.return_value = MagicMock(
            stdout='{"invalid": json, missing quotes}'
        )

        result = self.monitor._get_head_commit_details("org/repo", 123)

        self.assertIsNone(result, "Should return None on malformed JSON")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_handles_missing_data_field(self, mock_exec) -> None:
        """Should handle missing 'data' field in GraphQL response"""
        mock_exec.return_value = MagicMock(
            stdout='{"errors": [{"message": "Field error"}]}'
        )

        result = self.monitor._get_head_commit_details("org/repo", 123)

        self.assertIsNone(result, "Should return None when data field missing")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_handles_missing_repository_field(self, mock_exec) -> None:
        """Should handle missing 'repository' field gracefully"""
        mock_exec.return_value = MagicMock(
            stdout='{"data": {}}'
        )

        result = self.monitor._get_head_commit_details("org/repo", 123)

        self.assertIsNone(result, "Should return None when repository field missing")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_handles_missing_commits(self, mock_exec) -> None:
        """Should handle missing commits array gracefully"""
        response = {
            "data": {
                "repository": {
                    "pullRequest": {}
                }
            }
        }
        mock_exec.return_value = MagicMock(stdout=json.dumps(response))

        result = self.monitor._get_head_commit_details("org/repo", 123)

        self.assertIsNone(result, "Should return None when commits missing")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_handles_empty_commits_array(self, mock_exec) -> None:
        """Should handle empty commits array gracefully"""
        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "commits": {"nodes": []}
                    }
                }
            }
        }
        mock_exec.return_value = MagicMock(stdout=json.dumps(response))

        result = self.monitor._get_head_commit_details("org/repo", 123)

        self.assertIsNone(result, "Should return None when commits array empty")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_handles_called_process_error(self, mock_exec) -> None:
        """Should handle subprocess CalledProcessError gracefully"""
        mock_exec.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gh", "api"],
            stderr="API rate limit exceeded"
        )

        result = self.monitor._get_head_commit_details("org/repo", 123)

        self.assertIsNone(result, "Should return None on CalledProcessError")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_handles_generic_exception(self, mock_exec) -> None:
        """Should handle unexpected exceptions gracefully"""
        mock_exec.side_effect = RuntimeError("Unexpected error")

        result = self.monitor._get_head_commit_details("org/repo", 123)

        self.assertIsNone(result, "Should return None on unexpected exception")

    def test_validates_invalid_repo_format(self) -> None:
        """Should return None for invalid repository format"""
        result = self.monitor._get_head_commit_details("invalid-no-slash", 123)

        self.assertIsNone(result, "Should reject repo without slash separator")

    def test_validates_empty_repo_name(self) -> None:
        """Should return None for empty repository parts"""
        result = self.monitor._get_head_commit_details("/repo", 123)

        self.assertIsNone(result, "Should reject empty owner")

    def test_validates_invalid_github_owner_name(self) -> None:
        """Should return None for invalid GitHub owner/repo names"""
        # GitHub names cannot start with hyphen
        result = self.monitor._get_head_commit_details("-invalid/repo", 123)

        self.assertIsNone(result, "Should reject owner starting with hyphen")

    def test_validates_invalid_pr_number_string(self) -> None:
        """Should return None for non-integer PR number"""
        result = self.monitor._get_head_commit_details("org/repo", "not-a-number")

        self.assertIsNone(result, "Should reject string PR number")

    def test_validates_negative_pr_number(self) -> None:
        """Should return None for negative PR number"""
        result = self.monitor._get_head_commit_details("org/repo", -1)

        self.assertIsNone(result, "Should reject negative PR number")

    def test_validates_zero_pr_number(self) -> None:
        """Should return None for zero PR number"""
        result = self.monitor._get_head_commit_details("org/repo", 0)

        self.assertIsNone(result, "Should reject zero PR number")


if __name__ == "__main__":
    unittest.main()
