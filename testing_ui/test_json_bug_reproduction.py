#!/usr/bin/env python3
"""
Browser test to reproduce JSON bug and capture BEFORE state.
This test will:
1. Create a campaign with specific premise
2. Choose option 2 for character creation
3. Capture the JSON bug display
"""

import os
import sys
import time
from playwright.sync_api import Page, ConsoleMessage

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase

class JsonBugReproductionTest(BrowserTestBase):
    """Test to reproduce JSON display bug."""
    
    def __init__(self):
        super().__init__("JSON Bug Reproduction Test")
        self.console_logs = []
    
    def capture_console(self, msg: ConsoleMessage):
        """Capture browser console messages."""
        self.console_logs.append(f"[{msg.type}] {msg.text}")
    
    def run_test(self, page: Page):
        """Run the JSON bug reproduction test."""
        # Attach console listener
        page.on("console", self.capture_console)
        
        # Inject API monitoring
        page.add_init_script("""
            const originalFetch = window.fetch;
            window.fetch = async function(...args) {
                console.log('🔍 API_REQUEST:', args[0]);
                const response = await originalFetch.apply(window, args);
                const clone = response.clone();
                
                try {
                    const data = await clone.json();
                    if (data.text && typeof data.text === 'string') {
                        const isJson = data.text.trim().startsWith('{');
                        console.log('🔍 API_RESPONSE:', {
                            url: args[0],
                            textIsJSON: isJson,
                            textPreview: data.text.substring(0, 200)
                        });
                        
                        if (isJson && data.text.includes('narrative')) {
                            console.error('🚨 JSON BUG DETECTED: API returned JSON in text field!');
                        }
                    }
                } catch (e) {}
                
                return response;
            };
        """)
        
        # Take initial screenshot
        self.take_screenshot(page, "json_bug_01_homepage")
        
        # Click New Campaign
        print("🎮 Creating new campaign...")
        new_campaign_btn = page.get_by_role("button", name="New Campaign")
        new_campaign_btn.click()
        
        time.sleep(1)
        self.take_screenshot(page, "json_bug_02_campaign_form")
        
        # Fill campaign details
        print("📝 Filling campaign details...")
        page.fill("#campaignTitle", "JSON Bug Test Campaign")
        page.fill("#campaignPremise", "A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.")
        
        # Select default world
        page.click('input[name="customizationOption"][value="defaultWorld"]')
        
        self.take_screenshot(page, "json_bug_03_form_filled")
        
        # Submit form
        print("🚀 Creating campaign...")
        page.click('button[type="submit"]')
        
        # Wait for campaign to load
        page.wait_for_selector("#storyLog", timeout=30000)
        time.sleep(3)
        
        self.take_screenshot(page, "json_bug_04_campaign_created")
        
        # Now trigger the bug - type "2" for AI character creation
        print("🔍 Triggering JSON bug by selecting option 2...")
        input_field = page.query_selector("#userInput")
        if input_field:
            input_field.fill("2")
            self.take_screenshot(page, "json_bug_05_typed_2")
            
            # Submit
            input_field.press("Enter")
            
            print("⏳ Waiting for AI response...")
            time.sleep(10)  # Wait for response
            
            # Capture the JSON bug
            self.take_screenshot(page, "json_bug_06_BEFORE_json_displayed")
            
            # Get the last story entry
            story_entries = page.query_selector_all(".message-bubble")
            if story_entries and len(story_entries) > 1:
                last_entry = story_entries[-1]
                bug_text = last_entry.inner_text()
                
                print("\n🚨 CAPTURED BUG STATE:")
                print(f"Text displayed: {bug_text[:300]}...")
                
                if "{" in bug_text and "narrative" in bug_text:
                    print("✅ JSON BUG SUCCESSFULLY REPRODUCED!")
                    
                    # Save the full text for analysis
                    with open("/tmp/json_bug_before.txt", "w") as f:
                        f.write(bug_text)
                    print("💾 Full bug text saved to /tmp/json_bug_before.txt")
                else:
                    print("❓ Bug may not have been triggered - no JSON detected")
            
            # Print console logs
            print("\n📋 Browser Console Logs:")
            for log in self.console_logs:
                print(f"  {log}")
            
            return True
        else:
            print("❌ Could not find input field")
            return False

def test_json_bug_reproduction():
    """Entry point for standalone execution."""
    test = JsonBugReproductionTest()
    return test.execute()


if __name__ == "__main__":
    print("🚀 Starting JSON Bug Reproduction Test")
    print("⚠️  This test uses REAL Gemini and Firebase APIs")
    
    # Run with real APIs
    os.environ['USE_MOCKS'] = 'false'
    
    success = test_json_bug_reproduction()
    
    if success:
        print("\n✅ Test completed - check screenshots:")
        print("   Key screenshot: json_bug_06_BEFORE_json_displayed.png")
        sys.exit(0)
    else:
        print("\n❌ Test failed")
        sys.exit(1)