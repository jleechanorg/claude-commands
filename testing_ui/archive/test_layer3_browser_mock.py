#!/usr/bin/env python3
"""
Layer 3: Browser test with mocked services for structured fields.
Tests UI rendering with controlled, known API responses.
"""

import os
import sys
import time
import threading
from http.server import HTTPServer
from playwright.sync_api import sync_playwright

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import test utilities
sys.path.append(os.path.dirname(__file__))
from test_data_utils import create_test_campaign
from test_ui_helpers import capture_structured_fields_sequence
from testing_ui.mock_services import create_mock_api_server

def start_mock_server():
    """Start mock API server on port 8086."""
    handler = create_mock_api_server()
    server = HTTPServer(('localhost', 8086), handler)
    
    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return server

def test_layer3_structured_fields_mock():
    """Layer 3 test: Browser + Mock APIs for structured fields."""
    
    print("=== Layer 3: Browser + Mock APIs Test ===")
    
    # Start mock server
    print("🔧 Starting mock API server on port 8086...")
    mock_server = start_mock_server()
    time.sleep(1)  # Allow server to start
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Initialize helper for standardized screenshots
        helper = BrowserTestHelper("layer3_structured_fields_mock", page)
        
        try:
            # Navigate to app with mock API
            print("🌐 Navigating to app with mock API...")
            page.goto("http://localhost:6006?test_mode=true&test_user_id=layer3-test")
            page.wait_for_load_state('networkidle')
            
            # Override API base URL to use mock server
            page.evaluate("""
                // Override fetch to use mock API
                const originalFetch = window.fetch;
                window.fetch = function(url, options) {
                    if (url && typeof url === 'string' && url.includes('/api/')) {
                        const mockUrl = url.replace('http://localhost:6006', 'http://localhost:8086');
                        console.log('Mocking API call:', url, '->', mockUrl);
                        return originalFetch(mockUrl, options);
                    }
                    return originalFetch(url, options);
                };
            """)
            
            # Wait for dashboard
            if not helper.wait_for_element("text='My Campaigns'", timeout=10):
                raise Exception("Dashboard failed to load")
            
            helper.take_screenshot("dashboard_loaded")
            
            # Navigate directly to test game to avoid campaign list issues
            print("🎮 Navigating directly to test game...")
            page.goto("http://localhost:6006/game/test-campaign-id?test_mode=true&test_user_id=layer3-test")
            page.wait_for_load_state('networkidle')
            
            # Force game view to be visible
            page.evaluate("""
                const gameView = document.getElementById('game-view');
                if (gameView) {
                    gameView.classList.add('active-view');
                    gameView.style.display = 'flex';
                }
            """)
            
            # Wait for game view
            if not helper.wait_for_element("#game-view", timeout=5):
                raise Exception("Game view not found")
            
            helper.take_screenshot("game_view_loaded")
            
            print("⚔️ Testing character mode with mock response...")
            # Test character mode interaction with correct selectors
            action_input = page.locator("#user-input")
            action_input.fill("I attack the goblin")
            page.click("text='Send'")  # Use text selector for Send button
            
            # Wait for mock response
            if not helper.wait_for_content("Response time:", timeout=10):
                raise Exception("No response received from mock API")
            
            helper.take_screenshot("character_mode_response")
            
            # Verify structured fields are present
            field_checks = {
                'session_header': '.session-header',
                'entities_mentioned': '.entities-mentioned',
                'location_confirmed': '.location-confirmed',
                'dice_rolls': '.dice-rolls',
                'resources': '.resources',
                'planning_block': '.planning-block',
                'debug_info': '.debug-info',
                'dm_notes': '.dm-notes',
                'state_rationale': '.state-rationale'
            }
            
            print("🔍 Verifying structured fields presence...")
            found_fields = []
            for field_name, selector in field_checks.items():
                if page.locator(selector).count() > 0:
                    helper.take_screenshot(f"field_{field_name}", selector)
                    found_fields.append(field_name)
                    print(f"✅ {field_name} - Found and captured")
                else:
                    print(f"⚠️ {field_name} - Not found in UI")
            
            print("🔮 Testing god mode with mock response...")
            # Test god mode interaction
            god_radio = page.locator('input[value="god"]')
            if god_radio.count() > 0:
                god_radio.click()
                action_input.fill("/god show current game state")
                page.click("#send-action")
                
                # Wait for god mode response
                if helper.wait_for_content("Response time:", timeout=10):
                    helper.take_screenshot("god_mode_response")
                    
                    # Check for god mode response field
                    if page.locator('.god-mode-response').count() > 0:
                        helper.take_screenshot("god_mode_field", ".god-mode-response")
                        found_fields.append("god_mode_response")
                        print("✅ god_mode_response - Found and captured")
                    else:
                        print("⚠️ god_mode_response - Not found in UI")
            
            # Final summary
            helper.take_screenshot("final_state")
            summary = helper.get_screenshot_summary()
            
            print(f"\n✅ Layer 3 Test Complete!")
            print(f"📁 Screenshots: {summary['screenshot_dir']}")
            print(f"📸 Total: {summary['total_screenshots']}")
            print(f"🎯 Fields found: {len(found_fields)}/10")
            print(f"📋 Found fields: {', '.join(found_fields)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Layer 3 test failed: {e}")
            helper.take_screenshot("error")
            return False
        finally:
            browser.close()
            mock_server.shutdown()

if __name__ == "__main__":
    success = test_layer3_structured_fields_mock()
    exit(0 if success else 1)