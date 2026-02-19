#!/usr/bin/env python3
"""
Unit tests for authentication state restoration in CodexGitHubMentionsAutomation.
Focuses on cookie validation, localStorage restoration, and error handling.
"""

import json
from unittest.mock import AsyncMock, Mock, patch
import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from jleechanorg_pr_automation.openai_automation.codex_github_mentions import (
    CodexGitHubMentionsAutomation,
    AUTH_STATE_PATH,
)

@pytest.fixture
def automation():
    """Create automation instance with mocked browser/context/page."""
    auto = CodexGitHubMentionsAutomation()
    auto.context = AsyncMock()
    
    # Setup page mock
    page_mock = AsyncMock()
    # is_closed is synchronous in Playwright
    page_mock.is_closed = Mock(return_value=False)
    page_mock.url = "https://chatgpt.com/c/123"
    
    auto.page = page_mock
    return auto

@pytest.mark.asyncio
async def test_auth_restoration_cookies_and_localstorage(automation):
    """Test full restoration of cookies and localStorage from valid auth state."""
    
    mock_state = {
        "cookies": [
            {
                "name": "session_token", 
                "value": "xyz", 
                "domain": ".chatgpt.com", 
                "path": "/"
            }
        ],
        "origins": [
            {
                "origin": "https://chatgpt.com",
                "localStorage": [
                    {"name": "theme", "value": "dark"},
                    {"name": "feature_flags", "value": "true"}
                ]
            }
        ]
    }
    
    # Mock file existence and read
    with patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions.AUTH_STATE_PATH") as mock_path, \
         patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions._ensure_auth_state_permissions") as mock_perms:
        
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(mock_state)
        mock_path.__str__.return_value = "/tmp/fake_path"
        
        # Configure wait_for_selector to fail first, then succeed
        automation.page.wait_for_selector.side_effect = [
            PlaywrightTimeoutError("Not logged in"),
            True
        ]
        
        result = await automation.ensure_openai_login()
        
        # Verify permissions check
        mock_perms.assert_called_once_with(mock_path)
        
        # Verify cookie injection
        automation.context.add_cookies.assert_awaited_once_with(mock_state["cookies"])
        
        # Verify localStorage injection via page.evaluate
        assert automation.page.evaluate.call_count == 2
        
        # Verify calls contain the correct keys/values
        call_args = automation.page.evaluate.await_args_list
        # Note: calls might be in any order if list iteration order varies, but list is ordered here
        assert 'setItem("theme", "dark")' in call_args[0][0][0]
        assert 'setItem("feature_flags", "true")' in call_args[1][0][0]
        
        assert result is True

@pytest.mark.asyncio
async def test_auth_restoration_origin_mismatch(automation):
    """Test that localStorage is NOT injected if origin doesn't match."""
    
    mock_state = {
        "cookies": [{"name": "c", "value": "v", "domain": "chatgpt.com", "path": "/"}],
        "origins": [
            {
                "origin": "https://other-domain.com",
                "localStorage": [{"name": "secret", "value": "fail"}]
            }
        ]
    }
    
    # Page URL is chatgpt.com (from fixture), so origin shouldn't match
    with patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions.AUTH_STATE_PATH") as mock_path, \
         patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions._ensure_auth_state_permissions"):
        
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(mock_state)
        
        automation.page.wait_for_selector.side_effect = [PlaywrightTimeoutError("Fail"), True]
        
        await automation.ensure_openai_login()
        
        # Should NOT call evaluate to set items
        automation.page.evaluate.assert_not_awaited()

@pytest.mark.asyncio
async def test_auth_restoration_secure_origin_matching(automation):
    """Test that subdomain matching prevents injection into wrong subdomains."""
    
    # State has origin https://chatgpt.com
    mock_state = {
        "cookies": [{"name": "c", "value": "v", "domain": "chatgpt.com", "path": "/"}],
        "origins": [
            {
                "origin": "https://chatgpt.com",
                "localStorage": [{"name": "key", "value": "val"}]
            }
        ]
    }
    
    # 1. Malicious subdomain matching test
    automation.page.url = "https://chatgpt.com.evil.com/login"
    
    with patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions.AUTH_STATE_PATH") as mock_path, \
         patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions._ensure_auth_state_permissions"):
        
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(mock_state)
        
        automation.page.wait_for_selector = AsyncMock(side_effect=[
            PlaywrightTimeoutError("Fail"),
            True
        ])
        await automation.ensure_openai_login()
        automation.page.evaluate.assert_not_awaited()

    # 2. Correct domain test
    automation.page.url = "https://chatgpt.com/c/123"
    
    with patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions.AUTH_STATE_PATH") as mock_path, \
         patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions._ensure_auth_state_permissions"):
        
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(mock_state)
        
        # Reset mock for second run
        automation.page.evaluate = AsyncMock()
        automation.page.wait_for_selector = AsyncMock(side_effect=[
            PlaywrightTimeoutError("Fail"),
            True
        ])
        
        await automation.ensure_openai_login()
        automation.page.evaluate.assert_awaited()

@pytest.mark.asyncio
async def test_auth_restoration_cookie_validation(automation):
    """Test validation of cookies (missing fields, incomplete data)."""
    
    mock_state = {
        "cookies": [
            {"name": "valid", "value": "1", "domain": ".com", "path": "/"}, # Valid
            {"name": "bad1"}, # Missing value
            {"name": "bad2", "value": "2"}, # Missing domain/path AND url
            {"not_a_dict": True}, # Invalid type
        ]
    }
    
    with patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions.AUTH_STATE_PATH") as mock_path, \
         patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions._ensure_auth_state_permissions"):
        
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(mock_state)
        
        automation.page.wait_for_selector.side_effect = [PlaywrightTimeoutError("Fail"), True]
        
        await automation.ensure_openai_login()
        
        # Should only inject the one valid cookie
        automation.context.add_cookies.assert_awaited_once()
        call_args = automation.context.add_cookies.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["name"] == "valid"

@pytest.mark.asyncio
async def test_auth_restoration_null_cookies(automation):
    """Test handling of 'cookies': null in JSON."""
    
    mock_state = {"cookies": None}
    
    with patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions.AUTH_STATE_PATH") as mock_path, \
         patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions._ensure_auth_state_permissions"):
        
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(mock_state)
        
        automation.page.wait_for_selector.side_effect = [PlaywrightTimeoutError("Fail"), True]
        
        await automation.ensure_openai_login()
        
        # Should not crash, should not call add_cookies
        automation.context.add_cookies.assert_not_awaited()

@pytest.mark.asyncio
async def test_auth_restoration_empty_localstorage_values(automation):
    """Test that empty string values in localStorage are preserved (not skipped)."""
    
    mock_state = {
        "cookies": [{"name": "c", "value": "v", "domain": "chatgpt.com", "path": "/"}],
        "origins": [
            {
                "origin": "https://chatgpt.com",
                "localStorage": [
                    {"name": "empty_val", "value": ""}, # Should be kept
                    {"name": "null_val", "value": None}  # Should be skipped if logic checks for None
                ]
            }
        ]
    }
    
    with patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions.AUTH_STATE_PATH") as mock_path, \
         patch("jleechanorg_pr_automation.openai_automation.codex_github_mentions._ensure_auth_state_permissions"):
        
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(mock_state)
        
        automation.page.wait_for_selector.side_effect = [PlaywrightTimeoutError("Fail"), True]
        await automation.ensure_openai_login()
        
        # Should call evaluate for empty string value
        # But NOT for None value (logic: if key is not None and value is not None)
        assert automation.page.evaluate.call_count == 1
        call_arg = automation.page.evaluate.call_args[0][0]
        assert 'setItem("empty_val", "")' in call_arg
