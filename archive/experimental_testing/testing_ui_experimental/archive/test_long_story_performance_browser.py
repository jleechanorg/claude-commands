#!/usr/bin/env python3
"""
Real browser test for long story performance using Playwright.
Tests performance with story interactions.
"""

import os
import sys
import time

from playwright.sync_api import Page

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class LongStoryPerformanceTest(BrowserTestBase):
    """Test long story performance using the v2 framework."""

    def __init__(self):
        super().__init__("Long Story Performance Test")

    def run_test(self, page: Page) -> bool:
        """Test long story performance through real browser automation."""
        try:
            self.take_screenshot(page, "initial")

            # Create campaign
            print("🎮 Creating performance test campaign...")
            self._create_campaign(page)

            # Test performance with many messages
            print("📈 Testing performance with many messages...")
            self._test_message_performance(page)

            self.take_screenshot(page, "final_performance")

            print("\n✅ Performance test completed!")
            return True

        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error")
            return False

    def _create_campaign(self, page: Page):
        """Create a campaign for performance testing."""
        if page.is_visible("text=New Campaign"):
            page.click("text=New Campaign")
            page.wait_for_timeout(1000)

            if page.is_visible("#wizard-campaign-title"):
                page.fill("#wizard-campaign-title", "Performance Test Campaign")
                page.fill(
                    "#wizard-campaign-prompt", "A campaign for performance testing."
                )

                # Quick wizard navigation
                for _ in range(4):
                    if page.is_visible("#wizard-next"):
                        page.click("#wizard-next")
                        page.wait_for_timeout(500)
                    elif page.is_visible("#launch-campaign"):
                        page.click("#launch-campaign")
                        break

                page.wait_for_timeout(2000)

    def _test_message_performance(self, page: Page):
        """Test performance with multiple messages."""
        message_input = page.query_selector("#message-input")
        if not message_input:
            print("   ⚠️  Message input not found")
            return

        # Send 10 quick messages to test performance
        start_time = time.time()

        for i in range(10):
            message = f"Performance test message {i + 1}"
            message_input.fill(message)

            send_button = page.query_selector("button:has-text('Send')")
            if send_button:
                send_button.click()
            else:
                message_input.press("Enter")

            page.wait_for_timeout(500)

        end_time = time.time()
        duration = end_time - start_time

        print(f"   ⏱️  Sent 10 messages in {duration:.2f} seconds")
        print(f"   📊 Average: {duration / 10:.2f} seconds per message")


if __name__ == "__main__":
    test = LongStoryPerformanceTest()
    success = test.execute()

    if success:
        print("\n✅ TEST PASSED - Performance tested")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
