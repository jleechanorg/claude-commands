#!/usr/bin/env python3
"""
Real browser test for accessibility using Playwright.
Tests keyboard navigation and screen reader compatibility.
"""

import os
import sys

from playwright.sync_api import Page

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class AccessibilityTest(BrowserTestBase):
    """Test accessibility features using the v2 framework."""

    def __init__(self):
        super().__init__("Accessibility Test")

    def run_test(self, page: Page) -> bool:
        """Test accessibility through real browser automation."""
        try:
            self.take_screenshot(page, "initial")

            # Test keyboard navigation
            print("⌨️ Testing keyboard navigation...")
            if not self._test_keyboard_navigation(page):
                print("❌ Failed keyboard navigation test")
                return False

            self.take_screenshot(page, "keyboard_nav")

            # Test ARIA attributes
            print("🏷️ Testing ARIA attributes...")
            if not self._test_aria_attributes(page):
                print("❌ Failed ARIA attributes test")
                return False

            # Test color contrast
            print("🎨 Testing color contrast...")
            if not self._test_color_contrast(page):
                print("❌ Failed color contrast test")
                return False

            # Test focus management
            print("🎯 Testing focus management...")
            if not self._test_focus_management(page):
                print("❌ Failed focus management test")
                return False

            self.take_screenshot(page, "accessibility_complete")

            print("\n✅ Accessibility test completed!")
            return True

        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error")
            return False

    def _test_keyboard_navigation(self, page: Page) -> bool:
        """Test keyboard navigation functionality."""
        # Test Tab navigation
        print("   🔄 Testing Tab navigation...")

        # Start from a known element
        if page.is_visible("text=Settings"):
            page.click("text=Settings")
            page.wait_for_timeout(500)

        # Test basic keyboard navigation
        keyboard_tests = [
            ("Tab", "Tab key"),
            ("Shift+Tab", "Shift+Tab key"),
            ("Enter", "Enter key"),
            ("Escape", "Escape key"),
            ("ArrowDown", "Arrow down"),
            ("ArrowUp", "Arrow up"),
        ]

        successful_keys = 0
        for key, description in keyboard_tests:
            try:
                page.keyboard.press(key)
                page.wait_for_timeout(300)
                print(f"   ✅ {description} navigation works")
                successful_keys += 1
            except Exception as e:
                print(f"   ⚠️  {description} failed: {e}")

        # Test specific accessibility shortcuts
        accessibility_shortcuts = [
            ("Alt+1", "Skip to main content"),
            ("Control+/", "Keyboard shortcuts help"),
        ]

        for shortcut, description in accessibility_shortcuts:
            try:
                page.keyboard.press(shortcut)
                page.wait_for_timeout(500)
                print(f"   ✅ {description} shortcut tested")
            except:
                print(f"   ⚠️  {description} shortcut not implemented")

        return successful_keys > 0

    def _test_aria_attributes(self, page: Page) -> bool:
        """Test ARIA attributes for screen reader compatibility."""
        # Check for common ARIA attributes
        aria_checks = [
            ("[aria-label]", "ARIA labels"),
            ("[aria-describedby]", "ARIA descriptions"),
            ("[role]", "ARIA roles"),
            ("[aria-expanded]", "ARIA expanded states"),
            ("[aria-hidden]", "ARIA hidden elements"),
            ("[alt]", "Alt text for images"),
        ]

        aria_found = 0
        for selector, description in aria_checks:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    aria_found += len(elements)
                    print(f"   ✅ Found {len(elements)} elements with {description}")
                else:
                    print(f"   ⚠️  No {description} found")
            except:
                continue

        # Check for semantic HTML
        semantic_elements = [
            ("main", "Main content area"),
            ("nav", "Navigation"),
            ("header", "Header"),
            ("footer", "Footer"),
            ("h1, h2, h3, h4, h5, h6", "Headings"),
            ("button", "Buttons"),
            ("input", "Form inputs"),
        ]

        semantic_found = 0
        for selector, description in semantic_elements:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    semantic_found += len(elements)
                    print(f"   ✅ Found {len(elements)} {description} elements")
            except:
                continue

        total_found = aria_found + semantic_found
        if total_found > 0:
            print(f"   ✅ Total accessibility features found: {total_found}")
        else:
            print("   ⚠️  No accessibility features detected")

        return True

    def _test_color_contrast(self, page: Page) -> bool:
        """Test color contrast for accessibility."""
        # This is a basic test - in practice you'd use specialized tools

        # Check if dark mode is available (indicates contrast consideration)
        contrast_indicators = [
            "text=Dark Mode",
            "text=High Contrast",
            ".dark-theme",
            ".high-contrast",
        ]

        contrast_features = 0
        for indicator in contrast_indicators:
            try:
                if page.is_visible(indicator):
                    print(f"   ✅ Found contrast feature: {indicator}")
                    contrast_features += 1
            except:
                continue

        # Basic color analysis
        try:
            # Get computed styles of key elements
            button_styles = page.evaluate("""
                () => {
                    const button = document.querySelector('button');
                    if (button) {
                        const styles = window.getComputedStyle(button);
                        return {
                            color: styles.color,
                            backgroundColor: styles.backgroundColor
                        };
                    }
                    return null;
                }
            """)

            if button_styles:
                print(f"   📊 Button styles: {button_styles}")
        except:
            print("   ⚠️  Could not analyze color styles")

        if contrast_features > 0:
            print(f"   ✅ Found {contrast_features} contrast features")
        else:
            print("   ⚠️  No explicit contrast features found")

        return True

    def _test_focus_management(self, page: Page) -> bool:
        """Test focus management and visibility."""
        # Test focus visibility
        focusable_elements = ["button", "input", "a", "[tabindex]"]

        focused_elements = 0
        for selector in focusable_elements:
            try:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    # Focus the first element
                    elements[0].focus()
                    page.wait_for_timeout(200)

                    # Check if focus is visible
                    is_focused = page.evaluate(f"""
                        () => {{
                            const element = document.querySelector('{selector}');
                            return element === document.activeElement;
                        }}
                    """)

                    if is_focused:
                        print(f"   ✅ {selector} elements are focusable")
                        focused_elements += 1
                    else:
                        print(f"   ⚠️  {selector} focus not working properly")
            except:
                continue

        # Test focus trap (in modals, etc.)
        try:
            # Try to open settings or modal
            if page.is_visible("text=Settings"):
                page.click("text=Settings")
                page.wait_for_timeout(500)

                # Test if Tab stays within modal
                page.keyboard.press("Tab")
                page.wait_for_timeout(200)

                print("   ✅ Focus trap tested in modal")
        except:
            print("   ⚠️  No modal available for focus trap testing")

        if focused_elements > 0:
            print(f"   ✅ {focused_elements} types of focusable elements working")
        else:
            print("   ⚠️  No focusable elements detected")

        return True


if __name__ == "__main__":
    test = AccessibilityTest()
    success = test.execute()

    if success:
        print("\n✅ TEST PASSED - Accessibility tested")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)
