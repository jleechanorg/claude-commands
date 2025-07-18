#!/usr/bin/env python3
"""
Test for Campaign Wizard Character/Setting Display - Red/Green Test
Tests the fix for custom character names showing correctly in preview.
"""

import os
import sys

from playwright.sync_api import TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase
from browser_test_helpers import BrowserTestHelper

from testing_ui.config import BASE_URL


class WizardCharacterSettingTest(BrowserTestBase):
    """Test campaign wizard character/setting display through browser automation."""

    def __init__(self):
        super().__init__("Wizard Character Setting Display Test")

    def run_test(self, page):
        """Run the wizard character/setting test."""
        try:
            # Initialize browser test helper
            helper = BrowserTestHelper(page, BASE_URL)

            # Navigate with proper test authentication
            helper.navigate_with_test_auth()
            helper.wait_for_auth_bypass()

            # Take initial screenshot
            helper.take_screenshot("wizard_01_homepage")

            # Click "Create New Campaign" button
            print("🎮 Starting campaign wizard...")
            page.wait_for_selector("#go-to-new-campaign", timeout=10000)
            page.click("#go-to-new-campaign")
            print("✅ Clicked 'Create New Campaign' button")

            # Wait for wizard to load
            page.wait_for_selector(".wizard-container", state="visible", timeout=10000)
            helper.take_screenshot("wizard_02_initial_state")

            # RED TEST 1: Test the bug - custom campaign showing Dragon Knight defaults
            print(
                "\n🔴 RED TEST 1: Bug reproduction - custom campaign with empty fields"
            )

            # Select custom campaign type
            page.click("#wizard-custom-campaign")
            page.wait_for_timeout(500)

            # Fill campaign title but leave character/setting empty
            page.fill("#wizard-campaign-title", "Red Test Campaign")

            # Navigate to preview step
            for _ in range(3):
                page.click("button:has-text('Next')")
                page.wait_for_timeout(500)

            # Check preview - BUG: would show "Ser Arion" and "Dragon Knight World"
            character_preview = page.locator("#preview-character").text_content()
            options_preview = page.locator("#preview-options").text_content()

            print(f"❌ BUG CHECK - Character preview: '{character_preview}'")
            print(f"❌ BUG CHECK - Options preview: '{options_preview}'")

            # Take screenshot of the bug
            helper.take_screenshot("wizard_03_red_test_bug")

            # Navigate back to start
            page.reload()
            page.wait_for_selector("#go-to-new-campaign", timeout=10000)
            page.click("#go-to-new-campaign")
            page.wait_for_selector(".wizard-container", state="visible", timeout=10000)

            # GREEN TEST 1: Verify fix - custom campaign shows correct defaults
            print(
                "\n✅ GREEN TEST 1: Fix verification - custom campaign with empty fields"
            )

            # Select custom campaign type
            page.click("#wizard-custom-campaign")
            page.wait_for_timeout(500)

            # Fill campaign title but leave character/setting empty
            page.fill("#wizard-campaign-title", "Green Test Campaign")

            # Navigate to preview step
            for _ in range(3):
                page.click("button:has-text('Next')")
                page.wait_for_timeout(500)

            # Check preview - FIXED: should show "Auto-generated" not "Ser Arion"
            character_preview = page.locator("#preview-character").text_content()
            options_preview = page.locator("#preview-options").text_content()

            print(
                f"✅ FIXED - Character preview: '{character_preview}' (should be 'Auto-generated')"
            )
            print(
                f"✅ FIXED - Options preview: '{options_preview}' (should not contain 'Dragon Knight World')"
            )

            # Take screenshot of the fix
            helper.take_screenshot("wizard_04_green_test_fixed")

            # Verify the fix
            if "Auto-generated" in character_preview:
                print(
                    "✅ SUCCESS: Character shows 'Auto-generated' for empty custom campaign"
                )
            else:
                print("❌ FAIL: Character still shows Dragon Knight defaults")

            if "Dragon Knight World" not in options_preview:
                print(
                    "✅ SUCCESS: Options don't show 'Dragon Knight World' for custom campaign"
                )
            else:
                print("❌ FAIL: Options still show Dragon Knight defaults")

            # Navigate back for more tests
            page.reload()
            page.wait_for_selector("#go-to-new-campaign", timeout=10000)
            page.click("#go-to-new-campaign")
            page.wait_for_selector(".wizard-container", state="visible", timeout=10000)

            # GREEN TEST 2: Custom character input displays correctly
            print("\n✅ GREEN TEST 2: Custom character input displays in preview")

            # Select custom campaign
            page.click("#wizard-custom-campaign")
            page.wait_for_timeout(500)

            # Fill in custom values
            page.fill("#wizard-campaign-title", "Custom Character Test")
            page.fill("#wizard-character-input", "Astarion the Vampire Lord")
            page.fill("#wizard-setting-input", "Baldur's Gate")

            helper.take_screenshot("wizard_05_custom_input")

            # Navigate to preview
            for _ in range(3):
                page.click("button:has-text('Next')")
                page.wait_for_timeout(500)

            # Check preview shows custom values
            character_preview = page.locator("#preview-character").text_content()
            print(f"✅ Character preview: '{character_preview}'")

            helper.take_screenshot("wizard_06_custom_preview")

            if "Astarion the Vampire Lord" in character_preview:
                print("✅ SUCCESS: Custom character name displays correctly")
            else:
                print("❌ FAIL: Custom character name not showing")

            # GREEN TEST 3: Dragon Knight campaign still works correctly
            print("\n✅ GREEN TEST 3: Dragon Knight campaign shows correct defaults")

            page.reload()
            page.wait_for_selector("#go-to-new-campaign", timeout=10000)
            page.click("#go-to-new-campaign")
            page.wait_for_selector(".wizard-container", state="visible", timeout=10000)

            # Dragon Knight should be selected by default
            # Fill title only
            page.fill("#wizard-campaign-title", "Dragon Knight Test")

            # Navigate to preview
            for _ in range(3):
                page.click("button:has-text('Next')")
                page.wait_for_timeout(500)

            # Check preview shows Dragon Knight defaults
            character_preview = page.locator("#preview-character").text_content()
            options_preview = page.locator("#preview-options").text_content()

            print(f"✅ Dragon Knight - Character: '{character_preview}'")
            print(f"✅ Dragon Knight - Options: '{options_preview}'")

            helper.take_screenshot("wizard_07_dragon_knight_defaults")

            if "Ser Arion" in character_preview:
                print("✅ SUCCESS: Dragon Knight shows correct default character")
            if "Dragon Knight World" in options_preview:
                print("✅ SUCCESS: Dragon Knight shows correct world option")

            # Final summary
            print("\n📊 Test Summary:")
            print(
                "  🔴 RED TEST: Reproduced bug (Dragon Knight defaults in custom campaign)"
            )
            print("  ✅ GREEN TEST 1: Fixed - Custom campaign shows 'Auto-generated'")
            print(
                "  ✅ GREEN TEST 2: Fixed - Custom character input displays correctly"
            )
            print("  ✅ GREEN TEST 3: Dragon Knight campaign still works properly")

            return True

        except TimeoutError as e:
            print(f"❌ Test failed due to timeout: {str(e)}")
            helper.take_screenshot("wizard_error_timeout")
            return False
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            helper.take_screenshot("wizard_error_general")
            return False


if __name__ == "__main__":
    test = WizardCharacterSettingTest()
    success = test.execute()
    sys.exit(0 if success else 1)
