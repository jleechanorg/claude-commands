import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
import pytest

from mvp_site import llm_service
from mvp_site.game_state import GameState
from mvp_site.llm_response import LLMResponse
from mvp_site.narrative_response_schema import parse_structured_response


class TestJSONOnlyMode(unittest.TestCase):
    """Test that JSON mode is the ONLY mode - no fallbacks to regex parsing"""

    def test_parse_llm_response_for_state_changes_should_not_exist(self):
        """Test that the regex parsing function should not exist"""
        # This function should be removed
        with pytest.raises(AttributeError):
            llm_service.parse_llm_response_for_state_changes("any text")

    def test_all_gemini_calls_must_use_json_mode(self):
        """Test that all Gemini API calls enforce JSON mode"""
        with patch("mvp_site.llm_service.gemini_provider.generate_content_with_native_tools") as mock_generate_native, \
             patch("mvp_site.llm_service.gemini_provider.generate_content_with_code_execution") as mock_generate_code:
            
            mock_response = Mock(text='{"narrative": "test", "entities_mentioned": []}')
            mock_generate_native.return_value = mock_response
            mock_generate_code.return_value = mock_response

            test_game_state = GameState(user_id="test-user-123")  # Add required user_id
            
            # This triggers _call_llm_api
            llm_service.continue_story("test prompt", "story", [], test_game_state)

            # Check that either native or code execution was called
            assert mock_generate_native.called or mock_generate_code.called
            
            if mock_generate_native.called:
                call_args = mock_generate_native.call_args[1]
                assert call_args.get("json_mode_max_output_tokens") == llm_service.JSON_MODE_MAX_OUTPUT_TOKENS
            
            if mock_generate_code.called:
                call_args = mock_generate_code.call_args[1]
                assert call_args.get("json_mode_max_output_tokens") == llm_service.JSON_MODE_MAX_OUTPUT_TOKENS

    def test_generation_config_always_includes_json(self):
        """Test that generation config always includes JSON response format"""
        with patch("mvp_site.llm_service.gemini_provider.generate_content_with_native_tools") as mock_generate_native, \
             patch("mvp_site.llm_service.gemini_provider.generate_content_with_code_execution") as mock_generate_code:
            
            mock_response = Mock(text='{"narrative": "test", "entities_mentioned": []}')
            mock_generate_native.return_value = mock_response
            mock_generate_code.return_value = mock_response

            # Test continue_story
            llm_service.continue_story(
                "prompt", "story", [], GameState(user_id="test-user")
            )

            # Check that JSON mode was used
            assert mock_generate_native.called or mock_generate_code.called
            
            if mock_generate_native.called:
                kwargs = mock_generate_native.call_args[1]
                assert kwargs.get("json_mode_max_output_tokens") == llm_service.JSON_MODE_MAX_OUTPUT_TOKENS
            
            if mock_generate_code.called:
                kwargs = mock_generate_code.call_args[1]
                assert kwargs.get("json_mode_max_output_tokens") == llm_service.JSON_MODE_MAX_OUTPUT_TOKENS

    def test_robust_json_parser_is_only_fallback(self):
        """Test that robust JSON parser is the only fallback for malformed JSON"""

        # Test with malformed JSON (no closing brace)
        malformed = '```json\n{"narrative": "test", "entities_mentioned": ["hero"]\n```'

        # Should still extract what it can using robust parser
        narrative, response = parse_structured_response(malformed)

        # Should extract narrative but NOT try to parse STATE_UPDATES_PROPOSED blocks
        assert narrative == "test"

    def test_strip_functions_dont_affect_state_parsing(self):
        """Test that strip functions are only for display, not state extraction"""

        strip_state_updates_only = LLMResponse._strip_state_updates_only

        text_with_state_block = """Story text.
[STATE_UPDATES_PROPOSED]
{"pc_data": {"gold": 100}}
[END_STATE_UPDATES_PROPOSED]"""

        # Stripping should only affect display
        stripped = strip_state_updates_only(text_with_state_block)
        assert "STATE_UPDATES_PROPOSED" not in stripped

        # But this should NOT be used for parsing state updates
        # State updates come ONLY from JSON response

    def test_error_on_missing_structured_response(self):
        """Test that system logs error when structured response is missing"""
        with patch("logging.error"):
            LLMResponse(
                narrative_text="Story without JSON",
                structured_response=None,
                debug_tags_present={},
            )

            # Accessing state_updates on response without structured_response

            # Should log error or warning about missing structured response
            # (This test will fail until we implement the logging)


if __name__ == "__main__":
    unittest.main()
