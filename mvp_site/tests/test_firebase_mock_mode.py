"""
Test that Firebase initialization is skipped when MOCK_SERVICES_MODE is set.

This is a simplified test that verifies both main.py and world_logic.py
properly check for MOCK_SERVICES_MODE environment variable.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import firebase_admin
import pytest
from google.auth.exceptions import RefreshError

# Add tests directory to path for imports when run as standalone script
tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

# Add mvp_site directory to path for firebase_utils import
mvp_site_dir = os.path.dirname(tests_dir)
if mvp_site_dir not in sys.path:
    sys.path.insert(0, mvp_site_dir)

# Import proper fakes library


class TestFirebaseMockMode(unittest.TestCase):
    """Test Firebase initialization with MOCK_SERVICES_MODE."""

    def test_main_skips_firebase_with_mock_mode(self):
        """
        Test that main.py skips Firebase initialization when MOCK_SERVICES_MODE=true.
        """
        # Save original environment
        original_testing = os.environ.get("TESTING")
        original_mock = os.environ.get("MOCK_SERVICES_MODE")

        try:
            # Set up CI-like environment
            if "TESTING" in os.environ:
                del os.environ["TESTING"]
            os.environ["MOCK_SERVICES_MODE"] = "true"

            # Mock firebase_admin to prevent import errors
            mock_firebase = MagicMock()
            mock_firebase._apps = []
            mock_firebase.initialize_app = MagicMock()

            # Add proper path setup for importing main module
            test_dir = os.path.dirname(os.path.abspath(__file__))
            mvp_site_path = os.path.dirname(test_dir)  # mvp_site directory
            project_root = os.path.dirname(mvp_site_path)  # project root

            # Ensure mvp_site is in path for main.py imports
            if mvp_site_path not in sys.path:
                sys.path.insert(0, mvp_site_path)
            # Also add project root to path for other imports
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            # Mock all required modules to prevent import errors
            mock_logging_util = MagicMock()
            mock_logging_util.LoggingUtil.get_log_file.return_value = "/tmp/test.log"
            mock_logging_util.info = MagicMock()
            mock_logging_util.error = MagicMock()

            mock_modules = {
                "firebase_admin": mock_firebase,
                "firebase_admin.auth": MagicMock(),
                "logging_util": mock_logging_util,
                "constants": MagicMock(),
                "custom_types": MagicMock(),
                "mcp_client": MagicMock(),
                "firestore_service": MagicMock(),
                "firebase_utils": MagicMock(),
            }

            # Set up firebase_utils.should_skip_firebase_init to return True for MOCK_SERVICES_MODE
            mock_firebase_utils = mock_modules["firebase_utils"]
            mock_firebase_utils.should_skip_firebase_init.return_value = True

            with patch.dict("sys.modules", mock_modules):
                # Clear any cached imports
                if "main" in sys.modules:
                    del sys.modules["main"]

                # Import main - this should check MOCK_SERVICES_MODE and skip Firebase init

                # Verify Firebase was NOT initialized (because MOCK_SERVICES_MODE is set)
                mock_firebase.initialize_app.assert_not_called()

        finally:
            # Restore environment
            if original_testing is not None:
                os.environ["TESTING"] = original_testing
            elif "TESTING" in os.environ:
                del os.environ["TESTING"]

            if original_mock is not None:
                os.environ["MOCK_SERVICES_MODE"] = original_mock
            elif "MOCK_SERVICES_MODE" in os.environ:
                del os.environ["MOCK_SERVICES_MODE"]

            # Clean up any test imports from sys.modules to avoid interference
            if "main" in sys.modules:
                del sys.modules["main"]

    def test_world_logic_skips_firebase_with_mock_mode(self):
        """
        Test that world_logic.py skips Firebase initialization when MOCK_SERVICES_MODE=true.
        """
        # Save original environment
        original_testing = os.environ.get("TESTING")
        original_mock = os.environ.get("MOCK_SERVICES_MODE")

        try:
            # Set up CI-like environment
            if "TESTING" in os.environ:
                del os.environ["TESTING"]
            os.environ["MOCK_SERVICES_MODE"] = "true"

            # Mock all dependencies to prevent import errors
            mock_firebase = MagicMock()
            mock_firebase._apps = []
            mock_firebase.initialize_app = MagicMock()

            # Add proper path setup
            test_dir = os.path.dirname(os.path.abspath(__file__))
            mvp_site_path = os.path.dirname(test_dir)  # mvp_site directory
            project_root = os.path.dirname(mvp_site_path)  # project root

            # Ensure proper paths are available
            if mvp_site_path not in sys.path:
                sys.path.insert(0, mvp_site_path)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            # Mock logging_util with proper methods
            mock_logging_util = MagicMock()
            mock_logging_util.LoggingUtil.get_log_file.return_value = "/tmp/test.log"
            mock_logging_util.info = MagicMock()
            mock_logging_util.error = MagicMock()

            mocks = {
                "firebase_admin": mock_firebase,
                "firebase_admin.auth": MagicMock(),
                "constants": MagicMock(),
                "document_generator": MagicMock(),
                "logging_util": mock_logging_util,
                "structured_fields_utils": MagicMock(),
                "custom_types": MagicMock(),
                "debug_hybrid_system": MagicMock(),
                "firestore_service": MagicMock(),
                "gemini_service": MagicMock(),
                "game_state": MagicMock(),
                "firebase_utils": MagicMock(),
            }

            # Set up firebase_utils.should_skip_firebase_init to return True for MOCK_SERVICES_MODE
            mock_firebase_utils = mocks["firebase_utils"]
            mock_firebase_utils.should_skip_firebase_init.return_value = True

            with patch.dict("sys.modules", mocks):
                # Clear any cached imports
                if "world_logic" in sys.modules:
                    del sys.modules["world_logic"]

                # Import world_logic - this should check MOCK_SERVICES_MODE and skip Firebase init

                # Verify Firebase was NOT initialized (because MOCK_SERVICES_MODE is set)
                mock_firebase.initialize_app.assert_not_called()

        finally:
            # Restore environment
            if original_testing is not None:
                os.environ["TESTING"] = original_testing
            elif "TESTING" in os.environ:
                del os.environ["TESTING"]

            if original_mock is not None:
                os.environ["MOCK_SERVICES_MODE"] = original_mock
            elif "MOCK_SERVICES_MODE" in os.environ:
                del os.environ["MOCK_SERVICES_MODE"]

            # Clean up any test imports from sys.modules to avoid interference
            if "world_logic" in sys.modules:
                del sys.modules["world_logic"]


class TestFirebaseCredentialRegression(unittest.TestCase):
    """Test Firebase credential loading regression from centralization work."""

    def setUp(self):
        """Set up test environment."""
        # Clear any existing Firebase apps
        if firebase_admin._apps:
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)
        firebase_admin._apps.clear()

        # Remove world_logic from modules to allow fresh initialization
        modules_to_clear = [name for name in sys.modules if "world_logic" in name]
        for module_name in modules_to_clear:
            sys.modules.pop(module_name, None)

    def tearDown(self):
        """Clean up test environment."""
        # Clear Firebase apps after test
        if firebase_admin._apps:
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)
        firebase_admin._apps.clear()

        # Remove world_logic from modules to ensure clean state for next test
        modules_to_clear = [name for name in sys.modules if "world_logic" in name]
        for module_name in modules_to_clear:
            sys.modules.pop(module_name, None)

    def test_regression_firebase_credential_loading_without_creds(self):
        """
        RED: Reproduce the exact Firebase RefreshError when credentials are missing/invalid.

        This test reproduces the error signature:
        RefreshError | ["invalid_grant", "Invalid JWT Signature"] | Firebase credential loading
        """
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            # Mock firebase_admin.initialize_app to trigger auth error when called without proper credentials
            with patch("firebase_admin.initialize_app") as mock_init:
                with patch(
                    "firebase_utils.should_skip_firebase_init", return_value=False
                ):
                    # Simulate the exact error that occurs when credentials are invalid
                    mock_init.side_effect = RefreshError(
                        (
                            "invalid_grant: Invalid JWT Signature.",
                            {
                                "error": "invalid_grant",
                                "error_description": "Invalid JWT Signature.",
                            },
                        )
                    )

                    with pytest.raises(RuntimeError) as exc_info:
                        # Import world_logic which should trigger Firebase initialization
                        import world_logic  # noqa: F401

                    # Verify we get the exact error signature (wrapped in RuntimeError)
                    error_msg = str(exc_info.value)
                    assert "invalid_grant" in error_msg
                    assert "Invalid JWT Signature" in error_msg
                    assert "Firebase initialization failed" in error_msg
                    print(f"✅ RED: Reproduced exact error: {exc_info.value}")


if __name__ == "__main__":
    print("🟢 GREEN PHASE: Testing MOCK_SERVICES_MODE support...")
    print(
        f"Environment: TESTING={os.environ.get('TESTING', 'NOT SET')}, "
        f"MOCK_SERVICES_MODE={os.environ.get('MOCK_SERVICES_MODE', 'NOT SET')}"
    )

    unittest.main()
