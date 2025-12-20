#!/usr/bin/env python3
"""
OpenAI Codex GitHub Mentions Automation

Connects to existing Chrome browser, logs into OpenAI, finds all "GitHub mention"
tasks in Codex, and clicks "Update PR" on each one.

Uses Chrome DevTools Protocol (CDP) to connect to existing browser instance,
avoiding detection as automation.

Usage:
    # Start Chrome with remote debugging (if not already running):
    ./scripts/openai_automation/start_chrome_debug.sh

    # Run this script:
    python3 scripts/openai_automation/codex_github_mentions.py

    # With custom CDP port:
    python3 scripts/openai_automation/codex_github_mentions.py --cdp-port 9222
"""

import argparse
import asyncio
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

import logging_util

logger = logging_util.getLogger(__name__)

# Storage state path for persisting authentication.
# This file contains sensitive session data; enforce restrictive permissions.
AUTH_STATE_PATH = Path.home() / ".chatgpt_codex_auth_state.json"


def _ensure_auth_state_permissions(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.chmod(0o600)
    except OSError as exc:
        logger.warning(
            "Could not ensure secure permissions on auth state file %s: %s",
            path,
            exc,
        )


class CodexGitHubMentionsAutomation:
    """Automates finding and updating GitHub mention tasks in OpenAI Codex."""

    def __init__(
        self,
        cdp_url: Optional[str] = None,
        headless: bool = False,
        task_limit: Optional[int] = 50,
        user_data_dir: Optional[str] = None,
        debug: bool = False,
        all_tasks: bool = False,
    ):
        """
        Initialize the automation.

        Args:
            cdp_url: Chrome DevTools Protocol WebSocket URL (None = launch new browser)
            headless: Run in headless mode (not recommended - may be detected)
            task_limit: Maximum number of tasks to process (default: 50, None = all GitHub Mention tasks)
            user_data_dir: Chrome profile directory for persistent login (default: ~/.chrome-codex-automation)
            debug: Enable debug mode (screenshots, HTML dump, keep browser open)
        """
        self.cdp_url = cdp_url
        self.headless = headless
        self.task_limit = task_limit
        self.user_data_dir = user_data_dir or str(Path.home() / ".chrome-codex-automation")
        self.debug = debug
        self.all_tasks = all_tasks
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start_playwright(self) -> Playwright:
        if self.playwright is None:
            self.playwright = await async_playwright().start()
        return self.playwright

    async def connect_to_existing_browser(self) -> bool:
        """Connect to an existing Chrome instance over CDP."""
        await self.start_playwright()

        if not self.cdp_url:
            self.cdp_url = "http://127.0.0.1:9222"

        logger.info("🔌 Connecting to existing Chrome at %s...", self.cdp_url)

        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            logger.info("✅ Connected to Chrome (version: %s)", self.browser.version)

            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                logger.info("📱 Using existing context with %s page(s)", len(self.context.pages))
            else:
                self.context = await self.browser.new_context()
                logger.info("📱 Created new browser context")

            # Always create a new page to avoid browser UI elements (Omnibox, Extensions, etc.)
            self.page = await self.context.new_page()
            logger.info("📄 Created new page for automation")
            return True
        except (PlaywrightTimeoutError, PlaywrightError, OSError) as err:
            logger.warning("❌ Failed to connect via CDP: %s", err)
            return False

    async def setup(self) -> bool:
        """Set up browser connection (connect or launch new)."""
        await self.start_playwright()

        connected = False
        if self.cdp_url:
            connected = await self.connect_to_existing_browser()

        if not connected:
            # Check if we have saved authentication state
            storage_state = None
            if AUTH_STATE_PATH.exists():
                _ensure_auth_state_permissions(AUTH_STATE_PATH)
                logger.info("📂 Found saved authentication state at %s", AUTH_STATE_PATH)
                storage_state = str(AUTH_STATE_PATH)

            # Launch browser (not persistent context - use storage state instead)
            logger.info("🚀 Launching Chrome...")

            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
            )

            # Create context with storage state if available
            if storage_state:
                self.context = await self.browser.new_context(storage_state=storage_state)
                logger.info("✅ Restored previous authentication state")
            else:
                self.context = await self.browser.new_context()
                logger.info("🆕 Creating new authentication state (will save after login)")

            # Create page
            self.page = await self.context.new_page()

        return True

    async def ensure_openai_login(self):
        """Navigate to OpenAI and ensure user is logged in."""
        logger.info("🔐 Checking OpenAI login status...")

        # Create or use existing page
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

        # Navigate to OpenAI
        await self.page.goto("https://chatgpt.com/", wait_until="networkidle")
        await asyncio.sleep(2)

        try:
            await self.page.wait_for_selector(
                'button[aria-label*="User"], [data-testid="profile-button"]',
                timeout=5000,
            )
            logger.info("✅ Already logged in to OpenAI")

            # Save authentication state if not already saved
            if not AUTH_STATE_PATH.exists():
                await self.context.storage_state(path=str(AUTH_STATE_PATH))
                _ensure_auth_state_permissions(AUTH_STATE_PATH)
                logger.info("💾 Authentication state saved to %s", AUTH_STATE_PATH)

            return True
        except PlaywrightTimeoutError:
            try:
                await self.page.wait_for_selector(
                    'text="Log in", button:has-text("Log in")',
                    timeout=3000,
                )
                logger.warning("⚠️  Not logged in to OpenAI")

                # Check if running in non-interactive mode (cron/CI)
                if not sys.stdin.isatty():
                    logger.error(
                        "❌ ERROR: Authentication required but running in non-interactive mode"
                    )
                    logger.error(
                        "Solution: Log in manually via Chrome with CDP enabled, then run again"
                    )
                    logger.error("The script will save auth state to %s", AUTH_STATE_PATH)
                    return False

                logger.warning("🚨 MANUAL ACTION REQUIRED:")
                logger.warning("1. Log in to OpenAI in the browser window")
                logger.warning("2. Wait for login to complete")
                logger.warning("3. Press Enter here to continue...")
                input()

                logger.info("🔄 Re-checking OpenAI login status after manual login...")
                try:
                    await self.page.wait_for_selector(
                        'button[aria-label*="User"], [data-testid="profile-button"]',
                        timeout=5000,
                    )
                    await self.context.storage_state(path=str(AUTH_STATE_PATH))
                    _ensure_auth_state_permissions(AUTH_STATE_PATH)
                    logger.info(
                        "💾 New authentication state saved to %s",
                        AUTH_STATE_PATH,
                    )
                    return True
                except PlaywrightTimeoutError:
                    logger.error(
                        "❌ Still not logged in to OpenAI after manual login step"
                    )
                    return False

            except PlaywrightTimeoutError:
                logger.warning("⚠️  Could not determine login status")
                logger.warning("Assuming you're logged in and continuing...")
                return True
            except (PlaywrightError, OSError) as login_error:
                logger.warning(
                    "⚠️  Unexpected login detection error: %s",
                    login_error,
                )
                return False
        except (PlaywrightError, OSError) as user_menu_error:
            logger.warning(
                "⚠️  Unexpected login check error: %s",
                user_menu_error,
            )
            return False

    async def navigate_to_codex(self):
        """Navigate to OpenAI Codex tasks page."""
        logger.info("📍 Navigating to Codex...")

        codex_url = "https://chatgpt.com/codex"

        await self.page.goto(codex_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for Cloudflare challenge to complete
        logger.info("Waiting for Cloudflare challenge (if any)...")
        max_wait = 30  # 30 seconds max wait
        waited = 0
        while waited < max_wait:
            title = await self.page.title()
            if title != "Just a moment...":
                break
            await asyncio.sleep(2)
            waited += 2
            if waited % 10 == 0:
                logger.info("Still waiting... (%ss)", waited)

        # Extra wait for dynamic content to load after Cloudflare
        await asyncio.sleep(5)

        final_title = await self.page.title()
        logger.info(
            "✅ Navigated to %s (title: %s)",
            codex_url,
            final_title,
        )

    async def find_github_mention_tasks(self) -> list[dict[str, str]]:
        """
        Find task links in Codex.

        By default, filters for "GitHub Mention" tasks and applies task_limit.
        If all_tasks is True, collects the first N Codex tasks regardless of title.
        """
        if self.task_limit == 0:
            logger.warning("⚠️  Task limit set to 0 - skipping")
            return []

        try:
            logger.info("Waiting for content to load...")
            await asyncio.sleep(5)

            primary_selector = 'a[href*="/codex/tasks/"]'
            filtered_selector = f'{primary_selector}:has-text("GitHub Mention:")'
            selector_candidates = [primary_selector] if self.all_tasks else [
                filtered_selector,
                'a:has-text("GitHub Mention:")',
                primary_selector,
            ]

            locator_selector = selector_candidates[0]
            locator = self.page.locator(locator_selector)
            task_count = await locator.count()
            if task_count == 0 and len(selector_candidates) > 1:
                for candidate in selector_candidates[1:]:
                    locator = self.page.locator(candidate)
                    task_count = await locator.count()
                    if task_count > 0:
                        locator_selector = candidate
                        break
            logger.info("🔍 Searching for tasks using selector: %s", locator_selector)

            if self.debug:
                debug_dir = Path.home() / ".codex_automation_debug"
                debug_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = debug_dir / f"debug_screenshot_{timestamp}.png"
                html_path = debug_dir / f"debug_html_{timestamp}.html"

                await self.page.screenshot(path=str(screenshot_path))
                html_content = await self.page.content()
                html_path.write_text(html_content)

                logger.debug("🐛 Debug: Screenshot saved to %s", screenshot_path)
                logger.debug("🐛 Debug: HTML saved to %s", html_path)
                logger.debug("🐛 Debug: Current URL: %s", self.page.url)
                logger.debug("🐛 Debug: Page title: %s", await self.page.title())

            # Find all task links - use more specific selector to exclude navigation
            # Use /codex/tasks/ to exclude navigation links like Settings, Docs

            if task_count == 0:
                logger.warning("⚠️  No tasks found, retrying after short wait...")
                await asyncio.sleep(5)
                task_count = await locator.count()
                if task_count == 0:
                    logger.warning("⚠️  Still no tasks found")
                    return []

            limit = task_count if self.task_limit is None else min(task_count, self.task_limit)
            tasks: list[dict[str, str]] = []
            for idx in range(limit):
                item = locator.nth(idx)
                href = await item.get_attribute("href") or ""
                text = (await item.text_content()) or ""
                tasks.append({"href": href, "text": text})

            logger.info("✅ Prepared %s task link(s) for processing", len(tasks))
            logger.info("Prepared %s task link(s) using selector %s", len(tasks), locator_selector)
            return tasks

        except (PlaywrightError, PlaywrightTimeoutError, OSError) as err:
            logger.error("❌ Error finding tasks: %s", err)
            return []

    async def update_pr_for_task(self, task_link: dict[str, str]):
        """
        Open task and click 'Update branch' button to update the PR.

        Args:
            task_link: Mapping containing href and text preview for the task
        """
        href = task_link.get("href", "")
        task_text_raw = task_link.get("text", "")
        task_text = (task_text_raw or "").strip()[:80] or "(no text)"

        try:
            target_url = href if href.startswith("http") else f"https://chatgpt.com{href}"
            logger.info("Navigating to task: %s", task_text)
            await self.page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            update_branch_btn = self.page.locator('button:has-text("Update branch")').first

            if await update_branch_btn.count() > 0:
                await update_branch_btn.click()
                logger.info("✅ Clicked 'Update branch' button")
                await asyncio.sleep(2)
            else:
                logger.warning("⚠️  'Update branch' button not found")
                return False

            await self.page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            return True

        except (PlaywrightError, PlaywrightTimeoutError, OSError) as err:
            logger.error("❌ Failed to update PR: %s", err)
            try:
                await self.page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
            except (PlaywrightError, PlaywrightTimeoutError, OSError) as nav_err:
                logger.warning("⚠️ Failed to navigate back to Codex after error: %s", nav_err)
            return False

    async def process_all_github_mentions(self):
        """Find all GitHub mention tasks and update their PRs."""
        tasks = await self.find_github_mention_tasks()

        if not tasks:
            logger.info("🎯 No GitHub mention tasks to process")
            return 0

        logger.info("🎯 Processing %s task(s)...", len(tasks))
        success_count = 0

        for i, task in enumerate(tasks, 1):
            logger.info("📝 Task %s/%s:", i, len(tasks))

            try:
                raw_text = task.get("text", "") if isinstance(task, dict) else ""
                task_text = (raw_text or "").strip()
                preview = task_text[:100] + "..." if len(task_text) > 100 else (task_text or "(no text)")
                logger.info("%s", preview)
            except (AttributeError, TypeError) as text_error:
                logger.info("(Could not extract task text: %s)", text_error)

            if await self.update_pr_for_task(task):
                success_count += 1

            await asyncio.sleep(1)

        logger.info("✅ Successfully updated %s/%s task(s)", success_count, len(tasks))
        return success_count

    async def run(self):
        """Main automation workflow."""
        logger.info("🤖 OpenAI Codex GitHub Mentions Automation")
        logger.info("%s", "=" * 60)
        logger.info("Starting Codex automation workflow")

        try:
            # Step 1: Setup browser (connect or launch)
            await self.setup()

            # Step 2: Ensure logged in to OpenAI (will save auth state on first login)
            await self.ensure_openai_login()

            # Step 3: Navigate to Codex if not already there
            current_url = self.page.url
            if "chatgpt.com/codex" in current_url:
                logger.info("✅ Already on Codex page: %s", current_url)
                await asyncio.sleep(3)
            else:
                await self.navigate_to_codex()

            # Step 4: Process all GitHub mention tasks
            count = await self.process_all_github_mentions()

            logger.info("%s", "=" * 60)
            logger.info("✅ Automation complete! Processed %s task(s)", count)
            return True

        except KeyboardInterrupt:
            logger.warning("⚠️  Automation interrupted by user")
            return False

        except (PlaywrightError, PlaywrightTimeoutError, OSError) as err:
            logger.error("❌ Automation failed: %s", err)
            traceback.print_exc()
            return False

        finally:
            # Close context or browser depending on how it was created
            if self.debug:
                logger.info("🐛 Debug mode: Keeping browser open for inspection")
                logger.info("Press Ctrl+C to exit when done inspecting")
                try:
                    await asyncio.sleep(3600)  # Wait 1 hour for inspection
                except KeyboardInterrupt:
                    logger.info("🐛 Debug inspection complete")

            if not self.cdp_url and not self.debug:
                # Close both context and browser (we launched them both)
                logger.info("🔒 Closing browser (launched by automation)")
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
            else:
                logger.info("💡 Browser left open (CDP mode or debug mode)")

            await self.cleanup()

    async def cleanup(self):
        """Clean up Playwright client resources."""
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automate OpenAI Codex GitHub mention tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Default (connects to Chrome on port 9222)
    python3 %(prog)s

    # Custom CDP port
    python3 %(prog)s --cdp-port 9223

    # Verbose mode
    python3 %(prog)s --verbose
        """
    )

    parser.add_argument(
        "--cdp-port",
        type=int,
        default=9222,
        help="Chrome DevTools Protocol port (default: 9222)"
    )

    parser.add_argument(
        "--use-existing-browser",
        action="store_true",
        help="Connect to existing Chrome (requires start_chrome_debug.sh)"
    )

    parser.add_argument(
        "--cdp-host",
        default="127.0.0.1",
        help="CDP host (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of tasks to process (default: 50)"
    )

    parser.add_argument(
        "--all-tasks",
        action="store_true",
        help="Process all Codex tasks (not just GitHub Mention tasks)",
    )

    parser.add_argument(
        "--profile-dir",
        help="Chrome profile directory for persistent login (default: ~/.chrome-codex-automation)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode: take screenshots, save HTML, keep browser open"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    # Build CDP URL only if using existing browser
    cdp_url = f"http://{args.cdp_host}:{args.cdp_port}" if args.use_existing_browser else None

    # Run automation
    automation = CodexGitHubMentionsAutomation(
        cdp_url=cdp_url,
        task_limit=args.limit,
        user_data_dir=args.profile_dir,
        debug=args.debug,
        all_tasks=args.all_tasks,
    )

    try:
        success = await automation.run()
        sys.exit(0 if success else 1)
    finally:
        await automation.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
