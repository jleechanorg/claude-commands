"""
End-to-end integration test for THINK MODE functionality.
Only mocks external services (LLM provider APIs and Firestore DB) at the lowest level.
Tests the full flow including think mode prompt selection and response handling.

THINK MODE is for strategic planning and tactical analysis WITHOUT narrative advancement.
Time advances by only 1 microsecond. The character thinks but does not act.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestThinkModeEnd2End(unittest.TestCase):
    """Test THINK MODE functionality through the full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-think-mode"
        self._auth_patcher = patch(
            "mvp_site.main.auth.verify_id_token",
            return_value={"uid": self.test_user_id},
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        # Test headers with Authorization token
        self.test_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

        # Standard mock THINK MODE response
        self.mock_think_mode_response_data = {
            "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 10, Afternoon\nLocation: Dungeon Entrance\nStatus: Lvl 3 Rogue | HP: 22/28 | XP: 2500/6000 | Gold: 75gp",
            "narrative": "You pause to consider your options. Your mind works through the problem methodically... (INT 14)",
            "entities_mentioned": [],
            "location_confirmed": "Dungeon Entrance",
            "dice_rolls": [
                {
                    "type": "Intelligence Check (Planning)",
                    "roll": "1d20+2",
                    "result": 16,
                    "dc": None,
                    "outcome": "Good - Sharp analysis",
                }
            ],
            "planning_block": {
                "plan_quality": {
                    "stat_used": "Intelligence",
                    "modifier": 2,
                    "roll_result": 16,
                    "quality": "Sharp",
                },
                "thinking": "The player wants to analyze options for entering the dungeon.",
                "options": [
                    {
                        "name": "Scout ahead",
                        "description": "Use stealth to check for traps and guards",
                        "pros": ["Low risk", "Gather information"],
                        "cons": ["Takes time", "May be spotted"],
                        "confidence": 0.75,
                    },
                    {
                        "name": "Direct approach",
                        "description": "Walk in confidently",
                        "pros": ["Fast", "Surprise factor"],
                        "cons": ["High risk", "No retreat option"],
                        "confidence": 0.45,
                    },
                ],
                "choices": {
                    "think:scout": {
                        "text": "Scout ahead",
                        "description": "Use stealth to reconnoiter",
                        "risk_level": "low",
                    },
                    "think:direct": {
                        "text": "Direct approach",
                        "description": "Walk in confidently",
                        "risk_level": "high",
                    },
                },
            },
            "state_updates": {
                "world_data": {
                    "world_time": {
                        "year": 1492,
                        "month": "Mirtul",
                        "day": 10,
                        "hour": 14,
                        "minute": 0,
                        "microsecond": 1,  # Only +1 microsecond in think mode
                        "time_of_day": "Afternoon",
                    }
                }
            },
        }

    def _setup_fake_firestore_with_campaign(self, fake_firestore, campaign_id):
        """Helper to set up fake Firestore with campaign and game state."""
        # Create test campaign data
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {
                "title": "Test Campaign",
                "setting": "Fantasy realm",
                "selected_prompts": ["narrative", "mechanics"],
            }
        )

        # Create game state with proper structure
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "You stand at the dungeon entrance.",
                "player_character_data": {
                    "name": "Shadow",
                    "hp_current": 22,
                    "hp_max": 28,
                    "level": 3,
                    "class": "Rogue",
                    "experience": {"current": 2500, "next_level": 6000},
                    "ability_scores": {
                        "intelligence": {"score": 14, "modifier": 2},
                        "wisdom": {"score": 12, "modifier": 1},
                    },
                },
                "world_data": {
                    "current_location_name": "Dungeon Entrance",
                    "world_time": {
                        "year": 1492,
                        "month": "Mirtul",
                        "day": 10,
                        "hour": 14,
                        "minute": 0,
                        "microsecond": 0,
                        "time_of_day": "Afternoon",
                    },
                },
                "npc_data": {},
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_think_mode_returns_planning_block(self, mock_gemini_generate, mock_get_db):
        """
        Test that THINK MODE commands return planning_block with choices.

        This test exercises the full interaction flow including:
        - Agent selection (PlanningAgent)
        - LLM call with think mode prompts
        - Response formatting
        """

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_think_mode"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini provider to return think mode response
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_think_mode_response_data)
        )

        # Make THINK MODE request (mode='think' with THINK: prefix added by frontend)
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps(
                {
                    "input": "THINK:What are my options for entering the dungeon?",
                    "mode": "think",
                }
            ),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data.decode('utf-8')}"
        )
        data = json.loads(response.data)

        # Verify planning_block is present in the response
        assert "planning_block" in data, "planning_block field should be present"
        # Check for choices (the actual field used in the schema)
        assert "choices" in data["planning_block"], "planning_block should have choices"

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_character_mode_after_think_mode_works(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that character mode works correctly.

        BUG REPRODUCTION: This test exercises the _enforce_rewards_processed_flag
        code path which is called for character mode. If the parameter is named
        _original_state_dict instead of original_state_dict, this test will FAIL
        with: _enforce_rewards_processed_flag() got an unexpected keyword argument
        'original_state_dict'
        """

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_char_mode"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock character mode response
        char_mode_response = {
            "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR\nLocation: Dungeon",
            "narrative": "You enter the dungeon cautiously...",
            "entities_mentioned": [],
            "location_confirmed": "Dungeon Entrance",
            "state_updates": {},
            "planning_block": {
                "thinking": "Player is exploring",
                "choices": {
                    "explore": {
                        "text": "Explore",
                        "description": "Look around",
                        "risk_level": "low",
                    }
                },
            },
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(char_mode_response)
        )

        # Make CHARACTER MODE request - this calls _enforce_rewards_processed_flag
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "I enter the dungeon", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        # This is the key assertion - if the bug exists, we get 400 error
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data.decode('utf-8')}"
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_think_mode_uses_planning_agent(self, mock_gemini_generate, mock_get_db):
        """Test that THINK MODE uses PlanningAgent with think mode prompts."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_think_mode_agent"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini provider
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_think_mode_response_data)
        )

        # Make THINK MODE request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps(
                {"input": "THINK:Should I attack or retreat?", "mode": "think"}
            ),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify request succeeded
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data.decode('utf-8')}"
        )

        # Verify Gemini was called
        assert mock_gemini_generate.call_count >= 1, "LLM should be called"

        # Get the system instruction passed to the LLM
        call_args = mock_gemini_generate.call_args

        # Ensure we actually inspected a call
        assert call_args is not None, "LLM call args should not be None"

        if call_args and len(call_args) > 0:
            all_args_str = str(call_args)

            # Think mode should have planning/strategic language
            has_think_mode_prompt = (
                "Think Mode" in all_args_str
                or "strategic planning" in all_args_str.lower()
                or "planning_block" in all_args_str
                or "microsecond" in all_args_str
            )

            # Think mode should NOT have full narrative generation language
            # (though it may have some basic state info)
            has_full_narrative_prompt = (
                "Master Game Weaver" in all_args_str and "living_world" in all_args_str
            )

            # Positive assertion: THINK mode prompts must be present
            assert has_think_mode_prompt, (
                f"THINK MODE prompt not found in call args: {all_args_str[:500]}"
            )

            if has_full_narrative_prompt and not has_think_mode_prompt:
                self.fail(
                    "THINK MODE should use think mode prompts, not full narrative"
                )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_think_mode_does_not_increment_player_turn(
        self, mock_gemini_generate, mock_get_db
    ):
        """Test that THINK MODE does not increment player_turn counter."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_think_mode_turn"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Set initial player_turn
        game_state_ref = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
        )
        initial_state = game_state_ref.get().to_dict()
        initial_state["player_turn"] = 5
        game_state_ref.set(initial_state)

        # Mock Gemini provider
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_think_mode_response_data)
        )

        # Make THINK MODE request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "THINK:What should I do next?", "mode": "think"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify request succeeded
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data.decode('utf-8')}"
        )

        # Verify player_turn was NOT incremented (think mode freezes time)
        final_state = game_state_ref.get().to_dict()
        assert final_state.get("player_turn") == 5, (
            f"player_turn should stay at 5 in Think Mode, got {final_state.get('player_turn')}"
        )


if __name__ == "__main__":
    unittest.main()
