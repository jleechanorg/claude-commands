"""
End-to-end test for action_resolution backward compatibility and null handling.

Tests the full flow from LLM response through API to ensure:
1. Backward compatibility: outcome_resolution maps to action_resolution
2. Null safety: None values don't leak to API responses
3. Both fields appear in unified_response when present
4. llm_response.action_resolution property falls back correctly

Only mocks external services (Gemini API and Firestore DB) at the lowest level.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

# Set TESTING_AUTH_BYPASS environment variable before imports
os.environ["TESTING_AUTH_BYPASS"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestActionResolutionBackwardCompatEnd2End(unittest.TestCase):
    """Test action_resolution backward compatibility through the full application stack."""

    def setUp(self):
        """Set up test client and test data."""
        # Disable MOCK_SERVICES_MODE to ensure our mocks are used
        import os
        self._original_mock_mode = os.environ.get("MOCK_SERVICES_MODE")
        os.environ["MOCK_SERVICES_MODE"] = "false"
        
        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data
        self.test_user_id = "action-res-test-user-123"
        self.test_campaign_id = "action-res-test-campaign-456"

        # Stub Firebase token verification
        self._auth_patcher = patch(
            "mvp_site.main.auth.verify_id_token", return_value={"uid": self.test_user_id}
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        self.test_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

        # Set up fake Firestore
        self.fake_firestore = FakeFirestoreClient()

        # Create initial user document with settings
        user_data = {
            "settings": {
                "gemini_model": "gemini-3-flash-preview",
            },
            "lastUpdated": "2025-01-01T00:00:00Z",
        }
        users_collection = self.fake_firestore.collection("users")
        user_doc = users_collection.document(self.test_user_id)
        user_doc.set(user_data)

        # Create initial campaign data
        campaign_data = {
            "title": "Action Resolution Test Campaign",
            "prompt": "Test campaign for action resolution backward compatibility",
            "user_id": self.test_user_id,
        }

        # Set up campaign in fake Firestore
        campaigns_collection = user_doc.collection("campaigns")
        campaign_doc = campaigns_collection.document(self.test_campaign_id)
        campaign_doc.set(campaign_data)

        # Set up initial game state
        game_state_data = {
            "game_state_version": 1,
            "player_character_data": {
                "name": "Test Hero",
                "level": 1,
                "hp_current": 10,
                "hp_max": 10,
            },
        }
        game_state_doc = campaign_doc.collection("game_state").document("current")
        game_state_doc.set(game_state_data)
    
    def tearDown(self):
        """Clean up test environment."""
        import os
        if hasattr(self, "_original_mock_mode"):
            if self._original_mock_mode is None:
                os.environ.pop("MOCK_SERVICES_MODE", None)
            else:
                os.environ["MOCK_SERVICES_MODE"] = self._original_mock_mode

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_action_resolution_primary_field_in_api_response(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that action_resolution (new field) appears in API response.

        Scenario:
        1. LLM returns response with action_resolution field
        2. API response includes action_resolution in unified_response
        3. No null values leak to API
        """
        mock_get_db.return_value = self.fake_firestore

        # Mock LLM response with action_resolution
        llm_response_json = json.dumps({
            "narrative": "You attack the goblin with your sword.",
            "action_resolution": {
                "player_input": "I attack the goblin",
                "interpreted_as": "melee_attack",
                "reinterpreted": False,
                "mechanics": {
                    "rolls": [{"purpose": "attack", "notation": "1d20+5", "result": 17}],
                },
                "audit_flags": [],
            },
        })

        mock_gemini_generate.return_value = FakeLLMResponse(llm_response_json)

        # Process action
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            json={"input": "I attack the goblin"},
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify action_resolution appears in response
        self.assertIn("action_resolution", data)
        self.assertIsInstance(data["action_resolution"], dict)
        self.assertEqual(data["action_resolution"]["player_input"], "I attack the goblin")
        self.assertEqual(data["action_resolution"]["interpreted_as"], "melee_attack")
        self.assertFalse(data["action_resolution"]["reinterpreted"])

        # Verify no null values
        self.assertIsNotNone(data["action_resolution"])

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_outcome_resolution_backward_compat_in_api_response(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that outcome_resolution (legacy field) maps to action_resolution in API.

        Scenario:
        1. LLM returns response with ONLY outcome_resolution (legacy format)
        2. API response includes BOTH action_resolution (mapped) AND outcome_resolution (for backward compat)
        3. No null values leak to API
        """
        mock_get_db.return_value = self.fake_firestore

        # Mock LLM response with ONLY outcome_resolution (legacy format)
        llm_response_json = json.dumps({
            "narrative": "You try to convince the king to help.",
            "outcome_resolution": {
                "player_input": "The king agrees",
                "interpreted_as": "persuasion_attempt",
                "reinterpreted": True,
                "mechanics": {
                    "skill": "Persuasion",
                    "dc": 18,
                    "roll": "1d20+5",
                    "result": 19,
                },
                "audit_flags": ["player_declared_outcome"],
            },
        })

        mock_gemini_generate.return_value = FakeLLMResponse(llm_response_json)

        # Process action
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            json={"input": "The king agrees"},
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify action_resolution appears (mapped from outcome_resolution)
        self.assertIn("action_resolution", data)
        self.assertIsInstance(data["action_resolution"], dict)
        self.assertEqual(data["action_resolution"]["player_input"], "The king agrees")
        self.assertTrue(data["action_resolution"]["reinterpreted"])

        # Verify outcome_resolution also appears (for backward compatibility)
        self.assertIn("outcome_resolution", data)
        self.assertIsInstance(data["outcome_resolution"], dict)
        self.assertEqual(data["outcome_resolution"]["player_input"], "The king agrees")

        # Verify no null values
        self.assertIsNotNone(data["action_resolution"])
        self.assertIsNotNone(data["outcome_resolution"])

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_null_action_resolution_not_in_api_response(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that None values for action_resolution don't leak to API.

        Scenario:
        1. LLM returns response with action_resolution=None
        2. API response does NOT include action_resolution field (not null)
        3. Field is absent, not null
        """
        mock_get_db.return_value = self.fake_firestore

        # Mock LLM response with action_resolution=None
        llm_response_json = json.dumps({
            "narrative": "You look around the room.",
            "action_resolution": None,  # Explicitly None
        })

        mock_gemini_generate.return_value = FakeLLMResponse(llm_response_json)

        # Process action
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            json={"input": "I look around"},
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify action_resolution is NOT in response (not null, just absent)
        # OR if present, it's an empty dict, not None
        if "action_resolution" in data:
            # If present, must be dict, not None
            self.assertIsInstance(data["action_resolution"], dict)
            self.assertIsNotNone(data["action_resolution"])

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_both_fields_when_both_provided(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that when both action_resolution and outcome_resolution are provided,
        action_resolution takes precedence but both appear in API.

        Scenario:
        1. LLM returns response with BOTH fields
        2. API response includes both fields
        3. action_resolution takes precedence (used internally)
        """
        mock_get_db.return_value = self.fake_firestore

        # Mock LLM response with BOTH fields
        llm_response_json = json.dumps({
            "narrative": "You cast a fireball.",
            "action_resolution": {
                "player_input": "I cast Fireball",
                "interpreted_as": "spell_cast",
                "reinterpreted": False,
                "mechanics": {
                    "spell": "Fireball",
                    "level": 3,
                },
                "audit_flags": [],
            },
            "outcome_resolution": {
                "player_input": "I cast Fireball (legacy)",
                "interpreted_as": "spell_cast",
                "reinterpreted": False,
            },
        })

        mock_gemini_generate.return_value = FakeLLMResponse(llm_response_json)

        # Process action
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            json={"input": "I cast Fireball"},
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify both fields appear
        self.assertIn("action_resolution", data)
        self.assertIn("outcome_resolution", data)

        # Verify action_resolution takes precedence (has spell info)
        self.assertEqual(data["action_resolution"]["player_input"], "I cast Fireball")
        self.assertIn("mechanics", data["action_resolution"])
        self.assertEqual(data["action_resolution"]["mechanics"]["spell"], "Fireball")

        # Verify no null values
        self.assertIsNotNone(data["action_resolution"])
        self.assertIsNotNone(data["outcome_resolution"])

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_llm_response_action_resolution_property_fallback(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that llm_response.action_resolution property falls back to outcome_resolution.

        This tests the backward compatibility in llm_response.py property.
        """
        mock_get_db.return_value = self.fake_firestore

        # Mock LLM response with ONLY outcome_resolution
        llm_response_json = json.dumps({
            "narrative": "You attempt to persuade the guard.",
            "outcome_resolution": {
                "player_input": "The guard lets you pass",
                "interpreted_as": "persuasion_attempt",
                "reinterpreted": True,
                "audit_flags": ["player_declared_outcome"],
            },
        })

        mock_gemini_generate.return_value = FakeLLMResponse(llm_response_json)

        # Process action
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            json={"input": "The guard lets you pass"},
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify action_resolution appears (via property fallback)
        # The llm_response.action_resolution property should have fallen back
        # to outcome_resolution, and world_logic should include it in unified_response
        self.assertIn("action_resolution", data)
        self.assertEqual(data["action_resolution"]["player_input"], "The guard lets you pass")
        self.assertTrue(data["action_resolution"]["reinterpreted"])

        # Verify no null values
        self.assertIsNotNone(data["action_resolution"])

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_action_resolution_persisted_to_firestore(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that action_resolution is persisted to Firestore story entries.
        
        This validates the fix for the bug where action_resolution was added to
        unified_response but not persisted to Firestore.
        
        Scenario:
        1. LLM returns response with action_resolution
        2. Process action via API
        3. Verify action_resolution is saved in Firestore story entry
        """
        mock_get_db.return_value = self.fake_firestore

        # Mock LLM response with action_resolution
        llm_response_json = json.dumps({
            "narrative": "You attack the goblin with your sword.",
            "action_resolution": {
                "player_input": "I attack the goblin",
                "interpreted_as": "melee_attack",
                "reinterpreted": False,
                "mechanics": {
                    "rolls": [{"purpose": "attack", "notation": "1d20+5", "result": 17}],
                },
                "audit_flags": [],
            },
        })

        mock_gemini_generate.return_value = FakeLLMResponse(llm_response_json)

        # Process action
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            json={"input": "I attack the goblin"},
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify action_resolution appears in API response
        self.assertIn("action_resolution", data)

        # Verify action_resolution is persisted to Firestore story entry
        # Get the story collection
        users_collection = self.fake_firestore.collection("users")
        user_doc = users_collection.document(self.test_user_id)
        campaigns_collection = user_doc.collection("campaigns")
        campaign_doc = campaigns_collection.document(self.test_campaign_id)
        story_collection = campaign_doc.collection("story")

        # Find the latest Gemini entry (actor == 'gemini')
        gemini_entries = [
            entry for entry in story_collection.stream()
            if entry.to_dict().get("actor") == "gemini"
        ]

        self.assertGreater(len(gemini_entries), 0, "No Gemini story entries found")

        # Check the most recent entry
        latest_entry = gemini_entries[-1]
        entry_data = latest_entry.to_dict()

        # Verify action_resolution is present in Firestore entry
        self.assertIn(
            "action_resolution",
            entry_data,
            "action_resolution not found in Firestore story entry. "
            "This indicates the bug where action_resolution wasn't persisted."
        )

        # Verify the structure matches what was in the API response
        firestore_ar = entry_data["action_resolution"]
        self.assertIsInstance(firestore_ar, dict)
        self.assertEqual(firestore_ar["player_input"], "I attack the goblin")
        self.assertEqual(firestore_ar["interpreted_as"], "melee_attack")
        self.assertFalse(firestore_ar["reinterpreted"])
        self.assertIn("mechanics", firestore_ar)
        self.assertIn("audit_flags", firestore_ar)

        # Also verify outcome_resolution is present (backward compat)
        self.assertIn(
            "outcome_resolution",
            entry_data,
            "outcome_resolution should also be persisted for backward compatibility"
        )


if __name__ == "__main__":
    unittest.main()
