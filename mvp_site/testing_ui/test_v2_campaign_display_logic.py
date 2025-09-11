#!/usr/bin/env python3
"""
Test V2 Campaign Display Logic - Red/Green Test
Verifies V2 shows campaigns dashboard when campaigns exist (not landing page)
"""

import os
import sys

from browser_test_base import TestBase
from playwright.sync_api import sync_playwright

# Set up path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "testing_ui"
    )
)


class TestV2CampaignDisplayLogic(TestBase):
    """Test V2 properly displays campaigns dashboard when campaigns exist"""

    def test_v2_shows_campaigns_when_they_exist(self):
        """
        RED/GREEN Test: V2 should show campaigns dashboard, not landing page

        EXPECTED BEHAVIOR:
        1. User has existing campaigns (confirmed via API: 503 campaigns)
        2. V2 should show campaigns dashboard with campaign list
        3. V2 should NOT show "Create Your First Campaign" landing page

        CURRENT BROKEN BEHAVIOR (RED):
        - V2 API fetches 503 campaigns successfully
        - V2 still shows landing page instead of campaigns dashboard
        - This breaks user experience for existing users
        """
        print("🔴 RED TEST: V2 Campaign Display Logic")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context()
                page = context.new_page()

                # Navigate to V2 React frontend
                print("📍 Navigating to V2 React frontend...")
                page.goto("http://localhost:3001")

                # Wait for authentication and API calls to complete
                print("⏳ Waiting for authentication and API calls...")
                page.wait_for_timeout(5000)  # Wait for auth + API calls

                # Check current page state
                page_content = page.content()

                # TEST ASSERTION: V2 should show campaigns dashboard, not landing page
                print("🧪 Testing V2 display logic...")

                # Check if showing landing page (WRONG behavior)
                has_create_first_campaign = "Create Your First Campaign" in page_content
                has_welcome_adventurer = "Welcome, Adventurer" in page_content

                # Check if showing campaigns dashboard (CORRECT behavior)
                has_campaign_list = "campaigns" in page_content.lower() and (
                    "my campaigns" in page_content.lower()
                    or "campaign list" in page_content.lower()
                )
                has_campaign_data = any(
                    keyword in page_content.lower()
                    for keyword in ["zara", "elara", "warrior", "knight"]
                )

                print("📊 V2 Page Analysis:")
                print(
                    f"   - Has 'Create Your First Campaign': {has_create_first_campaign}"
                )
                print(f"   - Has 'Welcome, Adventurer': {has_welcome_adventurer}")
                print(f"   - Has campaign list UI: {has_campaign_list}")
                print(f"   - Has campaign data: {has_campaign_data}")

                # RED TEST: This should FAIL initially (V2 showing wrong page)
                if has_create_first_campaign and has_welcome_adventurer:
                    print(
                        "🔴 TEST FAILURE (EXPECTED): V2 showing landing page instead of campaigns dashboard"
                    )
                    print(
                        "   ✅ This confirms the bug - V2 has campaigns but shows landing page"
                    )
                    print(
                        "   🎯 Next: Fix V2 to show campaigns dashboard when campaigns exist"
                    )
                    return False  # RED - Test fails as expected

                if has_campaign_list or has_campaign_data:
                    print("✅ TEST PASSING: V2 correctly showing campaigns dashboard")
                    print(
                        "   🎯 V2 properly displays existing campaigns instead of landing page"
                    )
                    return True  # GREEN - Test passes after fix

                print(
                    "❓ UNCLEAR STATE: V2 showing neither landing page nor campaigns dashboard"
                )
                print("   🔍 Manual investigation needed")
                return False

            finally:
                browser.close()


def run_red_green_test():
    """Run the red-green test for V2 campaign display logic"""
    print("🚀 Starting V2 Campaign Display Logic Test")
    print("=" * 60)

    test = TestV2CampaignDisplayLogic()

    print("🔴 RED PHASE: Testing current (broken) behavior...")
    result = test.test_v2_shows_campaigns_when_they_exist()

    if not result:
        print("\n🔴 RED PHASE COMPLETE: Test fails as expected")
        print("   ✅ Confirmed: V2 shows landing page despite having campaigns")
        print("   🎯 Next: Implement fix to show campaigns dashboard")
        return "RED"
    print("\n✅ GREEN PHASE: Test passes!")
    print("   🎯 V2 correctly shows campaigns dashboard when campaigns exist")
    return "GREEN"


if __name__ == "__main__":
    result = run_red_green_test()
    print(f"\n📊 RESULT: {result} PHASE")
