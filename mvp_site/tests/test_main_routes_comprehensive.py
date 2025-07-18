"""
Unit tests for main.py business logic functions without Flask dependencies.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock firebase_admin before imports
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# Setup module mocks
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["firebase_admin.auth"] = mock_auth

from main import _prepare_game_state

# Import after mocking
from game_state import GameState


class TestBusinessLogic(unittest.TestCase):
    """Test main.py business logic functions directly."""

    def test_prepare_game_state_success(self):
        """Test successful game state preparation."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
            patch("main.GameState") as mock_game_state_class,
        ):
            # Mock firestore returning a game state document
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = {"test": "data"}
            mock_firestore_service.get_campaign_game_state.return_value = mock_doc

            # Mock GameState creation
            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {"test": "data"}
            mock_game_state_class.from_dict.return_value = mock_game_state

            # Mock StateHelper
            mock_gemini_response.cleanup_legacy_state.return_value = (
                {"test": "data"},
                False,
                0,
            )

            # Call the function
            result, was_cleaned, num_cleaned = _prepare_game_state(
                "user123", "campaign456"
            )

            # Verify
            self.assertEqual(result, mock_game_state)
            self.assertFalse(was_cleaned)
            self.assertEqual(num_cleaned, 0)
            mock_firestore_service.get_campaign_game_state.assert_called_once_with(
                "user123", "campaign456"
            )

    def test_prepare_game_state_no_existing_state(self):
        """Test game state preparation when no state exists."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
            patch("main.GameState") as mock_game_state_class,
        ):
            # Mock firestore returning None (no existing state)
            mock_firestore_service.get_campaign_game_state.return_value = None

            # Mock GameState creation
            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {}
            mock_game_state_class.return_value = mock_game_state

            # Mock StateHelper
            mock_gemini_response.cleanup_legacy_state.return_value = ({}, False, 0)

            # Call the function
            result, was_cleaned, num_cleaned = _prepare_game_state(
                "user123", "campaign456"
            )

            # Verify
            self.assertEqual(result, mock_game_state)
            self.assertFalse(was_cleaned)
            self.assertEqual(num_cleaned, 0)
            mock_firestore_service.get_campaign_game_state.assert_called_once_with(
                "user123", "campaign456"
            )

    def test_prepare_game_state_with_cleanup(self):
        """Test game state preparation with legacy cleanup."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("main._cleanup_legacy_state") as mock_cleanup,
        ):
            # Mock firestore returning a real GameState object with legacy data
            mock_game_state = GameState.from_dict(
                {"old": "data", "world_time": "old_time", "some.key": "value"}
            )
            mock_firestore_service.get_campaign_game_state.return_value = (
                mock_game_state
            )

            # Mock cleanup to return cleaned data
            mock_cleanup.return_value = ({"cleaned": "data"}, True, 5)

            # Call the function
            result, was_cleaned, num_cleaned = _prepare_game_state(
                "user123", "campaign456"
            )

            # Verify
            self.assertTrue(was_cleaned)
            self.assertEqual(num_cleaned, 5)
            # Verify cleanup was called with the original state
            mock_cleanup.assert_called_once()
            # Verify firestore was updated with cleaned state
            mock_firestore_service.update_campaign_game_state.assert_called_once()

    def test_prepare_game_state_firestore_error(self):
        """Test _prepare_game_state when Firestore operations fail."""
        with patch("main.firestore_service") as mock_firestore_service:
            # Mock get_campaign_game_state to raise an exception
            mock_firestore_service.get_campaign_game_state.side_effect = Exception(
                "Database error"
            )

            # Call the function directly and verify it raises the exception
            with self.assertRaises(Exception) as context:
                _prepare_game_state("test-user", "test-campaign")

            # Verify the correct exception was raised
            self.assertEqual(str(context.exception), "Database error")

            # Verify the firestore service was called with correct parameters
            mock_firestore_service.get_campaign_game_state.assert_called_once_with(
                "test-user", "test-campaign"
            )


if __name__ == "__main__":
    unittest.main()
