#!/usr/bin/env python3
"""
Test for detection of old/deprecated tag formats in LLM responses.
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import unittest
from unittest.mock import patch

from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse


class TestOldTagDetection(unittest.TestCase):
    """Test that old/deprecated tags are properly detected and logged."""

    def setUp(self):
        """Set up test logging capture."""
        self.log_capture = []

    def test_detect_state_updates_proposed_in_narrative(self):
        """Test detection of [STATE_UPDATES_PROPOSED] blocks in narrative."""
        narrative_with_old_tags = """
        You enter the tavern. The barkeep greets you warmly.
        [STATE_UPDATES_PROPOSED]
        {
            "player_character_data": {
                "location": "Tavern"
            }
        }
        [END_STATE_UPDATES_PROPOSED]
        What would you like to do?
        """

        with (
            patch("gemini_response.logging.warning") as mock_warning,
            patch("gemini_response.logging.error") as mock_error,
        ):
            response = GeminiResponse(
                narrative_text=narrative_with_old_tags,
                provider="gemini",
                model="test-model",
            )

            # Check that warnings were logged
            assert mock_warning.called
            warning_messages = [call[0][0] for call in mock_warning.call_args_list]
            assert any("STATE_UPDATES_PROPOSED" in msg for msg in warning_messages)

            # Check that error summary was logged
            assert mock_error.called
            error_msg = mock_error.call_args[0][0]
            assert "DEPRECATED TAGS DETECTED" in error_msg

    def test_detect_debug_blocks_in_narrative(self):
        """Test detection of debug blocks in narrative."""
        narrative_with_debug = """
        You attack the goblin!
        [DEBUG_START]
        Roll: 1d20+5 = 18
        [DEBUG_END]
        You hit for 8 damage!
        """

        with patch("gemini_response.logging.warning") as mock_warning:
            response = GeminiResponse(
                narrative_text=narrative_with_debug,
                provider="gemini",
                model="test-model",
            )

            # Check warnings for debug tags
            warning_messages = [call[0][0] for call in mock_warning.call_args_list]
            assert any("DEBUG_START" in msg for msg in warning_messages)
            assert any("DEBUG_END" in msg for msg in warning_messages)

    def test_clean_narrative_no_warnings(self):
        """Test that clean narrative produces no warnings."""
        clean_narrative = """
        You enter the tavern. The barkeep greets you warmly.
        The atmosphere is lively with patrons enjoying their evening.
        """

        with (
            patch("gemini_response.logging.warning") as mock_warning,
            patch("gemini_response.logging.error") as mock_error,
        ):
            response = GeminiResponse(
                narrative_text=clean_narrative, provider="gemini", model="test-model"
            )

            # No warnings or errors should be logged
            assert not mock_warning.called
            assert not mock_error.called

    def test_metadata_includes_deprecated_tags(self):
        """Test that deprecated tags are stored in processing metadata."""
        narrative_with_multiple_tags = """
        [DEBUG_STATE_START]
        HP: 45/50
        [DEBUG_STATE_END]
        You feel stronger!
        [STATE_UPDATES_PROPOSED]
        {"hp": 50}
        [END_STATE_UPDATES_PROPOSED]
        """

        response = GeminiResponse(
            narrative_text=narrative_with_multiple_tags,
            provider="gemini",
            model="test-model",
        )

        # Check metadata
        assert "deprecated_tags_found" in response.processing_metadata
        tags_found = response.processing_metadata["deprecated_tags_found"]

        # Should have found state updates and debug blocks
        assert len(tags_found["state_updates_proposed"]) > 0
        assert len(tags_found["debug_blocks"]) > 0

    def test_detect_tags_in_structured_response(self):
        """Test detection of old tags within structured response fields."""
        # Create a structured response with old tags in debug info
        structured = NarrativeResponse(
            narrative="Clean narrative text",
            session_header="[SESSION_HEADER]\\nLocation: Tavern",
            planning_block="What next?",
            dice_rolls=[],
            resources="HP: 50/50",
            entities_mentioned=["barkeep"],
            location_confirmed="Tavern",
            state_updates={},
            debug_info={
                "dm_notes": [
                    "The [STATE_UPDATES_PROPOSED] block should be in state_updates field"
                ],
                "state_rationale": "Moving to tavern",
            },
        )

        with patch("gemini_response.logging.warning") as mock_warning:
            response = GeminiResponse(
                narrative_text="Clean narrative",
                provider="gemini",
                model="test-model",
                structured_response=structured,
            )

            # Should detect tag in structured response
            assert mock_warning.called
            warning_messages = [call[0][0] for call in mock_warning.call_args_list]
            assert any("structured response" in msg for msg in warning_messages)


if __name__ == "__main__":
    unittest.main()
