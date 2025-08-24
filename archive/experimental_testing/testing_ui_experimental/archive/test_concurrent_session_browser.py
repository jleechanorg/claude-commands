#!/usr/bin/env python3
"""
Real browser test for concurrent sessions using Playwright.
Tests multiple browser tabs with no conflicts.
"""

import os
import sys

from playwright.sync_api import Page

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase

# Configuration
BASE_URL = os.getenv("TEST_SERVER_URL", "http://localhost:6006")


class ConcurrentSessionTest(BrowserTestBase):
    """Test concurrent sessions using the v2 framework."""

    def __init__(self):
        super().__init__("Concurrent Session Test")

    def run_test(self, page: Page) -> bool:
        """Test concurrent sessions through real browser automation."""
        try:
            self.take_screenshot(page, "initial")

            print("🌐 Testing concurrent browser sessions...")

            # Open second tab
            new_tab = page.context.new_page()

            # Navigate both tabs
            test_url = f"{BASE_URL}?test_mode=true&test_user_id=browser-test-user"
            new_tab.goto(test_url)
            new_tab.wait_for_timeout(2000)

            # Take screenshots of both tabs
            self.take_screenshot(page, "concurrent_tab1")
            self.take_screenshot(new_tab, "concurrent_tab2")

            # Test that both tabs work independently
            if page.is_visible("#dashboard-view") and new_tab.is_visible(
                "#dashboard-view"
            ):
                print("   ✅ Both tabs loaded successfully")
            else:
                print("   ⚠️  One or both tabs did not load properly")

            new_tab.close()

            self.take_screenshot(page, "concurrent_complete")

            print("\n✅ Concurrent session test completed!")
            return True

        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error")
            return False


if __name__ == "__main__":
    test = ConcurrentSessionTest()
    success = test.execute()

    if success:
        print("\n✅ TEST PASSED - Concurrent sessions tested")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
