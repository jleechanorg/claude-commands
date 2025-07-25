#!/usr/bin/env python3
"""
Test granular mock control for Firebase and Gemini services.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGranularMockControl(unittest.TestCase):
    def setUp(self):
        """Save original environment."""
        self.original_env = {}
        for key in ["USE_MOCKS", "USE_MOCK_FIREBASE", "USE_MOCK_GEMINI", "TESTING"]:
            self.original_env[key] = os.environ.get(key)

    def tearDown(self):
        """Restore original environment."""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _reload_main_with_env(self, **env_vars):
        """
        Reload the main module with specific environment variables.

        WARNING: This method clears the `sys.modules` cache for specific modules
        and re-imports them, which can lead to side effects such as breaking
        dependencies or causing inconsistent module states. Use this method
        only in controlled testing environments where module reloading is
        necessary to simulate different configurations.

        Parameters:
            env_vars (dict): Environment variables to set before reloading the main module.
                            Keys are variable names, and values are their corresponding values.
                            Use `None` to unset a variable.

        Returns:
            module: The reloaded `main` module.
        """
        # Clear module cache for main and services
        for module in [
            "main",
            "gemini_service",
            "firestore_service",
            "mocks.mock_gemini_service_wrapper",
            "mocks.mock_firestore_service_wrapper",
        ]:
            if module in sys.modules:
                del sys.modules[module]

        # Set environment variables
        os.environ["TESTING"] = "true"
        for key, value in env_vars.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

        # Import main to trigger conditional imports
        import main

        return main

    def test_mock_gemini_real_firebase(self):
        """Test mocking only Gemini while using real Firebase."""
        main = self._reload_main_with_env(
            USE_MOCK_GEMINI="true", USE_MOCK_FIREBASE="false"
        )

        # Check service types
        self.assertEqual(
            main.gemini_service.__name__,
            "mocks.mock_gemini_service_wrapper",
            "Gemini should be mocked",
        )
        self.assertEqual(
            main.firestore_service.__name__,
            "firestore_service",
            "Firebase should be real",
        )

        # Check app config
        app = main.create_app()
        self.assertTrue(app.config["USE_MOCK_GEMINI"])
        self.assertFalse(app.config["USE_MOCK_FIREBASE"])

    def test_real_gemini_mock_firebase(self):
        """Test using real Gemini while mocking Firebase."""
        main = self._reload_main_with_env(
            USE_MOCK_GEMINI="false", USE_MOCK_FIREBASE="true"
        )

        # Check service types
        self.assertEqual(
            main.gemini_service.__name__, "gemini_service", "Gemini should be real"
        )
        self.assertEqual(
            main.firestore_service.__name__,
            "mocks.mock_firestore_service_wrapper",
            "Firebase should be mocked",
        )

    def test_legacy_use_mocks_true(self):
        """Test that USE_MOCKS=true still mocks both services."""
        main = self._reload_main_with_env(
            USE_MOCKS="true", USE_MOCK_GEMINI=None, USE_MOCK_FIREBASE=None
        )

        # Both should be mocked
        self.assertEqual(
            main.gemini_service.__name__, "mocks.mock_gemini_service_wrapper"
        )
        self.assertEqual(
            main.firestore_service.__name__, "mocks.mock_firestore_service_wrapper"
        )

    def test_individual_flags_override_use_mocks(self):
        """Test that individual flags override USE_MOCKS."""
        main = self._reload_main_with_env(
            USE_MOCKS="true",
            USE_MOCK_GEMINI="false",  # Override to use real
            USE_MOCK_FIREBASE="true",
        )

        # Gemini should be real despite USE_MOCKS=true
        self.assertEqual(
            main.gemini_service.__name__,
            "gemini_service",
            "Individual flag should override USE_MOCKS",
        )
        # Firebase should still be mocked
        self.assertEqual(
            main.firestore_service.__name__, "mocks.mock_firestore_service_wrapper"
        )


if __name__ == "__main__":
    unittest.main()
