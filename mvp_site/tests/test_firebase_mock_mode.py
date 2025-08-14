"""
Test that Firebase initialization is skipped when MOCK_SERVICES_MODE is set.

This is a simplified test that verifies both main.py and world_logic.py
properly check for MOCK_SERVICES_MODE environment variable.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch


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
            
            # Add mvp_site to path
            mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if mvp_site_path not in sys.path:
                sys.path.insert(0, mvp_site_path)
            
            with patch.dict('sys.modules', {'firebase_admin': mock_firebase}):
                # Clear any cached imports
                if 'main' in sys.modules:
                    del sys.modules['main']
                
                # Import main - this should check MOCK_SERVICES_MODE and skip Firebase init
                import main
                
                # Verify Firebase was NOT initialized
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
            
            mocks = {
                'firebase_admin': mock_firebase,
                'constants': MagicMock(),
                'document_generator': MagicMock(),
                'logging_util': MagicMock(),
                'structured_fields_utils': MagicMock(),
                'custom_types': MagicMock(),
                'debug_hybrid_system': MagicMock(),
                'firestore_service': MagicMock(),
                'gemini_service': MagicMock(),
                'game_state': MagicMock(),
            }
            
            # Add mvp_site to path
            mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if mvp_site_path not in sys.path:
                sys.path.insert(0, mvp_site_path)
            
            with patch.dict('sys.modules', mocks):
                # Clear any cached imports
                if 'world_logic' in sys.modules:
                    del sys.modules['world_logic']
                
                # Import world_logic - this should check MOCK_SERVICES_MODE and skip Firebase init
                import world_logic
                
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


if __name__ == "__main__":
    print("🟢 GREEN PHASE: Testing MOCK_SERVICES_MODE support...")
    print(f"Environment: TESTING={os.environ.get('TESTING', 'NOT SET')}, "
          f"MOCK_SERVICES_MODE={os.environ.get('MOCK_SERVICES_MODE', 'NOT SET')}")
    
    unittest.main()