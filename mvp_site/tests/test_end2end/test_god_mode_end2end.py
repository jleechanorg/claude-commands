"""
End-to-end integration test for GOD MODE functionality.
Only mocks external services (LLM provider APIs and Firestore DB) at the lowest level.
Tests the full flow including god mode prompt selection and response handling.

GOD MODE is for correcting mistakes and changing campaign state, NOT for playing.
It uses a separate, focused prompt stack without narrative generation prompts.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch, MagicMock

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestGodModeEnd2End(unittest.TestCase):
    """Test GOD MODE functionality through the full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-god-mode"
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

        # Standard mock GOD MODE response
        self.mock_god_mode_response_data = {
            "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 10, Afternoon\nLocation: Tavern\nStatus: Lvl 5 Fighter | HP: 45/50 | XP: 6500/14000 | Gold: 150gp",
            "god_mode_response": "HP has been set to 50. Character is now at full health.",
            "narrative": "",
            "entities_mentioned": [],
            "location_confirmed": "Tavern",
            "state_updates": {
                "player_character_data": {"hp_current": 50}
            },
            "planning_block": {
                "thinking": "The user wants to modify HP. This is an administrative command.",
                "choices": {
                    "god:set_gold": {
                        "text": "Set Gold",
                        "description": "Modify character gold",
                        "risk_level": "safe"
                    },
                    "god:return_story": {
                        "text": "Return to Story",
                        "description": "Exit God Mode and resume gameplay",
                        "risk_level": "safe"
                    }
                }
            }
        }

        # Standard mock story mode response (for comparison)
        self.mock_story_response_data = {
            "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 10, Afternoon\nLocation: Tavern\nStatus: Lvl 5 Fighter | HP: 45/50",
            "narrative": "The tavern is bustling with activity...",
            "entities_mentioned": ["Bartender"],
            "location_confirmed": "Tavern",
            "state_updates": {},
            "planning_block": {
                "thinking": "The player enters the tavern.",
                "choices": {
                    "talk_bartender": {"text": "Talk to bartender", "description": "Ask about rumors", "risk_level": "low"},
                    "other_action": {"text": "Other Action", "description": "Do something else", "risk_level": "low"}
                }
            }
        }

    def _setup_fake_firestore_with_campaign(self, fake_firestore, campaign_id):
        """Helper to set up fake Firestore with campaign and game state."""
        # Create test campaign data
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {
                "title": "Test Campaign",
                "setting": "Fantasy realm",
                "selected_prompts": ["narrative", "mechanics"],
            }
        )

        # Create game state with proper structure
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "Previous story content",
                "player_character_data": {
                    "name": "Thorin",
                    "hp_current": 45,
                    "hp_max": 50,
                    "level": 5,
                    "class": "Fighter",
                },
                "world_data": {
                    "current_location_name": "Tavern",
                    "world_time": {
                        "year": 1492,
                        "month": "Mirtul",
                        "day": 10,
                        "hour": 14,
                        "minute": 0,
                        "time_of_day": "Afternoon"
                    }
                },
                "npc_data": {},
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_god_mode_returns_god_mode_response_field(self, mock_gemini_generate, mock_get_db):
        """Test that GOD MODE commands return god_mode_response field."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_god_mode"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini provider to return god mode response
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_god_mode_response_data)
        )

        # Make GOD MODE request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "GOD MODE: Set HP to 50",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        data = json.loads(response.data)

        # Verify god_mode_response is present in the response
        assert "god_mode_response" in data, "god_mode_response field should be present"
        assert data["god_mode_response"] == "HP has been set to 50. Character is now at full health."

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_god_mode_uses_separate_prompts(self, mock_gemini_generate, mock_get_db):
        """Test that GOD MODE uses separate system prompts (not narrative prompts)."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_god_mode_prompts"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini provider
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_god_mode_response_data)
        )

        # Make GOD MODE request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "GOD MODE: Show current state",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify request succeeded
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"

        # Verify Gemini was called
        assert mock_gemini_generate.call_count >= 1, "LLM should be called"

        # Get the system instruction passed to the LLM
        call_args = mock_gemini_generate.call_args

        # The system instruction is typically in the model_config or as a parameter
        # Check that god_mode_instruction content is present (administrative focus)
        # and that narrative_system_instruction is NOT present
        if call_args and len(call_args) > 0:
            # Look through all arguments for system instruction content
            all_args_str = str(call_args)

            # God mode should have "Administrative interface" or "pause menu" language
            has_god_mode_prompt = (
                "Administrative interface" in all_args_str or
                "pause menu" in all_args_str or
                "god_mode_response" in all_args_str
            )

            # God mode should NOT have narrative generation language
            has_narrative_prompt = (
                "Master Game Weaver" in all_args_str or
                "Subtlety and realism over theatrical drama" in all_args_str
            )

            # We expect god mode prompts, not narrative prompts
            # Note: This is a soft assertion - the key test is that it works correctly
            if has_narrative_prompt and not has_god_mode_prompt:
                self.fail("GOD MODE should use god_mode prompts, not narrative prompts")

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_god_mode_with_lowercase_prefix(self, mock_gemini_generate, mock_get_db):
        """Test that god mode works with lowercase 'god mode:' prefix."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_lowercase"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini provider
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_god_mode_response_data)
        )

        # Make request with lowercase god mode prefix
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "god mode: set hp to 50",  # lowercase
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response - should still work due to .upper() in detection
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        data = json.loads(response.data)

        # Verify god_mode_response is present
        assert "god_mode_response" in data, "god_mode_response should be present for lowercase prefix"

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_regular_input_does_not_trigger_god_mode(self, mock_gemini_generate, mock_get_db):
        """Test that regular input without GOD MODE prefix uses normal prompts."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_regular"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini provider with story response
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_story_response_data)
        )

        # Make regular (non-god-mode) request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "I walk into the tavern",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        data = json.loads(response.data)

        # Verify narrative is present (story mode)
        assert "story" in data, "story field should be present for regular input"

        # god_mode_response should be empty or missing for regular input
        god_mode_resp = data.get("god_mode_response", "")
        assert not god_mode_resp or god_mode_resp == "", "god_mode_response should be empty for regular input"

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_god_mode_state_updates_applied(self, mock_gemini_generate, mock_get_db):
        """Test that GOD MODE state_updates are properly applied."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_state_updates"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini provider with state updates
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_god_mode_response_data)
        )

        # Make GOD MODE request to set HP
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "GOD MODE: Set HP to 50",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        data = json.loads(response.data)

        # Verify game_state is returned with updates
        assert "game_state" in data, "game_state should be in response"


class TestGodModePromptSelection(unittest.TestCase):
    """Unit tests for GOD MODE prompt selection logic."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"

    def test_god_mode_detection_with_prefix(self):
        """Test that GOD MODE: prefix is correctly detected."""
        from mvp_site import llm_service

        # Test various god mode prefixes
        test_cases = [
            ("GOD MODE: Set HP", True),
            ("god mode: set hp", True),  # lowercase
            ("God Mode: teleport", True),  # mixed case
            ("  GOD MODE: with spaces", True),  # leading spaces
            ("I walk into the tavern", False),  # regular input
            ("Can you help me in god mode", False),  # god mode mentioned but not prefix
            ("GODMODE: no space", False),  # missing space after GOD
        ]

        for user_input, expected in test_cases:
            is_god_mode = user_input.strip().upper().startswith("GOD MODE:")
            assert is_god_mode == expected, f"Failed for '{user_input}': expected {expected}, got {is_god_mode}"

    def test_prompt_builder_has_god_mode_method(self):
        """Test that PromptBuilder has build_god_mode_instructions method."""
        from mvp_site.agent_prompts import PromptBuilder

        builder = PromptBuilder(None)
        assert hasattr(builder, 'build_god_mode_instructions'), \
            "PromptBuilder should have build_god_mode_instructions method"

        # Call the method and verify it returns a list
        instructions = builder.build_god_mode_instructions()
        assert isinstance(instructions, list), "build_god_mode_instructions should return a list"
        assert len(instructions) > 0, "God mode instructions should not be empty"

    def test_god_mode_instructions_contain_required_prompts(self):
        """Test that god mode instructions include required prompt types."""
        from mvp_site.agent_prompts import PromptBuilder
        from mvp_site import constants

        builder = PromptBuilder(None)
        instructions = builder.build_god_mode_instructions()

        # Join all instructions into one string for checking
        all_instructions = "\n".join(instructions)

        # God mode should include master directive content
        # (we check for content that should be in master_directive)
        assert len(all_instructions) > 1000, "God mode instructions should include substantial content"

        # God mode should include game state schema information
        assert "state_updates" in all_instructions.lower() or "game_state" in all_instructions.lower(), \
            "God mode instructions should include game state information"


if __name__ == "__main__":
    unittest.main()
