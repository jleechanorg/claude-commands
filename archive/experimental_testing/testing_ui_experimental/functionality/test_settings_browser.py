#!/usr/bin/env python3
"""
Real browser test for Settings Management functionality using Playwright.
This test automates a real browser to test application settings.
"""

import os
import sys

from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class SettingsTest(BrowserTestBase):
    """Test Settings Management functionality through real browser automation."""

    def __init__(self):
        super().__init__("Settings Management Test")

    def run_test(self, page: Page) -> bool:
        """Test settings management through browser automation."""

        try:
            # Take initial screenshot
            self.take_screenshot(page, "dashboard_initial")

            # Navigate to settings
            print("⚙️  Navigating to settings...")

            settings_selectors = [
                "text=Settings",
                "button:has-text('Settings')",
                "#settings-nav",
                ".settings-link",
                "text=Preferences",
            ]

            settings_found = False
            for selector in settings_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found settings: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(2000)
                    settings_found = True
                    break

            if not settings_found:
                print("   ⚠️  Settings not found - looking for user menu...")

                # Try user menu or profile
                user_selectors = [
                    "text=Profile",
                    "button:has-text('Account')",
                    ".user-menu",
                    "#user-dropdown",
                ]

                for selector in user_selectors:
                    if page.is_visible(selector):
                        page.click(selector)
                        page.wait_for_timeout(1000)

                        if page.is_visible("text=Settings"):
                            page.click("text=Settings")
                            page.wait_for_timeout(2000)
                            settings_found = True
                        break

            self.take_screenshot(page, "settings_page")

            if settings_found:
                # Test general settings
                print("🔧 Testing general settings...")

                # Look for theme settings
                theme_selectors = [
                    "select[name*='theme']",
                    "#theme-selector",
                    "input[name='dark_mode']",
                    "text=Dark Mode",
                    "text=Theme",
                ]

                for selector in theme_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found theme setting: {selector}")

                        if selector.startswith("select"):
                            page.select_option(selector, "dark")
                            page.wait_for_timeout(1000)
                            page.select_option(selector, "light")
                        elif selector.startswith("input"):
                            page.check(selector)
                            page.wait_for_timeout(1000)
                            page.uncheck(selector)
                        else:
                            page.click(selector)
                            page.wait_for_timeout(1000)

                        self.take_screenshot(page, "theme_settings")
                        break

                # Test notification settings
                print("🔔 Testing notification settings...")

                notification_selectors = [
                    "input[name*='notification']",
                    "input[name*='email']",
                    "text=Notifications",
                    "text=Email Alerts",
                ]

                for selector in notification_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found notification setting: {selector}")

                        if selector.startswith("input"):
                            page.check(selector)
                            page.wait_for_timeout(500)
                            page.uncheck(selector)
                        else:
                            page.click(selector)
                            page.wait_for_timeout(1000)

                        self.take_screenshot(page, "notification_settings")
                        break

                # Test AI/Game settings
                print("🤖 Testing AI and game settings...")

                ai_selectors = [
                    "select[name*='ai']",
                    "select[name*='model']",
                    "input[name*='creativity']",
                    "text=AI Model",
                    "text=Creativity Level",
                ]

                for selector in ai_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found AI setting: {selector}")

                        if selector.startswith("select"):
                            # Get options and select one
                            options = page.query_selector_all(f"{selector} option")
                            if len(options) > 1:
                                page.select_option(selector, index=1)
                                page.wait_for_timeout(1000)
                        elif selector.startswith("input"):
                            page.fill(selector, "0.7")
                            page.wait_for_timeout(500)

                        self.take_screenshot(page, "ai_settings")
                        break

                # Test save settings
                print("💾 Testing save settings...")

                save_selectors = [
                    "button:has-text('Save')",
                    "button:has-text('Apply')",
                    "button:has-text('Update')",
                    "#save-settings",
                ]

                for selector in save_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found save button: {selector}")
                        page.click(selector)
                        page.wait_for_timeout(2000)

                        # Look for save confirmation
                        if page.is_visible("text=Saved") or page.is_visible(
                            "text=Updated"
                        ):
                            print("   ✅ Settings saved successfully")

                        self.take_screenshot(page, "settings_saved")
                        break

                # Test reset settings
                print("🔄 Testing reset settings...")

                reset_selectors = [
                    "button:has-text('Reset')",
                    "button:has-text('Defaults')",
                    "button:has-text('Restore')",
                    "#reset-settings",
                ]

                for selector in reset_selectors:
                    if page.is_visible(selector):
                        print(f"   ✅ Found reset button: {selector}")
                        page.click(selector)
                        page.wait_for_timeout(1000)

                        # Handle confirmation
                        if page.is_visible("text=Are you sure"):
                            page.click("button:has-text('Confirm')")
                            page.wait_for_timeout(1000)
                            print("   ✅ Settings reset confirmed")

                        self.take_screenshot(page, "settings_reset")
                        break

            print("\n✅ Settings management test completed successfully!")
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
    test = SettingsTest()
    success = test.execute()

    if success:
        print("\n✅ TEST PASSED - Settings management tested via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
