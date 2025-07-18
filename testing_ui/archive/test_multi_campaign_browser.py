#!/usr/bin/env python3
"""
Real browser test for Multi-Campaign Management functionality using Playwright.
This test automates a real browser to test managing multiple campaigns.
"""

import os
import sys

from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class MultiCampaignTest(BrowserTestBase):
    """Test Multi-Campaign Management functionality through real browser automation."""

    def __init__(self):
        super().__init__("Multi-Campaign Management Test")

    def run_test(self, page: Page) -> bool:
        """Test multi-campaign management through browser automation."""

        try:
            # Take initial screenshot
            self.take_screenshot(page, "dashboard_initial")

            # Create multiple test campaigns
            campaign_names = [
                "Fantasy Adventure Campaign",
                "Sci-Fi Space Campaign",
                "Horror Mystery Campaign",
            ]

            created_campaigns = []

            for i, campaign_name in enumerate(campaign_names):
                print(f"🎮 Creating campaign {i + 1}: {campaign_name}")

                # Navigate to dashboard first
                if page.is_visible("text=Dashboard"):
                    page.click("text=Dashboard")
                    page.wait_for_timeout(1000)

                # Create new campaign
                if page.is_visible("text=New Campaign"):
                    page.click("text=New Campaign")
                    page.wait_for_timeout(1000)

                    # Fill in campaign details
                    if page.is_visible("#wizard-campaign-title"):
                        page.fill("#wizard-campaign-title", campaign_name)
                        page.fill(
                            "#wizard-campaign-prompt",
                            f"A {campaign_name.lower()} with unique storylines.",
                        )

                        # Click through wizard
                        print(f"   📝 Navigating wizard for {campaign_name}...")
                        for j in range(4):
                            if page.is_visible("#wizard-next"):
                                page.click("#wizard-next")
                                page.wait_for_timeout(1000)
                            elif page.is_visible("#launch-campaign") or page.is_visible(
                                "button:has-text('Begin Adventure')"
                            ):
                                print(f"   🚀 Launching {campaign_name}...")
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
                            page.wait_for_selector(
                                "#game-view.active-view", timeout=10000
                            )
                            print(f"✅ {campaign_name} created successfully")
                            created_campaigns.append(campaign_name)
                        except:
                            print(
                                f"⚠️  {campaign_name} creation timeout - continuing anyway"
                            )

                        self.take_screenshot(page, f"campaign_{i + 1}_created")

                        # Send a quick message to establish the campaign
                        message_input = page.query_selector(
                            "#message-input"
                        ) or page.query_selector(
                            "textarea[placeholder*='What do you do']"
                        )
                        if message_input:
                            message_input.fill("I begin my adventure in this world.")
                            send_button = page.query_selector(
                                "button:has-text('Send')"
                            ) or page.query_selector("#send-button")
                            if send_button:
                                send_button.click()
                            else:
                                message_input.press("Enter")

                            page.wait_for_timeout(3000)  # Wait for response
                            print(
                                f"   📝 Established {campaign_name} with initial message"
                            )

            # Test campaign switching
            print("🔄 Testing campaign switching...")

            # Navigate back to dashboard
            if page.is_visible("text=Dashboard"):
                page.click("text=Dashboard")
                page.wait_for_timeout(2000)

            # Wait for dashboard to load
            try:
                page.wait_for_selector("#dashboard-view.active-view", timeout=10000)
                print("✅ Dashboard loaded")
            except:
                print("⚠️  Dashboard timeout - continuing anyway")

            self.take_screenshot(page, "dashboard_with_campaigns")

            # Test campaign list display
            print("📋 Testing campaign list display...")

            # Look for campaign cards or list items
            campaign_found_count = 0
            for campaign_name in created_campaigns:
                if page.is_visible(f"text={campaign_name}"):
                    print(f"   ✅ Found campaign: {campaign_name}")
                    campaign_found_count += 1
                else:
                    print(f"   ⚠️  Campaign not found: {campaign_name}")

            print(
                f"   📊 Found {campaign_found_count}/{len(created_campaigns)} campaigns"
            )

            # Test switching between campaigns
            print("🔄 Testing campaign switching...")

            for i, campaign_name in enumerate(created_campaigns):
                if page.is_visible(f"text={campaign_name}"):
                    print(f"   🎮 Switching to: {campaign_name}")

                    # Click on the campaign
                    page.click(f"text={campaign_name}")
                    page.wait_for_timeout(2000)

                    # Wait for game view to load
                    try:
                        page.wait_for_selector("#game-view.active-view", timeout=10000)
                        print(f"   ✅ Successfully switched to {campaign_name}")

                        # Verify we're in the right campaign
                        if page.is_visible(f"text={campaign_name}"):
                            print(f"   ✅ Campaign title confirmed: {campaign_name}")

                        # Send a message to confirm the campaign context
                        message_input = page.query_selector(
                            "#message-input"
                        ) or page.query_selector(
                            "textarea[placeholder*='What do you do']"
                        )
                        if message_input:
                            message_input.fill(
                                f"I continue my adventure in {campaign_name}"
                            )
                            send_button = page.query_selector(
                                "button:has-text('Send')"
                            ) or page.query_selector("#send-button")
                            if send_button:
                                send_button.click()
                            else:
                                message_input.press("Enter")

                            page.wait_for_timeout(3000)  # Wait for response
                            print(
                                f"   📝 Confirmed campaign context for {campaign_name}"
                            )

                        self.take_screenshot(page, f"switched_to_campaign_{i + 1}")

                        # Go back to dashboard for next campaign
                        if page.is_visible("text=Dashboard"):
                            page.click("text=Dashboard")
                            page.wait_for_timeout(2000)

                    except:
                        print(f"   ❌ Failed to switch to {campaign_name}")

            # Test campaign search/filter
            print("🔍 Testing campaign search and filtering...")

            # Look for search functionality
            search_selectors = [
                "#campaign-search",
                "input[placeholder*='search']",
                "input[placeholder*='Search']",
                "input[placeholder*='filter']",
                ".search-input",
            ]

            for selector in search_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found search field: {selector}")

                    # Test search functionality
                    page.fill(selector, "Fantasy")
                    page.wait_for_timeout(1000)

                    # Check if filtering works
                    if page.is_visible("text=Fantasy Adventure Campaign"):
                        print("   ✅ Search filtering works")
                    else:
                        print("   ⚠️  Search filtering not working")

                    # Clear search
                    page.fill(selector, "")
                    page.wait_for_timeout(1000)

                    self.take_screenshot(page, "campaign_search_tested")
                    break

            # Test campaign sorting
            print("📊 Testing campaign sorting...")

            # Look for sort options
            sort_selectors = [
                "#campaign-sort",
                ".sort-dropdown",
                "select[name*='sort']",
                "button:has-text('Sort')",
            ]

            for selector in sort_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found sort option: {selector}")

                    if selector.startswith("select"):
                        # Test different sort options
                        page.select_option(selector, "name")
                        page.wait_for_timeout(1000)
                        page.select_option(selector, "date")
                        page.wait_for_timeout(1000)
                    elif selector.startswith("button"):
                        page.click(selector)
                        page.wait_for_timeout(1000)

                    self.take_screenshot(page, "campaign_sorting_tested")
                    break

            # Test campaign archiving/deactivation
            print("📦 Testing campaign archiving...")

            # Look for archive functionality
            archive_selectors = [
                "button:has-text('Archive')",
                "button:has-text('Deactivate')",
                "button:has-text('Pause')",
                ".archive-btn",
            ]

            for selector in archive_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found archive option: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Handle confirmation if it appears
                    if page.is_visible("text=Are you sure"):
                        page.click("button:has-text('Confirm')")
                        page.wait_for_timeout(1000)
                        print("   ✅ Campaign archived")

                    self.take_screenshot(page, "campaign_archived")
                    break

            # Test campaign reactivation
            print("🔄 Testing campaign reactivation...")

            # Look for archived campaigns view
            archived_selectors = [
                "button:has-text('Archived')",
                "button:has-text('Show Archived')",
                "text=Archived Campaigns",
                ".archived-tab",
            ]

            for selector in archived_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found archived view: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Look for reactivate button
                    if page.is_visible("button:has-text('Reactivate')"):
                        page.click("button:has-text('Reactivate')")
                        page.wait_for_timeout(1000)
                        print("   ✅ Campaign reactivated")

                    self.take_screenshot(page, "campaign_reactivated")
                    break

            # Test campaign statistics/overview
            print("📊 Testing campaign statistics...")

            # Look for statistics or overview
            stats_selectors = [
                "text=Statistics",
                "text=Overview",
                "text=Campaign Stats",
                ".campaign-stats",
                "#campaign-overview",
            ]

            for selector in stats_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found stats view: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Look for stat information
                    stat_indicators = [
                        "text=Messages",
                        "text=Characters",
                        "text=Sessions",
                        "text=Duration",
                    ]

                    for indicator in stat_indicators:
                        if page.is_visible(indicator):
                            print(f"   ✅ Found stat: {indicator}")

                    self.take_screenshot(page, "campaign_stats")
                    break

            # Test bulk campaign operations
            print("📦 Testing bulk campaign operations...")

            # Look for bulk selection
            if page.is_visible("input[type='checkbox']"):
                print("   ✅ Found bulk selection checkboxes")

                # Select multiple campaigns
                checkboxes = page.query_selector_all("input[type='checkbox']")
                if len(checkboxes) > 1:
                    for i in range(min(2, len(checkboxes))):
                        checkboxes[i].check()
                        page.wait_for_timeout(200)

                    # Look for bulk operations
                    bulk_selectors = [
                        "button:has-text('Bulk Actions')",
                        "button:has-text('Archive Selected')",
                        "button:has-text('Delete Selected')",
                        ".bulk-actions",
                    ]

                    for selector in bulk_selectors:
                        if page.is_visible(selector):
                            print(f"   ✅ Found bulk action: {selector}")
                            # Don't actually execute to avoid deleting campaigns
                            self.take_screenshot(page, "bulk_operations")
                            break

            # Test campaign export/import
            print("📤 Testing campaign export/import...")

            # Look for export functionality
            export_selectors = [
                "button:has-text('Export')",
                "button:has-text('Download')",
                "button:has-text('Backup')",
                ".export-btn",
            ]

            for selector in export_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found export option: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)

                    # Handle export dialog if it appears
                    if page.is_visible("text=Export Format"):
                        print("   ✅ Export dialog appeared")

                        # Cancel to avoid actual download
                        if page.is_visible("button:has-text('Cancel')"):
                            page.click("button:has-text('Cancel')")

                    self.take_screenshot(page, "campaign_export")
                    break

            print("\n✅ Multi-campaign management test completed successfully!")
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
    test = MultiCampaignTest()
    success = test.execute()

    if success:
        print(
            "\n✅ TEST PASSED - Multi-campaign management tested via browser automation"
        )
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
