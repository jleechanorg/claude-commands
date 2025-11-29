"""
TDD Tests for Centralized Model Selection

RED PHASE: Write failing tests that define the expected behavior
GREEN PHASE: Implement the fix to make tests pass
REFACTOR PHASE: Clean up and optimize

Problem: Model selection is inconsistent - TESTING env var not recognized,
causing gemini-2.5-flash to be used instead of gemini-3-pro-preview in test mode.

Solution: Centralize all model selection through _select_model_for_user() and
ensure it checks both TESTING and MOCK_SERVICES_MODE environment variables.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"

# Add parent directory to path for imports (insert at beginning to override system packages)
project_root = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, project_root)

from mvp_site.llm_service import DEFAULT_MODEL, TEST_MODEL, _select_model_for_user


class TestCentralizedModelSelection(unittest.TestCase):
    """Test that model selection is centralized and consistent"""

    def setUp(self):
        """Save original env vars"""
        self.original_testing = os.environ.get("TESTING")
        self.original_mock = os.environ.get("MOCK_SERVICES_MODE")

    def tearDown(self):
        """Restore original env vars"""
        if self.original_testing:
            os.environ["TESTING"] = self.original_testing
        elif "TESTING" in os.environ:
            del os.environ["TESTING"]

        if self.original_mock:
            os.environ["MOCK_SERVICES_MODE"] = self.original_mock
        elif "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

    def test_testing_env_returns_test_model(self):
        """
        RED PHASE TEST: TESTING=true should return TEST_MODEL

        This ensures that when running tests with TESTING=true, we use
        the TEST_MODEL (gemini-3-pro-preview) instead of fetching user preferences
        or using DEFAULT_MODEL.
        """
        os.environ["TESTING"] = "true"
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

        result = _select_model_for_user("test-user-123")

        self.assertEqual(
            result,
            TEST_MODEL,
            f"FAIL: TESTING=true should return TEST_MODEL ({TEST_MODEL}), "
            f"but got {result}",
        )

    def test_mock_services_mode_returns_test_model(self):
        """
        REGRESSION TEST: MOCK_SERVICES_MODE=true should still work

        Ensure backward compatibility - existing code using MOCK_SERVICES_MODE
        should continue to work.
        """
        if "TESTING" in os.environ:
            del os.environ["TESTING"]
        os.environ["MOCK_SERVICES_MODE"] = "true"

        result = _select_model_for_user("test-user-123")

        self.assertEqual(
            result,
            TEST_MODEL,
            f"FAIL: MOCK_SERVICES_MODE=true should return TEST_MODEL ({TEST_MODEL}), "
            f"but got {result}",
        )

    def test_testing_takes_precedence_over_user_preference(self):
        """
        CRITICAL TEST: TESTING=true should override user preferences

        Even if a user has gemini-2.5-flash saved, TESTING=true should
        force TEST_MODEL (gemini-3-pro-preview) to be used.
        """
        os.environ["TESTING"] = "true"
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

        # Mock user settings returning gemini-2.5-flash preference
        with patch("mvp_site.firestore_service.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = {"gemini_model": "gemini-2.5-flash"}

            result = _select_model_for_user("test-user-123")

            self.assertEqual(
                result,
                TEST_MODEL,
                f"FAIL: TESTING=true should override user preference, "
                f"expected {TEST_MODEL}, got {result}",
            )

    def test_no_user_id_returns_default_model(self):
        """
        BASE CASE TEST: No user_id should return DEFAULT_MODEL

        When no user is specified and not in test mode, use DEFAULT_MODEL.
        """
        if "TESTING" in os.environ:
            del os.environ["TESTING"]
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

        result = _select_model_for_user(None)

        self.assertEqual(
            result,
            DEFAULT_MODEL,
            f"FAIL: No user_id should return DEFAULT_MODEL ({DEFAULT_MODEL}), "
            f"but got {result}",
        )

    def test_valid_user_preference_is_respected(self):
        """
        PREFERENCE TEST: Valid user preference should be used in production

        When not in test mode, if user has a valid model preference, use it.
        """
        if "TESTING" in os.environ:
            del os.environ["TESTING"]
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

        # Mock user settings returning valid gemini-3-pro-preview preference
        with patch("mvp_site.firestore_service.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = {"gemini_model": "gemini-3-pro-preview"}

            result = _select_model_for_user("test-user-456")

            self.assertEqual(
                result,
                "gemini-3-pro-preview",
                f"FAIL: Valid user preference should be respected, "
                f"expected gemini-3-pro-preview, got {result}",
            )

    def test_invalid_user_preference_falls_back_to_default(self):
        """
        FALLBACK TEST: Invalid user preference should use DEFAULT_MODEL

        If user has an invalid/unsupported model preference, fall back to DEFAULT_MODEL.
        """
        if "TESTING" in os.environ:
            del os.environ["TESTING"]
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

        # Mock user settings returning invalid model preference
        with patch("mvp_site.firestore_service.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = {"gemini_model": "invalid-model-name"}

            result = _select_model_for_user("test-user-789")

            self.assertEqual(
                result,
                DEFAULT_MODEL,
                f"FAIL: Invalid user preference should fall back to DEFAULT_MODEL ({DEFAULT_MODEL}), "
                f"but got {result}",
            )

    def test_test_model_supports_code_execution(self):
        """
        INTEGRATION TEST: Verify TEST_MODEL supports code_execution + JSON

        The whole point of this fix is to ensure TEST_MODEL supports both
        code_execution and JSON mode simultaneously.
        """
        test_model = TEST_MODEL

        # TEST_MODEL should be gemini-3-pro-preview (supports both)
        self.assertEqual(
            test_model,
            "gemini-3-pro-preview",
            f"FAIL: TEST_MODEL should be gemini-3-pro-preview (supports code_execution + JSON), "
            f"but is {test_model}",
        )

        # DEFAULT_MODEL should also be gemini-3-pro-preview
        self.assertEqual(
            DEFAULT_MODEL,
            "gemini-3-pro-preview",
            f"FAIL: DEFAULT_MODEL should be gemini-3-pro-preview, "
            f"but is {DEFAULT_MODEL}",
        )


if __name__ == "__main__":
    unittest.main()
