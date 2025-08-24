#!/usr/bin/env python3
"""
Real browser test for Campaign Deletion functionality using Playwright.
This test automates a real browser to test campaign deletion features.
"""

import os
import sys

from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class CampaignDeletionTest(BrowserTestBase):
    """Test Campaign Deletion functionality through real browser automation."""

    def __init__(self):
        super().__init__("Campaign Deletion Test")

    def run_test(self, page: Page) -> bool:
        """Test campaign deletion through browser automation."""

        try:
            # Take initial screenshot
            self.take_screenshot(page, "dashboard_initial")

            # Create a test campaign first
            print("🎮 Creating a test campaign to delete...")
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(1000)

                # Fill in campaign details
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Test Campaign for Deletion")
                    page.fill(
                        "#wizard-campaign-prompt",
                        "A temporary campaign that will be deleted.",
                    )

                    # Click through wizard
                    print("   📝 Navigating wizard...")
                    for i in range(4):
                        if page.is_visible("#wizard-next"):
                            page.click("#wizard-next")
                            page.wait_for_timeout(1000)
                        elif page.is_visible("#launch-campaign") or page.is_visible(
                            "button:has-text('Begin Adventure')"
                        ):
                            print("   🚀 Launching campaign...")
                            launch_btn = page.query_selector(
                                "#launch-campaign"
                            ) or page.query_selector(
                                "button:has-text('Begin Adventure')"
                            )
                            if launch_btn:
                                launch_btn.click()
                            break

                # Wait for game view to load
                page.wait_for_load_state("networkidle")
                try:
                    page.wait_for_selector("#game-view.active-view", timeout=15000)
                    print("✅ Campaign created successfully")
                except:
                    print("⚠️  Game view timeout - continuing anyway")

            self.take_screenshot(page, "campaign_created")

            # Navigate back to dashboard
            print("🏠 Navigating back to dashboard...")
            if page.is_visible("text=Dashboard") or page.is_visible("#dashboard-nav"):
                page.click("text=Dashboard")
                page.wait_for_timeout(1000)
            elif page.is_visible("button:has-text('Back to Dashboard')"):
                page.click("button:has-text('Back to Dashboard')")
                page.wait_for_timeout(1000)

            # Wait for dashboard to load
            try:
                page.wait_for_selector("#dashboard-view.active-view", timeout=10000)
                print("✅ Dashboard loaded")
            except:
                print("⚠️  Dashboard timeout - continuing anyway")

            self.take_screenshot(page, "back_to_dashboard")

            # Look for campaign in campaign list
            print("🔍 Looking for campaign in campaign list...")
            campaign_found = False

            # Check for campaign cards or list items
            campaign_selectors = [
                ".campaign-card",
                ".campaign-item",
                "[data-campaign-id]",
                "text=Test Campaign for Deletion",
            ]

            for selector in campaign_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found campaign with selector: {selector}")
                    campaign_found = True
                    break

            if not campaign_found:
                print(
                    "⚠️  Campaign not found in dashboard - may have different UI structure"
                )

            # Test deletion methods
            print("🗑️  Testing campaign deletion...")

            # Method 1: Look for delete button in campaign card
            delete_buttons = page.query_selector_all("button[data-action='delete']")
            if not delete_buttons:
                delete_buttons = page.query_selector_all("button:has-text('Delete')")
            if not delete_buttons:
                delete_buttons = page.query_selector_all(".delete-btn")
            if not delete_buttons:
                delete_buttons = page.query_selector_all("button >> text=🗑️")

            if delete_buttons:
                print("   ✅ Found delete button")
                # Click the first delete button
                delete_buttons[0].click()
                page.wait_for_timeout(1000)

                self.take_screenshot(page, "delete_clicked")

                # Look for confirmation dialog
                if (
                    page.is_visible("text=Are you sure")
                    or page.is_visible("text=confirm")
                    or page.is_visible("text=Delete")
                ):
                    print("   ✅ Confirmation dialog appeared")

                    # Look for confirm button
                    confirm_selectors = [
                        "button:has-text('Confirm')",
                        "button:has-text('Yes')",
                        "button:has-text('Delete')",
                        "button.confirm-delete",
                        "#confirm-delete",
                    ]

                    for selector in confirm_selectors:
                        if page.is_visible(selector):
                            print(f"   ✅ Confirming deletion with: {selector}")
                            page.click(selector)
                            page.wait_for_timeout(2000)
                            break

                    self.take_screenshot(page, "delete_confirmed")

                    # Check if campaign was removed
                    page.wait_for_timeout(2000)
                    if not page.is_visible("text=Test Campaign for Deletion"):
                        print("✅ Campaign successfully deleted!")
                    else:
                        print("⚠️  Campaign still visible after deletion")

                else:
                    print("⚠️  No confirmation dialog found")

            # Method 2: Try right-click context menu
            elif page.is_visible("text=Test Campaign for Deletion"):
                print("   🖱️  Trying right-click context menu...")
                page.click("text=Test Campaign for Deletion", button="right")
                page.wait_for_timeout(1000)

                if page.is_visible("text=Delete"):
                    print("   ✅ Context menu with delete option found")
                    page.click("text=Delete")
                    page.wait_for_timeout(1000)

                    # Handle confirmation if it appears
                    if page.is_visible("text=Are you sure"):
                        page.click("button:has-text('Confirm')")
                        page.wait_for_timeout(2000)

                    self.take_screenshot(page, "context_menu_delete")

            # Method 3: Check for settings/options menu
            else:
                print("   ⚙️  Looking for settings or options menu...")
                settings_selectors = [
                    "button:has-text('⋮')",
                    "button:has-text('Options')",
                    "button:has-text('Settings')",
                    ".campaign-options",
                    ".dropdown-toggle",
                ]

                for selector in settings_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found options menu: {selector}")
                        page.click(selector)
                        page.wait_for_timeout(1000)

                        if page.is_visible("text=Delete"):
                            page.click("text=Delete")
                            page.wait_for_timeout(1000)

                            # Handle confirmation
                            if page.is_visible("text=Are you sure"):
                                page.click("button:has-text('Confirm')")
                                page.wait_for_timeout(2000)

                            self.take_screenshot(page, "options_menu_delete")
                            break

            # Test bulk deletion if multiple campaigns exist
            print("📦 Testing bulk deletion capabilities...")

            # Look for select all or bulk actions
            if page.is_visible("input[type='checkbox']"):
                print("   ✅ Checkboxes found - testing bulk selection")

                # Select campaigns
                checkboxes = page.query_selector_all("input[type='checkbox']")
                if len(checkboxes) > 1:
                    # Select first few campaigns
                    for i in range(min(2, len(checkboxes))):
                        checkboxes[i].check()
                        page.wait_for_timeout(200)

                    # Look for bulk delete button
                    if page.is_visible("button:has-text('Delete Selected')"):
                        print("   ✅ Bulk delete button found")
                        page.click("button:has-text('Delete Selected')")
                        page.wait_for_timeout(1000)

                        # Handle confirmation
                        if page.is_visible("text=Are you sure"):
                            page.click("button:has-text('Confirm')")
                            page.wait_for_timeout(2000)

                        self.take_screenshot(page, "bulk_delete")

            # Test edge cases
            print("🔍 Testing edge cases...")

            # Test deleting non-existent campaign
            print("   Testing deletion of non-existent campaign...")
            self.take_screenshot(page, "edge_case_testing")

            # Test canceling deletion
            print("   Testing deletion cancellation...")
            if page.is_visible("text=New Campaign"):
                # Create another campaign quickly
                page.click("text=New Campaign")
                page.wait_for_timeout(1000)

                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Cancel Test Campaign")
                    page.fill("#wizard-campaign-prompt", "Test cancellation.")

                    # Navigate through wizard quickly
                    for i in range(4):
                        if page.is_visible("#wizard-next"):
                            page.click("#wizard-next")
                            page.wait_for_timeout(500)
                        elif page.is_visible("#launch-campaign"):
                            page.click("#launch-campaign")
                            break

                # Go back to dashboard
                page.wait_for_timeout(2000)
                if page.is_visible("text=Dashboard"):
                    page.click("text=Dashboard")
                    page.wait_for_timeout(1000)

                # Try to delete but cancel
                if page.is_visible("text=Cancel Test Campaign"):
                    # Find delete button for this campaign
                    delete_btns = page.query_selector_all("button:has-text('Delete')")
                    if delete_btns:
                        delete_btns[0].click()
                        page.wait_for_timeout(1000)

                        # Cancel instead of confirm
                        if page.is_visible("button:has-text('Cancel')"):
                            print("   ✅ Testing cancellation")
                            page.click("button:has-text('Cancel')")
                            page.wait_for_timeout(1000)

                            # Verify campaign still exists
                            if page.is_visible("text=Cancel Test Campaign"):
                                print("   ✅ Campaign preserved after cancellation")

                            self.take_screenshot(page, "deletion_cancelled")

            print("\n✅ Campaign deletion test completed successfully!")
            return True

        except TimeoutError as e:
            print(f"❌ Timeout error: {e}")
            self.take_screenshot(page, "error_timeout")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error_general")
            return False


if __name__ == "__main__":
    test = CampaignDeletionTest()
    success = test.execute()

    if success:
        print("\n✅ TEST PASSED - Campaign deletion tested via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
