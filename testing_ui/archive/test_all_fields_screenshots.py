#!/usr/bin/env python3
"""
Comprehensive test to capture screenshots for every structured field from the schema.
This test demonstrates all 10 fields from game_state_instruction.md working in the UI.
Uses the shared browser_test_helpers library for standardized screenshot management.
"""

import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import test utilities
sys.path.append(os.path.dirname(__file__))
from screenshot_utils import take_screenshot
from test_data_utils import create_test_campaign
from test_ui_helpers import capture_structured_fields_sequence
from test_ui_util import navigate_to_page, run_ui_test, wait_for_element


def test_all_structured_fields(page, test_name):
    """Test that captures screenshots of all structured fields in action."""

    print("=== Testing All Structured Fields Screenshots ===")

    try:
        # Navigate to test application
        navigate_to_page(page, "", port=6006)

        # Wait for dashboard to load
        if not wait_for_element(page, "text='My Campaigns'", timeout=10000):
            raise Exception("Dashboard failed to load")

        take_screenshot(page, test_name, "full_page")

        # Look for existing test campaign or create one
        campaign_name = "All Fields Test Campaign"
        try:
            page.click(f"text='{campaign_name}'", timeout=5000)
        except:
            # Campaign doesn't exist, create it
            print("Creating test campaign...")
            if not create_test_campaign(page, campaign_name):
                raise Exception("Failed to create test campaign")

        # Wait for game view to load
        if not wait_for_element(page, "#game-view", timeout=30000):
            raise Exception("Game view failed to load")

        take_screenshot(page, test_name, "initial_campaign")

        # Use helper's structured fields capture sequence
        screenshots = capture_structured_fields_sequence(page, test_name)

        # Summary
        print("\n=== Screenshots Captured ===")
        for field_name, path in screenshots.items():
            if path:
                print(f"✅ {field_name}: {os.path.basename(path)}")

        print(
            f"\nTotal screenshots taken: {len([s for s in screenshots.values() if s])}"
        )

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the test using the test runner
    run_ui_test(test_all_structured_fields, "all_fields_screenshots", headless=True)
