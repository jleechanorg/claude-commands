"""
End-to-end integration test for embedded planning block JSON in narrative bug.

BUG REPRODUCTION:
When the LLM includes raw JSON like {"thinking": ..., "choices": ...} in the
narrative text, this JSON should be stripped from the displayed narrative since
the planning_block is a separate structured field.

This test mocks the LLM provider at the lowest level and tests the full flow
from API endpoint through all service layers to verify the JSON stripping works.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestEmbeddedJsonNarrativeEnd2End(unittest.TestCase):
    """End-to-end test for embedded planning block JSON in narrative."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-embedded-json"
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

        # The embedded planning block JSON that was appearing in user narratives
        self.embedded_planning_json = """{
    "thinking": "The family has been completely broken by your dramatic revelation. Now is the perfect moment to extract binding oaths while their psychological defenses are shattered.",
    "choices": {
        "magical_oaths_binding": {
            "text": "Magical Oaths and Binding",
            "description": "Use your spellcasting to magically bind each family member",
            "risk_level": "medium"
        },
        "psychological_dominance": {
            "text": "Psychological Dominance",
            "description": "Extract verbal oaths through terror and pressure",
            "risk_level": "low"
        }
    }
}"""

        # LLM response that reproduces the bug - narrative contains embedded JSON
        self.mock_llm_response_with_embedded_json = {
            "narrative": f"""--- PLANNING BLOCK ---

**Tactical Analysis:** Your family revelation has achieved perfect psychological impact.

{self.embedded_planning_json}

The family has been completely broken. Choose your approach.""",
            "entities_mentioned": ["family", "Marcus", "Elora"],
            "location_confirmed": "Chapel",
            "planning_block": {
                "thinking": "Proper planning block in the correct field",
                "choices": {
                    "option_1": {
                        "text": "Option 1",
                        "description": "First option",
                        "risk_level": "low",
                    }
                },
            },
            "state_updates": {},
        }

    def _setup_fake_firestore_with_campaign(self, fake_firestore, campaign_id):
        """Helper to set up fake Firestore with campaign and game state."""
        # Create test campaign data
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Test Campaign - Embedded JSON Bug", "setting": "Fantasy realm"}
        )

        # Create game state with proper structure
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "Previous story content",
                "characters": ["Marcus", "Elora"],
                "locations": ["Chapel"],
                "items": [],
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_embedded_json_stripped_from_narrative_end2end(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        RED→GREEN TEST: Embedded planning block JSON should be stripped from narrative.

        This test reproduces the exact bug scenario:
        1. LLM returns a response with planning block JSON embedded in the narrative
        2. The full application stack processes the response
        3. The API response should NOT contain raw JSON in the narrative text
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_embedded_json_bug"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini to return response with embedded JSON in narrative
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_with_embedded_json)
        )

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "extract binding oaths", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response is successful
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )
        data = json.loads(response.data)

        # Verify story data structure
        assert "story" in data
        assert isinstance(data["story"], list)
        assert len(data["story"]) > 0

        # Find all narrative text from all story entries
        all_narrative_text = " ".join(entry.get("text", "") for entry in data["story"])

        # THE CRITICAL ASSERTIONS - raw JSON should NOT appear in narrative
        assert '"thinking":' not in all_narrative_text, (
            f"BUG: Raw JSON key 'thinking' should not appear in narrative. Got: {all_narrative_text[:500]}"
        )
        assert '"choices":' not in all_narrative_text, (
            f"BUG: Raw JSON key 'choices' should not appear in narrative. Got: {all_narrative_text[:500]}"
        )
        assert '"magical_oaths_binding":' not in all_narrative_text, (
            f"BUG: Raw JSON choice key should not appear in narrative. Got: {all_narrative_text[:500]}"
        )

        # Verify context is still present (non-JSON parts)
        assert (
            "PLANNING BLOCK" in all_narrative_text
            or "Tactical Analysis" in all_narrative_text
        ), "Expected non-JSON context to be preserved in narrative"

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_narrative_only_json_gets_cleaned_end2end(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test case where narrative is ONLY the embedded JSON (worst case).

        When the narrative is ONLY planning block JSON and gets stripped to empty,
        the system should either:
        1. Return an error (empty narrative rejected), OR
        2. Return without displaying raw JSON to user

        This test verifies the JSON stripping works and the user never sees raw JSON.
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_json_only_narrative"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # LLM response where narrative is just the embedded JSON
        # Include some surrounding text so it doesn't become completely empty
        mock_response = {
            "narrative": f"The story continues.\n\n{self.embedded_planning_json}\n\nChoose wisely.",
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "planning_block": {},
            "state_updates": {},
        }

        mock_gemini_generate.return_value = FakeLLMResponse(json.dumps(mock_response))

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "test action", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Find all narrative text from story entries
        all_narrative_text = " ".join(entry.get("text", "") for entry in data["story"])

        # The narrative should not be raw JSON
        # Check that no entry starts with JSON brace
        json_start_entries = [
            e.get("text", "").strip()
            for e in data["story"]
            if e.get("text", "").strip().startswith("{")
        ]
        assert len(json_start_entries) == 0, (
            f"BUG: Narrative entries should not start with JSON brace. Got: {json_start_entries}"
        )
        assert '"thinking":' not in all_narrative_text, (
            f"BUG: Raw JSON should not appear. Got: {all_narrative_text[:200]}"
        )

        # Should preserve the surrounding narrative text
        assert (
            "story continues" in all_narrative_text
            or "Choose wisely" in all_narrative_text
        ), f"Non-JSON content should be preserved. Got: {all_narrative_text[:200]}"

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_clean_narrative_unchanged_end2end(self, mock_gemini_generate, mock_get_db):
        """
        Verify that normal narratives without embedded JSON are unchanged.
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_clean_narrative"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Clean LLM response without embedded JSON
        clean_narrative = "The adventurer walks into the tavern. A warm fire crackles in the hearth as patrons chat quietly over mugs of ale."
        mock_response = {
            "narrative": clean_narrative,
            "entities_mentioned": ["adventurer", "tavern"],
            "location_confirmed": "Tavern",
            "planning_block": {
                "thinking": "The player is exploring the town",
                "choices": {
                    "talk_bartender": {
                        "text": "Talk to Bartender",
                        "description": "Strike up a conversation",
                        "risk_level": "safe",
                    }
                },
            },
            "state_updates": {},
        }

        mock_gemini_generate.return_value = FakeLLMResponse(json.dumps(mock_response))

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "go to tavern", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Find all narrative text from story entries
        all_narrative_text = " ".join(entry.get("text", "") for entry in data["story"])

        # Clean narrative should be preserved (somewhere in story entries)
        assert "adventurer walks into the tavern" in all_narrative_text, (
            f"Clean narrative should be preserved. Got: {all_narrative_text}"
        )
        assert "warm fire crackles" in all_narrative_text, (
            f"Full narrative content should be preserved. Got: {all_narrative_text}"
        )


class TestEmbeddedJsonRealWorldScenario(unittest.TestCase):
    """Test the exact scenario reported by the user."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.test_user_id = "test-user-real-world"
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

    def _setup_fake_firestore_with_campaign(self, fake_firestore, campaign_id):
        """Helper to set up fake Firestore with campaign and game state."""
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "House Sosuke Campaign", "setting": "D&D 5e"}
        )

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "Previous events in the campaign",
                "characters": ["Marcus", "Elora", "Tomas"],
                "locations": ["Abandoned Sosuke Family Chapel"],
                "items": ["surveillance crystal"],
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_real_world_bug_exact_reproduction_end2end(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Reproduce the EXACT bug scenario from the user report.

        The user saw a campaign response like:
        - Session header with timestamp and location
        - Scene #444: --- PLANNING BLOCK ---
        - Tactical Analysis text
        - RAW JSON {"thinking": ..., "choices": ...}  <-- BUG!
        - Then properly rendered choices below
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "sosuke_campaign_bug"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # This is the EXACT response structure that caused the bug
        bug_response = {
            "narrative": """Main Character: Extract Binding Oaths - Use magical methods or psychological pressure.

Scene #444: --- PLANNING BLOCK ---

**Tactical Analysis:** Your family revelation has achieved perfect psychological impact. Marcus grovels at your feet, Elora sobs brokenly in the pews, and Tomas stands frozen in horror.

{
    "thinking": "The family has been completely broken by your dramatic revelation. Now is the perfect moment to extract binding oaths while their psychological defenses are shattered.",
    "choices": {
        "magical_oaths_binding": {
            "text": "Magical Oaths and Binding",
            "description": "Use your spellcasting to magically bind each family member to unbreakable oaths",
            "risk_level": "medium",
            "analysis": {
                "pros": ["Absolute supernatural compulsion", "Immediate and unbreakable results"],
                "cons": ["Consumes valuable spell slots", "Magical signatures detectable by authorities"]
            }
        },
        "psychological_dominance": {
            "text": "Psychological Dominance Extraction",
            "description": "Extract binding verbal oaths through amplified terror and blackmail",
            "risk_level": "low"
        }
    }
}

The family has been completely broken. Choose your approach.""",
            "session_header": "Timestamp: 1492 DR, Mirtul 16, 02:31:00\nLocation: Abandoned Sosuke Family Chapel",
            "entities_mentioned": ["Marcus", "Elora", "Tomas", "family"],
            "location_confirmed": "Abandoned Sosuke Family Chapel",
            "planning_block": {
                "thinking": "The family has been completely broken",
                "choices": {
                    "magical_oaths_binding": {
                        "text": "Magical Oaths and Binding",
                        "description": "Use spellcasting to bind family members",
                        "risk_level": "medium",
                    },
                    "psychological_dominance": {
                        "text": "Psychological Dominance",
                        "description": "Extract oaths through terror",
                        "risk_level": "low",
                    },
                },
            },
            "state_updates": {},
        }

        mock_gemini_generate.return_value = FakeLLMResponse(json.dumps(bug_response))

        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "Extract Binding Oaths", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = json.loads(response.data)

        # Find all narrative text from story entries
        all_narrative_text = " ".join(entry.get("text", "") for entry in data["story"])

        # CRITICAL: The raw JSON should NOT appear
        assert '{\n    "thinking":' not in all_narrative_text, (
            f"BUG NOT FIXED: Raw embedded JSON block found in narrative!\n\nNarrative:\n{all_narrative_text[:1000]}"
        )
        assert '"choices": {' not in all_narrative_text, (
            f"BUG NOT FIXED: Raw JSON choices found in narrative!\n\nNarrative:\n{all_narrative_text[:1000]}"
        )
        assert '"magical_oaths_binding":' not in all_narrative_text, (
            f"BUG NOT FIXED: Raw JSON choice key found!\n\nNarrative:\n{all_narrative_text[:1000]}"
        )

        # Context should be preserved
        assert (
            "PLANNING BLOCK" in all_narrative_text
            or "Tactical Analysis" in all_narrative_text
        ), f"Non-JSON context should be preserved. Got: {all_narrative_text[:500]}"


if __name__ == "__main__":
    unittest.main()
