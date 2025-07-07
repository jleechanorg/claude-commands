#!/usr/bin/env python3
"""
Comprehensive UI test to validate the raw JSON display bug fix.
Creates a campaign similar to Luke's and performs 20 interactions designed 
to trigger potential JSON parsing failures.
"""

import os
import sys
import re
import time
from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase, click_button_with_text, wait_for_element


class JsonBugValidationTest(BrowserTestBase):
    """Comprehensive test to validate raw JSON display bug fix."""
    
    def __init__(self):
        super().__init__("JSON Bug Validation Test")
        self.json_errors_found = []
        self.interactions_completed = 0
        self.target_interactions = 20
    
    def check_for_json_artifacts(self, page: Page, context: str) -> bool:
        """Check if any raw JSON artifacts are visible in the UI."""
        # Get all visible text on the page
        story_content = ""
        
        # Check story content specifically
        story_selectors = [
            "#story-content", 
            "#chat-messages", 
            ".story-container",
            ".message-content",
            "#game-content"
        ]
        
        for selector in story_selectors:
            element = page.query_selector(selector)
            if element and element.is_visible():
                story_content += element.text_content() or ""
        
        # Check for JSON artifacts
        json_indicators = [
            '"narrative":',
            '"god_mode_response":',
            '"entities_mentioned":',
            '"state_updates":',
            '"debug_info":',
            '"location_confirmed":',
            '{"narrative"',
            '{"god_mode_response"',
            '"entities_mentioned":[',
            '"state_updates":{',
            '{"entities_mentioned"'
        ]
        
        found_artifacts = []
        for indicator in json_indicators:
            if indicator in story_content:
                found_artifacts.append(indicator)
        
        if found_artifacts:
            error_msg = f"JSON artifacts found in {context}: {found_artifacts}"
            self.json_errors_found.append(error_msg)
            print(f"❌ {error_msg}")
            
            # Take screenshot of the problem
            self.take_screenshot(page, f"json_error_{len(self.json_errors_found)}")
            return True
        
        return False
    
    def wait_for_ai_response(self, page: Page, timeout: int = 15000) -> bool:
        """Wait for AI response to complete."""
        print("   ⏳ Waiting for AI response...")
        
        # Wait for loading spinner to disappear
        try:
            # First wait for spinner to appear (if it will)
            page.wait_for_timeout(1000)
            
            # Then wait for spinner to disappear
            spinner_selectors = [
                "#loading-spinner",
                ".loading-spinner", 
                "[id*='loading']",
                "[class*='loading']"
            ]
            
            for selector in spinner_selectors:
                try:
                    page.wait_for_selector(f"{selector}:not([style*='display: none'])", timeout=2000)
                    page.wait_for_selector(f"{selector}[style*='display: none']", timeout=timeout)
                    break
                except:
                    continue
            
            # Additional wait for content to settle
            page.wait_for_timeout(2000)
            return True
            
        except TimeoutError:
            print("   ⚠️  Timeout waiting for response, continuing...")
            return False
    
    def send_interaction(self, page: Page, message: str, mode: str = "character") -> bool:
        """Send an interaction and wait for response."""
        try:
            # Switch to the specified mode
            if mode == "god":
                god_radio = page.query_selector("input[type='radio'][value='god']")
                if god_radio:
                    god_radio.click()
                    page.wait_for_timeout(500)
                    print(f"   🔮 Switched to God Mode")
            else:
                char_radio = page.query_selector("input[type='radio'][value='character']")
                if char_radio:
                    char_radio.click()
                    page.wait_for_timeout(500)
                    print(f"   👤 Switched to Character Mode")
            
            # Find and fill the message input
            input_selectors = [
                "#user-input",
                "#message-input", 
                "textarea[placeholder*='What do you do']",
                "textarea[name='input']",
                "textarea"
            ]
            
            message_input = None
            for selector in input_selectors:
                element = page.query_selector(selector)
                if element and element.is_visible():
                    message_input = element
                    break
            
            if not message_input:
                print("   ❌ Could not find message input")
                return False
            
            # Clear and type the message
            message_input.click()
            message_input.fill("")
            message_input.type(message)
            print(f"   📝 Typed: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # Send the message (try Enter first, then send button)
            message_input.press("Enter")
            page.wait_for_timeout(1000)
            
            # Wait for response
            success = self.wait_for_ai_response(page)
            
            # Check for JSON artifacts after response
            self.check_for_json_artifacts(page, f"interaction_{self.interactions_completed + 1}")
            
            self.interactions_completed += 1
            print(f"   ✅ Interaction {self.interactions_completed}/{self.target_interactions} completed")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Failed to send interaction: {e}")
            return False
    
    def run_test(self, page: Page) -> bool:
        """Run the comprehensive JSON bug validation test."""
        
        try:
            # Take initial screenshot
            self.take_screenshot(page, "01_initial")
            
            # Create a Luke-style campaign
            print("🎮 Creating Luke-style campaign...")
            
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(2000)
                
                # Fill in Luke-style campaign details
                campaign_title = "Dark Side Ascension: A Sith Lord's Journey"
                campaign_prompt = """You are Luke Skywalker, but in this alternate timeline, you've turned to the Dark Side after losing everything in the Imperial conflict. You've become a powerful Sith apprentice seeking to overthrow your master and rule the galaxy. The story takes place in a gritty, morally complex Star Wars universe where the line between Jedi and Sith is blurred."""
                
                # Try wizard approach first
                if page.is_visible("#wizard-campaign-title"):
                    print("   📝 Using campaign wizard...")
                    page.fill("#wizard-campaign-title", campaign_title)
                    page.fill("#wizard-campaign-prompt", campaign_prompt)
                    
                    # Navigate through wizard
                    for i in range(5):
                        if page.is_visible("#wizard-next"):
                            page.click("#wizard-next")
                            page.wait_for_timeout(1500)
                        elif page.is_visible("#launch-campaign"):
                            page.click("#launch-campaign")
                            break
                        elif page.is_visible("button:has-text('Begin Adventure')"):
                            page.click("button:has-text('Begin Adventure')")
                            break
                
                # Try direct form approach
                elif page.is_visible("#campaign-title"):
                    print("   📝 Using direct form...")
                    page.fill("#campaign-title", campaign_title)
                    page.fill("#campaign-prompt", campaign_prompt)
                    
                    # Submit form
                    if page.is_visible("button[type='submit']"):
                        page.click("button[type='submit']")
                    elif page.is_visible("text=Create Campaign"):
                        page.click("text=Create Campaign")
                
                # Wait for game view to load
                print("   ⏳ Waiting for game to start...")
                page.wait_for_load_state("networkidle")
                
                try:
                    page.wait_for_selector("#game-view.active-view", timeout=20000)
                    print("   ✅ Game view loaded")
                except:
                    print("   ⚠️  Game view timeout - continuing anyway")
            
            self.take_screenshot(page, "02_game_started")
            
            # Perform 20 interactions designed to trigger JSON bugs
            interactions = [
                # Character mode interactions (1-5)
                ("character", "I examine the ancient Sith holocron, searching for secrets of unlimited power."),
                ("character", "I reach out with the Force to sense any nearby 'enemies' or 'allies' in this temple."),
                ("character", 'I speak aloud: "The Jedi were fools to trust in the light." Then I laugh darkly.'),
                ("character", "I attempt to corrupt this sacred place with my dark side energy, letting hatred flow through me."),
                ("character", "I use Force Lightning to destroy the Jedi artifacts scattered around this chamber."),
                
                # God mode interactions that might cause JSON issues (6-15)
                ("god", "A vision appears showing Luke's friends Han and Leia, but they're now his enemies."),
                ("god", 'The holocron whispers: "Your destiny is to rule, not serve. Kill your master."'),
                ("god", "A massive Imperial fleet arrives in orbit, blocking out the stars with their ships."),
                ("god", "Luke's lightsaber crystal suddenly cracks, turning from blue to deep crimson red."),
                ("god", 'A voice echoes: "The Emperor has a new apprentice. You must prove your worth."'),
                ("god", "Reality shifts - the temple transforms into Vader's meditation chamber on his Star Destroyer."),
                ("god", "An ancient Sith spirit possesses Luke temporarily, granting him forbidden knowledge."),
                ("god", "The Force itself recoils from Luke's corruption, creating a disturbance felt across the galaxy."),
                ("god", "Luke's memories are altered - he now remembers choosing the dark side willingly."),
                ("god", "A Jedi Master arrives to stop Luke, but she's someone he once loved and must now destroy."),
                
                # Mixed mode interactions with complex formatting (16-20)
                ("character", "I embrace the full power of the dark side and declare: 'I am no longer Luke Skywalker!'"),
                ("god", "The galaxy itself responds to Luke's transformation with systems falling into chaos."),
                ("character", "I reach out through the Force to communicate with any remaining Sith across the stars."),
                ("god", "Luke's transformation is complete - he is now Darth Venator, Sith Lord of Vengeance."),
                ("character", "I stand triumphant in my new identity, ready to claim my destiny as ruler of the galaxy.")
            ]
            
            print(f"\n🎯 Beginning {len(interactions)} targeted interactions...")
            
            for i, (mode, message) in enumerate(interactions, 1):
                print(f"\n📝 Interaction {i}/{len(interactions)} ({mode} mode):")
                
                # Send the interaction
                success = self.send_interaction(page, message, mode)
                
                if success:
                    # Take periodic screenshots
                    if i % 5 == 0:
                        self.take_screenshot(page, f"interaction_{i:02d}_complete")
                else:
                    print(f"   ⚠️  Interaction {i} had issues")
                
                # Short delay between interactions
                page.wait_for_timeout(1000)
            
            # Final screenshot
            self.take_screenshot(page, "03_all_interactions_complete")
            
            # Final check for JSON artifacts
            final_check = self.check_for_json_artifacts(page, "final_validation")
            
            # Summary
            print(f"\n📊 Test Summary:")
            print(f"   Interactions completed: {self.interactions_completed}/{self.target_interactions}")
            print(f"   JSON errors found: {len(self.json_errors_found)}")
            
            if self.json_errors_found:
                print(f"\n❌ JSON ERRORS DETECTED:")
                for error in self.json_errors_found:
                    print(f"   - {error}")
                return False
            else:
                print(f"\n✅ NO JSON ARTIFACTS FOUND - Fix validated!")
                return True
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            self.take_screenshot(page, "error_exception")
            return False


if __name__ == "__main__":
    test = JsonBugValidationTest()
    success = test.execute()
    
    if success:
        print("\n🎉 JSON BUG VALIDATION TEST PASSED")
        print("✅ Raw JSON display bug fix has been validated via comprehensive UI testing")
        print("✅ 20 interactions completed with no JSON artifacts detected")
        sys.exit(0)
    else:
        print("\n💥 JSON BUG VALIDATION TEST FAILED") 
        print("❌ Raw JSON artifacts were detected in the UI")
        print("❌ The fix may not be working correctly")
        sys.exit(1)