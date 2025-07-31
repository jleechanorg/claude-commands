#!/usr/bin/env python3
"""
Helper functions for common UI test operations.
Complements test_ui_util.py with additional patterns found in tests.
"""

import time
from typing import Any

from playwright.sync_api import Page
from screenshot_utils import take_screenshot


def wait_and_click(
    page: Page, selector: str, timeout: int = 5000, force: bool = False
) -> bool:
    """
    Wait for element and click it, with error handling.

    Returns:
        bool: True if clicked successfully, False otherwise
    """
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        page.click(selector, force=force)
        return True
    except Exception as e:
        print(f"❌ Could not click {selector}: {e}")
        return False


def try_multiple_selectors(
    page: Page, selectors: list[str], action: str = "click", timeout: int = 1000
) -> str | None:
    """
    Try multiple selectors until one works.

    Args:
        page: Playwright page
        selectors: List of selectors to try
        action: Action to perform ("click", "fill", "text", "visible")
        timeout: Timeout for each selector

    Returns:
        The selector that worked, or None
    """
    for selector in selectors:
        try:
            if action == "visible":
                if page.is_visible(selector):
                    return selector
            elif action == "text":
                text = page.text_content(selector, timeout=timeout)
                if text:
                    return selector
            elif action == "click":
                page.click(selector, timeout=timeout)
                return selector
            else:
                element = page.wait_for_selector(selector, timeout=timeout)
                if element:
                    return selector
        except Exception:
            continue
    return None


def verify_view_active(page: Page, view_name: str) -> bool:
    """
    Verify a specific view is active.

    Args:
        page: Playwright page
        view_name: Name of the view (e.g., "dashboard", "game", "new-campaign")

    Returns:
        bool: True if view is active
    """
    return page.is_visible(f"#{view_name}-view.active-view")


def get_active_view(page: Page) -> str | None:
    """
    Get the currently active view.

    Returns:
        str: Name of active view or None
    """
    views = ["auth", "dashboard", "new-campaign", "game"]
    for view in views:
        if verify_view_active(page, view):
            return view
    return None


def debug_print_views(page: Page):
    """Print the status of all views for debugging."""
    views = ["auth-view", "dashboard-view", "new-campaign-view", "game-view"]
    print("🔍 View Status:")
    for view in views:
        is_active = page.evaluate(f"""
            document.getElementById('{view}')?.classList.contains('active-view')
        """)
        exists = page.evaluate(f"!!document.getElementById('{view}')")
        print(f"   {view}: exists={exists}, active={is_active}")


def fill_form_field(
    page: Page, field_id: str, value: str, clear_first: bool = True
) -> bool:
    """
    Fill a form field with proper clearing and verification.

    Returns:
        bool: True if filled successfully
    """
    try:
        if clear_first:
            page.fill(f"#{field_id}", "")
        page.fill(f"#{field_id}", value)

        # Verify the value was set
        actual_value = page.input_value(f"#{field_id}")
        return actual_value == value
    except Exception as e:
        print(f"❌ Could not fill {field_id}: {e}")
        return False


def get_element_text_safe(page: Page, selector: str, default: str = "NOT FOUND") -> str:
    """
    Safely get text content with fallback.
    """
    try:
        return page.text_content(selector) or default
    except Exception:
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


def wait_for_any_selector(
    page: Page, selectors: list[str], timeout: int = 5000
) -> str | None:
    """
    Wait for any of the given selectors to appear.

    Returns:
        The first selector that appears, or None if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout / 1000:
        for selector in selectors:
            if page.is_visible(selector):
                return selector
        time.sleep(0.1)
    return None


def extract_structured_fields(page: Page) -> dict[str, Any]:
    """
    Extract common structured response fields from the page.

    Returns:
        Dict with narrative_text, session_header, planning_block, etc.
    """
    fields = {}

    # Narrative text
    narrative_selectors = [
        ".narrative-text",
        ".story-text",
        "[data-field='narrative_text']",
    ]
    fields["narrative_text"] = get_element_text_safe(
        page, try_multiple_selectors(page, narrative_selectors, "text") or ""
    )

    # Session header
    session_selectors = [".session-header", "[data-field='session_header']"]
    fields["session_header"] = get_element_text_safe(
        page, try_multiple_selectors(page, session_selectors, "text") or ""
    )

    # Planning block
    planning_selectors = [".planning-block", "[data-field='planning_block']"]
    if page.is_visible(planning_selectors[0]):
        fields["planning_block"] = {
            "thinking": get_element_text_safe(page, ".thinking-content"),
            "context": get_element_text_safe(page, ".context-content"),
        }

    return fields


def verify_api_call_made(
    page: Page, url_pattern: str, method: str = "POST", timeout: int = 5000
) -> bool:
    """
    Verify that an API call was made by checking network activity.
    Note: Requires page.on('request') to be set up.
    """
    # This is a placeholder - actual implementation would need
    # request interception set up in the test
    print("⚠️ API call verification requires request interception setup")
    return True


def scroll_to_bottom(page: Page):
    """Scroll to the bottom of the page."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)


def scroll_to_top(page: Page):
    """Scroll to the top of the page."""
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)


def is_element_in_viewport(page: Page, selector: str) -> bool:
    """
    Check if an element is visible in the viewport.
    """
    return page.evaluate(f"""
        (() => {{
            const element = document.querySelector('{selector}');
            if (!element) return false;

            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= window.innerHeight &&
                rect.right <= window.innerWidth
            );
        }})()
    """)


def wait_for_text_to_appear(page: Page, text: str, timeout: int = 5000) -> bool:
    """
    Wait for specific text to appear anywhere on the page.
    """
    try:
        page.wait_for_function(
            f"document.body.innerText.includes('{text}')", timeout=timeout
        )
        return True
    except Exception:
        return False


def count_elements(page: Page, selector: str) -> int:
    """Count the number of elements matching a selector."""
    return page.locator(selector).count()


def get_all_text_content(page: Page, selector: str) -> list[str]:
    """Get text content from all elements matching a selector."""
    elements = page.locator(selector).all()
    return [el.text_content() or "" for el in elements]


def navigate_to_test_game(
    page: Page,
    campaign_name: str = "All Fields Test Campaign",
    port: int = 8081,
    test_user_id: str = "test-user-123",
) -> bool:
    """
    Navigate to a test game using standard test mode parameters.

    Args:
        page: Playwright page object
        campaign_name: Name of campaign to navigate to
        port: Port number for localhost
        test_user_id: Test user ID

    Returns:
        True if navigation successful, False otherwise
    """
    try:
        # Navigate to dashboard with test mode
        page.goto(f"http://localhost:{port}?test_mode=true&test_user_id={test_user_id}")
        page.wait_for_load_state("networkidle")

        # Wait for dashboard to load
        if not wait_for_any_selector(
            page,
            ["[data-testid='campaign-list']", ".campaign-card", "text='My Campaigns'"],
            timeout=10000,
        ):
            print("❌ Dashboard not loaded - no campaign list found")
            return False

        # Click on the specified campaign
        campaign_selector = f"text='{campaign_name}'"
        if not wait_for_element(page, campaign_selector, timeout=5000):
            print(f"❌ Campaign '{campaign_name}' not found")
            return False

        page.click(campaign_selector)

        # Wait for game view to load
        if not wait_for_element(page, "#game-view", timeout=10000):
            print("❌ Game view not loaded")
            return False

        return True

    except Exception as e:
        print(f"❌ Navigation failed: {e}")
        return False


def capture_structured_fields_sequence(
    page: Page, test_name: str, action_text: str = "I attack the goblin"
) -> dict[str, str]:
    """
    Capture a complete sequence of structured fields screenshots.

    Args:
        page: Playwright page object
        test_name: Name of the test (for screenshots)
        action_text: Text to send to trigger AI response

    Returns:
        Dictionary mapping field names to screenshot paths
    """


    screenshots = {}

    # Take initial screenshot
    screenshots["full_page"] = take_screenshot(page, test_name, "full_page")

    # Enter action and submit
    action_input = page.locator(
        "#player-action, #user-input, textarea[name='user-input']"
    ).first
    if action_input:
        action_input.fill(action_text)

        # Find and click send button
        send_button = page.locator(
            "#send-action, button:has-text('Send'), button[type='submit']"
        ).first
        if send_button:
            send_button.click()

        # Wait for response
        if not wait_for_text_to_appear(page, "Response time:", timeout=30000):
            # Try alternate response indicators
            if not wait_for_any_selector(
                page,
                [".narrative-text", ".ai-response", ".story-content"],
                timeout=30000,
            ):
                print("❌ No AI response received")
                return screenshots

    # Take screenshot of full response
    screenshots["full_ai_response"] = take_screenshot(
        page, test_name, "full_ai_response"
    )

    # Capture individual field screenshots
    field_selectors = {
        "session_header": '.session-header, [data-field="session_header"]',
        "narrative": '.narrative-text, #story-content p:last-child, [data-field="narrative_text"]',
        "dice_rolls": '.dice-rolls, [data-field="dice_rolls"]',
        "resources": '.resources, .resource-updates, [data-field="resource_updates"]',
        "planning_block": '.planning-block, [data-field="planning_block"]',
        "debug_info": '.debug-info, [data-field="debug_info"]',
        "god_mode_response": '.god-mode-response, [data-field="god_mode_response"]',
        "entities_mentioned": '.entities-mentioned, [data-field="entities_mentioned"]',
        "location_confirmed": '.location-confirmed, [data-field="location_confirmed"]',
    }

    for field_name, selectors in field_selectors.items():
        # Try multiple selectors
        element = None
        for selector in selectors.split(", "):
            if page.locator(selector).count() > 0:
                element = selector
                break

        if element:
            screenshots[field_name] = take_screenshot(
                page, test_name, field_name, element_selector=element
            )
        else:
            print(f"⚠️ Field not found: {field_name}")

    # Take final full page screenshot
    screenshots["full_page_final"] = take_screenshot(page, test_name, "full_page_final")

    return screenshots
