"""
End-to-end test for CharacterCreationAgent activation on Turn 1.

Tests that CharacterCreationAgent ALWAYS activates on Turn 1, even when:
1. God Mode includes pre-defined character data (name, class, stats)
2. God Mode includes minimal data (just character name and setting)

CRITICAL: This validates the invariant that users creating campaigns from templates 
(like "My Epic Adventure") must review their character via CharacterCreationAgent 
before story mode starts.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ.setdefault("TESTING_AUTH_BYPASS", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient, FakeLLMResponse


class TestCharacterCreationTurn1End2End(unittest.TestCase):
    """Test CharacterCreationAgent activation on Turn 1 through full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-char-creation-turn1"
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
    def test_character_creation_agent_turn1_with_full_god_mode(
        self, mock_gemini_request, mock_get_db
    ):
        """
        Invariant: CharacterCreationAgent should activate on Turn 1 even with full God Mode character data.

        This test ensures that campaigns created from templates like "My Epic Adventure" 
        (with full character: Ser Arion, Level 1 Paladin, stats) activate the 
        CharacterCreationAgent on Turn 1 instead of jumping straight to SCENE 1.
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # God Mode data matching production "My Epic Adventure" template
        god_mode_data = """Character: Ser Arion | Setting: World of Assiah
**Your Character:**
- **Name:** Ser Arion val Valerion
- **Age:** 16
- **Class:** Level 1 Paladin (Oath of the Crown)
- **Alignment:** Neutral (Lawful Neutral leaning)

**Default Build (Level 1 Paladin):**
- **Stats:** Str 16, Con 14, Cha 16 | **HP:** 12 | **AC:** 20
- **Skills:** Persuasion, Intimidation
- **Features:** Divine Sense (4 uses), Lay on Hands (5 HP pool)

**Gear:**
- **Valerion Plate:** Heavy plate armor (AC 18)
- **"Duty's Edge":** Longsword (+5 to hit, 1d8+3 slashing)
- **Shield:** +2 AC, bearing the Two Suns of the Imperium
"""

        # Mock campaign creation response (initial campaign setup)
        campaign_creation_response = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": "Welcome to your adventure! Campaign created successfully.",
                    "entities_mentioned": [],
                    "location_confirmed": "World of Assiah",
                    "state_updates": {},
                }
            )
        )

        # Mock CharacterCreationAgent response for Turn 1
        character_creation_response = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": """[CHARACTER CREATION]

Welcome! I see you have a pre-defined character template for Ser Arion val Valerion, a Level 1 Paladin. Let's review and finalize your character before we begin the adventure.

**Your Character So Far:**
- **Name:** Ser Arion val Valerion
- **Age:** 16
- **Class:** Level 1 Paladin (Oath of the Crown)
- **Race:** (Not specified yet)

**Questions to Complete Your Character:**

1. **Race:** What race is Ser Arion? (Human, Elf, Dwarf, Halfling, Dragonborn, etc.)
2. **Background:** What was Ser Arion's life before becoming a paladin? (Noble, Soldier, Acolyte, Folk Hero, etc.)
3. **Alignment Confirmation:** You mentioned Lawful Neutral leaning - does that feel right for your character?
4. **Personality:** What drives Ser Arion? What are his ideals, bonds, and flaws?

Take your time! Once we finalize these details, we'll begin your epic adventure in the World of Assiah.""",
                    "entities_mentioned": ["Ser Arion val Valerion"],
                    "location_confirmed": "World of Assiah",
                    "state_updates": {
                        "custom_campaign_state": {
                            "character_creation_in_progress": True
                        }
                    },
                }
            )
        )

        # Set up mock response for Turn 1 interaction
        # NOTE: Campaign creation uses hardcoded mock (llm_service.py:2558), not this mock.
        # So only Turn 1 interaction calls _call_llm_api_with_llm_request.
        mock_gemini_request.return_value = character_creation_response

        # Step 1: Create campaign with full God Mode data
        campaign_data = {
            "title": "RED Test - My Epic Adventure",
            "god_mode_data": god_mode_data,
            "selectedPrompts": [],
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

        # Step 2: Make Turn 1 interaction - user wants to create their character
        turn1_data = {
            "input": "Let's create my character!",  # API expects "input" not "user_input"
            "mode": "character",
            "include_raw_llm_payloads": True,  # Get debug_info with system_instruction_files
        }

        turn1_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps(turn1_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(turn1_response.status_code, 200)
        turn1_data_response = json.loads(turn1_response.data)

        # Step 3: Verify CharacterCreationAgent was activated
        # Check system_instruction_files in debug_info to confirm which agent was used
        debug_info = turn1_data_response.get("debug_info", {})
        system_files = debug_info.get("system_instruction_files", [])

        # CharacterCreationAgent should load character_creation_instruction.md
        has_char_creation = any(
            "character_creation" in f for f in system_files
        )

        self.assertTrue(
            has_char_creation,
            f"CharacterCreationAgent should activate on Turn 1. "
            f"Expected 'character_creation_instruction.md' in system files, "
            f"got: {[f.split('/')[-1] for f in system_files]}",
        )

        # Verify character_creation_in_progress flag is set
        game_state = turn1_data_response.get("game_state", {})
        custom_state = game_state.get("custom_campaign_state", {})

        self.assertTrue(
            custom_state.get("character_creation_in_progress", False),
            "character_creation_in_progress flag should be True on Turn 1",
        )

        # Step 4: Verify narrative content shows CHARACTER CREATION, not STORY MODE
        narrative = turn1_data_response.get("narrative", "")

        # CharacterCreationAgent should return narrative with [CHARACTER CREATION] prefix
        self.assertIn(
            "[CHARACTER CREATION]",
            narrative,
            f"CharacterCreationAgent narrative should start with [CHARACTER CREATION] prefix. "
            f"Got: {narrative[:100]}..."
        )

        # CharacterCreationAgent should ask for character details (name, race, class, background, etc.)
        character_keywords = ["name", "race", "class", "background", "alignment"]
        has_char_questions = any(keyword.lower() in narrative.lower() for keyword in character_keywords)
        self.assertTrue(
            has_char_questions,
            f"CharacterCreationAgent should ask character creation questions (name, race, class, etc.). "
            f"Got: {narrative[:200]}..."
        )

        # CharacterCreationAgent should NOT return story mode content
        story_keywords = ["SCENE", "combat", "mission", "dungeon", "attack"]
        has_story_content = any(keyword in narrative for keyword in story_keywords)
        self.assertFalse(
            has_story_content,
            f"CharacterCreationAgent should NOT return story mode content (SCENE, combat, mission). "
            f"Got: {narrative[:200]}..."
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    def test_character_creation_agent_turn1_with_minimal_god_mode(
        self, mock_gemini_request, mock_get_db
    ):
        """
        Invariant: CharacterCreationAgent should activate even with minimal God Mode data.

        This test validates that even minimal God Mode (just "Character: luke | Setting: star wars")
        still activates CharacterCreationAgent instead of jumping to story mode.
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Minimal God Mode data (like user's "luke | star wars" example)
        god_mode_data = "Character: luke | Setting: star wars"

        # Mock responses
        campaign_creation_response = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": "Welcome to Star Wars! Campaign created successfully.",
                    "entities_mentioned": [],
                    "location_confirmed": "Star Wars Galaxy",
                    "state_updates": {},
                }
            )
        )

        # Return proper character creation narrative
        character_creation_response = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": """[CHARACTER CREATION]

Welcome to your Star Wars adventure! I see you want to play as Luke. Let's create your character together.

**Character Concept:** Luke in the Star Wars setting

**Let's Define Your Character:**

1. **Full Name:** Is your character named Luke Skywalker, or a different Luke?
2. **Species/Race:** Human, or another Star Wars species? (Twi'lek, Wookiee, Droid, etc.)
3. **Class/Role:** What type of character is Luke? (Jedi, Scoundrel, Soldier, Force Adept, etc.)
4. **Background:** What's Luke's story before this adventure begins?
5. **Alignment:** Light side, dark side, or somewhere in between?

Tell me your choices and we'll build Luke's character sheet together!""",
                    "entities_mentioned": ["Luke"],
                    "location_confirmed": "Star Wars Galaxy",
                    "state_updates": {
                        "custom_campaign_state": {
                            "character_creation_in_progress": True
                        }
                    },
                }
            )
        )

        # Set up mock response for Turn 1 interaction
        # NOTE: Campaign creation uses hardcoded mock, not this mock.
        mock_gemini_request.return_value = character_creation_response

        # Create campaign
        campaign_data = {
            "title": "RED Test - Star Wars Luke",
            "god_mode_data": god_mode_data,
            "selectedPrompts": [],
            "use_default_world": False,
        }

        create_response = self.client.post(
            "/api/campaigns",
            data=json.dumps(campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(create_response.status_code, 201)
        campaign_id = json.loads(create_response.data)["campaign_id"]

        # Turn 1 interaction
        turn1_response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "I want to create my character",
                "mode": "character",
                "include_raw_llm_payloads": True,
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(turn1_response.status_code, 200)
        turn1_data = json.loads(turn1_response.data)

        # Verify CharacterCreationAgent activated by checking system_instruction_files
        debug_info = turn1_data.get("debug_info", {})
        system_files = debug_info.get("system_instruction_files", [])

        has_char_creation = any("character_creation" in f for f in system_files)
        self.assertTrue(
            has_char_creation,
            f"CharacterCreationAgent should activate even with minimal God Mode data. "
            f"Got system files: {[f.split('/')[-1] for f in system_files]}",
        )

        # Verify narrative content shows CHARACTER CREATION, not STORY MODE
        narrative = turn1_data.get("narrative", "")

        self.assertIn(
            "[CHARACTER CREATION]",
            narrative,
            f"CharacterCreationAgent narrative should start with [CHARACTER CREATION] prefix. "
            f"Got: {narrative[:100]}..."
        )

        character_keywords = ["name", "race", "class", "background", "alignment"]
        has_char_questions = any(keyword.lower() in narrative.lower() for keyword in character_keywords)
        self.assertTrue(
            has_char_questions,
            f"CharacterCreationAgent should ask character creation questions (name, race, class, etc.). "
            f"Got: {narrative[:200]}..."
        )

        story_keywords = ["SCENE", "combat", "mission", "dungeon", "attack"]
        has_story_content = any(keyword in narrative for keyword in story_keywords)
        self.assertFalse(
            has_story_content,
            f"CharacterCreationAgent should NOT return story mode content (SCENE, combat, mission). "
            f"Got: {narrative[:200]}..."
        )


if __name__ == "__main__":
    unittest.main()
