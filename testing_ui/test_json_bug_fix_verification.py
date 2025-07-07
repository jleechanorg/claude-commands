#!/usr/bin/env python3
"""
Browser test to verify the JSON display bug fix works end-to-end.
This test simulates the exact user scenario and verifies the fix.
"""

import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'mvp_site'))

try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    print("❌ Playwright not installed. Cannot run browser tests.")
    sys.exit(1)

def test_json_bug_fix():
    """Test that the JSON bug fix works in the browser."""
    
    print("🧪 Testing JSON bug fix in browser...")
    
    # Start the test server
    print("🔄 Starting test server...")
    server_process = subprocess.Popen([
        sys.executable, 'mvp_site/main.py', 'serve'
    ], env={**os.environ, 'TESTING': 'true', 'PORT': '6006'}, 
    cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to the app
            page.goto("http://localhost:6006")
            
            # Wait for page to load
            page.wait_for_selector("#userInputEl", timeout=10000)
            
            print("✅ Page loaded successfully")
            
            # Create a new campaign with the problematic prompt
            page.click("button:has-text('New Campaign')")
            page.wait_for_selector("#campaignPromptEl", timeout=5000)
            
            # Use the exact prompt from the bug report
            campaign_prompt = "Play as Nolan's son. He's offering you to join him. TV show invincible"
            page.fill("#campaignPromptEl", campaign_prompt)
            page.click("button:has-text('Start Campaign')")
            
            print("✅ Campaign created")
            
            # Wait for the story content to appear
            page.wait_for_selector("#story-content", timeout=15000)
            
            # Continue the story a few times to trigger the bug scenario
            for i in range(3):
                print(f"🔄 Story continuation {i+1}/3...")
                
                # Wait for input to be enabled
                page.wait_for_function("() => !document.getElementById('userInputEl').disabled", timeout=10000)
                
                # Enter a response
                user_input = f"I consider Omni-Man's offer carefully, turn {i+1}."
                page.fill("#userInputEl", user_input)
                page.click("button:has-text('Submit')")
                
                # Wait for AI response
                page.wait_for_function("() => !document.getElementById('userInputEl').disabled", timeout=30000)
                
                # Check story content
                story_content = page.inner_text("#story-content")
                
                # Critical test: Check for JSON artifacts
                json_artifacts = [
                    '"narrative":',
                    '"god_mode_response":',
                    '"entities_mentioned":',
                    '{"narrative"',
                    'Scene #2: {"',
                    'Scene #3: {"',
                    'Scene #4: {"'
                ]
                
                found_artifacts = []
                for artifact in json_artifacts:
                    if artifact in story_content:
                        found_artifacts.append(artifact)
                
                if found_artifacts:
                    print(f"❌ JSON artifacts found in story content: {found_artifacts}")
                    print(f"Story content sample: {story_content[:500]}...")
                    browser.close()
                    return False
                
                print(f"✅ Turn {i+1} clean - no JSON artifacts detected")
            
            # Take a screenshot for verification
            screenshot_dir = Path("/tmp/worldarchitectai/browser")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshot_dir / "json_bug_fix_verification.png"
            page.screenshot(path=str(screenshot_path))
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Get final story content for analysis
            final_story = page.inner_text("#story-content")
            
            # Verify we have substantial content
            if len(final_story) < 100:
                print(f"❌ Story content too short: {len(final_story)} characters")
                browser.close()
                return False
            
            # Verify Scene numbering is working correctly
            scene_count = final_story.count("Scene #")
            if scene_count < 2:
                print(f"❌ Expected multiple scenes, found {scene_count}")
                browser.close()
                return False
            
            print(f"✅ Found {scene_count} scenes in story")
            print(f"✅ Story content length: {len(final_story)} characters")
            
            browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False
    finally:
        # Stop the server
        server_process.terminate()
        server_process.wait()
        print("🔄 Test server stopped")

def main():
    """Main test execution."""
    print("=" * 60)
    print("🧪 JSON Bug Fix Verification Test")
    print("=" * 60)
    
    # Check if we're in the right environment
    if not Path("mvp_site/main.py").exists():
        print("❌ Must run from project root directory")
        sys.exit(1)
    
    # Run the test
    success = test_json_bug_fix()
    
    print("=" * 60)
    if success:
        print("🎉 JSON bug fix verification PASSED!")
        print("✅ No JSON artifacts found in browser display")
        print("✅ Scene numbering works correctly")
        print("✅ Story content is properly formatted")
    else:
        print("💥 JSON bug fix verification FAILED!")
        print("❌ JSON artifacts still present or other issues detected")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()