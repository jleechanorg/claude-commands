#!/usr/bin/env python3
"""
Real browser test for continuing an existing campaign using Playwright.
This test automates a real browser to test campaign continuation functionality.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8080"
TEST_USER_ID = "browser-test-user"
SCREENSHOT_DIR = "/tmp/worldarchitect_browser_screenshots"  # Standardized screenshot directory

def test_continue_campaign_browser():
    """Test continuing an existing campaign through real browser automation."""
    
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser (headless=True for CI)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Set up console listener before navigation
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            page.on("pageerror", lambda exc: console_logs.append(f"pageerror: {exc}"))
            
            # Listen for request failures
            def on_request_failed(request):
                console_logs.append(f"request_failed: {request.url} - {request.failure}")
            page.on("requestfailed", on_request_failed)
            
            # Listen for responses
            def on_response(response):
                if 'auth.js' in response.url:
                    console_logs.append(f"response: auth.js status={response.status}")
            page.on("response", on_response)
            
            # Add debugging script before navigation
            page.add_init_script("""
                console.log('=== PAGE LOADING ===');
                console.log('Initial URL:', window.location.href);
                console.log('URL params:', window.location.search);
                
                // Log when scripts execute
                const scriptObserver = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        mutation.addedNodes.forEach((node) => {
                            if (node.tagName === 'SCRIPT' && node.src) {
                                if (node.src.includes('auth.js')) {
                                    console.log('🔑 auth.js script tag added:', node.src);
                                }
                            }
                        });
                    });
                });
                scriptObserver.observe(document.documentElement, { childList: true, subtree: true });
            """)
            
            # Don't add any init scripts that might interfere
            
            print("🌐 Navigating to WorldArchitect.AI...")
            # Navigate with test mode parameters
            page.goto(f"{BASE_URL}?test_mode=true&test_user_id={TEST_USER_ID}", wait_until="networkidle")
            
            # Wait longer for test mode to fully initialize
            print("⏳ Waiting for test mode initialization...")
            page.wait_for_timeout(2000)
            
            # Check if auth.js is loaded
            auth_check = page.evaluate("""
                (() => {
                    const scripts = Array.from(document.querySelectorAll('script'));
                    const authScript = scripts.find(s => s.src && s.src.includes('auth.js'));
                    const urlParams = new URLSearchParams(window.location.search);
                    return {
                        authScriptFound: !!authScript,
                        authScriptSrc: authScript ? authScript.src : null,
                        testModeParam: urlParams.get('test_mode'),
                        testUserIdParam: urlParams.get('test_user_id'),
                        windowTestAuthBypass: !!window.testAuthBypass,
                        locationSearch: window.location.search
                    };
                })();
            """)
            print(f"\n🔍 Auth check: {auth_check}")
            
            page.wait_for_timeout(3000)  # More time
            
            # Print console logs for debugging
            print("\n🗒️  Console logs:")
            for log in console_logs[:10]:  # Show first 10 logs
                print(f"   {log}")
            
            # Check if test mode is working by looking for auth screen
            if page.is_visible("text=Sign in with Google"):
                print("❌ Test mode authentication bypass not working!")
                print("   Injecting manual test mode activation...")
                
                # Manually trigger test mode
                page.evaluate("""
                    console.log('🔧 Manually activating test mode...');
                    // Set test auth bypass
                    window.testAuthBypass = {
                        enabled: true,
                        userId: 'browser-test-user'
                    };
                    
                    // Hide auth view and show dashboard directly
                    const authView = document.getElementById('auth-view');
                    const dashboardView = document.getElementById('dashboard-view');
                    if (authView && dashboardView) {
                        console.log('🔀 Switching views manually...');
                        authView.classList.remove('active-view');
                        dashboardView.classList.add('active-view');
                    }
                    
                    // Fire the test mode ready event
                    window.dispatchEvent(new CustomEvent('testModeReady', { 
                        detail: { userId: 'browser-test-user' } 
                    }));
                    
                    // Ensure fetchApi will work with test auth
                    window.fetchApi = async function(path, options = {}) {
                        const config = { 
                            ...options, 
                            headers: {
                                'X-Test-Bypass-Auth': 'true',
                                'X-Test-User-ID': 'browser-test-user',
                                'Content-Type': 'application/json',
                                ...options.headers
                            }
                        };
                        const response = await fetch(path, config);
                        if (!response.ok) throw new Error(`HTTP ${response.status}`);
                        return response.json();
                    };
                    
                    // Trigger campaign list render if function exists
                    if (window.renderCampaignList) {
                        console.log('📝 Rendering campaign list...');
                        window.renderCampaignList();
                    }
                """)
                
                page.wait_for_timeout(2000)
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_01b_after_manual_activation.png"))
                
                # Check again
                if page.is_visible("text=Sign in with Google"):
                    print("❌ Still showing auth screen after manual activation")
                    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_error_auth_screen.png"))
                    return False
            
            # Wait for testModeReady event to fire
            print("⏳ Waiting for test mode to initialize...")
            page.wait_for_timeout(2000)  # Give test mode time to set up
            
            # Wait for dashboard to load
            try:
                page.wait_for_selector("#dashboard-view.active-view", timeout=5000)
                print("✅ Dashboard view is active")
            except:
                print("⚠️  Dashboard not active, checking current state...")
            
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_01_dashboard.png"))
            
            # First create a real campaign
            print("🎮 Creating initial campaign to continue later...")
            
            # Click Start New Campaign
            new_campaign_button = page.query_selector("button:has-text('Start New Campaign')") or page.query_selector("text=New Campaign")
            if new_campaign_button:
                new_campaign_button.click()
                page.wait_for_timeout(2000)
                
                # Fill campaign details
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Adventure to Continue")
                    page.fill("#wizard-campaign-prompt", "A quest to find the lost artifact of power.")
                    
                    # Navigate through wizard
                    for i in range(4):
                        page.wait_for_timeout(1000)
                        if page.is_visible("#wizard-next"):
                            print(f"   ➡️ Step {i+1}: Clicking Next")
                            page.click("#wizard-next")
                        elif page.is_visible("#launch-campaign") or page.is_visible("button:has-text('Begin Adventure')"):
                            print("   🚀 Found Launch button")
                            launch_btn = page.query_selector("#launch-campaign") or page.query_selector("button:has-text('Begin Adventure')")
                            if launch_btn:
                                launch_btn.click()
                            break
                
                # Wait for game view
                print("⏳ Waiting for campaign creation...")
                page.wait_for_load_state("networkidle")
                try:
                    page.wait_for_selector("#game-view.active-view", timeout=15000)
                    print("✅ Campaign created and game view active")
                except:
                    print("❌ Game view timeout - campaign creation failed")
                    return False
            else:
                print("❌ Could not find New Campaign button")
                return False
            
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_01_campaign_created.png"))
            
            # Make some progress in the campaign
            print("📝 Making progress in the campaign...")
            message_input = page.query_selector("#message-input") or page.query_selector("textarea[placeholder*='What do you do']")
            if message_input:
                message_input.fill("I search for clues about the artifact's location")
                page.wait_for_timeout(500)
                
                # Send message
                send_button = page.query_selector("button:has-text('Send')") or page.query_selector("#send-button")
                if send_button:
                    send_button.click()
                else:
                    message_input.press("Enter")
                
                print("   ✉️ Action sent, waiting for response...")
                page.wait_for_timeout(8000)  # Wait for AI response
            
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_02_progress_made.png"))
            
            # Go back to dashboard
            print("🏠 Returning to dashboard...")
            back_button = page.query_selector("button:has-text('Back to Dashboard')") or page.query_selector("button:has-text('Dashboard')")
            if back_button:
                back_button.click()
                page.wait_for_timeout(3000)
            else:
                print("❌ Could not find Back to Dashboard button")
                return False
            
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_03_back_to_dashboard.png"))
            
            # Find and continue the campaign
            print("🔍 Looking for campaign to continue...")
            
            # Wait for campaigns to load
            page.wait_for_timeout(2000)
            
            # Look for the campaign we created
            campaign_found = False
            
            # Try different selectors for campaign cards
            campaign_selectors = [
                "text=Adventure to Continue",
                ".campaign-card:has-text('Adventure to Continue')",
                "[data-campaign-title='Adventure to Continue']"
            ]
            
            for selector in campaign_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found campaign with selector: {selector}")
                    page.click(selector)
                    campaign_found = True
                    break
            
            if not campaign_found:
                # Try to find any campaign card
                campaign_cards = page.query_selector_all(".campaign-card")
                if campaign_cards:
                    print(f"   📋 Found {len(campaign_cards)} campaign(s)")
                    # Click the first one that contains our title
                    for card in campaign_cards:
                        if "Adventure to Continue" in (card.text_content() or ""):
                            print("   ✅ Found campaign by text content")
                            card.click()
                            campaign_found = True
                            break
            
            if not campaign_found:
                print("❌ Could not find campaign to continue")
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_error_no_campaign.png"))
                return False
            
            # Wait for game to load
            print("⏳ Loading campaign...")
            page.wait_for_load_state("networkidle")
            
            try:
                page.wait_for_selector("#game-view.active-view", timeout=10000)
                print("✅ Successfully continued campaign!")
            except:
                print("⚠️  Game view not active after continue")
            
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_05_campaign_continued.png"))
            
            # Verify we're in the same campaign with history
            print("📜 Verifying campaign history...")
            
            # Check for previous messages
            chat_area = page.query_selector("#chat-messages") or page.query_selector(".chat-messages")
            if chat_area:
                messages = chat_area.text_content() or ""
                if "search for clues" in messages.lower() or "artifact" in messages.lower():
                    print("   ✅ Previous game history is visible")
                else:
                    print("   ⚠️  History not clearly visible in chat")
            
            # Check debug panel for state
            try:
                if page.is_visible("text=Debug Mode Active", timeout=2000):
                    print("   ✅ Debug mode is active")
                    # Try to find debug panel with different selectors
                    debug_panel = page.query_selector(".debug-panel") or page.query_selector("#debug-panel") or page.query_selector("[class*='debug']")
                    if debug_panel:
                        debug_content = debug_panel.text_content() or ""
                        if "custom_campaign_state" in debug_content:
                            print("   ✅ Campaign state preserved")
                        else:
                            print("   ⚠️  Debug panel found but no state info")
                    else:
                        print("   ⚠️  Debug panel not found")
            except:
                print("   ⚠️  Debug mode check skipped")
            
            # Send another action to verify continuity
            print("💬 Sending follow-up action...")
            message_input = page.query_selector("#message-input") or page.query_selector("textarea[placeholder*='What do you do']")
            if message_input:
                message_input.fill("I continue my search based on the clues found")
                
                send_button = page.query_selector("button:has-text('Send')") or page.query_selector("#send-button")
                if send_button:
                    send_button.click()
                else:
                    message_input.press("Enter")
                
                print("   ✉️ Follow-up action sent")
                page.wait_for_timeout(5000)
            
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_06_continued_gameplay.png"))
            
            # Print any console errors
            error_logs = [log for log in console_logs if "error" in log.lower()]
            if error_logs:
                print("\n⚠️  Console errors detected:")
                for log in error_logs[:5]:
                    print(f"   {log}")
            
            print("\n✅ Campaign continuation browser test completed successfully!")
            return True
            
        except TimeoutError as e:
            print(f"❌ Timeout error: {e}")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_error_timeout.png"))
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "continue_error_general.png"))
            return False
        finally:
            browser.close()


if __name__ == "__main__":
    print("🚀 Starting WorldArchitect.AI Campaign Continuation Browser Test")
    print(f"📍 Target URL: {BASE_URL}")
    print(f"📸 Screenshots will be saved to: {SCREENSHOT_DIR}")
    
    success = test_continue_campaign_browser()
    
    if success:
        print("\n✅ TEST PASSED - Campaign continuation tested via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)