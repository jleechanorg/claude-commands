#!/usr/bin/env python3
"""
Browser test specifically for structured fields display after campaign creation.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase
from browser_test_helpers import BrowserTestHelper

from testing_ui.config import BASE_URL, SCREENSHOT_DIR


class StructuredFieldsCampaignTest(BrowserTestBase):
    """Test structured fields display in campaigns."""

    def __init__(self):
        super().__init__("Structured Fields Campaign Test")

    def run_test(self, page):
        """Run the structured fields test."""
        try:
            # Initialize browser test helper
            helper = BrowserTestHelper(page, BASE_URL)

            # Navigate with test auth
            helper.navigate_with_test_auth()
            helper.wait_for_auth_bypass()

            # Create a campaign using the helper
            print("🎮 Creating test campaign...")
            if not helper.create_test_campaign(
                "Structured Fields Test", debug_mode=True
            ):
                print("❌ Failed to create campaign")
                return False

            # Wait for game view to be ready
            page.wait_for_timeout(3000)

            # Check initial state - might not have structured fields yet
            print("\n🔍 Checking initial state after campaign creation...")
            helper.take_screenshot("structured_01_initial_state")

            # Make a character mode interaction to trigger structured response
            print("\n📝 Making character mode interaction...")
            page.fill("#user-input", "I look around the area")
            page.click("#char-mode")  # Ensure character mode is selected
            page.click('button[type="submit"]')

            # Wait for AI response
            print("⏳ Waiting for AI response with structured fields...")
            page.wait_for_selector(".story-entry:has-text('Story:')", timeout=30000)

            # Wait a bit more for all fields to render
            page.wait_for_timeout(3000)

            # Now check for structured fields
            print("\n🔍 Checking for structured fields...")

            fields_found = []
            fields_missing = []

            # Check session header
            if page.query_selector(".session-header"):
                fields_found.append("Session Header")
                print("✅ Session header found!")
            else:
                fields_missing.append("Session Header")
                print("❌ Session header NOT found")

            # Check planning block/choices
            if page.query_selector(".planning-block") or page.query_selector(
                ".choice-button"
            ):
                fields_found.append("Planning Block")
                print("✅ Planning block/choices found!")
            else:
                fields_missing.append("Planning Block")
                print("❌ Planning block NOT found")

            # Check dice rolls
            if page.query_selector(".dice-rolls"):
                fields_found.append("Dice Rolls")
                print("✅ Dice rolls found!")
            else:
                fields_missing.append("Dice Rolls")
                print("❌ Dice rolls NOT found")

            # Check resources
            if page.query_selector(".resources"):
                fields_found.append("Resources")
                print("✅ Resources field found!")
            else:
                fields_missing.append("Resources")
                print("❌ Resources field NOT found")

            # Check entities mentioned
            if page.query_selector(".entities-mentioned"):
                fields_found.append("Entities Mentioned")
                print("✅ Entities mentioned found!")
            else:
                fields_missing.append("Entities Mentioned")
                print("❌ Entities mentioned NOT found")

            # Check location confirmed
            if page.query_selector(".location-confirmed"):
                fields_found.append("Location Confirmed")
                print("✅ Location confirmed found!")
            else:
                fields_missing.append("Location Confirmed")
                print("❌ Location confirmed NOT found")

            # Check state updates (in debug mode)
            if page.query_selector(".state-updates"):
                fields_found.append("State Updates")
                print("✅ State updates found!")
            else:
                fields_missing.append("State Updates")
                print("❌ State updates NOT found")

            # Check debug info (in debug mode)
            if page.query_selector(".dm-notes") or page.query_selector(
                ".state-rationale"
            ):
                fields_found.append("Debug Info")
                print("✅ Debug info found!")
            else:
                fields_missing.append("Debug Info")
                print("❌ Debug info NOT found")

            # Take screenshot of structured fields
            helper.take_screenshot("structured_02_after_interaction")

            # Make a god mode interaction to check god mode response field
            print("\n🔮 Testing god mode interaction...")
            page.fill("#user-input", "What secrets are in this area?")
            page.click("#god-mode")
            page.click('button[type="submit"]')

            # Wait for god mode response
            page.wait_for_timeout(5000)

            # Check for god mode response field
            if page.query_selector(".god-mode-response"):
                fields_found.append("God Mode Response")
                print("✅ God mode response found!")
            else:
                fields_missing.append("God Mode Response")
                print("❌ God mode response NOT found")

            helper.take_screenshot("structured_03_god_mode")

            # Summary
            print("\n📊 Summary:")
            print(f"   ✅ Fields found: {len(fields_found)}")
            print(f"   ❌ Fields missing: {len(fields_missing)}")

            if fields_found:
                print(f"   Found: {', '.join(fields_found)}")
            if fields_missing:
                print(f"   Missing: {', '.join(fields_missing)}")

            # Test passes if we found at least some structured fields
            success = len(fields_found) > 0

            if success:
                print("\n✅ Structured fields are being displayed!")
            else:
                print("\n❌ No structured fields found!")

            return success

        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            helper.take_screenshot("structured_error")
            return False


def test_structured_fields_campaign():
    """Entry point for standalone execution."""
    test = StructuredFieldsCampaignTest()
    return test.execute()


if __name__ == "__main__":
    print("🚀 Starting Structured Fields Campaign Test")
    print(f"📸 Screenshots will be saved to: {SCREENSHOT_DIR}")

    success = test_structured_fields_campaign()

    if success:
        print("\n✅ TEST PASSED - Structured fields displayed")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - Structured fields not working")
        sys.exit(1)
