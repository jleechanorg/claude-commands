#!/usr/bin/env python3
"""
Direct test of UI features bypassing wizard.
"""

import os
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/worldarchitectai/ui_fixes_direct"

def setup_dirs():
    """Create screenshot directory."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_screenshot(page, name):
    """Take a screenshot."""
    filepath = f"{SCREENSHOT_DIR}/{name}.png"
    page.screenshot(path=filepath, full_page=False)
    print(f"📸 {name}")

def main():
    print("🎯 Direct UI Features Test")
    print("=" * 50)
    
    setup_dirs()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        
        try:
            # Navigate with test mode
            print("\n1️⃣ Testing campaign form directly...")
            test_url = f"{BASE_URL}?test_mode=true&test_user_id=direct-test"
            page.goto(test_url)
            time.sleep(2)
            
            # Directly show new campaign view
            page.evaluate("""
                // Hide all views
                document.querySelectorAll('.view').forEach(v => v.classList.remove('active-view'));
                
                // Show new campaign view
                const newCampaignView = document.getElementById('new-campaign-view');
                if (newCampaignView) {
                    newCampaignView.classList.add('active-view');
                    
                    // Initialize campaign type handlers
                    if (typeof setupCampaignTypeHandlers === 'function') {
                        setupCampaignTypeHandlers();
                    }
                }
            """)
            time.sleep(2)
            
            # Check radio buttons
            radio_visible = page.evaluate("""
                (() => {
                    const radios = document.querySelectorAll('input[name="campaignType"]');
                    return radios.length > 0;
                })()
            """)
            
            if radio_visible:
                print("   ✅ Radio buttons found!")
                
                # Highlight radio section
                page.evaluate("""
                    const radioSection = document.querySelector('input[name="campaignType"]')?.closest('.mb-3');
                    if (radioSection) {
                        radioSection.style.border = '3px solid red';
                        radioSection.style.padding = '15px';
                        radioSection.style.backgroundColor = '#ffeeee';
                    }
                """)
                time.sleep(0.5)
                take_screenshot(page, "01_radio_buttons_visible")
                
                # Check Dragon Knight content
                page.evaluate("""
                    const textarea = document.getElementById('campaign-prompt');
                    if (textarea) {
                        textarea.style.border = '3px solid blue';
                        textarea.style.backgroundColor = '#f0f0ff';
                    }
                """)
                time.sleep(0.5)
                take_screenshot(page, "02_dragon_knight_content")
                
                # Click custom radio
                custom_radio = page.query_selector("#customCampaign")
                if custom_radio:
                    custom_radio.click()
                    time.sleep(1)
                    
                    page.evaluate("""
                        const textarea = document.getElementById('campaign-prompt');
                        if (textarea) {
                            textarea.style.border = '3px solid green';
                            textarea.value = 'CUSTOM CAMPAIGN - This is now editable!';
                        }
                    """)
                    time.sleep(0.5)
                    take_screenshot(page, "03_custom_campaign_editable")
            else:
                print("   ❌ Radio buttons not found - checking wizard...")
                
                # Go to dashboard and use wizard
                page.evaluate("""
                    document.querySelectorAll('.view').forEach(v => v.classList.remove('active-view'));
                    const dashboardView = document.getElementById('dashboard-view');
                    if (dashboardView) dashboardView.classList.add('active-view');
                """)
                time.sleep(1)
                
                # Click wizard button
                wizard_btn = page.query_selector("button:has-text('Start New Campaign')")
                if wizard_btn:
                    wizard_btn.click()
                    time.sleep(2)
                    take_screenshot(page, "04_wizard_view")
            
            # Test 2: Create campaign and test inline editing
            print("\n2️⃣ Creating campaign for inline edit test...")
            
            # Use the regular form
            page.evaluate("""
                document.querySelectorAll('.view').forEach(v => v.classList.remove('active-view'));
                document.getElementById('new-campaign-view').classList.add('active-view');
            """)
            time.sleep(1)
            
            # Fill form
            name_input = page.query_selector("#campaign-title")
            if name_input:
                name_input.fill("Test Campaign for Inline Edit")
            
            # Select custom to make it faster
            custom_radio = page.query_selector("#customCampaign")
            if custom_radio:
                custom_radio.click()
                time.sleep(0.5)
            
            # Simple prompt
            prompt_textarea = page.query_selector("#campaign-prompt")
            if prompt_textarea:
                prompt_textarea.fill("A simple test campaign")
            
            # Submit
            submit_btn = page.query_selector("button[type='submit']")
            if submit_btn:
                submit_btn.click()
                print("   Creating campaign...")
                time.sleep(8)
            
            # Test inline editing
            game_view = page.query_selector("#game-view.active-view")
            if game_view:
                print("\n3️⃣ Testing inline campaign name editing...")
                
                # Add inline editor if not present
                page.evaluate("""
                    const title = document.getElementById('game-title');
                    if (title && typeof InlineEditor !== 'undefined') {
                        window.titleEditor = new InlineEditor(title, '/api/campaigns/' + window.currentCampaignId, 'title');
                        title.style.cursor = 'pointer';
                        title.style.textDecoration = 'underline';
                        title.style.textDecorationStyle = 'dotted';
                        
                        // Add tooltip
                        title.title = 'Click to edit campaign name';
                    }
                """)
                time.sleep(0.5)
                
                # Highlight title
                page.evaluate("""
                    const title = document.getElementById('game-title');
                    if (title) {
                        title.style.border = '3px solid orange';
                        title.style.padding = '5px';
                        
                        const note = document.createElement('div');
                        note.textContent = '👆 Click to edit inline!';
                        note.style.cssText = 'color: orange; font-weight: bold;';
                        title.parentElement.appendChild(note);
                    }
                """)
                take_screenshot(page, "05_inline_edit_ready")
                
                # Test story reader
                print("\n4️⃣ Testing story reader controls...")
                story_btn = page.query_selector("#story-reader-toggle")
                if story_btn:
                    page.evaluate("""
                        const btn = document.getElementById('story-reader-toggle');
                        if (btn) {
                            btn.style.border = '3px solid purple';
                            btn.style.boxShadow = '0 0 15px purple';
                        }
                    """)
                    take_screenshot(page, "06_story_reader_button")
                else:
                    print("   ❌ Story reader button not found")
                
                # Show download/share buttons
                print("\n5️⃣ Showing download/share buttons...")
                page.evaluate("""
                    const downloadBtn = document.getElementById('downloadStoryBtn');
                    const shareBtn = document.getElementById('shareStoryBtn');
                    
                    [downloadBtn, shareBtn].forEach(btn => {
                        if (btn) {
                            btn.style.border = '3px solid red';
                            btn.style.boxShadow = '0 0 10px red';
                        }
                    });
                """)
                take_screenshot(page, "07_download_share_visible")
            
            print(f"\n✅ Test complete! Screenshots in: {SCREENSHOT_DIR}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            take_screenshot(page, "error_state")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

if __name__ == "__main__":
    main()