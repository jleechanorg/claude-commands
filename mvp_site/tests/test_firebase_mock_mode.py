"""
Test that Firebase initialization is skipped when MOCK_SERVICES_MODE is set.

This is a simplified test that verifies both main.py and world_logic.py
properly check for MOCK_SERVICES_MODE environment variable.
"""

import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add tests directory to path for imports when run as standalone script
tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

# Import proper fakes library


class TestFirebaseMockMode(unittest.TestCase):
    """Test Firebase initialization with MOCK_SERVICES_MODE."""

    def test_main_initializes_firebase_regardless_of_mock_mode(self):
        """
        Test that main.py initializes Firebase regardless of MOCK_SERVICES_MODE (testing mode removed).
        """
        # Save original environment
        original_testing = os.environ.get("TESTING_AUTH_BYPASS")
        original_mock = os.environ.get("MOCK_SERVICES_MODE")

        try:
            # Set up CI-like environment
            if "TESTING_AUTH_BYPASS" in os.environ:
                del os.environ["TESTING_AUTH_BYPASS"]
            os.environ["MOCK_SERVICES_MODE"] = "true"

            # Mock firebase_admin to control init path
            mock_firebase = MagicMock()
            mock_firebase.auth = MagicMock()
            mock_firebase.get_app = MagicMock(side_effect=ValueError("No Firebase app"))
            mock_firebase.initialize_app = MagicMock(return_value=MagicMock(name="app"))

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
                "logging_util": mock_logging_util,
                "mvp_site.logging_util": mock_logging_util,
                # Fallbacks for package imports:
                "constants": MagicMock(),
                "custom_types": MagicMock(),
                "mcp_client": MagicMock(),
                "firestore_service": MagicMock(),
                "mvp_site.constants": MagicMock(),
                "mvp_site.custom_types": MagicMock(),
                "mvp_site.mcp_client": MagicMock(),
                "mvp_site.firestore_service": MagicMock(),
            }

            # firebase_utils removed - Firebase now always initializes

            with patch.dict("sys.modules", mock_modules):
                # Clear any cached imports
                for mod in ("mvp_site.main", "main"):
                    if mod in sys.modules:
                        del sys.modules[mod]
                importlib.invalidate_caches()

                # Import main - should initialize Firebase regardless of MOCK_SERVICES_MODE
                importlib.import_module("main")

                # Verify Firebase WAS initialized (testing mode removed)
                # May be called multiple times if multiple modules initialize Firebase
                mock_firebase.initialize_app.assert_called()

        finally:
            # Restore environment
            if original_testing is not None:
                os.environ["TESTING_AUTH_BYPASS"] = original_testing
            elif "TESTING_AUTH_BYPASS" in os.environ:
                del os.environ["TESTING_AUTH_BYPASS"]

            if original_mock is not None:
                os.environ["MOCK_SERVICES_MODE"] = original_mock
            elif "MOCK_SERVICES_MODE" in os.environ:
                del os.environ["MOCK_SERVICES_MODE"]

            # Clean up any test imports from sys.modules to avoid interference
            if "main" in sys.modules:
                del sys.modules["main"]

    def test_world_logic_initializes_firebase_regardless_of_mock_mode(self):
        """
        Test that world_logic.py initializes Firebase regardless of MOCK_SERVICES_MODE (testing mode removed).
        """
        # Save original environment
        original_testing = os.environ.get("TESTING_AUTH_BYPASS")
        original_mock = os.environ.get("MOCK_SERVICES_MODE")

        try:
            # Set up CI-like environment
            if "TESTING_AUTH_BYPASS" in os.environ:
                del os.environ["TESTING_AUTH_BYPASS"]
            os.environ["MOCK_SERVICES_MODE"] = "true"

            # Mock firebase_admin to control init path
            mock_firebase = MagicMock()
            mock_firebase.auth = MagicMock()
            mock_firebase.get_app = MagicMock(side_effect=ValueError("No Firebase app"))
            mock_firebase.initialize_app = MagicMock(return_value=MagicMock(name="app"))

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
                "logging_util": mock_logging_util,
                "mvp_site.logging_util": mock_logging_util,
                # Fallbacks for package imports:
                "constants": MagicMock(),
                "mvp_site.constants": MagicMock(),
                "custom_types": MagicMock(),
                "mvp_site.custom_types": MagicMock(),
                "document_generator": MagicMock(),
                "mvp_site.document_generator": MagicMock(),
                "structured_fields_utils": MagicMock(),
                "mvp_site.structured_fields_utils": MagicMock(),
                "debug_hybrid_system": MagicMock(),
                "mvp_site.debug_hybrid_system": MagicMock(),
                "firestore_service": MagicMock(),
                "mvp_site.firestore_service": MagicMock(),
                "llm_service": MagicMock(),
                "mvp_site.llm_service": MagicMock(),
                "game_state": MagicMock(),
                "mvp_site.game_state": MagicMock(),
            }

            # firebase_utils removed - Firebase now always initializes

            with patch.dict("sys.modules", mocks):
                # Clear any cached imports
                for mod in ("mvp_site.world_logic", "world_logic"):
                    if mod in sys.modules:
                        del sys.modules[mod]
                importlib.invalidate_caches()

                # Import world_logic - should initialize Firebase regardless of MOCK_SERVICES_MODE
                importlib.import_module("world_logic")

                # Verify Firebase WAS initialized (testing mode removed)
                # May be called multiple times if multiple modules initialize Firebase
                mock_firebase.initialize_app.assert_called()

        finally:
            # Restore environment
            if original_testing is not None:
                os.environ["TESTING_AUTH_BYPASS"] = original_testing
            elif "TESTING_AUTH_BYPASS" in os.environ:
                del os.environ["TESTING_AUTH_BYPASS"]

            if original_mock is not None:
                os.environ["MOCK_SERVICES_MODE"] = original_mock
            elif "MOCK_SERVICES_MODE" in os.environ:
                del os.environ["MOCK_SERVICES_MODE"]

            # Clean up any test imports from sys.modules to avoid interference
            if "world_logic" in sys.modules:
                del sys.modules["world_logic"]


if __name__ == "__main__":
    print("🟢 GREEN PHASE: Testing MOCK_SERVICES_MODE support...")
    print(
        f"Environment: TESTING_AUTH_BYPASS={os.environ.get('TESTING_AUTH_BYPASS', 'NOT SET')}, "
        f"MOCK_SERVICES_MODE={os.environ.get('MOCK_SERVICES_MODE', 'NOT SET')}"
    )

    unittest.main()
