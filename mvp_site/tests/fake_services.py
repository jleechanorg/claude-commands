"""
Unified fake services for testing WorldArchitect.AI.
Provides a single point to configure all fake services instead of complex mocking.
"""

import os
import sys
from typing import Dict, Any, Optional
from unittest.mock import patch

# Import our fake implementations
from fake_firestore import FakeFirestoreClient, FakeFirestoreDocument, FakeFirestoreCollection
from fake_gemini import FakeGeminiClient, FakeGenerativeModel, create_fake_gemini_client
from fake_auth import FakeFirebaseAuth, FakeUserRecord, FakeDecodedToken


class FakeServiceManager:
    """Manages all fake services for testing."""
    
    def __init__(self):
        self.firestore = FakeFirestoreClient()
        self.auth = FakeFirebaseAuth()
        self.gemini_client = create_fake_gemini_client()
        self._patches = []
        self._original_env = {}
    
    def setup_environment(self):
        """Set up test environment variables."""
        test_env = {
            'TESTING': 'true',
            'GEMINI_API_KEY': 'fake-api-key',
            'FIREBASE_CREDENTIALS': 'fake-credentials'
        }
        
        for key, value in test_env.items():
            self._original_env[key] = os.environ.get(key)
            os.environ[key] = value
    
    def restore_environment(self):
        """Restore original environment variables."""
        for key, original_value in self._original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        self._original_env.clear()
    
    def start_patches(self):
        """Start all service patches."""
        try:
            # Patch Firebase Admin - handle missing modules gracefully
            firebase_patch = patch('firebase_admin.firestore.client', return_value=self.firestore)
            
            # Create auth mock that matches the interface
            auth_mock = type('AuthMock', (), {
                'verify_id_token': self.auth.verify_id_token,
                'get_user': self.auth.get_user,
                'create_user': self.auth.create_user,
                'update_user': self.auth.update_user,
                'delete_user': self.auth.delete_user
            })()
            
            auth_patch = patch('firebase_admin.auth', auth_mock)
            
            # Patch Gemini Client - handle missing modules gracefully  
            genai_client_patch = patch('google.genai.Client', return_value=self.gemini_client)
            
            # Start patches
            self._patches = [
                firebase_patch.start(),
                auth_patch.start(), 
                genai_client_patch.start()
            ]
        except ImportError:
            # Modules not available - create mock modules
            self._setup_mock_modules()
            
        return self
    
    def _setup_mock_modules(self):
        """Set up mock modules when real ones aren't available."""
        import sys
        from unittest.mock import MagicMock
        
        # Store original modules for cleanup
        self._original_modules = {}
        modules_to_mock = [
            'firebase_admin',
            'firebase_admin.firestore', 
            'firebase_admin.auth',
            'google',
            'google.genai'
        ]
        
        for module_name in modules_to_mock:
            if module_name in sys.modules:
                self._original_modules[module_name] = sys.modules[module_name]
        
        # Create mock firebase_admin
        mock_firebase_admin = MagicMock()
        mock_firestore = MagicMock()
        mock_auth = MagicMock()
        
        # Configure mocks to use our fakes
        mock_firestore.client.return_value = self.firestore
        mock_auth.verify_id_token = self.auth.verify_id_token
        mock_auth.get_user = self.auth.get_user
        
        # Set up module mocks
        sys.modules['firebase_admin'] = mock_firebase_admin
        sys.modules['firebase_admin.firestore'] = mock_firestore
        sys.modules['firebase_admin.auth'] = mock_auth
        
        # Create mock google.genai
        mock_genai = MagicMock()
        mock_genai.Client.return_value = self.gemini_client
        sys.modules['google'] = MagicMock()
        sys.modules['google.genai'] = mock_genai
        
        self._patches = []  # No patches needed when using module mocks
    
    def stop_patches(self):
        """Stop all service patches."""
        for patcher in self._patches:
            try:
                if hasattr(patcher, 'stop'):
                    patcher.stop()
            except (RuntimeError, AttributeError):
                pass  # Already stopped or not a patcher
        self._patches.clear()
        
        # Restore original modules if we mocked them
        if hasattr(self, '_original_modules'):
            import sys
            for module_name, original_module in self._original_modules.items():
                sys.modules[module_name] = original_module
            self._original_modules.clear()
    
    def __enter__(self):
        """Context manager entry."""
        self.setup_environment()
        self.start_patches()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_patches()
        self.restore_environment()
    
    def reset(self):
        """Reset all services to clean state."""
        self.firestore = FakeFirestoreClient()
        self.auth = FakeFirebaseAuth()
        self.gemini_client = create_fake_gemini_client()
    
    def setup_campaign(self, campaign_id: str = "test-campaign", user_id: str = "test-user-123") -> Dict[str, Any]:
        """Set up a test campaign with realistic data."""
        campaign_data = {
            "id": campaign_id,
            "title": "Test Adventure",
            "character": "Test Hero",
            "setting": "Fantasy Realm",
            "description": "A test campaign for automated testing",
            "user_id": user_id,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "status": "active"
        }
        
        # Set up in Firestore
        campaign_doc = self.firestore.collection("campaigns").document(campaign_id)
        campaign_doc.set(campaign_data)
        
        # Set up story context
        story_data = {
            "narrative": "Welcome to the Fantasy Realm, Test Hero. Your adventure begins...",
            "scene_number": 1,
            "location": "Starting Village",
            "npcs": ["Village Elder", "Merchant"],
            "objects": ["sword", "shield", "potion"],
            "state_updates": {
                "health": 100,
                "level": 1,
                "experience": 0
            }
        }
        
        story_doc = campaign_doc.collection("story").document("current")
        story_doc.set(story_data)
        
        return campaign_data
    
    def setup_user(self, user_id: str = "test-user-123", email: str = "test@example.com") -> FakeUserRecord:
        """Set up a test user."""
        try:
            return self.auth.get_user(user_id)
        except:
            return self.auth.create_user(uid=user_id, email=email, display_name="Test User")
    
    def create_test_token(self, user_id: str = "test-user-123") -> str:
        """Create a test authentication token."""
        self.setup_user(user_id)
        return self.auth.create_custom_token(user_id)


class TestCase:
    """Base test case with fake services pre-configured."""
    
    def setUp(self):
        """Set up fake services for each test."""
        self.services = FakeServiceManager()
        self.services.setup_environment()
        self.services.start_patches()
        
        # Common test data
        self.test_user_id = "test-user-123"
        self.test_campaign_id = "test-campaign"
        self.services.setup_user(self.test_user_id)
        self.services.setup_campaign(self.test_campaign_id, self.test_user_id)
    
    def tearDown(self):
        """Clean up fake services after each test."""
        self.services.stop_patches()
        self.services.restore_environment()


# Convenience functions for quick test setup
def with_fake_services():
    """Decorator to automatically set up fake services for a test."""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            with FakeServiceManager() as services:
                # Add services to test context
                if args and hasattr(args[0], '__dict__'):
                    args[0].services = services
                return test_func(*args, **kwargs)
        return wrapper
    return decorator


def create_test_app():
    """Create a test Flask app with fake services configured."""
    from main import create_app
    
    # Set up fake services
    services = FakeServiceManager()
    services.setup_environment()
    services.start_patches()
    
    # Create app
    app = create_app()
    app.config['TESTING'] = True
    
    # Store services on app for cleanup
    app.fake_services = services
    
    return app


def get_test_headers(user_id: str = "test-user-123") -> Dict[str, str]:
    """Get test headers for bypassing authentication."""
    from main import HEADER_TEST_BYPASS, HEADER_TEST_USER_ID
    
    return {
        HEADER_TEST_BYPASS: 'true',
        HEADER_TEST_USER_ID: user_id
    }


# Example usage patterns for migration from mocks:

# OLD MOCK PATTERN:
# @patch('firebase_admin.firestore.client')
# @patch('google.genai.Client') 
# def test_something(self, mock_genai, mock_firestore):
#     mock_firestore.return_value = MagicMock()
#     mock_genai.return_value = MagicMock()
#     # Complex mock setup...

# NEW FAKE PATTERN:
# @with_fake_services()
# def test_something(self):
#     # Services automatically available
#     campaign = self.services.setup_campaign()
#     # Test with realistic data...