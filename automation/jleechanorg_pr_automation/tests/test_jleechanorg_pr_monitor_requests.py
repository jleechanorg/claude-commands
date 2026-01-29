#!/usr/bin/env python3
"""Unit tests for jleechanorg_pr_monitor using Python requests instead of gh CLI."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import requests

from automation.jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestDiscoverOpenPRsWithRequests:
    """Test discover_open_prs() using Python requests instead of gh CLI."""

    def test_discover_open_prs_success(self, monkeypatch):
        """Test discover_open_prs successfully fetches PRs via GraphQL API."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        # Mock get_github_token
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock GraphQL API response
        mock_response = Mock()
        mock_response.status_code = 200
        from datetime import datetime, timedelta, timezone
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        mock_response.json.return_value = {
            "data": {
                "search": {
                    "nodes": [
                        {
                            "__typename": "PullRequest",
                            "number": 42,
                            "title": "Test PR",
                            "headRefName": "feature-branch",
                            "baseRefName": "main",
                            "updatedAt": recent_date,
                            "url": "https://github.com/org/repo/pull/42",
                            "author": {"login": "testuser"},
                            "headRefOid": "abc123",
                            "state": "OPEN",
                            "isDraft": False,
                            "repository": {
                                "name": "repo",
                                "nameWithOwner": "org/repo"
                            }
                        }
                    ],
                    "pageInfo": {
                        "hasNextPage": False,
                        "endCursor": None
                    }
                }
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.post", return_value=mock_response):
            prs = monitor.discover_open_prs(cutoff_hours=24)
            
            assert len(prs) == 1
            assert prs[0]["number"] == 42
            assert prs[0]["title"] == "Test PR"

    def test_discover_open_prs_no_token(self, monkeypatch):
        """Test discover_open_prs raises error when no token available."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: None
        )
        
        with pytest.raises(RuntimeError, match="No GitHub token available"):
            monitor.discover_open_prs(cutoff_hours=24)

    def test_discover_open_prs_api_error(self, monkeypatch):
        """Test discover_open_prs handles API errors gracefully."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.HTTPError("API Error")
        http_error.response = mock_response
        mock_response.raise_for_status = Mock(side_effect=http_error)
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="GraphQL search failed"):
                monitor.discover_open_prs(cutoff_hours=24)

    def test_discover_open_prs_pagination(self, monkeypatch):
        """Test discover_open_prs handles pagination correctly."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # First page response
        first_response = Mock()
        first_response.status_code = 200
        from datetime import datetime, timedelta, timezone
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        first_response.json.return_value = {
            "data": {
                "search": {
                    "nodes": [
                        {
                            "__typename": "PullRequest",
                            "number": 1,
                            "title": "PR 1",
                            "headRefName": "branch1",
                            "baseRefName": "main",
                            "updatedAt": recent_date,
                            "url": "https://github.com/org/repo/pull/1",
                            "author": {"login": "user1"},
                            "headRefOid": "abc123",
                            "state": "OPEN",
                            "isDraft": False,
                            "repository": {"name": "repo", "nameWithOwner": "org/repo"}
                        }
                    ],
                    "pageInfo": {
                        "hasNextPage": True,
                        "endCursor": "cursor123"
                    }
                }
            }
        }
        first_response.raise_for_status = Mock()
        
        # Second page response
        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "data": {
                "search": {
                    "nodes": [
                        {
                            "__typename": "PullRequest",
                            "number": 2,
                            "title": "PR 2",
                            "headRefName": "branch2",
                            "baseRefName": "main",
                            "updatedAt": recent_date,
                            "url": "https://github.com/org/repo/pull/2",
                            "author": {"login": "user2"},
                            "headRefOid": "def456",
                            "state": "OPEN",
                            "isDraft": False,
                            "repository": {"name": "repo", "nameWithOwner": "org/repo"}
                        }
                    ],
                    "pageInfo": {
                        "hasNextPage": False,
                        "endCursor": None
                    }
                }
            }
        }
        second_response.raise_for_status = Mock()
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.post", side_effect=[first_response, second_response]):
            prs = monitor.discover_open_prs(cutoff_hours=24)
            
            assert len(prs) == 2
            assert prs[0]["number"] == 1
            assert prs[1]["number"] == 2


class TestGetFixCommentWatchStateWithRequests:
    """Test _get_fix_comment_watch_state() using Python requests instead of gh CLI."""

    def test_get_fix_comment_watch_state_success(self, monkeypatch):
        """Test _get_fix_comment_watch_state successfully fetches PR data via REST API."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        # Mock get_github_token
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock PR data response
        pr_response = Mock()
        pr_response.status_code = 200
        pr_response.json.return_value = {
            "head": {"sha": "abc123", "ref": "feature-branch"},
            "title": "Test PR",
            "user": {"login": "testuser"}
        }
        pr_response.raise_for_status = Mock()
        
        # Mock comments response
        comments_response = Mock()
        comments_response.status_code = 200
        comments_response.json.return_value = [
            {"id": 1, "body": "Comment 1"},
            {"id": 2, "body": "Comment 2"}
        ]
        comments_response.raise_for_status = Mock()
        
        # Mock commits response (with messageHeadline structure)
        commits_response = Mock()
        commits_response.status_code = 200
        commits_response.json.return_value = [
            {"sha": "abc123", "commit": {"message": "Test commit", "messageHeadline": "Test commit"}}
        ]
        commits_response.raise_for_status = Mock()
        
        get_calls = []
        def mock_get(url, headers=None, timeout=None, params=None):
            get_calls.append(url)
            if "pulls" in url and "comments" not in url and "commits" not in url:
                return pr_response
            elif "comments" in url:
                return comments_response
            elif "commits" in url:
                return commits_response
            return Mock(status_code=200, json=lambda: {}, raise_for_status=Mock())
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get", side_effect=mock_get):
            pr_data, head_sha, comments, headlines = monitor._get_fix_comment_watch_state("org/repo", 123)
            
            assert head_sha == "abc123"
            assert pr_data["title"] == "Test PR"
            assert len(comments) == 2
            assert isinstance(headlines, list)  # headlines is a list of commit message headlines
            # Verify all three endpoints were called
            assert any("pulls/123" in url and "comments" not in url and "commits" not in url for url in get_calls)
            assert any("issues/123/comments" in url for url in get_calls)
            assert any("pulls/123/commits" in url for url in get_calls)

    def test_get_fix_comment_watch_state_no_token(self, monkeypatch):
        """Test _get_fix_comment_watch_state raises error when no token available."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: None
        )
        
        with pytest.raises(RuntimeError, match="No GitHub token available"):
            monitor._get_fix_comment_watch_state("org/repo", 123)

    def test_get_fix_comment_watch_state_api_error(self, monkeypatch):
        """Test _get_fix_comment_watch_state handles API errors gracefully."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status = Mock(side_effect=http_error)
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to fetch PR data"):
                monitor._get_fix_comment_watch_state("org/repo", 123)

    def test_get_fix_comment_watch_state_comments_optional(self, monkeypatch):
        """Test _get_fix_comment_watch_state handles missing comments gracefully."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock PR data response
        pr_response = Mock()
        pr_response.status_code = 200
        pr_response.json.return_value = {
            "head": {"sha": "abc123", "ref": "feature-branch"},
            "title": "Test PR",
            "user": {"login": "testuser"}
        }
        pr_response.raise_for_status = Mock()
        
        # Mock comments error (optional)
        comments_error = requests.RequestException("Network error")
        
        # Mock commits response
        commits_response = Mock()
        commits_response.status_code = 200
        commits_response.json.return_value = []
        commits_response.raise_for_status = Mock()
        
        call_count = 0
        def mock_get(url, headers=None, timeout=None, params=None):
            nonlocal call_count
            call_count += 1
            if "pulls" in url and "comments" not in url and "commits" not in url:
                return pr_response
            elif "comments" in url:
                raise comments_error  # Comments fail but should be handled
            elif "commits" in url:
                return commits_response
            return Mock(status_code=200, json=lambda: {}, raise_for_status=Mock())
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get", side_effect=mock_get):
            pr_data, head_sha, comments, headlines = monitor._get_fix_comment_watch_state("org/repo", 123)
            
            # Should still succeed with empty comments list
            assert head_sha == "abc123"
            assert comments == []  # Empty list when comments fail
            assert isinstance(headlines, list)  # headlines is a list
