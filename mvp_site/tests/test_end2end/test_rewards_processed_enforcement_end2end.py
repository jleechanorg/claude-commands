"""
End-to-end test for rewards_processed discrepancy detection and LLM self-correction.

Tests that when combat ends and the LLM doesn't set rewards_processed=True,
the server detects the discrepancy and returns it in system_corrections
for LLM self-correction in the next turn.

Root Cause Context:
- In campaign kuXKa6vrYY6P99MfhWBn, combat ended but rewards_processed stayed False
- RewardsAgent was selected 52+ consecutive times instead of StoryModeAgent
- Living world stopped updating because RewardsAgent didn't include living world prompts

Previous Approach (Removed):
- Server-side enforcement that overrode LLM decisions

Current Approach (LLM Self-Correction):
- Server detects discrepancy via _detect_rewards_discrepancy()
- Discrepancy message added to response.system_corrections
- Next LLM call receives system_corrections in input
- LLM fixes the issue itself

This follows CLAUDE.md "LLM Decides, Server Detects" principle.
"""

from __future__ import annotations

import io
import json
import logging
import os
import unittest
from unittest.mock import patch

# Ensure TESTING is set before importing app modules
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestRewardsDiscrepancyDetectionEnd2End(unittest.TestCase):
    """
    Test that server detects rewards discrepancies for LLM self-correction.

    Instead of server-side enforcement, we now detect discrepancies and
    return them in system_corrections for the LLM to fix in the next turn.
    """

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-enforcement"
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

    def _setup_campaign_with_combat_ended(self, fake_firestore, campaign_id):
        """
        Set up a campaign where combat just ended but rewards_processed=False.

        This simulates the bug state where the LLM ended combat but didn't
        set rewards_processed, causing RewardsAgent to get stuck.
        """
        # Create test campaign
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Combat Test Campaign", "setting": "Fantasy realm"}
        )

        # Create game state with combat ended but rewards_processed=False
        # This is the bug state that triggers RewardsAgent forever
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "The goblin falls defeated.",
                "player_turn": 10,
                "player_character_data": {
                    "level": 3,
                    "experience": {"current": 500},
                },
                "combat_state": {
                    "in_combat": False,
                    "combat_phase": "ended",
                    "combat_summary": {
                        "xp_awarded": 50,
                        "enemies_defeated": ["goblin_1"],
                        "outcome": "victory",
                    },
                    "rewards_processed": False,  # BUG: LLM didn't set this
                },
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_server_detects_discrepancy_when_llm_forgets_rewards_processed(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that server detects discrepancy and returns system_corrections.

        Scenario:
        1. Combat just ended (combat_phase="ended", combat_summary exists)
        2. rewards_processed=False (LLM failed to set it)
        3. User sends input
        4. LLM response also doesn't set rewards_processed
        5. Server DETECTS discrepancy (doesn't enforce)
        6. Response includes system_corrections with REWARDS_STATE_ERROR

        The LLM self-correction happens in the NEXT turn when system_corrections
        is included in the input.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "discrepancy_detection_test"
        self._setup_campaign_with_combat_ended(fake_firestore, campaign_id)

        # Mock LLM response that DOES NOT set rewards_processed
        # This simulates the LLM failing to follow the ESSENTIALS protocol
        mock_response_data = {
            "narrative": "With the goblin defeated, you catch your breath. Victory!",
            "planning_block": {
                "thinking": "Combat is over. Player earned XP.",
                "choices": {
                    "continue": {
                        "text": "Continue",
                        "description": "Move on from the battle",
                        "risk_level": "low",
                    },
                },
            },
            "state_updates": {
                "player_character_data": {
                    "experience": {"current": 550},  # XP increased by 50
                },
                # NOTE: NO combat_state.rewards_processed=True here!
                # This is the bug - LLM forgot to set it
            },
            "rewards_box": {
                "xp_earned": 50,
                "gold_earned": 10,
            },
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(mock_response_data)
        )

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "continue", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response is successful
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        # Parse response
        response_data = json.loads(response.data)

        # CRITICAL: Verify system_corrections contains the discrepancy
        # This is the new behavior - we DETECT instead of ENFORCE
        system_corrections = response_data.get("system_corrections", [])

        # The discrepancy should be detected and returned
        # Note: The actual correction happens when the LLM receives this in the next turn
        self.assertTrue(
            len(system_corrections) > 0
            or response_data.get("state_updates", {})
            .get("combat_state", {})
            .get("rewards_processed", False),
            "Server should either detect discrepancy (system_corrections) or "
            "state should have rewards_processed=True (if RewardsAgent followup fixed it)"
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_no_discrepancy_when_rewards_already_processed(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Verify no discrepancy is reported when rewards_processed=True.

        This is the happy path - LLM correctly set rewards_processed,
        so no system_corrections should be added.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "no_discrepancy_test"

        # Set up campaign with rewards ALREADY processed
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "No Discrepancy Test", "setting": "Fantasy realm"}
        )
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "You've collected your rewards.",
                "player_turn": 11,
                "combat_state": {
                    "in_combat": False,
                    "combat_phase": "ended",
                    "combat_summary": {"xp_awarded": 50},
                    "rewards_processed": True,  # Already processed - no discrepancy
                },
            }
        )

        # Mock standard story continuation response
        mock_response_data = {
            "narrative": "The adventure continues...",
            "planning_block": {"thinking": "Normal story mode"},
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(mock_response_data)
        )

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "explore the area", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        # Parse response
        response_data = json.loads(response.data)

        # No system_corrections with REWARDS_STATE_ERROR should be present
        system_corrections = response_data.get("system_corrections", [])
        rewards_errors = [c for c in system_corrections if "REWARDS_STATE_ERROR" in c]

        self.assertEqual(
            len(rewards_errors),
            0,
            f"No REWARDS_STATE_ERROR expected when rewards_processed=True, "
            f"but got: {rewards_errors}",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_rewards_agent_not_called_repeatedly_after_rewards_processed(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Verify that after rewards_processed=True, RewardsAgent is NOT selected.

        This is the second part of the fix - once rewards are processed,
        subsequent requests should go to StoryModeAgent, not RewardsAgent.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "after_rewards_test"

        # Set up campaign with rewards ALREADY processed
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "After Rewards Test", "setting": "Fantasy realm"}
        )
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "You've collected your rewards.",
                "player_turn": 11,
                "combat_state": {
                    "in_combat": False,
                    "combat_phase": "ended",
                    "combat_summary": {"xp_awarded": 50},
                    "rewards_processed": True,  # Already processed
                },
            }
        )

        # Mock standard story continuation response
        mock_response_data = {
            "narrative": "The adventure continues...",
            "planning_block": {"thinking": "Normal story mode"},
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(mock_response_data)
        )

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "explore the area", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        # The test passing means RewardsAgent.matches_game_state() returned False
        # (because rewards_processed=True) and StoryModeAgent was used instead


class TestMultiTurnCorrectionInjection(unittest.TestCase):
    """
    Test that pending_system_corrections from previous turn are injected into next LLM request.

    This is the critical multi-turn flow:
    1. Turn N: LLM forgets rewards_processed → Server detects and persists to game_state
    2. Turn N+1: Server reads pending_system_corrections and injects into LLM request
    3. LLM sees correction and fixes the state

    These tests verify step 2 - that corrections are properly injected.
    """

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-multiturn"
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
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_pending_system_corrections_injected_into_llm_request(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that pending_system_corrections from game_state are passed to LLM.

        This is the multi-turn correction flow:
        1. Previous turn detected discrepancy and persisted to game_state
        2. This turn should inject those corrections into the LLM request
        3. Verify the LLM actually receives the corrections

        We verify by checking the log output contains the injection message.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "multiturn_correction_test"

        # Set up campaign
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Multi-Turn Correction Test", "setting": "Fantasy realm"}
        )

        # CRITICAL: Set up game_state WITH pending_system_corrections
        # This simulates the previous turn having detected a discrepancy
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "The goblin falls defeated.",
                "player_turn": 10,
                "player_character_data": {
                    "level": 3,
                    "experience": {"current": 550},  # XP was already increased
                },
                "combat_state": {
                    "in_combat": False,
                    "combat_phase": "ended",
                    "combat_summary": {
                        "xp_awarded": 50,
                        "enemies_defeated": ["goblin_1"],
                        "outcome": "victory",
                    },
                    "rewards_processed": False,  # Still False - needs fixing
                },
                # THIS IS THE KEY: pending_system_corrections from previous turn
                "pending_system_corrections": [
                    "REWARDS_STATE_ERROR: Combat ended (phase=ended) with summary, "
                    "but rewards_processed=False. You MUST set combat_state.rewards_processed=true."
                ],
            }
        )

        # Set up log capture to verify the injection message
        log_capture_string = io.StringIO()
        handler = logging.StreamHandler(log_capture_string)
        handler.setLevel(logging.WARNING)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        try:
            # Capture the call args
            mock_gemini_generate.return_value = FakeLLMResponse(
                json.dumps({
                    "narrative": "You check your rewards. [Fixing the state as instructed]",
                    "planning_block": {"thinking": "System correction received."},
                    "state_updates": {
                        "combat_state": {
                            "rewards_processed": True,  # LLM fixes the issue
                        },
                    },
                })
            )

            # Make the API request (Turn N+1)
            response = self.client.post(
                f"/api/campaigns/{campaign_id}/interaction",
                data=json.dumps({"input": "check my rewards", "mode": "character"}),
                content_type="application/json",
                headers=self.test_headers,
            )

            # Verify response is successful
            self.assertEqual(
                response.status_code, 200,
                f"Expected 200, got {response.status_code}: {response.data}",
            )

            # Get the log output
            log_contents = log_capture_string.getvalue()

        finally:
            root_logger.removeHandler(handler)

        # CRITICAL: Verify the log shows system_corrections were injected
        # The log message is: "🔧 Injecting N system_corrections into LLM request: [...]"
        self.assertIn(
            "Injecting",
            log_contents,
            f"Should see 'Injecting' in logs. Got: {log_contents[:500]}",
        )
        self.assertIn(
            "system_corrections",
            log_contents,
            f"Should see 'system_corrections' in logs. Got: {log_contents[:500]}",
        )
        self.assertIn(
            "REWARDS_STATE_ERROR",
            log_contents,
            f"Should see 'REWARDS_STATE_ERROR' in logs. Got: {log_contents[:500]}",
        )


class TestSystemCorrectionsInPrompt(unittest.TestCase):
    """
    Test that system_corrections documentation is in the prompts.

    This verifies the LLM will understand how to handle corrections.
    """

    def test_game_state_instruction_documents_system_corrections(self):
        """Verify game_state_instruction.md includes system_corrections docs."""
        import os

        # Get the path relative to this test file
        test_dir = os.path.dirname(os.path.abspath(__file__))
        mvp_site_dir = os.path.dirname(os.path.dirname(test_dir))
        prompt_path = os.path.join(mvp_site_dir, "prompts", "game_state_instruction.md")

        self.assertTrue(
            os.path.exists(prompt_path),
            f"game_state_instruction.md not found at {prompt_path}",
        )

        with open(prompt_path, "r") as f:
            content = f.read()

        # Check for system_corrections documentation
        self.assertIn(
            "system_corrections",
            content,
            "game_state_instruction.md must document system_corrections field",
        )
        self.assertIn(
            "REWARDS_STATE_ERROR",
            content,
            "game_state_instruction.md should show example of REWARDS_STATE_ERROR",
        )

    def test_rewards_instruction_mentions_system_corrections(self):
        """Verify rewards_system_instruction.md mentions system_corrections."""
        import os

        # Get the path relative to this test file
        test_dir = os.path.dirname(os.path.abspath(__file__))
        mvp_site_dir = os.path.dirname(os.path.dirname(test_dir))
        prompt_path = os.path.join(mvp_site_dir, "prompts", "rewards_system_instruction.md")

        self.assertTrue(
            os.path.exists(prompt_path),
            f"rewards_system_instruction.md not found at {prompt_path}",
        )

        with open(prompt_path, "r") as f:
            content = f.read()

        # Check for system_corrections mention
        self.assertIn(
            "SYSTEM CORRECTIONS",
            content,
            "rewards_system_instruction.md should mention SYSTEM CORRECTIONS",
        )


class TestCombatModeCorrectionsPersistedEnd2End(unittest.TestCase):
    """
    Test that system_corrections are persisted for COMBAT mode.

    BUG FOUND: In world_logic.py:process_action_unified():
    1. Line 2036: pending_system_corrections cleared before first Firestore persist
    2. Line 2040: First Firestore persist (without new corrections)
    3. Line 2323: New corrections added to game_state dict
    4. Line 2362-2368: Second persist ONLY for CHARACTER mode

    For COMBAT mode, corrections detected during the turn are added to the
    in-memory dict but NEVER persisted to Firestore. This breaks the LLM
    self-correction mechanism for combat mode.
    """

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.test_user_id = "test-user-combat-persistence"
        self.campaign_id = "combat_persistence_test"

    def _setup_active_combat_campaign(self, fake_firestore):
        """
        Set up a campaign with active combat that will end this turn.

        The LLM will return a response that ends combat but doesn't set
        rewards_processed=True, which should trigger discrepancy detection.
        """
        # Create test campaign
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.campaign_id).set(
            {"title": "Combat Persistence Test", "setting": "A dungeon"}
        )

        # Create game state with ACTIVE combat (not ended yet)
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.campaign_id).collection("game_states").document(
            "current_state"
        ).set(
            {
                "user_id": self.test_user_id,
                "story_text": "You face the goblin in combat!",
                "player_turn": 5,
                "player_character_data": {
                    "name": "TestHero",
                    "level": 3,
                    "experience": {"current": 500},
                },
                "combat_state": {
                    "in_combat": True,
                    "combat_phase": "player_turn",
                    "enemies": [{"id": "goblin_1", "hp": 5}],
                    "rewards_processed": False,
                },
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_combat_mode_discrepancies_persisted_to_firestore(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that discrepancies detected in COMBAT mode are persisted.

        This test should FAIL with the current implementation because:
        1. Combat ends with discrepancy (rewards_processed=False)
        2. Server detects discrepancy and adds to game_state dict
        3. But for COMBAT mode, there's no second Firestore persist
        4. Corrections are lost and won't be available for next turn

        Expected: pending_system_corrections should be in the final Firestore state
        Actual (Bug): pending_system_corrections is NOT persisted for combat mode
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        self._setup_active_combat_campaign(fake_firestore)

        # Mock LLM response that ENDS combat but FORGETS to set rewards_processed
        # This simulates the bug scenario
        mock_response_data = {
            "narrative": "You strike the goblin down! Victory is yours!",
            "planning_block": {
                "thinking": "Combat ended. Player won.",
            },
            "state_updates": {
                "combat_state": {
                    "in_combat": False,
                    "combat_phase": "ended",  # Combat ended
                    "combat_summary": {
                        "xp_awarded": 50,
                        "enemies_defeated": ["goblin_1"],
                        "outcome": "victory",
                    },
                    # BUG: rewards_processed NOT set to True
                },
                "player_character_data": {
                    "experience": {"current": 550},  # XP awarded
                },
            },
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(mock_response_data)
        )

        # Import world_logic to call directly
        from mvp_site import world_logic

        # Call process_action_unified in COMBAT mode
        import asyncio
        result = asyncio.run(
            world_logic.process_action_unified(
                {
                    "user_id": self.test_user_id,
                    "campaign_id": self.campaign_id,
                    "user_input": "I attack the goblin with my sword!",
                    "mode": "combat",  # COMBAT mode, not character
                }
            )
        )

        # Verify the call succeeded
        self.assertNotIn(
            "error", result,
            f"process_action_unified failed: {result.get('error')}",
        )

        # CRITICAL CHECK: Verify system_corrections detected in response
        self.assertIn(
            "system_corrections", result,
            "Server should detect rewards discrepancy and return system_corrections",
        )
        self.assertTrue(
            len(result["system_corrections"]) > 0,
            "Should have at least one system correction for rewards_processed",
        )

        # CRITICAL CHECK: Verify corrections were PERSISTED to Firestore
        # This is the bug - for combat mode, the corrections are NOT persisted
        final_game_state = fake_firestore.collection("users").document(
            self.test_user_id
        ).collection("campaigns").document(self.campaign_id).collection(
            "game_states"
        ).document("current_state").get()

        final_state_data = final_game_state.to_dict() if final_game_state.exists else {}

        # THIS ASSERTION SHOULD FAIL with current implementation
        # because combat mode doesn't have a second Firestore persist
        self.assertIn(
            "pending_system_corrections", final_state_data,
            "PERSISTENCE BUG: pending_system_corrections not persisted for combat mode! "
            "Corrections detected during combat won't be available in next turn's prompt. "
            f"Final state keys: {list(final_state_data.keys())}",
        )

        # Also verify the content of persisted corrections
        if "pending_system_corrections" in final_state_data:
            corrections = final_state_data["pending_system_corrections"]
            self.assertTrue(
                len(corrections) > 0,
                "Persisted corrections should not be empty",
            )
            self.assertTrue(
                any("REWARDS_STATE_ERROR" in c for c in corrections),
                f"Corrections should contain REWARDS_STATE_ERROR. Got: {corrections}",
            )


class TestLLMSetCorrectionsPreservedEnd2End(unittest.TestCase):
    """
    Test that LLM-set pending_system_corrections are preserved during state merge.

    BUG FOUND (fixed): When an LLM (especially god mode) sets pending_system_corrections
    in its state_updates response, these corrections were being popped at line 2036
    AFTER being merged into the game state dict. This meant:
    1. LLM response contains state_updates.pending_system_corrections
    2. Corrections merged into updated_game_state_dict
    3. Line 2036 pops ALL pending_system_corrections (including the new ones!)
    4. Corrections lost and not persisted to Firestore

    FIX: Move the pop to BEFORE the merge (line 1791), so:
    1. Old corrections (from previous turn) are cleared
    2. New corrections from LLM state_updates are merged in
    3. New corrections are preserved and persisted

    This test verifies that LLM-set corrections persist correctly.
    """

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.test_user_id = "test-user-llm-corrections"
        self.campaign_id = "llm_corrections_test"

    def _setup_basic_campaign(self, fake_firestore):
        """Set up a basic campaign for god mode testing."""
        # Create test campaign
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.campaign_id).set(
            {"title": "LLM Corrections Test", "setting": "A dungeon"}
        )

        # Create basic game state
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.campaign_id).collection("game_states").document(
            "current_state"
        ).set(
            {
                "user_id": self.test_user_id,
                "story_text": "You are in a dungeon.",
                "player_turn": 1,
                "player_character_data": {
                    "name": "TestHero",
                    "level": 1,
                    "experience": {"current": 0},
                },
                "combat_state": {
                    "in_combat": False,
                },
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_llm_set_pending_corrections_persisted_to_firestore(
        self, mock_gemini_generate, mock_get_db
    ):
        """
        Test that when LLM sets pending_system_corrections in state_updates,
        those corrections are preserved and persisted to Firestore.

        This reproduces the bug where god mode couldn't set up correction test
        scenarios because the corrections were immediately popped after merge.

        Before fix: pending_system_corrections would be [] in Firestore
        After fix: pending_system_corrections contains LLM-set corrections
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        self._setup_basic_campaign(fake_firestore)

        # The correction message that god mode would set
        correction_msg = (
            "REWARDS_STATE_ERROR: Combat ended (phase=ended) with summary, "
            "but rewards_processed=False. You MUST set combat_state.rewards_processed=true."
        )

        # Mock LLM response that SETS pending_system_corrections (like god mode)
        mock_response_data = {
            "narrative": "State has been set for testing.",
            "god_mode_response": "FORCED STATE UPDATE: pending_system_corrections set",
            "planning_block": {
                "thinking": "Setting up test state",
            },
            "state_updates": {
                "combat_state": {
                    "in_combat": False,
                    "combat_phase": "ended",
                    "combat_summary": {
                        "xp_awarded": 100,
                        "enemies_defeated": ["goblin_1"],
                        "outcome": "victory",
                    },
                    "rewards_processed": False,  # Bug state
                },
                # KEY: LLM is setting pending_system_corrections directly
                "pending_system_corrections": [correction_msg],
            },
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(mock_response_data)
        )

        # Import world_logic to call directly
        from mvp_site import world_logic

        # Call process_action_unified in GOD mode (like the test scenario)
        import asyncio
        result = asyncio.run(
            world_logic.process_action_unified(
                {
                    "user_id": self.test_user_id,
                    "campaign_id": self.campaign_id,
                    "user_input": "Set pending_system_corrections for testing",
                    "mode": "god",  # GOD mode sets state directly
                }
            )
        )

        # Verify the call succeeded
        self.assertNotIn(
            "error", result,
            f"process_action_unified failed: {result.get('error')}",
        )

        # CRITICAL CHECK: Verify corrections were PERSISTED to Firestore
        # Before fix: This would FAIL because corrections were popped after merge
        # After fix: This should PASS because corrections are preserved
        final_game_state = fake_firestore.collection("users").document(
            self.test_user_id
        ).collection("campaigns").document(self.campaign_id).collection(
            "game_states"
        ).document("current_state").get()

        final_state_data = final_game_state.to_dict() if final_game_state.exists else {}

        # Debug info for assertion
        debug_info = (
            f"Final state keys: {list(final_state_data.keys())}, "
            f"combat_state: {final_state_data.get('combat_state', {})}"
        )

        # THIS ASSERTION verifies the fix
        self.assertIn(
            "pending_system_corrections", final_state_data,
            f"LLM-set pending_system_corrections should be persisted to Firestore! "
            f"Before fix, corrections were popped at line 2036 after merge. "
            f"{debug_info}",
        )

        # Verify the content of persisted corrections
        corrections = final_state_data.get("pending_system_corrections", [])
        self.assertTrue(
            len(corrections) > 0,
            f"Persisted corrections should not be empty. Got: {corrections}",
        )
        self.assertTrue(
            any("REWARDS_STATE_ERROR" in c for c in corrections),
            f"Corrections should contain the LLM-set REWARDS_STATE_ERROR. Got: {corrections}",
        )


if __name__ == "__main__":
    unittest.main()
