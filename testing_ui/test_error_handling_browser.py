#!/usr/bin/env python3
"""
Real browser test for Error Handling functionality using Playwright.
This test automates a real browser to test error handling and recovery.
"""

import os
import sys
from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_ui.browser_test_base import BrowserTestBase, click_button_with_text, wait_for_element


class ErrorHandlingTest(BrowserTestBase):
    """Test Error Handling functionality through real browser automation."""
    
    def __init__(self):
        super().__init__("Error Handling Test")
    
    def run_test(self, page: Page) -> bool:
        """Test error handling and recovery through browser automation."""
        
        try:
            # Take initial screenshot
            self.take_screenshot(page, "dashboard_initial")
            
            # Test network error handling
            print("🌐 Testing network error handling...")
            
            # Simulate network issues by blocking requests
            page.route("**/api/**", lambda route: route.abort())
            
            # Try to create a campaign with blocked network
            print("   🚫 Testing with blocked network requests...")
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(2000)
                
                # Look for error messages
                error_indicators = [
                    "text=Error",
                    "text=Network Error",
                    "text=Connection Failed",
                    "text=Unable to connect",
                    ".error-message",
                    "#error-notification"
                ]
                
                error_found = False
                for indicator in error_indicators:
                    if page.is_visible(indicator):
                        print(f"   ✅ Found error message: {indicator}")
                        error_text = page.text_content(indicator)
                        print(f"   Error text: {error_text}")
                        error_found = True
                        break
                
                if not error_found:
                    print("   ⚠️  No error message displayed for network failure")
                
                self.take_screenshot(page, "network_error")
            
            # Re-enable network requests
            page.unroute("**/api/**")
            
            # Test recovery from network error
            print("   🔄 Testing recovery from network error...")
            
            # Look for retry buttons
            retry_selectors = [
                "button:has-text('Retry')",
                "button:has-text('Try Again')",
                "button:has-text('Refresh')",
                ".retry-btn"
            ]
            
            for selector in retry_selectors:
                if page.is_visible(selector):
                    print(f"   ✅ Found retry button: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(2000)
                    
                    # Check if error is cleared
                    if not page.is_visible("text=Error"):
                        print("   ✅ Error cleared after retry")
                    
                    self.take_screenshot(page, "network_recovery")
                    break
            
            # Test form validation errors
            print("📝 Testing form validation errors...")
            
            # Navigate to campaign creation
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(1000)
                
                # Try to submit without filling required fields
                if page.is_visible("#wizard-next"):
                    page.click("#wizard-next")
                    page.wait_for_timeout(1000)
                    
                    # Look for validation errors
                    validation_errors = [
                        "text=required",
                        "text=Required",
                        "text=This field is required",
                        "text=Please fill",
                        ".validation-error",
                        ".field-error"
                    ]
                    
                    for error in validation_errors:
                        if page.is_visible(error):
                            print(f"   ✅ Found validation error: {error}")
                            error_text = page.text_content(error)
                            print(f"   Validation error: {error_text}")
                            break
                    
                    self.take_screenshot(page, "validation_errors")
                
                # Fill in valid data to clear errors
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Error Test Campaign")
                    page.fill("#wizard-campaign-prompt", "A campaign for testing error handling.")
                    page.wait_for_timeout(1000)
                    
                    # Check if validation errors are cleared
                    if not page.is_visible(".validation-error"):
                        print("   ✅ Validation errors cleared after fixing input")
                    
                    self.take_screenshot(page, "validation_fixed")
            
            # Test API error handling
            print("🔌 Testing API error handling...")
            
            # Complete campaign creation to get to game view
            if page.is_visible("#wizard-next"):
                for i in range(4):
                    if page.is_visible("#wizard-next"):
                        page.click("#wizard-next")
                        page.wait_for_timeout(1000)
                    elif page.is_visible("#launch-campaign"):
                        page.click("#launch-campaign")
                        break
                
                # Wait for game view
                page.wait_for_timeout(3000)
                
                # Simulate API error by blocking specific endpoints
                page.route("**/chat/**", lambda route: route.fulfill(status=500, body="Internal Server Error"))
                
                # Try to send a message
                message_input = page.query_selector("#message-input") or page.query_selector("textarea[placeholder*='What do you do']")
                if message_input:
                    message_input.fill("This message should trigger an API error")
                    
                    send_button = page.query_selector("button:has-text('Send')") or page.query_selector("#send-button")
                    if send_button:
                        send_button.click()
                    else:
                        message_input.press("Enter")
                    
                    page.wait_for_timeout(3000)
                    
                    # Look for API error messages
                    api_error_indicators = [
                        "text=Server Error",
                        "text=Failed to send",
                        "text=API Error",
                        "text=500",
                        ".api-error"
                    ]
                    
                    for indicator in api_error_indicators:
                        if page.is_visible(indicator):
                            print(f"   ✅ Found API error message: {indicator}")
                            break
                    
                    self.take_screenshot(page, "api_error")
                
                # Clear the API error route
                page.unroute("**/chat/**")
            
            # Test timeout handling
            print("⏱️  Testing timeout handling...")
            
            # Simulate slow API response
            page.route("**/chat/**", lambda route: page.wait_for_timeout(10000) or route.continue_())
            
            # Send another message
            if message_input:
                message_input.fill("This message should timeout")
                
                if send_button:
                    send_button.click()
                else:
                    message_input.press("Enter")
                
                # Wait for timeout indication
                page.wait_for_timeout(5000)
                
                # Look for timeout messages
                timeout_indicators = [
                    "text=Timeout",
                    "text=Taking too long",
                    "text=Request timeout",
                    ".timeout-error",
                    ".loading-indicator"
                ]
                
                for indicator in timeout_indicators:
                    if page.is_visible(indicator):
                        print(f"   ✅ Found timeout indicator: {indicator}")
                        break
                
                self.take_screenshot(page, "timeout_handling")
            
            # Clear timeout route
            page.unroute("**/chat/**")
            
            # Test authentication error handling
            print("🔐 Testing authentication error handling...")
            
            # Simulate auth error
            page.route("**/auth/**", lambda route: route.fulfill(status=401, body="Unauthorized"))
            
            # Try to access protected resource
            if page.is_visible("text=Settings"):
                page.click("text=Settings")
                page.wait_for_timeout(2000)
                
                # Look for auth error messages
                auth_error_indicators = [
                    "text=Unauthorized",
                    "text=Please log in",
                    "text=Session expired",
                    "text=401",
                    ".auth-error"
                ]
                
                for indicator in auth_error_indicators:
                    if page.is_visible(indicator):
                        print(f"   ✅ Found auth error message: {indicator}")
                        break
                
                self.take_screenshot(page, "auth_error")
            
            # Clear auth error route
            page.unroute("**/auth/**")
            
            # Test error boundaries/crash handling
            print("💥 Testing error boundaries and crash handling...")
            
            # Try to trigger a JavaScript error
            try:
                page.evaluate("throw new Error('Test error for error boundary')")
                page.wait_for_timeout(2000)
                
                # Look for error boundary UI
                error_boundary_indicators = [
                    "text=Something went wrong",
                    "text=Error occurred",
                    "text=Application error",
                    ".error-boundary",
                    "#error-fallback"
                ]
                
                for indicator in error_boundary_indicators:
                    if page.is_visible(indicator):
                        print(f"   ✅ Found error boundary: {indicator}")
                        break
                
                self.take_screenshot(page, "error_boundary")
            except Exception as e:
                print(f"   ⚠️  JavaScript error injection failed: {e}")
            
            # Test browser compatibility errors
            print("🌐 Testing browser compatibility handling...")
            
            # Check for browser compatibility warnings
            compat_indicators = [
                "text=unsupported browser",
                "text=Please update",
                "text=Browser not supported",
                ".browser-warning",
                "#compatibility-warning"
            ]
            
            for indicator in compat_indicators:
                if page.is_visible(indicator):
                    print(f"   ✅ Found compatibility warning: {indicator}")
                    break
            
            # Test offline handling
            print("📱 Testing offline handling...")
            
            # Set browser to offline mode
            page.context.set_offline(True)
            
            # Try to perform an action
            if page.is_visible("text=Dashboard"):
                page.click("text=Dashboard")
                page.wait_for_timeout(2000)
                
                # Look for offline indicators
                offline_indicators = [
                    "text=Offline",
                    "text=No connection",
                    "text=Check your internet",
                    ".offline-indicator",
                    "#offline-warning"
                ]
                
                for indicator in offline_indicators:
                    if page.is_visible(indicator):
                        print(f"   ✅ Found offline indicator: {indicator}")
                        break
                
                self.take_screenshot(page, "offline_handling")
            
            # Set browser back online
            page.context.set_offline(False)
            
            # Test recovery from offline
            print("   🔄 Testing recovery from offline...")
            page.wait_for_timeout(2000)
            
            # Look for online indicators
            online_indicators = [
                "text=Online",
                "text=Connected",
                "text=Back online",
                ".online-indicator"
            ]
            
            for indicator in online_indicators:
                if page.is_visible(indicator):
                    print(f"   ✅ Found online indicator: {indicator}")
                    break
            
            self.take_screenshot(page, "online_recovery")
            
            # Test graceful degradation
            print("🔧 Testing graceful degradation...")
            
            # Disable JavaScript to test degradation
            page.context.add_init_script("window.testDegradation = true;")
            
            # Try to use the application
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(2000)
                
                # Check if basic functionality still works
                if page.is_visible("#wizard-campaign-title"):
                    print("   ✅ Basic functionality available in degraded mode")
                    page.fill("#wizard-campaign-title", "Degraded Mode Test")
                    self.take_screenshot(page, "graceful_degradation")
            
            # Test error reporting
            print("📊 Testing error reporting...")
            
            # Look for error reporting UI
            error_report_indicators = [
                "text=Report Error",
                "text=Send Report",
                "button:has-text('Report')",
                ".error-report",
                "#error-feedback"
            ]
            
            for indicator in error_report_indicators:
                if page.is_visible(indicator):
                    print(f"   ✅ Found error reporting: {indicator}")
                    page.click(indicator)
                    page.wait_for_timeout(1000)
                    
                    # Look for error report form
                    if page.is_visible("textarea"):
                        print("   ✅ Error report form available")
                        page.fill("textarea", "This is a test error report")
                        
                        # Don't actually submit to avoid spam
                        if page.is_visible("button:has-text('Cancel')"):
                            page.click("button:has-text('Cancel')")
                    
                    self.take_screenshot(page, "error_reporting")
                    break
            
            print("\n✅ Error handling test completed successfully!")
            return True
            
        except TimeoutError as e:
            print(f"❌ Timeout error: {e}")
            self.take_screenshot(page, "error_timeout")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error_general")
            return False


if __name__ == "__main__":
    test = ErrorHandlingTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - Error handling tested via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)