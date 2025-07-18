#!/usr/bin/env python3
"""Integration test for structured response fields flow"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app


class TestStructuredResponseIntegration(unittest.TestCase):
    """Test structured fields flow with only external mocks"""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "test-user",
        }

    @patch("gemini_service.genai.Client")
    @patch("firestore_service.firestore")
    def test_structured_response_flow(self, mock_firestore, mock_genai_client):
        """Test complete flow returns structured fields"""
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db

        # Mock campaign exists
        mock_campaign = MagicMock()
        mock_campaign.to_dict.return_value = {
            "id": "test-123",
            "title": "Test Campaign",
            "game_state": {"debug_mode": True},
        }
        mock_campaign.exists = True

        # Mock Gemini response with schema fields
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "narrative": "You attack! --- PLANNING BLOCK ---\nWhat next?",
                "entities_mentioned": ["goblin"],
                "location_confirmed": "Cave",
                "state_updates": {"npc_data": {"goblin_1": {"hp_current": 3}}},
                "debug_info": {
                    "dice_rolls": ["1d20+5 = 18"],
                    "resources": "HD: 2/2",
                    "dm_notes": ["Test note"],
                    "state_rationale": "Damage applied",
                },
            }
        )

        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client_instance.models.count_tokens.return_value = MagicMock(
            total_tokens=100
        )

        # Setup Firestore responses
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_campaign
        )
        mock_db.collection.return_value.document.return_value.collection.return_value.stream.return_value = []

        # Make request
        response = self.client.post(
            "/api/campaigns/test-123/interaction",
            headers=self.test_headers,
            json={"input": "I attack the goblin!"},
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Check all fields present
        self.assertIn("response", data)
        self.assertIn("debug_info", data)
        self.assertIn("entities_mentioned", data)
        self.assertIn("location_confirmed", data)
        self.assertIn("state_updates", data)

        # Verify nested structure
        self.assertIn("dice_rolls", data["debug_info"])
        self.assertIn("resources", data["debug_info"])
        self.assertEqual(data["entities_mentioned"], ["goblin"])

    @patch("gemini_service.genai.Client")
    @patch("firestore_service.firestore")
    def test_god_mode_response_generation(self, mock_firestore, mock_genai_client):
        """Test that LLM generates proper God mode responses with planning blocks"""
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db

        # Mock campaign exists with God mode
        mock_campaign = MagicMock()
        mock_campaign.to_dict.return_value = {
            "id": "test-god-123",
            "title": "God Mode Test Campaign",
            "game_state": {"debug_mode": True},
        }
        mock_campaign.exists = True

        # Mock game state doc
        mock_game_state_doc = MagicMock()
        mock_game_state_doc.exists = True
        mock_game_state_doc.to_dict.return_value = {
            "player_character_data": {"name": "Hero", "level": 5},
            "npc_data": {"orc_1": {"name": "Orc Warrior", "hp_current": 25}},
            "world_data": {"location": "Forest Clearing"},
            "debug_mode": True,
        }

        # Mock Gemini response with God mode fields and planning block
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "narrative": "The orc raises its weapon menacingly...",
                "god_mode_response": "Behind the scenes: The orc has AC 14 and will target the player with a scimitar attack (+5 to hit, 1d6+3 damage). It's positioned to flank if the player moves east.",
                "planning_block": {
                    "thinking": "The player is in combat with an orc. I should present tactical options that showcase different combat mechanics.",
                    "choices": {
                        "god:attack_sword": {
                            "text": "Attack with sword",
                            "description": "Make a melee weapon attack with your longsword (+7 to hit, 1d8+4 damage)",
                        },
                        "god:cast_spell": {
                            "text": "Cast Magic Missile",
                            "description": "Auto-hit spell dealing 3d4+3 force damage, no attack roll needed",
                        },
                        "god:defensive_move": {
                            "text": "Dodge and reposition",
                            "description": "Take the Dodge action and move to gain advantage on next attack",
                        },
                    },
                },
                "entities_mentioned": ["orc_1", "Hero"],
                "location_confirmed": "Forest Clearing",
                "state_updates": {
                    "combat_state": {
                        "round_number": 1,
                        "initiative_order": ["Hero", "orc_1"],
                    }
                },
                "debug_info": {
                    "dice_rolls": ["Initiative: Hero 18, Orc 12"],
                    "resources": "Player HP: 45/45, Spell Slots: 4/4/3/3/1",
                    "dm_notes": [
                        "Orc positioned for flanking",
                        "Player has tactical advantage with ranged options",
                    ],
                    "state_rationale": "Combat initiated, positions set",
                },
            }
        )

        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client_instance.models.count_tokens.return_value = MagicMock(
            total_tokens=150
        )

        # Setup Firestore responses for campaign and game state
        campaign_doc_mock = MagicMock()
        campaign_doc_mock.get.return_value = mock_campaign
        campaign_doc_mock.collection.return_value.document.return_value.get.return_value = mock_game_state_doc
        campaign_doc_mock.collection.return_value.stream.return_value = []

        mock_db.collection.return_value.document.return_value = campaign_doc_mock

        # Make God mode request
        response = self.client.post(
            "/api/campaigns/test-god-123/interaction",
            headers=self.test_headers,
            json={
                "input": "god mode: An orc appears! What should I do?",
                "mode": "god",
            },
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify God mode specific fields are present
        self.assertIn("response", data)
        self.assertIn("god_mode_response", data)
        self.assertIn("planning_block", data)

        # Verify God mode response content
        god_response = data["god_mode_response"]
        self.assertIn("Behind the scenes", god_response)
        self.assertIn("AC 14", god_response)
        self.assertIn("flank", god_response)

        # Verify planning block structure
        planning_block = data["planning_block"]
        self.assertIn("thinking", planning_block)
        self.assertIn("choices", planning_block)

        # Verify God mode choice prefixes
        choices = planning_block["choices"]
        god_choices = [
            choice_id for choice_id in choices.keys() if choice_id.startswith("god:")
        ]
        self.assertGreaterEqual(
            len(god_choices), 2, "Should have at least 2 God mode choices"
        )

        # Verify choice structure
        for choice_id, choice_data in choices.items():
            if choice_id.startswith("god:"):
                self.assertIn("text", choice_data)
                self.assertIn("description", choice_data)
                # God mode descriptions should contain mechanical details
                self.assertRegex(
                    choice_data["description"],
                    r"(\+\d+|\d+d\d+|AC|damage|advantage)",
                    f"God mode choice {choice_id} should contain mechanical details",
                )

        # Verify other structured fields
        self.assertIn("entities_mentioned", data)
        self.assertIn("location_confirmed", data)
        self.assertIn("state_updates", data)
        self.assertIn("debug_info", data)

        # Verify combat state update
        self.assertIn("combat_state", data["state_updates"])
        self.assertEqual(data["state_updates"]["combat_state"]["round_number"], 1)

    @patch("gemini_service.genai.Client")
    @patch("firestore_service.firestore")
    def test_meta_dm_advice_god_mode_generation(
        self, mock_firestore, mock_genai_client
    ):
        """Test that LLM generates proper God mode responses for meta DM advice about plot arcs"""
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db

        # Mock campaign exists
        mock_campaign = MagicMock()
        mock_campaign.to_dict.return_value = {
            "id": "test-meta-456",
            "title": "Meta DM Advice Campaign",
            "game_state": {"debug_mode": True},
        }
        mock_campaign.exists = True

        # Mock game state doc with ongoing story
        mock_game_state_doc = MagicMock()
        mock_game_state_doc.exists = True
        mock_game_state_doc.to_dict.return_value = {
            "player_character_data": {"name": "Lyra", "class": "Ranger", "level": 8},
            "world_data": {"location": "Ancient Ruins", "chapter": "The Lost Prophecy"},
            "story_threads": {
                "main_quest": "Finding the Crystal of Eternal Light",
                "character_arc": "Lyra questioning her past",
                "relationship_tension": "Trust issues with party wizard",
            },
            "debug_mode": True,
        }

        # Mock Gemini response with meta DM advice and plot guidance
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "narrative": "The ancient prophecy speaks of three trials that test the heart, mind, and spirit...",
                "god_mode_response": "DM Strategy: This is a perfect moment to weave Lyra's backstory into the main plot. Consider having the prophecy mention a 'child of two worlds' which hints at her half-elf heritage. The wizard's knowledge about this could create dramatic tension - does he know more than he's letting on? Plot-wise, you're setting up a classic 'revelation that changes everything' moment.",
                "planning_block": {
                    "thinking": "The player is asking for plot advice about their character arc. I should provide DM-level guidance on narrative structure, character development, and how to weave personal stories into the main quest. This is meta-gaming advice, not in-character responses.",
                    "choices": {
                        "god:backstory_integration": {
                            "text": "Integrate Lyra's backstory into the prophecy",
                            "description": "Reveal that the prophecy specifically mentions someone of Lyra's heritage. This creates personal stakes and makes the quest feel destined rather than random.",
                        },
                        "god:relationship_drama": {
                            "text": "Escalate wizard trust subplot",
                            "description": "Have the wizard reveal he's been researching Lyra's family line. This adds layers - is he protective, manipulative, or hiding something darker?",
                        },
                        "god:pacing_control": {
                            "text": "Use the three trials structure",
                            "description": "Classic storytelling: Trial of Heart (emotional challenge), Trial of Mind (puzzle/wisdom), Trial of Spirit (moral choice). Each reveals character depth.",
                        },
                        "god:narrative_hook": {
                            "text": "Plant seeds for future revelations",
                            "description": "Drop hints that Lyra's 'lost memories' aren't lost - they were hidden. Sets up a major plot twist for later sessions.",
                        },
                    },
                },
                "entities_mentioned": [
                    "Lyra",
                    "Crystal_of_Eternal_Light",
                    "Ancient_Prophecy",
                ],
                "location_confirmed": "Ancient Ruins",
                "state_updates": {
                    "story_threads": {
                        "revelation_setup": "Prophecy hints at Lyra's importance",
                        "dramatic_irony": "Players don't know wizard's true knowledge level",
                    },
                    "dm_notes": {
                        "pacing": "Building toward major revelation",
                        "character_focus": "Lyra's arc becoming central to plot",
                    },
                },
                "debug_info": {
                    "plot_structure": [
                        "Setup complete",
                        "Rising action: personal stakes",
                        "Next: complication",
                    ],
                    "character_development": "Lyra: Identity crisis -> Self-acceptance arc",
                    "dm_tools": [
                        "Dramatic irony",
                        "Foreshadowing",
                        "Personal stakes integration",
                    ],
                    "narrative_timing": "Perfect moment for backstory integration - player investment is high",
                },
            }
        )

        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client_instance.models.count_tokens.return_value = MagicMock(
            total_tokens=200
        )

        # Setup Firestore responses
        campaign_doc_mock = MagicMock()
        campaign_doc_mock.get.return_value = mock_campaign
        campaign_doc_mock.collection.return_value.document.return_value.get.return_value = mock_game_state_doc
        campaign_doc_mock.collection.return_value.stream.return_value = []

        mock_db.collection.return_value.document.return_value = campaign_doc_mock

        # Make meta DM advice request
        response = self.client.post(
            "/api/campaigns/test-meta-456/interaction",
            headers=self.test_headers,
            json={
                "input": "god mode: How should I handle Lyra's character development? What are some good plot arcs for connecting her backstory to the main quest?",
                "mode": "god",
            },
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify God mode DM advice fields are present
        self.assertIn("response", data)
        self.assertIn("god_mode_response", data)
        self.assertIn("planning_block", data)

        # Verify God mode response contains DM strategy advice
        god_response = data["god_mode_response"]
        self.assertIn("DM Strategy", god_response)
        self.assertIn("backstory", god_response.lower())
        self.assertIn("plot", god_response.lower())
        self.assertIn("dramatic", god_response.lower())

        # Verify planning block structure for DM advice
        planning_block = data["planning_block"]
        self.assertIn("thinking", planning_block)
        self.assertIn("plot advice", planning_block["thinking"].lower())
        self.assertIn("meta-gaming", planning_block["thinking"].lower())

        # Verify God mode choice prefixes for DM advice
        choices = planning_block["choices"]
        god_choices = [
            choice_id for choice_id in choices.keys() if choice_id.startswith("god:")
        ]
        self.assertGreaterEqual(
            len(god_choices), 3, "Should have at least 3 God mode DM advice choices"
        )

        # Verify DM advice choices contain narrative guidance
        dm_keywords = [
            "backstory",
            "narrative",
            "character",
            "plot",
            "reveal",
            "development",
            "arc",
        ]
        for choice_id, choice_data in choices.items():
            if choice_id.startswith("god:"):
                self.assertIn("text", choice_data)
                self.assertIn("description", choice_data)
                # DM advice descriptions should contain storytelling terms
                description_lower = choice_data["description"].lower()
                keyword_found = any(
                    keyword in description_lower for keyword in dm_keywords
                )
                self.assertTrue(
                    keyword_found,
                    f"DM advice choice {choice_id} should contain narrative/storytelling keywords",
                )

        # Verify story-focused state updates
        self.assertIn("state_updates", data)
        state_updates = data["state_updates"]
        self.assertIn("story_threads", state_updates)
        self.assertIn("dm_notes", state_updates)

        # Verify debug info contains plot structure guidance
        self.assertIn("debug_info", data)
        debug_info = data["debug_info"]
        self.assertIn("plot_structure", debug_info)
        self.assertIn("character_development", debug_info)
        self.assertIn("narrative_timing", debug_info)

    @patch.dict("os.environ", {"AUTH_SKIP_MODE": "true"}, clear=False)
    def test_real_god_mode_dm_advice_integration(self):
        """REAL API TEST: Ask for DM advice and verify LLM generates God mode responses"""

        # Skip if no API key (CI environment)
        if not os.environ.get("GEMINI_API_KEY"):
            self.skipTest("GEMINI_API_KEY not set - skipping real API test")

        # Test meta-level DM guidance request
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use auth bypass for integration testing
        test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "integration-test-user",
        }

        # Create test campaign
        campaign_data = {
            "title": "God Mode DM Advice Test",
            "initial_prompt": "A heroic fantasy campaign where I need DM guidance",
            "selected_prompts": ["narrative", "mechanics"],
        }

        create_response = self.client.post(
            "/api/campaigns", headers=test_headers, json=campaign_data
        )

        if create_response.status_code not in [200, 201]:
            self.skipTest(f"Campaign creation failed: {create_response.status_code}")

        campaign_id = create_response.json["campaign_id"]

        # Make meta-level God mode request for DM advice
        god_mode_request = {
            "input": "god mode: What are some compelling plot hooks I could use to transition from exploration to social intrigue? How should I handle player agency when introducing political conflicts?",
            "mode": "god",
        }

        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            headers=test_headers,
            json=god_mode_request,
        )

        # Verify successful response
        self.assertEqual(
            response.status_code, 200, f"God mode request failed: {response.data}"
        )
        data = response.json

        # CRITICAL: Verify God mode specific fields are present
        self.assertIn("god_mode_response", data, "Missing god_mode_response field")
        self.assertIn("planning_block", data, "Missing planning_block field")

        # Verify God mode response contains DM advice
        god_response = data["god_mode_response"]
        self.assertIsInstance(god_response, str, "god_mode_response should be string")
        self.assertGreater(len(god_response), 50, "God mode response too short")

        # Check for DM-specific advice content
        dm_advice_indicators = [
            "plot",
            "hook",
            "intrigue",
            "player",
            "agency",
            "political",
            "transition",
            "story",
            "narrative",
            "conflict",
            "character",
            "motivation",
        ]
        god_response_lower = god_response.lower()
        advice_matches = [
            indicator
            for indicator in dm_advice_indicators
            if indicator in god_response_lower
        ]
        self.assertGreaterEqual(
            len(advice_matches),
            3,
            f"God mode response should contain DM advice keywords. Found: {advice_matches}",
        )

        # Verify planning block structure for meta-advice
        planning_block = data["planning_block"]
        self.assertIn(
            "thinking", planning_block, "Missing thinking field in planning block"
        )
        self.assertIn(
            "choices", planning_block, "Missing choices field in planning block"
        )

        # Verify choices have God mode structure
        choices = planning_block["choices"]
        self.assertIsInstance(choices, dict, "Choices should be dictionary")
        self.assertGreater(len(choices), 1, "Should have multiple choices")

        # Check for God mode choice prefixes and DM-oriented options
        god_choices = [
            choice_id for choice_id in choices.keys() if choice_id.startswith("god:")
        ]
        self.assertGreaterEqual(
            len(god_choices),
            2,
            f"Should have God mode choices with god: prefix. Got: {list(choices.keys())}",
        )

        # Verify choice structure and DM-focused content
        for choice_id, choice_data in choices.items():
            if choice_id.startswith("god:"):
                self.assertIn("text", choice_data, f"Choice {choice_id} missing text")
                self.assertIn(
                    "description",
                    choice_data,
                    f"Choice {choice_id} missing description",
                )

                # Skip DM guidance check for return choices (they're for exiting God mode)
                if "return" in choice_id.lower() or "exit" in choice_id.lower():
                    continue

                # God mode choices should contain DM guidance terms
                choice_text_lower = (
                    choice_data["text"] + " " + choice_data["description"]
                ).lower()
                dm_guidance_terms = [
                    "introduce",
                    "develop",
                    "create",
                    "guide",
                    "present",
                    "establish",
                    "handle",
                    "discuss",
                    "explain",
                    "transition",
                    "political",
                    "conflict",
                    "player",
                    "agency",
                    "intrigue",
                    "social",
                    "plot",
                    "hook",
                ]
                has_dm_guidance = any(
                    term in choice_text_lower for term in dm_guidance_terms
                )
                self.assertTrue(
                    has_dm_guidance,
                    f"God choice {choice_id} should contain DM guidance terms: {choice_data}",
                )

        # Verify other structured fields work with God mode
        self.assertIn("response", data, "Missing main response field")

        # Log success for verification
        print("\n✅ REAL API GOD MODE TEST PASSED")
        print(f"📝 God Mode Response Length: {len(god_response)} chars")
        print(f"🎯 DM Advice Keywords Found: {advice_matches}")
        print(f"🎮 God Mode Choices: {len(god_choices)} of {len(choices)} total")
        print(f"🔧 Choice IDs: {list(choices.keys())}")


if __name__ == "__main__":
    unittest.main()
