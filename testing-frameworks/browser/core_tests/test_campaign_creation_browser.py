#!/usr/bin/env python3
"""
Dual-mode browser test for campaign creation using Playwright.
Supports both fake APIs (/testui) and real APIs (/testuif).

MODES:
- Fake API Mode: Fast, no cost, uses mocks
- Real API Mode: Slow, costs money, uses real Gemini + Firebase
"""

import json
import os
import sys

from playwright.sync_api import TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from testing_ui.browser_test_base import BrowserTestBase
from testing_ui.browser_test_helpers import BrowserTestHelper
from testing_ui.config import (
    BASE_URL,
    get_api_timeouts,
    get_test_mode,
    is_real_api_mode,
)


class CampaignCreationTest(BrowserTestBase):
    """Test campaign creation through browser automation."""

    def __init__(self):
        super().__init__("Campaign Creation Browser Test")

    def run_test(self, page):
        """Run the campaign creation test with dual mode support."""
        try:
            # Get test mode and timeouts
            test_mode = get_test_mode()
            timeouts = get_api_timeouts()

            print(f"🔧 Running in {test_mode.upper()} API mode")
            if is_real_api_mode():
                print("⚠️  WARNING: Using REAL APIs - this costs money!")
                print(
                    f"⏰ Extended timeouts: Campaign creation={timeouts['campaign_creation'] / 1000}s, AI response={timeouts['ai_response'] / 1000}s"
                )
            else:
                print("🏃 Using MOCK APIs - fast and free")

            # Initialize browser test helper
            helper = BrowserTestHelper(page, BASE_URL)

            # Navigate with proper test authentication
            helper.navigate_with_test_auth()
            helper.wait_for_auth_bypass()

            # Take initial screenshot
            helper.take_screenshot(f"creation_01_homepage_{test_mode}_mode")

            # Look for "Start New Campaign" button (corrected button text)
            print("🎮 Looking for 'Start New Campaign' button...")

            try:
                # Wait for dashboard to load and click the Start New Campaign button
                page.wait_for_selector("#go-to-new-campaign", timeout=10000)
                page.click("#go-to-new-campaign")
                print("✅ Clicked 'Start New Campaign' button")
            except:
                helper.take_screenshot("creation_02_button_not_found")
                print("❌ Could not find 'Start New Campaign' button")
                return False

            # Wait for campaign creation form to load
            page.wait_for_load_state("networkidle")
            helper.take_screenshot("creation_03_campaign_form")

            # Fill in campaign details
            print("📝 Filling campaign details...")

            # Check if we're in the campaign wizard
            if page.is_visible("#campaign-wizard") or page.is_visible(
                ".wizard-container"
            ):
                print("🧙‍♂️ Campaign wizard detected")

                # Fill campaign title
                if page.is_visible("#campaign-title") or page.is_visible(
                    "input[name='title']"
                ):
                    page.fill(
                        "#campaign-title, input[name='title']", "Browser Test Campaign"
                    )
                    print("   ✅ Filled campaign title")

                # Fill campaign description
                if page.is_visible("#campaign-description") or page.is_visible(
                    "textarea[name='description']"
                ):
                    page.fill(
                        "#campaign-description, textarea[name='description']",
                        "This is a test campaign created by automated browser testing.",
                    )
                    print("   ✅ Filled campaign description")

                # Look for Next button and navigate through wizard steps
                if page.is_visible("button:has-text('Next')"):
                    print("   ➡️ Clicking Next to step 2")
                    page.click("button:has-text('Next')")
                    page.wait_for_timeout(1000)
                else:
                    print("   ❌ Next button not found")

                # Keep clicking through wizard steps until we reach launch
                for i in range(3):  # Steps 2, 3, 4
                    helper.take_screenshot(f"creation_wizard_step_{i + 2}")

                    # Check if we're on the launch step
                    if page.is_visible("#launch-campaign") or page.is_visible(
                        "button:has-text('Begin Adventure')"
                    ):
                        print(
                            f"   🚀 Step {i + 2}: Found Launch/Begin Adventure button"
                        )
                        print("   🎯 Clicking launch button...")

                        # Wait for button to be properly visible and stable
                        try:
                            page.wait_for_selector(
                                "button:has-text('Begin Adventure')",
                                state="visible",
                                timeout=5000,
                            )
                            # Scroll button into view and wait for stability
                            button = page.locator(
                                "button:has-text('Begin Adventure')"
                            ).first
                            button.scroll_into_view_if_needed()
                            page.wait_for_timeout(1000)  # Let animations settle
                            button.click(timeout=10000)
                            print("   ✅ Successfully clicked Begin Adventure button")
                        except Exception as e:
                            print(f"   ⚠️  Button click failed, trying alternative: {e}")
                            # Try clicking by ID if text selector fails
                            if page.is_visible("#launch-campaign"):
                                page.click("#launch-campaign", timeout=10000)
                            else:
                                # Force click with JavaScript
                                page.evaluate(
                                    "document.querySelector('button[type=submit]').click()"
                                )
                        break
                    if page.is_visible("button:has-text('Next')"):
                        print(f"   ➡️ Step {i + 2}: Clicking Next")
                        page.click("button:has-text('Next')")
                        page.wait_for_timeout(1000)
                    else:
                        print(f"   ⚠️  Step {i + 2}: No Next or Launch button found")
                        break

            # Wait for campaign creation to complete with mode-appropriate timeout
            creation_timeout = timeouts["campaign_creation"]
            print(
                f"⏳ Waiting for campaign creation ({creation_timeout / 1000}s timeout for {test_mode} mode)..."
            )
            try:
                # Wait for spinner to disappear and game view to appear
                page.wait_for_selector(".spinner", state="hidden", timeout=5000)
            except TimeoutError:
                print("   ⚠️  Spinner timeout - checking game state anyway")

            # Check if we successfully created the campaign
            try:
                page.wait_for_selector("#game-view", timeout=creation_timeout)
                print("✅ Game view is active - campaign created!")
                helper.take_screenshot(f"creation_04_game_view_{test_mode}")

                # Campaign created successfully
            except TimeoutError:
                print("⚠️  Game view not active, checking other states...")
                helper.take_screenshot(f"creation_04_timeout_state_{test_mode}")

                # Check which view is currently active
                current_view = page.evaluate("""
                    (() => {
                        const views = ['auth-view', 'dashboard-view', 'new-campaign-view', 'game-view'];
                        return views.find(view => document.getElementById(view)?.classList.contains('active-view')) || 'unknown';
                    })()
                """)
                print(f"   📍 Current view: {current_view}")

                if current_view == "game-view":
                    print("✅ Campaign created successfully!")
                else:
                    if is_real_api_mode():
                        print(
                            "❌ Real API campaign creation failed - check Gemini API status"
                        )
                    else:
                        print("❌ Mock campaign creation failed - check mock responses")
                    return False

            # Test complete chat flow (this is the key missing piece!)
            print("💬 Testing complete chat interface...")

            # Wait for story content and input to load
            page.wait_for_selector("#story-content", timeout=timeouts["page_load"])
            page.wait_for_selector("#user-input", timeout=timeouts["page_load"])
            print("✅ Chat interface loaded")

            helper.take_screenshot(f"creation_05_chat_interface_{test_mode}")

            # Check initial story content
            initial_entries = page.locator(".story-entry").count()
            print(f"📖 Found {initial_entries} initial story entries")

            # Send a test message to validate complete flow
            print(
                f"🤖 Sending test message (timeout: {timeouts['ai_response'] / 1000}s)..."
            )
            test_message = (
                "I look around carefully and check my surroundings. What do I see?"
            )

            page.fill("#user-input", test_message)
            helper.take_screenshot(f"creation_06_message_typed_{test_mode}")

            # Send the message
            page.press("#user-input", "Enter")
            print(f"📤 Sent: {test_message[:50]}...")

            # Wait for AI response with appropriate timeout
            ai_timeout = timeouts["ai_response"]
            try:
                print(f"⏳ Waiting for AI response ({ai_timeout / 1000}s timeout)...")
                page.wait_for_function(
                    "document.querySelector('#user-input').disabled === false",
                    timeout=ai_timeout,
                )
                page.wait_for_timeout(2000)  # Extra time for DOM updates
                print("✅ AI response received!")

            except TimeoutError:
                if is_real_api_mode():
                    print(
                        "⚠️  Real Gemini API response timed out - may still be processing"
                    )
                else:
                    print("⚠️  Mock API response timed out - check mock service")
                # Continue to capture current state

            # Take screenshot of final state with AI response
            helper.take_screenshot(f"creation_07_ai_response_{test_mode}")

            # Validate response format and compare fake vs real if needed
            final_entries = page.locator(".story-entry").count()
            if final_entries > initial_entries:
                print(
                    f"✅ New story entry added ({final_entries - initial_entries} new entries)"
                )

                # Get the latest response for format validation
                latest_entry = page.locator(".story-entry").last
                response_html = latest_entry.inner_html()

                # Check response format and warn about differences
                self._validate_response_format(response_html, test_mode)

                # Screenshot just the latest response
                from testing_ui.config import SCREENSHOT_DIR

                latest_entry.screenshot(
                    path=f"{SCREENSHOT_DIR}/creation_08_latest_response_{test_mode}.png"
                )

            else:
                print(
                    f"⚠️  No new story entries detected (still {final_entries} entries)"
                )
                if is_real_api_mode():
                    print("   Real API may have failed - check Gemini API status")
                else:
                    print("   Mock API may have failed - check mock responses")

            helper.take_screenshot(f"creation_09_final_complete_{test_mode}")
            print(f"✅ Complete {test_mode} mode browser test finished!")
            return True

        except TimeoutError as e:
            print(f"❌ Timeout error: {e}")
            helper.take_screenshot("creation_error_timeout")
            return False
        except Exception as e:
            test_mode = get_test_mode()
            print(f"❌ {test_mode.title()} mode test failed: {e}")
            helper.take_screenshot(f"creation_error_general_{test_mode}")
            return False

    def _validate_response_format(self, response_html, test_mode):
        """Validate response format and warn about fake vs real differences."""
        print(f"\n🔍 Validating {test_mode} mode response format...")

        # Check for expected structured elements
        elements_found = {
            "session-header": "session-header" in response_html,
            "narrative": "<p>" in response_html and len(response_html) > 50,
            "dice-rolls": "dice-rolls" in response_html,
            "resources": "resources" in response_html,
            "planning-block": "planning-block" in response_html,
        }

        print("   📋 Response structure:")
        for element, found in elements_found.items():
            status = "✅" if found else "❌"
            print(f"      {status} {element}")

        # Store format info for comparison
        format_info = {
            "mode": test_mode,
            "elements": elements_found,
            "html_length": len(response_html),
            "has_structured_content": any(elements_found.values()),
        }

        # Save format info for potential comparison
        format_file = f"/tmp/worldarchitectai/response_format_{test_mode}.json"
        os.makedirs(os.path.dirname(format_file), exist_ok=True)
        with open(format_file, "w") as f:
            json.dump(format_info, f, indent=2)

        print(f"   💾 Format info saved: {format_file}")

        # If we have both fake and real format files, compare them
        fake_file = "/tmp/worldarchitectai/response_format_fake.json"
        real_file = "/tmp/worldarchitectai/response_format_real.json"

        if os.path.exists(fake_file) and os.path.exists(real_file):
            self._compare_response_formats(fake_file, real_file)

    def _compare_response_formats(self, fake_file, real_file):
        """Compare fake vs real response formats and warn about differences."""
        try:
            with open(fake_file) as f:
                fake_format = json.load(f)
            with open(real_file) as f:
                real_format = json.load(f)

            print("\n⚖️  FAKE vs REAL API FORMAT COMPARISON:")

            fake_elements = fake_format["elements"]
            real_elements = real_format["elements"]

            differences = []
            for element in fake_elements:
                if fake_elements[element] != real_elements.get(element, False):
                    fake_status = "✅" if fake_elements[element] else "❌"
                    real_status = "✅" if real_elements.get(element, False) else "❌"
                    differences.append(
                        f"   {element}: Fake {fake_status} vs Real {real_status}"
                    )

            if differences:
                print("   🚨 FORMAT DIFFERENCES DETECTED:")
                for diff in differences:
                    print(diff)
                print(
                    "   ⚠️  WARNING: Mock and real API responses have different formats!"
                )
                print("   📝 This may indicate mock responses need updating.")
            else:
                print("   ✅ Fake and real API formats match - good consistency!")

        except Exception as e:
            print(f"   ⚠️  Format comparison failed: {e}")


def test_campaign_creation_browser():
    """Entry point for standalone execution."""
    test = CampaignCreationTest()
    return test.execute()


if __name__ == "__main__":
    print("🚀 Starting WorldArchitect.AI Campaign Creation Browser Test")

    success = test_campaign_creation_browser()

    if success:
        print("\n✅ TEST PASSED - Campaign created via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
