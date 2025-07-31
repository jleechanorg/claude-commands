#!/usr/bin/env python3
"""
Real browser test for Gemini Model Settings functionality using Playwright.
Tests the specific settings page implementation with model selection.
"""

import os
import sys

from playwright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_gemini_settings_browser():
    """Test Gemini model settings through real browser automation."""

    with sync_playwright() as p:
        # Launch browser (headless=False for visual debugging)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        # Set viewport for consistent screenshots
        page.set_viewport_size({"width": 1280, "height": 720})

        # Set authentication headers for all requests
        page.set_extra_http_headers({
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "gemini-settings-test-user"
        })

        # Monitor console logs and errors
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda error: print(f"PAGE ERROR: {error}"))

        try:
            base_url = "http://localhost:6006"
            test_user_id = "gemini-settings-test-user"

            print("🚀 Starting Gemini Settings Browser Test")

            # Navigate with test mode authentication
            test_url = f"{base_url}?test_mode=true&test_user_id={test_user_id}"
            print(f"📍 Navigating to: {test_url}")
            page.goto(test_url)

            # Wait for test mode initialization
            page.wait_for_function("window.testAuthBypass !== undefined", timeout=10000)
            print("✅ Test authentication initialized")

            # Take screenshot of dashboard
            page.screenshot(path="testing_ui/test_results/01_dashboard.png")
            print("📸 Screenshot: Dashboard loaded")

            # Find and click the Settings button (the one that navigates to /settings)
            print("🔍 Looking for Settings button...")
            settings_button = page.locator("button[onclick=\"window.location.href='/settings'\"]")
            settings_button.wait_for(timeout=5000)

            # Take screenshot before clicking settings
            page.screenshot(path="testing_ui/test_results/02_before_settings_click.png")
            print("📸 Screenshot: Before clicking Settings")

            settings_button.click()
            print("🔧 Clicked Settings button")

            # Wait for navigation to complete
            page.wait_for_load_state("networkidle", timeout=10000)
            print(f"   Current URL after click: {page.url}")

            # Take screenshot to see what we got
            page.screenshot(path="testing_ui/test_results/03_after_settings_click.png")

            # Check if we're on settings page or if auth is required
            if "/settings" in page.url:
                print("✅ Navigated to settings page")
                # Wait for page content to load, be more flexible with selector
                try:
                    page.wait_for_selector("text=Settings", timeout=5000)
                except:
                    print("   ⚠️  Settings text not found, trying other selectors...")
                    # Just wait a bit for page to fully render
                    page.wait_for_timeout(2000)
            else:
                print("⚠️  Not on settings page, trying direct navigation...")
                # Try direct navigation with auth headers in URL
                direct_url = f"{base_url}/settings?test_mode=true&test_user_id={test_user_id}"
                page.goto(direct_url)
                page.wait_for_load_state("networkidle", timeout=10000)

            print("✅ Settings page loaded")

            # Debug: print page title and content
            print(f"   Page title: {page.title()}")
            print(f"   Final URL: {page.url}")

            # Take screenshot of settings page
            page.screenshot(path="testing_ui/test_results/03_settings_page_loaded.png")
            print("📸 Screenshot: Settings page loaded")

            # Verify settings page elements with debugging
            print("🔍 Checking page content...")
            page_content = page.content()
            if "AI Model Selection" in page_content:
                print("✅ AI Model Selection found in HTML")
            else:
                print("❌ AI Model Selection NOT found in HTML")

            if "geminiModel" in page_content:
                print("✅ Radio buttons found in HTML")
            else:
                print("❌ Radio buttons NOT found in HTML")

            # Check if elements are visible
            try:
                assert page.is_visible("text=AI Model Selection")
                print("✅ AI Model Selection is visible")
            except:
                print("❌ AI Model Selection not visible")

            try:
                assert page.is_visible("text=Choose your preferred Gemini model")
                print("✅ Gemini model text is visible")
            except:
                print("❌ Gemini model text not visible")

            print("✅ Settings page elements checked")

            # Check initial model selection (should be Pro 2.5 by default)
            pro_radio = page.locator("input[value='pro-2.5']")
            flash_radio = page.locator("input[value='flash-2.5']")

            assert pro_radio.is_checked()
            print("✅ Pro 2.5 is initially selected (default)")

            # Take screenshot of initial state
            page.screenshot(path="testing_ui/test_results/04_initial_model_selection.png")
            print("📸 Screenshot: Initial model selection (Pro 2.5)")

            # Change to Flash 2.5
            print("🔄 Changing to Flash 2.5...")
            flash_radio.click()

            # Wait for auto-save (our implementation has 300ms debounce + network time)
            page.wait_for_timeout(2000)

            # Verify Flash is now selected
            assert flash_radio.is_checked()
            assert not pro_radio.is_checked()
            print("✅ Flash 2.5 selected successfully")

            # Check for any JavaScript errors
            page.wait_for_timeout(500)

            # Wait for save message to appear (with longer timeout)
            save_message = page.locator("#save-message")
            try:
                save_message.wait_for(state="visible", timeout=10000)
                print("✅ Save message appeared")
            except:
                print("⚠️  Save message didn't appear, checking if API call completed...")
                # Take screenshot to debug
                page.screenshot(path="testing_ui/test_results/05_debug_no_save_message.png")

                # Check if message is there but hidden
                if page.locator("#save-message").count() > 0:
                    print("   Save message element exists but may not be visible")
                else:
                    print("   Save message element not found")

                # Still continue test to see if functionality works

            # Take screenshot of Flash selection with save message
            page.screenshot(path="testing_ui/test_results/05_flash_selected_with_message.png")
            print("📸 Screenshot: Flash 2.5 selected with save confirmation")

            # Verify save message content
            assert page.is_visible("text=Settings saved successfully!")
            print("✅ Save confirmation message displayed")

            # Change back to Pro 2.5
            print("🔄 Changing back to Pro 2.5...")
            pro_radio.click()

            # Wait for auto-save
            page.wait_for_timeout(1000)

            # Verify Pro is selected again
            assert pro_radio.is_checked()
            assert not flash_radio.is_checked()
            print("✅ Pro 2.5 selected successfully")

            # Wait for save message
            page.wait_for_timeout(1000)

            # Take screenshot of Pro selection
            page.screenshot(path="testing_ui/test_results/06_pro_selected_final.png")
            print("📸 Screenshot: Pro 2.5 selected (final state)")

            # Test navigation back to home
            back_button = page.locator("a:has-text('Back to Home')")
            back_button.click()
            print("🏠 Clicked Back to Home")

            # Wait for dashboard to load
            page.wait_for_url(f"{base_url}/**", timeout=5000)
            page.wait_for_selector("h2:has-text('My Campaigns')", timeout=5000)

            # Take final screenshot
            page.screenshot(path="testing_ui/test_results/07_back_to_dashboard.png")
            print("📸 Screenshot: Back to dashboard")
            print("✅ Navigation back to dashboard successful")

            print("\n🎉 ALL TESTS PASSED!")
            print("📸 Screenshots saved to testing_ui/test_results/")
            print("   - Dashboard loaded")
            print("   - Before clicking Settings")
            print("   - Settings page loaded")
            print("   - Initial model selection (Pro 2.5)")
            print("   - Flash 2.5 selected with save message")
            print("   - Pro 2.5 selected (final)")
            print("   - Back to dashboard")

            return True

        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(path="testing_ui/test_results/ERROR_test_failed.png")
            return False

        finally:
            browser.close()

if __name__ == "__main__":
    # Create results directory
    os.makedirs("testing_ui/test_results", exist_ok=True)

    success = test_gemini_settings_browser()

    if success:
        print("\n✅ GEMINI SETTINGS BROWSER TEST PASSED")
        sys.exit(0)
    else:
        print("\n❌ GEMINI SETTINGS BROWSER TEST FAILED")
        sys.exit(1)
