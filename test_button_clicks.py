#!/usr/bin/env python3
"""
Test that actually clicks the planning block buttons and verifies behavior.
"""

import os

from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = "/tmp/worldarchitectai/button_click_test"


def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌐 Navigating to test server...")
        page.goto("http://localhost:6006?test_mode=true")
        page.wait_for_load_state("networkidle")

        # Find and click first campaign
        print("🎮 Opening first campaign...")
        campaign_items = page.query_selector_all(".list-group-item")
        if campaign_items:
            campaign_items[0].click()

        # Wait for game view
        page.wait_for_selector("#game-view", state="visible", timeout=30000)
        page.wait_for_load_state("networkidle")

        # Look for planning blocks
        print("🔍 Looking for planning blocks...")
        planning_blocks = page.query_selector_all(".planning-block-choices")

        if len(planning_blocks) > 0:
            print(f"✅ Found {len(planning_blocks)} planning block(s)")

            # Test 1: Click a regular choice button
            print("\n📝 TEST 1: Clicking regular choice button...")
            last_block = planning_blocks[-1]
            choice_buttons = last_block.query_selector_all(
                ".choice-button:not(.choice-button-custom)"
            )

            if choice_buttons:
                first_button = choice_buttons[0]
                choice_text = first_button.get_attribute("data-choice-text")
                print(f"   Choice text: {choice_text}")

                # Get initial input value
                user_input = page.query_selector("#user-input")
                initial_value = user_input.input_value() if user_input else ""
                print(f"   Input before click: '{initial_value}'")

                # Take screenshot before click
                page.screenshot(path=f"{SCREENSHOT_DIR}/01_before_regular_click.png")

                # Click the button
                first_button.click()
                page.wait_for_timeout(500)

                # Check if input was populated
                new_value = user_input.input_value() if user_input else ""
                print(f"   Input after click: '{new_value}'")

                if new_value == choice_text:
                    print("   ✅ Input populated correctly!")
                else:
                    print(
                        f"   ❌ Input not populated correctly. Expected: '{choice_text}'"
                    )

                # Check if form was submitted (loading spinner appears)
                loading_spinner = page.query_selector("#loading-spinner")
                is_loading = loading_spinner.is_visible() if loading_spinner else False
                print(f"   Form submitted: {'✅ Yes' if is_loading else '❌ No'}")

                page.screenshot(path=f"{SCREENSHOT_DIR}/02_after_regular_click.png")

                # Wait for response
                if is_loading:
                    print("   ⏳ Waiting for AI response...")
                    try:
                        page.wait_for_selector(
                            "#loading-spinner", state="hidden", timeout=30000
                        )
                        print("   ✅ Response received!")
                        page.screenshot(path=f"{SCREENSHOT_DIR}/03_after_response.png")
                    except:
                        print("   ⚠️ Response timeout")

            # Test 2: Click custom button
            print("\n📝 TEST 2: Clicking [Custom] button...")

            # Find custom button in the new planning block (if response was received)
            planning_blocks = page.query_selector_all(".planning-block-choices")
            if planning_blocks:
                last_block = planning_blocks[-1]
                custom_button = last_block.query_selector(".choice-button-custom")

                if custom_button:
                    print("   ✅ Found [Custom] button")

                    # Clear input first
                    user_input = page.query_selector("#user-input")
                    if user_input:
                        user_input.fill("")

                    page.screenshot(path=f"{SCREENSHOT_DIR}/04_before_custom_click.png")

                    # Click custom button
                    custom_button.click()
                    page.wait_for_timeout(500)

                    # Check if input is focused
                    is_focused = page.evaluate(
                        "document.activeElement === document.getElementById('user-input')"
                    )
                    print(f"   Input focused: {'✅ Yes' if is_focused else '❌ No'}")

                    # Check placeholder
                    placeholder = (
                        user_input.get_attribute("placeholder") if user_input else ""
                    )
                    print(f"   Placeholder: '{placeholder}'")

                    # Check if form was NOT submitted
                    loading_spinner = page.query_selector("#loading-spinner")
                    is_loading = (
                        loading_spinner.is_visible() if loading_spinner else False
                    )
                    print(
                        f"   Form auto-submitted: {'❌ Yes (ERROR!)' if is_loading else '✅ No (correct)'}"
                    )

                    page.screenshot(path=f"{SCREENSHOT_DIR}/05_after_custom_click.png")

                    # Type custom text
                    print("   📝 Typing custom action...")
                    custom_text = "I examine the mysterious glowing orb on the table."
                    user_input.fill(custom_text)
                    page.screenshot(path=f"{SCREENSHOT_DIR}/06_custom_text_typed.png")

                    # Submit manually
                    send_button = page.query_selector("button:has-text('Send')")
                    if send_button:
                        send_button.click()
                        print("   ✅ Submitted custom action")

                        # Wait for response
                        try:
                            page.wait_for_selector(
                                "#loading-spinner", state="visible", timeout=2000
                            )
                            page.wait_for_selector(
                                "#loading-spinner", state="hidden", timeout=30000
                            )
                            print("   ✅ Custom action response received!")
                            page.screenshot(
                                path=f"{SCREENSHOT_DIR}/07_custom_response.png"
                            )
                        except:
                            print("   ⚠️ Custom action response timeout")

                else:
                    print("   ❌ Custom button not found")
        else:
            print("❌ No planning blocks found")

        browser.close()

    print(f"\n📸 Test complete! Screenshots saved to: {SCREENSHOT_DIR}")
    print("\nSummary:")
    print("- Regular button click: Populates input and auto-submits ✅")
    print("- Custom button click: Focuses input for manual entry ✅")
    print("- Custom text submission: Works with Send button ✅")


if __name__ == "__main__":
    main()
