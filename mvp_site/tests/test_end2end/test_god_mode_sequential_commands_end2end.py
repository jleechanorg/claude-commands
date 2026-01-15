"""
End-to-end integration test for GOD MODE sequential commands bug.

Tests that when two god mode commands are sent consecutively, both commands
are properly processed and responded to, not just the first one.

This test specifically targets the caching bug where story_context is cached
and reused for the second command, causing it to respond to the first command
instead of the second one.

Bug: When campaign_data is cached (not None), story_context is reused from
the first request, causing the LLM to see stale context and respond to the
wrong command.
"""

from __future__ import annotations

import json
import os

# Set this before importing mvp_site modules to bypass clock skew validation
os.environ["TESTING_AUTH_BYPASS"] = "true"

import unittest
from unittest.mock import patch

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestGodModeSequentialCommandsEnd2End(unittest.TestCase):
    """Test that sequential GOD MODE commands are both processed correctly."""

    def setUp(self):
        """Set up test client."""
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")
        # Disable MOCK_SERVICES_MODE to allow patching generate_json_mode_content
        os.environ["MOCK_SERVICES_MODE"] = "false"

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-god-mode-sequential"
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

    def _setup_fake_firestore_with_campaign(self, fake_firestore, campaign_id):
        """Helper to set up fake Firestore with campaign and game state."""
        # Create test campaign data
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {
                "title": "Test Campaign Sequential",
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
                    "gold": 100,
                },
                "world_data": {
                    "current_location_name": "Tavern",
                    "world_time": {
                        "year": 1492,
                        "month": "Mirtul",
                        "day": 10,
                        "hour": 14,
                        "minute": 0,
                        "time_of_day": "Afternoon",
                    },
                },
                "npc_data": {},
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_two_god_mode_commands_both_respected(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that two consecutive god mode commands are both processed correctly.
        
        This test verifies the fix for the caching bug where the second command
        would respond to the first command instead of the second one.
        
        Steps:
        1. Send first god mode command: "GOD MODE: Set HP to 50"
        2. Send second god mode command: "GOD MODE: Set gold to 200"
        3. Verify both commands are processed and responded to correctly
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_sequential_commands"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Track calls to verify both commands are processed
        call_count = {"count": 0}

        def mock_gemini_side_effect(*args, **kwargs):
            """Mock Gemini to return different responses based on call count."""
            call_count["count"] += 1
            
            if call_count["count"] == 1:
                # First command: Set HP to 50
                return FakeLLMResponse(
                    json.dumps(
                        {
                            "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 10, Afternoon\nLocation: Tavern\nStatus: Lvl 5 Fighter | HP: 50/50 | XP: 6500/14000 | Gold: 100gp",
                            "god_mode_response": "HP has been set to 50. Character is now at full health.",
                            "narrative": "",
                            "entities_mentioned": [],
                            "location_confirmed": "Tavern",
                            "state_updates": {"player_character_data": {"hp_current": 50}},
                            "planning_block": {
                                "thinking": "The user wants to modify HP. This is an administrative command.",
                                "choices": {
                                    "god:return_story": {
                                        "text": "Return to Story",
                                        "description": "Exit God Mode and resume gameplay",
                                        "risk_level": "safe",
                                    },
                                },
                            },
                        }
                    )
                )
            elif call_count["count"] == 2:
                # Second command: Set gold to 200
                return FakeLLMResponse(
                    json.dumps(
                        {
                            "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 10, Afternoon\nLocation: Tavern\nStatus: Lvl 5 Fighter | HP: 50/50 | XP: 6500/14000 | Gold: 200gp",
                            "god_mode_response": "Gold has been set to 200. Character now has 200 gold pieces.",
                            "narrative": "",
                            "entities_mentioned": [],
                            "location_confirmed": "Tavern",
                            "state_updates": {"player_character_data": {"gold": 200}},
                            "planning_block": {
                                "thinking": "The user wants to modify gold. This is an administrative command.",
                                "choices": {
                                    "god:return_story": {
                                        "text": "Return to Story",
                                        "description": "Exit God Mode and resume gameplay",
                                        "risk_level": "safe",
                                    },
                                },
                            },
                        }
                    )
                )
            else:
                # Fallback for any additional calls
                return FakeLLMResponse(
                    json.dumps(
                        {
                            "god_mode_response": f"Unexpected call #{call_count['count']}",
                            "narrative": "",
                            "state_updates": {},
                        }
                    )
                )

        mock_gemini_generate.side_effect = mock_gemini_side_effect

        # FIRST GOD MODE COMMAND: Set HP to 50
        response1 = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "GOD MODE: Set HP to 50", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify first response
        assert (
            response1.status_code == 200
        ), f"First command failed with {response1.status_code}: {response1.data}"
        data1 = json.loads(response1.data)

        # Verify first command was processed correctly
        assert "god_mode_response" in data1, "First command should have god_mode_response"
        assert (
            "HP" in data1["god_mode_response"] or "50" in data1["god_mode_response"]
        ), f"First command should mention HP/50. Got: {data1.get('god_mode_response')}"

        # Verify HP was updated in state
        if "game_state" in data1:
            hp = data1["game_state"].get("player_character_data", {}).get("hp_current")
            assert hp == 50, f"HP should be 50 after first command, got {hp}"

        # SECOND GOD MODE COMMAND: Set gold to 200
        # This is where the bug would manifest - if story_context is cached,
        # the LLM might respond to the first command instead of this one
        response2 = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps(
                {"input": "GOD MODE: Set gold to 200", "mode": "character"}
            ),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify second response
        assert (
            response2.status_code == 200
        ), f"Second command failed with {response2.status_code}: {response2.data}"
        data2 = json.loads(response2.data)

        # CRITICAL TEST: Verify second command was processed correctly
        assert "god_mode_response" in data2, "Second command should have god_mode_response"
        
        # The second response should mention gold/200, NOT HP/50
        god_mode_resp2 = data2.get("god_mode_response", "").lower()
        assert (
            "gold" in god_mode_resp2 or "200" in god_mode_resp2
        ), (
            f"Second command should mention gold/200, not HP. "
            f"Got: {data2.get('god_mode_response')}"
        )
        
        # Verify response primarily addresses gold, not HP
        # (The mock is controlled, but this guards against future regression)
        assert "gold" in god_mode_resp2, (
            f"Second command should mention gold. Got: {data2.get('god_mode_response')}"
        )

        # Verify gold was updated in state
        if "game_state" in data2:
            gold = data2["game_state"].get("player_character_data", {}).get("gold")
            assert gold == 200, f"Gold should be 200 after second command, got {gold}"

        # Verify both LLM calls were made (not just one)
        assert (
            mock_gemini_generate.call_count >= 2
        ), f"Expected at least 2 LLM calls, got {mock_gemini_generate.call_count}"

        # Verify the second call received the second command, not the first
        # Check the user_action in the second call
        if mock_gemini_generate.call_count >= 2:
            second_call_args = mock_gemini_generate.call_args_list[1]
            # The user_action should be in the prompt/content
            call_str = str(second_call_args)
            assert (
                "gold" in call_str.lower() or "200" in call_str
            ), (
                f"Second LLM call should contain 'gold' or '200', not 'HP' or '50'. "
                f"Call args: {call_str[:500]}"
            )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_story_context_reloaded_for_each_command(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that story_context is reloaded from Firestore for each command.
        
        This verifies that the caching bug is fixed by ensuring story_context
        includes the previous command's entry when processing the second command.
        """
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_context_reload"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        call_count = {"count": 0}
        captured_calls = []

        def mock_gemini_side_effect(*args, **kwargs):
            """Mock Gemini to track story_context in each call."""
            call_count["count"] += 1
            
            # Extract story_history from the call to verify it's being reloaded
            # The story_history should grow with each command
            call_args_str = str(args) + str(kwargs)
            captured_calls.append(call_args_str)
            
            if call_count["count"] == 1:
                # First call: story_context should be empty or minimal
                # (no previous commands yet)
                return FakeLLMResponse(
                    json.dumps(
                        {
                            "god_mode_response": "First command processed",
                            "narrative": "",
                            "state_updates": {},
                        }
                    )
                )
            elif call_count["count"] == 2:
                # Second call: story_context should include the first command
                return FakeLLMResponse(
                    json.dumps(
                        {
                            "god_mode_response": "Second command processed",
                            "narrative": "",
                            "state_updates": {},
                        }
                    )
                )
            else:
                return FakeLLMResponse(
                    json.dumps(
                        {
                            "god_mode_response": f"Call #{call_count['count']}",
                            "narrative": "",
                            "state_updates": {},
                        }
                    )
                )

        mock_gemini_generate.side_effect = mock_gemini_side_effect

        # Send first command
        response1 = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "GOD MODE: Set HP to 50", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )
        assert response1.status_code == 200

        # Send second command
        response2 = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps(
                {"input": "GOD MODE: Set gold to 200", "mode": "character"}
            ),
            content_type="application/json",
            headers=self.test_headers,
        )
        assert response2.status_code == 200

        # Verify both calls were made
        assert (
            mock_gemini_generate.call_count >= 2
        ), f"Expected at least 2 calls, got {mock_gemini_generate.call_count}"

        # Verify second call includes first command in story_context
        assert len(captured_calls) >= 2, f"Expected at least 2 calls, got {len(captured_calls)}"
        second_call = captured_calls[1]
        assert "GOD MODE: Set HP" in second_call or "Set HP" in second_call, (
            f"Second call should include first command in story_context. "
            f"Call args (first 1000 chars): {second_call[:1000]}"
        )


if __name__ == "__main__":
    unittest.main()
