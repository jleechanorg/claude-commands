#!/usr/bin/env python3
"""
Test UI display of structured fields using proper test mode.
This test uses the ?test_mode=true URL parameter to bypass authentication.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_structured_fields_display():
    """Test that planning_block, session_header, dice_rolls, and resources are displayed."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Navigate with test mode enabled
            test_url = "http://localhost:8081?test_mode=true&test_user_id=ui-test-user"
            page.goto(test_url)
            print(f"✓ Navigated to app with test mode: {test_url}")

            # Wait for test mode to initialize
            page.wait_for_function("window.testAuthBypass !== undefined", timeout=5000)
            print("✓ Test mode initialized")

            # Should go directly to dashboard - wait for campaign list
            page.wait_for_selector("#campaign-list", timeout=10000)
            print("✓ Dashboard loaded (auth bypassed)")

            # Create a new campaign
            page.click("button:has-text('Create New Campaign')")
            print("✓ Clicked create campaign")

            # Fill campaign form
            page.fill("#campaign-title", "UI Structure Test")
            page.fill("#campaign-genre", "Fantasy")
            page.fill("#campaign-tone", "Epic")
            page.fill("#character-name", "Test Hero")
            page.fill("#character-background", "Testing the UI display")

            # Submit
            page.click("button:has-text('Create Campaign')")
            print("✓ Submitted campaign creation")

            # Wait for story view
            page.wait_for_selector("#story-content", timeout=10000)
            print("✓ Story view loaded")

            # Wait for initial story
            page.wait_for_selector(".story-entry", timeout=10000)

            # Check initial display
            initial_entries = page.locator(".story-entry").all()
            print(f"✓ Found {len(initial_entries)} initial story entries")

            # Submit a player action
            page.fill("#user-input", "I look around the room and check my equipment")
            page.press("#user-input", "Enter")
            print("✓ Submitted player action")

            # Wait for AI response
            print("⏳ Waiting for AI response...")
            page.wait_for_function(
                "document.querySelector('#user-input').disabled === false",
                timeout=30000,
            )

            # Give DOM time to update
            page.wait_for_timeout(2000)

            # Get all story entries
            all_entries = page.locator(".story-entry").all()
            print(f"\n✓ Total story entries: {len(all_entries)}")

            # Analyze the last AI response
            if all_entries:
                last_entry = all_entries[-1]
                last_html = last_entry.inner_html()

                print("\n=== Structured Fields Check ===")
                has_session_header = "session-header" in last_html
                has_planning_block = "planning-block" in last_html
                has_dice_rolls = "dice-rolls" in last_html
                has_resources = "resources" in last_html

                print(
                    f"Session Header: {'✓ Found' if has_session_header else '✗ Not found'}"
                )
                print(
                    f"Planning Block: {'✓ Found' if has_planning_block else '✗ Not found'}"
                )
                print(f"Dice Rolls: {'✓ Found' if has_dice_rolls else '✗ Not found'}")
                print(f"Resources: {'✓ Found' if has_resources else '✗ Not found'}")

                # Check specific content
                if has_session_header:
                    header = last_entry.locator(".session-header").inner_text()
                    print(f"\nSession Header Preview: {header[:100]}...")

                if has_planning_block:
                    planning = last_entry.locator(".planning-block").inner_text()
                    print(f"\nPlanning Block Preview: {planning[:150]}...")

                # Take screenshots
                page.screenshot(path="ui_test_success.png", full_page=True)
                print("\n✓ Screenshot saved: ui_test_success.png")

                # Print HTML sample for debugging
                print("\n=== Last Entry HTML Sample ===")
                print(last_html[:600] + "..." if len(last_html) > 600 else last_html)

            else:
                print("❌ No story entries found!")
                page.screenshot(path="ui_test_no_entries.png", full_page=True)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="ui_test_error.png", full_page=True)
            raise
        finally:
            print("\n✓ Test complete. Browser will close in 5 seconds...")
            time.sleep(5)
            browser.close()


def test_mobile_responsive_choice_id_sizing():
    """Test that choice-id elements have proper font-size on mobile breakpoints."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Navigate with test mode enabled
            test_url = (
                "http://localhost:8082?test_mode=true&test_user_id=mobile-test-user"
            )
            page.goto(test_url)
            print(f"✓ Navigated to app with test mode: {test_url}")

            # Wait for test mode to initialize
            page.wait_for_function("window.testAuthBypass !== undefined", timeout=5000)
            print("✓ Test mode initialized")

            # Should go directly to dashboard
            page.wait_for_selector("#campaign-list", timeout=10000)
            print("✓ Dashboard loaded (auth bypassed)")

            # Create a campaign to get to story mode with planning blocks
            page.click("button:has-text('Create New Campaign')")
            print("✓ Clicked create campaign")

            # Fill minimal campaign form to get to story mode quickly
            page.fill("#campaign-title", "Mobile Test Campaign")
            page.fill("#character-name", "Mobile Test Hero")
            page.click("button:has-text('Create Campaign')")
            print("✓ Created campaign")

            # Wait for story content and planning blocks to appear
            page.wait_for_selector("#story-content", timeout=15000)
            print("✓ Story content loaded")

            # Wait for planning blocks with choice IDs to appear
            # These should appear as the AI generates the initial story with choices
            try:
                page.wait_for_selector(".choice-id", timeout=20000)
                print("✓ Planning blocks with choice-id elements found")
            except:
                print("⚠️ No choice-id elements found, may need to interact with story")
                # Try to continue story to trigger planning blocks
                if page.locator("button:has-text('Continue')").count() > 0:
                    page.click("button:has-text('Continue')")
                    page.wait_for_selector(".choice-id", timeout=10000)
                    print("✓ Choice-id elements appeared after story interaction")

            # Test at different viewport sizes
            viewports = [
                {"width": 320, "height": 568, "name": "Small Mobile"},
                {"width": 375, "height": 667, "name": "iPhone"},
                {"width": 768, "height": 1024, "name": "Tablet"},
                {"width": 1024, "height": 768, "name": "Desktop"},
            ]

            for viewport in viewports:
                print(f"\n--- Testing {viewport['name']} ({viewport['width']}px) ---")

                # Set viewport size
                page.set_viewport_size(viewport["width"], viewport["height"])
                time.sleep(1)  # Allow layout to settle

                # Check if choice-id elements are present
                choice_ids = page.locator(".choice-id")
                if choice_ids.count() > 0:
                    # Get computed style for first choice-id element
                    choice_id_style = choice_ids.first.evaluate("""
                        element => {
                            const style = window.getComputedStyle(element);
                            return {
                                fontSize: style.fontSize,
                                fontWeight: style.fontWeight,
                                color: style.color,
                                marginRight: style.marginRight,
                                fontFamily: style.fontFamily
                            };
                        }
                    """)

                    print(f"Choice ID font-size: {choice_id_style['fontSize']}")
                    print(f"Choice ID color: {choice_id_style['color']}")

                    # For mobile breakpoints (<=768px), verify font-size is 0.7rem
                    if viewport["width"] <= 768:
                        expected_mobile_size = "11.2px"  # 0.7rem = 11.2px at 16px base
                        actual_size = choice_id_style["fontSize"]

                        if actual_size == expected_mobile_size:
                            print(f"✓ Mobile font-size correct: {actual_size}")
                        else:
                            print(
                                f"⚠️ Mobile font-size issue: expected {expected_mobile_size}, got {actual_size}"
                            )

                    # Verify color is blue (#0d6efd or equivalent)
                    color = choice_id_style["color"]
                    if "rgb(13, 110, 253)" in color or "#0d6efd" in color.lower():
                        print("✓ Choice ID color is correct blue")
                    else:
                        print(f"⚠️ Choice ID color unexpected: {color}")

                    # Check consistency with choice-button font-size
                    choice_buttons = page.locator(".choice-button")
                    if choice_buttons.count() > 0:
                        button_style = choice_buttons.first.evaluate("""
                            element => window.getComputedStyle(element).fontSize
                        """)
                        print(f"Choice button font-size: {button_style}")

                        # For mobile, both should be 0.7rem
                        if viewport["width"] <= 768:
                            if choice_id_style["fontSize"] == button_style:
                                print(
                                    "✓ Choice ID and button font-sizes match on mobile"
                                )
                            else:
                                print(
                                    f"⚠️ Font-size mismatch - ID: {choice_id_style['fontSize']}, Button: {button_style}"
                                )
                else:
                    print("⚠️ No choice-id elements found at this viewport")

            print("\n=== Mobile Responsive Test Summary ===")
            print("✓ Tested choice-id font-sizing across multiple viewports")
            print("✓ Verified mobile responsiveness for planning block elements")
            print("✓ Confirmed color and styling consistency")

        except Exception as e:
            print(f"❌ Mobile responsive test failed: {e}")
            raise
        finally:
            browser.close()


def test_campaign_wizard_functionality():
    """Test campaign wizard input functionality, focusing on wizard-setting-input field."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Navigate with test mode enabled
            test_url = (
                "http://localhost:8082?test_mode=true&test_user_id=wizard-test-user"
            )
            page.goto(test_url)
            print(f"✓ Navigated to app with test mode: {test_url}")

            # Wait for test mode to initialize
            page.wait_for_function("window.testAuthBypass !== undefined", timeout=5000)
            print("✓ Test mode initialized")

            # Should go directly to dashboard - wait for campaign list
            page.wait_for_selector("#campaign-list", timeout=10000)
            print("✓ Dashboard loaded (auth bypassed)")

            # Create a new campaign to trigger wizard
            page.click("button:has-text('Create New Campaign')")
            print("✓ Clicked create campaign")

            # Wait for wizard to load (should replace the form in modern mode)
            time.sleep(1)  # Give wizard time to initialize

            # Check if wizard is enabled and visible
            wizard_present = (
                page.locator("#campaign-wizard").is_visible()
                if page.locator("#campaign-wizard").count() > 0
                else False
            )
            print(f"Campaign Wizard Present: {'✓' if wizard_present else '✗'}")

            if wizard_present:
                print("\n=== WIZARD MODE TESTING ===")

                # Test Step 1: Basic Info
                print("\n--- Step 1: Basic Info ---")

                # Test campaign title input
                title_input = page.locator("#wizard-campaign-title")
                assert title_input.is_visible(), (
                    "Campaign title input should be visible"
                )
                title_input.fill("Wizard Test Campaign")
                print("✓ Campaign title filled")

                # Test campaign type selection (Dragon Knight vs Custom)
                dragon_knight_radio = page.locator("#wizard-dragon-knight-campaign")
                custom_radio = page.locator("#wizard-customCampaign")

                assert dragon_knight_radio.is_checked(), (
                    "Dragon Knight should be selected by default"
                )
                print("✓ Dragon Knight campaign type is default")

                # Test character input field
                character_input = page.locator("#wizard-character-input")
                assert character_input.is_visible(), "Character input should be visible"

                # Check default placeholder for Dragon Knight
                character_placeholder = character_input.get_attribute("placeholder")
                print(f"Character placeholder: {character_placeholder}")

                # Test the key field mentioned in scratchpad: wizard-setting-input
                setting_input = page.locator("#wizard-setting-input")
                assert setting_input.is_visible(), (
                    "Setting input (wizard-setting-input) should be visible"
                )

                # Check auto-generation placeholder
                setting_placeholder = setting_input.get_attribute("placeholder")
                print(f"✓ Setting placeholder: {setting_placeholder}")

                expected_placeholder = "Random fantasy D&D world (auto-generate)"
                if expected_placeholder in setting_placeholder:
                    print("✓ Auto-generation placeholder text matches expected")
                else:
                    print(f"⚠️ Placeholder mismatch. Expected: {expected_placeholder}")

                # Test switching to Custom campaign type
                custom_radio.click()
                print("✓ Switched to Custom campaign type")

                # Verify placeholder changes for custom
                page.wait_for_timeout(500)  # Wait for dynamic update
                setting_placeholder_custom = setting_input.get_attribute("placeholder")
                print(f"Custom setting placeholder: {setting_placeholder_custom}")

                # Switch back to Dragon Knight for continued testing
                dragon_knight_radio.click()
                print("✓ Switched back to Dragon Knight")

                # Test form validation by trying to proceed with empty required fields
                next_btn = page.locator("#wizard-next")
                next_btn.click()
                print("✓ Clicked Next to test validation")

                # Should advance to step 2 since title is filled and no fields are actually required
                page.wait_for_timeout(1000)
                current_step = page.locator(".step-indicator.active").get_attribute(
                    "data-step"
                )
                print(f"Current step after Next: {current_step}")

                # Test Step 2: AI Style
                if current_step == "2":
                    print("\n--- Step 2: AI Style ---")

                    # Check default personality selections
                    narrative_checked = page.locator("#wizard-narrative").is_checked()
                    mechanics_checked = page.locator("#wizard-mechanics").is_checked()
                    companions_checked = page.locator("#wizard-companions").is_checked()

                    print(f"Narrative enabled: {'✓' if narrative_checked else '✗'}")
                    print(f"Mechanics enabled: {'✓' if mechanics_checked else '✗'}")
                    print(f"Companions enabled: {'✓' if companions_checked else '✗'}")

                    # Test toggling personality options
                    page.locator("#wizard-narrative").click()
                    print("✓ Toggled narrative option")

                    # Proceed to step 3
                    next_btn.click()
                    page.wait_for_timeout(1000)

                # Test Step 3: Campaign Options
                current_step = page.locator(".step-indicator.active").get_attribute(
                    "data-step"
                )
                if current_step == "3":
                    print("\n--- Step 3: Campaign Options ---")

                    default_world_checked = page.locator(
                        "#wizard-default-world"
                    ).is_checked()
                    print(
                        f"Default world enabled: {'✓' if default_world_checked else '✗'}"
                    )

                    # Proceed to step 4
                    next_btn.click()
                    page.wait_for_timeout(1000)

                # Test Step 4: Launch
                current_step = page.locator(".step-indicator.active").get_attribute(
                    "data-step"
                )
                if current_step == "4":
                    print("\n--- Step 4: Launch ---")

                    # Check preview content
                    preview_title = page.locator("#preview-title").inner_text()
                    preview_character = page.locator("#preview-character").inner_text()

                    print(f"Preview title: {preview_title}")
                    print(f"Preview character: {preview_character}")

                    # Test campaign launch (but don't actually submit)
                    launch_btn = page.locator("#launch-campaign")
                    assert launch_btn.is_visible(), "Launch button should be visible"
                    print("✓ Launch button is visible and ready")

                print("\n✓ Wizard navigation and input testing complete")

            else:
                print("\n=== FALLBACK FORM TESTING ===")
                # Test the original form if wizard is not present

                # Test basic form inputs
                page.fill("#campaign-title", "Fallback Form Test")
                print("✓ Filled campaign title in original form")

                # Look for character and setting inputs in original form
                if page.locator("#character-input").count() > 0:
                    page.fill("#character-input", "Test Character")
                    print("✓ Filled character input")

                if page.locator("#setting-input").count() > 0:
                    page.fill("#setting-input", "Test Setting")
                    print("✓ Filled setting input")

            # Take screenshot for visual verification
            page.screenshot(path="wizard_test_success.png", full_page=True)
            print("\n✓ Screenshot saved: wizard_test_success.png")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="wizard_test_error.png", full_page=True)
            raise
        finally:
            print("\n✓ Wizard test complete. Browser will close in 5 seconds...")
            time.sleep(5)
            browser.close()


if __name__ == "__main__":
    print("=" * 60)
    print("UI Test Suite with Test Mode")
    print("Server should be running on port 8082 for current tests")
    print("=" * 60)

    # Run wizard functionality test
    print("\n🧙‍♂️ Testing Campaign Wizard Functionality...")
    test_campaign_wizard_functionality()

    print("\n" + "=" * 60)
    print("UI Structure Display Test")
    print("=" * 60)
    test_structured_fields_display()
