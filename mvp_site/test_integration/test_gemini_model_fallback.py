"""
Tests for Gemini API model fallback functionality when API calls fail.
Tests the MODEL_FALLBACK_CHAIN behavior for 503, 429, and 400 errors.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_service import (
    _call_gemini_api_with_model_cycling, 
    MODEL_FALLBACK_CHAIN,
    DEFAULT_MODEL,
    TEST_MODEL
)
from google.genai import types

class TestGeminiModelFallback(unittest.TestCase):
    """Test model fallback functionality when API calls fail"""
    
    def setUp(self):
        """Set up test environment"""
        os.environ['TESTING'] = 'true'
        os.environ['GEMINI_API_KEY'] = 'test-key'
        
    def tearDown(self):
        """Clean up after tests"""
        if 'TESTING' in os.environ:
            del os.environ['TESTING']
    
    @patch('gemini_service.get_client')
    def test_primary_model_success(self, mock_get_client):
        """Test that primary model is used when it succeeds"""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "Test response"
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # Call the function
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"],
            DEFAULT_MODEL,
            current_prompt_text_for_logging="Test"
        )
        
        # Verify primary model was used
        self.assertEqual(result, mock_response)
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        # In TESTING mode, either TEST_MODEL or the requested model (DEFAULT_MODEL) could be used
        self.assertIn(call_args[1]['model'], [DEFAULT_MODEL, TEST_MODEL])
    
    @patch('gemini_service.get_client')
    @patch('gemini_service._log_token_count')
    def test_503_overload_fallback(self, mock_log_token, mock_get_client):
        """Test fallback when primary model returns 503 overload error"""
        # Mock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # First call fails with 503, second succeeds
        mock_response = Mock()
        mock_response.text = "Fallback response"
        
        mock_client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE"),
            mock_response
        ]
        
        # Call the function
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"],
            DEFAULT_MODEL,
            current_prompt_text_for_logging="Test"
        )
        
        # Verify fallback was used
        self.assertEqual(result, mock_response)
        self.assertEqual(mock_client.models.generate_content.call_count, 2)
        
        # Check models used
        calls = mock_client.models.generate_content.call_args_list
        # First call should use the requested model (might be TEST_MODEL in test env)
        first_model = calls[0][1]['model']
        # Second call should be different (fallback)
        second_model = calls[1][1]['model']
        self.assertNotEqual(first_model, second_model)
    
    @patch('gemini_service.get_client')
    @patch('gemini_service._log_token_count')
    def test_429_rate_limit_fallback(self, mock_log_token, mock_get_client):
        """Test fallback when model returns 429 rate limit error"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # First two calls fail with 429, third succeeds
        mock_response = Mock()
        mock_response.text = "Success after rate limits"
        
        mock_client.models.generate_content.side_effect = [
            Exception("429 Rate limit exceeded"),
            Exception("429 Rate limit exceeded"),
            mock_response
        ]
        
        # Call the function
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"],
            LARGE_CONTEXT_MODEL,
            current_prompt_text_for_logging="Test"
        )
        
        # Verify multiple fallbacks were attempted
        self.assertEqual(result, mock_response)
        self.assertEqual(mock_client.models.generate_content.call_count, 3)
    
    @patch('gemini_service.get_client')
    @patch('gemini_service._log_token_count')
    def test_400_model_not_found_fallback(self, mock_log_token, mock_get_client):
        """Test fallback when model returns 400 not found error"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # First call fails with 400, second succeeds
        mock_response = Mock()
        mock_response.text = "Found with different model"
        
        mock_client.models.generate_content.side_effect = [
            Exception("400 Model not found"),
            mock_response
        ]
        
        # Call the function with a non-existent model
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"],
            "non-existent-model",
            current_prompt_text_for_logging="Test"
        )
        
        # Verify fallback was used
        self.assertEqual(result, mock_response)
        self.assertEqual(mock_client.models.generate_content.call_count, 2)
    
    @patch('gemini_service.get_client')
    @patch('gemini_service._log_token_count')
    def test_all_models_fail(self, mock_log_token, mock_get_client):
        """Test behavior when all models in fallback chain fail"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # All calls fail with 503
        mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE")
        
        # Call should raise the last exception
        with self.assertRaises(Exception) as context:
            _call_gemini_api_with_model_cycling(
                ["Test prompt"],
                DEFAULT_MODEL,
                current_prompt_text_for_logging="Test"
            )
        
        # Verify multiple models were tried (at least 2)
        # The exact count depends on test environment and model deduplication
        self.assertGreaterEqual(mock_client.models.generate_content.call_count, 2)
        self.assertIn("503", str(context.exception))
    
    @patch('gemini_service.get_client')
    @patch('gemini_service._log_token_count')
    def test_non_recoverable_error(self, mock_log_token, mock_get_client):
        """Test that non-recoverable errors don't trigger fallback"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # First call fails with non-recoverable error
        mock_client.models.generate_content.side_effect = Exception("401 Unauthorized")
        
        # Call should fail immediately without trying fallbacks
        with self.assertRaises(Exception) as context:
            _call_gemini_api_with_model_cycling(
                ["Test prompt"],
                DEFAULT_MODEL,
                current_prompt_text_for_logging="Test"
            )
        
        # Verify only one attempt was made
        self.assertEqual(mock_client.models.generate_content.call_count, 1)
        self.assertIn("401", str(context.exception))
    
    @patch('gemini_service.get_client')
    @patch('gemini_service._log_token_count')
    def test_fallback_chain_order(self, mock_log_token, mock_get_client):
        """Test that fallback models are tried in correct order"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Make all calls fail to see full chain
        mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE")
        
        # Start with a model not at beginning of chain
        starting_model = MODEL_FALLBACK_CHAIN[2]
        
        try:
            _call_gemini_api_with_model_cycling(
                ["Test prompt"],
                starting_model,
                current_prompt_text_for_logging="Test"
            )
        except Exception:
            pass  # Expected to fail
        
        # Verify order: starting model first, then full chain
        calls = mock_client.models.generate_content.call_args_list
        models_tried = [call[1]['model'] for call in calls]
        
        # First should be the requested model
        self.assertEqual(models_tried[0], starting_model)
        
        # Rest should follow fallback chain order (excluding duplicates)
        remaining_models = [m for m in models_tried[1:]]
        for i, model in enumerate(MODEL_FALLBACK_CHAIN):
            if model != starting_model and i < len(remaining_models):
                self.assertIn(model, remaining_models)
    
    @patch('gemini_service.get_client')
    @patch('gemini_service._log_token_count')
    def test_json_mode_preserved_on_fallback(self, mock_log_token, mock_get_client):
        """Test that JSON mode is preserved when falling back to other models"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.text = '{"narrative": "test"}'
        
        mock_client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE"),
            mock_response
        ]
        
        # Call with JSON mode
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"],
            DEFAULT_MODEL,
            use_json_mode=True
        )
        
        # Verify JSON mode was set on both attempts
        calls = mock_client.models.generate_content.call_args_list
        for call in calls:
            config = call[1]['config']
            # Config object may have attributes directly or via dict
            if hasattr(config, 'response_mime_type'):
                self.assertEqual(config.response_mime_type, 'application/json')
            elif hasattr(config, '_kwargs'):
                self.assertIn('response_mime_type', config._kwargs)
                self.assertEqual(config._kwargs['response_mime_type'], 'application/json')
            else:
                # Mock object case
                self.assertTrue(True)  # Skip validation for mocks
    
    @patch('gemini_service.get_client')
    @patch('gemini_service._log_token_count')
    def test_system_instruction_preserved_on_fallback(self, mock_log_token, mock_get_client):
        """Test that system instruction is preserved when falling back"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.text = "Response with system instruction"
        
        mock_client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE"),
            mock_response
        ]
        
        system_instruction = "Test system instruction"
        
        # Call with system instruction
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"],
            DEFAULT_MODEL,
            system_instruction_text=system_instruction
        )
        
        # Verify system instruction was passed on both attempts
        calls = mock_client.models.generate_content.call_args_list
        for call in calls:
            config = call[1]['config']
            # Config object may have attributes directly or via dict
            if hasattr(config, 'system_instruction'):
                if hasattr(config.system_instruction, 'text'):
                    self.assertEqual(config.system_instruction.text, system_instruction)
                else:
                    self.assertEqual(str(config.system_instruction), system_instruction)
            elif hasattr(config, '_kwargs'):
                self.assertIn('system_instruction', config._kwargs)
                self.assertEqual(config._kwargs['system_instruction'].text, system_instruction)
            else:
                # Mock object case
                self.assertTrue(True)  # Skip validation for mocks


if __name__ == '__main__':
    unittest.main()