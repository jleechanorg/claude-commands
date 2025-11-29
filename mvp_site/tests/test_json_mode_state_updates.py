#!/usr/bin/env python3
"""Test that state updates work properly in JSON response mode."""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


import unittest

from mvp_site import logging_util
from mvp_site.llm_response import LLMResponse


class TestJsonModeStateUpdates(unittest.TestCase):
    """Test that state updates are properly extracted from JSON responses."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"
        logging_util.basicConfig(level=logging_util.INFO)

    def test_json_response_with_state_updates(self):
        """Test that state updates from JSON response are appended to response text."""
        # Create a JSON response with state updates
        json_response = {
            "narrative": "Drake swings his sword at the goblin, dealing a mighty blow!",
            "entities_mentioned": ["Drake", "goblin"],
            "location_confirmed": "Forest clearing",
            "state_updates": {
                "npc_data": {"goblin_001": {"hp_current": 0, "status": "Defeated"}},
                "player_character_data": {"xp_current": 150},
            },
        }

        raw_response = json.dumps(json_response)

        # Process the response using new API
        gemini_response = LLMResponse.create(raw_response)
        result = gemini_response.narrative_text
        structured_response = gemini_response.structured_response

        # Check that narrative is included
        assert "Drake swings his sword" in result

        # Check that state updates are NOT in the narrative text (bug fix)
        assert "[STATE_UPDATES_PROPOSED]" not in result
        assert "[END_STATE_UPDATES_PROPOSED]" not in result
        assert '"npc_data"' not in result
        assert '"goblin_001"' not in result

        # Check that state updates are in the structured response
        assert structured_response is not None
        assert structured_response.state_updates is not None
        assert (
            structured_response.state_updates["npc_data"]["goblin_001"]["hp_current"]
            == 0
        )
        assert (
            structured_response.state_updates["player_character_data"]["xp_current"]
            == 150
        )

        print("✅ JSON response with state updates properly converted")

    def test_json_response_without_state_updates(self):
        """Test that responses without state updates work correctly."""
        # Create a JSON response without state updates
        json_response = {
            "narrative": "Drake explores the peaceful forest.",
            "entities_mentioned": ["Drake"],
            "location_confirmed": "Forest",
        }

        raw_response = json.dumps(json_response)

        # Process the response using new API
        gemini_response = LLMResponse.create(raw_response)
        result = gemini_response.narrative_text

        # Check that narrative is included
        assert "Drake explores the peaceful forest" in result

        # Check that no STATE_UPDATES_PROPOSED block is added
        assert "[STATE_UPDATES_PROPOSED]" not in result

        print("✅ JSON response without state updates handled correctly")

    def test_json_response_with_empty_state_updates(self):
        """Test that empty state updates are handled correctly."""
        # Create a JSON response with empty state updates
        json_response = {
            "narrative": "The scene is quiet.",
            "entities_mentioned": [],
            "location_confirmed": "Town square",
            "state_updates": {},
        }

        raw_response = json.dumps(json_response)

        # Process the response using new API
        gemini_response = LLMResponse.create(raw_response)
        result = gemini_response.narrative_text

        # Check that narrative is included
        assert "The scene is quiet" in result

        # Check that no STATE_UPDATES_PROPOSED block is added for empty updates
        assert "[STATE_UPDATES_PROPOSED]" not in result

        print("✅ Empty state updates handled correctly")


if __name__ == "__main__":
    unittest.main()
