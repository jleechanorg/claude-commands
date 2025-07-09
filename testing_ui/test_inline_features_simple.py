#!/usr/bin/env python3
"""
Simple test to verify inline editing and story reader features are accessible.
"""

import time
import sys
import os
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        try:
            # Navigate to test mode
            print("1. Loading application...")
            page.goto("http://localhost:6006?test_mode=true")
            page.wait_for_load_state("networkidle")
            
            # Anonymous login
            print("2. Logging in anonymously...")
            page.wait_for_selector("#auth-view.active-view")
            page.click("button:has-text('Continue without login')")
            
            # Wait for dashboard
            print("3. Navigating to dashboard...")
            page.wait_for_selector("#dashboard-view.active-view", timeout=10000)
            
            # Check for campaigns or create one
            campaigns = page.query_selector_all(".campaign-card")
            if campaigns:
                print(f"4. Found {len(campaigns)} campaigns, clicking first one...")
                page.click(".campaign-card:first-child")
            else:
                print("4. No campaigns found, creating new one...")
                page.click("button:has-text('Create New Campaign')")
                page.wait_for_selector("#new-campaign-view.active-view")
                page.fill("#campaign-title", "Test Campaign")
                page.fill("#campaign-prompt", "Test campaign for feature verification.")
                page.click("button:has-text('Create Campaign')")
            
            # Wait for game view
            print("5. Waiting for game view...")
            page.wait_for_selector("#game-view.active-view", timeout=30000)
            time.sleep(2)  # Let everything load
            
            # Check inline editing
            print("\n=== INLINE EDITING CHECK ===")
            
            # Get title element info
            title_info = page.evaluate("""
                () => {
                    const title = document.getElementById('game-title');
                    if (!title) return { found: false };
                    
                    return {
                        found: true,
                        text: title.innerText,
                        hasInlineClass: title.classList.contains('inline-editable'),
                        hasClickHandler: title.onclick !== null,
                        classNames: Array.from(title.classList).join(', '),
                        inlineEditorDefined: typeof window.InlineEditor !== 'undefined'
                    };
                }
            """)
            
            print(f"Title element found: {title_info.get('found')}")
            if title_info.get('found'):
                print(f"  Text: '{title_info.get('text')}'")
                print(f"  Has inline-editable class: {title_info.get('hasInlineClass')}")
                print(f"  Has click handler: {title_info.get('hasClickHandler')}")
                print(f"  Classes: {title_info.get('classNames')}")
                print(f"  InlineEditor defined: {title_info.get('inlineEditorDefined')}")
            
            # Try clicking title
            print("\nClicking title to test inline editing...")
            page.click("#game-title")
            time.sleep(1)
            
            # Check if edit mode activated
            edit_active = page.query_selector(".inline-edit-container") is not None
            print(f"Edit mode activated: {edit_active}")
            
            if edit_active:
                # Try to edit
                page.fill(".inline-edit-input", "Updated Title")
                page.click(".inline-edit-save")
                time.sleep(1)
                new_title = page.query_selector("#game-title").inner_text()
                print(f"Title updated to: '{new_title}'")
            
            # Check story reader controls
            print("\n=== STORY READER CONTROLS CHECK ===")
            
            controls_info = page.evaluate("""
                () => {
                    const readBtn = document.getElementById('readStoryBtn');
                    const pauseBtn = document.getElementById('pauseStoryBtn');
                    const controls = document.querySelector('.story-reader-controls-inline');
                    
                    return {
                        readBtnFound: readBtn !== null,
                        readBtnVisible: readBtn ? window.getComputedStyle(readBtn).display !== 'none' : false,
                        readBtnText: readBtn ? readBtn.innerText : null,
                        pauseBtnFound: pauseBtn !== null,
                        pauseBtnVisible: pauseBtn ? window.getComputedStyle(pauseBtn).display !== 'none' : false,
                        pauseBtnText: pauseBtn ? pauseBtn.innerText : null,
                        controlsFound: controls !== null,
                        controlsVisible: controls ? window.getComputedStyle(controls).display !== 'none' : false,
                        storyReaderDefined: typeof window.StoryReader !== 'undefined'
                    };
                }
            """)
            
            print(f"Read button found: {controls_info.get('readBtnFound')}")
            print(f"Read button visible: {controls_info.get('readBtnVisible')}")
            print(f"Read button text: '{controls_info.get('readBtnText')}'")
            print(f"Pause button found: {controls_info.get('pauseBtnFound')}")
            print(f"Pause button visible: {controls_info.get('pauseBtnVisible')}")
            print(f"Controls container found: {controls_info.get('controlsFound')}")
            print(f"Controls container visible: {controls_info.get('controlsVisible')}")
            print(f"StoryReader class defined: {controls_info.get('storyReaderDefined')}")
            
            # Take screenshot
            screenshot_path = "/tmp/inline_features_check.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"\nScreenshot saved to: {screenshot_path}")
            
            # Print console messages
            if console_messages:
                print("\n=== CONSOLE MESSAGES ===")
                for msg in console_messages[-20:]:  # Last 20 messages
                    print(msg)
            
            print("\n✅ Test completed successfully")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Emergency screenshot
            try:
                page.screenshot(path="/tmp/inline_features_error.png")
                print("Error screenshot saved to: /tmp/inline_features_error.png")
            except:
                pass
                
        finally:
            browser.close()

if __name__ == "__main__":
    print("Inline Features Verification Test")
    print("=" * 50)
    run_test()