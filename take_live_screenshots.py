#!/usr/bin/env python3
"""Take screenshots of the live planning blocks test page."""

import os

from playwright.sync_api import sync_playwright


def main():
    # Create screenshot directory
    screenshot_dir = "/tmp/worldarchitectai/planning_blocks_live"
    os.makedirs(screenshot_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load the test page
        test_file = os.path.abspath("test_planning_blocks_live.html")
        page.goto(f"file://{test_file}")

        # Take initial screenshot
        page.screenshot(path=f"{screenshot_dir}/01_initial_empty.png")
        print(f"✅ Saved: {screenshot_dir}/01_initial_empty.png")

        # Click to add planning block
        page.click("button:has-text('Add Test Planning Block')")
        page.wait_for_timeout(500)
        page.screenshot(path=f"{screenshot_dir}/02_with_planning_block.png")
        print(f"✅ Saved: {screenshot_dir}/02_with_planning_block.png")

        # Hover over first choice button
        first_button = page.query_selector(".choice-button:not(.choice-button-custom)")
        if first_button:
            first_button.hover()
            page.wait_for_timeout(500)
            page.screenshot(path=f"{screenshot_dir}/03_button_hover.png")
            print(f"✅ Saved: {screenshot_dir}/03_button_hover.png")

        # Hover over custom button
        custom_button = page.query_selector(".choice-button-custom")
        if custom_button:
            custom_button.hover()
            page.wait_for_timeout(500)
            page.screenshot(path=f"{screenshot_dir}/04_custom_button_hover.png")
            print(f"✅ Saved: {screenshot_dir}/04_custom_button_hover.png")

            # Click custom button
            custom_button.click()
            page.wait_for_timeout(500)
            page.screenshot(path=f"{screenshot_dir}/05_after_custom_click.png")
            print(f"✅ Saved: {screenshot_dir}/05_after_custom_click.png")

        # Add custom-only block
        page.click("button:has-text('Add Custom-Only Block')")
        page.wait_for_timeout(500)
        page.screenshot(
            path=f"{screenshot_dir}/06_custom_only_block.png", full_page=True
        )
        print(f"✅ Saved: {screenshot_dir}/06_custom_only_block.png")

        # Click a regular button to show alert
        first_button = page.query_selector(".choice-button:not(.choice-button-custom)")
        if first_button:
            # Handle the alert dialog
            page.on("dialog", lambda dialog: dialog.accept())
            first_button.click()
            page.wait_for_timeout(100)
            page.screenshot(path=f"{screenshot_dir}/07_after_choice_click.png")
            print(f"✅ Saved: {screenshot_dir}/07_after_choice_click.png")

        browser.close()

    print(f"\n📸 All screenshots saved to: {screenshot_dir}")
    print("\nScreenshots show:")
    print("1. Initial empty state")
    print("2. Planning block with choice buttons and custom option")
    print("3. Hover effect on regular choice button")
    print("4. Hover effect on custom button (dashed border)")
    print("5. Input field focused after custom button click")
    print("6. Custom-only block (when no predefined choices)")
    print("7. Button disabled state after clicking a choice")


if __name__ == "__main__":
    main()
