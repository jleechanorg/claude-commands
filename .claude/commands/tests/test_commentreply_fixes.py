#!/usr/bin/env python3
"""
Unit tests for commentreply.py fixes (retry logic, summary stats).
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add parent directory (commands) to path to import commentreply
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Add _copilot_modules for dependencies
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_copilot_modules"))

import commentreply

class TestCommentReplyFixes(unittest.TestCase):
    
    def test_post_final_summary_calculation_strict(self):
        """Test that post_final_summary calculates failures correctly and outputs to body."""
        # Setup mocks
        mock_run_command = MagicMock(return_value=(True, '{"html_url": "http://url"}', ""))
        
        with patch("commentreply.run_command", mock_run_command), \
             patch("tempfile.NamedTemporaryFile") as mock_temp, \
             patch("os.unlink"), \
             patch("json.dump") as mock_json_dump:
            
            # Setup temp file mock
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test_summary.json"

            # Test input details
            processed_count = 10
            success_count = 6
            already_replied_count = 2
            # Expected failed = 10 - 6 - 2 = 2
            
            # Execute
            commentreply.post_final_summary(
                "owner", "repo", "123",
                processed_count, success_count, already_replied_count,
                "commit_hash"
            )
            
            # Verify the data passed to json.dump
            self.assertEqual(mock_json_dump.call_count, 1)
            args, _ = mock_json_dump.call_args
            summary_data = args[0]
            
            self.assertIn("body", summary_data)
            body = summary_data["body"]
            
            # Verify calculated values are in the string
            self.assertIn("**Failed Replies**: 2", body)
            self.assertIn("**Already Replied**: 2", body)
            self.assertIn("**Successfully Replied**: 6", body)
            self.assertIn("**Total Comments Processed**: 10", body)

    def test_create_issue_comment_reply_error_type(self):
        """Test that create_issue_comment_reply returns correct error type for 422."""
        mock_run_command = MagicMock(return_value=(False, None, "422 Unprocessable Entity: Not Found"))
        
        with patch("commentreply.run_command", mock_run_command):
            # Pass required fields to pass validation
            comment = {"id": 1, "body": "test", "author": "tester"}
            success, reply_id, error_type = commentreply.create_issue_comment_reply(
                "owner", "repo", "123", comment, "response"
            )
            
            self.assertFalse(success)
            self.assertEqual(error_type, "422_not_found", "Should map 422 error to 422_not_found string")

    @patch("commentreply.load_comments_with_staleness_check")
    @patch("commentreply.create_threaded_reply")
    @patch("commentreply.run_command")
    @patch("commentreply.parse_arguments")
    @patch("commentreply.load_claude_responses")
    @patch("commentreply.get_git_commit_hash")
    @patch("commentreply.get_repo_name")
    @patch("commentreply.get_current_branch")
    @patch("commentreply.get_response_for_comment")
    @patch("commentreply.post_final_summary")
    @patch("commentreply.post_initial_summary")
    def test_retry_mechanism(self, mock_post_initial, mock_post_final, mock_get_response, 
                           mock_branch, mock_repo_name, mock_hash, mock_load_resp, 
                           mock_parse_args, mock_run_command, mock_create_reply, mock_load_comments):
        """Test that main loop retries on 422 failure."""
        
        # Setup mocks
        mock_parse_args.return_value = ("owner", "repo", "123")
        mock_repo_name.return_value = "repo"
        mock_branch.return_value = "branch"
        mock_hash.return_value = "hash"
        mock_load_resp.return_value = {}
        mock_get_response.return_value = "Generated response"
        
        # Run command mock for user check (validate_actor_login)
        # Run command mock for user check (validate_actor_login)
        # It calls `gh api user` - returns plain string with -q .login
        mock_run_command.return_value = (True, "bot_user", "")
        
        # Test Data
        comment_1 = {"id": 1, "body": "test", "user": {"login": "user1"}}
        
        # Scenario:
        # Attempt 1: Load comments -> returns [comment_1]
        #            Process comment -> create_threaded_reply fails with "422_not_found"
        # Attempt 2: Load comments -> returns [comment_1]
        #            Process comment -> create_threaded_reply succeeds
        
        mock_load_comments.side_effect = [[comment_1], [comment_1]]
        mock_create_reply.side_effect = [
            (False, None, "422_not_found"), # Fail first
            (True, "reply_id", None)        # Succeed second
        ]
        
        # Execute main
        commentreply.main()
        
        # Verification
        # 1. load_comments called twice
        self.assertEqual(mock_load_comments.call_count, 2, "Should load comments twice (initial + retry)")
        
        # 2. create_threaded_reply called twice
        self.assertEqual(mock_create_reply.call_count, 2, "Should attempt reply twice")
        
        # 3. post_final_summary called once at end
        self.assertEqual(mock_post_final.call_count, 1)
        
        # 4. Verify post_final_summary arguments:
        args, _ = mock_post_final.call_args
        # Should be 1 because we loaded 1 comment total
        self.assertEqual(args[3], 1, "Total targets should be 1")
        self.assertEqual(args[4], 1, "Total successful should be 1")
        self.assertEqual(args[5], 0, "Already replied should be 0")

    @patch("commentreply.load_comments_with_staleness_check")
    @patch("commentreply.create_threaded_reply")
    @patch("commentreply.run_command")
    @patch("commentreply.parse_arguments")
    @patch("commentreply.load_claude_responses")
    @patch("commentreply.get_git_commit_hash")
    @patch("commentreply.get_repo_name")
    @patch("commentreply.get_current_branch")
    @patch("commentreply.get_response_for_comment")
    @patch("commentreply.post_final_summary")
    @patch("commentreply.post_initial_summary")
    def test_summary_stats_persistence(self, mock_post_initial, mock_post_final, mock_get_response, 
                           mock_branch, mock_repo_name, mock_hash, mock_load_resp, 
                           mock_parse_args, mock_run_command, mock_create_reply, mock_load_comments):
        """Test that total_targets persists from first pass effectively for summary."""
        
        # Setup mocks
        mock_parse_args.return_value = ("owner", "repo", "123")
        mock_repo_name.return_value = "repo"
        mock_branch.return_value = "branch"
        mock_hash.return_value = "hash"
        mock_load_resp.return_value = {}
        mock_get_response.return_value = "Response"
        mock_run_command.return_value = (True, '{"login": "bot"}', "")
        
        # Scenario: 2 comments total
        # Comment 1: Success first try
        # Comment 2: Fails first try (422), Succeeds second try
        c1 = {"id": 1, "body": "test1", "user": {"login": "u1"}, "created_at": "2023-01-01T10:00:00Z"}
        c2 = {"id": 2, "body": "test2", "user": {"login": "u2"}, "created_at": "2023-01-01T11:00:00Z"}
        
        # First load returns both
        # Second load (retry) returns both (but logic selects failed IDs)
        mock_load_comments.side_effect = [[c1, c2], [c1, c2]]
        
        # Reply sequence:
        # Pass 1: c1 -> Success, c2 -> Fail (422)
        # Pass 2: c2 -> Success
        mock_create_reply.side_effect = [
            (True, "r1", None),           # c1
            (False, None, "422_not_found"), # c2
            (True, "r2", None)            # c2 retry
        ]
        
        commentreply.main()
        
        self.assertEqual(mock_post_final.call_count, 1)
        args, _ = mock_post_final.call_args
        
        # Verify passed values
        # processed_count (total_targets) should be 2 (from first pass)
        self.assertEqual(args[3], 2, "Should report 2 total targets even after retry loop")
        # successful_replies should be 2 (1 from pass 1 + 1 from pass 2)
        self.assertEqual(args[4], 2, "Should report 2 successful replies total")

    @patch("commentreply.load_comments_with_staleness_check")
    @patch("commentreply.create_threaded_reply")
    @patch("commentreply.run_command")
    @patch("commentreply.parse_arguments")
    @patch("commentreply.load_claude_responses")
    @patch("commentreply.get_git_commit_hash")
    @patch("commentreply.get_repo_name")
    @patch("commentreply.get_current_branch")
    @patch("commentreply.get_response_for_comment")
    @patch("commentreply.post_final_summary")
    @patch("commentreply.post_initial_summary")
    def test_issue_comment_idempotency(self, mock_post_initial, mock_post_final, mock_get_response, 
                           mock_branch, mock_repo_name, mock_hash, mock_load_resp, 
                           mock_parse_args, mock_run_command, mock_create_reply, mock_load_comments):
        """Test that issue comments are skipped if already replied (idempotency)."""
        
        # Setup mocks
        mock_parse_args.return_value = ("owner", "repo", "123")
        mock_repo_name.return_value = "repo"
        mock_branch.return_value = "branch"
        mock_hash.return_value = "hash"
        mock_load_resp.return_value = {}
        mock_get_response.return_value = "Response"
        # Current actor is "bot"
        mock_run_command.return_value = (True, "bot", "")
        
        # Scenario:
        # Comment 1: User comment (issue type)
        # Comment 2: Bot reply to Comment 1 via reference pattern (issue type)
        c1 = {"id": 100, "body": "User issue comment", "user": {"login": "user"}, "type": "issue", "created_at": "2023-01-01T10:00:00Z"}
        # Note: Comment 2 body contains the reference pattern
        c2 = {"id": 101, "body": "In response to [comment #100](url)\n\nAnswer", "user": {"login": "bot"}, "type": "issue", "created_at": "2023-01-01T10:01:00Z"}
        
        mock_load_comments.return_value = [c1, c2]
        
        commentreply.main()
        
        # Verification
        # create_threaded_reply should NOT be called because c1 is handled by c2 via pattern match
        mock_create_reply.assert_not_called()
        
        # Post summary should show 1 already replied
        self.assertEqual(mock_post_final.call_count, 1)
        args, _ = mock_post_final.call_args
        self.assertEqual(args[5], 1, "Should report 1 already replied")

if __name__ == "__main__":
    unittest.main()
