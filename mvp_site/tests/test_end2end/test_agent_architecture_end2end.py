"""
End-to-end integration test for Agent Architecture.

Tests the agent-based mode handling (StoryModeAgent vs GodModeAgent) through
the full application stack. Verifies that:
1. Agent selection works correctly based on user input
2. Each agent builds the correct system instructions
3. Mode detection (GOD MODE: prefix) works end-to-end
4. Both agents integrate correctly with the LLM service

This test suite complements test_god_mode_end2end.py by focusing specifically
on the agent architecture rather than god mode functionality.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from mvp_site import main, constants
from mvp_site.agents import (
    BaseAgent,
    StoryModeAgent,
    GodModeAgent,
    get_agent_for_input,
)
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestAgentArchitectureEnd2End(unittest.TestCase):
    """Test agent architecture through the full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-agent-e2e"
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

        # Standard mock story mode response
        self.mock_story_response = {
            "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 10\nLocation: Forest",
            "narrative": "You walk through the dense forest, leaves crunching under your feet...",
            "entities_mentioned": ["Forest Spirit"],
            "location_confirmed": "Enchanted Forest",
            "state_updates": {},
            "planning_block": {
                "thinking": "The player is exploring the forest.",
                "choices": {
                    "continue": {"text": "Continue", "description": "Keep walking", "risk_level": "low"},
                    "rest": {"text": "Rest", "description": "Take a break", "risk_level": "safe"}
                }
            }
        }

        # Standard mock god mode response
        self.mock_god_mode_response = {
            "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 10\nLocation: Forest",
            "god_mode_response": "Level has been set to 10. Character stats updated accordingly.",
            "narrative": "",
            "entities_mentioned": [],
            "location_confirmed": "Enchanted Forest",
            "state_updates": {
                "player_character_data": {"level": 10}
            },
            "planning_block": {
                "thinking": "Administrative command to modify character level.",
                "choices": {}
            }
        }

    def _setup_fake_firestore_with_campaign(self, fake_firestore, campaign_id):
        """Helper to set up fake Firestore with campaign and game state."""
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {
                "title": "Agent Test Campaign",
                "setting": "Fantasy realm",
                "selected_prompts": ["narrative", "mechanics"],
            }
        )

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "Previous story content",
                "player_character_data": {
                    "name": "TestHero",
                    "hp_current": 30,
                    "hp_max": 30,
                    "level": 5,
                    "class": "Wizard",
                },
                "world_data": {
                    "current_location_name": "Enchanted Forest",
                    "world_time": {
                        "year": 1492,
                        "month": "Mirtul",
                        "day": 10,
                        "hour": 10,
                        "minute": 0,
                    }
                },
                "npc_data": {},
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
            }
        )

    # =========================================================================
    # Agent Selection Tests
    # =========================================================================

    def test_agent_selection_story_mode(self):
        """Test that StoryModeAgent is selected for regular inputs."""
        test_inputs = [
            "I attack the goblin!",
            "Search the room for traps",
            "Talk to the merchant",
            "Cast fireball",
            "think about my options",
        ]

        for user_input in test_inputs:
            agent = get_agent_for_input(user_input)
            self.assertIsInstance(
                agent, StoryModeAgent,
                f"Expected StoryModeAgent for input: {user_input}"
            )
            self.assertEqual(agent.MODE, constants.MODE_CHARACTER)

    def test_agent_selection_god_mode(self):
        """Test that GodModeAgent is selected for GOD MODE inputs."""
        test_inputs = [
            "GOD MODE: Set HP to 50",
            "god mode: change my level",
            "GOD MODE: teleport me to town",
            "  GOD MODE: fix my inventory",
        ]

        for user_input in test_inputs:
            agent = get_agent_for_input(user_input)
            self.assertIsInstance(
                agent, GodModeAgent,
                f"Expected GodModeAgent for input: {user_input}"
            )
            self.assertEqual(agent.MODE, constants.MODE_GOD)

    def test_agent_selection_edge_cases(self):
        """Test edge cases in agent selection."""
        # These should NOT trigger god mode
        edge_cases = [
            ("god", StoryModeAgent),  # Just the word
            ("tell me about god mode", StoryModeAgent),  # Contains but doesn't start
            ("GODMODE: test", StoryModeAgent),  # Missing space
            ("GOD_MODE: test", StoryModeAgent),  # Wrong format
            ("The god mode is powerful", StoryModeAgent),  # In middle of text
        ]

        for user_input, expected_type in edge_cases:
            agent = get_agent_for_input(user_input)
            self.assertIsInstance(
                agent, expected_type,
                f"Expected {expected_type.__name__} for input: {user_input}"
            )

    # =========================================================================
    # Agent Prompt Set Tests
    # =========================================================================

    def test_story_mode_agent_has_correct_prompts(self):
        """Test that StoryModeAgent has the correct prompt set."""
        agent = StoryModeAgent()

        # Required prompts
        self.assertIn(constants.PROMPT_TYPE_MASTER_DIRECTIVE, agent.REQUIRED_PROMPTS)
        self.assertIn(constants.PROMPT_TYPE_GAME_STATE, agent.REQUIRED_PROMPTS)
        self.assertIn(constants.PROMPT_TYPE_DND_SRD, agent.REQUIRED_PROMPTS)

        # Optional prompts
        self.assertIn(constants.PROMPT_TYPE_NARRATIVE, agent.OPTIONAL_PROMPTS)
        self.assertIn(constants.PROMPT_TYPE_MECHANICS, agent.OPTIONAL_PROMPTS)

        # Should NOT have god mode prompt
        all_prompts = agent.get_all_prompts()
        self.assertNotIn(constants.PROMPT_TYPE_GOD_MODE, all_prompts)

    def test_god_mode_agent_has_correct_prompts(self):
        """Test that GodModeAgent has the correct prompt set."""
        agent = GodModeAgent()

        # Required prompts
        self.assertIn(constants.PROMPT_TYPE_MASTER_DIRECTIVE, agent.REQUIRED_PROMPTS)
        self.assertIn(constants.PROMPT_TYPE_GOD_MODE, agent.REQUIRED_PROMPTS)
        self.assertIn(constants.PROMPT_TYPE_GAME_STATE, agent.REQUIRED_PROMPTS)
        self.assertIn(constants.PROMPT_TYPE_DND_SRD, agent.REQUIRED_PROMPTS)
        self.assertIn(constants.PROMPT_TYPE_MECHANICS, agent.REQUIRED_PROMPTS)

        # Should NOT have narrative prompts
        all_prompts = agent.get_all_prompts()
        self.assertNotIn(constants.PROMPT_TYPE_NARRATIVE, all_prompts)
        self.assertNotIn(constants.PROMPT_TYPE_CHARACTER_TEMPLATE, all_prompts)

    # =========================================================================
    # End-to-End Flow Tests
    # =========================================================================

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
    def test_story_mode_flow_end2end(self, mock_gemini_generate, mock_get_db):
        """Test that story mode works end-to-end through agent architecture."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_story_agent_e2e"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_story_response)
        )

        # Make story mode request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "I explore the forest deeper",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200, f"Got: {response.data}")
        data = json.loads(response.data)

        # Verify story mode response characteristics
        self.assertIn("narrative", data)
        self.assertGreater(
            len(data.get("narrative", "")),
            0,
            "Expected non-empty narrative in story mode response",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
    def test_god_mode_flow_end2end(self, mock_gemini_generate, mock_get_db):
        """Test that god mode works end-to-end through agent architecture."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_god_agent_e2e"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_god_mode_response)
        )

        # Make god mode request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "GOD MODE: Set my level to 10",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200, f"Got: {response.data}")
        data = json.loads(response.data)

        # Verify god mode response characteristics
        self.assertIn("god_mode_response", data)
        self.assertEqual(
            data["god_mode_response"],
            "Level has been set to 10. Character stats updated accordingly."
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
    def test_mode_switching_in_same_session(self, mock_gemini_generate, mock_get_db):
        """Test switching between story mode and god mode in the same session."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_mode_switch_e2e"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # First request: Story mode
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_story_response)
        )

        response1 = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "I look around",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(response1.status_code, 200)
        data1 = json.loads(response1.data)
        self.assertIn("narrative", data1)
        self.assertNotIn("god_mode_response", data1)

        # Second request: God mode
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_god_mode_response)
        )

        response2 = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "GOD MODE: Set level to 10",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.data)
        self.assertIn("god_mode_response", data2)

        # Third request: Back to story mode
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_story_response)
        )

        response3 = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "Continue exploring",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(response3.status_code, 200)
        data3 = json.loads(response3.data)
        self.assertIn("narrative", data3)

    # =========================================================================
    # Agent Instruction Building Tests
    # =========================================================================

    @patch("mvp_site.agent_prompts._load_instruction_file")
    def test_story_mode_agent_builds_instructions(self, mock_load):
        """Test that StoryModeAgent builds correct system instructions."""
        mock_load.return_value = "Test instruction content"

        agent = StoryModeAgent()
        instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE, constants.PROMPT_TYPE_MECHANICS],
            use_default_world=False,
            include_continuation_reminder=True,
        )

        self.assertIsInstance(instructions, str)
        self.assertGreater(
            len(instructions),
            0,
            "StoryModeAgent should build non-empty instructions",
        )

    @patch("mvp_site.agent_prompts._load_instruction_file")
    def test_god_mode_agent_builds_instructions(self, mock_load):
        """Test that GodModeAgent builds correct system instructions."""
        mock_load.return_value = "Test instruction content"

        agent = GodModeAgent()
        instructions = agent.build_system_instructions()

        self.assertIsInstance(instructions, str)
        self.assertGreater(
            len(instructions),
            0,
            "GodModeAgent should build non-empty instructions",
        )

    @patch("mvp_site.agent_prompts._load_instruction_file")
    def test_god_mode_ignores_selected_prompts(self, mock_load):
        """Test that GodModeAgent ignores selected_prompts parameter."""
        mock_load.return_value = "Test instruction content"

        agent = GodModeAgent()

        # Both calls should work without error
        instructions1 = agent.build_system_instructions(selected_prompts=None)
        instructions2 = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE]
        )

        self.assertIsInstance(instructions1, str)
        self.assertIsInstance(instructions2, str)


if __name__ == "__main__":
    unittest.main()
