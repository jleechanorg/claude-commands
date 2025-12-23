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
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)


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

        print(f"🔌 Connecting to existing Chrome at {self.cdp_url}...")
        logger.info(f"Connecting to Chrome at {self.cdp_url}")

        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            print(f"✅ Connected to Chrome (version: {self.browser.version})")
            logger.info(f"Successfully connected to Chrome (version: {self.browser.version})")

            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                print(f"📱 Using existing context with {len(self.context.pages)} page(s)")
            else:
                self.context = await self.browser.new_context()
                print("📱 Created new browser context")

            self.page = await self._select_existing_page()
            if self.page:
                print("📄 Reusing existing tab for automation")
            else:
                self.page = await self.context.new_page()
                print("📄 Created new page for automation")
            return True
        except Exception as e:
            print(f"❌ Failed to connect via CDP: {e}")
            logger.warning(f"CDP connection failed: {e}")
            return False

    async def _select_existing_page(self) -> Optional[Page]:
        """Reuse a ready ChatGPT/Codex tab, preferring Codex over generic chat."""
        if not self.context or not self.context.pages:
            return None

        async def is_ready(page: Page) -> bool:
            try:
                if page.is_closed():
                    return False
                title = await page.title()
                return title.strip().lower() != "just a moment..."
            except Exception:
                return False

        candidates = [page for page in self.context.pages if not page.is_closed()]

        for page in candidates:
            try:
                if "chatgpt.com/codex" in (page.url or "") and await is_ready(page):
                    return page
            except Exception:
                continue

        for page in candidates:
            try:
                if "chatgpt.com" in (page.url or "") and await is_ready(page):
                    return page
            except Exception:
                continue

        return None

    async def _ensure_page(self) -> bool:
        """Ensure there is an active page, creating one if needed."""
        try:
            if self.page and not self.page.is_closed():
                return True
        except Exception as exc:
            logger.debug(
                "Error while checking existing page state; attempting to create a new page: %s",
                exc,
            )

        if not self.context:
            return False

        try:
            self.page = await self.context.new_page()
            return True
        except Exception as exc:
            logger.debug("Failed to create new page: %s", exc)
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
                print(f"📂 Found saved authentication state at {AUTH_STATE_PATH}")
                logger.info(f"Loading authentication state from {AUTH_STATE_PATH}")
                storage_state = str(AUTH_STATE_PATH)

            # Launch browser (not persistent context - use storage state instead)
            print(f"🚀 Launching Chrome...")
            logger.info(f"Launching Chrome")

            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
            )

            # Create context with storage state if available
            if storage_state:
                self.context = await self.browser.new_context(storage_state=storage_state)
                print("✅ Restored previous authentication state")
                logger.info("Restored authentication state from storage")
            else:
                self.context = await self.browser.new_context()
                print("🆕 Creating new authentication state (will save after login)")
                logger.info("Creating new browser context")

            # Create page
            self.page = await self.context.new_page()

        return True

    async def ensure_openai_login(self):
        """Navigate to OpenAI and ensure user is logged in."""
        print("\n🔐 Checking OpenAI login status...")

        if not await self._ensure_page():
            print("❌ Unable to create browser page for login check")
            return False

        try:
            current_url = self.page.url or ""
        except Exception:
            current_url = ""

        if "chatgpt.com" not in current_url:
            try:
                await self.page.goto("https://chatgpt.com/", wait_until="networkidle")
            except PlaywrightTimeoutError:
                await self.page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        try:
            await self.page.wait_for_selector(
                'button[aria-label*="User"], [data-testid="profile-button"]',
                timeout=5000,
            )
            print("✅ Already logged in to OpenAI")

            # Save authentication state if not already saved
            if not AUTH_STATE_PATH.exists():
                await self.context.storage_state(path=str(AUTH_STATE_PATH))
                _ensure_auth_state_permissions(AUTH_STATE_PATH)
                print(f"💾 Authentication state saved to {AUTH_STATE_PATH}")
                logger.info(f"Saved authentication state to {AUTH_STATE_PATH}")

            return True
        except PlaywrightTimeoutError:
            try:
                await self.page.wait_for_selector(
                    'text="Log in", button:has-text("Log in")',
                    timeout=3000,
                )
                print("⚠️  Not logged in to OpenAI")

                # Check if running in non-interactive mode (cron/CI)
                if not sys.stdin.isatty():
                    print("❌ ERROR: Authentication required but running in non-interactive mode")
                    print("   Solution: Log in manually via Chrome with CDP enabled, then run again")
                    print(f"   The script will save auth state to {AUTH_STATE_PATH}")
                    return False

                print("\n🚨 MANUAL ACTION REQUIRED:")
                print("   1. Log in to OpenAI in the browser window")
                print("   2. Wait for login to complete")
                print("   3. Press Enter here to continue...")
                input()

                print("🔄 Re-checking OpenAI login status after manual login...")
                try:
                    await self.page.wait_for_selector(
                        'button[aria-label*="User"], [data-testid="profile-button"]',
                        timeout=5000,
                    )
                    await self.context.storage_state(path=str(AUTH_STATE_PATH))
                    _ensure_auth_state_permissions(AUTH_STATE_PATH)
                    print(f"💾 New authentication state saved to {AUTH_STATE_PATH}")
                    logger.info(f"Saved new authentication state after manual login to {AUTH_STATE_PATH}")
                    return True
                except PlaywrightTimeoutError:
                    print("❌ Still not logged in to OpenAI after manual login step")
                    return False

            except PlaywrightTimeoutError:
                print("⚠️  Could not determine login status")
                print("   Assuming you're logged in and continuing...")
                return True
            except Exception as login_error:
                print(f"⚠️  Unexpected login detection error: {login_error}")
                return False
        except Exception as user_menu_error:
            print(f"⚠️  Unexpected login check error: {user_menu_error}")
            return False

    async def navigate_to_codex(self):
        """Navigate to OpenAI Codex tasks page."""
        print("\n📍 Navigating to Codex...")
        logger.info("Navigating to Codex...")

        codex_url = "https://chatgpt.com/codex"

        if not await self._ensure_page():
            raise RuntimeError("No active browser page available for Codex navigation")

        await self.page.goto(codex_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for Cloudflare challenge to complete
        print("   Waiting for Cloudflare challenge (if any)...")
        max_wait = 90  # 90 seconds max wait
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

    async def find_github_mention_tasks(self) -> List[Dict[str, str]]:
        """
        Find task links in Codex.

        By default, filters for "GitHub Mention" tasks and applies task_limit.
        If all_tasks is True, collects the first N Codex tasks regardless of title.
        """
        if self.task_limit == 0:
            print("⚠️  Task limit set to 0 - skipping")
            return []

        try:
            print("   Waiting for content to load...")
            await asyncio.sleep(5)

            primary_selector = 'a[href*="/codex/tasks/"]'
            filtered_selector = f'{primary_selector}:has-text("GitHub Mention:")'
            selector_candidates = [primary_selector] if self.all_tasks else [
                filtered_selector,
                'a:has-text("GitHub Mention:")',
                primary_selector,
            ]

            if self.debug:
                debug_dir = Path("/tmp/automate_codex_update")
                debug_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = debug_dir / f"debug_screenshot_{timestamp}.png"
                html_path = debug_dir / f"debug_html_{timestamp}.html"

                await self.page.screenshot(path=str(screenshot_path))
                html_content = await self.page.content()
                html_path.write_text(html_content)

                print(f"🐛 Debug: Screenshot saved to {screenshot_path}")
                print(f"🐛 Debug: HTML saved to {html_path}")
                print(f"🐛 Debug: Current URL: {self.page.url}")
                print(f"🐛 Debug: Page title: {await self.page.title()}")

            per_tab_limit = None if self.task_limit is None else self.task_limit
            tasks = await self._collect_task_links(selector_candidates, per_tab_limit, tab_label="Tasks")

            if await self._switch_to_tab("Code reviews"):
                code_review_tasks = await self._collect_task_links(
                    selector_candidates,
                    per_tab_limit,
                    tab_label="Code reviews",
                )
                tasks.extend(code_review_tasks)

            if not tasks:
                print("⚠️  Still no tasks found")
                return []

            deduped: List[Dict[str, str]] = []
            seen: Set[str] = set()
            for task in tasks:
                href = task.get("href", "")
                if not href or href in seen:
                    continue
                seen.add(href)
                deduped.append(task)

            if self.task_limit is not None:
                deduped = deduped[: self.task_limit]

            print(f"✅ Prepared {len(deduped)} task link(s) for processing")
            logger.info(f"Prepared {len(deduped)} task link(s) across tabs")
            return deduped

        except Exception as e:
            print(f"❌ Error finding tasks: {e}")
            logger.error(f"Error finding tasks: {e}")
            return []

    async def _collect_task_links(
        self,
        selector_candidates: List[str],
        limit: Optional[int],
        tab_label: str,
    ) -> List[Dict[str, str]]:
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

        print(f"\n🔍 Searching for tasks in {tab_label} using selector: {locator_selector}")

        if task_count == 0:
            print("⚠️  No tasks found, retrying after short wait...")
            await asyncio.sleep(5)
            task_count = await locator.count()
            if task_count == 0:
                return []

        local_limit = task_count if limit is None else min(task_count, limit)
        tasks: List[Dict[str, str]] = []
        for idx in range(local_limit):
            item = locator.nth(idx)
            href = await item.get_attribute("href") or ""
            text = (await item.text_content()) or ""
            tasks.append({"href": href, "text": text})
        return tasks

    async def _switch_to_tab(self, label: str) -> bool:
        selectors = [
            f'button:has-text("{label}")',
            f'a:has-text("{label}")',
            f'[role="tab"]:has-text("{label}")',
        ]
        for selector in selectors:
            locator = self.page.locator(selector)
            try:
                if await locator.count() > 0:
                    await locator.first.click()
                    await asyncio.sleep(2)
                    return True
            except Exception as exc:
                logger.debug("Failed to switch to tab %s with %s: %s", label, selector, exc)
                continue
        logger.debug("Unable to switch to tab %s using selectors %s", label, selectors)
        return False

    async def update_pr_for_task(self, task_link: Dict[str, str]):
        """
        Open task and click 'Update branch' button to update the PR.

        Args:
            task_link: Mapping containing href and text preview for the task
        """
        href = task_link.get("href", "")
        task_text_raw = task_link.get("text", "")
        task_text = (task_text_raw or "").strip()[:80] or "(no text)"

        target_url = href if href.startswith("http") else f"https://chatgpt.com{href}"

        for attempt in range(2):
            if not await self._ensure_page():
                print("  ❌ No active browser page available to update task")
                if attempt == 0:
                    continue
                return False

            try:
                print(f"   Navigating to task: {task_text}")
                await self.page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)

                update_branch_locator = self.page.locator('button:has-text("Update branch")')

                if await update_branch_locator.count() > 0:
                    await update_branch_locator.first.click()
                    print("  ✅ Clicked 'Update branch' button")
                    await asyncio.sleep(2)
                else:
                    print("  ⚠️  'Update branch' button not found")
                    return False

            except Exception as e:
                error_text = str(e)
                print(f"  ❌ Failed to update PR: {e}")
                if "Target page, context or browser has been closed" in error_text and attempt == 0:
                    print("  🔄 Page was closed; reopening a new tab and retrying...")
                    continue
                return False

            try:
                await self.page.goto("https://chatgpt.com/codex", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
            except Exception as nav_err:
                print(f"  ⚠️ Failed to navigate back to Codex after update: {nav_err}")
            return True

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

            try:
                raw_text = task.get("text", "") if isinstance(task, dict) else ""
                task_text = (raw_text or "").strip()
                preview = task_text[:100] + "..." if len(task_text) > 100 else (task_text or "(no text)")
                print(f"   {preview}")
            except Exception as text_error:
                print(f"   (Could not extract task text: {text_error})")

            if await self.update_pr_for_task(task):
                success_count += 1

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
            # Step 1: Setup browser (connect or launch)
            await self.setup()

            # Step 2: Ensure logged in to OpenAI (will save auth state on first login)
            logged_in = await self.ensure_openai_login()
            if not logged_in:
                print("\n❌ Failed to verify OpenAI login; aborting automation.")
                logger.error("Failed to verify OpenAI login; aborting automation.")
                return False

            # Step 3: Navigate to Codex if not already on tasks list
            current_url = self.page.url
            if "chatgpt.com/codex" in current_url and not self._is_task_detail_url(current_url):
                print(f"\n✅ Already on Codex page: {current_url}")
                logger.info(f"Already on Codex page: {current_url}")
                await asyncio.sleep(3)
            else:
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
            traceback.print_exc()
            return False

        finally:
            # Close context or browser depending on how it was created
            if self.debug:
                print("\n🐛 Debug mode: Keeping browser open for inspection")
                print("   Press Ctrl+C to exit when done inspecting")
                try:
                    await asyncio.sleep(3600)  # Wait 1 hour for inspection
                except KeyboardInterrupt:
                    print("\n🐛 Debug inspection complete")

            if not self.cdp_url and not self.debug:
                # Close both context and browser (we launched them both)
                print("\n🔒 Closing browser (launched by automation)")
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
            else:
                print("\n💡 Browser left open (CDP mode or debug mode)")

            await self.cleanup()

    async def cleanup(self):
        """Clean up Playwright client resources."""
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def _is_task_detail_url(self, url: str) -> bool:
        return "/codex/tasks/" in url and "task_" in url


def _format_cdp_host_for_url(host: str) -> str:
    if ":" in host and not (host.startswith("[") and host.endswith("]")):
        return f"[{host}]"
    return host


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
    cdp_host = _format_cdp_host_for_url(args.cdp_host)
    cdp_url = f"http://{cdp_host}:{args.cdp_port}" if args.use_existing_browser else None

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
