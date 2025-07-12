#!/usr/bin/env python3
"""
Core browser test for all structured response fields from game_state_instruction.md.
Tests and captures screenshots of all 10 fields that can be sent by the LLM.
"""

import os
import sys
import time
from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase, SCREENSHOT_DIR


class StructuredFieldsTest(BrowserTestBase):
    """Test all 10 structured response fields through browser automation."""
    
    def __init__(self):
        super().__init__("Structured Fields Browser Test")
    
    def run_test(self, page: Page) -> bool:
        """Test all structured fields from game_state_instruction.md."""
        
        # All 10 fields from game_state_instruction.md
        REQUIRED_FIELDS = [
            'session_header',
            'narrative', 
            'planning_block',
            'dice_rolls',
            'resources',
            'god_mode_response',
            'entities_mentioned',
            'location_confirmed',
            'state_updates',
            'debug_info'
        ]
        
        try:
            # Take initial screenshot
            self.take_screenshot(page, "01_homepage")
            
            # Wait a bit for campaigns to load
            page.wait_for_timeout(3000)
            
            # Try to use the first available campaign if any exist
            campaign_items = page.locator(".list-group-item[data-campaign-id]")
            if campaign_items.count() > 0:
                print("📌 Found existing campaign, using it...")
                campaign_items.first.click()
                page.wait_for_timeout(3000)
            else:
                # Create new campaign only if none exist
                print("🎮 Creating new test campaign for structured fields...")
                test_campaign_name = f"Structured Fields Test {int(time.time())}"
                
                if not self._create_test_campaign(page, test_campaign_name):
                    print("❌ Failed to create test campaign")
                    return False
            
            # Skip old campaign selection logic - commented out for now
            """
            # Try to use existing campaign first
            print("🔍 Looking for existing test campaign...")
            
            # Check for campaigns
            page.wait_for_timeout(2000)  # Wait for campaigns to load
            
            # Debug: Log the campaigns list HTML
            try:
                campaigns_list = page.locator("#campaign-list")
                if campaigns_list.count() > 0:
                    list_html = campaigns_list.inner_html()
                    print(f"📋 Campaign list HTML (first 500 chars): {list_html[:500]}...")
            except:
                print("⚠️ Could not get campaign list HTML")
            
            # Look for campaign items - based on actual DOM structure
            campaign_selectors = [
                ".list-group-item[data-campaign-id]",  # Primary selector with campaign ID
                ".list-group-item.list-group-item-action",  # Fallback
                "[data-campaign-id]"  # Any element with campaign ID
            ]
            
            found_campaign = False
            for selector in campaign_selectors:
                elements = page.locator(selector)
                count = elements.count()
                if count > 0:
                    print(f"✅ Found {count} campaigns with selector: {selector}")
                    
                    # Get first campaign element
                    campaign_elem = elements.first
                    
                    # Try to extract campaign ID or text
                    try:
                        campaign_text = campaign_elem.text_content()
                        print(f"   Campaign text: {campaign_text}")
                        
                        # Check for data-campaign-id attribute
                        campaign_id = campaign_elem.get_attribute("data-campaign-id")
                        if campaign_id:
                            print(f"   Campaign ID: {campaign_id}")
                        else:
                            print("   ⚠️ No data-campaign-id attribute found")
                    except Exception as e:
                        print(f"   ⚠️ Error extracting campaign info: {e}")
                    
                    # Click the campaign
                    print("🖱️ Clicking campaign...")
                    campaign_elem.click()
                    found_campaign = True
                    print("⏳ Waiting for campaign to load...")
                    page.wait_for_timeout(5000)  # Give time for the campaign to load
                    
                    # Take screenshot after clicking
                    self.take_screenshot(page, "02_after_campaign_click")
                    
                    # Check current URL
                    current_url = page.url
                    print(f"📍 Current URL after click: {current_url}")
                    break
            
            if not found_campaign:
                # Create new campaign only if none found
                print("🎮 Creating new test campaign for structured fields...")
                test_campaign_name = f"Structured Fields Test {int(time.time())}"
                
                if not self._create_test_campaign(page, test_campaign_name):
                    print("❌ Failed to create test campaign")
                    return False
            else:
                # If we found a mock campaign, create a real one instead
                if "browser_test_campaign" in str(campaign_id):
                    print("📌 Found mock campaign, creating real campaign instead...")
                    test_campaign_name = f"Structured Fields Test {int(time.time())}"
                    
                    if not self._create_test_campaign(page, test_campaign_name):
                        print("❌ Failed to create test campaign")
                        return False
            """
            
            # Wait for game view
            try:
                page.wait_for_selector("#game-view.active-view", timeout=20000)
                print("✅ Game view loaded")
            except:
                # Try alternate game view check
                if page.is_visible("#game-view"):
                    print("✅ Game view visible (not necessarily active)")
                else:
                    print("❌ Game view not found")
                    return False
            
            self.take_screenshot(page, "02_game_view")
            
            # Test 1: Character mode - all standard fields
            print("\n📝 Test 1: Character mode with standard fields")
            field_results = self._test_character_mode_fields(page)
            
            # Test 2: God mode - special god_mode_response field
            print("\n🔮 Test 2: God mode response field")
            god_mode_result = self._test_god_mode_response(page)
            field_results['god_mode_response'] = god_mode_result
            
            # Test 3: Debug mode - verify debug_info visibility
            print("\n🐛 Test 3: Debug mode fields")
            debug_result = self._test_debug_mode(page)
            field_results['debug_info'] = field_results.get('debug_info', False) or debug_result
            
            # Final summary
            print("\n" + "="*60)
            print("Field Validation Summary:")
            print("="*60)
            
            all_passed = True
            for field in REQUIRED_FIELDS:
                status = "✅" if field_results.get(field, False) else "❌"
                print(f"{status} {field}")
                if not field_results.get(field, False):
                    all_passed = False
            
            # Take final screenshot
            self.take_screenshot(page, "10_final_summary", full_page=True)
            
            return all_passed
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error_state")
            return False
    
    def _create_test_campaign(self, page: Page, campaign_name: str) -> bool:
        """Create a test campaign through the wizard."""
        try:
            # Try multiple selectors for new campaign button
            new_campaign_selectors = [
                "text='New Campaign'",
                "button:has-text('New Campaign')",
                "#new-campaign-btn",
                ".new-campaign-button"
            ]
            
            clicked = False
            for selector in new_campaign_selectors:
                if page.is_visible(selector):
                    page.click(selector)
                    clicked = True
                    break
            
            if not clicked:
                print("❌ Could not find New Campaign button")
                return False
            
            page.wait_for_timeout(2000)
            
            # Check if we're in wizard view
            if page.is_visible("#new-campaign-view.active-view"):
                print("✅ In new campaign wizard")
                
                # Fill campaign details - try multiple selectors
                title_selectors = ["#wizard-campaign-title", "#campaign-title", "input[name='title']"]
                for selector in title_selectors:
                    if page.is_visible(selector):
                        page.fill(selector, campaign_name)
                        break
                
                prompt_selectors = ["#wizard-campaign-prompt", "#campaign-prompt", "textarea[name='prompt']"]
                for selector in prompt_selectors:
                    if page.is_visible(selector):
                        page.fill(selector, "Fantasy adventure to test all structured fields")
                        break
                
                # Navigate wizard - try different approaches
                for i in range(5):
                    # Check for various next/continue buttons
                    next_selectors = [
                        "#wizard-next",
                        "button:has-text('Next')",
                        "button:has-text('Continue')",
                        "#next-button"
                    ]
                    
                    for selector in next_selectors:
                        if page.is_visible(selector):
                            page.click(selector)
                            page.wait_for_timeout(1500)
                            break
                    
                    # Check for launch/begin buttons
                    launch_selectors = [
                        "#launch-campaign",
                        "button:has-text('Begin Adventure')",
                        "button:has-text('Launch Campaign')",
                        "button:has-text('Start Campaign')"
                    ]
                    
                    for selector in launch_selectors:
                        if page.is_visible(selector):
                            page.click(selector)
                            print("✅ Launched campaign")
                            page.wait_for_timeout(3000)
                            return True
                
                # Alternative: direct create button
                if page.is_visible("button:has-text('Create Campaign')"):
                    page.click("button:has-text('Create Campaign')")
                    page.wait_for_timeout(3000)
                    return True
                
            return False
        except Exception as e:
            print(f"❌ Error creating campaign: {e}")
            return False
    
    def _test_character_mode_fields(self, page: Page) -> dict:
        """Test standard character mode fields."""
        results = {}
        
        # Send action to trigger response
        action_input = page.locator("#player-action, #user-input, textarea[name='user-input']").first
        send_button = page.locator("#send-action, button:has-text('Send')").first
        
        if action_input.count() > 0 and send_button.count() > 0:
            action_input.fill("I attack the goblin with my sword and cast shield spell!")
            send_button.click()
            
            # Wait for response
            print("⏳ Waiting for AI response...")
            page.wait_for_timeout(10000)
            
            self.take_screenshot(page, "03_character_response")
            
            # Check each field
            field_selectors = {
                'session_header': ['.session-header', '[data-field="session_header"]'],
                'narrative': ['.narrative-text', '[data-field="narrative"]', '#story-content p:last-child'],
                'planning_block': ['.planning-block', '[data-field="planning_block"]'],
                'dice_rolls': ['.dice-rolls', '[data-field="dice_rolls"]'],
                'resources': ['.resources', '[data-field="resources"]', '.resource-updates'],
                'entities_mentioned': ['.entities-mentioned', '[data-field="entities_mentioned"]'],
                'location_confirmed': ['.location-confirmed', '[data-field="location_confirmed"]'],
                'state_updates': ['.state-updates', '[data-field="state_updates"]'],
                'debug_info': ['.debug-info', '[data-field="debug_info"]']
            }
            
            for field, selectors in field_selectors.items():
                found = False
                for selector in selectors:
                    if page.locator(selector).count() > 0:
                        found = True
                        print(f"✅ Found {field}: {selector}")
                        # Take element screenshot
                        element = page.locator(selector).first
                        if element:
                            element.screenshot(path=f"{SCREENSHOT_DIR}/{field}_element.png")
                            print(f"   📸 Element screenshot: {field}_element.png")
                        break
                results[field] = found
                if not found:
                    print(f"❌ Missing {field}")
        
        return results
    
    def _test_god_mode_response(self, page: Page) -> bool:
        """Test god mode response field."""
        action_input = page.locator("#player-action, #user-input, textarea[name='user-input']").first
        send_button = page.locator("#send-action, button:has-text('Send')").first
        
        if action_input.count() > 0 and send_button.count() > 0:
            # Send god mode command
            action_input.fill("GOD MODE: Create a magical artifact in the room")
            send_button.click()
            
            print("⏳ Waiting for god mode response...")
            page.wait_for_timeout(10000)
            
            self.take_screenshot(page, "05_god_mode_response")
            
            # Check for god_mode_response field
            god_selectors = [
                '.god-mode-response',
                '[data-field="god_mode_response"]',
                '.field-god_mode_response'
            ]
            
            for selector in god_selectors:
                if page.locator(selector).count() > 0:
                    print(f"✅ Found god_mode_response: {selector}")
                    element = page.locator(selector).first
                    if element:
                        element.screenshot(path=f"{SCREENSHOT_DIR}/god_mode_response_element.png")
                        print(f"   📸 Element screenshot: god_mode_response_element.png")
                    return True
            
            # Check if it's in debug info
            debug_content = page.locator(".debug-info, [data-field='debug_info']").first
            if debug_content and "god_mode_response" in debug_content.text_content():
                print("✅ Found god_mode_response in debug info")
                return True
        
        return False
    
    def _test_debug_mode(self, page: Page) -> bool:
        """Test debug info visibility."""
        # Toggle debug mode if available
        debug_toggle = page.locator("#debug-toggle, .debug-toggle, button:has-text('Debug')")
        if debug_toggle.count() > 0:
            debug_toggle.first.click()
            page.wait_for_timeout(1000)
            print("✅ Toggled debug mode")
        
        # Check for debug info
        debug_selectors = ['.debug-info', '[data-field="debug_info"]', '#debug-panel']
        for selector in debug_selectors:
            if page.locator(selector).count() > 0:
                print(f"✅ Found debug_info: {selector}")
                element = page.locator(selector).first
                if element:
                    element.screenshot(path=f"{SCREENSHOT_DIR}/debug_info_element.png")
                    print(f"   📸 Element screenshot: debug_info_element.png")
                return True
        
        return False


if __name__ == "__main__":
    # Set mock mode - both services must be mocked for browser tests
    os.environ['USE_MOCK_GEMINI'] = 'true'
    os.environ['USE_MOCK_FIREBASE'] = 'true'
    
    test = StructuredFieldsTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - All structured fields validated")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - Some fields missing")
        sys.exit(1)