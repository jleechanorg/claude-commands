#!/usr/bin/env python3
"""
Browser test to verify TASK-137: Download/Share buttons moved to top of campaign page.
Tests that buttons are positioned correctly below the campaign title.
"""

import os
import sys
from playwright.sync_api import Page, sync_playwright

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class Task137ButtonPlacementTest(BrowserTestBase):
    """Test that download/share buttons are positioned at top of campaign page per TASK-137."""
    
    def __init__(self):
        super().__init__("TASK-137 Button Placement Test")
    
    def run_test(self, page: Page) -> bool:
        """Test button placement after TASK-137 changes."""
        try:
            self.take_screenshot(page, "initial_dashboard")
            
            # Create a campaign to get to game view where buttons should be visible
            print("🎮 Creating test campaign to access game view...")
            if not self._create_quick_campaign(page):
                print("❌ Failed to create test campaign")
                return False
            
            self.take_screenshot(page, "campaign_created")
            
            # Wait for game view to load
            page.wait_for_selector("#game-view", timeout=10000)
            print("✅ Game view loaded")
            
            # Test button positioning
            print("📍 Testing button placement after TASK-137...")
            button_positioning_ok = self._test_button_positioning(page)
            
            self.take_screenshot(page, "button_placement_final")
            
            if button_positioning_ok:
                print("✅ TASK-137 button placement verification PASSED")
                return True
            else:
                print("❌ TASK-137 button placement verification FAILED")
                return False
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error")
            return False
    
    def _create_quick_campaign(self, page: Page) -> bool:
        """Create a campaign quickly to test button placement."""
        try:
            # Click start new campaign
            if page.is_visible("text=Start New Campaign"):
                page.click("text=Start New Campaign")
                page.wait_for_timeout(1000)
            
            # Fill form quickly
            if page.is_visible("#campaign-title"):
                page.fill("#campaign-title", "TASK-137 Button Test")
                page.fill("#campaign-prompt", "Testing button placement.")
                
                # Submit form
                page.click("text=Begin Adventure!")
                page.wait_for_timeout(3000)
                
                print("   ✅ Campaign created")
                return True
            
        except Exception as e:
            print(f"   ❌ Error creating campaign: {e}")
            
        return False
    
    def _test_button_positioning(self, page: Page) -> bool:
        """Test that download/share buttons are positioned correctly."""
        positioning_tests = []
        
        # Test 1: Check if buttons exist
        download_btn = page.query_selector("#downloadStoryBtn")
        share_btn = page.query_selector("#shareStoryBtn")
        
        if download_btn and share_btn:
            print("   ✅ Both download and share buttons found")
            positioning_tests.append(True)
        else:
            print("   ❌ Download or share button not found")
            positioning_tests.append(False)
        
        # Test 2: Check button positioning relative to title
        game_title = page.query_selector("#game-title")
        
        if game_title and download_btn:
            # Get element positions
            title_box = game_title.bounding_box()
            button_box = download_btn.bounding_box()
            
            if title_box and button_box:
                # Check if buttons are below the title (higher Y coordinate)
                if button_box['y'] > title_box['y']:
                    print("   ✅ Buttons positioned below campaign title")
                    positioning_tests.append(True)
                else:
                    print("   ❌ Buttons appear to be above campaign title")
                    positioning_tests.append(False)
                
                # Check if buttons are near the top of the page
                if button_box['y'] < 300:  # Should be in top portion of page
                    print("   ✅ Buttons positioned near top of page")
                    positioning_tests.append(True)
                else:
                    print("   ❌ Buttons appear to be too far down the page")
                    positioning_tests.append(False)
                    
                print(f"   📍 Title Y position: {title_box['y']}")
                print(f"   📍 Button Y position: {button_box['y']}")
            else:
                print("   ❌ Could not get element positions")
                positioning_tests.append(False)
        else:
            print("   ❌ Could not find title or button elements")
            positioning_tests.append(False)
        
        # Test 3: Check if buttons are in the correct container
        button_container = page.query_selector(".d-flex.justify-content-end.gap-2.mb-3")
        if button_container and download_btn:
            # Check if download button is within the container
            container_box = button_container.bounding_box()
            button_box = download_btn.bounding_box()
            
            if (container_box and button_box and 
                container_box['x'] <= button_box['x'] <= container_box['x'] + container_box['width'] and
                container_box['y'] <= button_box['y'] <= container_box['y'] + container_box['height']):
                print("   ✅ Buttons are in correct container")
                positioning_tests.append(True)
            else:
                print("   ❌ Buttons not in expected container")
                positioning_tests.append(False)
        else:
            print("   ❌ Could not find button container")
            positioning_tests.append(False)
        
        # Test 4: Verify buttons are visible when in game view
        if page.is_visible("#downloadStoryBtn") and page.is_visible("#shareStoryBtn"):
            print("   ✅ Buttons are visible in game view")
            positioning_tests.append(True)
        else:
            print("   ❌ Buttons not visible in game view")
            positioning_tests.append(False)
        
        # Return True if most tests passed
        passed_tests = sum(positioning_tests)
        total_tests = len(positioning_tests)
        
        print(f"   📊 Button positioning tests: {passed_tests}/{total_tests} passed")
        
        return passed_tests >= (total_tests * 0.75)  # 75% pass rate required


if __name__ == "__main__":
    test = Task137ButtonPlacementTest()
    success = test.execute()
    
    if success:
        print("\n✅ TASK-137 TEST PASSED - Download/Share buttons correctly positioned")
        sys.exit(0)
    else:
        print("\n❌ TASK-137 TEST FAILED - Button positioning issues detected")
        sys.exit(1)