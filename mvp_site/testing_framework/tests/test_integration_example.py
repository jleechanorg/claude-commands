"""
Integration example showing how existing tests can use the framework.
This demonstrates backwards compatibility and easy migration.
"""

import os
import sys
import unittest

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from mvp_site.testing_framework.factory import (
    get_current_provider,
    reset_global_provider,
)


class TestIntegrationExample(unittest.TestCase):
    """Example showing how tests can use the service provider framework."""

    def setUp(self):
        """Set up test fixtures - use mock mode for safety."""
        # Ensure we're in mock mode for testing
        os.environ["TEST_MODE"] = "mock"
        reset_global_provider()

    def tearDown(self):
        """Clean up after tests."""
        reset_global_provider()

    def test_existing_test_pattern(self):
        """Test that simulates how existing tests would be updated."""
        # Get the appropriate service provider (mock or real based on TEST_MODE)
        provider = get_current_provider()

        # Use services through the provider interface
        firestore = provider.get_firestore()
        gemini = provider.get_gemini()
        auth = provider.get_auth()

        # Verify we got mock services (since TEST_MODE=mock)
        self.assertFalse(provider.is_real_service)
        self.assertIsNotNone(firestore)
        self.assertIsNotNone(gemini)

        # Test firestore operations
        campaigns = firestore.get_campaigns_for_user("test_user")
        self.assertIsInstance(campaigns, list)

        # Test gemini operations
        response = gemini.generate_content("test prompt")
        self.assertIsNotNone(response)

        # Cleanup after test
        provider.cleanup()

    def test_seamless_mode_switching(self):
        """Test that mode switching works without changing test code."""
        # Test with mock mode
        provider = get_current_provider()
        self.assertFalse(provider.is_real_service)

        # The same test could run with real services by just setting:
        # os.environ['TEST_MODE'] = 'real'
        # os.environ['TEST_GEMINI_API_KEY'] = 'actual_key'
        # (but we won't do that here to avoid costs)

        # Test that the interface is identical regardless of mode
        firestore = provider.get_firestore()
        gemini = provider.get_gemini()

        # Both mock and real providers support these methods
        self.assertTrue(hasattr(firestore, "get_campaigns_for_user"))
        self.assertTrue(hasattr(gemini, "generate_content"))
        self.assertTrue(hasattr(provider, "cleanup"))
        self.assertTrue(hasattr(provider, "is_real_service"))


if __name__ == "__main__":
    unittest.main()
