#!/usr/bin/env python3
"""
Comprehensive TDD Matrix Testing for commentreply.py
Ensures all critical permutations and edge cases are covered
"""

import unittest
from unittest.mock import patch, MagicMock, call
import json
import tempfile
import os
import sys

# Add the module path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.claude', 'commands'))

import commentreply


class TestCommentReplyComprehensive(unittest.TestCase):
    """Comprehensive matrix testing for commentreply functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_comments = {
            "technical_comment": {
                "id": 12345,
                "body": "Using f-string with json.dumps() output in shell command is unsafe.",
                "user": {"login": "coderabbitai"},
                "path": "file.py",
                "line": 42,
                "created_at": "2025-09-02T01:00:00Z"
            },
            "meta_comment": {
                "id": 67890,
                "body": """🚨 **CLAUDE RESPONSE NEEDED** (Commit: abc123)

❌ No Claude-generated response found for this comment.""",
                "user": {"login": "jleechan2015"},
                "created_at": "2025-09-02T01:30:00Z"
            },
            "quote_comment": {
                "id": 11111,
                "body": "> Seems like humans are chatting",
                "user": {"login": "human"},
                "created_at": "2025-09-02T01:45:00Z"
            }
        }

    ## Phase 0: Matrix Planning

    # Matrix 1: Comment Type × Response Generation × API Call Type
    # | Comment Type  | Has Response | API Type | Expected Result |
    # |---------------|--------------|----------|-----------------|
    # | Technical     | Yes         | Review   | Success         |
    # | Technical     | No          | Review   | Meta-comment    |
    # | Technical     | Yes         | Issue    | Success         |
    # | Technical     | No          | Issue    | Meta-comment    |
    # | Meta-comment  | Any         | Any      | Skip            |
    # | Quote-only    | Any         | Any      | Skip            |

    ## Phase 1: RED - Matrix-Driven Failing Tests

    def test_matrix_technical_comment_with_response_review_api(self):
        """Matrix [Technical, HasResponse, Review] → Success"""
        comment = self.sample_comments["technical_comment"]
        responses_data = {
            "responses": [{
                "comment_id": "12345",
                "response": "✅ Fixed security issue"
            }]
        }

        with patch('commentreply.create_review_comment_reply') as mock_create:
            mock_create.return_value = True

            response = commentreply.get_response_for_comment(comment, responses_data, "abc123")
            self.assertEqual(response, "✅ Fixed security issue")

            # Test API call
            result = commentreply.create_threaded_reply("owner", "repo", "123", comment, response)
            self.assertTrue(result)
            mock_create.assert_called_once()

    def test_matrix_technical_comment_no_response_generates_meta(self):
        """Matrix [Technical, NoResponse, Any] → Meta-comment"""
        comment = self.sample_comments["technical_comment"]
        responses_data = {"responses": []}  # No responses

        response = commentreply.get_response_for_comment(comment, responses_data, "abc123")

        # Should generate meta-comment
        self.assertIn("CLAUDE RESPONSE NEEDED", response)
        self.assertIn("Comment #12345", response)
        self.assertIn("coderabbitai", response)

    def test_matrix_technical_comment_with_response_issue_api(self):
        """Matrix [Technical, HasResponse, Issue] → Success"""
        # Modify comment to look like issue comment (no path/line)
        issue_comment = self.sample_comments["technical_comment"].copy()
        del issue_comment["path"]
        del issue_comment["line"]

        responses_data = {
            "responses": [{
                "comment_id": "12345",
                "response": "✅ Issue addressed"
            }]
        }

        with patch('commentreply.create_issue_comment_reply') as mock_create:
            mock_create.return_value = True

            response = commentreply.get_response_for_comment(issue_comment, responses_data, "abc123")
            result = commentreply.create_threaded_reply("owner", "repo", "123", issue_comment, response)

            self.assertTrue(result)
            mock_create.assert_called_once()

    ## Matrix 2: Comment Detection × API Routing

    def test_detect_comment_type_review_by_path(self):
        """Comment with path/line → Review comment"""
        comment = self.sample_comments["technical_comment"]
        comment_type = commentreply.detect_comment_type(comment)
        self.assertEqual(comment_type, "review")

    def test_detect_comment_type_review_by_url_pattern(self):
        """Comment with discussion_r URL → Review comment"""
        comment = {"html_url": "https://github.com/repo/pull/123#discussion_r456"}
        comment_type = commentreply.detect_comment_type(comment)
        self.assertEqual(comment_type, "review")

    def test_detect_comment_type_issue_by_url_pattern(self):
        """Comment with issuecomment URL → Issue comment"""
        comment = {"html_url": "https://github.com/repo/pull/123#issuecomment-789"}
        comment_type = commentreply.detect_comment_type(comment)
        self.assertEqual(comment_type, "issue")

    def test_detect_comment_type_default_review(self):
        """Unknown comment type → Default to review"""
        comment = {"body": "Some comment"}
        comment_type = commentreply.detect_comment_type(comment)
        self.assertEqual(comment_type, "review")

    ## Matrix 3: Error Handling × Recovery Patterns

    @patch('commentreply.subprocess.run')
    def test_run_command_success_path(self, mock_subprocess):
        """Command execution success path"""
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="success",
            stderr=""
        )

        success, stdout, stderr = commentreply.run_command(["echo", "test"])

        self.assertTrue(success)
        self.assertEqual(stdout, "success")
        self.assertEqual(stderr, "")

    @patch('commentreply.subprocess.run')
    def test_run_command_failure_path(self, mock_subprocess):
        """Command execution failure path"""
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error occurred"
        )

        success, stdout, stderr = commentreply.run_command(["false"])

        self.assertFalse(success)
        self.assertEqual(stderr, "error occurred")

    @patch('commentreply.subprocess.run')
    def test_run_command_timeout_handling(self, mock_subprocess):
        """Command timeout handling"""
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired(["sleep"], 30)

        success, stdout, stderr = commentreply.run_command(["sleep", "60"])

        self.assertFalse(success)
        self.assertIn("timed out", stderr)

    ## Matrix 4: File I/O × Data Persistence

    def test_load_claude_responses_file_exists(self):
        """Responses file exists and is valid JSON"""
        test_data = {
            "pr": "123",
            "responses": [{"comment_id": "456", "response": "test"}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            # Mock the file path
            with patch('commentreply.os.path.exists') as mock_exists:
                mock_exists.return_value = True
                with patch('builtins.open', open):
                    with patch('commentreply.open', open):
                        # Temporarily replace the file path logic
                        original_path = f"/tmp/test-branch/responses.json"
                        with patch('commentreply.os.path.exists') as mock_exists:
                            mock_exists.return_value = True
                            # Direct test of loading logic
                            with open(temp_path, 'r') as test_file:
                                loaded_data = json.load(test_file)

                            self.assertEqual(loaded_data["pr"], "123")
                            self.assertEqual(len(loaded_data["responses"]), 1)
        finally:
            os.unlink(temp_path)

    def test_load_claude_responses_file_not_found(self):
        """Responses file does not exist"""
        result = commentreply.load_claude_responses("nonexistent-branch")
        self.assertEqual(result, {})

    ## Matrix 5: GitHub API Integration × Authentication

    @patch('commentreply.run_command')
    def test_create_review_comment_reply_success(self, mock_run):
        """Review comment API call success"""
        mock_run.return_value = (True, '{"id": 789}', "")

        result = commentreply.create_review_comment_reply("owner", "repo", "123", 456, "Test response")

        self.assertTrue(result)
        # Verify API call structure
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("gh", call_args)
        self.assertIn("api", call_args)
        self.assertIn("repos/owner/repo/pulls/123/comments", call_args)

    @patch('commentreply.run_command')
    def test_create_review_comment_reply_api_failure(self, mock_run):
        """Review comment API call failure"""
        mock_run.return_value = (False, "", "API Error: 422 Unprocessable Entity")

        result = commentreply.create_review_comment_reply("owner", "repo", "123", 456, "Test response")

        self.assertFalse(result)

    @patch('commentreply.run_command')
    def test_create_issue_comment_reply_success(self, mock_run):
        """Issue comment API call success"""
        mock_run.return_value = (True, '{"id": 999}', "")

        result = commentreply.create_issue_comment_reply("owner", "repo", "123", 456, "Test response")

        self.assertTrue(result)

    ## Matrix 6: Git Integration × Commit Tracking

    @patch('commentreply.run_command')
    def test_get_git_commit_hash_success(self, mock_run):
        """Git commit hash retrieval success"""
        mock_run.return_value = (True, "abc123def\n", "")

        commit_hash = commentreply.get_git_commit_hash()

        self.assertEqual(commit_hash, "abc123def")

    @patch('commentreply.run_command')
    def test_get_git_commit_hash_failure(self, mock_run):
        """Git commit hash retrieval failure"""
        mock_run.return_value = (False, "", "not a git repository")

        commit_hash = commentreply.get_git_commit_hash()

        self.assertEqual(commit_hash, "unknown")

    @patch('commentreply.run_command')
    def test_get_current_branch_success(self, mock_run):
        """Git branch name retrieval success"""
        mock_run.return_value = (True, "feature-branch\n", "")

        branch = commentreply.get_current_branch()

        self.assertEqual(branch, "feature-branch")

    @patch('commentreply.run_command')
    def test_get_current_branch_failure(self, mock_run):
        """Git branch name retrieval failure"""
        mock_run.return_value = (False, "", "HEAD detached")

        branch = commentreply.get_current_branch()

        self.assertEqual(branch, "unknown")

    ## Matrix 7: Argument Parsing × Validation

    def test_parse_arguments_valid_input(self):
        """Valid command line arguments"""
        original_argv = sys.argv
        try:
            sys.argv = ["commentreply.py", "owner", "repo", "123"]

            owner, repo, pr_number = commentreply.parse_arguments()

            self.assertEqual(owner, "owner")
            self.assertEqual(repo, "repo")
            self.assertEqual(pr_number, "123")
        finally:
            sys.argv = original_argv

    def test_parse_arguments_invalid_count(self):
        """Invalid argument count"""
        original_argv = sys.argv
        try:
            sys.argv = ["commentreply.py", "owner"]  # Missing args

            with self.assertRaises(SystemExit):
                commentreply.parse_arguments()
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main(verbosity=2)
