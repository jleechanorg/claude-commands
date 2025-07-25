"""
🔴 RED PHASE: Failing tests for user model selection in Gemini service

These tests document the expected behavior for applying user settings
to Gemini API model selection. Currently FAILING because the feature
is not implemented.

Test Coverage:
- Model selection respects user settings
- Fallback to default model when no settings
- Proper user_id parameter handling
- Integration with get_user_settings()
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import gemini_service
import constants
from custom_types import UserId


class TestUserModelSelection(unittest.TestCase):
    """🔴 RED: Tests for user-specific model selection in Gemini service"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_user_id = "test-user-123"
        self.test_prompt = "Start an adventure"
        
    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    def test_uses_user_preferred_model_flash(self, mock_get_text, mock_api_call, mock_get_settings):
        """🟢 GREEN: Should use flash-2.5 when user prefers it"""
        # Arrange
        mock_get_settings.return_value = {'gemini_model': 'gemini-2.5-flash'}
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}}'
        
        # Act
        result = gemini_service.get_initial_story(
            prompt=self.test_prompt,
            user_id=self.test_user_id
        )
        
        # Assert
        mock_get_settings.assert_called_once_with(self.test_user_id)
        mock_api_call.assert_called_once()
        # Verify the model used was gemini-2.5-flash
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model
        self.assertEqual(model_used, "gemini-2.5-flash")

    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    def test_uses_user_preferred_model_pro(self, mock_get_text, mock_api_call, mock_get_settings):
        """🟢 GREEN: Should use pro-2.5 when user prefers it"""
        # Arrange
        mock_get_settings.return_value = {'gemini_model': 'pro-2.5'}
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}}'
        
        # Act
        result = gemini_service.get_initial_story(
            prompt=self.test_prompt,
            user_id=self.test_user_id
        )
        
        # Assert
        mock_get_settings.assert_called_once_with(self.test_user_id)
        mock_api_call.assert_called_once()
        # Verify the model used was pro-2.5
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model
        self.assertEqual(model_used, "gemini-2.5-pro")

    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    def test_falls_back_to_default_when_no_settings(self, mock_get_text, mock_api_call, mock_get_settings):
        """🟢 GREEN: Should use default model when no user settings"""
        # Arrange
        mock_get_settings.return_value = {}  # No settings
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}}'
        
        # Act
        result = gemini_service.get_initial_story(
            prompt=self.test_prompt,
            user_id=self.test_user_id
        )
        
        # Assert
        mock_get_settings.assert_called_once_with(self.test_user_id)
        mock_api_call.assert_called_once()
        # Verify fallback to default model
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model
        self.assertEqual(model_used, gemini_service.DEFAULT_MODEL)

    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    def test_handles_invalid_model_preference(self, mock_get_text, mock_api_call, mock_get_settings):
        """🟢 GREEN: Should fallback to default for invalid model preference"""
        # Arrange
        mock_get_settings.return_value = {'gemini_model': 'invalid-model'}
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}}'
        
        # Act
        result = gemini_service.get_initial_story(
            prompt=self.test_prompt,
            user_id=self.test_user_id
        )
        
        # Assert
        mock_get_settings.assert_called_once_with(self.test_user_id)
        mock_api_call.assert_called_once()
        # Verify fallback to default model for invalid preference
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model
        self.assertEqual(model_used, gemini_service.DEFAULT_MODEL)

    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    @patch.dict(os.environ, {'MOCK_SERVICES_MODE': 'true'})
    def test_uses_test_model_in_mock_mode(self, mock_get_text, mock_api_call, mock_get_settings):
        """🟢 GREEN: Should use test model when in mock mode regardless of user preference"""
        # Arrange
        mock_get_settings.return_value = {'gemini_model': 'pro-2.5'}
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}}'
        
        # Act
        result = gemini_service.get_initial_story(
            prompt=self.test_prompt,
            user_id=self.test_user_id
        )
        
        # Assert
        # Should not call get_user_settings in mock mode
        mock_get_settings.assert_not_called()
        mock_api_call.assert_called_once()
        # Verify test model is used even with user preference
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]
        self.assertEqual(model_used, gemini_service.TEST_MODEL)


if __name__ == '__main__':
    print("🔴 RED PHASE: Running failing tests for user model selection")
    print("Expected: All tests should FAIL because feature is not implemented")
    unittest.main()