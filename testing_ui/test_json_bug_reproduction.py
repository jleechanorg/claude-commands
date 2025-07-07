#!/usr/bin/env python3
"""
Focused UI test to reproduce the JSON display bug.
Follows the exact scenario where user reported seeing raw JSON in the UI.
"""

import os
import sys
import time
from playwright.sync_api import TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase, BASE_URL


class JSONBugReproductionTest(BrowserTestBase):
    """Test to reproduce JSON display bug with specific scenario."""
    
    def __init__(self):
        super().__init__("JSON Bug Reproduction Test - Invincible Scenario")
    
    def run_test(self, page):
        """
        Reproduce the exact scenario where raw JSON appeared.
        Uses the prompt: "Play as Nolan's son. He's offering you to join him. TV show invincible"
        """
        print("\n=== TEST: JSON Bug Reproduction - Invincible Scenario ===")
        
        # Navigate to campaign creation
        print("1. Going to home page...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Click Create Campaign
        print("2. Looking for campaign creation button...")
        
        # Try multiple selectors for campaign creation button
        button_selectors = [
            "text=New Campaign",
            "button:has-text('New Campaign')",
            "#new-campaign-btn",
            ".new-campaign-button",
            "text=Create Campaign",
            "button:has-text('Create Campaign')"
        ]
        
        button_found = False
        for selector in button_selectors:
            if page.is_visible(selector):
                print(f"   Found button with selector: {selector}")
                page.click(selector)
                button_found = True
                break
        
        if not button_found:
            # Take screenshot to debug
            self.take_screenshot(page, "json_bug_no_button_found")
            print("   ❌ Could not find campaign creation button")
            return False
        
        # Wait for form to load
        page.wait_for_timeout(1000)
        
        # Fill in campaign details with the exact prompt
        print("3. Filling campaign form with Invincible scenario...")
        
        # Check if we're in a wizard or simple form
        if page.is_visible("#campaign-wizard") or page.is_visible(".wizard-container"):
            print("   Using wizard interface...")
            
            # Fill campaign title
            if page.is_visible("#campaign-title"):
                page.fill("#campaign-title", "Invincible Test Campaign")
            elif page.is_visible("input[name='title']"):
                page.fill("input[name='title']", "Invincible Test Campaign")
            
            # Fill campaign description with the exact prompt that triggered the bug
            if page.is_visible("#campaign-description"):
                page.fill("#campaign-description", "Play as Nolan's son. He's offering you to join him. TV show invincible")
            elif page.is_visible("textarea[name='description']"):
                page.fill("textarea[name='description']", "Play as Nolan's son. He's offering you to join him. TV show invincible")
            
            # Navigate through wizard if needed
            while page.is_visible("button:has-text('Next')"):
                print("   Clicking Next...")
                page.click("button:has-text('Next')")
                page.wait_for_timeout(1000)
            
            # Look for launch button
            if page.is_visible("#launch-campaign"):
                page.click("#launch-campaign")
            elif page.is_visible("button:has-text('Begin Adventure')"):
                page.click("button:has-text('Begin Adventure')")
            elif page.is_visible("button:has-text('Launch Campaign')"):
                page.click("button:has-text('Launch Campaign')")
        else:
            print("   Using simple form interface...")
            
            # Try different field selectors
            if page.is_visible("#campaign-name"):
                page.fill("#campaign-name", "Invincible Test Campaign")
            elif page.is_visible("input[placeholder*='Campaign']"):
                page.fill("input[placeholder*='Campaign']", "Invincible Test Campaign")
            
            # Fill prompt/description
            if page.is_visible("#campaign-prompt"):
                page.fill("#campaign-prompt", "Play as Nolan's son. He's offering you to join him. TV show invincible")
            elif page.is_visible("textarea"):
                page.fill("textarea", "Play as Nolan's son. He's offering you to join him. TV show invincible")
            
            # Submit
            if page.is_visible("#create-campaign-submit"):
                page.click("#create-campaign-submit")
            elif page.is_visible("button[type='submit']"):
                page.click("button[type='submit']")
            elif page.is_visible("button:has-text('Create')"):
                page.click("button:has-text('Create')")
        
        # Wait for campaign to load
        print("4. Waiting for campaign to load...")
        page.wait_for_timeout(5000)
        
        # Check for JSON artifacts in initial story
        print("5. Checking for JSON artifacts in opening story...")
        story_area = page.locator("#story-area")
        story_text = story_area.inner_text()
        
        # Look for telltale signs of raw JSON
        json_indicators = [
            'Scene #',
            '"narrative":',
            '"god_mode_response":',
            '"entities_mentioned":',
            '{',
            '}'
        ]
        
        found_json = False
        for indicator in json_indicators:
            if indicator in story_text:
                print(f"   ⚠️ Found JSON indicator: {indicator}")
                found_json = True
        
        if found_json:
            print(f"   ❌ RAW JSON DETECTED in opening story!")
            print(f"   Story text preview: {story_text[:500]}...")
        else:
            print(f"   ✅ No JSON artifacts in opening story")
        
        # Take screenshot of initial state
        self.take_screenshot(page, "json_bug_01_opening_story")
        
        # Continue the story for multiple turns
        responses = [
            "I look at my father with confusion. 'Join you? What are you talking about, Dad?'",
            "I take a step back, shocked. 'You're... you're a Viltrumite? All this time?'",
            "I feel anger rising. 'How could you lie to me? To Mom? Was any of it real?'",
            "I clench my fists. 'I won't help you conquer Earth. These are my people!'",
            "'You're not my father anymore. You're just another alien invader.'"
        ]
        
        for i, response in enumerate(responses, 1):
            print(f"\n6.{i} Turn {i}: Sending response...")
            
            # Type response
            input_area = page.locator("#user-input")
            input_area.fill(response)
            
            # Submit
            submit_button = page.locator("button#submit-action")
            submit_button.click()
            
            # Wait for AI response
            print(f"   Waiting for AI response...")
            page.wait_for_timeout(5000)
            
            # Check latest story entry for JSON
            story_entries = page.locator(".story-entry").all()
            if story_entries:
                latest_entry = story_entries[-1]
                entry_text = latest_entry.inner_text()
                
                # Check for JSON artifacts
                found_json_in_turn = False
                for indicator in json_indicators:
                    if indicator in entry_text:
                        print(f"   ⚠️ Turn {i}: Found JSON indicator: {indicator}")
                        found_json_in_turn = True
                
                if found_json_in_turn:
                    print(f"   ❌ Turn {i}: RAW JSON DETECTED!")
                    print(f"   Entry preview: {entry_text[:500]}...")
                    
                    # Check specific Scene pattern
                    if "Scene #" in entry_text and "{" in entry_text:
                        print(f"   🎯 EXACT BUG PATTERN FOUND: 'Scene #X: {{' pattern detected!")
                        # Take screenshot of the bug
                        self.take_screenshot(page, f"json_bug_turn_{i}_detected")
                else:
                    print(f"   ✅ Turn {i}: No JSON artifacts")
            
            # Small delay between turns
            page.wait_for_timeout(1000)
        
        # Final check of entire story
        print("\n7. Final check of complete story...")
        final_story = page.locator("#story-area").inner_text()
        
        # Count JSON occurrences
        json_count = final_story.count('"narrative":')
        scene_count = final_story.count('Scene #')
        brace_count = final_story.count('{')
        
        print(f"   JSON artifact counts:")
        print(f"   - 'narrative' occurrences: {json_count}")
        print(f"   - 'Scene #' occurrences: {scene_count}")
        print(f"   - '{{' occurrences: {brace_count}")
        
        if json_count > 0 or (scene_count > 0 and brace_count > scene_count):
            print(f"\n   ❌ JSON BUG CONFIRMED: Raw JSON is being displayed in the UI")
            print(f"\n   📋 INSTRUCTIONS: Check server logs for JSON_BUG entries to trace the issue")
            self.take_screenshot(page, "json_bug_final_state")
            return False
        else:
            print(f"\n   ✅ No JSON bugs detected in this test run")
            return True


if __name__ == "__main__":
    test = JSONBugReproductionTest()
    test.execute()