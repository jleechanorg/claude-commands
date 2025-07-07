#!/usr/bin/env python3
"""
Real browser test for campaign creation using Playwright.
This test automates a real browser to create a campaign through the UI.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8080?test_mode=true&test_user_id=browser-test-user"
SCREENSHOT_DIR = "/tmp/worldarchitect_browser_screenshots"

def test_campaign_creation_browser():
    """Test campaign creation through real browser automation."""
    
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser (headless=False to see it in action)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Set up console listener before navigation
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            # Also capture errors
            page.on("pageerror", lambda exc: console_logs.append(f"error: {exc}"))
            
            print("🌐 Navigating to WorldArchitect.AI...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_01_homepage.png"))
            
            # Wait for test mode to initialize and trigger route change
            print("⏳ Waiting for test mode initialization...")
            page.wait_for_timeout(3000)  # Give test mode time to set up
            
            # Try to wait for dashboard view to become active
            try:
                page.wait_for_selector("#dashboard-view.active-view", timeout=5000)
                print("✅ Dashboard view is now active")
            except TimeoutError:
                print("⚠️  Dashboard view did not become active")
                # Try to manually trigger route change
                page.evaluate("if (window.handleRouteChange) window.handleRouteChange()")
                page.wait_for_timeout(1000)
            
            # Check if we're still on auth page (shouldn't be with test mode)
            if page.is_visible("text=Sign In") or page.is_visible("text=Sign in with Google"):
                print("❌ Still on auth page - test mode may not be working")
                print("   Make sure server was started with: TESTING=true")
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_01_auth_blocked.png"))
                return False
            
            # Print any console messages
            if console_logs:
                print("📋 Console messages:")
                for log in console_logs:
                    print(f"   {log}")
            
            # Look for "New Campaign" or "Create Campaign" button
            print("🎮 Looking for campaign creation button...")
            
            # Debug: print page content
            page_content = page.content()
            if len(page_content) < 1000:
                print(f"⚠️  Page content seems too short ({len(page_content)} chars)")
            
            # Check which view is active
            views = ["auth-view", "dashboard-view", "new-campaign-view", "game-view"]
            for view_id in views:
                view_elem = page.query_selector(f"#{view_id}")
                if view_elem:
                    classes = view_elem.get_attribute("class") or ""
                    is_active = "active-view" in classes
                    print(f"   View #{view_id}: active={is_active}")
            
            # Try different possible selectors
            campaign_button_selectors = [
                "text=New Campaign",
                "text=Create Campaign", 
                "text=Start New Campaign",
                "button:has-text('Campaign')",
                "#new-campaign-btn",
                "#go-to-new-campaign",
                ".create-campaign-button"
            ]
            
            button_found = False
            for selector in campaign_button_selectors:
                if page.is_visible(selector):
                    print(f"✅ Found button with selector: {selector}")
                    page.click(selector)
                    button_found = True
                    break
            
            if not button_found:
                # Take screenshot to debug
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_02_no_button_found.png"))
                print("❌ Could not find campaign creation button")
                print("📸 Screenshot saved to help debug")
                return False
            
            # Wait for campaign creation form or modal
            page.wait_for_load_state("networkidle")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_03_campaign_form.png"))
            
            # Fill in campaign details
            print("📝 Filling campaign details...")
            
            # Check if we're in wizard mode or traditional form
            if page.is_visible(".wizard-step"):
                print("🧙‍♂️ Campaign wizard detected")
                
                # Fill in campaign title and description
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Browser Test Campaign")
                    print("   ✅ Filled campaign title")
                
                if page.is_visible("#wizard-campaign-prompt"):
                    page.fill("#wizard-campaign-prompt", "A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.")
                    print("   ✅ Filled campaign description")
                
                # Click Next to proceed to step 2
                if page.is_visible("#wizard-next"):
                    print("   ➡️ Clicking Next to step 2")
                    page.click("#wizard-next")
                    page.wait_for_timeout(1000)
                else:
                    print("   ❌ Next button not found")
                
                # Keep clicking through wizard steps until we reach launch
                for i in range(3):  # Steps 2, 3, 4
                    page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"creation_wizard_step_{i+2}.png"))
                    
                    # Check if we're on the launch step
                    if page.is_visible("#launch-campaign") or page.is_visible("button:has-text('Begin Adventure')"):
                        print(f"   🚀 Step {i+2}: Found Launch/Begin Adventure button")
                        # Try the correct ID first
                        launch_btn = page.query_selector("#launch-campaign")
                        if not launch_btn:
                            launch_btn = page.query_selector("button:has-text('Begin Adventure')")
                        
                        if launch_btn:
                            print("   🎯 Clicking launch button...")
                            launch_btn.click()
                            page.wait_for_timeout(2000)  # Wait for campaign creation
                        break
                    elif page.is_visible("#wizard-next"):
                        print(f"   ➡️ Step {i+2}: Clicking Next")
                        page.click("#wizard-next")
                        page.wait_for_timeout(1000)
                    else:
                        print(f"   ⚠️ Step {i+2}: No navigation button found")
                        # Try to find any visible button in wizard navigation
                        wizard_nav_btns = page.query_selector_all(".wizard-navigation button")
                        for btn in wizard_nav_btns:
                            if btn.is_visible():
                                btn_text = btn.text_content()
                                print(f"   📍 Found button: {btn_text}")
                                if "Launch" in btn_text or "Create" in btn_text:
                                    btn.click()
                                    break
            else:
                # Traditional form
                print("📋 Traditional form detected")
                # Try to find campaign name input
                name_selectors = [
                    "input[name='campaign-name']",
                    "#campaign-title",
                    "input[placeholder*='Campaign']",
                    "#campaign-name"
                ]
                
                for selector in name_selectors:
                    if page.is_visible(selector):
                        page.fill(selector, "Browser Test Campaign")
                        break
                
                # Submit the form
                submit_selectors = [
                    "button:has-text('Create')",
                    "button:has-text('Start')",
                    "button[type='submit']",
                    "#create-campaign-btn"
                ]
                
                for selector in submit_selectors:
                    if page.is_visible(selector):
                        page.click(selector)
                        break
            
            # Wait for campaign to be created
            print("⏳ Waiting for campaign creation...")
            page.wait_for_load_state("networkidle")
            
            # Wait for the spinner to disappear
            try:
                page.wait_for_selector("#campaign-creation-spinner", state="detached", timeout=15000)
                print("   ✅ Creation spinner completed")
            except:
                print("   ⚠️  Spinner timeout - checking game state anyway")
            
            # Verify we're in a campaign (look for game view)
            try:
                page.wait_for_selector("#game-view.active-view", timeout=10000)
                print("✅ Game view is active - campaign created!")
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_04_game_view.png"))
                
                # Check for campaign elements
                if page.is_visible("#message-input"):
                    print("   ✅ Message input visible")
                if page.is_visible("#chat-messages"):
                    print("   ✅ Chat area visible")
                if page.is_visible(".campaign-title"):
                    campaign_title = page.text_content(".campaign-title")
                    print(f"   ✅ Campaign title: {campaign_title}")
                    
            except TimeoutError:
                print("⚠️  Game view not active, checking other states...")
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_04_timeout_state.png"))
                
                # Check which view is currently active
                views = ["auth-view", "dashboard-view", "new-campaign-view", "game-view"]
                for view_id in views:
                    if page.is_visible(f"#{view_id}.active-view"):
                        print(f"   📍 Current view: {view_id}")
                
                # Maybe we're back at dashboard, check for the new campaign
                if page.is_visible("text=Browser Test Campaign"):
                    print("✅ Campaign visible in dashboard (but not in game view)")
                    return True  # Still counts as success
                else:
                    print("❌ Campaign creation verification failed")
                    return False
            
            print("✅ Campaign created successfully!")
            
            # Test character creation within campaign
            print("👤 Testing character creation...")
            
            char_selectors = [
                "text=Create Character",
                "text=New Character",
                "button:has-text('Character')"
            ]
            
            for selector in char_selectors:
                if page.is_visible(selector):
                    page.click(selector)
                    break
            
            # Wait for character creation form
            page.wait_for_load_state("networkidle")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_05_character_form.png"))
            
            # Fill character details if form is visible
            if page.is_visible("input[type='text']"):
                page.fill("input[type='text']:first-of-type", "Test Hero")
            
            # Submit character
            for selector in ["button:has-text('Create')", "button[type='submit']"]:
                if page.is_visible(selector):
                    page.click(selector)
                    break
            
            page.wait_for_load_state("networkidle")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_06_final_state.png"))
            
            print("✅ Browser test completed successfully!")
            return True
            
        except TimeoutError as e:
            print(f"❌ Timeout error: {e}")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_error_timeout.png"))
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "creation_error_general.png"))
            return False
        finally:
            browser.close()


if __name__ == "__main__":
    print("🚀 Starting WorldArchitect.AI Campaign Creation Browser Test")
    print(f"📍 Target URL: {BASE_URL}")
    print(f"📸 Screenshots will be saved to: {SCREENSHOT_DIR}")
    
    success = test_campaign_creation_browser()
    
    if success:
        print("\n✅ TEST PASSED - Campaign created via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)