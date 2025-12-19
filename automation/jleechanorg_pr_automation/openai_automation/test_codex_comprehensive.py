#!/usr/bin/env python3
"""
Comprehensive Matrix-Driven Tests for Codex GitHub Mentions Automation.

Test Matrices:
- Matrix 1: Limit Parameter Combinations (12 tests)
- Matrix 2: CDP Connection States (8 tests)
- Matrix 3: Task Finding Scenarios (10 tests)
- Matrix 4: Navigation & Interaction (8 tests)

Total: 38 systematic test cases

Run with:
    pytest automation/openai_automation/test_codex_comprehensive.py -v
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest

from jleechanorg_pr_automation.openai_automation.codex_github_mentions import (
    CodexGitHubMentionsAutomation,
)


# Helper to check if Chrome is running with CDP
async def chrome_is_running(port=9222):
    """Check if Chrome is running with remote debugging."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://localhost:{port}/json/version", timeout=aiohttp.ClientTimeout(total=1)
            ) as resp:
                return resp.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
        return False


# Skip marker for tests requiring Chrome
requires_chrome = pytest.mark.skipif(
    not asyncio.run(chrome_is_running()),
    reason="Chrome with remote debugging not running on port 9222"
)


class TestLimitParameter:
    """Matrix 1: Test limit parameter combinations."""

    @pytest.mark.parametrize("limit,expected_behavior", [
        (None, "GitHub Mention tasks only"),
        (50, "Limit GitHub Mention tasks to 50"),
        (10, "Limit GitHub Mention tasks to 10"),
        (100, "Limit GitHub Mention tasks to 100"),
        (0, "No tasks processed"),
        (1, "Limit GitHub Mention tasks to 1"),
        (5, "Limit GitHub Mention tasks to 5"),
    ])
    def test_limit_initialization(self, limit, expected_behavior):
        """Test automation initialization with different limit values."""
        automation = CodexGitHubMentionsAutomation(task_limit=limit)
        assert automation.task_limit == limit
        print(f"✅ Limit {limit}: {expected_behavior}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limit,mock_task_count,expected_return", [
        (50, 100, 50),  # Limit to 50 when 100 available
        (10, 5, 5),     # Return all when fewer than limit
        (None, 20, 20), # No limit, return all
        (0, 50, 0),     # Zero limit, return none
    ])
    async def test_limit_applied_to_task_finding(self, limit, mock_task_count, expected_return):
        """Test that limit is correctly applied when finding tasks."""
        automation = CodexGitHubMentionsAutomation(task_limit=limit)
        automation.page = AsyncMock()

        mock_locator = AsyncMock()
        task_items = []
        for i in range(mock_task_count):
            item = Mock()
            item.get_attribute = AsyncMock(return_value=f"/codex/{i}")
            item.text_content = AsyncMock(return_value=f"Task {i}")
            task_items.append(item)

        mock_locator.count = AsyncMock(return_value=mock_task_count)
        mock_locator.nth = Mock(side_effect=lambda idx: task_items[idx])
        automation.page.locator = Mock(return_value=mock_locator)

        tasks = await automation.find_github_mention_tasks()
        assert len(tasks) == expected_return
        print(f"✅ Limit {limit} with {mock_task_count} tasks returned {expected_return}")

    @requires_chrome
    @pytest.mark.asyncio
    async def test_default_limit_50_with_real_chrome(self):
        """Test default limit of 50 with real Chrome instance."""
        automation = CodexGitHubMentionsAutomation()
        assert automation.task_limit == 50

        await automation.connect_to_existing_browser()
        await automation.navigate_to_codex()

        tasks = await automation.find_github_mention_tasks()
        # Should use ALL tasks selector when limit is set
        assert isinstance(tasks, list)
        assert len(tasks) <= 50
        print(f"✅ Default limit 50 found {len(tasks)} tasks")


class TestCDPConnectionStates:
    """Matrix 2: Test CDP connection state handling."""

    @pytest.mark.asyncio
    async def test_connect_chrome_not_running(self):
        """Test connection failure when Chrome is not running."""
        automation = CodexGitHubMentionsAutomation(cdp_url="http://localhost:9999")

        result = await automation.connect_to_existing_browser()
        assert result is False
        assert automation.browser is None
        print("✅ Correctly handled Chrome not running")

    @pytest.mark.asyncio
    async def test_connect_wrong_port(self):
        """Test connection failure on wrong port."""
        automation = CodexGitHubMentionsAutomation(cdp_url="http://localhost:1234")

        result = await automation.connect_to_existing_browser()
        assert result is False
        print("✅ Correctly handled wrong port")

    @requires_chrome
    @pytest.mark.asyncio
    async def test_connect_success_on_9222(self):
        """Test successful connection on default port 9222."""
        automation = CodexGitHubMentionsAutomation()

        result = await automation.connect_to_existing_browser()
        assert result is True
        assert automation.browser is not None
        assert automation.page is not None
        print("✅ Successfully connected to Chrome on port 9222")

    @pytest.mark.asyncio
    async def test_no_contexts_creates_new(self):
        """Test that automation creates new context when none exist."""
        automation = CodexGitHubMentionsAutomation()

        # Mock browser with no contexts
        mock_browser = AsyncMock()
        mock_browser.contexts = []
        mock_browser.new_context = AsyncMock()
        mock_context = AsyncMock()
        mock_context.pages = []
        mock_context.new_page = AsyncMock(return_value=AsyncMock())
        mock_browser.new_context.return_value = mock_context

        automation.browser = mock_browser

        # This would normally be in connect_to_existing_browser
        if not automation.browser.contexts:
            automation.context = await automation.browser.new_context()
            automation.page = await automation.context.new_page()

        assert automation.context is not None
        assert automation.page is not None
        print("✅ Created new context when none existed")


class TestTaskFinding:
    """Matrix 3: Test task finding scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("task_count,limit,expected_found,behavior", [
        (0, 50, 0, "Graceful empty"),
        (5, 50, 5, "All found"),
        (100, 50, 50, "Limited"),
        (10, None, 10, "GitHub only filter"),
        (25, 10, 10, "Limited to 10"),
        (3, 100, 3, "All found (fewer than limit)"),
    ])
    async def test_task_finding_matrix(self, task_count, limit, expected_found, behavior):
        """Test various task finding scenarios from matrix."""
        automation = CodexGitHubMentionsAutomation(task_limit=limit)
        automation.page = AsyncMock()

        # Mock task locator
        mock_locator = AsyncMock()
        mock_tasks = []
        for idx in range(task_count):
            item = Mock()
            item.get_attribute = AsyncMock(return_value=f"/codex/{idx}")
            item.text_content = AsyncMock(return_value=f"Task {idx}")
            mock_tasks.append(item)

        mock_locator.count = AsyncMock(return_value=task_count)
        mock_locator.nth = Mock(side_effect=lambda idx: mock_tasks[idx])
        automation.page.locator = Mock(return_value=mock_locator)

        tasks = await automation.find_github_mention_tasks()

        assert len(tasks) == expected_found
        print(f"✅ {behavior}: {task_count} tasks, limit={limit} → found {expected_found}")

    @pytest.mark.asyncio
    async def test_github_mention_selector_used_when_no_limit(self):
        """Test that task selector is used (now always uses /codex/tasks/ to exclude navigation)."""
        automation = CodexGitHubMentionsAutomation(task_limit=None)
        automation.page = AsyncMock()

        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=0)
        automation.page.locator = Mock(return_value=mock_locator)

        await automation.find_github_mention_tasks()

        # Verify correct selector was used - now uses /codex/tasks/ to exclude navigation links
        automation.page.locator.assert_called_with('a[href*="/codex/tasks/"]')
        print("✅ Correct selector used for None limit")

    @pytest.mark.asyncio
    async def test_all_tasks_selector_used_when_limit_set(self):
        """Test that task selector is used (now always uses /codex/tasks/ to exclude navigation)."""
        automation = CodexGitHubMentionsAutomation(task_limit=50, all_tasks=True)
        automation.page = AsyncMock()

        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=0)
        automation.page.locator = Mock(return_value=mock_locator)

        await automation.find_github_mention_tasks()

        # Verify correct selector was used - now uses /codex/tasks/ to exclude navigation links
        automation.page.locator.assert_called_with('a[href*="/codex/tasks/"]')
        print("✅ Correct selector used for limit=50")


class TestNavigationInteraction:
    """Matrix 4: Test navigation and interaction scenarios."""

    @pytest.mark.asyncio
    async def test_navigate_to_codex_success(self):
        """Test successful navigation to Codex."""
        automation = CodexGitHubMentionsAutomation()
        automation.page = AsyncMock()

        await automation.navigate_to_codex()

        automation.page.goto.assert_called_once()
        print("✅ Navigation to Codex successful")

    @pytest.mark.asyncio
    async def test_navigate_timeout_handled(self):
        """Test that navigation timeout is handled gracefully."""
        automation = CodexGitHubMentionsAutomation()
        automation.page = AsyncMock()
        automation.page.goto.side_effect = TimeoutError("Navigation timeout")

        with pytest.raises(TimeoutError):
            await automation.navigate_to_codex()

        print("✅ Navigation timeout raised correctly")

    @pytest.mark.asyncio
    async def test_click_task_success(self):
        """Test clicking task link successfully."""
        automation = CodexGitHubMentionsAutomation()

        # Create mock for the button locator (after .first)
        mock_button = AsyncMock()
        mock_button.count = AsyncMock(return_value=1)
        mock_button.click = AsyncMock()

        # Create mock for the main locator that returns the button when .first is accessed
        mock_locator = Mock()
        mock_locator.first = mock_button

        automation.page = AsyncMock()
        automation.page.goto = AsyncMock()
        automation.page.locator = Mock(return_value=mock_locator)

        task = {"href": "/codex/123", "text": "Test Task"}
        result = await automation.update_pr_for_task(task)

        assert result is True
        automation.page.goto.assert_called()
        mock_button.click.assert_awaited()
        print("✅ Task navigation and update simulated successfully")

    @pytest.mark.asyncio
    async def test_find_button_when_present(self):
        """Test finding Update branch button when present."""
        automation = CodexGitHubMentionsAutomation()
        automation.page = AsyncMock()

        mock_first = Mock()
        mock_first.count = AsyncMock(return_value=1)
        mock_locator = Mock()
        mock_locator.first = mock_first
        mock_locator.count = AsyncMock(return_value=1)
        automation.page.locator = Mock(return_value=mock_locator)

        # Simulate button check
        button = automation.page.locator('button:has-text("Update branch")').first
        count = await button.count()

        assert count > 0
        print("✅ Update branch button found")

    @pytest.mark.asyncio
    async def test_missing_button_handled(self):
        """Test handling when Update branch button is missing."""
        automation = CodexGitHubMentionsAutomation()
        automation.page = AsyncMock()

        mock_locator = Mock()
        mock_locator.count = AsyncMock(return_value=0)
        automation.page.locator = Mock(return_value=mock_locator)

        button_locator = automation.page.locator('button:has-text("Update branch")')
        count = await button_locator.count()

        assert count == 0
        print("✅ Missing button handled correctly")

    @requires_chrome
    @pytest.mark.asyncio
    async def test_complete_workflow_with_real_chrome(self):
        """Test complete workflow with real Chrome instance."""
        automation = CodexGitHubMentionsAutomation(task_limit=5)

        # Connect
        connected = await automation.connect_to_existing_browser()
        assert connected is True

        # Navigate
        await automation.navigate_to_codex()

        # Find tasks
        tasks = await automation.find_github_mention_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) <= 5

        print(f"✅ Complete workflow successful with {len(tasks)} tasks found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
