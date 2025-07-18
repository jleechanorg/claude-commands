"""
Configuration management for real service testing.
Handles environment variables and validation for test isolation.
"""

import os
from typing import Any


class TestConfig:
    """Configuration for real service testing."""

    @staticmethod
    def get_real_service_config() -> dict[str, Any]:
        """Get configuration for real services."""
        return {
            "firestore": {
                "project_id": os.getenv(
                    "TEST_FIRESTORE_PROJECT", "worldarchitect-test"
                ),
                "collection_prefix": "test_",
            },
            "gemini": {
                "api_key": os.getenv("TEST_GEMINI_API_KEY"),
                "model": "gemini-1.5-flash",  # Use cheaper model for testing
                "max_requests_per_test": 10,
            },
            "auth": {
                "test_user_id": "test-user-123",
                "test_session_id": "test-session-456",
            },
        }

    @staticmethod
    def validate_real_service_config() -> None:
        """Validate that required configuration is present."""
        config = TestConfig.get_real_service_config()

        if not config["gemini"]["api_key"]:
            raise ValueError(
                "TEST_GEMINI_API_KEY environment variable required for real service testing"
            )

        # Add other validation as needed

    @staticmethod
    def get_test_collection_name(base_name: str) -> str:
        """Get test-specific collection name with prefix."""
        config = TestConfig.get_real_service_config()
        prefix = config["firestore"]["collection_prefix"]
        return f"{prefix}{base_name}"
