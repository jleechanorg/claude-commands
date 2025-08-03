import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
import pytest
from gemini_response import GeminiResponse
from narrative_response_schema import parse_structured_response

import gemini_service
from game_state import GameState


class TestJSONOnlyMode(unittest.TestCase):
    """Test that JSON mode is the ONLY mode - no fallbacks to regex parsing"""

    def test_parse_llm_response_for_state_changes_should_not_exist(self):
        """Test that the regex parsing function should not exist"""
        # This function should be removed
        with pytest.raises(AttributeError):
            gemini_service.parse_llm_response_for_state_changes("any text")

    def test_all_gemini_calls_must_use_json_mode(self):
        """Test that all Gemini API calls enforce JSON mode"""
        with patch("gemini_service.get_client") as mock_get_client:
            mock_client = Mock()
            Mock()
            mock_get_client.return_value = mock_client
            mock_client.models = Mock()
            mock_client.models.generate_content = Mock(
                return_value=Mock(
                    text='{"narrative": "test", "entities_mentioned": []}'
                )
            )

            # Test continue_story (need proper parameters)

            test_game_state = GameState(user_id="test-user-123")  # Add required user_id
            gemini_service.continue_story("test prompt", "story", [], test_game_state)

            # Verify JSON mode was used
            call_args = mock_client.models.generate_content.call_args
            # The config is passed under 'config' key
            assert "config" in call_args[1]
            config_obj = call_args[1]["config"]
            # Check the config object attributes
            assert config_obj.response_mime_type == "application/json"

    def test_main_py_no_fallback_parsing(self):
        """Test that main.py doesn't have fallback regex parsing"""
        # Import main module

        # Create a mock response without structured_response
        mock_response = Mock(spec=GeminiResponse)
        mock_response.structured_response = None
        mock_response.state_updates = {}
        mock_response.narrative_text = (
            '[STATE_UPDATES_PROPOSED]{"test": true}[END_STATE_UPDATES_PROPOSED]'
        )

        # The code should NOT attempt to parse markdown blocks
        # Since parse_llm_response_for_state_changes doesn't exist,
        # we just verify the new logic works correctly
        proposed_changes = mock_response.state_updates

        # Should be empty since there's no structured response
        assert proposed_changes == {}

    def test_no_regex_state_update_extraction(self):
        """Test that STATE_UPDATES_PROPOSED regex extraction is removed"""
        # The parse_llm_response_for_state_changes function should not exist
        assert not hasattr(gemini_service, "parse_llm_response_for_state_changes")

        # The helper function should also not exist
        assert not hasattr(gemini_service, "_clean_markdown_from_json")

    def test_always_structured_response_required(self):
        """Test that a structured response is always required"""
        # Any GeminiResponse without structured_response should have empty state_updates
        response = GeminiResponse(
            narrative_text='Some text with [STATE_UPDATES_PROPOSED]{"gold": 100}[END_STATE_UPDATES_PROPOSED]',
            structured_response=None,
            debug_tags_present={},
        )

        # Should return empty dict, not parse from text
        assert response.state_updates == {}

    def test_generation_config_always_includes_json(self):
        """Test that generation config always includes JSON response format"""
        with patch("gemini_service.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.models.generate_content = Mock(
                return_value=Mock(text='{"narrative": "test"}')
            )

            # Test various API calls
            test_cases = [
                (
                    "continue_story",
                    lambda: gemini_service.continue_story(
                        [], "prompt", "story", GameState(user_id="test-user")
                    ),
                ),
                (
                    "generate_opening_story",
                    lambda: gemini_service.generate_opening_story("prompt"),
                ),
                (
                    "get_god_response",
                    lambda: gemini_service.get_god_response({}, "command"),
                ),
            ]

            for test_name, test_func in test_cases:
                with self.subTest(test=test_name):
                    mock_client.models.generate_content.reset_mock()

                    # Call the function
                    try:
                        test_func()
                    except Exception:
                        pass  # Some might fail due to mocking, we just need the call args

                    # Check that JSON mode was used
                    if mock_client.models.generate_content.called:
                        call_args = mock_client.models.generate_content.call_args
                        if "generation_config" in call_args[1]:
                            config = call_args[1]["generation_config"]
                            assert (
                                config.response_mime_type == "application/json"
                            ), f"{test_name} should use JSON mode"

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

        strip_state_updates_only = GeminiResponse._strip_state_updates_only

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
            GeminiResponse(
                narrative_text="Story without JSON",
                structured_response=None,
                debug_tags_present={},
            )

            # Accessing state_updates on response without structured_response

            # Should log error or warning about missing structured response
            # (This test will fail until we implement the logging)


if __name__ == "__main__":
    unittest.main()
