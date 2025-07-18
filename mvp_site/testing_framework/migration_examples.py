"""
Migration examples showing how to update existing tests to support dual modes.
Demonstrates before/after patterns for common test scenarios.
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import testing framework
from testing_framework.fixtures import BaseTestCase

# Set testing environment
os.environ["TESTING"] = "true"

from main import create_app

# ============================================================================
# BEFORE: Traditional Mock-Only Test
# ============================================================================


class TraditionalCharacterTestBefore:
    """Example of old-style test that only works with mocks."""

    def setup_method(self):
        """Setup test client"""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_api_accepts_character_setting_params_old_way(self):
        """Test that /api/campaigns accepts character and setting parameters - OLD WAY"""

        # BEFORE: Hardcoded mocks, only works in mock mode
        with (
            patch("main.gemini_service") as mock_gemini,
            patch("main.firestore_service") as mock_firestore,
            patch("main.firebase_admin.auth") as mock_auth,
        ):
            # Setup mocks manually
            mock_auth.verify_id_token.return_value = {"uid": "test-user-123"}
            mock_response = MagicMock()
            mock_response.narrative_text = "Test story"
            mock_gemini.get_initial_story.return_value = mock_response
            mock_firestore.create_campaign.return_value = "test-campaign-id"

            # Test continues as normal...
            test_data = {
                "character": "Astarion who ascended in BG3",
                "setting": "Baldur's Gate",
                "title": "Test Campaign",
                "selected_prompts": ["mechanics"],
                "custom_options": [],
            }

            response = self.client.post(
                "/api/campaigns",
                data=json.dumps(test_data),
                content_type="application/json",
                headers={
                    "X-Test-Bypass-Auth": "true",
                    "X-Test-User-ID": "test-user-123",
                },
            )

            assert response.status_code != 400


# ============================================================================
# AFTER: Dual-Mode Test with Service Provider
# ============================================================================


class ModernCharacterTestAfter(BaseTestCase):
    """Example of modernized test that works with both mock and real services."""

    def setUp(self):
        """Setup test client and services"""
        super().setUp()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_api_accepts_character_setting_params_new_way(self):
        """Test that /api/campaigns accepts character and setting parameters - NEW WAY"""

        # AFTER: Use service provider - works with mock OR real services
        if not self.is_real:
            # Only patch when using mock mode
            with (
                patch("main.gemini_service", self.gemini),
                patch("main.firestore_service", self.firestore),
                patch("main.firebase_admin.auth", self.auth),
            ):
                self._run_character_setting_test()
        else:
            # Real mode - no patching needed, services are real
            self._run_character_setting_test()

    def _run_character_setting_test(self):
        """Common test logic that works with both mock and real services."""
        test_data = {
            "character": "Astarion who ascended in BG3",
            "setting": "Baldur's Gate",
            "title": "Test Campaign",
            "selected_prompts": ["mechanics"],
            "custom_options": [],
        }

        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(test_data),
            content_type="application/json",
            headers={"X-Test-Bypass-Auth": "true", "X-Test-User-ID": "test-user-123"},
        )

        assert response.status_code != 400

        if self.is_real:
            print("✅ Test passed with REAL services")
        else:
            print("✅ Test passed with MOCK services")


# ============================================================================
# PYTEST STYLE EXAMPLES
# ============================================================================


def test_character_creation_pytest_old():
    """BEFORE: Pytest test with manual mocking."""

    with patch("main.gemini_service") as mock_gemini:
        mock_gemini.generate_character.return_value = {"name": "Test Character"}
        # Test logic...
        assert True  # Placeholder


def test_character_creation_pytest_new(service_provider):
    """AFTER: Pytest test with service provider fixture."""

    gemini = service_provider.get_gemini()

    # This works with both mock and real services
    result = gemini.generate_character({"class": "fighter"})

    if service_provider.is_real_service:
        # Real service - validate actual response structure
        assert "name" in result
        assert "class" in result
    else:
        # Mock service - validate mock behavior
        assert result is not None


# ============================================================================
# GRADUAL MIGRATION PATTERNS
# ============================================================================


class GradualMigrationExample:
    """Shows how to gradually migrate existing tests."""

    def setup_method(self):
        """Original setup method - unchanged."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_legacy_with_compatibility_helper(self):
        """Existing test with minimal changes using compatibility helper."""

        # STEP 1: Add this single line to existing tests
        from testing_framework.fixtures import get_test_client_for_mode

        services = get_test_client_for_mode()

        try:
            # STEP 2: Replace manual patches with service provider
            if not services["is_real"]:
                # Only patch in mock mode
                with patch("main.firestore_service", services["firestore"]):
                    self._run_existing_test_logic()
            else:
                # Real mode - no patches needed
                self._run_existing_test_logic()
        finally:
            # STEP 3: Add cleanup
            services["provider"].cleanup()

    def _run_existing_test_logic(self):
        """Existing test logic - unchanged."""
        # Original test code goes here


# ============================================================================
# COMPATIBILITY LAYER EXAMPLE
# ============================================================================


class BackwardsCompatibleTest:
    """Shows how to make existing tests work with minimal changes."""

    def setup_method(self):
        """Setup with backwards compatibility."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Add compatibility layer
        from testing_framework.fixtures import get_test_client_for_mode

        services = get_test_client_for_mode()

        # Existing tests expect these attributes
        self.mock_firestore = services["firestore"]
        self.mock_gemini = services["gemini"]
        self.mock_auth = services["auth"]
        self._provider = services["provider"]  # For cleanup

    def teardown_method(self):
        """Cleanup resources."""
        if hasattr(self, "_provider"):
            self._provider.cleanup()

    def test_existing_code_unchanged(self):
        """Existing test code works without modification."""

        # This code doesn't need to change - it will work with
        # either mock or real services transparently
        result = self.mock_firestore.get_document("test/doc")
        assert result is not None


# ============================================================================
# REAL MODE SAFETY EXAMPLES
# ============================================================================


class RealModeSafetyExample(BaseTestCase):
    """Examples of safety patterns for real mode tests."""

    def test_with_resource_limits(self):
        """Test that respects resource limits in real mode."""

        if self.is_real:
            # Real mode - limit API calls
            max_calls = 3
            call_count = 0

            for i in range(max_calls):
                result = self.gemini.generate_simple_response("test prompt")
                call_count += 1
                assert result is not None

            print(f"Real mode test completed with {call_count} API calls")
        else:
            # Mock mode - no limits needed
            for i in range(10):  # Can test more iterations
                result = self.gemini.generate_simple_response("test prompt")
                assert result is not None

    def test_with_isolation(self):
        """Test with proper isolation for real services."""

        if self.is_real:
            # Real mode - use test-specific prefixes
            test_collection = f"test_{self._testMethodName}_{os.getpid()}"
            doc_ref = self.firestore.collection(test_collection).document("test_doc")
        else:
            # Mock mode - normal collection names
            doc_ref = self.firestore.collection("test").document("test_doc")

        # Test logic works the same way
        doc_ref.set({"test": True})
        result = doc_ref.get()
        assert result.exists
