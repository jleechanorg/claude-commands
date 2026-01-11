"""
End-to-end integration test for NPC death state persistence.

Bug: When a user kills an NPC (e.g., Marcus), the game still presents options
to kill them again on subsequent turns. The death state is not being properly
synced between combat_state and npc_data.

This test verifies the full flow:
1. Set up campaign with active combat and named NPC
2. Send interaction that kills the NPC (LLM returns hp_current: 0)
3. Verify NPC is removed from combat but preserved in npc_data with dead status
4. Verify subsequent turns don't offer the dead NPC as a target

Only mocks external services (LLM provider APIs and Firestore DB) at the lowest level.
Tests the full flow from API endpoint through all service layers.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest.mock import patch

# Set this before importing mvp_site modules to bypass clock skew validation
os.environ["TESTING_AUTH_BYPASS"] = "true"

# Add project root to sys.path for proper import resolution
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestNPCDeathStateEnd2End(unittest.TestCase):
    """End-to-end tests for NPC death state persistence through the full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")
        # Disable MOCK_SERVICES_MODE to allow patching generate_json_mode_content
        os.environ["MOCK_SERVICES_MODE"] = "false"

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-death-state"
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

    def _setup_campaign_with_combat(self, fake_firestore, campaign_id):
        """
        Set up a campaign in active combat with a named NPC.

        Creates:
        - Campaign document
        - Game state with active combat
        - Named NPC "Marcus" with role and backstory
        - Marcus as combatant with HP > 0
        """
        # Create campaign
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {
                "title": "Death State Test Campaign",
                "setting": "Dark Fantasy",
                "created_at": "2025-01-01T00:00:00Z",
            }
        )

        # Create game state with active combat and named NPC
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "You face Marcus the Betrayer in combat.",
                "player_character_data": {
                    "name": "Hero",
                    "level": 5,
                    "hp_current": 50,
                    "hp_max": 50,
                    "class": "Fighter",
                },
                "combat_state": {
                    "in_combat": True,
                    "current_round": 1,
                    "current_turn_index": 0,
                    "initiative_order": [
                        {"name": "Hero", "initiative": 18, "type": "pc"},
                        {"name": "Marcus", "initiative": 14, "type": "enemy"},
                    ],
                    "combatants": {
                        "Hero": {
                            "name": "Hero",
                            "hp_current": 50,
                            "hp_max": 50,
                            "type": "pc",
                            "status": [],
                        },
                        "Marcus": {
                            "name": "Marcus",
                            "hp_current": 30,
                            "hp_max": 30,
                            "type": "enemy",
                            "status": [],
                        },
                    },
                    "combat_log": ["Combat initiated with Marcus the Betrayer"],
                },
                "npc_data": {
                    "Marcus": {
                        "name": "Marcus the Betrayer",
                        "role": "villain",  # Named NPC - has meaningful role
                        "backstory": "A corrupt merchant who betrayed the town for gold",
                        "description": "A well-dressed man with shifty eyes and a cruel smile",
                        "hp_current": 30,
                        "hp_max": 30,
                    },
                },
                "world_data": {
                    "current_location": "Town Square",
                    "world_time": {"hour": 14, "day": 1},
                },
                "custom_campaign_state": {},
            }
        )

    def _create_kill_npc_response(self, npc_name: str) -> dict:
        """Create a mock LLM response that kills the specified NPC.

        Note: The key is 'state_updates' (not 'state_changes') - this matches
        the schema expected by the LLM response parser.
        """
        return {
            "narrative": f"With a powerful strike, you defeat {npc_name}! The villain falls to the ground, defeated at last.",
            "state_updates": {  # CRITICAL: Must be state_updates, not state_changes
                "combat_state": {
                    "combatants": {
                        npc_name: {
                            "hp_current": 0,
                            "status": ["dead"],
                        }
                    },
                    "combat_log": [f"{npc_name} has been defeated!"],
                }
            },
            "options": [
                "Search the body",
                "Leave the scene",
                "Check for witnesses",
            ],
        }

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
    def test_named_npc_death_persists_in_npc_data(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        End-to-end test: Named NPC killed in combat should be preserved in npc_data with dead status.

        This test verifies the complete flow:
        1. Campaign has active combat with named NPC "Marcus"
        2. Player attacks and kills Marcus (LLM returns hp_current: 0)
        3. After processing, Marcus should:
           - Be REMOVED from combat_state.combatants (can't target dead enemies)
           - Be PRESERVED in npc_data with status: ["dead"] (narrative continuity)
        """
        # Set up fake Firestore with campaign in active combat
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_death_state_campaign"
        self._setup_campaign_with_combat(fake_firestore, campaign_id)

        # Mock LLM response that kills Marcus
        kill_response = self._create_kill_npc_response("Marcus")
        mock_gemini_generate.return_value = FakeLLMResponse(json.dumps(kill_response))

        # Make the API request - attack Marcus
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps(
                {"input": "I attack Marcus with my sword!", "mode": "character"}
            ),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response success
        self.assertEqual(
            response.status_code,
            200,
            f"Expected 200, got {response.status_code}: {response.data.decode()}",
        )

        # Get the updated game state from fake Firestore
        game_state_doc = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
        )
        updated_state = game_state_doc.to_dict()

        # CRITICAL ASSERTION 1: Marcus should be REMOVED from combat combatants
        # (Dead enemies can't be targeted in combat)
        combatants = updated_state.get("combat_state", {}).get("combatants", {})
        self.assertNotIn(
            "Marcus",
            combatants,
            f"Dead NPC 'Marcus' should be removed from combat combatants. "
            f"Combatants: {list(combatants.keys())}",
        )

        # CRITICAL ASSERTION 2: Marcus should be PRESERVED in npc_data
        # (Named NPCs need to persist for narrative continuity)
        npc_data = updated_state.get("npc_data", {})
        self.assertIn(
            "Marcus",
            npc_data,
            f"Named NPC 'Marcus' should be preserved in npc_data (not deleted). "
            f"npc_data keys: {list(npc_data.keys())}",
        )

        # CRITICAL ASSERTION 3: Marcus should have "dead" status
        marcus_npc = npc_data.get("Marcus", {})
        marcus_status = marcus_npc.get("status", [])
        self.assertIn(
            "dead",
            marcus_status,
            f"Marcus should have 'dead' in status list. "
            f"Current status: {marcus_status}, Full data: {marcus_npc}",
        )

        # CRITICAL ASSERTION 4: Marcus HP should be 0
        self.assertEqual(
            marcus_npc.get("hp_current"),
            0,
            f"Marcus hp_current should be 0. Current: {marcus_npc.get('hp_current')}",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
    def test_generic_enemy_deleted_from_npc_data(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        End-to-end test: Generic enemies (not named NPCs) should be fully deleted.

        Regression test to ensure we didn't break the cleanup of generic enemies
        while preserving named NPCs.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_generic_enemy_campaign"

        # Set up campaign with a GENERIC enemy (role=enemy, no backstory)
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {
                "title": "Generic Enemy Test",
                "setting": "Fantasy",
            }
        )

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "A goblin attacks!",
                "player_character_data": {
                    "name": "Hero",
                    "level": 3,
                    "hp_current": 40,
                    "hp_max": 40,
                },
                "combat_state": {
                    "in_combat": True,
                    "current_round": 1,
                    "initiative_order": [
                        {"name": "Hero", "initiative": 15, "type": "pc"},
                        {"name": "Goblin Scout", "initiative": 12, "type": "enemy"},
                    ],
                    "combatants": {
                        "Hero": {
                            "name": "Hero",
                            "hp_current": 40,
                            "hp_max": 40,
                            "type": "pc",
                        },
                        "Goblin Scout": {
                            "name": "Goblin Scout",
                            "hp_current": 8,
                            "hp_max": 8,
                            "type": "enemy",
                        },
                    },
                },
                "npc_data": {
                    "Goblin Scout": {
                        "name": "Goblin Scout",
                        "role": "enemy",  # Generic role - should be deleted
                        "description": "A sneaky goblin",
                        # No backstory - generic enemy
                    },
                },
                "world_data": {},
                "custom_campaign_state": {},
            }
        )

        # Mock LLM response killing the goblin
        kill_response = self._create_kill_npc_response("Goblin Scout")
        mock_gemini_generate.return_value = FakeLLMResponse(json.dumps(kill_response))

        # Attack the goblin
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "I stab the goblin!", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Get updated state
        game_state_doc = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
        )
        updated_state = game_state_doc.to_dict()

        # Generic enemy should be DELETED from both combat and npc_data
        combatants = updated_state.get("combat_state", {}).get("combatants", {})
        npc_data = updated_state.get("npc_data", {})

        self.assertNotIn(
            "Goblin Scout",
            combatants,
            "Generic enemy should be removed from combatants",
        )

        self.assertNotIn(
            "Goblin Scout",
            npc_data,
            f"Generic enemy should be fully DELETED from npc_data. "
            f"npc_data: {npc_data}",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
    def test_dead_npc_not_offered_as_target_next_turn(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        End-to-end test: After killing an NPC, they should not appear in combat next turn.

        This tests the full scenario:
        1. Kill Marcus in turn 1
        2. On turn 2, Marcus should not be in combatants (can't attack dead enemy)
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_next_turn_campaign"
        self._setup_campaign_with_combat(fake_firestore, campaign_id)

        # Turn 1: Kill Marcus
        kill_response = self._create_kill_npc_response("Marcus")
        mock_gemini_generate.return_value = FakeLLMResponse(json.dumps(kill_response))

        response1 = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "I defeat Marcus!", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )
        self.assertEqual(response1.status_code, 200)

        # Get state after turn 1
        game_state_doc = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
        )
        state_after_kill = game_state_doc.to_dict()

        # Verify Marcus is dead but preserved
        self.assertIn("Marcus", state_after_kill.get("npc_data", {}))
        self.assertIn(
            "dead",
            state_after_kill.get("npc_data", {}).get("Marcus", {}).get("status", []),
        )

        # Verify Marcus is NOT in combatants (the bug we're fixing!)
        combatants = state_after_kill.get("combat_state", {}).get("combatants", {})
        self.assertNotIn(
            "Marcus",
            combatants,
            f"Dead NPC should NOT be in combatants on next turn. "
            f"This is the bug we're testing! Combatants: {list(combatants.keys())}",
        )


if __name__ == "__main__":
    print("=" * 70)
    print("End-to-End Tests for NPC Death State Persistence Bug")
    print("=" * 70)
    unittest.main(verbosity=2)
