"""
End-to-end test for entity tracking budget fix.

Tests that story continuation with large context + many NPCs does not cause
ContextTooLargeError. This validates the ENTITY_TRACKING_TOKEN_RESERVE fix.

Bug reproduced: qwen-3-235b model received 97,923 tokens when max allowed was
94,372 tokens because entity tracking (~3,500+ tokens) was added AFTER truncation
but not budgeted in scaffold calculation.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestEntityTrackingBudgetEnd2End(unittest.TestCase):
    """Test that large context + many NPCs doesn't cause context overflow."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.test_user_id = "test-user-entity-budget"
        self._auth_patcher = patch(
            "mvp_site.main.auth.verify_id_token",
            return_value={"uid": self.test_user_id},
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        self.test_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

        self.mock_llm_response_data = {
            "narrative": "The party continues their journey through the realm...",
            "entities_mentioned": ["Thorin", "Elena", "Marcus"],
            "location_confirmed": "Ancient Forest",
            "state_updates": {"story_progression": "continued"},
        }

    def _create_many_npcs(self, count: int = 15) -> dict:
        """Create NPC data with many characters to trigger large entity tracking."""
        npc_data = {}
        for i in range(count):
            npc_name = f"NPC_{i}_{'Warrior' if i % 3 == 0 else 'Mage' if i % 3 == 1 else 'Rogue'}"
            npc_data[npc_name] = {
                "mbti": "INTJ",
                "role": "ally" if i % 2 == 0 else "neutral",
                "background": f"A mysterious {npc_name.split('_')[-1].lower()} with a complex past involving ancient artifacts and forgotten kingdoms. " * 3,
                "relationship": "companion" if i < 5 else "acquaintance",
                "skills": ["combat", "magic", "stealth", "diplomacy"][:((i % 4) + 1)],
                "personality_traits": ["brave", "cunning", "loyal", "mysterious"][:((i % 4) + 1)],
                "equipment": [f"item_{j}" for j in range(3)],
                "current_hp": 50 + i,
                "max_hp": 100,
                "status": "normal",
            }
        return npc_data

    def _create_large_story_context(self, turns: int = 50) -> list:
        """Create a large story context with many turns."""
        story_context = []
        for i in range(turns):
            # Alternate between player and GM turns
            if i % 2 == 0:
                story_context.append({
                    "actor": "player",
                    "text": f"Turn {i}: The player decides to explore the ancient ruins, "
                            f"searching for clues about the mysterious artifact. "
                            f"They examine the weathered stone walls and find inscriptions. " * 2,
                    "sequence_id": i + 1,
                })
            else:
                story_context.append({
                    "actor": "gm",
                    "text": f"Turn {i}: The Game Master describes the scene in vivid detail. "
                            f"Ancient runes glow with ethereal light as the party advances. "
                            f"NPCs react to the player's actions with varied emotions. " * 3,
                    "sequence_id": i + 1,
                })
        return story_context

    def _setup_fake_firestore_with_large_campaign(self, fake_firestore, campaign_id):
        """Set up Firestore with large game state (many NPCs + story context)."""
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Large Entity Test Campaign", "setting": "Epic Fantasy"}
        )

        # Create game state with MANY NPCs to trigger large entity tracking
        game_state = {
            "user_id": self.test_user_id,
            "story_text": "A long and complex story...",
            "story_context": self._create_large_story_context(50),
            "characters": ["Hero"],
            "locations": ["Ancient Forest", "Mountain Pass", "Dark Cave"],
            "items": ["Magic Sword", "Health Potion", "Ancient Map"],
            "combat_state": {"in_combat": False},
            "custom_campaign_state": {"session_number": 5},
            "npc_data": self._create_many_npcs(15),  # 15 NPCs with detailed data
            "world_data": {
                "current_location_name": "Ancient Forest",
                "time_of_day": "evening",
            },
        }

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            game_state
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.cerebras_provider.generate_content")
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
    def test_large_context_with_many_npcs_does_not_overflow(
        self, mock_gemini_generate, mock_cerebras_generate, mock_get_db
    ):
        """
        Test that story continuation with large context + many NPCs succeeds.

        This is the regression test for the entity tracking budget bug.
        Before the fix, this would fail with ContextTooLargeError because
        entity tracking tokens were not budgeted in scaffold calculation.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "large_entity_test_campaign"
        self._setup_fake_firestore_with_large_campaign(fake_firestore, campaign_id)

        mock_cerebras_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )

        # This request should NOT fail with ContextTooLargeError
        # Before the fix, large entity tracking overhead would cause overflow
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "I approach the ancient altar and examine the runes closely",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Should succeed - if entity tracking budget fix works
        self.assertEqual(
            response.status_code,
            200,
            f"Expected 200 (entity budget fix working), got {response.status_code}: "
            f"{response.data.decode()[:500]}"
        )

        data = json.loads(response.data)
        self.assertIn("story", data)
        self.assertIsInstance(data["story"], list)

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.cerebras_provider.generate_content")
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
    def test_maximum_npc_count_still_succeeds(
        self, mock_gemini_generate, mock_cerebras_generate, mock_get_db
    ):
        """
        Test with maximum realistic NPC count (25+) to stress test entity tracking.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "max_npc_test_campaign"

        # Set up campaign with 25 NPCs (stress test)
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Max NPC Test", "setting": "Epic War"}
        )

        game_state = {
            "user_id": self.test_user_id,
            "story_text": "An epic battle unfolds...",
            "story_context": self._create_large_story_context(30),
            "characters": ["Commander"],
            "locations": ["Battlefield"],
            "items": ["War Banner"],
            "combat_state": {"in_combat": True},  # Combat mode for extra complexity
            "custom_campaign_state": {"session_number": 10},
            "npc_data": self._create_many_npcs(25),  # 25 NPCs - stress test
            "world_data": {"current_location_name": "Battlefield"},
        }

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            game_state
        )

        mock_cerebras_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )

        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "Rally the troops!", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(
            response.status_code,
            200,
            f"Max NPC test failed: {response.status_code}: {response.data.decode()[:500]}"
        )


if __name__ == "__main__":
    unittest.main()
