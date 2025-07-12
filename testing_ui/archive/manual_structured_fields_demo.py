#!/usr/bin/env python3
"""
Manual test to capture screenshots of structured fields with real data.
"""
import time
from playwright.sync_api import sync_playwright

def capture_structured_fields():
    """Manually capture structured fields screenshots"""
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode so we can see what's happening
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("🌐 Navigate to WorldArchitect.AI...")
            # Navigate with test mode
            page.goto("http://localhost:6006?test_mode=true&test_user_id=demo-user")
            page.wait_for_load_state('networkidle')
            
            print("⏸️  Please manually:")
            print("1. Create a new campaign or select an existing one")
            print("2. Send a message in character mode")
            print("3. Switch to god mode and send another message")
            print("4. Press Enter when you see all structured fields displayed...")
            input()
            
            # Take screenshots
            print("📸 Capturing structured fields...")
            
            # Full page screenshot
            page.screenshot(path="/tmp/structured_fields_demo_full.png", full_page=True)
            print("✅ Saved: /tmp/structured_fields_demo_full.png")
            
            # Try to capture individual fields
            fields = {
                'resources': '.resources, .resource-updates, .alert-warning:has-text("Resources")',
                'session_header': '.session-header, [data-field="session_header"]',
                'planning_block': '.planning-block, .choice-container',
                'dice_rolls': '.dice-rolls, [data-field="dice_rolls"]',
                'narrative': '.narrative-text, #story-content p:last-child'
            }
            
            for field_name, selectors in fields.items():
                for selector in selectors.split(', '):
                    try:
                        element = page.locator(selector).first
                        if element.is_visible():
                            element.screenshot(path=f"/tmp/structured_field_{field_name}.png")
                            print(f"✅ Captured {field_name}: /tmp/structured_field_{field_name}.png")
                            break
                    except:
                        continue
            
            print("\n✅ Screenshots captured successfully!")
            print("Check /tmp/ directory for the images.")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            print("\n🔚 Closing browser...")
            browser.close()

if __name__ == "__main__":
    capture_structured_fields()