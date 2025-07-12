#!/usr/bin/env python3
"""
Automated test to capture structured fields with real Gemini API responses.
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright, Page

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase, SCREENSHOT_DIR

class StructuredFieldsDemo(BrowserTestBase):
    """Capture real structured fields from Gemini API."""
    
    def __init__(self):
        super().__init__("Structured Fields Real Demo")
    
    def run_test(self, page: Page) -> bool:
        """Run demo to capture real structured fields."""
        try:
            print("📸 Starting structured fields demo with real Gemini API...")
            
            # Take initial screenshot
            self.take_screenshot(page, "01_dashboard")
            
            # Create a new campaign
            print("🎮 Creating new campaign...")
            new_campaign_btn = page.locator("text='New Campaign', button:has-text('New Campaign')").first
            if new_campaign_btn.is_visible():
                new_campaign_btn.click()
                page.wait_for_timeout(2000)
                
                # Fill wizard
                page.fill("#wizard-campaign-title", "Structured Fields Real Demo")
                page.fill("#wizard-campaign-prompt", "A fantasy adventure where I explore a dungeon filled with traps and treasures")
                page.click("#wizard-next")
                page.wait_for_timeout(1000)
                
                # Character details
                page.fill("#wizard-character-name", "Demo Hero")
                page.fill("#wizard-character-class", "Fighter/Wizard")
                page.fill("#wizard-character-race", "Human")
                page.fill("#wizard-character-background", "A brave adventurer skilled in both sword and spell")
                
                # Launch campaign
                launch_btn = page.locator("#launch-campaign, button:has-text('Begin Adventure')").first
                if launch_btn.is_visible():
                    launch_btn.click()
                    print("✅ Campaign created, waiting for game view...")
                    page.wait_for_selector("#game-view", timeout=15000)
                    page.wait_for_timeout(5000)  # Let initial content load
                    
                    self.take_screenshot(page, "02_initial_game_view")
                    
                    # Send character mode action
                    print("⚔️ Sending character mode action...")
                    action_input = page.locator("#player-action, textarea[placeholder*='What do you do']").first
                    send_btn = page.locator("button:has-text('Send')").first
                    
                    if action_input.is_visible() and send_btn.is_visible():
                        action_input.fill("I carefully examine the dungeon entrance for traps, then cast a light spell on my sword and enter cautiously.")
                        send_btn.click()
                        
                        print("⏳ Waiting for Gemini response (this will cost API credits)...")
                        page.wait_for_timeout(15000)  # Give time for real API response
                        
                        self.take_screenshot(page, "03_character_response")
                        
                        # Capture resources if visible
                        resources = page.locator(".resources, .alert-warning:has-text('Resources')").first
                        if resources.is_visible():
                            resources.screenshot(path=f"{SCREENSHOT_DIR}/field_resources.png")
                            print("✅ Captured resources field")
                        
                        # Switch to god mode
                        print("🎭 Switching to god mode...")
                        god_mode_radio = page.locator("input[value='god']").first
                        if god_mode_radio.is_visible():
                            god_mode_radio.click()
                            page.wait_for_timeout(1000)
                            
                            # Send god mode command
                            action_input.fill("What monsters and treasures await in the first chamber? Roll initiative for any encounters.")
                            send_btn.click()
                            
                            print("⏳ Waiting for god mode response...")
                            page.wait_for_timeout(15000)
                            
                            self.take_screenshot(page, "04_god_mode_response")
                            
                            # Try to capture individual fields
                            fields_to_capture = {
                                'planning_block': '.planning-block, .choice-container',
                                'dice_rolls': '.dice-rolls, .dice-roll-result',
                                'session_header': '.session-header',
                                'god_mode_response': '.god-mode-response, .gm-response'
                            }
                            
                            for field_name, selectors in fields_to_capture.items():
                                for selector in selectors.split(', '):
                                    try:
                                        element = page.locator(selector).first
                                        if element.is_visible():
                                            element.screenshot(path=f"{SCREENSHOT_DIR}/field_{field_name}.png")
                                            print(f"✅ Captured {field_name} field")
                                            break
                                    except:
                                        continue
                            
                            # Final full page screenshot
                            page.screenshot(path=f"{SCREENSHOT_DIR}/05_full_page_final.png", full_page=True)
                            print("✅ Captured full page with all fields")
                            
                            print("\n🎉 Demo completed successfully!")
                            print(f"📁 Screenshots saved to: {SCREENSHOT_DIR}")
                            return True
            
            print("❌ Could not complete demo")
            return False
            
        except Exception as e:
            print(f"❌ Error during demo: {e}")
            self.take_screenshot(page, "error_state")
            return False

if __name__ == "__main__":
    # Ensure we're using real APIs
    os.environ.pop('USE_MOCK_GEMINI', None)
    os.environ.pop('USE_MOCK_FIREBASE', None)
    
    demo = StructuredFieldsDemo()
    success = demo.execute()
    
    if success:
        print("\n✅ Structured fields demo completed!")
        print("Check the screenshots directory for captured images.")
    else:
        print("\n❌ Demo failed")