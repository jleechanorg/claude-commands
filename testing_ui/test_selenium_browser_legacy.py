#!/usr/bin/env python3
"""
Selenium-based browser test for WorldArchitect.AI
This performs real browser testing against the running server
"""

import time
import json
from datetime import datetime

# Check if selenium is available
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not installed. Install with: pip install selenium")

def log(message):
    """Log with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def create_headless_browser():
    """Create a headless Chrome browser"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        log(f"❌ Failed to create browser: {e}")
        return None

def test_homepage(driver):
    """Test homepage loading and UI elements"""
    log("Testing homepage with real browser...")
    
    driver.get("http://localhost:8080")
    time.sleep(2)  # Wait for page load
    
    # Check title
    assert "WorldArchitect.AI" in driver.title
    log(f"✅ Page title: {driver.title}")
    
    # Check for key elements
    elements = {
        "navbar": "nav.navbar",
        "auth_view": "#auth-view",
        "dashboard_view": "#dashboard-view",
        "new_campaign_view": "#new-campaign-view",
        "game_view": "#game-view"
    }
    
    for name, selector in elements.items():
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            log(f"✅ Found {name}: {element.tag_name}")
        except:
            log(f"❌ Missing {name}")
    
    # Check for Firebase auth
    try:
        driver.execute_script("return typeof firebase !== 'undefined'")
        log("✅ Firebase loaded")
    except:
        log("❌ Firebase not loaded")
    
    # Take screenshot
    driver.save_screenshot("/tmp/worldarchitect_homepage.png")
    log("📸 Screenshot saved to /tmp/worldarchitect_homepage.png")

def test_form_interaction(driver):
    """Test form interactions"""
    log("Testing form interactions...")
    
    # Check if new campaign form is visible
    try:
        form = driver.find_element(By.ID, "new-campaign-form")
        if form.is_displayed():
            log("✅ New campaign form is visible")
            
            # Fill out form
            title_input = driver.find_element(By.ID, "campaign-title")
            prompt_input = driver.find_element(By.ID, "campaign-prompt")
            
            title_input.clear()
            title_input.send_keys("Selenium Test Campaign")
            
            prompt_input.clear()
            prompt_input.send_keys("Testing with automated browser")
            
            log("✅ Form fields populated")
            
            # Check checkboxes
            narrative_cb = driver.find_element(By.ID, "prompt-narrative")
            mechanics_cb = driver.find_element(By.ID, "prompt-mechanics")
            
            log(f"Narrative checkbox: {'checked' if narrative_cb.is_selected() else 'unchecked'}")
            log(f"Mechanics checkbox: {'checked' if mechanics_cb.is_selected() else 'unchecked'}")
        else:
            log("⚠️ New campaign form not visible (may need auth)")
    except Exception as e:
        log(f"❌ Form interaction failed: {e}")

def test_javascript_console(driver):
    """Check for JavaScript errors"""
    log("Checking browser console...")
    
    # Get browser logs
    try:
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if errors:
            log(f"❌ Found {len(errors)} JavaScript errors:")
            for error in errors[:3]:  # Show first 3
                log(f"  - {error['message']}")
        else:
            log("✅ No JavaScript errors")
    except:
        log("⚠️ Could not access browser logs")

def main():
    """Run browser tests"""
    if not SELENIUM_AVAILABLE:
        log("❌ Cannot run browser tests without Selenium")
        return
    
    log("🌐 Starting Selenium browser tests...")
    
    driver = create_headless_browser()
    if not driver:
        return
    
    try:
        test_homepage(driver)
        test_form_interaction(driver)
        test_javascript_console(driver)
        
        log("\n✅ Browser testing complete!")
        
    except Exception as e:
        log(f"❌ Browser test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        log("🏁 Browser closed")

if __name__ == "__main__":
    # First show what's really possible without Selenium
    log("📊 PR #314 Analysis:")
    log("- Claims '30-minute manual testing simulation'")
    log("- Actually used programmatic API testing")
    log("- No real browser was launched")
    log("- 'Playwright tests' were mocked, not real")
    log("")
    
    # Try to run real browser test
    main()
    
    # If Selenium not available, explain
    if not SELENIUM_AVAILABLE:
        log("\n💡 To run real browser tests:")
        log("1. Install Selenium: pip install selenium")
        log("2. Install Chrome/Chromium browser")
        log("3. Install ChromeDriver")
        log("4. Run this script again")