"""
TDD Tests for Centralized Model Selection

Tests ensure provider and model selection respects user settings
and falls back to defaults appropriately.
"""

# ruff: noqa: E402, PT009

import os
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path for imports (insert at beginning to override system packages)
project_root = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, project_root)

from mvp_site.llm_service import DEFAULT_MODEL, TEST_MODEL, _select_model_for_user


class TestCentralizedModelSelection(unittest.TestCase):
    """Test that model selection is centralized and consistent"""

    def test_no_user_id_returns_default_model(self):
        """
        BASE CASE TEST: No user_id should return DEFAULT_MODEL

        When no user is specified, use DEFAULT_MODEL.
        """
        result = _select_model_for_user(None)

        self.assertEqual(
            result,
            DEFAULT_MODEL,
            f"FAIL: No user_id should return DEFAULT_MODEL ({DEFAULT_MODEL}), "
            f"but got {result}",
        )

    def test_valid_user_preference_is_respected(self):
        """
        PREFERENCE TEST: Valid user preference should be used

        When user has a valid model preference, use it.
        Note: Must disable ALL test mode environment variables to allow user preferences.
        """
        # Mock user settings returning valid cerebras model preference
        # Disable all three test mode environment variables
        with patch("mvp_site.llm_service.get_user_settings") as mock_get_settings, \
             patch.dict(os.environ, {
                 "TESTING": "false",
                 "MOCK_SERVICES_MODE": "false",
                 "FORCE_TEST_MODEL": "false"
             }):
            mock_get_settings.return_value = {"cerebras_model": "llama-3.3-70b"}

            result = _select_model_for_user("test-user-456")

            self.assertEqual(
                result,
                "llama-3.3-70b",
                f"FAIL: Valid user preference should be respected, "
                f"expected llama-3.3-70b, got {result}",
            )

    def test_invalid_user_preference_falls_back_to_default(self):
        """
        FALLBACK TEST: Invalid user preference should use DEFAULT_MODEL

        If user has an invalid/unsupported model preference, fall back to DEFAULT_MODEL.
        """
        # Mock user settings returning invalid model preference
        with patch("mvp_site.llm_service.get_user_settings") as mock_get_settings, \
             patch.dict(
                 os.environ,
                 {
                     "TESTING": "false",
                     "MOCK_SERVICES_MODE": "false",
                     "FORCE_TEST_MODEL": "false",
                 },
             ):
            mock_get_settings.return_value = {"cerebras_model": "invalid-model-name"}

            result = _select_model_for_user("test-user-789")

            self.assertEqual(
                result,
                DEFAULT_MODEL,
                f"FAIL: Invalid user preference should fall back to DEFAULT_MODEL ({DEFAULT_MODEL}), "
                f"but got {result}",
            )

    def test_test_model_supports_code_execution(self):
        """
        INTEGRATION TEST: Verify TEST_MODEL is set to default Cerebras model

        The TEST_MODEL should match the current DEFAULT_MODEL based on DEFAULT_LLM_PROVIDER.
        """
        test_model = TEST_MODEL

        # TEST_MODEL should be qwen-3-235b-a22b-instruct-2507 (default Cerebras model)
        self.assertEqual(
            test_model,
            "qwen-3-235b-a22b-instruct-2507",
            f"FAIL: TEST_MODEL should be qwen-3-235b-a22b-instruct-2507 (default Cerebras model), "
            f"but is {test_model}",
        )

        # DEFAULT_MODEL should also be qwen-3-235b-a22b-instruct-2507
        self.assertEqual(
            DEFAULT_MODEL,
            "qwen-3-235b-a22b-instruct-2507",
            f"FAIL: DEFAULT_MODEL should be qwen-3-235b-a22b-instruct-2507, "
            f"but is {DEFAULT_MODEL}",
        )

    def test_database_error_falls_back_to_default(self):
        """
        ERROR HANDLING: Database error should fall back to DEFAULT_MODEL
        """
        with patch("mvp_site.llm_service.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = None  # Simulates database error

            result = _select_model_for_user("test-user-error")

            self.assertEqual(
                result,
                DEFAULT_MODEL,
                f"FAIL: Database error should fall back to DEFAULT_MODEL ({DEFAULT_MODEL}), "
                f"but got {result}",
            )


if __name__ == "__main__":
    unittest.main()
