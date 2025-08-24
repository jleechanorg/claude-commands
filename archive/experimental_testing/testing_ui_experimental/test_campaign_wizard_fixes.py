#!/usr/bin/env python3
"""
Test for campaign wizard fixes:
1. Custom character name displays correctly on confirmation screen
2. Campaign page loads with full story content after creation
"""

import os
import sys
import time

from playwright.sync_api import expect, sync_playwright

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test configuration
BASE_URL = "http://localhost:8081"
TEST_USER_ID = "test-wizard-fixes-" + str(int(time.time()))


def test_campaign_wizard_character_display():
    """Test that custom character names display correctly in confirmation screen"""

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("🧪 Testing campaign wizard character display fix...")

            # Navigate to the app with test mode parameters
            page.goto(f"{BASE_URL}?test_mode=true&test_user_id={TEST_USER_ID}")
            page.wait_for_load_state("networkidle")
            print("✓ Navigated to app in test mode")

            # Click "Create New Campaign" button
            page.click("button#go-to-new-campaign")
            page.wait_for_timeout(1000)
            print("✓ Clicked create new campaign")

            # Wait for wizard to load
            page.wait_for_selector(".wizard-container", state="visible")
            print("✓ Campaign wizard loaded")

            # Step 1: Fill in basic info with custom character
            page.fill("#wizard-campaign-title", "Test Character Display Campaign")
            page.fill("#wizard-character-input", "Sir TestCharacter the Bold")
            page.fill("#wizard-setting-input", "A mystical test realm")
            print("✓ Filled in basic campaign info with custom character")

            # Click Next to go to step 2
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            print("✓ Proceeded to AI Personality step")

            # Step 2: Keep default AI personality selections and click Next
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            print("✓ Proceeded to Custom Options step")

            # Step 3: Keep default options and click Next
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            print("✓ Proceeded to Launch/Confirmation step")

            # Step 4: Verify character name appears in confirmation
            character_preview = page.locator("#preview-character")
            expect(character_preview).to_be_visible()
            character_text = character_preview.text_content()
            print(f"✓ Character preview element found with text: '{character_text}'")

            # Verify it shows our custom character name, not "dragon knight" or default
            assert "Sir TestCharacter the Bold" in character_text, (
                f"Expected custom character name but got: {character_text}"
            )
            assert "dragon knight" not in character_text.lower(), (
                f"Found 'dragon knight' in character preview: {character_text}"
            )
            print(
                "✅ SUCCESS: Custom character name displays correctly in confirmation!"
            )

            # Also verify the description doesn't show hardcoded dragon knight text
            description_preview = page.locator("#preview-description")
            description_text = description_preview.text_content()
            assert "ser arion dragon knight campaign" not in description_text.lower(), (
                f"Found hardcoded dragon knight text in description: {description_text}"
            )
            print("✅ SUCCESS: No hardcoded 'dragon knight' text in description!")

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            # Take screenshot for debugging
            page.screenshot(path="test_character_display_error.png")
            raise
        finally:
            browser.close()


def test_campaign_wizard_empty_character_display():
    """Test that empty character input shows 'Auto-generated' in preview"""

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("\n🧪 Testing campaign wizard empty character display...")

            # Navigate to the app with test mode parameters
            page.goto(f"{BASE_URL}?test_mode=true&test_user_id={TEST_USER_ID}-empty")
            page.wait_for_load_state("networkidle")
            print("✓ Navigated to app in test mode")

            # Click "Create New Campaign" button
            page.click("button#go-to-new-campaign")
            page.wait_for_timeout(1000)
            print("✓ Clicked create new campaign")

            # Wait for wizard to load
            page.wait_for_selector(".wizard-container", state="visible")
            print("✓ Campaign wizard loaded")

            # Select custom campaign type (not Dragon Knight)
            page.click("#wizard-custom-campaign")
            page.wait_for_timeout(500)
            print("✓ Selected custom campaign type")

            # Step 1: Fill in title but leave character empty
            page.fill("#wizard-campaign-title", "Test Empty Character Campaign")
            # Explicitly clear the character input to ensure it's empty
            page.fill("#wizard-character-input", "")
            page.fill("#wizard-setting-input", "A mystical test realm")
            print("✓ Filled in campaign info with empty character field")

            # Click Next to go to step 2
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            print("✓ Proceeded to AI Personality step")

            # Step 2: Keep default AI personality selections and click Next
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            print("✓ Proceeded to Custom Options step")

            # Step 3: Keep default options and click Next
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            print("✓ Proceeded to Launch/Confirmation step")

            # Step 4: Verify character shows 'Auto-generated' in confirmation
            character_preview = page.locator("#preview-character")
            expect(character_preview).to_be_visible()
            character_text = character_preview.text_content()
            print(f"✓ Character preview element found with text: '{character_text}'")

            # Verify it shows 'Auto-generated' for empty input
            assert "Auto-generated" in character_text, (
                f"Expected 'Auto-generated' for empty character but got: {character_text}"
            )
            assert "Ser Arion" not in character_text, (
                f"Found Dragon Knight default in character preview: {character_text}"
            )
            print("✅ SUCCESS: Empty character input shows 'Auto-generated' correctly!")

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            # Take screenshot for debugging
            page.screenshot(path="test_empty_character_error.png")
            raise
        finally:
            browser.close()


def test_campaign_page_loads_with_story():
    """Test that campaign page loads with full story content after creation"""

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("\n🧪 Testing campaign page loading fix...")

            # Navigate to the app with test mode parameters
            page.goto(f"{BASE_URL}?test_mode=true&test_user_id={TEST_USER_ID}-story")
            page.wait_for_load_state("networkidle")
            print("✓ Navigated to app in test mode")

            # Create a campaign using the quick form (not wizard)
            page.click("button#go-to-new-campaign")
            page.wait_for_timeout(1000)

            # Close wizard if it appears and use regular form
            if page.locator(".wizard-container").is_visible():
                page.click(".wizard-close")
                page.wait_for_timeout(500)

            # Fill in the regular campaign form
            page.fill("#campaign-title", "Test Story Loading Campaign")
            page.fill("#character-input", "Test Hero")
            page.fill("#setting-input", "Test Kingdom")
            page.fill(
                "#description-input",
                "A brave hero begins their journey in a mystical kingdom.",
            )
            print("✓ Filled in campaign form")

            # Submit the form
            page.click("button[type='submit']:has-text('Start Campaign')")
            print("✓ Submitted campaign form")

            # Wait for navigation to campaign page
            page.wait_for_url("**/game/**", timeout=10000)
            print("✓ Navigated to campaign page")

            # Wait for story content to load (with retries)
            max_wait_time = 15000  # 15 seconds total
            start_time = time.time()
            story_loaded = False

            while (time.time() - start_time) * 1000 < max_wait_time:
                # Check if story content exists
                story_entries = page.locator(".story-entry")
                if story_entries.count() > 0:
                    story_loaded = True
                    break

                # Check for error messages
                if page.locator(".alert-danger").is_visible():
                    error_text = page.locator(".alert-danger").text_content()
                    print(f"⚠️  Error message displayed: {error_text}")

                page.wait_for_timeout(1000)
                print(
                    f"⏳ Waiting for story content... ({int(time.time() - start_time)}s)"
                )

            assert story_loaded, "Story content did not load within timeout period"

            # Verify we have story entries
            story_count = story_entries.count()
            print(f"✓ Found {story_count} story entries")

            # Verify we have more than just the initial prompt
            assert story_count >= 1, (
                f"Expected at least 1 story entry, but found {story_count}"
            )

            # Check that we have AI response (not just user prompt)
            ai_responses = page.locator(".story-entry:has-text('Scene #')")
            ai_count = ai_responses.count()
            assert ai_count >= 1, (
                f"Expected at least 1 AI response, but found {ai_count}"
            )

            print("✅ SUCCESS: Campaign page loads with full story content!")

            # Verify no error messages are shown
            assert not page.locator(".alert-danger").is_visible(), (
                "Error alert should not be visible"
            )
            assert not page.locator(".alert-warning").is_visible(), (
                "Warning alert should not be visible"
            )
            print("✅ SUCCESS: No error messages displayed!")

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            # Take screenshot for debugging
            page.screenshot(path="test_story_loading_error.png")
            raise
        finally:
            browser.close()


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Running Campaign Wizard Fix Tests")
    print("=" * 60)

    # Test 1: Character display in confirmation
    test_campaign_wizard_character_display()

    # Test 2: Empty character shows 'Auto-generated'
    test_campaign_wizard_empty_character_display()

    # Test 3: Story loading after campaign creation
    test_campaign_page_loads_with_story()

    print("\n" + "=" * 60)
    print("✅ All tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
