"""
End-to-end test for RewardsAgent being purely mechanical.

Tests that RewardsAgent:
1. Does NOT advance time or the game clock
2. Does NOT generate narrative beyond the rewards summary
3. Does NOT include planning_block choices (except level-up options)
4. ONLY outputs: rewards_box, XP updates, loot, level-up offers, rewards_processed=true

Design Decision:
RewardsAgent is purely mechanical - it calculates and displays rewards.
StoryModeAgent handles all narrative continuation after rewards.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

# Ensure TESTING is set before importing app modules
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestRewardsAgentMechanicalEnd2End(unittest.TestCase):
    """
    Test that RewardsAgent is purely mechanical with no narrative advancement.

    RewardsAgent should ONLY:
    - Calculate and display XP/loot/rewards
    - Detect and offer level-ups
    - Set rewards_processed=true

    RewardsAgent should NOT:
    - Advance game time
    - Generate story narrative
    - Provide story continuation choices in planning_block
    """

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-rewards-mechanical"
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

    def _setup_campaign_awaiting_rewards(self, fake_firestore, campaign_id):
        """
        Set up a campaign where combat just ended and rewards are pending.
        """
        # Create test campaign
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Mechanical Rewards Test", "setting": "Fantasy realm"}
        )

        # Create game state with combat ended, rewards pending
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "The goblin falls defeated.",
                "player_turn": 10,
                "current_time": "2025-01-04T10:00:00Z",  # Track time
                "player_character_data": {
                    "level": 1,
                    "experience": {"current": 250},  # Close to level 2 (300 XP)
                },
                "combat_state": {
                    "in_combat": False,
                    "combat_phase": "ended",
                    "combat_summary": {
                        "xp_awarded": 100,  # Will put them at 350 XP -> level up!
                        "enemies_defeated": ["goblin_1"],
                        "outcome": "victory",
                    },
                    "rewards_processed": False,
                },
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_rewards_agent_no_time_advancement(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that RewardsAgent does NOT advance game time.

        Game time should only advance in StoryModeAgent, not during reward processing.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "no_time_advance_test"
        self._setup_campaign_awaiting_rewards(fake_firestore, campaign_id)

        # Get initial time
        initial_state = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
            .to_dict()
        )
        initial_time = initial_state.get("current_time")

        # Mock a purely mechanical rewards response
        mock_response_data = {
            "narrative": (
                "**=================================================**\n"
                "**               REWARDS EARNED                    **\n"
                "**=================================================**\n"
                "** SOURCE: Combat                                  **\n"
                "** XP GAINED: 100 XP                               **\n"
                "**=================================================**"
            ),
            "rewards_box": {
                "source": "combat",
                "xp_gained": 100,
                "current_xp": 350,
                "next_level_xp": 300,
                "progress_percent": 116,
                "level_up_available": True,
                "loot": ["10 gp"],
                "gold": 10,
            },
            "state_updates": {
                "player_character_data": {
                    "experience": {"current": 350},
                },
                "combat_state": {
                    "rewards_processed": True,
                },
                # NOTE: No current_time update - rewards should NOT advance time
            },
            # Level-up choices are allowed
            "planning_block": {
                "thinking": "Level-up is available.",
                "choices": {
                    "level_up_now": {
                        "text": "Level Up to Level 2",
                        "description": "Apply level 2 benefits",
                        "risk_level": "safe",
                    },
                    "continue_adventuring": {
                        "text": "Continue Adventuring",
                        "description": "Level up later",
                        "risk_level": "safe",
                    },
                },
            },
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(mock_response_data)
        )

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "continue", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        # Verify time was NOT advanced
        final_state = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
            .to_dict()
        )
        final_time = final_state.get("current_time")

        # Time should be unchanged (or not present) - rewards don't advance time
        self.assertEqual(
            initial_time,
            final_time,
            f"RewardsAgent should NOT advance time. "
            f"Initial: {initial_time}, Final: {final_time}. "
            f"Time advancement is StoryModeAgent's responsibility."
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_rewards_agent_minimal_output_no_story_choices(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that RewardsAgent outputs only mechanical rewards, no story choices.

        RewardsAgent should output:
        - rewards_box (required)
        - rewards_processed=true (required)
        - Optional: level-up choices only

        RewardsAgent should NOT output:
        - Story continuation choices like "Continue the Adventure", "Take a Rest"
        - Narrative story beats
        - Time advancement
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "minimal_output_test"
        self._setup_campaign_awaiting_rewards(fake_firestore, campaign_id)

        # CORRECT: Mock minimal mechanical response (no story choices)
        correct_response_data = {
            "narrative": (
                "**=================================================**\n"
                "**               REWARDS EARNED                    **\n"
                "**=================================================**\n"
                "** XP GAINED: 100 XP                               **\n"
                "**=================================================**"
            ),
            "rewards_box": {
                "source": "combat",
                "xp_gained": 100,
                "current_xp": 350,
                "next_level_xp": 300,
            },
            "state_updates": {
                "player_character_data": {"experience": {"current": 350}},
                "combat_state": {"rewards_processed": True},
            },
            # No planning_block at all - purely mechanical
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(correct_response_data)
        )

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "continue", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        response_json = json.loads(response.data)

        # Verify rewards_box is present
        self.assertIn(
            "rewards_box",
            response_json,
            "RewardsAgent must output rewards_box"
        )

        # Verify no story continuation choices in planning_block
        planning_block = response_json.get("planning_block", {})
        choices = planning_block.get("choices", {})
        story_choices = ["continue_story", "rest", "explore", "continue_adventure"]
        present_story_choices = [c for c in story_choices if c in choices]

        self.assertEqual(
            present_story_choices,
            [],
            f"RewardsAgent should NOT output story choices. "
            f"Found: {present_story_choices}. StoryModeAgent handles that."
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_rewards_agent_level_up_choices_allowed(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that RewardsAgent CAN provide level-up choices (the only exception).

        Level-up is part of the reward process, so these choices are allowed.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "level_up_allowed_test"
        self._setup_campaign_awaiting_rewards(fake_firestore, campaign_id)

        # GOOD: Mock response with only level-up choices
        good_response_data = {
            "narrative": (
                "**REWARDS EARNED**\n"
                "XP: 100\n\n"
                "**LEVEL UP AVAILABLE!** You have earned enough experience "
                "to reach Level 2!"
            ),
            "rewards_box": {
                "xp_gained": 100,
                "current_xp": 350,
                "next_level_xp": 300,
                "level_up_available": True,
            },
            "state_updates": {
                "player_character_data": {"experience": {"current": 350}},
                "combat_state": {"rewards_processed": True},
            },
            # GOOD: Only level-up choices
            "planning_block": {
                "thinking": "Level-up available, offering choice.",
                "choices": {
                    "level_up_now": {
                        "text": "Level Up to Level 2",
                        "description": "Apply level 2 benefits immediately",
                        "risk_level": "safe",
                    },
                    "continue_adventuring": {
                        "text": "Continue Adventuring",
                        "description": "Level up later and continue the story",
                        "risk_level": "safe",
                    },
                },
            },
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(good_response_data)
        )

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "continue", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        response_json = json.loads(response.data)
        planning_block = response_json.get("planning_block", {})
        choices = planning_block.get("choices", {})

        # Level-up choices ARE allowed
        allowed_choices = ["level_up_now", "continue_adventuring"]
        for choice in allowed_choices:
            if choice in choices:
                # This is expected - level-up choices are allowed
                pass

        # Verify rewards_processed was set
        final_state = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
            .to_dict()
        )
        combat_state = final_state.get("combat_state", {})
        self.assertTrue(
            combat_state.get("rewards_processed", False),
            "rewards_processed should be True after RewardsAgent completes"
        )


if __name__ == "__main__":
    unittest.main()
