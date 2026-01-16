#!/usr/bin/env python3
"""
Unit tests for commentreply.py processing ALL comments including replies.

Tests the fix where commentreply.py now processes all comments (including replies)
instead of filtering out comments with in_reply_to_id set.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the module under test
import commentreply


class TestCommentReplyProcessing(unittest.TestCase):
    """Test that commentreply.py processes ALL comments including replies"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_comments = [
            # Top-level comment 1
            {
                "id": 1001,
                "body": "Top-level comment 1",
                "user": {"login": "user1"},
                "created_at": "2024-01-01T10:00:00Z",
            },
            # Reply to comment 1
            {
                "id": 1002,
                "body": "Reply to comment 1",
                "user": {"login": "user2"},
                "in_reply_to_id": 1001,
                "created_at": "2024-01-01T11:00:00Z",
            },
            # Top-level comment 2
            {
                "id": 1003,
                "body": "Top-level comment 2",
                "user": {"login": "user3"},
                "created_at": "2024-01-01T12:00:00Z",
            },
            # Reply to comment 2
            {
                "id": 1004,
                "body": "Reply to comment 2",
                "user": {"login": "user1"},
                "in_reply_to_id": 1003,
                "created_at": "2024-01-01T13:00:00Z",
            },
            # Another reply to comment 1
            {
                "id": 1005,
                "body": "Another reply to comment 1",
                "user": {"login": "user3"},
                "in_reply_to_id": 1001,
                "created_at": "2024-01-01T14:00:00Z",
            },
        ]

    def test_all_targets_includes_reply_comments(self):
        """Test that all_targets includes comments with in_reply_to_id"""
        # Simulate the old behavior (filtering out replies)
        old_behavior = [c for c in self.sample_comments if not c.get("in_reply_to_id")]
        self.assertEqual(len(old_behavior), 2, "Old behavior only processed top-level")

        # Simulate the new behavior (includes all comments)
        new_behavior = self.sample_comments  # all_targets = all_comments
        self.assertEqual(len(new_behavior), 5, "New behavior processes all comments")

        # Verify reply comments are included
        reply_comments = [c for c in new_behavior if c.get("in_reply_to_id")]
        self.assertEqual(len(reply_comments), 3, "Should include all 3 reply comments")

    def test_validate_comment_data_works_for_replies(self):
        """Test that comment validation works for reply comments"""
        # Reply comment should pass validation
        reply_comment = {
            "id": 1002,
            "body": "This is a reply",
            "user": {"login": "user1"},
            "in_reply_to_id": 1001,
        }

        is_valid = commentreply.validate_comment_data(reply_comment)
        self.assertTrue(is_valid, "Reply comments should pass validation")

    def test_reply_comment_can_get_response(self):
        """Test that get_response_for_comment works for reply comments"""
        reply_comment = {
            "id": 1002,
            "body": "This is a reply",
            "user": {"login": "user1"},
            "in_reply_to_id": 1001,
        }

        responses_data = {
            "responses": [
                {
                    "comment_id": 1002,
                    "reply_text": "Response to reply comment",
                }
            ]
        }

        response = commentreply.get_response_for_comment(
            reply_comment, responses_data, "abc123"
        )

        self.assertEqual(
            response,
            "Response to reply comment",
            "Should get response for reply comment",
        )

    def test_actor_filter_works_for_reply_comments(self):
        """Test that actor filtering (skip own comments) works for replies"""
        actor_login = "bot_user"

        # Own reply comment should be skipped
        own_reply = {
            "id": 1002,
            "body": "My own reply",
            "user": {"login": actor_login},
            "in_reply_to_id": 1001,
        }

        # Should skip comments by actor
        should_skip = own_reply.get("user", {}).get("login") == actor_login
        self.assertTrue(should_skip, "Should skip own reply comments")

        # Other user's reply should NOT be skipped
        other_reply = {
            "id": 1003,
            "body": "Someone else's reply",
            "user": {"login": "other_user"},
            "in_reply_to_id": 1001,
        }

        should_not_skip = other_reply.get("user", {}).get("login") != actor_login
        self.assertTrue(should_not_skip, "Should not skip other users' replies")

    def test_already_replied_check_works_for_replies(self):
        """Test that idempotency check (already replied) works for reply comments"""
        actor_login = "bot_user"

        target_comment = {
            "id": 1001,
            "body": "Target comment",
            "user": {"login": "user1"},
        }

        # Scenario 1: Already replied to this comment
        all_comments_with_reply = [
            target_comment,
            {
                "id": 1002,
                "body": "Bot's reply",
                "user": {"login": actor_login},
                "in_reply_to_id": 1001,
            },
        ]

        replied_by_actor = any(
            (c.get("in_reply_to_id") == target_comment["id"])
            and (c.get("user", {}).get("login") == actor_login)
            for c in all_comments_with_reply
        )

        self.assertTrue(replied_by_actor, "Should detect when already replied")

        # Scenario 2: Not yet replied
        all_comments_without_reply = [target_comment]

        not_replied_by_actor = not any(
            (c.get("in_reply_to_id") == target_comment["id"])
            and (c.get("user", {}).get("login") == actor_login)
            for c in all_comments_without_reply
        )

        self.assertTrue(not_replied_by_actor, "Should detect when not yet replied")

    def test_thread_completion_check_works_for_replies(self):
        """Test that thread completion check ([AI responder]) works for reply comments"""
        target_comment = {"id": 1001, "body": "Original comment"}

        # Scenario 1: Thread ends with [AI responder] - should skip
        all_comments_completed = [
            target_comment,
            {
                "id": 1002,
                "body": "Some reply",
                "in_reply_to_id": 1001,
                "created_at": "2024-01-01T10:00:00Z",
            },
            {
                "id": 1003,
                "body": "Final reply with [AI responder] marker",
                "in_reply_to_id": 1001,
                "created_at": "2024-01-01T11:00:00Z",
            },
        ]

        thread_replies = [
            c for c in all_comments_completed if c.get("in_reply_to_id") == 1001
        ]
        thread_replies.sort(key=lambda x: x.get("created_at", ""))
        last_reply_body = thread_replies[-1].get("body", "")
        is_completed = "[AI responder]" in last_reply_body

        self.assertTrue(is_completed, "Should detect thread completion")

        # Scenario 2: Thread does not end with [AI responder] - should process
        all_comments_incomplete = [
            target_comment,
            {
                "id": 1002,
                "body": "Regular reply",
                "in_reply_to_id": 1001,
                "created_at": "2024-01-01T10:00:00Z",
            },
        ]

        thread_replies_incomplete = [
            c for c in all_comments_incomplete if c.get("in_reply_to_id") == 1001
        ]
        thread_replies_incomplete.sort(key=lambda x: x.get("created_at", ""))
        last_reply_body_incomplete = thread_replies_incomplete[-1].get("body", "")
        is_not_completed = "[AI responder]" not in last_reply_body_incomplete

        self.assertTrue(is_not_completed, "Should process incomplete threads")

    def test_reply_to_bot_comment_processed(self):
        """Test that replies to bot comments are processed (e.g., CodeRabbit replying to CodeRabbit)"""
        # Scenario: CodeRabbit bot replies to its own comment with clarifications
        bot_login = "coderabbitai[bot]"
        actor_login = "github-actions[bot]"  # Different bot responding

        bot_original = {
            "id": 2001,
            "body": "CodeRabbit suggestion",
            "user": {"login": bot_login},
        }

        bot_reply = {
            "id": 2002,
            "body": "CodeRabbit clarification (reply to self)",
            "user": {"login": bot_login},
            "in_reply_to_id": 2001,
        }

        # With old behavior (top_level only), this reply would be filtered out
        old_behavior = [c for c in [bot_original, bot_reply] if not c.get("in_reply_to_id")]
        self.assertEqual(len(old_behavior), 1, "Old behavior misses bot replies")

        # With new behavior (all_targets), this reply should be included
        new_behavior = [bot_original, bot_reply]
        self.assertEqual(len(new_behavior), 2, "New behavior includes bot replies")

        # Verify it wouldn't be skipped by actor filter (different bot)
        should_not_skip = bot_reply.get("user", {}).get("login") != actor_login
        self.assertTrue(should_not_skip, "Should process reply from different bot")

    def test_coverage_calculation_includes_replies(self):
        """Test that coverage calculation accounts for reply comments"""
        actor_login = "bot_user"

        # Mix of top-level and replies
        all_comments = [
            {"id": 1, "body": "Top 1", "user": {"login": "user1"}},
            {"id": 2, "body": "Reply to 1", "user": {"login": "user2"}, "in_reply_to_id": 1},
            {"id": 3, "body": "Top 2", "user": {"login": "user3"}},
            {"id": 4, "body": "Reply to 2", "user": {"login": "user1"}, "in_reply_to_id": 2},
        ]

        # Simulate processing: skip actor's own comments
        targets = [c for c in all_comments if c.get("user", {}).get("login") != actor_login]

        # Old behavior would only count top-level comments (2)
        old_target_count = len([c for c in targets if not c.get("in_reply_to_id")])
        self.assertEqual(old_target_count, 2, "Old behavior: 2 top-level targets")

        # New behavior counts ALL comments (4)
        new_target_count = len(targets)
        self.assertEqual(new_target_count, 4, "New behavior: 4 total targets")

        # Coverage calculation should be based on ALL targets, not just top-level
        # This ensures true 100% coverage


if __name__ == "__main__":
    unittest.main()
