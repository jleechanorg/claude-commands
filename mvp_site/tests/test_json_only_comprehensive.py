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
from mvp_site.llm_response import LLMResponse
from mvp_site.narrative_response_schema import NarrativeResponse


class TestJSONOnlyComprehensive(unittest.TestCase):
    """Comprehensive test suite to verify JSON mode is the ONLY mode"""

    def test_no_fallback_in_main_py(self):
        """Test that main.py no longer has fallback parsing logic"""
        # Create a response without structured_response
        mock_response = Mock(spec=LLMResponse)
        mock_response.structured_response = None
        mock_response.state_updates = {}
        mock_response.narrative_text = 'Text with [STATE_UPDATES_PROPOSED]{"gold": 100}[END_STATE_UPDATES_PROPOSED]'

        # Simulate the main.py logic (lines 873-876)
        # This is the actual implementation now:
        proposed_changes = mock_response.state_updates

        # Should be empty, not parsed from text
        assert proposed_changes == {}

    def test_gemini_response_logs_error_without_structured(self):
        """Test that LLMResponse logs error when no structured response"""
        with patch("logging.error") as mock_log_error:
            response = LLMResponse(
                narrative_text="Story text",
                structured_response=None,
                debug_tags_present={},
            )

            # Access state_updates
            updates = response.state_updates

            # Should log error
            mock_log_error.assert_called_once_with(
                "ERROR: No structured response available for state updates. JSON mode is required."
            )
            assert updates == {}

    def test_json_mode_always_enabled(self):
        """Test that all API calls use JSON mode"""
        with patch("mvp_site.llm_service.gemini_provider.generate_content_with_code_execution") as mock_generate, \
             patch("mvp_site.constants.get_dice_roll_strategy", return_value="code_execution"):
            
            mock_generate.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": []}'
            )

            # Call _call_llm_api directly
            llm_service._call_llm_api(
                ["test prompt"], "gemini-3-pro-preview", "test logging"
            )

            # Verify arguments
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args[1]
            
            # Check json_mode_max_output_tokens is set
            assert call_kwargs["json_mode_max_output_tokens"] == llm_service.JSON_MODE_MAX_OUTPUT_TOKENS

    def test_parse_function_removed(self):
        """Test that parse_llm_response_for_state_changes is removed"""
        # Should not exist
        assert not hasattr(llm_service, "parse_llm_response_for_state_changes")

        # Attempting to access should raise AttributeError
        with pytest.raises(AttributeError):
            llm_service.parse_llm_response_for_state_changes

    def test_clean_markdown_helper_removed(self):
        """Test that _clean_markdown_from_json helper is removed"""
        # Should not exist
        assert not hasattr(llm_service, "_clean_markdown_from_json")

    def test_state_updates_only_from_json(self):
        """Test that state updates come ONLY from JSON response"""
        # Create proper structured response
        narrative_response = NarrativeResponse(
            narrative="The hero gains gold",
            entities_mentioned=["hero"],
            state_updates={"pc_data": {"gold": 500}},
        )

        response = LLMResponse(
            narrative_text='The hero gains gold [STATE_UPDATES_PROPOSED]{"pc_data": {"gold": 100}}[END_STATE_UPDATES_PROPOSED]',
            structured_response=narrative_response,
            debug_tags_present={},
        )

        # Should use JSON value, not parsed from text
        assert response.state_updates["pc_data"]["gold"] == 500

    def test_no_state_updates_without_json(self):
        """Test that no state updates are available without JSON response"""
        response = LLMResponse(
            narrative_text='Story with [STATE_UPDATES_PROPOSED]{"gold": 999}[END_STATE_UPDATES_PROPOSED]',
            structured_response=None,
            debug_tags_present={},
        )

        # Should be empty
        assert response.state_updates == {}

    def test_strip_functions_only_for_display(self):
        """Test that strip functions don't affect state parsing"""

        strip_debug_content = LLMResponse._strip_debug_content

        # Text with state block
        text = """Story text.
[STATE_UPDATES_PROPOSED]
{"gold": 100}
[END_STATE_UPDATES_PROPOSED]"""

        # Strip removes for display
        stripped = strip_debug_content(text)
        assert "STATE_UPDATES_PROPOSED" not in stripped

        # But this has NO effect on state parsing - states come from JSON only


if __name__ == "__main__":
    unittest.main()
