#!/usr/bin/env python3
"""
Real browser test for campaign creation using Playwright.
This test automates a real browser to create a campaign through the UI.
"""

import os
import sys
import time
from playwright.sync_api import TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase
from browser_test_helpers import BrowserTestHelper
from testing_ui.config import BASE_URL


class CampaignCreationTest(BrowserTestBase):
    """Test campaign creation through browser automation."""
    
    def __init__(self):
        super().__init__("Campaign Creation Browser Test")
    
    def run_test(self, page):
        """Run the campaign creation test."""
        try:
            # Initialize browser test helper
            helper = BrowserTestHelper(page, BASE_URL)
            
            # Navigate with proper test authentication
            helper.navigate_with_test_auth()
            helper.wait_for_auth_bypass()
            
            # Take initial screenshot
            helper.take_screenshot("creation_01_homepage")
            
            # Look for "Start New Campaign" button (corrected button text)
            print("🎮 Looking for 'Start New Campaign' button...")
            
            try:
                # Wait for dashboard to load and click the Start New Campaign button
                page.wait_for_selector("#go-to-new-campaign", timeout=10000)
                page.click("#go-to-new-campaign")
                print("✅ Clicked 'Start New Campaign' button")
            except:
                helper.take_screenshot("creation_02_button_not_found")
                print("❌ Could not find 'Start New Campaign' button")
                return False
            
            # Wait for campaign creation form to load
            page.wait_for_load_state("networkidle")
            helper.take_screenshot("creation_03_campaign_form")
            
            # Fill in campaign details
            print("📝 Filling campaign details...")
            
            # Check if we're in the campaign wizard
            if page.is_visible("#campaign-wizard") or page.is_visible(".wizard-container"):
                print("🧙‍♂️ Campaign wizard detected")
                
                # Fill campaign title
                if page.is_visible("#campaign-title") or page.is_visible("input[name='title']"):
                    page.fill("#campaign-title, input[name='title']", "Browser Test Campaign")
                    print("   ✅ Filled campaign title")
                
                # Fill campaign description  
                if page.is_visible("#campaign-description") or page.is_visible("textarea[name='description']"):
                    page.fill("#campaign-description, textarea[name='description']", "This is a test campaign created by automated browser testing.")
                    print("   ✅ Filled campaign description")
                
                # Look for Next button and navigate through wizard steps
                if page.is_visible("button:has-text('Next')"):
                    print("   ➡️ Clicking Next to step 2")
                    page.click("button:has-text('Next')")
                    page.wait_for_timeout(1000)
                else:
                    print("   ❌ Next button not found")
                
                # Keep clicking through wizard steps until we reach launch
                for i in range(3):  # Steps 2, 3, 4
                    helper.take_screenshot(f"creation_wizard_step_{i+2}")
                    
                    # Check if we're on the launch step
                    if page.is_visible("#launch-campaign") or page.is_visible("button:has-text('Begin Adventure')"):
                        print(f"   🚀 Step {i+2}: Found Launch/Begin Adventure button")
                        print("   🎯 Clicking launch button...")
                        
                        # Wait for button to be properly visible and stable
                        try:
                            page.wait_for_selector("button:has-text('Begin Adventure')", state="visible", timeout=5000)
                            # Scroll button into view and wait for stability
                            button = page.locator("button:has-text('Begin Adventure')").first
                            button.scroll_into_view_if_needed()
                            page.wait_for_timeout(1000)  # Let animations settle
                            button.click(timeout=10000)
                            print("   ✅ Successfully clicked Begin Adventure button")
                        except Exception as e:
                            print(f"   ⚠️  Button click failed, trying alternative: {e}")
                            # Try clicking by ID if text selector fails
                            if page.is_visible("#launch-campaign"):
                                page.click("#launch-campaign", timeout=10000)
                            else:
                                # Force click with JavaScript
                                page.evaluate("document.querySelector('button[type=submit]').click()")
                        break
                    elif page.is_visible("button:has-text('Next')"):
                        print(f"   ➡️ Step {i+2}: Clicking Next")
                        page.click("button:has-text('Next')")
                        page.wait_for_timeout(1000)
                    else:
                        print(f"   ⚠️  Step {i+2}: No Next or Launch button found")
                        break
            
            # Wait for campaign creation to complete
            print("⏳ Waiting for campaign creation...")
            try:
                # Wait for spinner to disappear and game view to appear
                page.wait_for_selector(".spinner", state="hidden", timeout=5000)
            except TimeoutError:
                print("   ⚠️  Spinner timeout - checking game state anyway")
            
            # Check if we successfully created the campaign
            try:
                page.wait_for_selector("#game-view", timeout=10000)
                print("✅ Game view is active - campaign created!")
                helper.take_screenshot("creation_04_game_view")
                
                # Check for campaign elements
                # (Add any specific validation here)
                
                campaign_created = True
            except TimeoutError:
                print("⚠️  Game view not active, checking other states...")
                helper.take_screenshot("creation_04_timeout_state")
                
                # Check which view is currently active
                current_view = page.evaluate("""
                    const views = ['auth-view', 'dashboard-view', 'new-campaign-view', 'game-view'];
                    return views.find(view => document.getElementById(view)?.classList.contains('active-view')) || 'unknown';
                """)
                print(f"   📍 Current view: {current_view}")
                
                if current_view == "game-view":
                    campaign_created = True
                    print("✅ Campaign created successfully!")
                else:
                    print("❌ Campaign creation verification failed")
                    return False
            
            # Test character creation if we're in game view
            print("👤 Testing character creation...")
            
            # Wait for character creation form
            page.wait_for_load_state("networkidle")
            helper.take_screenshot("creation_05_character_form")
            
            # Fill character details if form is visible
            if page.is_visible("#character-name") or page.is_visible("input[name='characterName']"):
                page.fill("#character-name, input[name='characterName']", "Test Hero")
                print("   ✅ Filled character name")
            
            page.wait_for_load_state("networkidle")
            helper.take_screenshot("creation_06_final_state")
            
            print("✅ Browser test completed successfully!")
            return True
            
        except TimeoutError as e:
            print(f"❌ Timeout error: {e}")
            helper.take_screenshot("creation_error_timeout")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            helper.take_screenshot("creation_error_general")
            return False


def test_campaign_creation_browser():
    """Entry point for standalone execution."""
    test = CampaignCreationTest()
    return test.execute()


if __name__ == "__main__":
    print("🚀 Starting WorldArchitect.AI Campaign Creation Browser Test")
    
    success = test_campaign_creation_browser()
    
    if success:
        print("\n✅ TEST PASSED - Campaign created via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)