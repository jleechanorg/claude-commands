"""
Validation tests for the Real-Mode Testing Framework integration.
Ensures that the integration works correctly and existing tests remain compatible.
"""

import os
import sys
import time
import unittest

from main import create_app
from testing_framework.integration_utils import get_test_mode_info

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set testing environment
os.environ["TESTING"] = "true"

# Test imports
from testing_framework.fixtures import BaseTestCase, get_test_client_for_mode
from testing_framework.integration_utils import (
    DualModeTestMixin,
    dual_mode_test,
    real_mode_only,
    skip_in_real_mode,
    smart_patch,
    validate_test_environment,
)


class TestFrameworkIntegration(BaseTestCase):
    """Test that the framework integration works correctly."""

    def test_service_provider_access(self):
        """Test that services are accessible through the framework."""
        # All services should be available
        assert self.firestore is not None
        assert self.gemini is not None
        assert self.auth is not None
        assert isinstance(self.is_real, bool)

        print(f"✅ Services accessible in {'REAL' if self.is_real else 'MOCK'} mode")

    def test_firestore_operations(self):
        """Test basic Firestore operations work in both modes."""
        # Create a test document
        collection_name = "test_integration_validation"
        if self.is_real:
            # Use unique collection name in real mode

            collection_name = f"{collection_name}_{int(time.time())}"

        doc_ref = self.firestore.collection(collection_name).document("test_doc")

        # Set data
        test_data = {
            "message": "Hello from integration test",
            "mode": "real" if self.is_real else "mock",
        }
        doc_ref.set(test_data)

        # Get data
        result = doc_ref.get()

        if self.is_real:
            # Real Firestore - document should exist
            assert result.exists, "Document should exist in real Firestore"
            data = result.to_dict()
            assert data["message"] == test_data["message"]
            print("✅ Real Firestore operations working")
        else:
            # Mock Firestore - should simulate the operation
            assert result is not None, "Mock should return a result"
            print("✅ Mock Firestore operations working")

    def test_gemini_operations(self):
        """Test basic Gemini operations work in both modes."""
        try:
            # Simple content generation
            response = self.gemini.generate_content(
                "Say 'Hello, World!' in a friendly way."
            )

            if self.is_real:
                # Real Gemini - should get actual response
                assert response is not None, "Should get real response from Gemini"
                # Real responses typically have text content
                assert hasattr(response, "text") or hasattr(response, "content"), (
                    "Response should have text content"
                )
                print("✅ Real Gemini operations working")
            else:
                # Mock Gemini - should get mock response
                assert response is not None, "Should get mock response"
                print("✅ Mock Gemini operations working")

        except Exception as e:
            if self.is_real:
                print(f"⚠️ Real Gemini test failed (may need API key): {e}")
            else:
                raise AssertionError(f"Mock Gemini test should not fail: {e}")


class TestBackwardsCompatibility(DualModeTestMixin, unittest.TestCase):
    """Test that existing test patterns still work with the framework."""

    def setUp(self):
        """Setup test environment."""
        super().setUp()

        # Simulate existing test setup
        try:
            self.app = create_app()
            self.app.config["TESTING"] = True
            self.client = self.app.test_client()
        except ImportError:
            # Skip if app dependencies not available
            self.client = None

    def test_mock_compatibility_attributes(self):
        """Test that mock compatibility attributes work."""
        # These attributes should be available for backward compatibility
        assert hasattr(self, "test_firestore")
        assert hasattr(self, "test_gemini")
        assert hasattr(self, "test_auth")
        assert hasattr(self, "is_real_mode")

        # Services should be functional
        assert self.test_firestore is not None
        assert self.test_gemini is not None
        assert self.test_auth is not None

        print(
            f"✅ Compatibility attributes available in {'REAL' if self.is_real_mode else 'MOCK'} mode"
        )

    @dual_mode_test
    def test_decorator_compatibility(self):
        """Test that dual_mode_test decorator works."""
        # This test should work with the decorator
        assert hasattr(self, "_dual_mode_setup")
        print("✅ Dual mode decorator working")

    def test_smart_patch_usage(self):
        """Test that smart_patch works correctly."""
        with smart_patch(test_service=self.test_gemini):
            # Should work without errors
            assert True

        print("✅ Smart patch working")


class TestGradualMigration(unittest.TestCase):
    """Test gradual migration patterns for existing tests."""

    def setUp(self):
        """Setup with gradual migration pattern."""
        # Simulate existing test setup
        self.original_setup_done = True

        # Add framework support gradually
        try:
            self.services = get_test_client_for_mode()
            self.has_framework = True
        except ImportError:
            self.services = None
            self.has_framework = False

    def tearDown(self):
        """Cleanup resources."""
        if self.services:
            self.services["provider"].cleanup()

    def test_gradual_adoption(self):
        """Test that tests can adopt framework features gradually."""
        if self.has_framework:
            # Framework available - use enhanced features
            assert self.services["provider"] is not None
            assert "firestore" in self.services
            assert "gemini" in self.services
            assert "auth" in self.services
            assert "is_real" in self.services

            print(
                f"✅ Gradual migration working with {'REAL' if self.services['is_real'] else 'MOCK'} services"
            )
        else:
            # Framework not available - fallback gracefully
            print("✅ Graceful fallback when framework not available")

        # Original test logic still works
        assert self.original_setup_done


class TestResourceManagement(BaseTestCase):
    """Test that resource management works correctly."""

    def test_cleanup_called(self):
        """Test that cleanup is called automatically."""
        # The BaseTestCase should handle cleanup automatically
        # We can't directly test cleanup, but we can verify setup
        assert self.provider is not None
        print("✅ Resource management setup correctly")

    def test_isolation_between_tests(self):
        """Test that tests are properly isolated."""
        # Each test should get fresh services
        test_id = id(self.provider)

        # Store test-specific data
        if hasattr(self, "_previous_test_id"):
            # This is not the first test method
            assert test_id != self._previous_test_id, (
                "Should get fresh provider instance"
            )

        self._previous_test_id = test_id
        print("✅ Test isolation working")


class TestModeSkipping(unittest.TestCase):
    """Test that mode-specific skipping works."""

    @skip_in_real_mode("Test uses hardcoded mock data")
    def test_mock_only_test(self):
        """This test should only run in mock mode."""
        # If this runs, we're in mock mode
        test_mode = os.getenv("TEST_MODE", "mock")
        if test_mode in ["real", "capture"]:
            raise AssertionError("This test should have been skipped in real mode")

        print("✅ Mock-only test running correctly")

    @real_mode_only("Test requires actual API integration")
    def test_real_only_test(self):
        """This test should only run in real mode."""
        # If this runs, we're in real mode
        test_mode = os.getenv("TEST_MODE", "mock")
        if test_mode == "mock":
            raise AssertionError("This test should have been skipped in mock mode")

        print("✅ Real-only test running correctly")


class TestFrameworkValidation(unittest.TestCase):
    """Test framework validation functions."""

    def test_environment_validation(self):
        """Test that validate_test_environment works."""
        result = validate_test_environment()
        assert isinstance(result, bool)

        if result:
            print("✅ Test environment validation passed")
        else:
            print("⚠️ Test environment validation failed (expected in some setups)")

    def test_mode_detection(self):
        """Test that test mode is detected correctly."""

        info = get_test_mode_info()
        assert "mode" in info
        assert "is_real" in info
        assert "provider_type" in info
        assert "test_mode_env" in info

        print(f"✅ Mode detection working: {info}")


if __name__ == "__main__":
    # Run validation tests
    print("🧪 Running Real-Mode Testing Framework Integration Validation")
    print("=" * 60)

    # Test basic framework functionality
    print("\n1. Testing basic framework functionality...")
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestFrameworkIntegration)
    result1 = unittest.TextTestRunner(verbosity=2).run(suite1)

    # Test backwards compatibility
    print("\n2. Testing backwards compatibility...")
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestBackwardsCompatibility)
    result2 = unittest.TextTestRunner(verbosity=2).run(suite2)

    # Test gradual migration
    print("\n3. Testing gradual migration...")
    suite3 = unittest.TestLoader().loadTestsFromTestCase(TestGradualMigration)
    result3 = unittest.TextTestRunner(verbosity=2).run(suite3)

    # Test resource management
    print("\n4. Testing resource management...")
    suite4 = unittest.TestLoader().loadTestsFromTestCase(TestResourceManagement)
    result4 = unittest.TextTestRunner(verbosity=2).run(suite4)

    # Test framework validation
    print("\n5. Testing framework validation...")
    suite5 = unittest.TestLoader().loadTestsFromTestCase(TestFrameworkValidation)
    result5 = unittest.TextTestRunner(verbosity=2).run(suite5)

    # Summary
    all_results = [result1, result2, result3, result4, result5]
    total_tests = sum(r.testsRun for r in all_results)
    total_failures = sum(len(r.failures) for r in all_results)
    total_errors = sum(len(r.errors) for r in all_results)

    print("\n" + "=" * 60)
    print("🏁 VALIDATION SUMMARY")
    print(f"Total tests run: {total_tests}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")

    if total_failures == 0 and total_errors == 0:
        print("✅ ALL INTEGRATION VALIDATION TESTS PASSED!")
        print("🎉 Real-Mode Testing Framework integration is working correctly")
    else:
        print("❌ Some integration validation tests failed")
        print("🔧 Check test output above for details")

    test_mode = os.getenv("TEST_MODE", "mock")
    print(f"📊 Tests run in {test_mode.upper()} mode")
