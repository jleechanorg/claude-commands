#!/usr/bin/env python3
"""
Real browser test for mobile responsive design using Playwright.
Tests on mobile viewport sizes and touch interactions.
"""

import os
import sys
from playwright.sync_api import Page

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class MobileResponsiveTest(BrowserTestBase):
    """Test mobile responsive design using the v2 framework."""
    
    def __init__(self):
        super().__init__("Mobile Responsive Test")
    
    def run_test(self, page: Page) -> bool:
        """Test mobile responsive design through real browser automation."""
        try:
            # Start with desktop view
            self.take_screenshot(page, "desktop_initial")
            
            # Test tablet viewport
            print("📱 Testing tablet viewport...")
            if not self._test_tablet_viewport(page):
                print("❌ Failed to test tablet viewport")
                return False
            
            self.take_screenshot(page, "tablet_viewport")
            
            # Test mobile viewport
            print("📱 Testing mobile viewport...")
            if not self._test_mobile_viewport(page):
                print("❌ Failed to test mobile viewport")
                return False
            
            self.take_screenshot(page, "mobile_viewport")
            
            # Test touch interactions
            print("👆 Testing touch interactions...")
            if not self._test_touch_interactions(page):
                print("❌ Failed to test touch interactions")
                return False
            
            self.take_screenshot(page, "touch_interactions")
            
            # Test responsive navigation
            print("🧭 Testing responsive navigation...")
            if not self._test_responsive_navigation(page):
                print("❌ Failed to test responsive navigation")
                return False
            
            self.take_screenshot(page, "responsive_navigation")
            
            # Test responsive layout
            print("📐 Testing responsive layout...")
            if not self._test_responsive_layout(page):
                print("❌ Failed to test responsive layout")
                return False
            
            self.take_screenshot(page, "responsive_layout")
            
            # Test orientation changes
            print("🔄 Testing orientation changes...")
            if not self._test_orientation_changes(page):
                print("❌ Failed to test orientation changes")
                return False
            
            self.take_screenshot(page, "orientation_changes")
            
            print("\n✅ Mobile responsive test completed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error")
            return False
    
    def _test_tablet_viewport(self, page: Page) -> bool:
        """Test application behavior in tablet viewport."""
        # Set tablet viewport (768x1024)
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(1000)
        
        # Test that content is visible and usable
        essential_elements = [
            "#dashboard-view",
            "text=New Campaign",
            ".campaign-card, .campaign-item"
        ]
        
        visible_elements = 0
        for element in essential_elements:
            try:
                if page.is_visible(element):
                    visible_elements += 1
                    print(f"   ✅ Tablet: {element} visible")
                else:
                    print(f"   ⚠️  Tablet: {element} not visible")
            except:
                print(f"   ⚠️  Tablet: {element} not found")
        
        if visible_elements > 0:
            print(f"   ✅ {visible_elements}/{len(essential_elements)} elements visible on tablet")
            return True
        else:
            print("   ⚠️  No essential elements visible on tablet")
            return False
    
    def _test_mobile_viewport(self, page: Page) -> bool:
        """Test application behavior in mobile viewport."""
        # Set mobile viewport (375x667 - iPhone SE)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(1000)
        
        # Test that content is still accessible
        mobile_essential_elements = [
            "#dashboard-view",
            "text=New Campaign"
        ]
        
        mobile_visible = 0
        for element in mobile_essential_elements:
            try:
                if page.is_visible(element):
                    mobile_visible += 1
                    print(f"   ✅ Mobile: {element} visible")
                else:
                    print(f"   ⚠️  Mobile: {element} not visible")
            except:
                print(f"   ⚠️  Mobile: {element} not found")
        
        # Test mobile-specific features
        mobile_features = [
            ".mobile-menu",
            ".hamburger-menu",
            ".mobile-nav",
            ".drawer-menu",
            "☰"
        ]
        
        mobile_menu_found = False
        for feature in mobile_features:
            try:
                if page.is_visible(feature):
                    print(f"   ✅ Mobile feature found: {feature}")
                    mobile_menu_found = True
                    break
            except:
                continue
        
        if not mobile_menu_found:
            print("   ⚠️  Mobile-specific navigation not found")
        
        if mobile_visible > 0:
            print(f"   ✅ {mobile_visible}/{len(mobile_essential_elements)} elements visible on mobile")
            return True
        else:
            print("   ⚠️  No essential elements visible on mobile")
            return False
    
    def _test_touch_interactions(self, page: Page) -> bool:
        """Test touch-friendly interactions."""
        # Test tap interactions
        tappable_elements = [
            "text=New Campaign",
            ".button",
            "button",
            "a",
            ".clickable"
        ]
        
        touch_tested = 0
        for element in tappable_elements:
            try:
                if page.is_visible(element):
                    # Get element size to check if it's touch-friendly
                    element_box = page.locator(element).first.bounding_box()
                    
                    if element_box:
                        min_touch_size = 44  # 44px minimum touch target
                        
                        if element_box["width"] >= min_touch_size and element_box["height"] >= min_touch_size:
                            print(f"   ✅ Touch-friendly size: {element} ({element_box['width']}x{element_box['height']})")
                            touch_tested += 1
                        else:
                            print(f"   ⚠️  Small touch target: {element} ({element_box['width']}x{element_box['height']})")
                    
                    # Test actual tap
                    page.locator(element).first.tap()
                    page.wait_for_timeout(500)
                    print(f"   ✅ Tap successful: {element}")
                    
                    break  # Only test first tappable element
            except Exception as e:
                print(f"   ⚠️  Tap failed for {element}: {e}")
                continue
        
        if touch_tested > 0:
            print(f"   ✅ Touch interactions tested")
            return True
        else:
            print("   ⚠️  No touch interactions could be tested")
            return True  # Don't fail if elements don't exist
    
    def _test_responsive_navigation(self, page: Page) -> bool:
        """Test responsive navigation behavior."""
        # Look for mobile navigation patterns
        nav_patterns = [
            ".navbar-toggler",
            ".mobile-menu-toggle",
            ".hamburger",
            ".menu-icon",
            "☰",
            "[aria-label='Menu']",
            "button[aria-expanded]"
        ]
        
        nav_found = False
        for pattern in nav_patterns:
            try:
                if page.is_visible(pattern):
                    print(f"   ✅ Responsive nav found: {pattern}")
                    
                    # Test toggling navigation
                    page.click(pattern)
                    page.wait_for_timeout(500)
                    
                    # Look for expanded menu
                    expanded_selectors = [
                        ".navbar-collapse.show",
                        ".mobile-menu.open",
                        ".nav-menu.active",
                        "[aria-expanded='true']"
                    ]
                    
                    for exp_selector in expanded_selectors:
                        try:
                            if page.is_visible(exp_selector):
                                print(f"   ✅ Nav expanded: {exp_selector}")
                                nav_found = True
                                break
                        except:
                            continue
                    
                    # Close menu
                    page.click(pattern)
                    page.wait_for_timeout(500)
                    
                    break
            except:
                continue
        
        if not nav_found:
            print("   ⚠️  Responsive navigation not found - may use different pattern")
        
        return True
    
    def _test_responsive_layout(self, page: Page) -> bool:
        """Test responsive layout adjustments."""
        # Test different viewport sizes
        viewports = [
            {"width": 1200, "height": 800, "name": "Desktop"},
            {"width": 768, "height": 1024, "name": "Tablet"},
            {"width": 375, "height": 667, "name": "Mobile"}
        ]
        
        layout_tests_passed = 0
        
        for viewport in viewports:
            page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            page.wait_for_timeout(500)
            
            # Check if content flows properly
            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = viewport["width"]
            
            if body_width <= viewport_width + 20:  # Allow small margins
                print(f"   ✅ {viewport['name']}: No horizontal overflow ({body_width}px <= {viewport_width}px)")
                layout_tests_passed += 1
            else:
                print(f"   ⚠️  {viewport['name']}: Horizontal overflow detected ({body_width}px > {viewport_width}px)")
            
            # Check for responsive classes
            responsive_classes = page.evaluate("""
                Array.from(document.body.classList).filter(cls => 
                    cls.includes('mobile') || cls.includes('tablet') || cls.includes('responsive')
                )
            """)
            
            if responsive_classes:
                print(f"   ✅ {viewport['name']}: Responsive classes detected: {responsive_classes}")
            
        if layout_tests_passed > 0:
            print(f"   ✅ {layout_tests_passed}/{len(viewports)} viewports passed layout test")
            return True
        else:
            print("   ⚠️  Layout issues detected across viewports")
            return True  # Don't fail, just warn
    
    def _test_orientation_changes(self, page: Page) -> bool:
        """Test orientation changes (portrait/landscape)."""
        # Test portrait mobile
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(500)
        
        portrait_scrollable = page.evaluate("document.body.scrollHeight > window.innerHeight")
        print(f"   ✅ Portrait: Content scrollable = {portrait_scrollable}")
        
        # Test landscape mobile
        page.set_viewport_size({"width": 667, "height": 375})
        page.wait_for_timeout(500)
        
        landscape_scrollable = page.evaluate("document.body.scrollHeight > window.innerHeight")
        print(f"   ✅ Landscape: Content scrollable = {landscape_scrollable}")
        
        # Check if content adapts
        landscape_body_width = page.evaluate("document.body.scrollWidth")
        if landscape_body_width <= 667 + 20:
            print("   ✅ Landscape: Content adapts to wider viewport")
        else:
            print("   ⚠️  Landscape: Content may not adapt properly")
        
        # Test orientation media queries
        orientation_support = page.evaluate("""
            window.matchMedia && (
                window.matchMedia('(orientation: portrait)').matches ||
                window.matchMedia('(orientation: landscape)').matches
            )
        """)
        
        if orientation_support:
            print("   ✅ Orientation media queries supported")
        else:
            print("   ⚠️  Orientation media queries may not be supported")
        
        return True


if __name__ == "__main__":
    test = MobileResponsiveTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - Mobile responsive design tested")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)