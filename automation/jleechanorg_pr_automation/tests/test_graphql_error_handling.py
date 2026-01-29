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
        self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")

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

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_unresolved_returns_true(self, mock_exec) -> None:
        """Should return True when unresolved review threads exist across pages"""
        page_one = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [{"id": "1", "isResolved": True}],
                            "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
                        }
                    }
                }
            }
        }
        page_two = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [{"id": "2", "isResolved": False}],
                            "pageInfo": {"hasNextPage": False, "endCursor": "cursor-2"},
                        }
                    }
                }
            }
        }
        mock_exec.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(page_one)),
            MagicMock(returncode=0, stdout=json.dumps(page_two)),
        ]

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertTrue(result, "Should return True when any thread is unresolved")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_all_resolved_returns_false(self, mock_exec) -> None:
        """Should return False when all review threads are resolved"""
        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [{"id": "1", "isResolved": True}],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }
        }
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps(response))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertFalse(result, "Should return False when all threads resolved")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_empty_returns_false(self, mock_exec) -> None:
        """Should return False when no review threads exist"""
        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }
        }
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps(response))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertFalse(result, "Should return False when no threads exist")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_graphql_failure_returns_none(self, mock_exec) -> None:
        """Should return None when GraphQL query fails for review threads"""
        mock_exec.return_value = MagicMock(returncode=1, stderr="boom", stdout="")

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None when GraphQL call fails")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_malformed_json_returns_none(self, mock_exec) -> None:
        """Should return None when review threads JSON is malformed"""
        mock_exec.return_value = MagicMock(
            returncode=0, stdout='{"data": {"repository": [}'
        )

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None on malformed review thread JSON")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_missing_data_returns_none(self, mock_exec) -> None:
        """Should return None when review threads payload is missing nodes"""
        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": None
                    }
                }
            }
        }
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps(response))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None when reviewThreads missing")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_missing_repository_returns_none(self, mock_exec) -> None:
        """Should return None when review threads response lacks repository data"""
        response = {"data": {}}
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps(response))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None when repository data missing")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_errors_field_returns_none(self, mock_exec) -> None:
        """Should return None when GraphQL response includes errors"""
        response = {
            "errors": [{"message": "Rate limit exceeded"}],
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
        }
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps(response))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None when GraphQL errors are present")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_errors_only_returns_none(self, mock_exec) -> None:
        """Should return None when GraphQL response includes only errors"""
        response = {"errors": [{"message": "Bad credentials"}]}
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps(response))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None when response has only errors")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_non_dict_response_returns_none(self, mock_exec) -> None:
        """Should return None when GraphQL response is not a JSON object"""
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps([]))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None when response is not a dict")

    def test_review_threads_invalid_repo_format_returns_none(self) -> None:
        """Should return None for invalid repository format in review threads"""
        result = self.monitor._has_unresolved_review_threads("invalid-no-slash", 123)

        self.assertIsNone(result, "Should reject repo without slash separator")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_missing_end_cursor_returns_none(self, mock_exec) -> None:
        """Should return None when pagination is requested without an endCursor"""
        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [{"id": "1", "isResolved": True}],
                            "pageInfo": {"hasNextPage": True, "endCursor": None},
                        }
                    }
                }
            }
        }
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps(response))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None when endCursor is missing")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_nodes_not_list_returns_none(self, mock_exec) -> None:
        """Should return None when reviewThreads.nodes is not a list"""
        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": {"id": "1", "isResolved": True},
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }
        }
        mock_exec.return_value = MagicMock(returncode=0, stdout=json.dumps(response))

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertIsNone(result, "Should return None when nodes is not a list")

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_review_threads_pagination_handles_large_counts(self, mock_exec) -> None:
        """Should handle pagination when reviewThreads exceed 100 nodes"""
        page_one_nodes = [{"id": str(i), "isResolved": True} for i in range(100)]
        page_one = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": page_one_nodes,
                            "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
                        }
                    }
                }
            }
        }
        page_two = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [{"id": "101", "isResolved": False}],
                            "pageInfo": {"hasNextPage": False, "endCursor": "cursor-2"},
                        }
                    }
                }
            }
        }
        mock_exec.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(page_one)),
            MagicMock(returncode=0, stdout=json.dumps(page_two)),
        ]

        result = self.monitor._has_unresolved_review_threads("org/repo", 123)

        self.assertTrue(result, "Should return True when unresolved threads exist after pagination")

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

    @patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout")
    def test_checks_issue_comments_when_no_review_threads(self, mock_exec) -> None:
        """Should check issue comments even when GraphQL returns False (no unresolved review threads)"""
        # GraphQL returns False (no unresolved review threads)
        graphql_response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [{"id": "1", "isResolved": True}],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }
        }

        # REST API returns actionable issue comment
        issue_comments_response = [
            {
                "id": 123,
                "user": {"login": "reviewer"},
                "body": "Please fix this issue in the code",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]

        # Mock responses: GraphQL (resolved threads), then issue comments, then empty reviews/inline
        mock_exec.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(graphql_response)),  # GraphQL
            MagicMock(returncode=0, stdout=json.dumps(issue_comments_response)),  # Issue comments
            MagicMock(returncode=0, stdout="[]"),  # Review comments
            MagicMock(returncode=0, stdout="[]"),  # Inline comments
        ]

        result = self.monitor._has_unaddressed_comments("org/repo", 123)

        self.assertTrue(result, "Should return True when issue comments exist even if no unresolved review threads")


if __name__ == "__main__":
    unittest.main()
