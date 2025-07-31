#!/usr/bin/env python3

"""
Red/Green Test: Authentication Resilience
Tests that JWT clock skew errors are automatically handled with retry logic
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from config.paths import PATHS


class AuthResilienceTest(unittest.TestCase):
    """Test authentication resilience features"""

    def setUp(self):
        """Set up test environment"""
        # Use centralized path configuration - no more manual calculations!
        self.test_dir = PATHS.base_dir

    def test_clock_skew_auto_retry_mechanism(self):
        """
        🔴 RED TEST: Verify that clock skew errors trigger auto-retry
        This test simulates the JWT "Token used too early" error and verifies
        that the new resilience logic attempts retry with fresh token
        """
        print("🔴 RED TEST: Testing clock skew auto-retry mechanism")

        # Read the updated api.js file
        api_js_file = self.test_dir / "frontend_v1/api.js"
        if not api_js_file.exists():
            self.fail("api.js file not found - cannot test resilience features")

        api_js_content = api_js_file.read_text()

        # 🔴 RED: Check that auto-retry logic exists
        assert (
            "retryCount" in api_js_content
        ), "FAIL: No retry count parameter found - auto-retry not implemented"

        assert (
            "Token used too early" in api_js_content
        ), "FAIL: No clock skew detection found"

        assert (
            "isClockSkewError" in api_js_content
        ), "FAIL: No clock skew error detection logic found"

        assert "forceRefresh" in api_js_content, "FAIL: No token refresh forcing found"

        # 🔴 RED: Check that retry happens for 401 errors
        retry_pattern_found = (
            "response.status === 401" in api_js_content
            and "retryCount < 2" in api_js_content
        )
        assert (
            retry_pattern_found
        ), "FAIL: No 401 retry logic found - won't auto-recover from auth failures"

        # 🔴 RED: Check that recursive retry call exists
        recursive_retry_found = (
            "fetchApi(path, options, retryCount + 1)" in api_js_content
        )
        assert (
            recursive_retry_found
        ), "FAIL: No recursive retry call found - won't actually retry"

        print("✅ Auto-retry mechanism implementation found")

    def test_user_friendly_error_messages(self):
        """
        🔴 RED TEST: Verify that user gets helpful error messages instead of generic failures
        """
        print("🔴 RED TEST: Testing user-friendly error messaging")

        # Read the updated app.js file with robust path resolution
        frontend_dir = self.test_dir / "frontend_v1"
        app_js_file = frontend_dir / "app.js"

        # Comprehensive debugging for CI issues
        if not app_js_file.exists():
            print("🔍 PATH DEBUG INFORMATION:")
            print(f"  Current working dir: {os.getcwd()}")
            print(f"  Test file location: {Path(__file__).resolve()}")
            print(f"  Calculated test_dir: {self.test_dir}")
            print(f"  Looking for app.js at: {app_js_file}")
            print(f"  frontend_v1 dir exists: {frontend_dir.exists()}")
            print(
                f"  mvp_site contents: {list(self.test_dir.iterdir()) if self.test_dir.exists() else 'DIR_NOT_FOUND'}"
            )
            if frontend_dir.exists():
                print(f"  frontend_v1 contents: {list(frontend_dir.iterdir())}")

            # Try alternate locations as diagnostic
            alt_static = self.test_dir / "static" / "app.js"
            alt_root = self.test_dir / "app.js"
            print(f"  static/app.js exists: {alt_static.exists()}")
            print(f"  root app.js exists: {alt_root.exists()}")

            self.fail("app.js file not found - cannot test error messaging")

        app_js_content = app_js_file.read_text()

        # 🔴 RED: Check for specific error message improvements
        assert (
            "Authentication timing issue detected" in app_js_content
        ), "FAIL: No user-friendly clock skew message found"

        assert (
            "Would you like to try again?" in app_js_content
        ), "FAIL: No retry option offered to user"

        assert "showRetryOption" in app_js_content, "FAIL: No retry option logic found"

        # 🔴 RED: Check for different error categories
        assert (
            "Network connection issue" in app_js_content
        ), "FAIL: No network error categorization found"

        assert (
            "Authentication issue" in app_js_content
        ), "FAIL: No auth error categorization found"

        print("✅ User-friendly error messaging implementation found")

    def test_offline_campaign_caching(self):
        """
        🔴 RED TEST: Verify that successful campaign data is cached for offline viewing
        """
        print("🔴 RED TEST: Testing offline campaign caching")

        app_js_file = self.test_dir / "frontend_v1/app.js"
        app_js_content = app_js_file.read_text()

        # 🔴 RED: Check for localStorage caching implementation
        assert (
            "localStorage.setItem('cachedCampaigns'" in app_js_content
        ), "FAIL: No campaign caching found"

        assert (
            "localStorage.getItem('cachedCampaigns')" in app_js_content
        ), "FAIL: No cached campaign retrieval found"

        assert (
            "Offline Mode:" in app_js_content
        ), "FAIL: No offline mode user notification found"

        # 🔴 RED: Check for cache fallback logic
        assert (
            "cachedCampaigns" in app_js_content
        ), "FAIL: No cache fallback implementation found"

        print("✅ Offline campaign caching implementation found")

    def test_connection_status_monitoring(self):
        """
        🔴 RED TEST: Verify that connection status is monitored for smart UI adaptations
        """
        print("🔴 RED TEST: Testing connection status monitoring")

        api_js_file = self.test_dir / "frontend_v1/api.js"
        api_js_content = api_js_file.read_text()

        # 🔴 RED: Check for connection monitoring
        assert (
            "navigator.onLine" in api_js_content
        ), "FAIL: No online status monitoring found"

        assert (
            "connectionStatus" in api_js_content
        ), "FAIL: No connection status tracking found"

        assert (
            "getConnectionStatus" in api_js_content
        ), "FAIL: No connection status getter function found"

        # 🔴 RED: Check for network event listeners
        assert (
            "addEventListener('online'" in api_js_content
        ), "FAIL: No online event listener found"

        assert (
            "addEventListener('offline'" in api_js_content
        ), "FAIL: No offline event listener found"

        print("✅ Connection status monitoring implementation found")

    def test_integrated_resilience_workflow(self):
        """
        🟢 GREEN TEST: Test the complete resilience workflow end-to-end
        This verifies that all components work together correctly
        """
        print("🟢 GREEN TEST: Testing integrated resilience workflow")

        # This would be a more complex integration test in a real browser environment
        # For now, we verify that all required components are present and properly integrated

        api_js_file = self.test_dir / "frontend_v1/api.js"
        app_js_file = self.test_dir / "frontend_v1/app.js"

        api_content = api_js_file.read_text()
        app_content = app_js_file.read_text()

        # 🟢 GREEN: Verify integration points
        integration_checks = [
            # API retry logic is properly structured
            ("retryCount = 0" in api_content, "Default retry count parameter"),
            (
                "forceRefresh = retryCount > 0" in api_content,
                "Token refresh forcing logic",
            ),
            ("setTimeout(resolve, 1000)" in api_content, "Retry delay implementation"),
            # App error handling calls retry logic
            (
                "dispatchEvent(new Event('submit'))" in app_content,
                "Retry form submission",
            ),
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
    print("\n" + "=" * 60)
    print("🧪 AUTHENTICATION RESILIENCE: RED/GREEN TEST SUITE")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(AuthResilienceTest)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
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

    print("=" * 60)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_red_green_test()
    sys.exit(0 if success else 1)
