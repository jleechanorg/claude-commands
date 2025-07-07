#!/usr/bin/env python3
"""
Browser test for campaign continuation using the shared test base.
"""

from browser_test_base import BrowserTestBase, click_button_with_text, wait_for_element


class CampaignContinuationTest(BrowserTestBase):
    """Test continuing an existing campaign through browser automation."""
    
    def __init__(self):
        super().__init__("Campaign Continuation Browser Test")
    
    def run_test(self, page):
        """Run the campaign continuation test."""
        
        # First create a campaign to continue
        print("🎮 Creating initial campaign...")
        if not self._create_campaign(page):
            return False
        
        # Make some progress
        print("📝 Making progress in the campaign...")
        if not self._make_progress(page):
            return False
        
        # Return to dashboard
        print("🏠 Returning to dashboard...")
        if not self._return_to_dashboard(page):
            return False
        
        # Find and continue the campaign
        print("🔍 Looking for campaign to continue...")
        if not self._continue_campaign(page):
            return False
        
        # Verify continuation worked
        print("✅ Campaign continuation successful!")
        return True
    
    def _create_campaign(self, page):
        """Create a campaign to test continuation."""
        if not click_button_with_text(page, "New Campaign"):
            print("❌ Could not find New Campaign button")
            return False
        
        page.wait_for_timeout(2000)
        
        # Fill campaign details
        if page.is_visible("#wizard-campaign-title"):
            page.fill("#wizard-campaign-title", "Adventure to Continue")
            page.fill("#wizard-campaign-prompt", "A quest to find the lost artifact of power.")
            
            # Navigate through wizard
            for i in range(4):
                page.wait_for_timeout(1000)
                if page.is_visible("#wizard-next"):
                    page.click("#wizard-next")
                elif page.is_visible("#launch-campaign") or page.is_visible("button:has-text('Begin Adventure')"):
                    launch_btn = page.query_selector("#launch-campaign") or page.query_selector("button:has-text('Begin Adventure')")
                    if launch_btn:
                        launch_btn.click()
                    break
            
            # Wait for game view
            if wait_for_element(page, "#game-view.active-view", timeout=15000):
                print("   ✅ Campaign created")
                self.take_screenshot(page, "campaign_created")
                return True
        
        print("   ❌ Failed to create campaign")
        return False
    
    def _make_progress(self, page):
        """Make some progress in the campaign."""
        message_input = page.query_selector("#message-input") or page.query_selector("textarea[placeholder*='What do you do']")
        if message_input:
            message_input.fill("I search for clues about the artifact's location")
            page.wait_for_timeout(500)
            
            send_button = page.query_selector("button:has-text('Send')") or page.query_selector("#send-button")
            if send_button:
                send_button.click()
            else:
                message_input.press("Enter")
            
            print("   ✅ Progress made")
            page.wait_for_timeout(8000)  # Wait for AI response
            self.take_screenshot(page, "progress_made")
            return True
        
        print("   ❌ Could not send message")
        return False
    
    def _return_to_dashboard(self, page):
        """Return to the dashboard."""
        back_button = page.query_selector("button:has-text('Back to Dashboard')") or page.query_selector("button:has-text('Dashboard')")
        if back_button:
            back_button.click()
            page.wait_for_timeout(3000)
            
            if wait_for_element(page, "#dashboard-view.active-view"):
                print("   ✅ Returned to dashboard")
                self.take_screenshot(page, "back_to_dashboard")
                return True
        
        print("   ❌ Could not return to dashboard")
        return False
    
    def _continue_campaign(self, page):
        """Find and continue the campaign."""
        # Look for the campaign
        campaign_selectors = [
            "text=Adventure to Continue",
            ".campaign-card:has-text('Adventure to Continue')",
            "[data-campaign-title='Adventure to Continue']"
        ]
        
        for selector in campaign_selectors:
            if page.is_visible(selector):
                print(f"   ✅ Found campaign with selector: {selector}")
                page.click(selector)
                page.wait_for_timeout(3000)
                
                if wait_for_element(page, "#game-view.active-view", timeout=10000):
                    print("   ✅ Campaign loaded")
                    self.take_screenshot(page, "campaign_continued")
                    
                    # Send another message to verify
                    message_input = page.query_selector("#message-input") or page.query_selector("textarea[placeholder*='What do you do']")
                    if message_input:
                        message_input.fill("I continue my search based on the clues found")
                        page.wait_for_timeout(500)
                        
                        send_button = page.query_selector("button:has-text('Send')") or page.query_selector("#send-button")
                        if send_button:
                            send_button.click()
                        else:
                            message_input.press("Enter")
                        
                        print("   ✅ Follow-up action sent")
                        page.wait_for_timeout(5000)
                        self.take_screenshot(page, "continued_gameplay")
                    
                    return True
        
        print("   ❌ Could not find campaign to continue")
        return False


if __name__ == "__main__":
    test = CampaignContinuationTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - Campaign continuation tested via browser automation")
        exit(0)
    else:
        print("\n❌ TEST FAILED")
        exit(1)