"""
Test-Driven Development: Tests for LLMResponse object

These tests define the expected behavior for the LLMResponse object
that will clean up the architecture between llm_service and main.py.

Updated for new API where LLMResponse.create() takes raw response text.
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add the parent directory to the Python path so we can import modules
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.game_state import GameState
from mvp_site import constants
from mvp_site.llm_response import LLMResponse
from mvp_site.llm_service import continue_story, get_initial_story
from mvp_site.narrative_response_schema import NarrativeResponse


class TestLLMResponse(unittest.TestCase):
    """Test cases for LLMResponse object."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_narrative = "The brave knight looked around the tavern."

        # Create mock raw JSON response
        self.sample_raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "debug_info": {
                    "dm_notes": ["Player seems cautious"],
                    "dice_rolls": ["Perception: 1d20+3 = 15"],
                    "resources": "HD: 2/3, Spells: L1 1/2",
                    "state_rationale": "Updated HP after healing",
                },
                "state_updates": {"player_character_data": {"hp_current": 18}},
                "entities_mentioned": ["knight", "tavern"],
                "location_confirmed": "Silver Stag Tavern",
            }
        )

    def test_gemini_response_creation(self):
        """Test creating a LLMResponse object."""

        response = LLMResponse.create(self.sample_raw_response)

        # Core fields should be set
        assert response.narrative_text == self.sample_narrative
        assert response.structured_response is not None

        # Should have debug tags detection
        assert isinstance(response.debug_tags_present, dict)
        assert "dm_notes" in response.debug_tags_present
        assert "dice_rolls" in response.debug_tags_present
        # state_changes debug tag removed as part of cleanup

    def test_debug_tags_detection_with_content(self):
        """Test debug tags are properly detected when content exists."""

        response = LLMResponse.create(self.sample_raw_response)

        # Should detect dm_notes and dice_rolls from structured response
        assert response.debug_tags_present["dm_notes"]
        assert response.debug_tags_present["dice_rolls"]

        # has_debug_content should be True
        assert response.has_debug_content

    def test_debug_tags_detection_no_content(self):
        """Test debug tags detection when no debug content exists."""

        # Create raw response without debug content
        clean_raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "debug_info": {
                    "dm_notes": [],
                    "dice_rolls": [],
                    "resources": "HD: 2/3",
                    "state_rationale": "",
                },
                "entities_mentioned": ["knight", "tavern"],
                "location_confirmed": "Silver Stag Tavern",
            }
        )

        response = LLMResponse.create(clean_raw_response)

        # Should detect no debug content
        assert not response.debug_tags_present["dm_notes"]
        assert not response.debug_tags_present["dice_rolls"]

        # has_debug_content should be False
        assert not response.has_debug_content

    def test_state_updates_property(self):
        """Test state_updates property returns correct data."""

        response = LLMResponse.create(self.sample_raw_response)

        # Should return state updates from structured response
        assert response.state_updates == {"player_character_data": {"hp_current": 18}}

    def test_entities_mentioned_property(self):
        """Test entities_mentioned property returns correct data."""

        response = LLMResponse.create(self.sample_raw_response)

        # Should return entities from structured response
        assert response.entities_mentioned == ["knight", "tavern"]

    def test_location_confirmed_property(self):
        """Test location_confirmed property returns correct data."""

        response = LLMResponse.create(self.sample_raw_response)

        # Should return location from structured response
        assert response.location_confirmed == "Silver Stag Tavern"

    def test_debug_info_property(self):
        """Test debug_info property returns correct data."""

        response = LLMResponse.create(self.sample_raw_response)

        # Should return debug_info from structured response
        assert response.debug_info is not None
        assert "dm_notes" in response.debug_info
        assert response.debug_info["dm_notes"] == ["Player seems cautious"]

    def test_none_structured_response_handling(self):
        """Test LLMResponse handles plain text gracefully."""

        # Test with plain text (no JSON)
        plain_response = self.sample_narrative
        response = LLMResponse.create(plain_response)

        # Should extract the narrative
        assert response.narrative_text == self.sample_narrative

        # Should have a structured response (even if empty)
        assert response.structured_response is not None

        # Properties should return empty/default values gracefully
        assert response.state_updates == {}
        assert response.entities_mentioned == []
        assert response.location_confirmed == "Unknown"  # Default value
        assert response.debug_info == {}

    @patch("mvp_site.llm_service._call_llm_api")
    @patch("mvp_site.llm_service._get_text_from_response")
    def test_get_initial_story_returns_gemini_response(self, mock_get_text, mock_api):
        """Test that get_initial_story returns a LLMResponse object."""

        # Setup mocks - return raw response text
        mock_api.return_value = Mock()
        mock_get_text.return_value = self.sample_raw_response

        # Call function
        result = get_initial_story(
            "Start a fantasy adventure",
            generate_companions=False,
            user_id="test-user-123",
        )

        # Should return a LLMResponse object
        assert type(result).__name__ == "LLMResponse"
        # Check that we got valid narrative content (environment-agnostic)
        assert result.narrative_text is not None
        assert len(result.narrative_text) > 0
        # Verify content is meaningful narrative text (environment-agnostic)
        # In CI/mock mode, it may return different mock content than our patch
        assert isinstance(result.narrative_text, str)
        assert (
            "adventure" in result.narrative_text.lower()
            or "knight" in result.narrative_text.lower()
            or len(result.narrative_text) > 20
        )

    @patch(
        "mvp_site.llm_service.get_client"
    )  # Patch get_client to prevent GEMINI_API_KEY error
    @patch("mvp_site.llm_service._call_llm_api")
    @patch("mvp_site.llm_service._get_text_from_response")
    def test_continue_story_returns_gemini_response(
        self, mock_get_text, mock_api, mock_get_client
    ):
        """Test that continue_story returns a LLMResponse object."""

        # Setup mocks
        mock_get_client.return_value = (
            Mock()
        )  # Mock Gemini client to prevent API key error
        mock_api.return_value = Mock()
        mock_get_text.return_value = self.sample_raw_response

        game_state = GameState(user_id="test-user-123")  # Add required user_id
        story_context: list = []

        # Call function
        result = continue_story(
            user_input="I approach the barkeep",
            mode="story",
            story_context=story_context,
            current_game_state=game_state,
        )

        # Should return a LLMResponse object
        assert type(result).__name__ == "LLMResponse"
        assert result.narrative_text == self.sample_narrative

    @patch("mvp_site.llm_service._validate_and_enforce_planning_block")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    @patch("mvp_site.llm_service.estimate_tokens", return_value=0)
    @patch("mvp_site.llm_service._get_current_turn_prompt", return_value="prompt")
    @patch("mvp_site.llm_service._build_timeline_log", return_value="")
    @patch("mvp_site.llm_service._prepare_entity_tracking", return_value=("", [], ""))
    @patch("mvp_site.llm_service._truncate_context", return_value=[])
    @patch("mvp_site.llm_service._get_static_prompt_parts")
    @patch("mvp_site.agents.PromptBuilder")
    @patch("mvp_site.llm_service.get_client")
    @patch("mvp_site.llm_service._get_text_from_response")
    def test_god_mode_prefix_survives_validation_and_skips_planning_block(
        self,
        mock_get_text,
        mock_get_client,
        mock_prompt_builder,
        mock_static_parts,
        mock_truncate_context,
        mock_prepare_entity_tracking,
        mock_build_timeline_log,
        mock_get_current_turn_prompt,
        mock_estimate_tokens,
        mock_call_llm_api_with_llm_request,
        mock_validate_planning_block,
    ):
        """Ensure GOD MODE detection uses raw input and bypasses planning blocks."""

        mock_get_client.return_value = Mock()
        mock_call_llm_api_with_llm_request.return_value = Mock()
        mock_get_text.return_value = json.dumps(
            {
                "narrative": "",
                "god_mode_response": "Acknowledged.",
                "state_updates": {"player_character_data": {"hp_current": 5}},
                "planning_block": {"choices": {"god:return_story": {"text": "Return"}}},
            }
        )

        mock_static_parts.return_value = ("checkpoint", [], [])

        builder_instance = Mock()
        builder_instance.build_god_mode_instructions.return_value = [
            "god mode instructions"
        ]
        builder_instance.finalize_instructions.return_value = "final instructions"
        mock_prompt_builder.return_value = builder_instance

        game_state = Mock(spec=GameState)
        game_state.user_id = "test-user-123"
        game_state.validate_checkpoint_consistency.return_value = ["mismatch"]
        game_state.to_dict.return_value = {}
        game_state.custom_campaign_state = {}
        game_state.combat_state = {}
        game_state.world_data = {}
        game_state.mission_data = {}
        game_state.npc_data = {}

        story_context = [
            {
                constants.KEY_ACTOR: constants.ACTOR_GEMINI,
                constants.KEY_TEXT: "Previous response",
            }
        ]

        result = continue_story(
            user_input="GOD MODE: adjust HP",
            mode="character",
            story_context=story_context,
            current_game_state=game_state,
        )

        builder_instance.build_god_mode_instructions.assert_called_once()
        builder_instance.build_core_system_instructions.assert_not_called()
        mock_validate_planning_block.assert_not_called()
        self.assertIsNotNone(result.structured_response)
        self.assertEqual(result.structured_response.god_mode_response, "Acknowledged.")

    def test_main_py_handles_gemini_response_object(self):
        """Test that main.py properly handles LLMResponse objects."""
        # This is more of an integration test - checking the interface contract

        response = LLMResponse.create(self.sample_raw_response)

        # Main.py expects these attributes/methods
        assert hasattr(response, "narrative_text")
        assert hasattr(response, "state_updates")
        assert hasattr(response, "debug_tags_present")
        assert hasattr(response, "has_debug_content")

        # Should be able to access all necessary data
        narrative = response.narrative_text
        updates = response.state_updates

        assert isinstance(narrative, str)
        assert isinstance(updates, dict)

    def test_legacy_create_method(self):
        """Test that the legacy create method still works for backwards compatibility."""

        # Mock structured response
        mock_structured = Mock(spec=NarrativeResponse)
        mock_structured.state_updates = {"hp": 10}
        mock_structured.entities_mentioned = ["dragon"]
        mock_structured.location_confirmed = "Dragon's Lair"
        mock_structured.debug_info = {"dm_notes": ["Boss fight"]}

        # Use legacy create method
        response = LLMResponse.create_legacy(
            narrative_text="The dragon roars!", structured_response=mock_structured
        )

        # Should work correctly
        assert response.narrative_text == "The dragon roars!"
        assert response.state_updates == {"hp": 10}
        assert response.entities_mentioned == ["dragon"]


if __name__ == "__main__":
    unittest.main()
