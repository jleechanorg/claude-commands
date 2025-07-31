"""
Test Settings and Utilities

Centralized test configuration, fixtures, base classes, and utilities
to eliminate duplication across test files and provide consistent patterns.
"""

import json
import os
import tempfile
import unittest
import uuid
from io import StringIO
from typing import Any
from unittest.mock import MagicMock, patch

import logging_util

# Mock firebase_admin globally for all tests
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# DELETE_FIELD sentinel for Firestore testing
DELETE_FIELD = object()
mock_firestore.DELETE_FIELD = DELETE_FIELD

# Apply global mocks
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["firebase_admin.auth"] = mock_auth

# Import after mocks are set up
from main import DEFAULT_TEST_USER, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID, create_app


class TestConstants:
    """Centralized test constants to eliminate magic strings."""

    # Test IDs
    TEST_CAMPAIGN_ID = "test-campaign-123"
    TEST_USER_ID = "test-user-456"
    NONEXISTENT_CAMPAIGN_ID = "nonexistent-campaign"

    # Test Titles
    SAMPLE_CAMPAIGN_TITLE = "Test Adventure Campaign"
    UPDATED_CAMPAIGN_TITLE = "Updated Adventure Title"

    # Error Messages
    ERROR_DATABASE_FAILURE = "Database connection failed"
    ERROR_NOT_FOUND = "Campaign not found"
    ERROR_MISSING_TITLE = "Title is required"
    ERROR_UNSUPPORTED_FORMAT = "Unsupported format"
    ERROR_MISSING_PROMPT = "Prompt is required"
    ERROR_GENERATION_FAILED = "Generation failed"

    # File Formats
    FORMATS = {
        "pdf": {"mime": "application/pdf", "content": b"PDF content here"},
        "docx": {
            "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "content": b"DOCX content here",
        },
        "txt": {"mime": "text/plain", "content": "Text content here"},
    }

    # Test Data Sizes
    LARGE_STORY_LENGTH = 1000
    MAX_TITLE_LENGTH = 255


class TestDataFixtures:
    """Reusable test data fixtures to eliminate duplication."""

    @staticmethod
    def get_sample_campaign(campaign_id: str = None) -> dict[str, Any]:
        """Get a standard test campaign."""
        return {
            "id": campaign_id or TestConstants.TEST_CAMPAIGN_ID,
            "title": TestConstants.SAMPLE_CAMPAIGN_TITLE,
            "story": [
                {"content": "Adventure begins in a dark forest...", "actor": "gemini"},
                {"content": "I examine the trees closely.", "actor": "user"},
                {
                    "content": "You find ancient runes carved into the bark.",
                    "actor": "gemini",
                },
            ],
            "player": {"name": "Hero", "level": 5, "hp": 45, "max_hp": 45},
            "created_at": "2024-01-01T10:00:00Z",
            "last_played": "2024-01-02T15:30:00Z",
        }

    @staticmethod
    def get_campaign_list() -> dict[str, list[dict[str, Any]]]:
        """Get a list of campaigns for testing."""
        return {
            "campaigns": [
                {
                    "id": "campaign1",
                    "title": "Dragon Quest Adventure",
                    "created_at": "2024-01-01T10:00:00Z",
                },
                {
                    "id": "campaign2",
                    "title": "Mystic Forest Journey",
                    "created_at": "2024-01-02T11:00:00Z",
                },
            ]
        }

    @staticmethod
    def get_empty_campaign_list() -> dict[str, list]:
        """Get empty campaigns list."""
        return {"campaigns": []}

    @staticmethod
    def get_campaign_with_combat() -> dict[str, Any]:
        """Get a campaign with active combat state."""
        campaign = TestDataFixtures.get_sample_campaign()
        campaign["combat_state"] = {
            "active": True,
            "combatants": [
                {
                    "name": "Goblin Warrior",
                    "hp": 15,
                    "max_hp": 15,
                    "status": "active",
                    "initiative": 12,
                },
                {
                    "name": "Orc Brute",
                    "hp": 25,
                    "max_hp": 25,
                    "status": "active",
                    "initiative": 8,
                },
            ],
            "current_turn": 0,
            "round_number": 1,
        }
        return campaign

    @staticmethod
    def get_gemini_response() -> dict[str, Any]:
        """Get a mock Gemini AI response."""
        return {
            "title": "AI Generated Adventure",
            "initial_story": "Your epic journey begins as you step into the unknown...",
            "player_character": {
                "name": "Brave Adventurer",
                "class": "Fighter",
                "level": 1,
            },
        }

    @staticmethod
    def get_invalid_campaigns() -> list[dict[str, Any]]:
        """Get various invalid campaign data for error testing."""
        return [
            {},  # Empty campaign
            {"title": ""},  # Empty title
            {"title": TestConstants.SAMPLE_CAMPAIGN_TITLE},  # Missing story
            {"story": "not_a_list"},  # Wrong story type
            {"title": "x" * (TestConstants.MAX_TITLE_LENGTH + 1)},  # Title too long
        ]

    @staticmethod
    def get_malformed_json_requests() -> list[str]:
        """Get various malformed JSON strings for testing."""
        return [
            "",  # Empty string
            "{",  # Incomplete JSON
            '{"title": }',  # Invalid JSON syntax
            '{"title": "test", "extra_comma": ,}',  # Trailing comma
        ]


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities."""

    def setUp(self):
        """Common setup for all tests."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_headers = {
            HEADER_TEST_BYPASS: "true",
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER,
        }
        self.test_id = f"test_{uuid.uuid4().hex[:8]}"

        # Reset all mocks
        self.reset_all_mocks()

    def reset_all_mocks(self):
        """Reset all global mocks to clean state."""
        mock_firebase_admin.auth.verify_id_token.reset_mock()
        mock_firestore.reset_mock()

    def assert_json_error(self, response, status_code: int, error_substring: str):
        """Assert response contains JSON error with specific status and message."""
        assert response.status_code == status_code
        data = json.loads(response.data)
        assert "error" in data
        assert error_substring.lower() in data["error"].lower()

    def assert_json_success(self, response, status_code: int = 200):
        """Assert response is successful JSON."""
        assert response.status_code == status_code
        return json.loads(response.data)

    def create_temp_file(self, content: str = "", suffix: str = ".txt") -> str:
        """Create a temporary file for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        self.addCleanup(os.unlink, temp_file.name)  # Clean up after test
        return temp_file.name


class BaseAPITest(BaseTestCase):
    """Base class for API endpoint tests with additional utilities."""

    def get_campaigns(self, expected_status: int = 200):
        """Helper to get campaigns with standard headers."""
        response = self.client.get("/api/campaigns", headers=self.test_headers)
        if expected_status:
            assert response.status_code == expected_status
        return response

    def get_campaign(self, campaign_id: str, expected_status: int = 200):
        """Helper to get specific campaign with standard headers."""
        response = self.client.get(
            f"/api/campaigns/{campaign_id}", headers=self.test_headers
        )
        if expected_status:
            assert response.status_code == expected_status
        return response

    def update_campaign(self, campaign_id: str, data: dict, expected_status: int = 200):
        """Helper to update campaign with standard headers."""
        response = self.client.patch(
            f"/api/campaigns/{campaign_id}", headers=self.test_headers, json=data
        )
        if expected_status:
            assert response.status_code == expected_status
        return response

    def create_campaign(self, data: dict, expected_status: int = 201):
        """Helper to create campaign with standard headers."""
        response = self.client.post(
            "/api/campaigns", headers=self.test_headers, json=data
        )
        if expected_status:
            assert response.status_code == expected_status
        return response

    def export_campaign(
        self, campaign_id: str, format_type: str, expected_status: int = 200
    ):
        """Helper to export campaign in specified format."""
        response = self.client.get(
            f"/api/campaigns/{campaign_id}/export?format={format_type}",
            headers=self.test_headers,
        )
        if expected_status:
            assert response.status_code == expected_status
        return response


class MockManager:
    """Centralized mock management with context managers."""

    @staticmethod
    def mock_firestore_service(**methods):
        """Context manager for mocking firestore_service."""
        return patch("main.firestore_service", **methods)

    @staticmethod
    def mock_gemini_service(**methods):
        """Context manager for mocking gemini_service."""
        return patch("main.gemini_service", **methods)

    @staticmethod
    def mock_document_generator(**methods):
        """Context manager for mocking document_generator."""
        return patch("main.document_generator", **methods)

    @staticmethod
    def mock_file_operations():
        """Context manager for mocking file operations."""
        return patch.multiple("main", send_file=MagicMock(), os=MagicMock())


class ParameterizedTestMixin:
    """Mixin for parameterized testing patterns."""

    def run_parameterized_test(self, test_cases: list[tuple], test_function):
        """Run parameterized test with subTest for each case."""
        for case in test_cases:
            if len(case) == 2:
                name, params = case
                expected = None
            else:
                name, params, expected = case

            with self.subTest(case=name):
                if expected is not None:
                    test_function(params, expected)
                else:
                    test_function(params)


class LoggingTestMixin:
    """Mixin for testing logging functionality."""

    def setUp_logging(self, logger_name: str = "test"):
        """Set up logging capture for tests."""
        self.test_logger = logging_util.getLogger(logger_name)
        self.test_logger.setLevel(logging_util.ERROR)
        self.log_stream = StringIO()
        self.handler = logging_util.StreamHandler(self.log_stream)
        self.test_logger.addHandler(self.handler)

    def tearDown_logging(self):
        """Clean up logging setup."""
        if hasattr(self, "test_logger") and hasattr(self, "handler"):
            self.test_logger.removeHandler(self.handler)
            self.handler.close()

    def get_log_output(self) -> str:
        """Get captured log output."""
        return self.log_stream.getvalue()

    def assert_logged(self, message: str):
        """Assert that message was logged."""
        log_output = self.get_log_output()
        assert message in log_output


class ErrorTestingMixin:
    """Mixin for comprehensive error testing patterns."""

    def test_error_conditions(
        self, endpoint: str, method: str, error_cases: list[tuple]
    ):
        """Test multiple error conditions for an endpoint."""
        for (
            case_name,
            request_data,
            mock_side_effect,
            expected_status,
            expected_error,
        ) in error_cases:
            with self.subTest(case=case_name):
                if mock_side_effect:
                    # Apply mock side effect
                    pass  # Implementation depends on specific service

                if method.upper() == "GET":
                    response = self.client.get(endpoint, headers=self.test_headers)
                elif method.upper() == "POST":
                    response = self.client.post(
                        endpoint, headers=self.test_headers, json=request_data
                    )
                elif method.upper() == "PATCH":
                    response = self.client.patch(
                        endpoint, headers=self.test_headers, json=request_data
                    )

                self.assert_json_error(response, expected_status, expected_error)


class TestUtilities:
    """Static utility methods for common test operations."""

    @staticmethod
    def generate_large_story(length: int = 1000) -> list[dict[str, str]]:
        """Generate a large story for testing limits."""
        story = []
        for i in range(length):
            story.append(
                {
                    "content": f"Story segment {i}: This is a test story segment with some content.",
                    "actor": "gemini" if i % 2 == 0 else "user",
                }
            )
        return story

    @staticmethod
    def corrupt_json_data(valid_data: dict) -> str:
        """Corrupt JSON data for error testing."""
        json_str = json.dumps(valid_data)
        # Remove random closing bracket
        return json_str[:-1]

    @staticmethod
    def create_mock_response(status_code: int, data: dict = None, headers: dict = None):
        """Create a mock HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.data = json.dumps(data or {}).encode()
        mock_response.headers = headers or {}
        return mock_response


# Test configuration for different environments
class TestConfig:
    """Test configuration settings."""

    # Environment configurations for testing
    ENVIRONMENTS = {
        "development": {
            "DEBUG": True,
            "TESTING": False,
            "AI_MODEL": "gemini-2.5-flash",
        },
        "testing": {"DEBUG": False, "TESTING": True, "AI_MODEL": "gemini-1.5-flash"},
        "production": {
            "DEBUG": False,
            "TESTING": False,
            "AI_MODEL": "gemini-2.5-flash",
        },
    }

    # Required environment variables
    REQUIRED_ENV_VARS = ["GOOGLE_APPLICATION_CREDENTIALS", "GEMINI_API_KEY"]


# Export commonly used items
__all__ = [
    "TestConstants",
    "TestDataFixtures",
    "BaseTestCase",
    "BaseAPITest",
    "MockManager",
    "ParameterizedTestMixin",
    "LoggingTestMixin",
    "ErrorTestingMixin",
    "TestUtilities",
    "TestConfig",
    # Mock objects
    "mock_firebase_admin",
    "mock_firestore",
    "mock_auth",
    "DELETE_FIELD",
]
