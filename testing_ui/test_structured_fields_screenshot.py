#!/usr/bin/env python3
"""
Quick browser test to capture screenshot of structured fields in action.
"""
import os
import time
from playwright.sync_api import sync_playwright

# Configuration
BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/structured_fields_demo"

def capture_structured_fields_demo():
    """Capture a demo screenshot of structured fields"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to the demo campaign
            print("Navigating to app...")
            page.goto(f"{BASE_URL}/?test_mode=true&test_user_id=test-demo")
            page.wait_for_load_state('networkidle')
            
            # Click start new campaign
            print("Starting new campaign...")
            page.click('text="Start New Campaign"')
            page.wait_for_selector('#wizard-step-1:not(.hidden)', timeout=5000)
            
            # Fill campaign details
            page.fill('#campaign-title', 'Structured Fields Demo')
            page.fill('#campaign-description', 'Demonstrating dice rolls, resources, and planning blocks')
            
            # Click next
            page.click('button:has-text("Next: Character Creation")')
            page.wait_for_selector('#wizard-step-2:not(.hidden)', timeout=5000)
            
            # Fill character details
            page.fill('#character-name', 'Demo Hero')
            page.fill('#character-class', 'Fighter')
            page.fill('#character-race', 'Human')
            page.fill('#character-background', 'Soldier with combat experience')
            
            # Create campaign
            print("Creating campaign...")
            page.click('button:has-text("Create Campaign")')
            
            # Wait for campaign to load
            page.wait_for_selector('.story-container', timeout=30000)
            time.sleep(3)
            
            # Submit an interaction
            print("Submitting interaction...")
            page.fill('#user-input', 'I attack the goblin with my sword!')
            page.click('button#send-button')
            
            # Wait for response
            print("Waiting for AI response...")
            page.wait_for_selector('.ai-message', timeout=60000)
            time.sleep(5)
            
            # Take screenshot
            screenshot_path = f"{SCREENSHOT_DIR}/structured_fields_example.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot saved: {screenshot_path}")
            
            # Check for structured fields
            if page.query_selector('.dice-rolls'):
                print("✅ Dice rolls section found!")
            if page.query_selector('.resources'):
                print("✅ Resources section found!")
            if page.query_selector('.planning-block'):
                print("✅ Planning block found!")
                
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    capture_structured_fields_demo()