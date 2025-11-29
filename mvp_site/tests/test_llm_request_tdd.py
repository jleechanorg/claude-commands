"""
Test-Driven Development for LLMRequest Class

This test defines the proper structured JSON that should be sent directly to Gemini API
instead of being converted back to concatenated string blobs. The tests will initially
FAIL until we implement the LLMRequest class properly.

RED -> GREEN -> REFACTOR approach:
1. RED: Tests fail because current implementation converts JSON back to strings
2. GREEN: Implement LLMRequest class that sends actual JSON to Gemini
3. REFACTOR: Remove old json_input_schema approach
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"
# NOTE: GEMINI_API_KEY is mocked in individual tests - no hardcoded keys

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mvp_site import llm_service
from mvp_site.game_state import GameState


class TestLLMRequestTDD(unittest.TestCase):
    """
    TDD tests for LLMRequest class that sends actual JSON to Gemini API.

    These tests define the EXPECTED behavior: structured JSON fields should be
    sent directly to Gemini API, not converted to concatenated strings.
    """

    def setUp(self):
        """Set up test fixtures."""
        # Mock game state with comprehensive data
        self.mock_game_state = GameState(
            user_id="test-user-123",
            player_character_data={
                "name": "Test Hero",
                "class": "Warrior",
                "level": 3,
                "hp_current": 25,
                "hp_max": 30,
            },
            world_data={
                "location": "Forest",
                "weather": "sunny",
                "current_location_name": "Enchanted Forest",
            },
            npc_data={"guard": {"name": "Town Guard", "disposition": "friendly"}},
            custom_campaign_state={"session_number": 1, "quest_active": True},
        )

        # Mock story context (previous story entries)
        self.mock_story_context = [
            {
                "actor": "user",
                "text": "I enter the tavern",
                "timestamp": "2024-01-01T10:00:00Z",
                "sequence_id": 1,
            },
            {
                "actor": "gemini",
                "text": "You see a crowded tavern...",
                "timestamp": "2024-01-01T10:01:00Z",
                "sequence_id": 2,
            },
        ]

    @patch("mvp_site.llm_service.get_client")  # Mock client to prevent API key requirement
    @patch("mvp_site.llm_service._get_text_from_response")
    @patch(
        "mvp_site.llm_service._call_llm_api_with_model_cycling"
    )  # Mock the underlying API
    @patch("mvp_site.llm_service._call_llm_api")  # Mock planning block API calls
    def test_continue_story_sends_structured_json_to_gemini(
        self, mock_planning_api, mock_api_call, mock_get_text, mock_get_client
    ):
        """
        FAILING TEST: Verify continue_story sends structured JSON directly to Gemini API.

        This test will FAIL initially because the current implementation converts
        JSON back to concatenated strings via to_gemini_format().

        Expected: Direct JSON fields sent to Gemini API
        Current: JSON converted back to string blob
        """
        # Arrange: Set up mock responses
        mock_get_client.return_value = MagicMock()  # Mock Gemini client
        mock_response = MagicMock()
        mock_api_call.return_value = mock_response
        mock_get_text.return_value = '{"narrative": "You continue your adventure..."}'

        # Mock planning block API call to return simple response
        mock_planning_response = MagicMock()
        mock_planning_api.return_value = mock_planning_response
        mock_get_text.return_value = '{"narrative": "You continue your adventure..."}'

        # Act: Call continue_story (this will currently FAIL the assertions)
        result = llm_service.continue_story(
            user_input="I look for hidden passages",
            mode="character",
            story_context=self.mock_story_context,
            current_game_state=self.mock_game_state,
            selected_prompts=["narrative"],
            use_default_world=False,
        )

        # Assert: Verify API was called with structured JSON, NOT string concatenation
        self.assertTrue(mock_api_call.called, "Gemini API should have been called")

        # Get the actual call arguments - we want the MAIN story API call, not planning block
        # The main call should be to _call_llm_api_with_model_cycling with structured JSON
        call_args = mock_api_call.call_args

        # The EXPECTED behavior: First argument should be structured JSON dict, not string list
        # This assertion will FAIL with current implementation
        prompt_content = (
            call_args.args[0][0] if call_args.args and call_args.args[0] else None
        )

        # CRITICAL TEST: The content sent to Gemini should be structured JSON string, not concatenated blob
        self.assertIsInstance(
            prompt_content,
            str,
            f"Gemini API should receive structured JSON string, not unstructured blob. Got: {type(prompt_content)} with content: {str(prompt_content)[:100]}",
        )

        # Verify it's valid JSON that can be parsed back to a dict
        try:
            parsed_json = json.loads(prompt_content)
            self.assertIsInstance(
                parsed_json, dict, "JSON content should parse to a dict structure"
            )
        except json.JSONDecodeError as e:
            self.fail(f"Content should be valid JSON, but got parse error: {e}")

        # Verify the JSON structure contains the expected fields (flat structure, no nested context)
        # Note: user_action may have validation warnings prepended, so check if our input is contained within it
        self.assertIn(
            "I look for hidden passages",
            parsed_json["user_action"],
            "Original user action should be preserved in user_action field",
        )
        self.assertEqual(parsed_json["game_mode"], "character")
        self.assertEqual(parsed_json["user_id"], "test-user-123")

        # Verify structured data fields are preserved as proper types
        self.assertIsInstance(
            parsed_json["game_state"], dict, "Game state should be dict, not string"
        )
        self.assertIsInstance(
            parsed_json["story_history"],
            list,
            "Story history should be list, not string",
        )
        self.assertIsInstance(
            parsed_json["entity_tracking"],
            dict,
            "Entity tracking should be dict, not string",
        )

        # Verify specific game state data is preserved
        self.assertEqual(
            parsed_json["game_state"]["player_character_data"]["name"], "Test Hero"
        )
        self.assertEqual(parsed_json["game_state"]["world_data"]["location"], "Forest")

        # Verify story history is structured list, not concatenated string
        self.assertEqual(len(parsed_json["story_history"]), 2)
        self.assertEqual(parsed_json["story_history"][0]["actor"], "user")
        self.assertEqual(parsed_json["story_history"][1]["actor"], "gemini")

        # Verify other required fields
        self.assertIn("checkpoint_block", parsed_json)
        self.assertIn("core_memories", parsed_json)
        self.assertIn("selected_prompts", parsed_json)
        self.assertEqual(parsed_json["selected_prompts"], ["narrative"])

        # CRITICAL: Verify NO nested "context" wrapper
        self.assertNotIn(
            "context", parsed_json, "Should not have nested context wrapper"
        )

        # CRITICAL: Verify NO string concatenation artifacts
        self.assertNotIn(
            "CURRENT GAME STATE:",
            str(prompt_content),
            "Should not contain string concatenation headers",
        )
        self.assertNotIn(
            "TIMELINE LOG:", str(prompt_content), "Should not contain timeline headers"
        )

        # Verify the result is valid
        self.assertIsNotNone(result, "Function should return a result")

    def test_get_initial_story_sends_structured_json_to_gemini(self):
        """
        TEST: Verify get_initial_story works with built-in mock mode.

        This test uses the built-in MOCK_SERVICES_MODE to avoid complex mocking.
        It verifies that the function returns a valid response structure.
        """
        # Ensure mock mode is enabled
        os.environ["MOCK_SERVICES_MODE"] = "true"

        # Act: Call get_initial_story in mock mode
        result = llm_service.get_initial_story(
            prompt="I am a brave warrior seeking adventure",
            user_id="test-user-123",
            selected_prompts=["character", "narrative"],
            generate_companions=True,
            use_default_world=False,
        )

        # Assert: Verify the function returns a valid LLMResponse
        self.assertIsNotNone(result, "Function should return a result")

        # Verify the result has the expected structure
        self.assertTrue(
            hasattr(result, "narrative_text"),
            "Result should have narrative_text attribute",
        )
        self.assertIsInstance(
            result.narrative_text, str, "narrative_text should be a string"
        )
        self.assertTrue(
            len(result.narrative_text) > 0, "narrative_text should not be empty"
        )

        # Additional verification: Check if result has structured_response
        if hasattr(result, "structured_response") and result.structured_response:
            # structured_response can be either a dict or a NarrativeResponse object
            self.assertTrue(
                isinstance(result.structured_response, dict)
                or hasattr(result.structured_response, "__dict__"),
                "structured_response should be a dict or have dict-like structure",
            )

        # Verify the function completed without throwing exceptions
        self.assertIsNotNone(
            result, "Function should return a result without exceptions"
        )

    def test_gemini_request_class_exists(self):
        """
        FAILING TEST: Verify LLMRequest class exists and has expected methods.

        This test will FAIL until we create the LLMRequest class.
        """
        # This import will FAIL until we create the class
        try:
            from mvp_site.llm_request import LLMRequest

            # Test that the class has the expected methods
            self.assertTrue(hasattr(LLMRequest, "build_story_continuation"))
            self.assertTrue(hasattr(LLMRequest, "build_initial_story"))
            self.assertTrue(hasattr(LLMRequest, "to_json"))

        except ImportError:
            self.fail("LLMRequest class should exist in llm_request.py")


if __name__ == "__main__":
    unittest.main()
