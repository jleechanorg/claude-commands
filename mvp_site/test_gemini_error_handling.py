import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy API key before importing gemini_service
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_TESTING"

from google.genai import types

import gemini_service


class TestGeminiErrorHandling(unittest.TestCase):
    """Test error handling in gemini_service.py"""

    def setUp(self):
        """Reset the client before each test"""
        gemini_service._clear_client()
        # Clear any cached instructions
        gemini_service._loaded_instructions_cache.clear()

    def tearDown(self):
        """Clean up after each test"""
        gemini_service._clear_client()

    # Group 1 - API Errors

    def test_api_503_with_retry(self):
        """Test that 503 errors trigger model cycling through fallback chain"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create a mock response for the third attempt
            mock_response = MagicMock()
            mock_response.text = '{"story": "Success after retries"}'

            # Create mock exception with 503 error
            error_503 = Exception("503 UNAVAILABLE: Service temporarily unavailable")

            # Mock generate_content to fail twice with 503, then succeed
            mock_client.models.generate_content.side_effect = [
                error_503,  # First model fails
                error_503,  # Second model fails
                mock_response,  # Third model succeeds
            ]

            # Call the API
            prompt_contents = [types.Part(text="Test prompt")]
            result = gemini_service._call_gemini_api_with_model_cycling(
                prompt_contents,
                model_name="gemini-2.5-flash",
                system_instruction_text="Test instruction",
            )

            # Verify we got the successful response
            self.assertEqual(result, mock_response)

            # Verify we tried multiple models
            self.assertEqual(mock_client.models.generate_content.call_count, 3)

            # Verify the models were tried in the correct order
            calls = mock_client.models.generate_content.call_args_list
            self.assertEqual(calls[0][1]["model"], "gemini-2.5-flash")
            self.assertEqual(
                calls[1][1]["model"], "gemini-2.5-flash-lite-preview-06-17"
            )
            self.assertEqual(calls[2][1]["model"], "gemini-2.0-flash")

    def test_api_503_exhausted(self):
        """Test that persistent 503 errors across all models result in failure"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create mock exception with 503 error
            error_503 = Exception("503 UNAVAILABLE: Service temporarily unavailable")

            # Mock generate_content to always return 503
            mock_client.models.generate_content.side_effect = error_503

            # Call the API and expect it to raise after trying all models
            prompt_contents = [types.Part(text="Test prompt")]
            with self.assertRaises(Exception) as context:
                gemini_service._call_gemini_api_with_model_cycling(
                    prompt_contents,
                    model_name="gemini-2.5-flash",
                    system_instruction_text="Test instruction",
                )

            # Verify error message
            self.assertIn("503 UNAVAILABLE", str(context.exception))

            # Verify we tried all models in the fallback chain
            expected_attempts = len(gemini_service.MODEL_FALLBACK_CHAIN)
            self.assertEqual(
                mock_client.models.generate_content.call_count, expected_attempts
            )

    def test_connection_error_no_retry(self):
        """Test that generic errors are treated as non-recoverable"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Mock generate_content to raise generic error
            mock_client.models.generate_content.side_effect = ValueError(
                "Invalid request format"
            )

            # Call the API and expect immediate failure (no retries for generic errors)
            prompt_contents = [types.Part(text="Test prompt")]
            with self.assertRaises(ValueError) as context:
                gemini_service._call_gemini_api_with_model_cycling(
                    prompt_contents,
                    model_name="gemini-2.5-flash",
                    system_instruction_text="Test instruction",
                )

            # Verify error message
            self.assertIn("Invalid request format", str(context.exception))

            # Verify we only tried once (generic errors are non-recoverable)
            self.assertEqual(mock_client.models.generate_content.call_count, 1)

    # Group 2 - Rate Limiting

    def test_rate_limit_retry_and_fallback_order(self):
        """Test that 429 rate limit errors trigger retries and model fallback in correct order"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create a mock response for success
            mock_response = MagicMock()
            mock_response.text = '{"story": "Success after rate limit"}'

            # Create mock exception with 429 error
            error_429 = Exception("429 Too Many Requests: Rate limit exceeded")

            # Mock generate_content to fail once with 429, then succeed with different model
            mock_client.models.generate_content.side_effect = [
                error_429,  # First model rate limited
                mock_response,  # Second model succeeds
            ]

            # Call the API
            prompt_contents = [types.Part(text="Test prompt")]
            result = gemini_service._call_gemini_api_with_model_cycling(
                prompt_contents,
                model_name="gemini-2.5-flash",
                system_instruction_text="Test instruction",
            )

            # Verify we got the successful response
            self.assertEqual(result, mock_response)

            # Verify we tried two models
            self.assertEqual(mock_client.models.generate_content.call_count, 2)

            # Verify the models were tried in the correct order
            calls = mock_client.models.generate_content.call_args_list
            self.assertEqual(calls[0][1]["model"], "gemini-2.5-flash")
            self.assertEqual(
                calls[1][1]["model"], "gemini-2.5-flash-lite-preview-06-17"
            )

    def test_rate_limit_all_models_fail(self):
        """Test that rate limits on all models result in final failure"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create mock exception with 429 error
            error_429 = Exception("429 Too Many Requests: Rate limit exceeded")

            # Mock generate_content to always return 429
            mock_client.models.generate_content.side_effect = error_429

            # Call the API and expect it to raise after trying all models
            prompt_contents = [types.Part(text="Test prompt")]
            with self.assertRaises(Exception) as context:
                gemini_service._call_gemini_api_with_model_cycling(
                    prompt_contents,
                    model_name="gemini-2.5-flash",
                    system_instruction_text="Test instruction",
                )

            # Verify error message
            self.assertIn("429", str(context.exception))

            # Verify we tried all models in the fallback chain
            expected_attempts = len(gemini_service.MODEL_FALLBACK_CHAIN)
            self.assertEqual(
                mock_client.models.generate_content.call_count, expected_attempts
            )

    # Group 3 - Auth Errors

    def test_invalid_api_key_handling(self):
        """Test that 403 auth errors are non-recoverable"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create mock exception with 403 error
            error_403 = Exception("403 Forbidden: Invalid API key")
            error_403.status_code = 403

            # Mock generate_content to raise 403
            mock_client.models.generate_content.side_effect = error_403

            # Call the API and expect immediate failure
            prompt_contents = [types.Part(text="Test prompt")]
            with self.assertRaises(Exception) as context:
                gemini_service._call_gemini_api_with_model_cycling(
                    prompt_contents,
                    model_name="gemini-2.5-flash",
                    system_instruction_text="Test instruction",
                )

            # Verify error message
            self.assertIn("403 Forbidden", str(context.exception))

            # Verify we only tried once (auth errors are non-recoverable)
            self.assertEqual(mock_client.models.generate_content.call_count, 1)

    def test_unauthorized_error_handling(self):
        """Test that 401 unauthorized errors are non-recoverable"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create mock exception with 401 error
            error_401 = Exception("401 Unauthorized: Authentication required")
            error_401.status_code = 401

            # Mock generate_content to raise 401
            mock_client.models.generate_content.side_effect = error_401

            # Call the API and expect immediate failure
            prompt_contents = [types.Part(text="Test prompt")]
            with self.assertRaises(Exception) as context:
                gemini_service._call_gemini_api_with_model_cycling(
                    prompt_contents,
                    model_name="gemini-2.5-flash",
                    system_instruction_text="Test instruction",
                )

            # Verify error message
            self.assertIn("401 Unauthorized", str(context.exception))

            # Verify we only tried once (auth errors are non-recoverable)
            self.assertEqual(mock_client.models.generate_content.call_count, 1)

    # Group 4 - Model Fallback

    def test_model_not_found_fallback(self):
        """Test that 400 'model not found' errors trigger model cycling"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create a mock response for success
            mock_response = MagicMock()
            mock_response.text = '{"story": "Success with fallback model"}'

            # Create mock exception with 400 model not found error
            error_400 = Exception("400 Bad Request: Model not found")

            # Mock generate_content to fail with first model, succeed with second
            mock_client.models.generate_content.side_effect = [
                error_400,  # First model not found
                mock_response,  # Second model succeeds
            ]

            # Call the API
            prompt_contents = [types.Part(text="Test prompt")]
            result = gemini_service._call_gemini_api_with_model_cycling(
                prompt_contents,
                model_name="gemini-2.5-flash",
                system_instruction_text="Test instruction",
            )

            # Verify we got the successful response
            self.assertEqual(result, mock_response)

            # Verify we tried two models
            self.assertEqual(mock_client.models.generate_content.call_count, 2)

            # Verify correct model fallback order
            calls = mock_client.models.generate_content.call_args_list
            self.assertEqual(calls[0][1]["model"], "gemini-2.5-flash")
            self.assertEqual(
                calls[1][1]["model"], "gemini-2.5-flash-lite-preview-06-17"
            )

    def test_all_models_not_found(self):
        """Test that all models failing with 'not found' results in final error"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create mock exception with 400 model not found error
            error_400 = Exception("400 Bad Request: Model not found")

            # Mock generate_content to always fail with model not found
            mock_client.models.generate_content.side_effect = error_400

            # Call the API and expect failure after trying all models
            prompt_contents = [types.Part(text="Test prompt")]
            with self.assertRaises(Exception) as context:
                gemini_service._call_gemini_api_with_model_cycling(
                    prompt_contents,
                    model_name="gemini-2.5-flash",
                    system_instruction_text="Test instruction",
                )

            # Verify error message
            self.assertIn("400 Bad Request", str(context.exception))
            self.assertIn("not found", str(context.exception).lower())

            # Verify we tried all models in the fallback chain
            expected_attempts = len(gemini_service.MODEL_FALLBACK_CHAIN)
            self.assertEqual(
                mock_client.models.generate_content.call_count, expected_attempts
            )

    # Group 5 - Response Errors

    def test_empty_response_handling(self):
        """Test that empty responses are handled gracefully"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create mock response with empty text
            mock_response = MagicMock()
            mock_response.text = ""
            mock_response.candidates = []

            # Mock generate_content to return empty response
            mock_client.models.generate_content.return_value = mock_response

            # Call the API
            prompt_contents = [types.Part(text="Test prompt")]
            result = gemini_service._call_gemini_api_with_model_cycling(
                prompt_contents,
                model_name="gemini-2.5-flash",
                system_instruction_text="Test instruction",
            )

            # Verify we got the response (even if empty)
            self.assertEqual(result, mock_response)

            # Verify we only tried once (empty response is not an error)
            self.assertEqual(mock_client.models.generate_content.call_count, 1)

    def test_malformed_json_response_handling(self):
        """Test handling of malformed JSON in response"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Create mock response with malformed JSON
            mock_response = MagicMock()
            mock_response.text = '{"story": "Incomplete JSON'  # Missing closing brace

            # Mock generate_content to return malformed response
            mock_client.models.generate_content.return_value = mock_response

            # Call the API - should succeed (JSON parsing happens later)
            prompt_contents = [types.Part(text="Test prompt")]
            result = gemini_service._call_gemini_api_with_model_cycling(
                prompt_contents,
                model_name="gemini-2.5-flash",
                system_instruction_text="Test instruction",
            )

            # Verify we got the response (parsing happens in caller)
            self.assertEqual(result, mock_response)
            self.assertEqual(result.text, '{"story": "Incomplete JSON')

    def test_none_response_handling(self):
        """Test that None responses trigger error"""
        with patch("gemini_service.genai.Client") as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Mock generate_content to return None (simulating API failure)
            mock_client.models.generate_content.return_value = None

            # Call the API - should return None (let caller handle)
            prompt_contents = [types.Part(text="Test prompt")]
            result = gemini_service._call_gemini_api_with_model_cycling(
                prompt_contents,
                model_name="gemini-2.5-flash",
                system_instruction_text="Test instruction",
            )

            # Verify we got None response
            self.assertIsNone(result)

            # Verify we only tried once
            self.assertEqual(mock_client.models.generate_content.call_count, 1)


if __name__ == "__main__":
    unittest.main()
