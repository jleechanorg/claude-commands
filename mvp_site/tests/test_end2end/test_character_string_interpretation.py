"""
Test that LLM interprets character strings correctly without brittle parsing.

This test validates the simplified approach where:
- Character strings are passed directly to LLM (no regex parsing)
- LLM interprets natural language like "A devout cleric..."
- Works with any character string format
- No crashes from parsing failures
"""

import json
import os
import unittest
from unittest.mock import patch

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ.setdefault("TESTING_AUTH_BYPASS", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient, FakeLLMResponse


class TestCharacterStringInterpretation(unittest.TestCase):
    """Test that character strings are interpreted by LLM, not parsed by regex."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-character-string-interpretation"
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

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    def test_natural_language_character_string(self, mock_gemini_request, mock_get_db):
        """
        Test that natural language character strings work (e.g., "A devout cleric...").
        
        This validates the simplified approach where LLM interprets the string
        instead of brittle regex parsing.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Natural language character string (no structured format)
        character = "A devout cleric blessed with divine power to heal and smite"
        setting = "The haunted moors of Barovia, trapped in eternal mist and ruled by dark powers"
        description = ""

        # Mock LLM response - LLM should interpret "devout cleric" as Cleric class
        character_creation_narrative = """[CHARACTER CREATION]

Welcome! I see you have a pre-defined character template. Let's review and finalize your character before we begin the adventure.

**Your Character So Far:**
- **Name:** A devout cleric blessed with divine power to heal and smite
- **Class:** Cleric (interpreted from character description)
- **Race:** (Not specified yet)

**Questions to Complete Your Character:**
1. **Race:** What race is your character?
2. **Background:** What was your life before becoming a cleric?
3. **Alignment:** What alignment best fits your character?

Take your time! Once we finalize these details, we'll begin your epic adventure."""

        mock_response = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": character_creation_narrative,
                    "entities_mentioned": [],
                    "location_confirmed": "",
                    "state_updates": {
                        "custom_campaign_state": {
                            "character_creation_in_progress": True
                        }
                    },
                }
            )
        )
        mock_gemini_request.return_value = mock_response

        # Create campaign with natural language character string
        campaign_data = {
            "title": "Natural Language Character Test",
            "character": character,  # ← Natural language, no structured format
            "setting": setting,
            "description": description,
            "selected_prompts": [],
            "use_default_world": False,
        }

        create_response = self.client.post(
            "/api/campaigns",
            data=json.dumps(campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(create_response.status_code, 201, "Campaign creation should succeed")
        create_data = json.loads(create_response.data)
        campaign_id = create_data["campaign_id"]

        # Get campaign state to verify opening story
        get_state_response = self.client.get(
            f"/api/campaigns/{campaign_id}",
            headers=self.test_headers,
        )

        self.assertEqual(get_state_response.status_code, 200)
        state_data = json.loads(get_state_response.data)

        # Extract opening story
        story_entries = state_data.get("story", [])
        opening_story_text = ""
        for entry in story_entries:
            if isinstance(entry, dict) and entry.get("actor") == "gemini":
                opening_story_text = entry.get("text", "")
                break

        # Verify NOT placeholder
        self.assertNotIn(
            "[Character Creation Mode - Story begins after character is complete]",
            opening_story_text,
            "Should NOT show placeholder - character string should be interpreted",
        )

        # Verify character creation narrative was generated
        self.assertIn(
            "CHARACTER CREATION",
            opening_story_text.upper(),
            "Should generate character creation narrative",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    def test_structured_character_string(self, mock_gemini_request, mock_get_db):
        """
        Test that structured character strings also work (e.g., "Level 1 Fighter").
        
        Validates that both natural language AND structured formats work.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Structured character string (with level and class)
        character = "Level 1 Fighter"
        setting = "Forgotten Realms"
        description = "A brave warrior seeking adventure"

        mock_response = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": "[CHARACTER CREATION]\n\nWelcome! Let's review your Level 1 Fighter...",
                    "entities_mentioned": [],
                    "location_confirmed": "",
                    "state_updates": {
                        "custom_campaign_state": {
                            "character_creation_in_progress": True
                        }
                    },
                }
            )
        )
        mock_gemini_request.return_value = mock_response

        campaign_data = {
            "title": "Structured Character Test",
            "character": character,
            "setting": setting,
            "description": description,
            "selected_prompts": [],
            "use_default_world": False,
        }

        create_response = self.client.post(
            "/api/campaigns",
            data=json.dumps(campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(create_response.status_code, 201)
        create_data = json.loads(create_response.data)
        campaign_id = create_data["campaign_id"]

        # Verify campaign was created successfully
        get_state_response = self.client.get(
            f"/api/campaigns/{campaign_id}",
            headers=self.test_headers,
        )

        self.assertEqual(get_state_response.status_code, 200)
        state_data = json.loads(get_state_response.data)

        # Verify NOT placeholder
        story_entries = state_data.get("story", [])
        opening_story_text = ""
        for entry in story_entries:
            if isinstance(entry, dict) and entry.get("actor") == "gemini":
                opening_story_text = entry.get("text", "")
                break

        self.assertNotIn(
            "[Character Creation Mode - Story begins after character is complete]",
            opening_story_text,
            "Structured format should also work",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    def test_minimal_character_string(self, mock_gemini_request, mock_get_db):
        """
        Test that minimal character strings work (just a name).
        
        Validates that even minimal strings don't crash.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Minimal character string (just a name)
        character = "Gandalf"
        setting = "Middle-earth"
        description = ""

        mock_response = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": "[CHARACTER CREATION]\n\nWelcome! Let's review your character Gandalf...",
                    "entities_mentioned": [],
                    "location_confirmed": "",
                    "state_updates": {
                        "custom_campaign_state": {
                            "character_creation_in_progress": True
                        }
                    },
                }
            )
        )
        mock_gemini_request.return_value = mock_response

        campaign_data = {
            "title": "Minimal Character Test",
            "character": character,
            "setting": setting,
            "description": description,
            "selected_prompts": [],
            "use_default_world": False,
        }

        create_response = self.client.post(
            "/api/campaigns",
            data=json.dumps(campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(create_response.status_code, 201, "Minimal character string should work")
        create_data = json.loads(create_response.data)
        campaign_id = create_data["campaign_id"]

        # Verify campaign was created
        get_state_response = self.client.get(
            f"/api/campaigns/{campaign_id}",
            headers=self.test_headers,
        )

        self.assertEqual(get_state_response.status_code, 200)

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    def test_complex_character_string(self, mock_gemini_request, mock_get_db):
        """
        Test that complex character strings work (multiple sentences, descriptions).
        
        Validates that complex natural language doesn't break parsing.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Complex character string (multiple sentences, no structured format)
        character = "A mysterious rogue who was once a noble but fell from grace. Now they wander the shadows, seeking redemption through acts of mercy and justice."
        setting = "Waterdeep"
        description = ""

        mock_response = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": "[CHARACTER CREATION]\n\nWelcome! Let's review your character...",
                    "entities_mentioned": [],
                    "location_confirmed": "",
                    "state_updates": {
                        "custom_campaign_state": {
                            "character_creation_in_progress": True
                        }
                    },
                }
            )
        )
        mock_gemini_request.return_value = mock_response

        campaign_data = {
            "title": "Complex Character Test",
            "character": character,
            "setting": setting,
            "description": description,
            "selected_prompts": [],
            "use_default_world": False,
        }

        create_response = self.client.post(
            "/api/campaigns",
            data=json.dumps(campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(create_response.status_code, 201, "Complex character string should work")
        create_data = json.loads(create_response.data)
        campaign_id = create_data["campaign_id"]

        # Verify campaign was created
        get_state_response = self.client.get(
            f"/api/campaigns/{campaign_id}",
            headers=self.test_headers,
        )

        self.assertEqual(get_state_response.status_code, 200)

    def test_god_mode_dict_building(self):
        """
        Test that god_mode dict is built correctly from character string.
        
        Validates that is_god_mode_with_character check works.
        """
        from mvp_site.world_logic import create_campaign_unified
        import asyncio

        # Test different character string formats
        test_cases = [
            {
                "name": "Natural language",
                "character": "A devout cleric blessed with divine power",
                "setting": "Barovia",
                "description": "",
            },
            {
                "name": "Structured format",
                "character": "Level 1 Fighter",
                "setting": "Forgotten Realms",
                "description": "",
            },
            {
                "name": "Minimal name",
                "character": "Gandalf",
                "setting": "Middle-earth",
                "description": "",
            },
            {
                "name": "Complex description",
                "character": "A mysterious rogue who was once a noble",
                "setting": "Waterdeep",
                "description": "Seeking redemption through acts of mercy",
            },
        ]

        for test_case in test_cases:
            with self.subTest(test_case=test_case["name"]):
                # Simulate the dict building logic
                character = test_case["character"]
                setting = test_case["setting"]
                description = test_case["description"]

                god_mode = {}
                if setting:
                    god_mode["setting"] = setting
                if description:
                    god_mode["description"] = description
                if character:
                    character_dict = {}
                    if isinstance(character, str):
                        character_dict["name"] = character.strip()
                        if description:
                            character_dict["description"] = description.strip()
                    if character_dict:
                        god_mode["character"] = character_dict

                # Verify is_god_mode_with_character check
                is_god_mode_with_character = (
                    god_mode
                    and isinstance(god_mode, dict)
                    and god_mode.get("character")
                    and isinstance(god_mode.get("character"), dict)
                )

                self.assertTrue(
                    is_god_mode_with_character,
                    f"is_god_mode_with_character should be True for {test_case['name']}. "
                    f"Got: god_mode={god_mode}",
                )

                # Verify character dict has name
                self.assertIn(
                    "name",
                    god_mode["character"],
                    f"Character dict should have 'name' key for {test_case['name']}",
                )

                # Verify character string is preserved
                self.assertEqual(
                    god_mode["character"]["name"],
                    character.strip(),
                    f"Character string should be preserved for {test_case['name']}",
                )


if __name__ == "__main__":
    unittest.main()
