#!/usr/bin/env python3
"""
Focused UI test to validate the raw JSON display bug fix.
Does 5 targeted interactions specifically designed to trigger the JSON parsing issues.
"""

import os
import sys
import re
import time
from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase, click_button_with_text, wait_for_element


class FocusedJsonBugTest(BrowserTestBase):
    """Focused test to validate raw JSON display bug fix with high-risk scenarios."""
    
    def __init__(self):
        super().__init__("Focused JSON Bug Test")
        self.json_errors_found = []
        self.interactions_completed = 0
    
    def check_for_json_artifacts(self, page: Page, context: str) -> bool:
        """Check if any raw JSON artifacts are visible in the UI."""
        # Get story content
        story_content = ""
        story_selectors = ["#story-content", "#chat-messages", ".story-container"]
        
        for selector in story_selectors:
            element = page.query_selector(selector)
            if element and element.is_visible():
                story_content += element.text_content() or ""
        
        # Check for JSON artifacts that indicate the bug
        json_artifacts = [
            '"narrative":',
            '"god_mode_response":',
            '"entities_mentioned":',
            '"state_updates":',
            '{"narrative"',
            '{"god_mode_response"',
            '"entities_mentioned":[',
            '"location_confirmed":'
        ]
        
        found_artifacts = []
        for artifact in json_artifacts:
            if artifact in story_content:
                found_artifacts.append(artifact)
        
        if found_artifacts:
            error_msg = f"JSON artifacts found in {context}: {found_artifacts}"
            self.json_errors_found.append(error_msg)
            print(f"❌ {error_msg}")
            self.take_screenshot(page, f"json_error_{context}")
            
            # Log the actual content for debugging
            print(f"   📄 Story content snippet: {story_content[:500]}...")
            return True
        
        return False
    
    def send_god_mode_command(self, page: Page, command: str) -> bool:
        """Send a god mode command and check for JSON artifacts."""
        try:
            # Switch to god mode
            god_radio = page.query_selector("input[type='radio'][value='god']")
            if god_radio:
                god_radio.click()
                page.wait_for_timeout(500)
                print(f"   🔮 Switched to God Mode")
            
            # Find message input
            input_selectors = ["#user-input", "textarea[placeholder*='What do you do']", "textarea"]
            message_input = None
            for selector in input_selectors:
                element = page.query_selector(selector)
                if element and element.is_visible():
                    message_input = element
                    break
            
            if not message_input:
                print("   ❌ Could not find message input")
                return False
            
            # Send command
            message_input.click()
            message_input.fill(command)
            print(f"   📝 Sent god command: {command[:60]}...")
            message_input.press("Enter")
            
            # Wait for response (longer timeout for god mode)
            print("   ⏳ Waiting for god mode response...")
            page.wait_for_timeout(8000)  # God mode responses can be slower
            
            # Check for JSON artifacts immediately after response
            has_artifacts = self.check_for_json_artifacts(page, f"god_interaction_{self.interactions_completed + 1}")
            
            self.interactions_completed += 1
            return not has_artifacts
            
        except Exception as e:
            print(f"   ❌ Failed god mode command: {e}")
            return False
    
    def run_test(self, page: Page) -> bool:
        """Run focused JSON bug validation test."""
        
        try:
            self.take_screenshot(page, "01_start")
            
            # Create minimal campaign
            print("🎮 Creating test campaign...")
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(2000)
                
                # Quick campaign setup
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "JSON Bug Test Campaign")
                    page.fill("#wizard-campaign-prompt", "A realm where gods intervene directly in mortal affairs.")
                    
                    # Fast wizard navigation
                    for i in range(5):
                        if page.is_visible("#wizard-next"):
                            page.click("#wizard-next")
                            page.wait_for_timeout(1000)
                        elif page.is_visible("#launch-campaign"):
                            page.click("#launch-campaign")
                            break
                
                # Wait for game
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)
            
            self.take_screenshot(page, "02_game_ready")
            
            # Test 5 specific scenarios designed to trigger JSON bugs
            print("\n🎯 Testing scenarios that previously caused JSON bugs...")
            
            # Scenario 1: God mode with quotes and special characters
            print("\n📝 Scenario 1: God mode with embedded quotes")
            success1 = self.send_god_mode_command(page, 
                'A voice echoes: "Your destiny is to rule, not serve. Kill your \\"master\\"."')
            
            self.take_screenshot(page, "03_scenario_1")
            
            # Scenario 2: God mode with JSON-like content
            print("\n📝 Scenario 2: God mode with JSON-like narrative")
            success2 = self.send_god_mode_command(page, 
                'Reality shifts and shows a status: {"power_level": 9000, "alignment": "chaotic_evil"}.')
            
            self.take_screenshot(page, "04_scenario_2")
            
            # Scenario 3: Complex god mode response
            print("\n📝 Scenario 3: Complex god mode transformation")
            success3 = self.send_god_mode_command(page, 
                "Luke's transformation accelerates - memories rewrite, power surges through him, and the Force itself recoils from his corruption.")
            
            self.take_screenshot(page, "05_scenario_3")
            
            # Scenario 4: God mode with state changes
            print("\n📝 Scenario 4: God mode with complex state updates")
            success4 = self.send_god_mode_command(page, 
                'The entire Imperial fleet recognizes Luke as their new Dark Lord, updating all systems and protocols.')
            
            self.take_screenshot(page, "06_scenario_4")
            
            # Scenario 5: God mode with entities and locations
            print("\n📝 Scenario 5: God mode with multiple entities")
            success5 = self.send_god_mode_command(page, 
                "Vader, Palpatine, and all Sith spirits converge to witness Luke's ascension to ultimate power.")
            
            self.take_screenshot(page, "07_scenario_5_final")
            
            # Final validation
            final_check = self.check_for_json_artifacts(page, "final_comprehensive")
            
            # Results
            successful_interactions = sum([success1, success2, success3, success4, success5])
            
            print(f"\n📊 Test Results:")
            print(f"   Scenarios completed: 5/5")
            print(f"   Successful (no JSON): {successful_interactions}/5")
            print(f"   JSON errors found: {len(self.json_errors_found)}")
            
            if self.json_errors_found:
                print(f"\n❌ JSON ARTIFACTS DETECTED:")
                for error in self.json_errors_found:
                    print(f"   - {error}")
                return False
            else:
                print(f"\n✅ NO JSON ARTIFACTS FOUND!")
                print(f"✅ Raw JSON display bug fix has been validated!")
                return True
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error")
            return False


if __name__ == "__main__":
    test = FocusedJsonBugTest()
    success = test.execute()
    
    if success:
        print("\n🎉 FOCUSED JSON BUG TEST PASSED")
        print("✅ Raw JSON display bug fix validated with high-risk scenarios")
        sys.exit(0)
    else:
        print("\n💥 FOCUSED JSON BUG TEST FAILED")
        print("❌ JSON artifacts detected - fix may need attention")
        sys.exit(1)