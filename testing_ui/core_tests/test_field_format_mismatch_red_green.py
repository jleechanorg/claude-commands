#!/usr/bin/env python3
"""
RED-GREEN TEST: Field Format Mismatch Detection
==============================================

This test specifically catches the architectural boundary bug where:
- world_logic.py creates story entries with {"story": "content"}
- main.py translation layer expects {"text": "content"}

RED PHASE: Test should FAIL with empty narrative due to field mismatch
GREEN PHASE: Test should PASS after fixing field format consistency

This test validates the full browser interaction flow to catch UI-visible bugs.
"""

import os
import sys
import tempfile

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_field_format_mismatch_detection():
    """
    RED-GREEN test for field format mismatch in character creation.

    This test specifically validates that character interaction produces
    visible narrative content in the browser UI, catching the architectural
    boundary bug between story creation and translation layers.
    """

    # Create screenshots directory
    screenshots_dir = os.path.join(
        tempfile.gettempdir(),
        "worldarchitectai",
        "red_green_test",
    )
    os.makedirs(screenshots_dir, exist_ok=True)

    print("\n" + "=" * 70)
    print("🔴 RED-GREEN TEST: Field Format Mismatch Detection")
    print("=" * 70)
    print("Testing architectural boundary between world_logic.py and main.py")
    print("Expected: Should FAIL in RED phase due to empty narrative")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        try:
            # Step 1: Navigate with test auth bypass
            print("\n🌐 Step 1: Loading app with test auth bypass...")
            page.goto(
                "http://localhost:8081?test_mode=true&test_user_id=red-green-test-user"
            )

            # Wait for test mode initialization
            page.wait_for_function("window.testAuthBypass !== undefined", timeout=10000)
            page.wait_for_selector("#campaign-list", timeout=15000)
            print("✓ Test auth bypass initialized")

            # Screenshot initial state
            page.screenshot(
                path=f"{screenshots_dir}/01_auth_bypass_loaded.png", full_page=True
            )

            # Step 2: Start campaign creation
            print("\n🎯 Step 2: Starting campaign creation...")
            start_button = page.locator("text=Start New Campaign")
            start_button.click()
            page.wait_for_selector("#campaign-wizard-step-1", timeout=10000)
            print("✓ Campaign wizard started")

            # Fill wizard step 1
            page.fill("#campaign-title", "Red-Green Field Format Test")
            page.fill(
                "#campaign-description", "Testing field format mismatch detection"
            )
            page.select_option("#genre-select", "Fantasy")
            page.select_option("#tone-select", "Epic")
            page.click("text=Next")

            # Wait for step 2 and fill character info
            page.wait_for_selector("#campaign-wizard-step-2", timeout=10000)
            page.fill("#character-name", "Test Character")
            page.fill(
                "#character-background", "A test character for field format validation"
            )
            page.click("text=Next")

            # Wait for step 3 and create campaign
            page.wait_for_selector("#campaign-wizard-step-3", timeout=10000)

            # Screenshot before creation
            page.screenshot(
                path=f"{screenshots_dir}/02_before_campaign_creation.png",
                full_page=True,
            )

            print("\n🚀 Step 3: Creating campaign (this should expose the bug)...")
            create_button = page.locator("text=Create Campaign")
            create_button.click()

            # Wait for campaign creation and redirect to game view
            print("⏳ Waiting for campaign creation...")
            page.wait_for_selector("#game-view", timeout=60000)
            page.wait_for_selector("#story-content", timeout=15000)
            print("✓ Game view loaded")

            # Screenshot game view
            page.screenshot(
                path=f"{screenshots_dir}/03_game_view_loaded.png", full_page=True
            )

            # Step 4: Check for initial story content (this is where the bug manifests)
            print("\n🔍 Step 4: Analyzing initial story content...")

            # Look for story entries in the UI
            story_entries = page.locator(".story-entry").all()
            print(f"Found {len(story_entries)} story entries")

            # Check if story content has actual narrative text
            empty_entries = 0

            for i, entry in enumerate(story_entries):
                entry_text = entry.inner_text().strip()
                print(f"Entry {i + 1} length: {len(entry_text)} characters")

                if len(entry_text) > 50:  # Meaningful narrative should be substantial
                    print(
                        f"✓ Entry {i + 1} has substantial content: {entry_text[:100]}..."
                    )
                else:
                    empty_entries += 1
                    print(f"⚠️  Entry {i + 1} appears empty or minimal: '{entry_text}'")

            # Screenshot story content area
            page.screenshot(
                path=f"{screenshots_dir}/04_story_content_analysis.png", full_page=True
            )

            # Step 5: Test character interaction (the critical test)
            print("\n💬 Step 5: Testing character interaction (critical test)...")

            user_input = page.locator("#user-input")
            test_message = "I look around. What do I see?"

            user_input.fill(test_message)
            print(f"✓ Typed test message: {test_message}")

            # Screenshot before sending
            page.screenshot(
                path=f"{screenshots_dir}/05_before_interaction.png", full_page=True
            )

            # Send message and wait for response
            user_input.press("Enter")
            print("✓ Sent message - waiting for AI response...")

            # Wait for response processing to complete
            page.wait_for_function(
                "document.querySelector('#user-input').disabled === false",
                timeout=60000,
            )
            page.wait_for_timeout(3000)  # Allow DOM to update

            # Screenshot after interaction
            page.screenshot(
                path=f"{screenshots_dir}/06_after_interaction.png", full_page=True
            )

            # Step 6: Validate response content (THE CRITICAL ASSERTION)
            print("\n📊 Step 6: Validating AI response content...")

            # Get all story entries after interaction
            final_story_entries = page.locator(".story-entry").all()
            print(f"Total story entries after interaction: {len(final_story_entries)}")

            # Look for the AI response (should be the last entry)
            if len(final_story_entries) > len(story_entries):
                latest_entry = final_story_entries[-1]
                response_text = latest_entry.inner_text().strip()

                print(f"AI response length: {len(response_text)} characters")
                print(f"AI response preview: {response_text[:200]}...")

                # Screenshot the latest response
                latest_entry.screenshot(
                    path=f"{screenshots_dir}/07_ai_response_content.png"
                )

                # THE CRITICAL TEST: Check if response has substantial content
                if len(response_text) > 100:  # AI responses should be substantial
                    print("✅ RED-GREEN TEST RESULT: PASS - AI response has content")
                    test_result = "PASS"
                else:
                    print(
                        "❌ RED-GREEN TEST RESULT: FAIL - AI response is empty/minimal"
                    )
                    test_result = "FAIL"

                    # Additional debugging for failure case
                    print("\n🔍 DEBUGGING EMPTY RESPONSE:")
                    print(f"   Response HTML: {latest_entry.inner_html()[:500]}...")

                    # Check for error indicators
                    if "[Error: No response from server]" in response_text:
                        print(
                            "   🎯 DETECTED: '[Error: No response from server]' - This is the target bug!"
                        )

            else:
                print("❌ RED-GREEN TEST RESULT: FAIL - No AI response detected")
                test_result = "FAIL"

            # Final screenshot
            page.screenshot(
                path=f"{screenshots_dir}/08_final_test_state.png", full_page=True
            )

            print("\n" + "=" * 70)
            print(f"🏁 RED-GREEN TEST COMPLETE: {test_result}")
            print("=" * 70)
            print(f"📁 Screenshots saved to: {screenshots_dir}")

            if test_result == "FAIL":
                print(
                    "🔴 RED PHASE: Test correctly identifies the field format mismatch bug"
                )
                print(
                    "   Expected behavior: This test should FAIL until the bug is fixed"
                )
            else:
                print(
                    "🟢 GREEN PHASE: Test passes - field format mismatch has been fixed"
                )

            print("=" * 70)

            return test_result == "PASS"

        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            page.screenshot(
                path=f"{screenshots_dir}/ERROR_test_exception.png", full_page=True
            )
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    print("🔴 Red-Green Test: Field Format Mismatch Detection")
    print("⚠️  Make sure server is running with mock APIs:")
    print("   ./run_ui_tests.sh mock --playwright")
    print(
        "   OR: USE_MOCK_FIREBASE=true USE_MOCK_GEMINI=true PORT=8081 python main.py serve"
    )
    print("-" * 70)

    success = test_field_format_mismatch_detection()

    if success:
        print("\n🟢 Test PASSED - Field format is working correctly")
        sys.exit(0)
    else:
        print("\n🔴 Test FAILED - Field format mismatch detected")
        sys.exit(1)
