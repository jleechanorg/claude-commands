"""
RED-GREEN test to reproduce CI Firebase initialization failure.

This test reproduces the exact CI environment where:
- MOCK_SERVICES_MODE=true (what CI sets)
- TESTING is NOT set (CI doesn't set this in env vars)
- world_logic.py tries to initialize Firebase and fails
"""

import os
import sys
import unittest

# Save original environment
original_testing = os.environ.get("TESTING")
original_mock_mode = os.environ.get("MOCK_SERVICES_MODE")


class TestCIFirebaseInitialization(unittest.TestCase):
    """Test Firebase initialization behavior in CI environment."""

    def setUp(self):
        """Set up CI-like environment."""
        # Clear any existing module imports that might have cached state
        modules_to_clear = [
            # Bare names (when sys.path includes mvp_site/)
            "world_logic",
            "main",
            "firebase_admin",
            "firestore_service",
            "gemini_service",
            "logging_util",
            "constants",
            "document_generator",
            "structured_fields_utils",
            "custom_types",
            "debug_hybrid_system",
            "debug_mode_parser",
            "game_state",
            # Fully-qualified (when importing as mvp_site.*)
            "mvp_site.world_logic",
            "mvp_site.main",
            "mvp_site.firestore_service",
            "mvp_site.gemini_service",
            "mvp_site.logging_util",
            "mvp_site.constants",
            "mvp_site.document_generator",
            "mvp_site.structured_fields_utils",
            "mvp_site.custom_types",
            "mvp_site.debug_hybrid_system",
            "mvp_site.game_state",
        ]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

    def test_ci_environment_firebase_initialization_failure(self):
        """
        RED: Reproduce the CI Firebase initialization failure.
        
        In CI:
        - MOCK_SERVICES_MODE=true is set
        - TESTING is not set in environment (only in command)
        - world_logic.py only checks TESTING, not MOCK_SERVICES_MODE
        - This causes Firebase initialization to be attempted and fail
        """
        # Set up CI-like environment
        if "TESTING" in os.environ:
            del os.environ["TESTING"]
        os.environ["MOCK_SERVICES_MODE"] = "true"
        
        # Add mvp_site to path
        mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__ if '__file__' in globals() else 'tests/test_ci_firebase_init_redgreen.py')))
        if mvp_site_path not in sys.path:
            sys.path.insert(0, mvp_site_path)
        
        # This should fail in RED phase because world_logic.py will try to initialize Firebase
        # since it only checks TESTING, not MOCK_SERVICES_MODE
        try:
            import world_logic
            # If we get here without error, the test PASSES (which means the fix is applied)
            self.assertTrue(True, "world_logic imported successfully without Firebase error")
        except ValueError as e:
            if "Firebase app does not exist" in str(e):
                # This is the expected RED phase failure - same as CI
                self.fail(f"RED PHASE: Firebase initialization error as expected in CI: {e}")
            else:
                # Some other ValueError - re-raise it
                raise
        except Exception as e:
            # Unexpected error
            self.fail(f"Unexpected error: {type(e).__name__}: {e}")

    def tearDown(self):
        """Restore original environment."""
        # Restore original environment
        if original_testing is not None:
            os.environ["TESTING"] = original_testing
        elif "TESTING" in os.environ:
            del os.environ["TESTING"]
            
        if original_mock_mode is not None:
            os.environ["MOCK_SERVICES_MODE"] = original_mock_mode
        elif "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]


if __name__ == "__main__":
    # Run without TESTING=true to simulate CI environment
    print("🔴 RED PHASE: Testing CI Firebase initialization issue...")
    print(f"Environment: TESTING={os.environ.get('TESTING', 'NOT SET')}, "
          f"MOCK_SERVICES_MODE={os.environ.get('MOCK_SERVICES_MODE', 'NOT SET')}")
    
    unittest.main()