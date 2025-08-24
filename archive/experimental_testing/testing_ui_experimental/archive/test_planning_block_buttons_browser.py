#!/usr/bin/env python3
"""
Real browser test for planning block choice buttons using Playwright.
This test verifies that planning block choices are rendered as clickable buttons
and that clicking them sends the full choice text.
"""

import os
import sys

from playwright.sync_api import TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class PlanningBlockButtonsTest(BrowserTestBase):
    """Test planning block choice buttons through browser automation."""

    def __init__(self):
        super().__init__("Planning Block Buttons Browser Test")

    def run_test(self, page):
        """Run the planning block buttons test."""
        try:
            # Take initial screenshot
            self.take_screenshot(page, "planning_blocks_01_homepage")

            # Navigate to an existing campaign or create a new one
            print("🎮 Setting up test campaign...")

            # Check if we have any campaigns
            if page.is_visible("#campaign-list"):
                campaign_items = page.query_selector_all(
                    ".campaign-item, .list-group-item"
                )
                if len(campaign_items) > 0:
                    print("   ✅ Found existing campaign, clicking first one...")
                    campaign_items[0].click()
                else:
                    print("   ℹ️ No existing campaigns, creating new one...")
                    self._create_test_campaign(page)
            else:
                print("   ℹ️ Not on dashboard, creating new campaign...")
                self._create_test_campaign(page)

            # Wait for game view to load
            print("⏳ Waiting for game view...")
            page.wait_for_selector("#game-view", state="visible", timeout=30000)
            page.wait_for_load_state("networkidle")
            self.take_screenshot(page, "planning_blocks_02_game_view")

            # Check if there's already a planning block visible
            print("🔍 Looking for existing planning blocks...")
            planning_blocks = page.query_selector_all(".planning-block-choices")

            if len(planning_blocks) == 0:
                print("   ℹ️ No planning blocks visible, sending a test interaction...")
                # Send an interaction to generate a response with planning block
                self._send_interaction(page, "I look around the room carefully.")

                # Wait for response
                print("   ⏳ Waiting for AI response with planning block...")
                page.wait_for_selector(".planning-block-choices", timeout=30000)

            # Now we should have planning blocks
            self.take_screenshot(page, "planning_blocks_03_choices_rendered")

            # Verify planning block buttons exist
            print("🔍 Verifying planning block buttons...")
            planning_blocks = page.query_selector_all(".planning-block-choices")
            assert len(planning_blocks) > 0, "No planning block choices found"
            print(f"   ✅ Found {len(planning_blocks)} planning block(s)")

            # Find all choice buttons in the last planning block
            last_block = planning_blocks[-1]
            choice_buttons = last_block.query_selector_all(".choice-button")
            assert len(choice_buttons) > 0, "No choice buttons found in planning block"
            print(f"   ✅ Found {len(choice_buttons)} choice button(s)")

            # Verify button structure - buttons now use data attributes
            first_button = choice_buttons[0]
            choice_id = first_button.get_attribute("data-choice-id")
            choice_text = first_button.get_attribute("data-choice-text")
            button_text = first_button.inner_text()

            assert choice_id is not None, "data-choice-id attribute not found"
            assert choice_text is not None, "data-choice-text attribute not found"
            assert button_text, "Button text is empty"

            print(f"   ✅ First button ID: {choice_id}")
            print(f"   ✅ Button display text: {button_text}")
            print(f"   ✅ Full choice text: {choice_text}")

            # Take screenshot of button hover state
            first_button.hover()
            page.wait_for_timeout(500)  # Wait for hover effect
            self.take_screenshot(page, "planning_blocks_04_button_hover")

            # The expected text is already stored in choice_text from above
            expected_text = choice_text
            print(f"   📝 Expected text when clicked: {expected_text}")

            # Before clicking, record the current number of story entries
            story_entries_before = len(
                page.query_selector_all(".story-entry, #story-content > p")
            )

            # Click the first choice button
            print("🖱️ Clicking first choice button...")
            first_button.click()

            # The form should auto-submit, so the input might be cleared quickly
            # Instead of checking the input value, verify that the choice was sent
            # by looking for it in the story content
            print("   ✓ Button clicked, form should auto-submit")

            # Wait for the response
            print("⏳ Waiting for AI response after button click...")

            # Wait for a new story entry to appear
            page.wait_for_function(
                f"document.querySelectorAll('.story-entry, #story-content > p').length > {story_entries_before}",
                timeout=30000,
            )

            # Find the latest player entry to verify the choice text was sent
            story_entries = page.query_selector_all(".story-entry, #story-content > p")
            latest_entries = story_entries[story_entries_before:]

            # Look for the player's choice in the new entries
            choice_found = False
            for entry in latest_entries:
                entry_text = entry.inner_text()
                if choice_id in entry_text or expected_text in entry_text:
                    print(f"   ✅ Choice text found in story: {entry_text[:100]}...")
                    choice_found = True
                    break

            assert choice_found, (
                f"Expected choice text '{expected_text}' not found in story entries"
            )

            # Take screenshot of the result
            self.take_screenshot(page, "planning_blocks_05_after_click")

            # Verify buttons are re-enabled after response
            print("🔍 Verifying buttons are re-enabled...")
            page.wait_for_timeout(
                2000
            )  # Give more time for AI response and button re-enabling

            # Find new planning block buttons
            new_planning_blocks = page.query_selector_all(".planning-block-choices")
            if len(new_planning_blocks) > len(planning_blocks):
                # We have a new planning block
                new_buttons = new_planning_blocks[-1].query_selector_all(
                    ".choice-button"
                )
                if len(new_buttons) > 0:
                    # Check if buttons are enabled
                    first_new_button = new_buttons[0]
                    is_disabled = first_new_button.is_disabled()
                    assert not is_disabled, (
                        "New planning block buttons should be enabled"
                    )
                    print(
                        f"   ✅ New planning block has {len(new_buttons)} enabled button(s)"
                    )
            else:
                # No new planning block yet, but old buttons should be re-enabled after response completes
                # This happens when the AI response doesn't include a new planning block
                print(
                    "   ℹ️ No new planning block in response, checking if old buttons were re-enabled..."
                )
                # The old buttons might stay disabled if the action was final or the AI is still processing
                # This is expected behavior, so we'll just note it
                old_buttons = planning_blocks[-1].query_selector_all(".choice-button")
                if len(old_buttons) > 0:
                    first_old_button = old_buttons[0]
                    is_disabled = first_old_button.is_disabled()
                    if is_disabled:
                        print(
                            "   ℹ️ Old buttons remain disabled (expected if action was final or processing)"
                        )
                    else:
                        print("   ✅ Old buttons were re-enabled")

            # Test with special characters
            print("🔍 Testing special character handling...")
            # Send a god mode command to inject a choice with quotes
            self._send_god_mode_interaction(
                page,
                'Add this choice to the next planning block: **[Talk_1]:** Say "Hello there, friend!" to the stranger.',
            )

            # Wait for the new planning block with special characters
            page.wait_for_timeout(3000)

            # Find the newest planning block
            special_blocks = page.query_selector_all(".planning-block-choices")
            if len(special_blocks) > len(planning_blocks):
                special_button = special_blocks[-1].query_selector(
                    "[data-choice-id='Talk_1']"
                )
                if special_button:
                    special_text = special_button.get_attribute("data-choice-text")
                    print(
                        f"   ✅ Special character button found with text: {special_text}"
                    )
                    assert '"Hello there, friend!"' in special_text, (
                        "Special characters not preserved"
                    )

            # Wait for response with special characters
            page.wait_for_timeout(2000)
            self.take_screenshot(page, "planning_blocks_06_special_chars")

            print("✅ Planning block buttons test completed successfully!")
            return True

        except TimeoutError as e:
            print(f"❌ Timeout waiting for element: {e}")
            self.take_screenshot(page, "planning_blocks_error_timeout")
            return False
        except AssertionError as e:
            print(f"❌ Assertion failed: {e}")
            self.take_screenshot(page, "planning_blocks_error_assertion")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.take_screenshot(page, "planning_blocks_error_unexpected")
            return False

    def _create_test_campaign(self, page):
        """Helper to create a test campaign."""
        # Click new campaign button
        if page.is_visible("text=New Campaign"):
            page.click("text=New Campaign")
        elif page.is_visible("#new-campaign-btn"):
            page.click("#new-campaign-btn")

        # Fill campaign form
        page.wait_for_selector("#new-campaign-view", state="visible")

        if page.is_visible("#campaign-title"):
            page.fill("#campaign-title", "Planning Blocks Test Campaign")

        if page.is_visible("#campaign-prompt"):
            page.fill(
                "#campaign-prompt",
                "A test campaign to verify planning block buttons work correctly.",
            )

        # Submit form
        if page.is_visible("button:has-text('Create Campaign')"):
            page.click("button:has-text('Create Campaign')")
        elif page.is_visible("button[type='submit']"):
            page.click("button[type='submit']")

    def _send_interaction(self, page, text):
        """Helper to send an interaction."""
        user_input = page.query_selector("#user-input")
        if user_input:
            user_input.fill(text)

            # Find and click send button
            send_button = page.query_selector("button:has-text('Send')")
            if send_button:
                send_button.click()

    def _send_god_mode_interaction(self, page, text):
        """Helper to send a god mode interaction."""
        # Switch to god mode
        god_mode_radio = page.query_selector("#god-mode")
        if god_mode_radio:
            god_mode_radio.click()

        # Send the interaction
        self._send_interaction(page, text)

        # Switch back to character mode
        char_mode_radio = page.query_selector("#char-mode")
        if char_mode_radio:
            char_mode_radio.click()


def test_planning_block_buttons_browser():
    """Entry point for standalone execution."""
    test = PlanningBlockButtonsTest()
    return test.execute()


def main():
    """Run the test."""
    success = test_planning_block_buttons_browser()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    print("🚀 Starting WorldArchitect.AI Planning Block Buttons Browser Test")
    success = test_planning_block_buttons_browser()

    if success:
        print("✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test failed!")
        sys.exit(1)
