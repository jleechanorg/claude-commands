"""
Unified fake services for testing WorldArchitect.AI.
Provides a single point to configure all fake services instead of complex mocking.
Includes JSON input schema validation support.
"""

import os
import sys

# Add mvp_site to path so 'import main' can find mvp_site/main.py
mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if mvp_site_path not in sys.path:
    sys.path.insert(0, mvp_site_path)

# Import JSON input schema components
from contextlib import suppress
from typing import Any
from unittest.mock import MagicMock, patch

# Import firebase_admin (fail fast if missing)
import firebase_admin.auth

# Import functions from main at module level to avoid inline imports
# Note: HEADER_TEST_BYPASS and HEADER_TEST_USER_ID removed with testing mode deletion
from main import create_app

# Import fake modules (fail fast if missing)
from .fake_auth import FakeFirebaseAuth, FakeUserRecord
from .fake_firestore import FakeFirestoreClient
from .fake_llm import create_fake_llm_client

FIREBASE_ADMIN_AVAILABLE = True

with suppress(ImportError):
    # Legacy json_input_schema imports removed - using LLMRequest now
    pass  # No imports needed - using LLMRequest directly

# Set fallback values for legacy compatibility
JsonInputBuilder = None
JsonInputValidator = None


class FakeServiceManager:
    """Manages all fake services for testing."""

    def __init__(self):
        self.firestore = FakeFirestoreClient()
        self.auth = FakeFirebaseAuth()
        self.gemini_client = create_fake_llm_client()
        self._patches = []
        self._original_env = {}

        # Initialize JSON input components if available
        self.json_builder = JsonInputBuilder() if JsonInputBuilder else None
        self.json_validator = JsonInputValidator() if JsonInputValidator else None

    def setup_environment(self):
        """Set up test environment variables."""
        test_env = {
            "TESTING_AUTH_BYPASS": "true",
            "GEMINI_API_KEY": "fake-api-key",
            "FIREBASE_CREDENTIALS": "fake-credentials",
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
            # Check if firebase_admin.auth module is available
            if not FIREBASE_ADMIN_AVAILABLE:
                # If firebase_admin.auth can't be imported, fall back to mock modules
                self._setup_mock_modules()
                return self

            # Patch Firebase Admin - handle missing modules gracefully
            firebase_patch = patch(
                "firestore_service.get_db", return_value=self.firestore
            )

            # Create auth mock that matches the interface
            auth_mock = type(
                "AuthMock",
                (),
                {
                    "verify_id_token": self.auth.verify_id_token,
                    "get_user": self.auth.get_user,
                    "create_user": self.auth.create_user,
                    "update_user": self.auth.update_user,
                    "delete_user": self.auth.delete_user,
                },
            )()

            auth_patch = patch("firebase_admin.auth", auth_mock)

            # Patch Gemini Client - handle missing modules gracefully
            genai_client_patch = patch(
                "google.genai.Client", return_value=self.gemini_client
            )

            # Start patches and keep patchers for cleanup
            self._patches = [firebase_patch, auth_patch, genai_client_patch]
            for patcher in self._patches:
                patcher.start()
        except ImportError:
            # Modules not available - create mock modules
            self._setup_mock_modules()

        return self

    def _setup_mock_modules(self):
        """Set up mock modules when real ones aren't available."""

        # Store original modules for cleanup
        self._original_modules = {}
        modules_to_mock = [
            "firebase_admin",
            "firebase_admin.firestore",
            "firebase_admin.auth",
            "google",
            "google.genai",
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
        sys.modules["firebase_admin"] = mock_firebase_admin
        sys.modules["firebase_admin.firestore"] = mock_firestore
        sys.modules["firebase_admin.auth"] = mock_auth

        # Create mock google.genai
        mock_genai = MagicMock()
        mock_genai.Client.return_value = self.gemini_client
        sys.modules["google"] = MagicMock()
        sys.modules["google.genai"] = mock_genai

        self._patches = []  # No patches needed when using module mocks

    def stop_patches(self):
        """Stop all service patches."""
        for patcher in self._patches:
            try:
                patcher.stop()
            except (RuntimeError, AttributeError):
                pass  # Already stopped or not a patcher
        self._patches.clear()

        # Restore original modules if we mocked them
        if hasattr(self, "_original_modules"):
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
        self.gemini_client = create_fake_llm_client()

    def create_json_input(self, message_type: str, **kwargs) -> dict:
        """Create structured JSON input for testing.

        Args:
            message_type: Type of message (initial_story, story_continuation, user_input, etc.)
            **kwargs: Additional fields for the JSON input

        Returns:
            Dict representing structured JSON input
        """
        if not self.json_builder:
            # Fallback for when JSON input schema is not available
            return {
                "message_type": message_type,
                "content": kwargs.get("content", ""),
                "context": kwargs.get("context", {}),
                **kwargs,
            }

        # Use JsonInputBuilder to create proper structured input
        if message_type == "initial_story":
            return self.json_builder.build_initial_story_input(
                character_prompt=kwargs.get(
                    "character_prompt", "A hero begins their journey"
                ),
                user_id=kwargs.get("user_id", "test-user"),
                selected_prompts=kwargs.get("selected_prompts", ["narrative"]),
                generate_companions=kwargs.get("generate_companions", False),
                use_default_world=kwargs.get("use_default_world", True),
                world_data=kwargs.get("world_data", {}),
                system_instructions=kwargs.get("system_instructions", {}),
            )
        if message_type == "story_continuation":
            return self.json_builder.build_story_continuation_input(
                user_action=kwargs.get("user_action", kwargs.get("content", "Hello")),
                user_id=kwargs.get("user_id", "test-user"),
                game_mode=kwargs.get("game_mode", "character"),
                game_state=kwargs.get("game_state", {}),
                story_history=kwargs.get("story_history", []),
                checkpoint_block=kwargs.get("checkpoint_block", "Continue the story"),
                core_memories=kwargs.get("core_memories", []),
                sequence_ids=kwargs.get("sequence_ids", []),
                entity_tracking=kwargs.get("entity_tracking", {}),
                selected_prompts=kwargs.get("selected_prompts", ["narrative"]),
                use_default_world=kwargs.get("use_default_world", True),
            )
        if message_type == "user_input":
            # For simple user input, use story continuation structure
            return {
                "message_type": "user_input",
                "content": kwargs.get("content", "Hello"),
                "context": {
                    "user_id": kwargs.get("user_id", "test-user"),
                    "game_mode": kwargs.get("game_mode", "character"),
                    **kwargs.get("context", {}),
                },
            }
        if message_type == "system_instruction":
            # System instructions don't have a specific builder method
            return {
                "message_type": "system_instruction",
                "content": kwargs.get("content", "System instruction"),
                "context": {
                    "instruction_type": kwargs.get("instruction_type", "base_system")
                },
            }
        # Generic JSON input structure
        return {
            "message_type": message_type,
            "content": kwargs.get("content", ""),
            "context": kwargs.get("context", {}),
            **kwargs,
        }

    def validate_json_input(self, json_input: dict) -> bool:
        """Validate JSON input structure.

        Args:
            json_input: JSON input to validate

        Returns:
            True if valid, False otherwise
        """
        if not self.json_validator:
            # Basic validation fallback
            return isinstance(json_input, dict) and "message_type" in json_input

        result = self.json_validator.validate(json_input)
        return result.is_valid

    def setup_campaign(
        self, campaign_id: str = "test-campaign", user_id: str = "test-user-123"
    ) -> dict[str, Any]:
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
            "status": "active",
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
            "state_updates": {"health": 100, "level": 1, "experience": 0},
        }

        story_doc = campaign_doc.collection("story").document("current")
        story_doc.set(story_data)

        return campaign_data

    def setup_user(
        self, user_id: str = "test-user-123", email: str = "test@example.com"
    ) -> FakeUserRecord:
        """Set up a test user."""
        try:
            return self.auth.get_user(user_id)
        except Exception:
            return self.auth.create_user(
                uid=user_id, email=email, display_name="Test User"
            )

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
                if args and hasattr(args[0], "__dict__"):
                    args[0].services = services
                return test_func(*args, **kwargs)

        return wrapper

    return decorator


def create_test_app():
    """Create a test Flask app with fake services configured."""
    # Set up fake services
    services = FakeServiceManager()
    services.setup_environment()
    services.start_patches()

    # Create app
    app = create_app()
    app.config["TESTING"] = True

    # Store services on app for cleanup
    app.fake_services = services

    return app


def get_test_headers(user_id: str = "test-user-123") -> dict[str, str]:
    """Get test headers for bypassing authentication."""
    # Testing mode removed - return empty headers (real authentication now required)
    return {}


# Example usage patterns for migration from mocks documented in README
