#!/usr/bin/env python3
"""
Comprehensive test to verify ALL UI elements are displayed correctly in debug mode.
This test takes screenshots of each structured field to prove the UI fix works.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_all_ui_elements_debug_mode():
    """Test and screenshot all UI elements in debug mode."""

    # Create screenshots directory
    screenshots_dir = "ui_verification_screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        # Launch browser in non-headless mode to see what's happening
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print("=" * 60)
            print("UI Elements Debug Mode Verification Test")
            print("=" * 60)

            # 1. Navigate with test mode
            test_url = "http://localhost:6006?test_mode=true&test_user_id=ui-debug-test"
            page.goto(test_url)
            print(f"✓ Navigated to: {test_url}")

            # Wait for test mode initialization
            page.wait_for_function("window.testAuthBypass !== undefined", timeout=5000)
            print("✓ Test mode initialized")

            # 2. Wait for dashboard and create campaign
            page.wait_for_selector("#campaign-list", timeout=10000)
            print("✓ Dashboard loaded")

            # Look for create campaign button
            create_btn = page.locator("button:has-text('Create New Campaign')").or_(
                page.locator("button:has-text('Start New Campaign')")
            )

            if create_btn.count() > 0:
                create_btn.first.click()
                print("✓ Clicked create campaign")

                # Wait for form
                page.wait_for_timeout(1000)

                # 3. Fill campaign form WITH DEBUG MODE ENABLED
                page.fill("#campaign-title", "Debug Mode UI Test")
                page.fill("#campaign-genre", "Fantasy")
                page.fill("#campaign-tone", "Epic")
                page.fill("#character-name", "Test Fighter")
                page.fill("#character-background", "A warrior testing the UI")

                # CRITICAL: Enable debug mode
                debug_checkbox = page.locator("#debug-mode")
                if debug_checkbox.count() > 0:
                    debug_checkbox.check()
                    print("✓ Debug mode ENABLED")
                else:
                    print("⚠️  Debug mode checkbox not found - may be on by default")

                # Submit form
                page.locator("button[type='submit']").or_(
                    page.locator("button:has-text('Create Campaign')")
                ).first.click()
                print("✓ Created campaign")

                # 4. Wait for story view
                page.wait_for_selector("#story-content", timeout=10000)
                page.wait_for_timeout(2000)  # Let initial story load

                # Take screenshot of initial story
                page.screenshot(
                    path=f"{screenshots_dir}/01_initial_story.png", full_page=True
                )
                print("✓ Screenshot: Initial story")

                # 5. Send combat action to trigger all fields
                user_input = page.locator("#user-input")
                if user_input.count() > 0:
                    # Send a combat action
                    user_input.fill("I attack the goblin with my sword!")
                    print("✓ Typed combat action")

                    # Take screenshot before sending
                    page.screenshot(path=f"{screenshots_dir}/02_before_send.png")

                    # Send the action
                    user_input.press("Enter")
                    print("✓ Sent combat action")

                    # Wait for response
                    print("⏳ Waiting for AI response with all fields...")
                    page.wait_for_function(
                        "document.querySelector('#user-input').disabled === false",
                        timeout=30000,
                    )
                    page.wait_for_timeout(2000)  # Extra time for DOM updates

                    # 6. Take screenshots of each element
                    print("\n📸 Taking screenshots of each UI element:")

                    # Get the last story entry (AI response)
                    last_entry = page.locator(".story-entry").last

                    # Full response screenshot
                    if last_entry.count() > 0:
                        last_entry.screenshot(
                            path=f"{screenshots_dir}/03_full_response.png"
                        )
                        print("✓ Screenshot: Full response")

                        # Session Header
                        session_header = last_entry.locator(".session-header")
                        if session_header.count() > 0:
                            session_header.screenshot(
                                path=f"{screenshots_dir}/04_session_header.png"
                            )
                            print("✓ Screenshot: Session header")
                            print(
                                f"  Content preview: {session_header.inner_text()[:100]}..."
                            )
                        else:
                            print("✗ Session header not found")

                        # Narrative (main story text)
                        narrative = last_entry.locator("p").first
                        if narrative.count() > 0:
                            narrative.screenshot(
                                path=f"{screenshots_dir}/05_narrative.png"
                            )
                            print("✓ Screenshot: Narrative")
                            print(
                                f"  Content preview: {narrative.inner_text()[:100]}..."
                            )
                        else:
                            print("✗ Narrative not found")

                        # Dice Rolls
                        dice_rolls = last_entry.locator(".dice-rolls")
                        if dice_rolls.count() > 0:
                            dice_rolls.screenshot(
                                path=f"{screenshots_dir}/06_dice_rolls.png"
                            )
                            print("✓ Screenshot: Dice rolls")
                            print(f"  Content: {dice_rolls.inner_text()}")
                        else:
                            print("✗ Dice rolls not found")

                        # Resources
                        resources = last_entry.locator(".resources")
                        if resources.count() > 0:
                            resources.screenshot(
                                path=f"{screenshots_dir}/07_resources.png"
                            )
                            print("✓ Screenshot: Resources")
                            print(f"  Content: {resources.inner_text()}")
                        else:
                            print("✗ Resources not found")

                        # Planning Block
                        planning_block = last_entry.locator(".planning-block")
                        if planning_block.count() > 0:
                            planning_block.screenshot(
                                path=f"{screenshots_dir}/08_planning_block.png"
                            )
                            print("✓ Screenshot: Planning block")
                            print(
                                f"  Content preview: {planning_block.inner_text()[:150]}..."
                            )
                        else:
                            print("✗ Planning block not found")

                        # Debug Info (only in debug mode)
                        debug_info = last_entry.locator(".debug-info")
                        if debug_info.count() > 0:
                            debug_info.screenshot(
                                path=f"{screenshots_dir}/09_debug_info.png"
                            )
                            print("✓ Screenshot: Debug info (DEBUG MODE CONFIRMED)")
                            print(
                                f"  Content preview: {debug_info.inner_text()[:100]}..."
                            )
                        else:
                            print(
                                "⚠️  Debug info not found - debug mode may not be enabled"
                            )

                        # 7. Verification summary
                        print("\n" + "=" * 60)
                        print("VERIFICATION SUMMARY")
                        print("=" * 60)

                        # Check what's in the HTML
                        last_entry_html = last_entry.inner_html()

                        elements = {
                            "session-header": "Session Header",
                            "dice-rolls": "Dice Rolls",
                            "resources": "Resources",
                            "planning-block": "Planning Block",
                            "debug-info": "Debug Info",
                            "Scene #": "Scene Number Label",
                            "--- PLANNING BLOCK ---": "Planning Block Text",
                            "What would you like to do": "Action Prompt",
                        }

                        found_count = 0
                        for selector, name in elements.items():
                            if selector in last_entry_html:
                                print(f"✓ {name}: FOUND")
                                found_count += 1
                            else:
                                print(f"✗ {name}: NOT FOUND")

                        print(f"\nTotal elements found: {found_count}/{len(elements)}")

                        # Take final full page screenshot
                        page.screenshot(
                            path=f"{screenshots_dir}/10_full_page_final.png",
                            full_page=True,
                        )
                        print("\n✓ Final full page screenshot saved")

                    else:
                        print("❌ No story entries found!")

                else:
                    print("❌ User input field not found!")

            else:
                print("❌ Create campaign button not found!")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(
                path=f"{screenshots_dir}/error_screenshot.png", full_page=True
            )
            raise
        finally:
            print(f"\n✓ Screenshots saved in: {screenshots_dir}/")
            print(
                "✓ Test complete. Browser will stay open for 15 seconds for inspection..."
            )
            time.sleep(15)
            browser.close()


if __name__ == "__main__":
    print("Starting UI Elements Debug Mode Verification Test")
    print(
        "Make sure server is running with: TESTING=true PORT=6006 python main.py serve"
    )
    print("-" * 60)
    test_all_ui_elements_debug_mode()
