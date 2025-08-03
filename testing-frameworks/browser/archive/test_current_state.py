#!/usr/bin/env python3
"""Quick test to check current UI state and take a screenshot"""

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:6006"


def check_current_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate and wait
        print(f"Navigating to {BASE_URL}...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Take screenshot
        page.screenshot(path="/tmp/current_ui_state.png")
        print("Screenshot saved to: /tmp/current_ui_state.png")

        # Check what's visible
        print("\nChecking UI elements:")
        elements = {
            "#dashboard-view": "Dashboard view",
            "#game-view": "Game view",
            "#new-campaign-view": "New campaign view",
            ".story-container": "Story container",
            "#user-input": "User input field",
            'text="Start New Campaign"': "Start campaign button",
        }

        for selector, name in elements.items():
            if page.query_selector(selector):
                print(f"✓ Found: {name}")
            else:
                print(f"✗ Not found: {name}")

        # Check page content
        print(f"\nPage title: {page.title()}")
        print(f"Page URL: {page.url}")

        input("Press Enter to close browser...")
        browser.close()


if __name__ == "__main__":
    check_current_state()
