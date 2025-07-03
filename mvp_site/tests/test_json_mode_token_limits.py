"""
Unit tests for JSON mode token limit functionality
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gemini_service
from google.genai import types


class TestJsonModeTokenLimits(unittest.TestCase):
    """Test cases for JSON mode token limit behavior"""
    
    def setUp(self):
        """Set up test environment"""
        # Save original values to restore later
        self.original_max_tokens = gemini_service.MAX_TOKENS
        self.original_json_max_tokens = gemini_service.JSON_MODE_MAX_TOKENS
        
        # Mock the client
        self.mock_client = MagicMock()
        self.mock_response = MagicMock()
        self.mock_response.text = '{"narrative": "Test response", "entities_mentioned": [], "location_confirmed": "test"}'
        
    def tearDown(self):
        """Restore original values"""
        gemini_service.MAX_TOKENS = self.original_max_tokens
        gemini_service.JSON_MODE_MAX_TOKENS = self.original_json_max_tokens
    
    @patch('gemini_service.get_client')
    def test_json_mode_uses_reduced_token_limit(self, mock_get_client):
        """Test that JSON mode uses the reduced token limit"""
        mock_get_client.return_value = self.mock_client
        self.mock_client.models.generate_content.return_value = self.mock_response
        self.mock_client.models.count_tokens.return_value = MagicMock(total_tokens=1000)
        
        # Call with JSON mode enabled
        response = gemini_service._call_gemini_api(
            ["Test prompt"],
            gemini_service.DEFAULT_MODEL,
            use_json_mode=True
        )
        
        # Verify the call was made with reduced token limit
        generate_call = self.mock_client.models.generate_content.call_args
        config = generate_call.kwargs['config']
        
        # The config should have the JSON mode token limit
        self.assertEqual(config.max_output_tokens, gemini_service.JSON_MODE_MAX_TOKENS)
        self.assertEqual(config.response_mime_type, "application/json")
    
    @patch('gemini_service.get_client')
    def test_non_json_mode_uses_standard_token_limit(self, mock_get_client):
        """Test that non-JSON mode uses the standard token limit"""
        mock_get_client.return_value = self.mock_client
        self.mock_client.models.generate_content.return_value = self.mock_response
        self.mock_client.models.count_tokens.return_value = MagicMock(total_tokens=1000)
        
        # Call without JSON mode
        response = gemini_service._call_gemini_api(
            ["Test prompt"],
            gemini_service.DEFAULT_MODEL,
            use_json_mode=False
        )
        
        # Verify the call was made with standard token limit
        generate_call = self.mock_client.models.generate_content.call_args
        config = generate_call.kwargs['config']
        
        # The config should have the standard token limit
        self.assertEqual(config.max_output_tokens, gemini_service.MAX_TOKENS)
        # Should not have response_mime_type set (should be None)
        self.assertIsNone(config.response_mime_type)
    
    @patch('gemini_service.get_client')
    @patch('gemini_service.logging')
    def test_json_mode_logs_token_limit(self, mock_logging, mock_get_client):
        """Test that JSON mode logs the reduced token limit"""
        mock_get_client.return_value = self.mock_client
        self.mock_client.models.generate_content.return_value = self.mock_response
        self.mock_client.models.count_tokens.return_value = MagicMock(total_tokens=1000)
        
        # Call with JSON mode
        response = gemini_service._call_gemini_api(
            ["Test prompt"],
            gemini_service.DEFAULT_MODEL,
            use_json_mode=True
        )
        
        # Check that appropriate log message was generated
        log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
        token_limit_logged = any(
            f"Using JSON response mode with reduced token limit ({gemini_service.JSON_MODE_MAX_TOKENS})" in log_call
            for log_call in log_calls
        )
        self.assertTrue(token_limit_logged, "JSON mode token limit not logged")
    
    def test_token_limit_values(self):
        """Test that token limit values are set correctly"""
        # Verify the constants are set as expected
        self.assertEqual(gemini_service.MAX_TOKENS, 30000)
        self.assertEqual(gemini_service.JSON_MODE_MAX_TOKENS, 20000)
        self.assertLess(gemini_service.JSON_MODE_MAX_TOKENS, gemini_service.MAX_TOKENS)
    
    @patch('gemini_service.get_client')
    def test_model_cycling_preserves_json_mode(self, mock_get_client):
        """Test that model cycling preserves JSON mode settings"""
        mock_get_client.return_value = self.mock_client
        
        # First call fails with 503
        error = Exception("503 UNAVAILABLE")
        self.mock_client.models.generate_content.side_effect = [
            error,  # First model fails
            self.mock_response  # Second model succeeds
        ]
        self.mock_client.models.count_tokens.return_value = MagicMock(total_tokens=1000)
        
        # Call with JSON mode
        response = gemini_service._call_gemini_api_with_model_cycling(
            ["Test prompt"],
            gemini_service.DEFAULT_MODEL,
            use_json_mode=True
        )
        
        # Should have tried twice
        self.assertEqual(self.mock_client.models.generate_content.call_count, 2)
        
        # Both calls should have JSON mode settings
        for call_args in self.mock_client.models.generate_content.call_args_list:
            config = call_args.kwargs['config']
            self.assertEqual(config.max_output_tokens, gemini_service.JSON_MODE_MAX_TOKENS)
            self.assertEqual(config.response_mime_type, "application/json")


if __name__ == '__main__':
    unittest.main()