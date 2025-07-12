#!/usr/bin/env python3
"""
Take screenshots of the planning block JSON system in action.
"""

import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def take_screenshots():
    """Take screenshots showing the JSON planning block system."""
    
    print("📸 Taking Planning Block JSON Screenshots")
    print("=" * 60)
    
    screenshot_dir = "/tmp/worldarchitectai/planning_block_screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser for debugging
        page = browser.new_page()
        
        try:
            # Start test server
            print("🚀 Starting test server...")
            import subprocess
            server = subprocess.Popen([
                sys.executable, "mvp_site/main.py", "serve"
            ], env={**os.environ, "TESTING": "true", "PORT": "6007"})
            
            # Wait for server
            time.sleep(3)
            
            # Navigate with test mode
            url = "http://localhost:6007?test_mode=true&test_user_id=screenshot-test"
            print(f"🌐 Navigating to {url}")
            page.goto(url)
            
            # Wait for page load
            page.wait_for_selector("#dashboard-view", timeout=10000)
            print("✅ Dashboard loaded")
            
            # Take screenshot 1: Dashboard
            page.screenshot(path=os.path.join(screenshot_dir, "01_dashboard.png"))
            print("📸 Screenshot 1: Dashboard")
            
            # Create a new campaign
            page.click("text=New Campaign")
            page.wait_for_selector("#new-campaign-view")
            
            # Fill campaign details
            page.fill("#campaign-title", "JSON Planning Block Demo")
            page.fill("#campaign-prompt", "Test the new JSON planning block system with various scenarios.")
            
            # Take screenshot 2: New campaign form
            page.screenshot(path=os.path.join(screenshot_dir, "02_new_campaign.png"))
            print("📸 Screenshot 2: New campaign form")
            
            # Start campaign
            page.click("#submit-campaign")
            page.wait_for_selector("#game-view", timeout=15000)
            
            # Wait for initial response
            time.sleep(3)
            
            # Take screenshot 3: Initial game view with planning block
            page.screenshot(path=os.path.join(screenshot_dir, "03_game_with_planning_block.png"))
            print("📸 Screenshot 3: Game view with JSON planning block")
            
            # Click a planning block choice if available
            try:
                choice_button = page.locator(".choice-button").first
                if choice_button:
                    # Take screenshot 4: Hovering over choice
                    choice_button.hover()
                    page.screenshot(path=os.path.join(screenshot_dir, "04_hovering_choice.png"))
                    print("📸 Screenshot 4: Hovering over choice button")
                    
                    # Click the choice
                    choice_button.click()
                    time.sleep(3)
                    
                    # Take screenshot 5: After choice selection
                    page.screenshot(path=os.path.join(screenshot_dir, "05_after_choice.png"))
                    print("📸 Screenshot 5: After selecting a choice")
            except:
                print("⚠️  No choice buttons found")
            
            # Test with custom action
            custom_input = page.locator("#user-input")
            if custom_input:
                custom_input.fill("I want to examine the room carefully for hidden doors")
                page.screenshot(path=os.path.join(screenshot_dir, "06_custom_action.png"))
                print("📸 Screenshot 6: Custom action input")
            
            print(f"\n✅ Screenshots saved to: {screenshot_dir}")
            print("\nScreenshots captured:")
            for f in sorted(os.listdir(screenshot_dir)):
                if f.endswith('.png'):
                    print(f"  - {f}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            browser.close()
            try:
                server.terminate()
                server.wait(timeout=5)
            except:
                pass
    
    return True

if __name__ == "__main__":
    take_screenshots()