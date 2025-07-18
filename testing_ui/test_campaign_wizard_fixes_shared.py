#!/usr/bin/env python3
"""
Refactored browser test using shared testing utilities.
Demonstrates code sharing between browser and HTTP tests.
"""

import os
import sys

from playwright.sync_api import expect, sync_playwright

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import shared testing utilities
from testing_shared import (
    TEST_SCENARIOS,
    generate_test_user_id,
    get_test_url,
    validate_character_name_display,
    validate_no_hardcoded_text,
)

# Test configuration using shared utilities
TEST_USER_ID = generate_test_user_id("wizard-fixes-browser")


def test_campaign_wizard_character_display_shared():
    """Test character display using shared test data and validation"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print(
                "🧪 Testing campaign wizard character display fix (with shared utilities)..."
            )

            # Use shared test data
            scenario = TEST_SCENARIOS["custom_character_display"]
            campaign_data = scenario["campaign_data"]
            expected_character = scenario["expected_character"]

            # Navigate using shared URL helper
            test_url = get_test_url("browser", TEST_USER_ID)
            page.goto(test_url)
            page.wait_for_load_state("networkidle")
            print("✓ Navigated to app in test mode")

            # Create campaign with shared test data
            page.click("button#go-to-new-campaign")
            page.wait_for_timeout(1000)

            page.wait_for_selector(".wizard-container", state="visible")
            print("✓ Campaign wizard loaded")

            # Fill form using shared campaign data
            page.fill("#wizard-campaign-title", campaign_data["title"])
            page.fill("#wizard-character-input", campaign_data["character_name"])
            page.fill("#wizard-setting-input", campaign_data["setting"])
            print(
                f"✓ Filled form with shared test data: {campaign_data['character_name']}"
            )

            # Navigate through wizard steps
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            print("✓ Navigated to confirmation screen")

            # Validate using shared validation functions
            character_preview = page.locator("#preview-character")
            expect(character_preview).to_be_visible()
            character_text = character_preview.text_content()
            print(f"✓ Character preview text: '{character_text}'")

            # Use shared validation
            validate_character_name_display(
                character_text, expected_character, "browser"
            )
            print("✅ SUCCESS: Shared validation passed for character display!")

            # Test description validation
            description_preview = page.locator("#preview-description")
            description_text = description_preview.text_content()
            validate_no_hardcoded_text(description_text, "browser")
            print("✅ SUCCESS: Shared validation passed for description!")

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            page.screenshot(path="test_character_display_shared_error.png")
            raise
        finally:
            browser.close()


def test_campaign_wizard_empty_character_shared():
    """Test empty character handling using shared test data"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("\n🧪 Testing empty character handling (with shared utilities)...")

            # Use shared test data for empty character scenario
            scenario = TEST_SCENARIOS["empty_character_handling"]
            campaign_data = scenario["campaign_data"]

            # Navigate using shared URL helper
            test_url = get_test_url("browser", TEST_USER_ID + "-empty")
            page.goto(test_url)
            page.wait_for_load_state("networkidle")

            # Create campaign with shared test data (empty character)
            page.click("button#go-to-new-campaign")
            page.wait_for_timeout(1000)

            page.wait_for_selector(".wizard-container", state="visible")

            # Select custom campaign type
            page.click("#wizard-custom-campaign")
            page.wait_for_timeout(500)

            # Fill form with shared data (empty character)
            page.fill("#wizard-campaign-title", campaign_data["title"])
            page.fill(
                "#wizard-character-input", campaign_data["character_name"]
            )  # Empty
            page.fill("#wizard-setting-input", campaign_data["setting"])
            print("✓ Filled form with empty character using shared data")

            # Navigate to confirmation
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)
            page.click("button:has-text('Next')")
            page.wait_for_timeout(500)

            # Validate auto-generated character
            character_preview = page.locator("#preview-character")
            expect(character_preview).to_be_visible()
            character_text = character_preview.text_content()
            print(f"✓ Character preview for empty input: '{character_text}'")

            # Validate auto-generation behavior
            assert (
                "Auto-generated" in character_text or len(character_text.strip()) > 0
            ), f"Expected auto-generated character but got: {character_text}"
            assert "Ser Arion" not in character_text, (
                f"Found Dragon Knight default: {character_text}"
            )
            print(
                "✅ SUCCESS: Empty character handling working with shared validation!"
            )

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            page.screenshot(path="test_empty_character_shared_error.png")
            raise
        finally:
            browser.close()


def main():
    """Run all browser tests with shared utilities"""
    print("=" * 60)
    print("🚀 Running Browser Tests with Shared Utilities")
    print("=" * 60)

    # Test 1: Character display with shared validation
    test_campaign_wizard_character_display_shared()

    # Test 2: Empty character with shared data
    test_campaign_wizard_empty_character_shared()

    print("\n" + "=" * 60)
    print("✅ All browser tests with shared utilities passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
