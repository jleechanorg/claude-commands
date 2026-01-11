"""
End-to-end test reproducing God Mode placeholder bug.

BUG: Real user campaigns show placeholder text on Turn 0:
    "[Character Creation Mode - Story begins after character is complete]"

Instead of proper character creation narrative that should be generated immediately.

ROOT CAUSE: god_mode_data (string format) is not parsed into god_mode (dict format),
so is_god_mode_with_character check fails and placeholder is shown.

This test reproduces the bug by:
1. Creating campaign with god_mode_data as string (matching real user flow)
2. Checking opening story (Turn 0) for placeholder text
3. Verifying that character creation narrative is NOT generated
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


class TestGodModePlaceholderBugEnd2End(unittest.TestCase):
    """Test that reproduces God Mode placeholder bug on Turn 0."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-god-mode-placeholder-bug"
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
    def test_god_mode_placeholder_bug_reproduction(
        self, mock_gemini_request, mock_get_db
    ):
        """
        RED TEST: Reproduce the bug where god_mode_data (string) shows placeholder.

        This test matches the REAL USER FLOW:
        - User creates campaign via frontend
        - Frontend sends god_mode_data as STRING (not dict)
        - Opening story should show character creation narrative
        - BUT bug shows placeholder instead

        Expected to FAIL (RED) until bug is fixed.
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # God Mode data as STRING (matching real user flow from frontend)
        # This is the format users send via frontend, NOT a dict
        god_mode_data = """Character: Ser Arion | Setting: World of Assiah. Caught between an oath to a ruthless tyrant who enforces a prosperous peace and the call of a chaotic dragon promising true freedom, a young knight must decide whether to slaughter innocents to preserve order or start a war to reclaim the world's soul. | Description: # Campaign summary

You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium. For decades, the Empire has been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her methods are terrifying, her reign has brought undeniable benefits: the roads are safe, trade flourishes, and the common people no longer starve or fear bandits. You are a product of this "Silent Peace," and your oath binds you to the security and prosperity it provides.

Your loyalty is now brutally tested. You have been ordered to slaughter a settlement of innocent refugees whose very existence has been deemed a threat to the Empress's perfect, unyielding order. As you wrestle with this monstrous command, the weight of your oath clashes with the humanity you feel for the innocent lives before you.

You are now caught between duty and conscience. Do you uphold your oath and commit an atrocity, believing the sacrifice of a few is worth the peace and safety of millions? Or do you break your vow and defy the Empress, knowing that rebellion could plunge the world back into chaos? This single choice will define your honor and your path in an empire where security is bought with blood.

**Your Character:**

- **Name:** Ser Arion val Valerion
- **Age:** 16
- **Class:** Level 1 Paladin (Oath of the Crown, sworn to Empress Sariel and the Laws of the Imperium)
- **Alignment:** Neutral (Lawful Neutral leaning) — Your choices determine whether you become a champion of justice or an instrument of tyranny.
- **Background:** Noble Knight of House Valerion

**Default Build (Level 1 Paladin):**
- **Stats:** Str 16, Con 14, Cha 16 | **HP:** 12 | **AC:** 20
- **Skills:** Persuasion, Intimidation
- **Features:** Divine Sense (4 uses), Lay on Hands (5 HP pool)

**Gear:**
- **Valerion Plate:** Heavy plate armor (AC 18), house sigil
- **"Duty's Edge":** Longsword (+5 to hit, 1d8+3 slashing)
- **Shield:** +2 AC, bearing the Two Suns of the Imperium
- **The Gryphon Helm:** Your iconic helmet"""

        # Mock LLM response for opening story generation (if it happens)
        # This should be called for God Mode campaigns with character data
        character_review_narrative = FakeLLMResponse(
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

        # Set up mock - but this might not be called if bug triggers placeholder
        mock_gemini_request.return_value = character_review_narrative

        # Step 1: Create campaign with god_mode_data as STRING (real user flow)
        campaign_data = {
            "title": "RED Test - God Mode Placeholder Bug",
            "god_mode_data": god_mode_data,  # ← STRING format, not dict!
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

        # Step 2: Get campaign state to check opening story (Turn 0)
        # The opening story is stored in the campaign's story collection
        # Use get_campaign_state MCP tool via the visit campaign endpoint
        get_state_response = self.client.get(
            f"/api/campaigns/{campaign_id}",
            headers=self.test_headers,
        )

        self.assertEqual(get_state_response.status_code, 200)
        state_data = json.loads(get_state_response.data)

        # Extract opening story from campaign state
        # Opening story is the first gemini/agent entry in the story collection
        story_entries = state_data.get("story", [])
        
        # Find the first agent/gemini story entry (opening story)
        opening_story = ""
        for entry in story_entries:
            if isinstance(entry, dict):
                actor = entry.get("actor", "")
                text = entry.get("text", "")
                # Opening story is typically from "gemini" or "agent" actor
                if actor in ("gemini", "agent", "system") and text:
                    opening_story = text
                    break
            elif isinstance(entry, str):
                # If story entries are just strings, use the first one
                opening_story = entry
                break
        
        # Fallback: check campaign metadata
        if not opening_story:
            opening_story = state_data.get("opening_story", "") or state_data.get("initial_story", "") or ""

        # Step 3: VERIFY BUG REPRODUCTION
        # The bug shows placeholder text instead of character creation narrative
        
        # BUG CHECK 1: Placeholder text should NOT be present
        placeholder_text = "[Character Creation Mode - Story begins after character is complete]"
        self.assertNotIn(
            placeholder_text,
            opening_story,
            f"BUG REPRODUCED: Opening story contains placeholder text '{placeholder_text}'. "
            f"This means god_mode_data (string) was not parsed into god_mode (dict), "
            f"so is_god_mode_with_character check failed. "
            f"Opening story: {opening_story[:200]}...",
        )

        # BUG CHECK 2: Character creation narrative SHOULD be present
        # For God Mode campaigns with character data, we should see character review narrative
        self.assertIn(
            "[CHARACTER CREATION]",
            opening_story,
            f"Opening story should contain character creation narrative for God Mode campaigns. "
            f"Got: {opening_story[:200]}...",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    def test_god_mode_placeholder_bug_frontend_format(
        self, mock_gemini_request, mock_get_db
    ):
        """
        Test that frontend format (character/setting/description as separate fields) works.

        Frontend sends character/setting/description as separate fields, NOT god_mode_data string.
        This test validates the fix handles the frontend format correctly.
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Frontend format: separate fields (NOT god_mode_data string)
        character = "Ser Arion val Valerion"
        setting = "World of Assiah. Caught between an oath to a ruthless tyrant..."
        description = """# Campaign summary

You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium.

**Your Character:**

- **Name:** Ser Arion val Valerion
- **Age:** 16
- **Class:** Level 1 Paladin (Oath of the Crown)
- **Stats:** Str 16, Con 14, Cha 16 | **HP:** 12 | **AC:** 20"""

        # Mock LLM response for opening story generation
        character_creation_narrative = """[CHARACTER CREATION]

Welcome! I see you have a pre-defined character template for Ser Arion val Valerion, a Level 1 Paladin. Let's review and finalize your character before we begin the adventure.

**Your Character So Far:**
- **Name:** Ser Arion val Valerion
- **Class:** Level 1 Paladin
- **Race:** (Not specified yet)

**Questions to Complete Your Character:**

1. **Race:** What race is Ser Arion? (Human, Elf, Dwarf, Halfling, Dragonborn, etc.)
2. **Background:** What was Ser Arion's life before becoming a paladin? (Noble, Soldier, Acolyte, Folk Hero, etc.)
3. **Alignment:** What alignment best fits your character?
4. **Personality:** What drives your character? What are their ideals, bonds, and flaws?

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

        # Create campaign with frontend format (separate fields)
        campaign_data = {
            "title": "Frontend Format Test - My Epic Adventure",
            "character": character,  # ← Separate field, not god_mode_data!
            "setting": setting,      # ← Separate field
            "description": description,  # ← Separate field
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

        # Get campaign state to check opening story
        get_state_response = self.client.get(
            f"/api/campaigns/{campaign_id}",
            headers=self.test_headers,
        )

        self.assertEqual(get_state_response.status_code, 200)
        state_data = json.loads(get_state_response.data)

        # Extract opening story from campaign state
        story_entries = state_data.get("story", [])
        opening_story_text = ""
        for entry in story_entries:
            if isinstance(entry, dict) and entry.get("actor") == "gemini":
                opening_story_text = entry.get("text", "")
                break
        
        # Fallback: check campaign metadata
        if not opening_story_text:
            opening_story_text = state_data.get("opening_story", "") or state_data.get("initial_story", "") or ""

        # Verify opening story is NOT placeholder
        self.assertNotIn(
            "[Character Creation Mode - Story begins after character is complete]",
            opening_story_text,
            f"BUG: Opening story contains placeholder when using frontend format (separate fields). "
            f"This means character/setting/description fields were not converted to god_mode dict. "
            f"Opening story: {opening_story_text[:200]}...",
        )
        
        # Verify opening story contains character creation narrative
        self.assertIn(
            "CHARACTER CREATION",
            opening_story_text.upper(),
            f"Opening story should contain character creation narrative. Got: {opening_story_text[:200]}...",
        )
        
        # Verify it's NOT the placeholder (main check)
        # Note: Mock mode uses generic template, so we just verify it's not placeholder
        self.assertNotEqual(
            opening_story_text.strip(),
            "[Character Creation Mode - Story begins after character is complete]",
            "Opening story should NOT be placeholder text",
        )
        
        # Verify opening story is substantial (not placeholder)
        self.assertGreater(
            len(opening_story_text),
            50,
            f"Opening story should be substantial (>50 chars). Got: {opening_story_text[:200]}...",
        )

        # Verify narrative contains character creation content
        character_keywords = ["name", "race", "class", "background", "character", "review", "questions"]
        has_char_content = any(
            keyword.lower() in opening_story_text.lower() for keyword in character_keywords
        )
        self.assertTrue(
            has_char_content,
            f"Opening story should contain character creation questions/review. "
            f"Got: {opening_story_text[:200]}...",
        )


if __name__ == "__main__":
    unittest.main()
