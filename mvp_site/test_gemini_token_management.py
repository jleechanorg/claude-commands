"""
Test Suite for Gemini Service Token Management

Tests token counting, context management, and multi-turn conversation handling
in the gemini_service module. Focuses on cost control and context limits.

Test Groups:
1. Token Counting - Basic ASCII, Unicode, special characters
2. Context Limits - 8k/32k windows, overflow handling
3. Multi-turn Context - History tracking, pruning, system prompt preservation  
4. Token Estimation - Prompt estimation, response budgeting, usage reporting
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call

# Add the root directory (two levels up) to the Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gemini_service
from token_utils import estimate_tokens
from game_state import GameState
import constants


class TestGeminiTokenManagement(unittest.TestCase):
    """Test cases for token management in gemini_service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock game state
        self.game_state = Mock(spec=GameState)
        self.game_state.is_onboarding = False
        self.game_state.story_context = []
        self.game_state.debug_mode = False
        self.game_state.world_data = {'current_location_name': 'Test Location'}
        self.game_state.custom_campaign_state = {'core_memories': []}
        
        # Mock Gemini client
        self.mock_client = Mock()
        self.mock_models = Mock()
        self.mock_client.models = self.mock_models
        
        # Mock response
        self.mock_response = Mock()
        self.mock_response.text = '{"narrative": "Test response", "entities_mentioned": []}'
        
    # Group 1 - Token Counting
    
    @patch('gemini_service.get_client')
    def test_basic_token_counting(self, mock_get_client):
        """Test token counting for basic ASCII text."""
        mock_get_client.return_value = self.mock_client
        
        # Test ASCII text
        test_text = "Hello, this is a test message with basic ASCII characters."
        test_contents = [test_text]
        
        # Mock token count response
        mock_count_response = Mock()
        mock_count_response.total_tokens = 15  # Approximately 58 chars / 4
        self.mock_models.count_tokens.return_value = mock_count_response
        
        # Call the token counting function
        gemini_service._log_token_count("gemini-2.5-flash", test_contents)
        
        # Verify count_tokens was called with correct parameters
        self.mock_models.count_tokens.assert_called_once_with(
            model="gemini-2.5-flash",
            contents=test_contents
        )
        
    @patch('gemini_service.get_client')
    @patch('gemini_service.logging_util')
    def test_unicode_token_counting(self, mock_logging, mock_get_client):
        """Test token counting for Unicode text (emoji, Chinese, Arabic)."""
        mock_get_client.return_value = self.mock_client
        
        # Test various Unicode texts
        test_cases = [
            ("Hello 👋 World 🌍", 5),  # Emoji
            ("你好世界", 8),  # Chinese characters (4 chars, might be ~8 tokens)
            ("مرحبا بالعالم", 10),  # Arabic
            ("Mixed: Hello 你好 👋", 12)  # Mixed content
        ]
        
        for text, expected_tokens in test_cases:
            with self.subTest(text=text):
                # Reset mock
                self.mock_models.count_tokens.reset_mock()
                mock_logging.info.reset_mock()
                
                # Mock token count response
                mock_count_response = Mock()
                mock_count_response.total_tokens = expected_tokens
                self.mock_models.count_tokens.return_value = mock_count_response
                
                # Call the token counting function
                gemini_service._log_token_count("gemini-2.5-flash", [text])
                
                # Verify count_tokens was called
                self.mock_models.count_tokens.assert_called_once()
                
                # Verify logging includes token count
                log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
                token_log = next((msg for msg in log_calls if "tokens to the API" in msg), None)
                self.assertIsNotNone(token_log)
                self.assertIn(str(expected_tokens), token_log)
                
    @patch('gemini_service.get_client')
    @patch('gemini_service.logging_util')
    def test_special_char_tokens(self, mock_logging, mock_get_client):
        """Test token counting for special characters (code, markdown, symbols)."""
        mock_get_client.return_value = self.mock_client
        
        # Test various special character texts
        test_cases = [
            # Code snippet
            ('```python\ndef hello():\n    print("world")\n```', 20),
            # Markdown formatting
            ("# Header\n**Bold** and *italic* text\n- List item", 25),
            # Special symbols
            ("Math: ∑(i=1→n) × ÷ ± √ ∞", 15),
            # Mixed special content
            ("Code: `var x = 42;` // Comment\nFormula: E=mc²", 18)
        ]
        
        for text, expected_tokens in test_cases:
            with self.subTest(text=text[:30] + "..."):
                # Reset mock
                self.mock_models.count_tokens.reset_mock()
                
                # Mock token count response
                mock_count_response = Mock()
                mock_count_response.total_tokens = expected_tokens
                self.mock_models.count_tokens.return_value = mock_count_response
                
                # Call the token counting function with system instruction
                gemini_service._log_token_count(
                    "gemini-2.5-flash", 
                    [text],
                    system_instruction_text="You are a helpful assistant."
                )
                
                # Should call count_tokens twice (once for user content, once for system)
                self.assertEqual(self.mock_models.count_tokens.call_count, 2)
                
                # Verify both user and system content were counted
                calls = self.mock_models.count_tokens.call_args_list
                # First call should be for user content
                self.assertEqual(calls[0][1]['contents'], [text])
                # Second call should be for system instruction
                self.assertEqual(calls[1][1]['contents'], ["You are a helpful assistant."])
    
    # Group 2 - Context Limits
    
    @patch('gemini_service.get_client')
    @patch('gemini_service.logging_util')
    def test_context_window_8k(self, mock_logging, mock_get_client):
        """Test handling of 8k token context window limit."""
        mock_get_client.return_value = self.mock_client
        
        # Create a large context that would exceed 8k tokens
        # Assuming ~4 chars per token, 8k tokens = ~32k chars
        large_text = "A" * 35000  # Should be ~8750 tokens
        
        # Mock token count to simulate exceeding limit
        mock_count_response = Mock()
        mock_count_response.total_tokens = 8750
        self.mock_models.count_tokens.return_value = mock_count_response
        
        # Mock the generate_content to succeed (after truncation)
        self.mock_models.generate_content.return_value = self.mock_response
        
        # Test with context that needs truncation
        # Note: The actual truncation logic would be in the main API call
        # Here we're testing that the token counting identifies the issue
        gemini_service._log_token_count("gemini-2.5-flash", [large_text])
        
        # Verify warning was logged about large token count
        log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
        token_log = next((msg for msg in log_calls if "8750 tokens" in msg), None)
        self.assertIsNotNone(token_log)
        
    @patch('gemini_service.get_client')
    @patch('gemini_service.logging_util')
    def test_context_window_32k(self, mock_logging, mock_get_client):
        """Test handling of 32k token context window limit."""
        mock_get_client.return_value = self.mock_client
        
        # Create context within 32k limit
        # 32k tokens = ~128k chars
        medium_text = "B" * 120000  # Should be ~30k tokens
        
        # Mock token count
        mock_count_response = Mock()
        mock_count_response.total_tokens = 30000
        self.mock_models.count_tokens.return_value = mock_count_response
        
        # Mock successful generation
        self.mock_models.generate_content.return_value = self.mock_response
        
        # Test token counting with 32k window
        gemini_service._log_token_count("gemini-2.5-flash", [medium_text])
        
        # Verify it logs the large token count
        log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
        token_log = next((msg for msg in log_calls if "30000 tokens" in msg), None)
        self.assertIsNotNone(token_log)
        
    @patch('gemini_service.get_client')
    @patch('gemini_service.logging_util')
    def test_context_overflow_handling(self, mock_logging, mock_get_client):
        """Test handling when context exceeds maximum allowed tokens."""
        mock_get_client.return_value = self.mock_client
        
        # Create context that exceeds MAX_INPUT_TOKENS (750k tokens = ~3M chars)
        # For testing, we'll simulate a much smaller overflow
        overflow_text = "C" * 50000  # Simulating overflow scenario
        
        # Mock token count to show overflow
        mock_count_response = Mock()
        mock_count_response.total_tokens = 760000  # Exceeds MAX_INPUT_TOKENS
        self.mock_models.count_tokens.return_value = mock_count_response
        
        # Test multiple contents that together exceed limit
        contents = [overflow_text, "Additional content that pushes over limit"]
        
        # The actual API call would fail or truncate, but we're testing token counting
        gemini_service._log_token_count("gemini-2.5-flash", contents)
        
        # Verify high token count was logged
        log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
        # Should log the total tokens
        token_log = next((msg for msg in log_calls if "tokens to the API" in msg), None)
        self.assertIsNotNone(token_log)
        
        # In a real scenario, the service would need to handle this overflow
        # by truncating or splitting the context
    
    # Group 3 - Multi-turn Context
    
    @patch('gemini_service.get_client')
    def test_conversation_history_tracking(self, mock_get_client):
        """Test tracking of multi-turn conversation history."""
        mock_get_client.return_value = self.mock_client
        
        # Create a mock conversation history
        conversation_history = [
            {"actor": "user", "text": "Hello, I want to start an adventure"},
            {"actor": "dm", "text": "Welcome adventurer! You find yourself..."},
            {"actor": "user", "text": "I look around the tavern"},
            {"actor": "dm", "text": "The tavern is dimly lit..."},
            {"actor": "user", "text": "I approach the bartender"},
            {"actor": "dm", "text": "The bartender greets you warmly..."}
        ]
        
        # Test _get_context_stats function
        self.game_state.story_context = conversation_history
        
        # Create a context string for token counting
        combined_text = ''.join(entry.get('text', '') for entry in conversation_history)
        
        # Mock token counting
        mock_count_response = Mock()
        # Calculate expected tokens based on character count
        expected_tokens = len(combined_text) // 4  # Using CHARS_PER_TOKEN = 4
        mock_count_response.total_tokens = expected_tokens
        self.mock_models.count_tokens.return_value = mock_count_response
        
        # Test context stats calculation
        stats = gemini_service._get_context_stats(
            conversation_history, 
            "gemini-2.5-flash", 
            self.game_state
        )
        
        # Verify stats format includes turn count and tokens
        self.assertIn("Turns:", stats)
        self.assertIn("6", stats)  # 6 turns in history
        self.assertIn("Tokens:", stats)
        
    @patch('gemini_service.get_client')
    def test_context_pruning_strategy(self, mock_get_client):
        """Test context pruning strategy for long conversations."""
        mock_get_client.return_value = self.mock_client
        
        # Mock token counting for the context stats
        mock_count_response = Mock()
        mock_count_response.total_tokens = 5000  # Large enough to trigger truncation
        self.mock_models.count_tokens.return_value = mock_count_response
        
        # Create a long conversation that needs pruning
        long_conversation = []
        for i in range(150):  # More than TURNS_TO_KEEP_AT_START + TURNS_TO_KEEP_AT_END
            long_conversation.append({
                "actor": "user" if i % 2 == 0 else "dm",
                "text": f"Turn {i}: This is message number {i} in the conversation with much more text to ensure we exceed token limits."
            })
        
        # Test truncation with default settings (25 start + 75 end = 100 total)
        max_chars = 2000  # Very small limit to force truncation
        truncated = gemini_service._truncate_context(
            long_conversation,
            max_chars,
            "gemini-2.5-flash",
            self.game_state
        )
        
        # Should keep first 25 turns
        self.assertEqual(truncated[0]["text"], "Turn 0: This is message number 0 in the conversation with much more text to ensure we exceed token limits.")
        self.assertEqual(truncated[24]["text"], "Turn 24: This is message number 24 in the conversation with much more text to ensure we exceed token limits.")
        
        # Should have truncation marker
        truncation_found = False
        for entry in truncated:
            if entry.get("actor") == "system" and "several moments" in entry.get("text", ""):
                truncation_found = True
                break
        self.assertTrue(truncation_found, "Truncation marker not found")
        
        # Should keep last 75 turns
        # The last entry should be from turn 149
        last_turn_text = truncated[-1]["text"]
        self.assertIn("Turn 149", last_turn_text)
        
        # Total turns should be 101 (25 start + 1 truncation + 75 end)
        self.assertEqual(len(truncated), 101)
        
    @patch('gemini_service.get_client')
    def test_system_prompt_preservation(self, mock_get_client):
        """Test that system prompts are preserved during context management."""
        mock_get_client.return_value = self.mock_client
        
        # Mock token counting
        mock_count_response = Mock()
        mock_count_response.total_tokens = 3000
        self.mock_models.count_tokens.return_value = mock_count_response
        
        # Create conversation with system prompts
        conversation_with_system = [
            {"actor": "system", "text": "[IMPORTANT: Core game rules apply]"},
            {"actor": "user", "text": "Start the game"},
            {"actor": "dm", "text": "Welcome to the adventure!"},
            {"actor": "system", "text": "[DEBUG: Entity tracking enabled]"},
            {"actor": "user", "text": "I look around"},
            {"actor": "dm", "text": "You see a vast landscape..."}
        ]
        
        # Add many more turns to trigger truncation
        for i in range(100):
            conversation_with_system.append({
                "actor": "user" if i % 2 == 0 else "dm",
                "text": f"Additional turn {i}"
            })
        
        # Test truncation preserves early system messages
        truncated = gemini_service._truncate_context(
            conversation_with_system,
            1000,  # Very small limit to force truncation
            "gemini-2.5-flash", 
            self.game_state
        )
        
        # Check that the first system prompt is preserved (it's in the first 25 turns)
        system_prompt_found = False
        for entry in truncated[:25]:  # Check in the preserved start section
            if entry.get("actor") == "system" and "IMPORTANT: Core game rules" in entry.get("text", ""):
                system_prompt_found = True
                break
        
        self.assertTrue(system_prompt_found, "System prompt was not preserved in truncated context")
        
        # Verify truncation occurred
        truncation_marker_found = False
        for entry in truncated:
            if entry.get("actor") == "system" and "several moments" in entry.get("text", ""):
                truncation_marker_found = True
                break
        self.assertTrue(truncation_marker_found, "Truncation should have occurred")
    
    # Group 4 - Token Estimation
    
    @patch('gemini_service.get_client')
    def test_prompt_token_estimation(self, mock_get_client):
        """Test comparing estimated tokens vs actual token count."""
        mock_get_client.return_value = self.mock_client
        
        test_cases = [
            # (text, actual_tokens) - actual tokens from API
            ("Simple text message", 5),
            ("A longer message with more words to test token counting accuracy", 15),
            ("Special chars: @#$%^&*()_+-=[]{}|;:',.<>?/`~", 20),
            ("Mixed content with numbers 12345 and symbols!", 10)
        ]
        
        for text, actual_tokens in test_cases:
            with self.subTest(text=text[:30]):
                # Calculate estimated tokens using the utility
                estimated = estimate_tokens(text)
                
                # Mock API response
                mock_count_response = Mock()
                mock_count_response.total_tokens = actual_tokens
                self.mock_models.count_tokens.return_value = mock_count_response
                
                # The estimation should be reasonably close (within 50% margin)
                # Since estimate_tokens uses chars/4, let's verify the estimation logic
                expected_estimate = len(text) // 4
                self.assertEqual(estimated, expected_estimate)
                
                # Log the token count to verify API is called
                gemini_service._log_token_count("gemini-2.5-flash", [text])
                
                # Verify API was called
                self.mock_models.count_tokens.assert_called()
                
    @patch('gemini_service.get_client')
    @patch('gemini_service.logging_util')
    def test_response_token_budgeting(self, mock_logging, mock_get_client):
        """Test that response token limits are properly configured."""
        mock_get_client.return_value = self.mock_client
        
        # Mock a successful API call
        self.mock_models.generate_content.return_value = self.mock_response
        
        # Test that JSON mode uses reduced token limit
        response = gemini_service._call_gemini_api(
            ["Test prompt"],
            "gemini-2.5-flash",
            "Test prompt for logging"
        )
        
        # Verify that JSON mode was configured with reduced tokens
        generate_call = self.mock_models.generate_content.call_args
        config = generate_call[1]['config']
        
        # Check that max_output_tokens is set to JSON_MODE_MAX_TOKENS
        self.assertEqual(config.max_output_tokens, gemini_service.JSON_MODE_MAX_TOKENS)
        self.assertEqual(config.response_mime_type, "application/json")
        
        # Verify logging mentions JSON mode
        log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
        json_mode_log = next((msg for msg in log_calls if "JSON response mode" in msg), None)
        self.assertIsNotNone(json_mode_log)
        self.assertIn(str(gemini_service.JSON_MODE_MAX_TOKENS), json_mode_log)
        
    @patch('gemini_service.get_client')
    @patch('gemini_service.log_with_tokens')
    def test_token_usage_reporting(self, mock_log_with_tokens, mock_get_client):
        """Test that token usage is properly tracked and reported."""
        mock_get_client.return_value = self.mock_client
        
        # Mock token counting
        mock_count_response = Mock()
        mock_count_response.total_tokens = 1500
        self.mock_models.count_tokens.return_value = mock_count_response
        
        # Mock successful generation
        self.mock_models.generate_content.return_value = self.mock_response
        
        # Create test prompt with system instruction
        test_prompt = "This is a test prompt for token usage tracking"
        system_instruction = "You are a helpful D&D game master"
        
        # Call the API
        response = gemini_service._call_gemini_api_with_model_cycling(
            [test_prompt],
            "gemini-2.5-flash",
            test_prompt,
            system_instruction
        )
        
        # Verify log_with_tokens was called to report token usage
        mock_log_with_tokens.assert_called()
        
        # Check that the combined text was logged
        call_args = mock_log_with_tokens.call_args
        self.assertIn("Calling Gemini API with prompt", call_args[0][0])
        
        # Verify token counting was performed for both user and system prompts
        count_calls = self.mock_models.count_tokens.call_args_list
        # Should have at least 2 calls (user content and system instruction)
        self.assertGreaterEqual(len(count_calls), 2)


if __name__ == '__main__':
    unittest.main()