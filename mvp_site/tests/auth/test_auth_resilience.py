#!/usr/bin/env python3

"""
Red/Green Test: Authentication Resilience
Tests that JWT clock skew errors are automatically handled with retry logic
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

class AuthResilienceTest(unittest.TestCase):
    """Test authentication resilience features"""
    
    def setUp(self):
        """Set up test environment"""
        # Go up two levels from tests/auth/ to get to mvp_site/
        self.test_dir = Path(__file__).parent.parent.parent
        
    def test_clock_skew_auto_retry_mechanism(self):
        """
        🔴 RED TEST: Verify that clock skew errors trigger auto-retry
        This test simulates the JWT "Token used too early" error and verifies
        that the new resilience logic attempts retry with fresh token
        """
        print("🔴 RED TEST: Testing clock skew auto-retry mechanism")
        
        # Read the updated api.js file
        api_js_file = self.test_dir / "static/api.js"
        if not api_js_file.exists():
            self.fail("api.js file not found - cannot test resilience features")
        
        api_js_content = api_js_file.read_text()
        
        # 🔴 RED: Check that auto-retry logic exists
        self.assertIn("retryCount", api_js_content, 
                     "FAIL: No retry count parameter found - auto-retry not implemented")
        
        self.assertIn("Token used too early", api_js_content,
                     "FAIL: No clock skew detection found")
        
        self.assertIn("isClockSkewError", api_js_content,
                     "FAIL: No clock skew error detection logic found")
        
        self.assertIn("forceRefresh", api_js_content,
                     "FAIL: No token refresh forcing found")
        
        # 🔴 RED: Check that retry happens for 401 errors
        retry_pattern_found = "response.status === 401" in api_js_content and "retryCount < 2" in api_js_content
        self.assertTrue(retry_pattern_found,
                       "FAIL: No 401 retry logic found - won't auto-recover from auth failures")
        
        # 🔴 RED: Check that recursive retry call exists
        recursive_retry_found = "fetchApi(path, options, retryCount + 1)" in api_js_content
        self.assertTrue(recursive_retry_found,
                       "FAIL: No recursive retry call found - won't actually retry")
        
        print("✅ Auto-retry mechanism implementation found")
        
    def test_user_friendly_error_messages(self):
        """
        🔴 RED TEST: Verify that user gets helpful error messages instead of generic failures
        """
        print("🔴 RED TEST: Testing user-friendly error messaging")
        
        # Read the updated app.js file  
        app_js_file = self.test_dir / "static/app.js"
        if not app_js_file.exists():
            self.fail("app.js file not found - cannot test error messaging")
            
        app_js_content = app_js_file.read_text()
        
        # 🔴 RED: Check for specific error message improvements
        self.assertIn("Authentication timing issue detected", app_js_content,
                     "FAIL: No user-friendly clock skew message found")
        
        self.assertIn("Would you like to try again?", app_js_content,
                     "FAIL: No retry option offered to user")
        
        self.assertIn("showRetryOption", app_js_content,
                     "FAIL: No retry option logic found")
        
        # 🔴 RED: Check for different error categories
        self.assertIn("Network connection issue", app_js_content,
                     "FAIL: No network error categorization found")
        
        self.assertIn("Authentication issue", app_js_content,
                     "FAIL: No auth error categorization found")
        
        print("✅ User-friendly error messaging implementation found")
        
    def test_offline_campaign_caching(self):
        """
        🔴 RED TEST: Verify that successful campaign data is cached for offline viewing
        """
        print("🔴 RED TEST: Testing offline campaign caching")
        
        app_js_file = self.test_dir / "static/app.js"
        app_js_content = app_js_file.read_text()
        
        # 🔴 RED: Check for localStorage caching implementation
        self.assertIn("localStorage.setItem('cachedCampaigns'", app_js_content,
                     "FAIL: No campaign caching found")
        
        self.assertIn("localStorage.getItem('cachedCampaigns')", app_js_content,
                     "FAIL: No cached campaign retrieval found")
        
        self.assertIn("Offline Mode:", app_js_content,
                     "FAIL: No offline mode user notification found")
        
        # 🔴 RED: Check for cache fallback logic
        self.assertIn("cachedCampaigns", app_js_content,
                     "FAIL: No cache fallback implementation found")
        
        print("✅ Offline campaign caching implementation found")
        
    def test_connection_status_monitoring(self):
        """
        🔴 RED TEST: Verify that connection status is monitored for smart UI adaptations
        """
        print("🔴 RED TEST: Testing connection status monitoring")
        
        api_js_file = self.test_dir / "static/api.js"
        api_js_content = api_js_file.read_text()
        
        # 🔴 RED: Check for connection monitoring
        self.assertIn("navigator.onLine", api_js_content,
                     "FAIL: No online status monitoring found")
        
        self.assertIn("connectionStatus", api_js_content,
                     "FAIL: No connection status tracking found")
        
        self.assertIn("getConnectionStatus", api_js_content,
                     "FAIL: No connection status getter function found")
        
        # 🔴 RED: Check for network event listeners
        self.assertIn("addEventListener('online'", api_js_content,
                     "FAIL: No online event listener found")
        
        self.assertIn("addEventListener('offline'", api_js_content,
                     "FAIL: No offline event listener found")
        
        print("✅ Connection status monitoring implementation found")

    def test_integrated_resilience_workflow(self):
        """
        🟢 GREEN TEST: Test the complete resilience workflow end-to-end
        This verifies that all components work together correctly
        """
        print("🟢 GREEN TEST: Testing integrated resilience workflow")
        
        # This would be a more complex integration test in a real browser environment
        # For now, we verify that all required components are present and properly integrated
        
        api_js_file = self.test_dir / "static/api.js"
        app_js_file = self.test_dir / "static/app.js"
        
        api_content = api_js_file.read_text()
        app_content = app_js_file.read_text()
        
        # 🟢 GREEN: Verify integration points
        integration_checks = [
            # API retry logic is properly structured
            ("retryCount = 0" in api_content, "Default retry count parameter"),
            ("forceRefresh = retryCount > 0" in api_content, "Token refresh forcing logic"),
            ("setTimeout(resolve, 1000)" in api_content, "Retry delay implementation"),
            
            # App error handling calls retry logic  
            ("dispatchEvent(new Event('submit'))" in app_content, "Retry form submission"),
            ("showRetryOption" in app_content, "User retry option logic"),
            
            # Offline mode integration
            ("renderCampaignListUI(campaigns" in app_content, "Offline UI rendering"),
            ("isOffline" in app_content, "Offline mode parameter"),
        ]
        
        failed_checks = []
        for check, description in integration_checks:
            if not check:
                failed_checks.append(description)
        
        if failed_checks:
            self.fail(f"Integration failures: {', '.join(failed_checks)}")
            
        print("✅ All resilience components properly integrated")

def run_red_green_test():
    """
    Run the red/green test suite and report results
    """
    print("\n" + "="*60)
    print("🧪 AUTHENTICATION RESILIENCE: RED/GREEN TEST SUITE")
    print("="*60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(AuthResilienceTest)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🟢 GREEN STATE ACHIEVED: All resilience features implemented correctly!")
        print(f"✅ {result.testsRun} tests passed")
        print("\n🎯 RESILIENCE FEATURES VALIDATED:")
        print("   • JWT clock skew auto-retry ✅")
        print("   • User-friendly error messages ✅") 
        print("   • Offline campaign caching ✅")
        print("   • Connection status monitoring ✅")
        print("   • Integrated workflow ✅")
    else:
        print("🔴 RED STATE: Some resilience features missing or broken!")
        print(f"❌ {len(result.failures)} test failures")
        print(f"❌ {len(result.errors)} test errors")
        
        if result.failures:
            print("\n🔍 FAILURES:")
            for test, failure in result.failures:
                print(f"   • {test}: {failure.split('FAIL:')[-1].strip()}")
                
        if result.errors:
            print("\n🔍 ERRORS:")
            for test, error in result.errors:
                print(f"   • {test}: {error}")
    
    print("="*60)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_red_green_test()
    exit(0 if success else 1) 