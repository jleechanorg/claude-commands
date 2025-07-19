#!/usr/bin/env python3
"""Take screenshots of the planning blocks demo page."""

import os

from playwright.sync_api import sync_playwright


def main():
    # Create screenshot directory
    screenshot_dir = "/tmp/worldarchitectai/planning_blocks_demo"
    os.makedirs(screenshot_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load the demo HTML file
        demo_file = os.path.abspath("test_planning_blocks_demo.html")
        page.goto(f"file://{demo_file}")

        # Take initial screenshot
        page.screenshot(path=f"{screenshot_dir}/01_initial_view.png")
        print(f"✅ Saved: {screenshot_dir}/01_initial_view.png")

        # Hover over first button
        first_button = page.query_selector(".choice-button")
        if first_button:
            first_button.hover()
            page.wait_for_timeout(500)
            page.screenshot(path=f"{screenshot_dir}/02_button_hover.png")
            print(f"✅ Saved: {screenshot_dir}/02_button_hover.png")

            # Click the button
            first_button.click()
            page.wait_for_timeout(500)
            page.screenshot(path=f"{screenshot_dir}/03_after_click.png")
            print(f"✅ Saved: {screenshot_dir}/03_after_click.png")

        # Take a full page screenshot
        page.screenshot(path=f"{screenshot_dir}/04_full_page.png", full_page=True)
        print(f"✅ Saved: {screenshot_dir}/04_full_page.png")

        browser.close()

    print(f"\n📸 All screenshots saved to: {screenshot_dir}")


if __name__ == "__main__":
    main()
