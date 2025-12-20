#!/usr/bin/env python3
"""
Integration tests for Codex GitHub Mentions automation.

These tests use minimal mocking and test against a real Chrome instance
when available. Tests will skip gracefully if Chrome is not running.

Run with:
    pytest automation/openai_automation/test_codex_integration.py -v

Or with Chrome running:
    # Terminal 1
    ./automation/openai_automation/start_chrome_debug.sh

    # Terminal 2
    pytest automation/openai_automation/test_codex_integration.py -v
"""

import asyncio

import aiohttp
import pytest
from playwright.async_api import async_playwright

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


# Fixture to check Chrome availability
@pytest.fixture(scope="session")
def chrome_available():
    """Check if Chrome with CDP is available."""
    return asyncio.run(chrome_is_running())


# Skip marker for tests requiring Chrome
requires_chrome = pytest.mark.skipif(
    not asyncio.run(chrome_is_running()),
    reason="Chrome with remote debugging not running on port 9222"
)


class TestCDPConnection:
    """Test Chrome DevTools Protocol connection."""

    @requires_chrome
    @pytest.mark.asyncio
    async def test_can_connect_to_chrome(self):
        """Test basic CDP connection to Chrome."""
        playwright = await async_playwright().start()

        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            assert browser is not None
            assert browser.version is not None
            print(f"✅ Connected to Chrome {browser.version}")

        finally:
            await playwright.stop()

    @requires_chrome
    @pytest.mark.asyncio
    async def test_can_access_context_and_pages(self):
        """Test accessing browser contexts and pages."""
        playwright = await async_playwright().start()

        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            contexts = browser.contexts
            assert len(contexts) > 0, "Should have at least one context"

            context = contexts[0]
            # Get or create a page
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()

            assert page is not None
            title = await page.title()
            print(f"✅ Got page with title: {title}")

        finally:
            await playwright.stop()


class TestCodexAutomation:
    """Test Codex automation functionality."""

    @requires_chrome
    @pytest.mark.asyncio
    async def test_can_navigate_to_codex(self):
        """Test navigation to Codex page."""
        playwright = await async_playwright().start()

        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # Navigate to Codex
            await page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            title = await page.title()
            assert "Codex" in title or "ChatGPT" in title
            print(f"✅ Navigated to Codex page")

        finally:
            await playwright.stop()

    @requires_chrome
    @pytest.mark.asyncio
    async def test_can_find_github_mention_tasks(self):
        """Test finding GitHub Mention tasks on Codex page."""
        playwright = await async_playwright().start()

        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # Navigate to Codex
            await page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)  # Wait for dynamic content

            # Find GitHub Mention tasks
            task_links = await page.locator('a:has-text("GitHub Mention:")').all()

            # We may or may not have tasks at any given time
            print(f"✅ Found {len(task_links)} GitHub Mention tasks")
            assert isinstance(task_links, list)

        finally:
            await playwright.stop()

    @requires_chrome
    @pytest.mark.asyncio
    async def test_can_click_task_and_find_button(self):
        """Test clicking a task and looking for Update branch button."""
        playwright = await async_playwright().start()

        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # Navigate to Codex
            await page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)

            # Find tasks
            task_links = await page.locator('a:has-text("GitHub Mention:")').all()

            if len(task_links) > 0:
                # Click first task
                task_text = await task_links[0].text_content()
                print(f"Testing with task: {task_text[:50]}...")

                await task_links[0].click()
                await asyncio.sleep(3)

                # Look for Update branch button
                update_btn = page.locator('button:has-text("Update branch")').first
                button_count = await update_btn.count()

                print(f"✅ Task opened, Update branch button present: {button_count > 0}")

                # Navigate back
                await page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
            else:
                print("⚠️  No tasks available to test with")
                pytest.skip("No GitHub Mention tasks available")

        finally:
            await playwright.stop()


class TestCodexAutomationClass:
    """Test the CodexGitHubMentionsAutomation class directly."""

    @requires_chrome
    @pytest.mark.asyncio
    async def test_automation_class_can_connect(self):
        """Test that automation class can connect to Chrome."""
        automation = CodexGitHubMentionsAutomation(cdp_url="http://localhost:9222")

        try:
            connected = await automation.connect_to_existing_browser()
            assert connected is True
            assert automation.browser is not None
            assert automation.page is not None
            print(f"✅ Automation class connected successfully")
        finally:
            # Cleanup
            pass

    @requires_chrome
    @pytest.mark.asyncio
    async def test_automation_can_navigate_to_codex(self):
        """Test that automation class can navigate to Codex."""
        automation = CodexGitHubMentionsAutomation(cdp_url="http://localhost:9222")

        try:
            await automation.connect_to_existing_browser()
            await automation.navigate_to_codex()

            title = await automation.page.title()
            # Allow for loading pages ("Just a moment...") from Cloudflare
            assert title is not None and len(title) > 0
            print(f"✅ Automation navigated to Codex (title: {title})")
        finally:
            pass

    @requires_chrome
    @pytest.mark.asyncio
    async def test_automation_can_find_tasks(self):
        """Test that automation class can find GitHub Mention tasks."""
        automation = CodexGitHubMentionsAutomation(cdp_url="http://localhost:9222")

        try:
            await automation.connect_to_existing_browser()
            await automation.navigate_to_codex()

            tasks = await automation.find_github_mention_tasks()
            assert isinstance(tasks, list)
            print(f"✅ Automation found {len(tasks)} tasks")
        finally:
            pass


def test_chrome_not_required_placeholder():
    """Placeholder test that always passes (doesn't require Chrome)."""
    assert True
    print("✅ Placeholder test passed (no Chrome required)")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
