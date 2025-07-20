#!/usr/bin/env python3
"""
Test suite for copilot_comment_fetch.py

Tests the CommentFetcher class which uses GitHub CLI hybrid API approach:
- REST API (gh api) for inline comments with pagination
- GraphQL-like queries (gh pr view --json) for reviews and general comments
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
import os

# Add the commands directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from copilot_comment_fetch import CommentFetcher, Comment


class TestCommentFetcher(unittest.TestCase):
    """Test cases for the CommentFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pr_number = "722"
        self.repo = "jleechanorg/worldarchitect.ai"
        self.fetcher = CommentFetcher(self.pr_number, self.repo)
    
    def test_init_with_repo(self):
        """Test CommentFetcher initialization with explicit repo."""
        fetcher = CommentFetcher("123", "owner/repo")
        self.assertEqual(fetcher.pr_number, "123")
        self.assertEqual(fetcher.repo, "owner/repo")
        self.assertEqual(fetcher.total_comments, 0)
        self.assertEqual(fetcher.fetch_duration, 0)
    
    @patch('subprocess.run')
    def test_get_current_repo_success(self, mock_run):
        """Test successful auto-detection of current repository."""
        mock_result = Mock()
        mock_result.stdout = json.dumps({
            "owner": {"login": "testowner"},
            "name": "testrepo"
        })
        mock_run.return_value = mock_result
        
        fetcher = CommentFetcher("123")
        self.assertEqual(fetcher.repo, "testowner/testrepo")
    
    @patch('subprocess.run')
    def test_get_current_repo_failure(self, mock_run):
        """Test repository auto-detection failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
        
        with self.assertRaises(ValueError) as context:
            CommentFetcher("123")
        
        self.assertIn("Could not auto-detect repository", str(context.exception))
    
    @patch('subprocess.run')
    def test_run_gh_command_success(self, mock_run):
        """Test successful GitHub CLI command execution."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([{"id": 1, "body": "test comment"}])
        mock_run.return_value = mock_result
        
        result = self.fetcher._run_gh_command(["gh", "api", "test"])
        
        self.assertEqual(result, [{"id": 1, "body": "test comment"}])
        mock_run.assert_called_once_with(["gh", "api", "test"], capture_output=True, text=True, check=True)
    
    @patch('subprocess.run')
    def test_run_gh_command_empty_response(self, mock_run):
        """Test GitHub CLI command with empty response."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        result = self.fetcher._run_gh_command(["gh", "api", "test"])
        
        self.assertEqual(result, [])
    
    @patch('subprocess.run')
    def test_run_gh_command_error(self, mock_run):
        """Test GitHub CLI command execution error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh", stderr="API error")
        
        with patch('sys.stderr'):
            result = self.fetcher._run_gh_command(["gh", "api", "test"])
        
        self.assertEqual(result, [])
    
    @patch('subprocess.run')
    def test_get_pagination_info_success(self, mock_run):
        """Test successful pagination info extraction from Link header."""
        mock_result = Mock()
        mock_result.stderr = 'link: <https://api.github.com/repos/test/repo/pulls/1/comments?page=5>; rel="last"'
        mock_run.return_value = mock_result
        
        pages = self.fetcher._get_rest_api_pagination_info()
        
        self.assertEqual(pages, 5)
    
    @patch('subprocess.run')
    def test_get_pagination_info_no_link_header(self, mock_run):
        """Test pagination info when no Link header present."""
        mock_result = Mock()
        mock_result.stderr = "No link header"
        mock_run.return_value = mock_result
        
        pages = self.fetcher._get_rest_api_pagination_info()
        
        self.assertEqual(pages, 1)
    
    @patch('subprocess.run')
    def test_get_pagination_info_error(self, mock_run):
        """Test pagination info extraction error handling."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
        
        pages = self.fetcher._get_rest_api_pagination_info()
        
        self.assertEqual(pages, 1)


class TestCommentFetcherIntegration(unittest.TestCase):
    """Integration tests for comment fetching methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = CommentFetcher("722", "jleechanorg/worldarchitect.ai")
    
    @patch.object(CommentFetcher, '_run_gh_command')
    @patch.object(CommentFetcher, '_get_rest_api_pagination_info')
    def test_fetch_inline_comments_with_pagination(self, mock_pagination, mock_gh_command):
        """Test inline comments fetching with pagination (REST API)."""
        # Mock pagination info
        mock_pagination.return_value = 1  # Simplified to no pagination
        
        # Mock API response for all comments
        mock_gh_command.return_value = [
            {"id": 1, "body": "Comment 1", "user": {"login": "coderabbit", "type": "Bot"}, 
             "path": "test.py", "line": 10, "created_at": "2025-07-19T10:00:00Z"},
            {"id": 2, "body": "Comment 2", "user": {"login": "jleechan2015", "type": "User"}, 
             "path": "test.py", "line": 20, "created_at": "2025-07-19T11:00:00Z"}
        ]
        
        comments = self.fetcher.fetch_inline_comments_rest_api()
        
        # Should fetch bot and specific user comments
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].id, "2")  # Most recent first (sorted by created_at)
        self.assertEqual(comments[0].comment_type, "inline")
        self.assertEqual(comments[0].file, "test.py")
        self.assertEqual(comments[0].line, 20)
        
        # Verify API call was made
        self.assertTrue(mock_gh_command.called)
    
    @patch.object(CommentFetcher, '_run_gh_command')
    def test_fetch_review_comments(self, mock_gh_command):
        """Test PR review comments fetching (GraphQL-like query)."""
        mock_gh_command.return_value = {
            "reviews": [
                {
                    "id": 100,
                    "body": "Review comment 1",
                    "author": {"login": "coderabbit"},
                    "state": "COMMENTED",
                    "createdAt": "2025-07-19T10:00:00Z"
                },
                {
                    "id": 101,
                    "body": "Review comment 2", 
                    "author": {"login": "jleechan2015"},
                    "state": "APPROVED",
                    "createdAt": "2025-07-19T11:00:00Z"
                }
            ]
        }
        
        comments = self.fetcher.fetch_review_comments_graphql()
        
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].id, "100")
        self.assertEqual(comments[0].comment_type, "review")
        self.assertEqual(comments[0].state, "COMMENTED")
        self.assertEqual(comments[1].state, "APPROVED")
    
    @patch.object(CommentFetcher, '_run_gh_command')
    def test_fetch_general_comments(self, mock_gh_command):
        """Test general PR comments fetching (GraphQL-like query)."""
        mock_gh_command.return_value = {
            "comments": [
                {
                    "id": 200,
                    "body": "General comment 1",
                    "author": {"login": "github-actions"},
                    "createdAt": "2025-07-19T10:00:00Z"
                },
                {
                    "id": 201,
                    "body": "General comment 2",
                    "author": {"login": "jleechan2015"},
                    "createdAt": "2025-07-19T11:00:00Z"
                }
            ]
        }
        
        comments = self.fetcher.fetch_general_comments_graphql()
        
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].id, "200")
        self.assertEqual(comments[0].comment_type, "general")
        self.assertEqual(comments[1].id, "201")


class TestCommentFetcherHybridAPI(unittest.TestCase):
    """Test the hybrid REST API + GraphQL approach."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = CommentFetcher("722", "jleechanorg/worldarchitect.ai")
    
    @patch.object(CommentFetcher, 'fetch_inline_comments_rest_api')
    @patch.object(CommentFetcher, 'fetch_review_comments_graphql')
    @patch.object(CommentFetcher, 'fetch_general_comments_graphql')
    def test_fetch_all_comments_hybrid_approach(self, mock_general, mock_review, mock_inline):
        """Test that fetch_all_comments uses hybrid API approach correctly."""
        # Mock responses from different API endpoints
        mock_inline.return_value = [
            Comment("1", "Inline comment", "coderabbit", "inline", "2025-07-19T10:00:00Z", "test.py", 10)
        ]
        mock_review.return_value = [
            Comment("2", "Review comment", "jleechan2015", "review", "2025-07-19T11:00:00Z", state="APPROVED")
        ]
        mock_general.return_value = [
            Comment("3", "General comment", "github-actions", "general", "2025-07-19T12:00:00Z")
        ]
        
        all_comments = self.fetcher.fetch_all_comments()
        
        # Should combine all comment types, sorted by recency
        self.assertEqual(len(all_comments), 3)
        self.assertEqual(all_comments[0].id, "3")  # Most recent first
        self.assertEqual(all_comments[1].id, "2")
        self.assertEqual(all_comments[2].id, "1")
        
        # Verify all API methods were called
        mock_inline.assert_called_once()
        mock_review.assert_called_once()
        mock_general.assert_called_once()
    
    def test_to_json_output_format(self):
        """Test JSON output format for shell workflow compatibility."""
        comments = [
            Comment("1", "Test comment", "coderabbit", "inline", "2025-07-19T10:00:00Z", "test.py", 10, 5),
            Comment("2", "Review comment", "jleechan2015", "review", "2025-07-19T11:00:00Z", state="APPROVED")
        ]
        
        json_output = self.fetcher.to_json(comments)
        parsed = json.loads(json_output)
        
        self.assertEqual(len(parsed), 2)
        
        # Check inline comment structure
        inline_comment = parsed[0]
        self.assertEqual(inline_comment['id'], "1")
        self.assertEqual(inline_comment['body'], "Test comment")
        self.assertEqual(inline_comment['user'], "coderabbit")
        self.assertEqual(inline_comment['_type'], "inline")
        self.assertEqual(inline_comment['file'], "test.py")
        self.assertEqual(inline_comment['line'], 10)
        self.assertEqual(inline_comment['position'], 5)
        
        # Check review comment structure
        review_comment = parsed[1]
        self.assertEqual(review_comment['id'], "2")
        self.assertEqual(review_comment['state'], "APPROVED")
        self.assertNotIn('file', review_comment)  # Optional fields not present


class TestCommentFetcherFiltering(unittest.TestCase):
    """Test comment filtering logic for bots and specific users."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = CommentFetcher("722", "jleechanorg/worldarchitect.ai")
    
    @patch.object(CommentFetcher, '_run_gh_command')
    def test_bot_filtering_inline_comments(self, mock_gh_command):
        """Test that inline comments correctly filter for bots and specific users."""
        mock_gh_command.return_value = [
            # Should be included - Bot type
            {"id": 1, "body": "Bot comment", "user": {"login": "coderabbit", "type": "Bot"}, 
             "path": "test.py", "created_at": "2025-07-19T10:00:00Z"},
            # Should be included - bot in name
            {"id": 2, "body": "Copilot comment", "user": {"login": "github-copilot", "type": "User"}, 
             "path": "test.py", "created_at": "2025-07-19T11:00:00Z"},
            # Should be included - specific user
            {"id": 3, "body": "User comment", "user": {"login": "jleechan2015", "type": "User"}, 
             "path": "test.py", "created_at": "2025-07-19T12:00:00Z"},
            # Should be excluded - regular user
            {"id": 4, "body": "Other user", "user": {"login": "randomuser", "type": "User"}, 
             "path": "test.py", "created_at": "2025-07-19T13:00:00Z"}
        ]
        
        comments = self.fetcher.fetch_inline_comments_rest_api()
        
        # Should only get bot and specific user comments
        self.assertEqual(len(comments), 3)
        user_logins = [c.user for c in comments]
        self.assertIn("coderabbit", user_logins)
        self.assertIn("github-copilot", user_logins)
        self.assertIn("jleechan2015", user_logins)
        self.assertNotIn("randomuser", user_logins)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)