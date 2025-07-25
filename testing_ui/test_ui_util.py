#!/usr/bin/env python3
"""
Common utilities for UI tests using Playwright.
Provides reusable functions for browser setup, navigation, and common test patterns.
"""

import os
import sys
from collections.abc import Callable
from typing import Any

from playwright.sync_api import Browser, Page, sync_playwright

import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(__file__))
from screenshot_utils import take_screenshot

# Import centralized configuration  
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from testing_util import TestConfig, TestType

# Default test configuration (now using centralized config)
DEFAULT_TEST_USER = TestConfig.DEFAULT_TEST_USER_ID
DEFAULT_PORT = TestConfig.get_server_config(TestType.BROWSER).base_port
DEFAULT_HEADLESS = False
DEFAULT_TIMEOUT = TestConfig.LONG_TIMEOUT_MS  # 30 seconds


def setup_browser(
    headless: bool = DEFAULT_HEADLESS, viewport: dict[str, int] | None = None
):
    """
    Set up a browser instance with common configuration.

    Args:
        headless: Whether to run browser in headless mode
        viewport: Optional viewport size (default: {'width': 1280, 'height': 720})

    Returns:
        tuple: (playwright, browser, page) objects
    """
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)

    # Set default viewport if not provided
    if viewport is None:
        viewport = {"width": 1280, "height": 720}

    page = browser.new_page(viewport=viewport)

    # Set default timeout
    page.set_default_timeout(DEFAULT_TIMEOUT)

    return p, browser, page


def navigate_to_page(
    page: Page,
    path: str = "",
    port: int = DEFAULT_PORT,
    test_mode: bool = True,
    test_user_id: str = DEFAULT_TEST_USER,
    wait_for_load: bool = True,
):
    """
    Navigate to a page with test mode parameters.

    Args:
        page: Playwright page object
        path: Path to navigate to (e.g., "new-campaign", "dashboard")
        port: Port number for localhost
        test_mode: Whether to enable test mode
        test_user_id: Test user ID to use
        wait_for_load: Whether to wait for network idle state

    Returns:
        str: The URL navigated to
    """
    # Build URL
    url = f"http://localhost:{port}"
    if path:
        url += f"/{path}"

    # Add test mode parameters
    if test_mode:
        separator = "?" if "?" not in url else "&"
        url += f"{separator}test_mode=true&test_user_id={test_user_id}"

    # Navigate
    page.goto(url)

    # Wait for load
    if wait_for_load:
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)  # Extra safety timeout

    return url


def enable_console_logging(page: Page, prefix: str = "Console:"):
    """
    Enable console logging for debugging.

    Args:
        page: Playwright page object
        prefix: Prefix to add to console messages
    """
    page.on("console", lambda msg: print(f"{prefix} {msg.text}"))


def enable_request_logging(page: Page, filter_pattern: str | None = None):
    """
    Enable request logging for debugging API calls.

    Args:
        page: Playwright page object
        filter_pattern: Optional pattern to filter requests (e.g., "api/")
    """

    def log_request(request):
        if filter_pattern is None or filter_pattern in request.url:
            print(f"→ Request: {request.method} {request.url}")

    page.on("request", log_request)


def enable_response_logging(page: Page, filter_pattern: str | None = None):
    """
    Enable response logging for debugging API responses.

    Args:
        page: Playwright page object
        filter_pattern: Optional pattern to filter responses (e.g., "api/")
    """

    def log_response(response):
        if filter_pattern is None or filter_pattern in response.url:
            print(f"← Response: {response.status} {response.url}")

    page.on("response", log_response)


def capture_api_request(
    page: Page, url_pattern: str, method: str = "POST"
) -> dict[str, Any]:
    """
    Capture API request data for verification.

    Args:
        page: Playwright page object
        url_pattern: Pattern to match in the URL (e.g., "api/campaigns")
        method: HTTP method to match

    Returns:
        dict: Captured request data or None if not captured
    """
    captured_data = {"request": None}

    def handle_request(request):
        if url_pattern in request.url and request.method == method:
            try:


                data = json.loads(request.post_data) if request.post_data else {}
                captured_data["request"] = {
                    "url": request.url,
                    "method": request.method,
                    "data": data,
                    "headers": dict(request.headers),
                }
            except Exception as e:
                print(f"Error capturing request: {e}")

    page.on("request", handle_request)
    return captured_data


def fill_wizard_step1(
    page: Page,
    title: str,
    campaign_type: str = "custom",
    character: str | None = None,
    setting: str | None = None,
):
    """
    Fill out step 1 of the campaign wizard.

    Args:
        page: Playwright page object
        title: Campaign title
        campaign_type: "custom" or "dragon-knight"
        character: Character name/description (for custom campaign)
        setting: Setting/world description (for custom campaign)
    """
    # Fill title
    page.fill("#wizard-campaign-title", title)

    # Select campaign type
    page.click(f'div.campaign-type-card[data-type="{campaign_type}"]')
    page.wait_for_timeout(500)

    # Fill character and setting if custom campaign
    if campaign_type == "custom" and character:
        page.fill("#wizard-character-input", character)
    if campaign_type == "custom" and setting:
        page.fill("#wizard-setting-input", setting)


def navigate_wizard_to_step(page: Page, target_step: int, current_step: int = 1):
    """
    Navigate wizard to a specific step.

    Args:
        page: Playwright page object
        target_step: Target step number (1-4)
        current_step: Current step number
    """
    steps_to_advance = target_step - current_step
    for _ in range(steps_to_advance):
        page.click('button:has-text("Next"):visible')
        page.wait_for_timeout(500)


def wait_for_element(
    page: Page, selector: str, timeout: int = 5000, state: str = "visible"
) -> bool:
    """
    Wait for an element with error handling.

    Args:
        page: Playwright page object
        selector: Element selector
        timeout: Timeout in milliseconds
        state: State to wait for ("visible", "hidden", "attached", "detached")

    Returns:
        bool: True if element reached desired state, False if timeout
    """
    try:
        page.wait_for_selector(selector, timeout=timeout, state=state)
        return True
    except Exception:
        return False


def check_element_exists(page: Page, selector: str) -> bool:
    """
    Check if an element exists on the page.

    Args:
        page: Playwright page object
        selector: Element selector

    Returns:
        bool: True if element exists
    """
    return page.locator(selector).count() > 0


def get_element_text(page: Page, selector: str, default: str = "") -> str:
    """
    Safely get text content of an element.

    Args:
        page: Playwright page object
        selector: Element selector
        default: Default value if element not found

    Returns:
        str: Element text content or default
    """
    try:
        element = page.locator(selector).first
        if element:
            return element.text_content() or default
    except Exception:
        pass
    return default


def scroll_to_element(page: Page, selector: str):
    """
    Scroll an element into view.

    Args:
        page: Playwright page object
        selector: Element selector
    """
    page.evaluate(
        f"document.querySelector('{selector}')?.scrollIntoView({{behavior: 'smooth', block: 'center'}})"
    )
    page.wait_for_timeout(500)  # Wait for scroll animation


def cleanup_browser(playwright, browser: Browser):
    """
    Clean up browser and playwright instances.

    Args:
        playwright: Playwright instance
        browser: Browser instance
    """
    try:
        browser.close()
    except Exception:
        pass

    try:
        playwright.stop()
    except Exception:
        pass


# Test runner helper for common test setup
def run_ui_test(
    test_function: Callable,
    test_name: str,
    headless: bool = DEFAULT_HEADLESS,
    port: int = DEFAULT_PORT,
):
    """
    Run a UI test with standard setup and teardown.

    Args:
        test_function: Test function that takes (page, test_name) as arguments
        test_name: Name of the test (for logging/screenshots)
        headless: Whether to run in headless mode
        port: Port number for localhost

    Example:
        def my_test(page, test_name):
            navigate_to_page(page, "new-campaign")
            take_screenshot(page, test_name, "initial")
            # ... test logic ...

        run_ui_test(my_test, "campaign_creation")
    """
    p, browser, page = None, None, None

    try:
        print(f"\n{'=' * 60}")
        print(f"Starting UI Test: {test_name}")
        print(f"{'=' * 60}\n")

        # Setup
        p, browser, page = setup_browser(headless=headless)

        # Run test
        test_function(page, test_name)

        print(f"\n✅ Test '{test_name}' completed successfully")

    except Exception as e:
        print(f"\n❌ Test '{test_name}' failed: {e}")
        if page:
            try:
                take_screenshot(page, test_name, "error")
            except:
                pass
        raise

    finally:
        # Cleanup
        if browser and p:
            cleanup_browser(p, browser)
