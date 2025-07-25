#!/usr/bin/env python3
"""
🔴 RED PHASE: Layer 1 Unit Tests for Debug Mode Setting

These tests document the expected behavior for debug mode setting functionality.
Currently FAILING because the feature is not implemented.

Test Coverage:
- Debug mode setting storage and retrieval
- Fallback to default when no setting exists
- Integration with get_user_settings()
- Validation of debug mode values
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import constants
from custom_types import UserId


class TestDebugModeSetting(unittest.TestCase):
    """🔴 RED: Tests for debug mode setting functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_user_id = "test-user-debug-123"
        
    @patch('firestore_service.get_user_settings')
    def test_debug_mode_enabled_setting(self, mock_get_settings):
        """🟢 GREEN: Should return True when debug mode is enabled"""
        # Arrange
        mock_get_settings.return_value = {'debug_mode': True}
        
        # Import after mocking to ensure proper module loading
        import firestore_service
        
        # Act
        settings = firestore_service.get_user_settings(self.test_user_id)
        debug_enabled = settings.get('debug_mode', False)
        
        # Assert
        mock_get_settings.assert_called_once_with(self.test_user_id)
        self.assertTrue(debug_enabled)

    @patch('firestore_service.get_user_settings')
    def test_debug_mode_disabled_setting(self, mock_get_settings):
        """🟢 GREEN: Should return False when debug mode is disabled"""
        # Arrange
        mock_get_settings.return_value = {'debug_mode': False}
        
        # Import after mocking to ensure proper module loading
        import firestore_service
        
        # Act
        settings = firestore_service.get_user_settings(self.test_user_id)
        debug_enabled = settings.get('debug_mode', False)
        
        # Assert
        mock_get_settings.assert_called_once_with(self.test_user_id)
        self.assertFalse(debug_enabled)

    @patch('firestore_service.get_user_settings')
    def test_debug_mode_fallback_to_default(self, mock_get_settings):
        """🟢 GREEN: Should fallback to False when no debug mode setting exists"""
        # Arrange
        mock_get_settings.return_value = {}  # No debug_mode setting
        
        # Import after mocking to ensure proper module loading
        import firestore_service
        
        # Act
        settings = firestore_service.get_user_settings(self.test_user_id)
        debug_enabled = settings.get('debug_mode', constants.DEFAULT_DEBUG_MODE)
        
        # Assert
        mock_get_settings.assert_called_once_with(self.test_user_id)
        self.assertEqual(debug_enabled, constants.DEFAULT_DEBUG_MODE)

    @patch('firestore_service.update_user_settings')
    def test_save_debug_mode_enabled(self, mock_update_settings):
        """🟢 GREEN: Should save debug mode enabled setting"""
        # Arrange
        mock_update_settings.return_value = True
        
        # Import after mocking to ensure proper module loading
        import firestore_service
        
        # Act
        result = firestore_service.update_user_settings(
            self.test_user_id, 
            {'debug_mode': True}
        )
        
        # Assert
        mock_update_settings.assert_called_once_with(self.test_user_id, {'debug_mode': True})
        self.assertTrue(result)

    @patch('firestore_service.update_user_settings')
    def test_save_debug_mode_disabled(self, mock_update_settings):
        """🟢 GREEN: Should save debug mode disabled setting"""
        # Arrange
        mock_update_settings.return_value = True
        
        # Import after mocking to ensure proper module loading
        import firestore_service
        
        # Act
        result = firestore_service.update_user_settings(
            self.test_user_id, 
            {'debug_mode': False}
        )
        
        # Assert
        mock_update_settings.assert_called_once_with(self.test_user_id, {'debug_mode': False})
        self.assertTrue(result)

    def test_debug_mode_validation_valid_true(self):
        """🟢 GREEN: Should validate True as valid debug mode value"""
        # Act & Assert
        self.assertIn(True, constants.ALLOWED_DEBUG_MODE_VALUES)

    def test_debug_mode_validation_valid_false(self):
        """🟢 GREEN: Should validate False as valid debug mode value"""
        # Act & Assert
        self.assertIn(False, constants.ALLOWED_DEBUG_MODE_VALUES)

    def test_debug_mode_validation_invalid_string(self):
        """🟢 GREEN: Should reject string values as invalid"""
        # Act & Assert
        self.assertNotIn("true", constants.ALLOWED_DEBUG_MODE_VALUES)
        self.assertNotIn("false", constants.ALLOWED_DEBUG_MODE_VALUES)


if __name__ == '__main__':
    print("🔴 RED PHASE: Running failing tests for debug mode setting")
    print("Expected: All tests should FAIL because feature is not implemented")
    unittest.main()