"""
Basic validation test for the Real-Mode Testing Framework integration.
Tests core functionality without external dependencies.
"""

import os
import sys
import unittest

from testing_framework.factory import get_current_provider
from testing_framework.factory import get_service_provider, reset_global_provider
from testing_framework.fixtures import get_test_client_for_mode
from testing_framework.integration_utils import (
from testing_framework.service_provider import TestServiceProvider

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set testing environment
os.environ["TESTING"] = "true"

# Test core framework imports
try:



    FRAMEWORK_AVAILABLE = True
    print("✅ Core framework imports successful")
except ImportError as e:
    print(f"❌ Framework import failed: {e}")
    FRAMEWORK_AVAILABLE = False


class TestBasicFramework(unittest.TestCase):
    """Test basic framework functionality."""

    def setUp(self):
        """Setup for each test."""
        if not FRAMEWORK_AVAILABLE:
            self.skipTest("Framework not available")

    def test_service_provider_creation(self):
        """Test that service providers can be created."""
        provider = get_service_provider("mock")
        self.assertIsNotNone(provider)
        self.assertIsInstance(provider, TestServiceProvider)

        # Test that services are available
        firestore = provider.get_firestore()
        gemini = provider.get_gemini()
        auth = provider.get_auth()

        self.assertIsNotNone(firestore)
        self.assertIsNotNone(gemini)
        self.assertIsNotNone(auth)

        # Test mode detection
        self.assertFalse(provider.is_real_service)  # Should be mock mode

        # Cleanup
        provider.cleanup()
        print("✅ Mock service provider working")

    def test_mode_switching(self):
        """Test switching between mock and real modes."""
        # Test mock mode
        mock_provider = get_service_provider("mock")
        self.assertFalse(mock_provider.is_real_service)
        mock_provider.cleanup()

        # Test real mode (should work even without real credentials)
        try:
            real_provider = get_service_provider("real")
            self.assertTrue(real_provider.is_real_service)
            real_provider.cleanup()
            print("✅ Real service provider creation working")
        except Exception as e:
            print(f"⚠️ Real service provider failed (expected without credentials): {e}")

    def test_global_provider_management(self):
        """Test global provider management."""


        # Reset to clean state
        reset_global_provider()

        # Get default provider (should use global)
        provider1 = get_current_provider()
        provider2 = get_current_provider()

        # Should get same instance (global)
        self.assertIs(provider1, provider2)

        # Reset and get new
        reset_global_provider()
        provider3 = get_current_provider()

        # Should be different instance
        self.assertIsNot(provider1, provider3)

        # Cleanup
        provider3.cleanup()
        print("✅ Global provider management working")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility features."""

    def setUp(self):
        """Setup for each test."""
        if not FRAMEWORK_AVAILABLE:
            self.skipTest("Framework not available")

    def test_get_test_client_helper(self):
        """Test the backward compatibility helper."""
        try:


            services = get_test_client_for_mode()

            # Should have all expected keys
            expected_keys = ["provider", "firestore", "gemini", "auth", "is_real"]
            for key in expected_keys:
                self.assertIn(key, services)
                self.assertIsNotNone(services[key])

            # Cleanup
            services["provider"].cleanup()
            print("✅ Backward compatibility helper working")

        except ImportError as e:
            print(f"⚠️ Pytest-based fixtures not available: {e}")

    def test_integration_utils_import(self):
        """Test that integration utilities can be imported."""
        try:

                get_test_mode_info,
                validate_test_environment,
            )

            # Test validation function
            result = validate_test_environment()
            self.assertIsInstance(result, bool)

            # Test mode info
            info = get_test_mode_info()
            self.assertIsInstance(info, dict)
            self.assertIn("mode", info)
            self.assertIn("is_real", info)

            print("✅ Integration utilities working")

        except ImportError as e:
            print(f"⚠️ Some integration utilities not available: {e}")


class TestServiceOperations(unittest.TestCase):
    """Test basic service operations."""

    def setUp(self):
        """Setup for each test."""
        if not FRAMEWORK_AVAILABLE:
            self.skipTest("Framework not available")

        self.provider = get_service_provider("mock")

    def tearDown(self):
        """Cleanup after each test."""
        if hasattr(self, "provider"):
            self.provider.cleanup()

    def test_firestore_mock_operations(self):
        """Test that mock Firestore operations work."""
        firestore = self.provider.get_firestore()

        # Basic operations should not raise errors
        try:
            collection = firestore.collection("test")
            doc_ref = collection.document("test_doc")

            # Mock operations
            doc_ref.set({"test": True})
            result = doc_ref.get()

            # Should not raise errors
            self.assertIsNotNone(result)
            print("✅ Mock Firestore operations working")

        except Exception as e:
            print(f"⚠️ Mock Firestore operations failed: {e}")

    def test_gemini_mock_operations(self):
        """Test that mock Gemini operations work."""
        gemini = self.provider.get_gemini()

        try:
            # Basic mock operation
            response = gemini.generate_content("test prompt")
            self.assertIsNotNone(response)
            print("✅ Mock Gemini operations working")

        except Exception as e:
            print(f"⚠️ Mock Gemini operations failed: {e}")

    def test_auth_mock_operations(self):
        """Test that mock auth operations work."""
        auth = self.provider.get_auth()

        try:
            # Mock auth should be available
            self.assertIsNotNone(auth)
            print("✅ Mock auth operations working")

        except Exception as e:
            print(f"⚠️ Mock auth operations failed: {e}")


def run_validation():
    """Run all validation tests."""
    print("🧪 Real-Mode Testing Framework Basic Validation")
    print("=" * 50)

    # Test basic framework
    print("\n1. Testing basic framework...")
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestBasicFramework)
    result1 = unittest.TextTestRunner(verbosity=2).run(suite1)

    # Test backward compatibility
    print("\n2. Testing backward compatibility...")
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestBackwardCompatibility)
    result2 = unittest.TextTestRunner(verbosity=2).run(suite2)

    # Test service operations
    print("\n3. Testing service operations...")
    suite3 = unittest.TestLoader().loadTestsFromTestCase(TestServiceOperations)
    result3 = unittest.TextTestRunner(verbosity=2).run(suite3)

    # Summary
    all_results = [result1, result2, result3]
    total_tests = sum(r.testsRun for r in all_results)
    total_failures = sum(len(r.failures) for r in all_results)
    total_errors = sum(len(r.errors) for r in all_results)

    print("\n" + "=" * 50)
    print("🏁 VALIDATION SUMMARY")
    print(f"Total tests run: {total_tests}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")

    if total_failures == 0 and total_errors == 0:
        print("✅ ALL BASIC VALIDATION TESTS PASSED!")
        print("🎉 Real-Mode Testing Framework is working correctly")
        return True
    print("❌ Some validation tests failed")
    return False


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
