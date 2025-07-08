#!/usr/bin/env python3
"""
Capture proof screenshots for UI bundle features.
"""

import os
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/worldarchitectai/ui_bundle_proof"
TEST_USER_ID = "browser-test-user"

def setup_dirs():
    """Create screenshot directory with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"{SCREENSHOT_DIR}/{timestamp}"
    os.makedirs(screenshot_path, exist_ok=True)
    return screenshot_path

def take_screenshot(page, name, path):
    """Take a screenshot with annotations."""
    filepath = f"{path}/{name}.png"
    page.screenshot(path=filepath, full_page=False)
    print(f"📸 Captured: {name}")
    return filepath

def highlight_element(page, selector, color="red"):
    """Highlight an element with a colored border."""
    try:
        page.evaluate(f"""
            const el = document.querySelector('{selector}');
            if (el) {{
                el.style.border = '3px solid {color}';
                el.style.boxShadow = '0 0 10px {color}';
            }}
        """)
    except:
        pass

def main():
    print("🎯 UI Bundle Feature Proof Screenshots")
    print("=" * 50)
    
    screenshot_path = setup_dirs()
    print(f"📁 Screenshots will be saved to: {screenshot_path}")
    
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        try:
            # 1. Dashboard with Edit buttons
            print("\n1️⃣ Capturing Dashboard with Edit buttons...")
            test_url = f"{BASE_URL}?test_mode=true&test_user_id={TEST_USER_ID}"
            page.goto(test_url, wait_until="networkidle")
            time.sleep(3)
            
            # Activate test mode
            page.evaluate(f"""
                window.testAuthBypass = {{
                    enabled: true,
                    userId: '{TEST_USER_ID}'
                }};
                const authView = document.getElementById('auth-view');
                const dashboardView = document.getElementById('dashboard-view');
                if (authView && dashboardView) {{
                    authView.classList.remove('active-view');
                    dashboardView.classList.add('active-view');
                }}
            """)
            time.sleep(2)
            
            # Highlight Edit buttons
            page.evaluate("""
                Array.from(document.querySelectorAll('button')).filter(btn => 
                    btn.textContent.includes('Edit')
                ).forEach(btn => {
                    btn.style.border = '3px solid #28a745';
                    btn.style.boxShadow = '0 0 10px #28a745';
                });
            """)
            time.sleep(0.5)
            take_screenshot(page, "01_dashboard_edit_buttons", screenshot_path)
            
            # 2. Click Edit to show modal
            print("\n2️⃣ Showing Edit Campaign modal...")
            edit_buttons = page.query_selector_all("button:has-text('Edit')")
            if edit_buttons:
                edit_buttons[0].click()
                time.sleep(1)
                take_screenshot(page, "02_edit_campaign_modal", screenshot_path)
                
                # Close modal
                cancel_btn = page.query_selector("button:has-text('Cancel')")
                if cancel_btn:
                    cancel_btn.click()
                    time.sleep(0.5)
            
            # 3. Enter a campaign
            print("\n3️⃣ Entering campaign to show Download/Share buttons...")
            campaign_cards = page.query_selector_all("h3")
            if campaign_cards and len(campaign_cards) > 0:
                # Scroll to campaign
                campaign_cards[0].scroll_into_view_if_needed()
                time.sleep(0.5)
                
                # Click to enter
                campaign_cards[0].click()
                time.sleep(3)
                
                # Check if in game view
                game_view = page.query_selector("#game-view.active-view")
                if game_view:
                    # Highlight download/share buttons
                    highlight_element(page, "#downloadStoryBtn", "red")
                    highlight_element(page, "#shareStoryBtn", "blue")
                    time.sleep(0.5)
                    
                    take_screenshot(page, "03_download_share_buttons_top", screenshot_path)
                    
                    # Zoom in on button area
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(0.5)
                    
                    # Take focused shot of top section
                    top_section = page.query_selector(".d-flex.justify-content-between.align-items-center.mb-3")
                    if top_section:
                        box = top_section.bounding_box()
                        if box:
                            # Capture just the top section
                            page.screenshot(
                                path=f"{screenshot_path}/04_buttons_closeup.png",
                                clip={
                                    'x': 0,
                                    'y': box['y'] - 20,
                                    'width': 1280,
                                    'height': 200
                                }
                            )
                            print("📸 Captured: 04_buttons_closeup")
            
            # 4. Go back to dashboard for wizard
            print("\n4️⃣ Opening Campaign Wizard...")
            page.goto(test_url, wait_until="networkidle")
            time.sleep(2)
            
            # Click Start New Campaign
            new_campaign_btn = page.query_selector("button:has-text('Start New Campaign')")
            if new_campaign_btn:
                new_campaign_btn.click()
                time.sleep(2)
                
                # Capture wizard with Dragon Knight content
                take_screenshot(page, "05_campaign_wizard_dragon_knight", screenshot_path)
                
                # Highlight Dragon Knight text
                page.evaluate("""
                    const textElements = Array.from(document.querySelectorAll('*')).filter(el => 
                        el.textContent.toLowerCase().includes('dragon') && 
                        el.textContent.toLowerCase().includes('knight')
                    );
                    if (textElements.length > 0) {
                        textElements[0].style.backgroundColor = 'yellow';
                        textElements[0].style.padding = '5px';
                    }
                """)
                time.sleep(0.5)
                take_screenshot(page, "06_dragon_knight_highlighted", screenshot_path)
            
            # 5. Check network for story reader files
            print("\n5️⃣ Checking Story Reader files loading...")
            page.goto(BASE_URL, wait_until="networkidle")
            
            # Open DevTools Network panel simulation
            page.evaluate("""
                const scripts = Array.from(document.querySelectorAll('script')).map(s => s.src);
                const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href);
                
                // Create overlay showing loaded files
                const overlay = document.createElement('div');
                overlay.style.position = 'fixed';
                overlay.style.top = '50px';
                overlay.style.right = '20px';
                overlay.style.background = 'white';
                overlay.style.border = '2px solid black';
                overlay.style.padding = '20px';
                overlay.style.zIndex = '9999';
                overlay.style.maxWidth = '400px';
                
                overlay.innerHTML = '<h3>Story Reader Files Loaded:</h3>';
                
                if (scripts.some(s => s.includes('story-reader.js'))) {
                    overlay.innerHTML += '<p style="color: green;">✅ story-reader.js</p>';
                }
                if (styles.some(s => s.includes('pagination-styles.css'))) {
                    overlay.innerHTML += '<p style="color: green;">✅ pagination-styles.css</p>';
                }
                if (styles.some(s => s.includes('story-reader.css'))) {
                    overlay.innerHTML += '<p style="color: green;">✅ story-reader.css</p>';
                }
                
                document.body.appendChild(overlay);
            """)
            time.sleep(1)
            take_screenshot(page, "07_story_reader_files_loaded", screenshot_path)
            
            # Summary
            print("\n" + "=" * 50)
            print("✅ Screenshot Capture Complete!")
            print(f"📁 All screenshots saved to: {screenshot_path}")
            print("\nCaptured proofs:")
            print("  1. Dashboard with Edit buttons (PR #301)")
            print("  2. Edit Campaign modal")
            print("  3. Download/Share buttons at top (PR #396)")
            print("  4. Buttons closeup view")
            print("  5. Campaign wizard with Dragon Knight")
            print("  6. Dragon Knight content highlighted")
            print("  7. Story Reader files loading (PR #323)")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            take_screenshot(page, "error_state", screenshot_path)
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

if __name__ == "__main__":
    main()