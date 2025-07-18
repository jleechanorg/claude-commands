#!/usr/bin/env python3
"""
Utility functions for managing screenshots in UI tests.
Ensures all screenshots are saved to the standard location.
"""

import os

# Standard screenshot directory as per project conventions
SCREENSHOT_BASE_DIR = "/tmp/worldarchitectai/browser"

# Subdirectories for different test types
STRUCTURED_FIELDS_DIR = f"{SCREENSHOT_BASE_DIR}/structured_fields"
INTEGRATION_DIR = f"{SCREENSHOT_BASE_DIR}/integration"
UNIT_DIR = f"{SCREENSHOT_BASE_DIR}/unit"


def get_screenshot_path(test_name, description, extension=".png"):
    """
    Generate a standardized screenshot path.

    Args:
        test_name: Name of the test (e.g., "wizard", "campaign_creation")
        description: Description of what the screenshot shows (e.g., "initial_state", "after_submit")
        extension: File extension (default: ".png")

    Returns:
        str: Full path to save the screenshot
    """
    # Create test-specific subdirectory
    test_dir = os.path.join(SCREENSHOT_BASE_DIR, test_name)
    os.makedirs(test_dir, exist_ok=True)

    # Clean up description for filename
    clean_desc = description.replace(" ", "_").replace("/", "_").lower()

    # Generate filename
    filename = f"{clean_desc}{extension}"

    return os.path.join(test_dir, filename)


def take_screenshot(
    page, test_name, description, full_page=False, element_selector=None
):
    """
    Take a screenshot with standardized path and logging.

    Args:
        page: Playwright page object
        test_name: Name of the test
        description: Description of the screenshot
        full_page: Whether to capture the full page (default: False)
        element_selector: Optional CSS selector to screenshot specific element

    Returns:
        str: Path where the screenshot was saved
    """
    screenshot_path = get_screenshot_path(test_name, description)

    try:
        if element_selector:
            # Screenshot specific element
            element = page.locator(element_selector)
            if element.count() > 0:
                element.screenshot(path=screenshot_path)
            else:
                print(f"⚠️ Element not found for screenshot: {element_selector}")
                return ""
        else:
            # Screenshot entire page
            page.screenshot(path=screenshot_path, full_page=full_page)

        # Log the action
        print(f"📸 Screenshot saved: {screenshot_path}")
        print(f"   Description: {description}")

        return screenshot_path

    except Exception as e:
        print(f"❌ Screenshot failed for {description}: {e}")
        return ""


def cleanup_old_screenshots(test_name=None, keep_latest=10, days_old=None):
    """
    Clean up old screenshots.

    Args:
        test_name: Name of the test (if None, cleans all directories)
        keep_latest: Number of latest screenshots to keep per test (default: 10)
        days_old: Remove screenshots older than this many days (if specified)
    """
    import time

    if test_name:
        # Clean specific test directory
        test_dir = os.path.join(SCREENSHOT_BASE_DIR, test_name)
        if not os.path.exists(test_dir):
            return

        # Get all PNG files in the directory
        screenshots = []
        for file in os.listdir(test_dir):
            if file.endswith(".png"):
                file_path = os.path.join(test_dir, file)
                mtime = os.path.getmtime(file_path)
                screenshots.append((mtime, file_path))

        # Sort by modification time (oldest first)
        screenshots.sort()

        # Remove old screenshots if we have more than keep_latest
        if len(screenshots) > keep_latest:
            for _, file_path in screenshots[:-keep_latest]:
                os.remove(file_path)
                print(f"🗑️  Removed old screenshot: {file_path}")

    elif days_old:
        # Clean all directories based on age
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)

        for root, dirs, files in os.walk(SCREENSHOT_BASE_DIR):
            for file in files:
                if file.endswith(".png"):
                    filepath = os.path.join(root, file)
                    if os.path.getctime(filepath) < cutoff_time:
                        os.remove(filepath)
                        print(f"🗑️  Removed old screenshot: {filepath}")


def get_screenshot_dir(test_name):
    """
    Get the screenshot directory for a specific test.
    Creates the directory if it doesn't exist.

    Args:
        test_name: Name of the test

    Returns:
        str: Path to the screenshot directory
    """
    test_dir = os.path.join(SCREENSHOT_BASE_DIR, test_name)
    os.makedirs(test_dir, exist_ok=True)
    return test_dir


# Backwards compatibility - direct access to base directory
def get_base_screenshot_dir():
    """Get the base screenshot directory."""
    os.makedirs(SCREENSHOT_BASE_DIR, exist_ok=True)
    return SCREENSHOT_BASE_DIR
