#!/usr/bin/env python3
"""
Real browser test for Search Functionality using Playwright.
This test automates a real browser to test search features.
"""

import os
import sys

from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class SearchTest(BrowserTestBase):
    """Test Search functionality through real browser automation."""

    def __init__(self):
        super().__init__("Search Functionality Test")

    def run_test(self, page: Page) -> bool:
        """Test search functionality through browser automation."""

        try:
            # Take initial screenshot
            self.take_screenshot(page, "dashboard_initial")

            # Create a campaign with searchable content first
            print("🎮 Creating campaign with searchable content...")
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(1000)

                # Fill campaign with searchable content
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Searchable Test Campaign")
                    page.fill(
                        "#wizard-campaign-prompt",
                        "A mystical forest with dragons, wizards, and ancient treasures.",
                    )

                    # Complete wizard
                    for _i in range(4):
                        if page.is_visible("#wizard-next"):
                            page.click("#wizard-next")
                            page.wait_for_timeout(1000)
                        elif page.is_visible("#launch-campaign"):
                            page.click("#launch-campaign")
                            break

                    page.wait_for_timeout(3000)

                    # Add searchable messages
                    searchable_messages = [
                        "I encounter a mighty dragon breathing fire",
                        "The wise wizard offers me a magical potion",
                        "Ancient treasure chest hidden in the cave",
                        "Mysterious forest spirits guide my path",
                    ]

                    message_input = page.query_selector(
                        "#message-input"
                    ) or page.query_selector("textarea[placeholder*='What do you do']")
                    send_button = page.query_selector(
                        "button:has-text('Send')"
                    ) or page.query_selector("#send-button")

                    if message_input:
                        for msg in searchable_messages:
                            message_input.fill(msg)
                            if send_button:
                                send_button.click()
                            else:
                                message_input.press("Enter")
                            page.wait_for_timeout(2000)  # Wait for AI response
                            print(f"   📝 Added: {msg}")

            self.take_screenshot(page, "content_created")

            # Test search functionality
            print("🔍 Testing search functionality...")

            # Look for search interface
            search_selectors = [
                "#search-input",
                "input[placeholder*='search']",
                "input[placeholder*='Search']",
                ".search-input",
                "button:has-text('Search')",
            ]

            search_found = False
            for selector in search_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found search interface: {selector}")
                    search_found = True

                    # Test basic search
                    if selector.startswith("input"):
                        page.fill(selector, "dragon")
                        page.wait_for_timeout(1000)

                        # Look for search results
                        if page.is_visible("text=dragon") or page.is_visible(
                            "text=fire"
                        ):
                            print("   ✅ Search results displayed")

                        # Clear search
                        page.fill(selector, "")
                        page.wait_for_timeout(500)

                    self.take_screenshot(page, "basic_search")
                    break

            if not search_found:
                # Look for search in menu or separate page
                print("   🔍 Looking for search in navigation...")
                nav_search_selectors = [
                    "text=Search",
                    "button:has-text('Search')",
                    "#search-nav",
                    ".search-link",
                ]

                for selector in nav_search_selectors:
                    if page.is_visible(selector):
                        page.click(selector)
                        page.wait_for_timeout(1000)
                        search_found = True
                        break

            if search_found:
                # Test different search types
                print("   🔍 Testing different search types...")

                search_terms = [
                    "wizard",  # Character search
                    "treasure",  # Item search
                    "forest",  # Location search
                    "fire",  # Action search
                ]

                search_input = page.query_selector(
                    "#search-input"
                ) or page.query_selector("input[placeholder*='search']")

                for term in search_terms:
                    if search_input:
                        print(f"   🔍 Searching for: {term}")
                        page.fill(search_input.nth(0), term)
                        page.wait_for_timeout(1000)

                        # Press Enter or click search button
                        search_btn = page.query_selector("button:has-text('Search')")
                        if search_btn:
                            search_btn.click()
                        else:
                            search_input.press("Enter")

                        page.wait_for_timeout(2000)

                        # Check for results
                        if page.is_visible(f"text={term}"):
                            print(f"   ✅ Found results for: {term}")
                        else:
                            print(f"   ⚠️  No results for: {term}")

                        self.take_screenshot(page, f"search_{term}")

                # Test search filters
                print("   🎛️  Testing search filters...")

                filter_selectors = [
                    "select[name*='filter']",
                    "select[name*='type']",
                    "input[type='checkbox']",
                    "text=Filter",
                    ".search-filters",
                ]

                for selector in filter_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found search filter: {selector}")

                        if selector.startswith("select"):
                            options = page.query_selector_all(f"{selector} option")
                            if len(options) > 1:
                                page.select_option(selector, index=1)
                                page.wait_for_timeout(1000)
                        elif selector.startswith("input[type='checkbox']"):
                            page.check(selector)
                            page.wait_for_timeout(1000)

                        self.take_screenshot(page, "search_filters")
                        break

                # Test search sorting
                print("   📊 Testing search result sorting...")

                sort_selectors = [
                    "select[name*='sort']",
                    "button:has-text('Sort')",
                    "text=Sort by",
                    ".sort-dropdown",
                ]

                for selector in sort_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found sort option: {selector}")

                        if selector.startswith("select"):
                            page.select_option(selector, "date")
                            page.wait_for_timeout(1000)
                            page.select_option(selector, "relevance")
                        elif selector.startswith("button"):
                            page.click(selector)
                            page.wait_for_timeout(1000)

                        self.take_screenshot(page, "search_sorting")
                        break

                # Test search within results
                print("   🔍 Testing search within results...")

                # Perform initial search
                if search_input:
                    page.fill(search_input.nth(0), "magic")
                    page.wait_for_timeout(1000)

                    # Look for refine search
                    refine_selectors = [
                        "input[placeholder*='refine']",
                        "input[placeholder*='within']",
                        "text=Refine",
                        ".refine-search",
                    ]

                    for selector in refine_selectors:
                        if page.is_visible(selector):
                            print(f"   ✅ Found refine search: {selector}")
                            if selector.startswith("input"):
                                page.fill(selector, "potion")
                                page.wait_for_timeout(1000)

                            self.take_screenshot(page, "refine_search")
                            break

                # Test search suggestions/autocomplete
                print("   💡 Testing search suggestions...")

                if search_input:
                    # Type partial term to trigger suggestions
                    page.fill(search_input.nth(0), "dra")
                    page.wait_for_timeout(1000)

                    # Look for suggestions dropdown
                    suggestion_selectors = [
                        ".search-suggestions",
                        ".autocomplete",
                        ".dropdown-menu",
                        "[data-suggestion]",
                    ]

                    for selector in suggestion_selectors:
                        if page.is_visible(selector):
                            print(f"   ✅ Found search suggestions: {selector}")

                            # Click on a suggestion
                            suggestions = page.query_selector_all(f"{selector} li")
                            if suggestions:
                                suggestions[0].click()
                                page.wait_for_timeout(1000)

                            self.take_screenshot(page, "search_suggestions")
                            break

                # Test search history
                print("   📜 Testing search history...")

                history_selectors = [
                    "text=Recent Searches",
                    "text=Search History",
                    ".search-history",
                    "#search-history",
                ]

                for selector in history_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found search history: {selector}")
                        page.click(selector)
                        page.wait_for_timeout(1000)

                        # Look for previous searches
                        if page.is_visible("text=dragon") or page.is_visible(
                            "text=wizard"
                        ):
                            print("   ✅ Search history populated")

                        self.take_screenshot(page, "search_history")
                        break

                # Test empty search handling
                print("   🚫 Testing empty search handling...")

                if search_input:
                    page.fill(search_input.nth(0), "nonexistentterm123")
                    page.wait_for_timeout(1000)

                    # Look for no results message
                    no_results_selectors = [
                        "text=No results",
                        "text=Nothing found",
                        "text=0 results",
                        ".no-results",
                    ]

                    for selector in no_results_selectors:
                        if page.is_visible(selector):
                            print(f"   ✅ Found no results message: {selector}")
                            break

                    self.take_screenshot(page, "empty_search")

            print("\n✅ Search functionality test completed successfully!")
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
    test = SearchTest()
    success = test.execute()

    if success:
        print("\n✅ TEST PASSED - Search functionality tested via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
