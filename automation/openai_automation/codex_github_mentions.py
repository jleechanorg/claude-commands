#!/usr/bin/env python3
"""
OpenAI Codex GitHub Mentions Automation

Connects to existing Chrome browser, logs into OpenAI, finds all "github mention"
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
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from playwright_stealth import Stealth


# Set up logging to /tmp
def setup_logging():
    """Set up logging to /tmp directory."""
    log_dir = Path("/tmp/automate_codex_update")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "codex_automation.log"

    # Create logger
    logger = logging.getLogger("codex_automation")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


logger = setup_logging()


class CodexGitHubMentionsAutomation:
    """Automates finding and updating GitHub mention tasks in OpenAI Codex."""

    def __init__(self, cdp_url: str = "http://localhost:9222", headless: bool = False, task_limit: int | None = 50):
        """
        Initialize the automation.

        Args:
            cdp_url: Chrome DevTools Protocol WebSocket URL
            headless: Run in headless mode (not recommended - may be detected)
            task_limit: Maximum number of tasks to process (default: 50, None = all Github Mention tasks)
        """
        self.cdp_url = cdp_url
        self.headless = headless
        self.task_limit = task_limit
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def connect_to_existing_browser(self):
        """Connect to existing Chrome browser via CDP."""
        print(f"🔌 Connecting to existing Chrome at {self.cdp_url}...")
        logger.info(f"Connecting to Chrome at {self.cdp_url}")

        playwright = await async_playwright().start()

        try:
            # Connect to existing browser (not headless, uses real profile)
            self.browser = await playwright.chromium.connect_over_cdp(self.cdp_url)
            print(f"✅ Connected to Chrome (version: {self.browser.version})")
            logger.info(f"Successfully connected to Chrome (version: {self.browser.version})")

            # Use existing context or create new one
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                print(f"📱 Using existing context with {len(self.context.pages)} page(s)")
            else:
                self.context = await self.browser.new_context()
                print("📱 Created new browser context")

            # Get or create a page
            if self.context.pages:
                self.page = self.context.pages[0]
                print(f"📄 Using existing page: {await self.page.title()}")
            else:
                self.page = await self.context.new_page()
                print("📄 Created new page")

            # Apply stealth patches to mask automation
            print("🥷 Applying stealth patches to evade detection...")
            stealth_config = Stealth(
                navigator_webdriver=True,
                chrome_runtime=True,
                navigator_languages=True,
                navigator_vendor=True,
                navigator_platform=True,
                webgl_vendor=True,
                navigator_user_agent=True
            )
            await stealth_config.apply_async(self.page)
            logger.info("Applied stealth patches to page")

            return True

        except Exception as e:
            print(f"❌ Failed to connect to Chrome: {e}")
            print("\n💡 Make sure Chrome is running with remote debugging:")
            print("   ./scripts/openai_automation/start_chrome_debug.sh")
            return False

    async def ensure_openai_login(self):
        """Navigate to OpenAI and ensure user is logged in."""
        print("\n🔐 Checking OpenAI login status...")

        # Create or use existing page
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

        # Navigate to OpenAI
        await self.page.goto("https://chatgpt.com/", wait_until="networkidle")
        await asyncio.sleep(2)

        # Check if logged in by looking for user menu or login button
        try:
            # Look for user avatar/menu (indicates logged in)
            user_menu = await self.page.wait_for_selector(
                'button[aria-label*="User"], [data-testid="profile-button"]',
                timeout=5000
            )
            print("✅ Already logged in to OpenAI")
            return True

        except Exception:
            # Look for login button (not logged in)
            try:
                login_btn = await self.page.wait_for_selector(
                    'text="Log in", button:has-text("Log in")',
                    timeout=3000
                )
                print("⚠️  Not logged in to OpenAI")
                print("\n🚨 MANUAL ACTION REQUIRED:")
                print("   1. Log in to OpenAI in the browser window")
                print("   2. Wait for login to complete")
                print("   3. Press Enter here to continue...")
                input()
                return await self.ensure_openai_login()

            except Exception:
                print("⚠️  Could not determine login status")
                print("   Assuming you're logged in and continuing...")
                return True

    async def navigate_to_codex(self):
        """Navigate to OpenAI Codex tasks page."""
        print("\n📍 Navigating to Codex...")
        logger.info("Navigating to Codex...")

        codex_url = "https://chatgpt.com/codex"

        await self.page.goto(codex_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for Cloudflare challenge to complete
        print("   Waiting for Cloudflare challenge (if any)...")
        max_wait = 30  # 30 seconds max wait
        waited = 0
        while waited < max_wait:
            title = await self.page.title()
            if title != "Just a moment...":
                break
            await asyncio.sleep(2)
            waited += 2
            if waited % 10 == 0:
                print(f"   Still waiting... ({waited}s)")

        # Extra wait for dynamic content to load after Cloudflare
        await asyncio.sleep(5)

        final_title = await self.page.title()
        print(f"✅ Navigated to {codex_url} (title: {final_title})")
        logger.info(f"Successfully navigated to {codex_url} (title: {final_title})")

    async def find_github_mention_tasks(self) -> List:
        """
        Find task links in Codex.

        If task_limit is set, finds ALL tasks (limited to first N).
        Otherwise, finds only tasks containing 'Github Mention:'.

        Returns:
            List of task link elements
        """
        try:
            # Wait for tasks to load on the page
            print("   Waiting for content to load...")
            await asyncio.sleep(5)  # Extra wait for dynamic content

            if self.task_limit is not None:
                # Find ALL tasks (limited to first N)
                print(f"\n🔍 Searching for first {self.task_limit} tasks...")

                # Find all task links - they typically have href and are clickable
                # Adjust selector based on Codex UI structure
                locator = self.page.locator('a[href*="/codex/"]')
                all_task_links = await locator.all()

                if not all_task_links:
                    print("⚠️  No tasks found")
                    print("   Retrying with longer wait...")
                    await asyncio.sleep(5)
                    locator = self.page.locator('a[href*="/codex/"]')
                    all_task_links = await locator.all()

                # Limit to first N tasks
                task_links = all_task_links[:self.task_limit]
                print(f"✅ Found {len(all_task_links)} total tasks, limiting to first {len(task_links)}")
                logger.info(f"Found {len(all_task_links)} total tasks, limiting to first {len(task_links)}")
                return task_links
            else:
                # Original behavior: Find only "Github Mention:" tasks
                print("\n🔍 Searching for 'Github Mention:' tasks...")

                locator = self.page.locator('a:has-text("Github Mention:")')
                task_links = await locator.all()

                if not task_links:
                    print("⚠️  No tasks found with 'Github Mention:'")
                    print("   Retrying with longer wait...")
                    await asyncio.sleep(5)
                    locator = self.page.locator('a:has-text("Github Mention:")')
                    task_links = await locator.all()

                    if not task_links:
                        print("⚠️  Still no tasks found")
                        return []

                print(f"✅ Found {len(task_links)} task(s) with 'Github Mention:'")
                logger.info(f"Found {len(task_links)} 'Github Mention:' tasks")
                return task_links

        except Exception as e:
            print(f"❌ Error finding tasks: {e}")
            logger.error(f"Error finding tasks: {e}")
            return []

    async def update_pr_for_task(self, task_link):
        """
        Open task and click 'GitHub Comment' button to update the PR.

        Args:
            task_link: The task link element to click
        """
        try:
            # Get task title for logging
            task_text = await task_link.text_content()
            task_text = task_text.strip()[:80]

            # Click the task link to open it
            await task_link.click()
            await asyncio.sleep(3)  # Wait for task page to load

            # Look for "Update branch" button
            update_branch_btn = self.page.locator('button:has-text("Update branch")').first

            # Check if button exists
            if await update_branch_btn.count() > 0:
                await update_branch_btn.click()
                print("  ✅ Clicked 'Update branch' button")
                await asyncio.sleep(2)

                # Navigate back to Codex main page
                await self.page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)

                return True
            else:
                print("  ⚠️  'Update branch' button not found")
                # Go back anyway
                await self.page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                return False

        except Exception as e:
            print(f"  ❌ Failed to update PR: {e}")
            # Try to go back to Codex page
            try:
                await self.page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
            except:
                pass
            return False

    async def process_all_github_mentions(self):
        """Find all GitHub mention tasks and update their PRs."""
        tasks = await self.find_github_mention_tasks()

        if not tasks:
            print("\n🎯 No GitHub mention tasks to process")
            logger.info("No tasks found to process")
            return 0

        print(f"\n🎯 Processing {len(tasks)} task(s)...")
        success_count = 0

        for i, task in enumerate(tasks, 1):
            print(f"\n📝 Task {i}/{len(tasks)}:")

            # Get task title/description for logging
            try:
                task_text = await task.text_content()
                preview = task_text[:100] + "..." if len(task_text) > 100 else task_text
                print(f"   {preview}")
            except:
                print("   (Could not extract task text)")

            # Update PR for this task
            if await self.update_pr_for_task(task):
                success_count += 1

            # Small delay between tasks
            await asyncio.sleep(1)

        print(f"\n✅ Successfully updated {success_count}/{len(tasks)} task(s)")
        logger.info(f"Successfully updated {success_count}/{len(tasks)} tasks")
        return success_count

    async def run(self):
        """Main automation workflow."""
        print("🤖 OpenAI Codex GitHub Mentions Automation")
        print("=" * 60)
        logger.info("Starting Codex automation workflow")

        try:
            # Step 1: Connect to existing browser
            if not await self.connect_to_existing_browser():
                return False

            # Step 2: Skip login check - user is already logged in
            print("\n✅ Assuming already logged in to OpenAI")

            # Step 3: Check if already on Codex page, otherwise navigate
            current_url = self.page.url
            if "chatgpt.com/codex" in current_url:
                print(f"\n✅ Already on Codex page: {current_url}")
                logger.info(f"Already on Codex page: {current_url}")
                # Just wait a bit for content to load
                await asyncio.sleep(3)
            else:
                print(f"\n⚠️  Not on Codex page (currently: {current_url})")
                print("💡 TIP: Manually navigate to https://chatgpt.com/codex in your browser")
                print("   to avoid Cloudflare challenges, then run this automation.")
                await self.navigate_to_codex()

            # Step 4: Process all GitHub mention tasks
            count = await self.process_all_github_mentions()

            print("\n" + "=" * 60)
            print(f"✅ Automation complete! Processed {count} task(s)")
            logger.info(f"Automation completed successfully - processed {count} task(s)")
            return True

        except KeyboardInterrupt:
            print("\n⚠️  Automation interrupted by user")
            logger.warning("Automation interrupted by user")
            return False

        except Exception as e:
            print(f"\n❌ Automation failed: {e}")
            logger.error(f"Automation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Keep browser open (we're using existing instance)
            print("\n💡 Browser left open (using existing instance)")

    async def cleanup(self):
        """Clean up resources (but keep browser open)."""
        # Don't close browser - we're connected to existing instance
        pass


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
        "--cdp-host",
        default="localhost",
        help="CDP host (default: localhost)"
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

    args = parser.parse_args()

    # Build CDP URL
    cdp_url = f"http://{args.cdp_host}:{args.cdp_port}"

    # Run automation
    automation = CodexGitHubMentionsAutomation(cdp_url=cdp_url, task_limit=args.limit)

    try:
        success = await automation.run()
        sys.exit(0 if success else 1)
    finally:
        await automation.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
