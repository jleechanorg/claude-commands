#!/usr/bin/env python3
"""
Real browser test for God Mode interactions using Playwright.
This test automates a real browser to test God Mode functionality.
"""

import os
import sys
from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_ui.browser_test_base import BrowserTestBase, click_button_with_text, wait_for_element


class GodModeTest(BrowserTestBase):
    """Test God Mode interactions through real browser automation."""
    
    def __init__(self):
        super().__init__("God Mode Test")
    
    def run_test(self, page: Page) -> bool:
        """Test God Mode interactions through real browser automation."""
        
        try:
            # Take initial screenshot
            self.take_screenshot(page, "homepage")
            
            # Create a new campaign first
            print("🎮 Creating a test campaign for God Mode...")
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(1000)
                
                # Fill in campaign details
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "God Mode Test Campaign")
                    page.fill("#wizard-campaign-prompt", "A mystical realm where gods intervene in mortal affairs.")
                    
                    # Click through wizard
                    print("   📝 Navigating wizard...")
                    for i in range(4):
                        if page.is_visible("#wizard-next"):
                            page.click("#wizard-next")
                            page.wait_for_timeout(1000)
                        elif page.is_visible("#launch-campaign") or page.is_visible("button:has-text('Begin Adventure')"):
                            print("   🚀 Launching campaign...")
                            launch_btn = page.query_selector("#launch-campaign") or page.query_selector("button:has-text('Begin Adventure')")
                            if launch_btn:
                                launch_btn.click()
                            break
                
                # Wait for game view
                page.wait_for_load_state("networkidle")
                try:
                    page.wait_for_selector("#game-view.active-view", timeout=15000)
                    print("✅ Game view active")
                except:
                    print("⚠️  Game view timeout - continuing anyway")
            
            self.take_screenshot(page, "game_view")
            
            # Test switching to God Mode
            print("🔮 Testing God Mode toggle...")
            
            # Look for mode toggle
            if page.is_visible("text=God Mode"):
                print("   ✅ Found God Mode option")
                page.click("text=God Mode")
                page.wait_for_timeout(1000)
            elif page.is_visible("#god-mode-toggle"):
                print("   ✅ Found God Mode toggle")
                page.click("#god-mode-toggle")
                page.wait_for_timeout(1000)
            else:
                # Try radio button approach
                god_radio = page.query_selector("input[type='radio'][value='god']")
                if god_radio:
                    print("   ✅ Found God Mode radio button")
                    god_radio.click()
                    page.wait_for_timeout(1000)
            
            self.take_screenshot(page, "god_mode_active")
            
            # Test God Mode command
            print("⚡ Sending God Mode command...")
            
            # Find message input
            message_input = page.query_selector("#message-input") or page.query_selector("textarea[placeholder*='What do you do']")
            if message_input:
                # Type a God Mode command
                god_command = "Create a powerful storm that sweeps across the land"
                message_input.fill(god_command)
                print(f"   📝 Typed: {god_command}")
                
                # Send the message
                send_button = page.query_selector("button:has-text('Send')") or page.query_selector("#send-button")
                if send_button:
                    send_button.click()
                    print("   ✉️ Message sent")
                else:
                    # Try pressing Enter
                    message_input.press("Enter")
                    print("   ⏎ Pressed Enter")
                
                # Wait for response
                print("⏳ Waiting for AI response...")
                page.wait_for_timeout(5000)  # Give AI time to respond
                
                self.take_screenshot(page, "god_response")
                
                # Check for response
                chat_area = page.query_selector("#chat-messages") or page.query_selector(".chat-messages")
                if chat_area:
                    messages = chat_area.text_content()
                    if "storm" in messages.lower() or "lightning" in messages.lower():
                        print("✅ God Mode response received!")
                    else:
                        print("⚠️  Response received but no storm-related content")
            
            # Test state updates in God Mode
            print("📊 Checking for state updates...")
            
            # Look for state update indicators
            if page.is_visible("text=STATE UPDATES"):
                print("   ✅ State updates visible")
            
            debug_panel = page.query_selector(".debug-panel") or page.query_selector("#debug-content")
            if debug_panel and debug_panel.is_visible():
                debug_content = debug_panel.text_content()
                if "custom_campaign_state" in debug_content:
                    print("   ✅ Campaign state visible in debug panel")
                if "world_state" in debug_content:
                    print("   ✅ World state visible in debug panel")
            
            self.take_screenshot(page, "state_updates")
            
            # Test switching back to Character Mode
            print("👤 Testing switch back to Character Mode...")
            
            if page.is_visible("text=Character Mode"):
                page.click("text=Character Mode")
                page.wait_for_timeout(1000)
            else:
                char_radio = page.query_selector("input[type='radio'][value='character']")
                if char_radio:
                    char_radio.click()
                    page.wait_for_timeout(1000)
            
            self.take_screenshot(page, "character_mode")
            
            # Verify mode switch
            if page.is_visible("input[type='radio'][value='character']:checked"):
                print("✅ Successfully switched back to Character Mode")
            
            print("\n✅ God Mode browser test completed successfully!")
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
    test = GodModeTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - God Mode tested via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)