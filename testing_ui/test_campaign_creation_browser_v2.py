#!/usr/bin/env python3
"""
Browser test for campaign creation using the shared test base.
"""

from browser_test_base import BrowserTestBase, click_button_with_text, wait_for_element


class CampaignCreationTest(BrowserTestBase):
    """Test campaign creation through browser automation."""
    
    def __init__(self):
        super().__init__("Campaign Creation Browser Test")
    
    def run_test(self, page):
        """Run the campaign creation test."""
        
        # Take initial screenshot
        self.take_screenshot(page, "dashboard")
        
        # Look for campaign creation button
        print("🎮 Looking for campaign creation button...")
        if not click_button_with_text(page, "New Campaign"):
            print("❌ Could not find New Campaign button")
            return False
        
        print("✅ Clicked New Campaign button")
        page.wait_for_timeout(2000)
        
        # Fill campaign details
        print("📝 Filling campaign details...")
        self.take_screenshot(page, "campaign_form")
        
        if page.is_visible("#wizard-campaign-title"):
            print("🧙‍♂️ Campaign wizard detected")
            page.fill("#wizard-campaign-title", "Browser Test Campaign")
            page.fill("#wizard-campaign-prompt", "A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.")
            
            # Navigate through wizard steps
            for i in range(4):
                page.wait_for_timeout(1000)
                if page.is_visible("#wizard-next"):
                    print(f"   ➡️ Step {i+1}: Clicking Next")
                    page.click("#wizard-next")
                    self.take_screenshot(page, f"wizard_step_{i+2}")
                elif page.is_visible("#launch-campaign") or page.is_visible("button:has-text('Begin Adventure')"):
                    print("   🚀 Found Launch button")
                    launch_btn = page.query_selector("#launch-campaign") or page.query_selector("button:has-text('Begin Adventure')")
                    if launch_btn:
                        launch_btn.click()
                    break
        else:
            print("❌ Campaign form not found")
            return False
        
        # Wait for campaign creation
        print("⏳ Waiting for campaign creation...")
        page.wait_for_load_state("networkidle")
        
        # Check if game view is active
        if wait_for_element(page, "#game-view.active-view", timeout=15000):
            print("✅ Game view is active - campaign created!")
            self.take_screenshot(page, "game_view")
            
            # Test sending a message
            print("💬 Testing message sending...")
            message_input = page.query_selector("#message-input") or page.query_selector("textarea[placeholder*='What do you do']")
            if message_input:
                message_input.fill("Hello, I am ready to begin my adventure!")
                page.wait_for_timeout(500)
                
                send_button = page.query_selector("button:has-text('Send')") or page.query_selector("#send-button")
                if send_button:
                    send_button.click()
                else:
                    message_input.press("Enter")
                
                print("   ✅ Message sent successfully")
                page.wait_for_timeout(3000)
                self.take_screenshot(page, "after_message")
            
            return True
        else:
            print("❌ Game view did not load")
            self.take_screenshot(page, "failed_state")
            return False


if __name__ == "__main__":
    test = CampaignCreationTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - Campaign created via browser automation")
        exit(0)
    else:
        print("\n❌ TEST FAILED")
        exit(1)