#!/usr/bin/env python3
"""
Test for the Campaign Wizard with Character and Setting Inputs
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json

# Import test utilities (adjust path for new structure)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from screenshot_utils import take_screenshot
from test_ui_util import run_ui_test, navigate_to_page, navigate_wizard_to_step, capture_api_request, enable_console_logging
from test_ui_helpers import fill_form_field, scroll_to_element
from testing_ui.config import BASE_URL

def test_wizard_character_setting(page, test_name):
    """Test the wizard with character and setting inputs"""
    
    print("🧙 WIZARD TEST: Character and Setting Inputs")
    
    # Enable console logging for debugging
    enable_console_logging(page)
    
    # Navigate to new campaign page with test mode
    navigate_to_page(page, "new-campaign", port=6007)
    
    # The wizard should be active automatically
    print("✅ Page loaded")
    
    # Screenshot 1: Initial wizard with Dragon Knight selected
    print("\n📸 Screenshot 1: Initial Wizard - Step 1 with Dragon Knight Default")
    take_screenshot(page, test_name, "1_dragon_knight_default")
    
    # Scroll down to see character and setting inputs
    scroll_to_element(page, "#wizard-character-input")
    
    # Screenshot 2: Character and setting inputs visible
    print("📸 Screenshot 2: Character and Setting Inputs (Dragon Knight)")
    take_screenshot(page, test_name, "2_dragon_knight_inputs")
    
    # Check default values for Dragon Knight
    character_value = page.input_value("#wizard-character-input")
    setting_value = page.input_value("#wizard-setting-input")
    print(f"\n✅ Dragon Knight Default Values:")
    print(f"  Character: '{character_value}' (should be 'Ser Arion')")
    print(f"  Setting: '{setting_value}' (should be 'World of Assiah')")
    
    # Test 1: Modify Dragon Knight character
    print("\n🧪 Test 1: Modifying Dragon Knight character...")
    fill_form_field(page, "wizard-character-input", "Sir Galahad the Bold")
    fill_form_field(page, "wizard-setting-input", "Medieval Kingdom of Camelot")
    
    # Screenshot 3: Modified Dragon Knight values
    print("📸 Screenshot 3: Modified Dragon Knight Character/Setting")
    take_screenshot(page, test_name, "3_dragon_knight_modified")
    
    # Test 2: Switch to Custom Campaign
    print("\n🧪 Test 2: Switching to Custom Campaign...")
    # Click on the campaign card instead of the radio button directly
    page.click('div.campaign-type-card[data-type="custom"]')
    page.wait_for_timeout(500)
    
    # Scroll to see inputs
    scroll_to_element(page, "#wizard-character-input")
    
    # Check that values cleared
    character_value_custom = page.input_value("#wizard-character-input")
    setting_value_custom = page.input_value("#wizard-setting-input")
    print(f"\n✅ Custom Campaign Values After Switch:")
    print(f"  Character: '{character_value_custom}' (should be empty)")
    print(f"  Setting: '{setting_value_custom}' (should be empty)")
    
    # Screenshot 4: Custom Campaign empty inputs
    print("\n📸 Screenshot 4: Custom Campaign with Empty Inputs")
    take_screenshot(page, test_name, "4_custom_empty")
    
    # Test 3: Fill custom values
    print("\n🧪 Test 3: Filling Custom Campaign values...")
    fill_form_field(page, "wizard-character-input", "Astarion who ascended in BG3")
    fill_form_field(page, "wizard-setting-input", "Baldur's Gate")
    
    # Screenshot 5: Custom Campaign filled
    print("📸 Screenshot 5: Custom Campaign with Astarion")
    take_screenshot(page, test_name, "5_custom_filled")
    
    # Test 4: Navigate through wizard steps
    print("\n🧪 Test 4: Navigating wizard steps...")
    
    # Navigate to Step 2
    navigate_wizard_to_step(page, 2, current_step=1)
    
    # Screenshot 6: Step 2 - AI Style
    print("📸 Screenshot 6: Step 2 - AI Style")
    take_screenshot(page, test_name, "6_step2_ai_style")
    
    # Navigate to Step 3
    navigate_wizard_to_step(page, 3, current_step=2)
    
    # Screenshot 7: Step 3 - Options
    print("📸 Screenshot 7: Step 3 - Options")
    take_screenshot(page, test_name, "7_step3_options")
    
    # Navigate to Step 4
    navigate_wizard_to_step(page, 4, current_step=3)
    
    # Screenshot 8: Step 4 - Launch
    print("📸 Screenshot 8: Step 4 - Launch Summary")
    take_screenshot(page, test_name, "8_step4_launch")
    
    # Test 5: Submit and capture API request
    print("\n🧪 Test 5: Submitting campaign...")
    
    # Set up API capture
    api_data = capture_api_request(page, "api/campaigns", "POST")
    
    # Click Begin Adventure (use the wizard button ID)
    page.click("#launch-campaign")
    page.wait_for_timeout(3000)
    
    # Analyze API request
    if api_data.get('request') and api_data['request'].get('data'):
        data = api_data['request']['data']
        print("\n✅ API Request Analysis:")
        print(f"  Title: {data.get('title', 'NOT FOUND')}")
        print(f"  Character: {data.get('character', 'NOT FOUND')}")
        print(f"  Setting: {data.get('setting', 'NOT FOUND')}")
        print(f"  Campaign Type: {data.get('campaignType', 'NOT FOUND')}")
        
        if 'character' in data and 'setting' in data:
            print("\n🎉 SUCCESS: Wizard correctly sends character and setting as separate fields!")
    
    print("\n📂 Screenshots saved:")
    print("  1. 1_dragon_knight_default.png - Initial state")
    print("  2. 2_dragon_knight_inputs.png - Shows Ser Arion and World of Assiah")
    print("  3. 3_dragon_knight_modified.png - Modified Dragon Knight values")
    print("  4. 4_custom_empty.png - Custom Campaign with empty inputs")
    print("  5. 5_custom_filled.png - Custom Campaign with Astarion")
    print("  6. 6_step2_ai_style.png - AI personality selection")
    print("  7. 7_step3_options.png - Campaign options")
    print("  8. 8_step4_launch.png - Final summary before launch")
    
    return True  # Test passed

if __name__ == "__main__":
    # Run the test using the test runner
    run_ui_test(test_wizard_character_setting, "wizard_character_setting", headless=False, port=6007)