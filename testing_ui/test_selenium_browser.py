#!/usr/bin/env python3
"""
Real browser test using Selenium to demonstrate actual browser automation.
This will use a headless Chrome browser to interact with WorldArchitect.AI.
"""

import os
import sys
import time
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8086"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "selenium_screenshots")

def test_with_selenium():
    """Test using Selenium with headless Chrome."""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        print("❌ Selenium not installed. Installing...")
        os.system("pip install selenium")
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
    
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,720")
    
    # Create browser
    print("🌐 Launching headless Chrome browser...")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Browser launched successfully")
    except Exception as e:
        print(f"❌ Failed to launch browser: {e}")
        print("Trying with chromium-driver...")
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        driver = webdriver.Chrome(options=chrome_options)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Navigate to the site
        print(f"🔗 Navigating to {BASE_URL}")
        driver.get(BASE_URL)
        time.sleep(2)  # Wait for initial load
        
        # Take initial screenshot
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"01_initial_{timestamp}.png"))
        print("📸 Screenshot 1: Initial page captured")
        
        # Get browser info as proof
        browser_info = driver.execute_script("""
            return {
                url: window.location.href,
                title: document.title,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                cookieEnabled: navigator.cookieEnabled,
                language: navigator.language,
                timestamp: new Date().toISOString()
            }
        """)
        
        print("\n🔍 Real Browser Information:")
        print(f"  URL: {browser_info['url']}")
        print(f"  Title: {browser_info['title']}")
        print(f"  Viewport: {browser_info['viewport']['width']}x{browser_info['viewport']['height']}")
        print(f"  User Agent: {browser_info['userAgent']}")
        print(f"  Platform: {browser_info['platform']}")
        print(f"  Cookies: {browser_info['cookieEnabled']}")
        print(f"  Language: {browser_info['language']}")
        
        # Check page content
        page_source = driver.page_source
        print(f"\n📄 Page loaded, HTML size: {len(page_source)} bytes")
        
        # Try to find and interact with elements
        try:
            # Look for the campaign button
            new_campaign_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'New Campaign')]"))
            )
            print("✅ Found 'New Campaign' button")
            
            # Click it
            driver.execute_script("arguments[0].scrollIntoView(true);", new_campaign_btn)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"02_before_click_{timestamp}.png"))
            
            new_campaign_btn.click()
            print("🖱️ Clicked 'New Campaign' button")
            time.sleep(2)
            
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"03_after_click_{timestamp}.png"))
            print("📸 Screenshot 2-3: Before and after clicking")
            
        except Exception as e:
            print(f"⚠️ Could not find New Campaign button: {e}")
            
        # Try to find campaign creation elements
        try:
            # Look for campaign prompt textarea
            prompt_textarea = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "campaignPrompt"))
            )
            print("✅ Found campaign prompt textarea")
            
            # Type in it
            test_prompt = "A brave knight must save a kingdom from an ancient dragon"
            prompt_textarea.send_keys(test_prompt)
            print(f"⌨️ Typed: '{test_prompt}'")
            
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"04_typed_prompt_{timestamp}.png"))
            print("📸 Screenshot 4: Typed campaign prompt")
            
        except Exception as e:
            print(f"⚠️ Could not find campaign prompt: {e}")
        
        # Execute JavaScript to prove browser control
        js_result = driver.execute_script("""
            // Modify the page to prove we have control
            const proof = document.createElement('div');
            proof.id = 'selenium-proof';
            proof.style.cssText = 'position: fixed; top: 10px; right: 10px; background: red; color: white; padding: 10px; z-index: 9999;';
            proof.textContent = 'Selenium Control Active - ' + new Date().toLocaleTimeString();
            document.body.appendChild(proof);
            
            // Return some page data
            return {
                elementsCount: document.querySelectorAll('*').length,
                buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent),
                inputs: Array.from(document.querySelectorAll('input, textarea')).map(i => ({
                    id: i.id,
                    type: i.type,
                    value: i.value
                }))
            };
        """)
        
        print(f"\n🎯 JavaScript Execution Proof:")
        print(f"  Total elements on page: {js_result['elementsCount']}")
        print(f"  Buttons found: {js_result['buttons']}")
        print(f"  Input fields: {len(js_result['inputs'])}")
        
        # Final screenshot with proof element
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"05_final_with_proof_{timestamp}.png"))
        print("📸 Screenshot 5: Final state with JavaScript proof")
        
    finally:
        # Close browser
        driver.quit()
        print("\n✅ Browser closed successfully")
        
        # List screenshots
        print(f"\n📁 Screenshots saved to: {SCREENSHOT_DIR}")
        for file in sorted(os.listdir(SCREENSHOT_DIR)):
            if file.endswith('.png'):
                file_path = os.path.join(SCREENSHOT_DIR, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size:,} bytes)")

def main():
    """Main entry point."""
    print("=" * 70)
    print("🔍 Selenium Real Browser Test")
    print("This uses a real headless Chrome browser via Selenium")
    print("=" * 70)
    
    # Check if test server is running
    import requests
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Test server is running on {BASE_URL}")
    except:
        print(f"❌ Test server not running on {BASE_URL}")
        return
    
    test_with_selenium()

if __name__ == "__main__":
    main()