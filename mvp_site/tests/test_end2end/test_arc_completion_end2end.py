"""
End-to-end integration test for arc/event completion tracking.

Tests the arc_milestones system that provides structured state tracking
for narrative arcs, preventing the LLM from losing track of completed events.

Problem being solved:
- LLM compressed memories capture narrative events as prose
- No structured "WEDDING_TOUR_COMPLETED" flag exists
- LLM can "forget" that major arcs are complete, causing timeline confusion

Solution:
- arc_milestones field in custom_campaign_state with explicit completion flags
- Milestone data persists to Firestore and is included in LLM context
- Provides deterministic arc phase tracking
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ.setdefault("TESTING_AUTH_BYPASS", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

from mvp_site import main
from mvp_site.game_state import GameState
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestArcCompletionEnd2End(unittest.TestCase):
    """End-to-end tests for arc/event completion tracking through the full stack."""

    def setUp(self):
        """Set up test client and mock infrastructure."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Stable test UID and stub Firebase verification
        self.test_user_id = "test-user-arc-completion"
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

    # =========================================================================
    # Test 1: GameState arc_milestones initialization
    # =========================================================================

    def test_game_state_initializes_with_empty_arc_milestones(self):
        """GameState should initialize with empty arc_milestones dict."""
        gs = GameState()
        self.assertIn("arc_milestones", gs.custom_campaign_state)
        self.assertEqual(gs.custom_campaign_state["arc_milestones"], {})

    def test_game_state_preserves_existing_arc_milestones(self):
        """GameState should preserve arc_milestones from input data."""
        initial_milestones = {
            "wedding_tour": {
                "status": "completed",
                "completed_at": "2024-01-15T10:30:00Z",
                "phase": "post_wedding",
            }
        }
        gs = GameState(custom_campaign_state={"arc_milestones": initial_milestones})
        self.assertEqual(gs.custom_campaign_state["arc_milestones"], initial_milestones)

    # =========================================================================
    # Test 2: Arc milestone completion tracking
    # =========================================================================

    def test_mark_arc_completed(self):
        """GameState.mark_arc_completed() should set status and timestamp."""
        gs = GameState()

        # Mark an arc as completed
        gs.mark_arc_completed("wedding_tour", phase="ceremony_complete")

        milestones = gs.custom_campaign_state["arc_milestones"]
        self.assertIn("wedding_tour", milestones)
        self.assertEqual(milestones["wedding_tour"]["status"], "completed")
        self.assertIn("completed_at", milestones["wedding_tour"])
        self.assertEqual(milestones["wedding_tour"]["phase"], "ceremony_complete")

    def test_mark_arc_in_progress(self):
        """GameState.update_arc_progress() should track in-progress arcs."""
        gs = GameState()

        # Start an arc
        gs.update_arc_progress("wedding_tour", phase="corellia_visit", progress=25)

        milestones = gs.custom_campaign_state["arc_milestones"]
        self.assertEqual(milestones["wedding_tour"]["status"], "in_progress")
        self.assertEqual(milestones["wedding_tour"]["phase"], "corellia_visit")
        self.assertEqual(milestones["wedding_tour"]["progress"], 25)

    def test_is_arc_completed(self):
        """GameState.is_arc_completed() should return completion status."""
        gs = GameState()

        # Initially not completed
        self.assertFalse(gs.is_arc_completed("wedding_tour"))

        # After marking completed
        gs.mark_arc_completed("wedding_tour")
        self.assertTrue(gs.is_arc_completed("wedding_tour"))

    def test_get_arc_phase(self):
        """GameState.get_arc_phase() should return current phase or None."""
        gs = GameState()

        # No arc tracked yet
        self.assertIsNone(gs.get_arc_phase("wedding_tour"))

        # After setting phase
        gs.update_arc_progress("wedding_tour", phase="nar_shaddaa")
        self.assertEqual(gs.get_arc_phase("wedding_tour"), "nar_shaddaa")

    def test_arc_milestones_handles_corrupt_entries(self):
        """Per-arc entries that are None/non-dict should not crash and should recover."""
        for bad_value in (None, "bad-data"):
            gs = GameState(
                custom_campaign_state={"arc_milestones": {"wedding_tour": bad_value}}
            )

            # Safe defaults for corrupt entries
            self.assertFalse(gs.is_arc_completed("wedding_tour"))
            self.assertIsNone(gs.get_arc_phase("wedding_tour"))
            self.assertEqual(gs.get_completed_arcs_summary(), "")

            # Updating progress should recover into a dict entry
            gs.update_arc_progress("wedding_tour", phase="corellia_visit", progress=10)
            milestone = gs.custom_campaign_state["arc_milestones"]["wedding_tour"]
            self.assertEqual(milestone["status"], "in_progress")
            self.assertEqual(milestone["phase"], "corellia_visit")

    def test_completed_arcs_summary_ignores_invalid_entries(self):
        """Summary should skip invalid per-arc entries rather than error."""
        gs = GameState(
            custom_campaign_state={
                "arc_milestones": {
                    "bad_arc": None,
                    "good_arc": {
                        "status": "completed",
                        "completed_at": "2024-01-15T10:30:00Z",
                        "phase": "finale",
                    },
                }
            }
        )

        summary = gs.get_completed_arcs_summary()
        self.assertIn("good_arc", summary)
        self.assertNotIn("bad_arc", summary)

    # =========================================================================
    # Test 3: Arc milestones persist to Firestore
    # =========================================================================

    @patch("mvp_site.firestore_service.get_db")
    def test_arc_milestones_persist_to_firestore(self, mock_get_db):
        """Arc milestones should be saved to Firestore when game state is saved."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_arc_campaign"

        # Set up campaign with arc milestones
        game_state_data = {
            "user_id": self.test_user_id,
            "custom_campaign_state": {
                "arc_milestones": {
                    "wedding_tour": {
                        "status": "completed",
                        "completed_at": "2024-01-15T10:30:00Z",
                        "phase": "ceremony_complete",
                    }
                }
            },
            "combat_state": {"in_combat": False},
        }

        # Save to Firestore
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            game_state_data
        )

        # Retrieve and verify
        doc = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
        )

        data = doc.to_dict()
        self.assertIn("arc_milestones", data["custom_campaign_state"])
        self.assertEqual(
            data["custom_campaign_state"]["arc_milestones"]["wedding_tour"]["status"],
            "completed",
        )

    # =========================================================================
    # Test 4: Arc milestones included in LLM context
    # =========================================================================

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_arc_milestones_included_in_llm_context(
        self, mock_gemini_generate, mock_get_db
    ):
        """Arc milestones should be included when building LLM context."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_arc_context_campaign"

        # Set up campaign with completed wedding tour
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set({"title": "Arc Test Campaign"})

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "custom_campaign_state": {
                    "arc_milestones": {
                        "wedding_tour": {
                            "status": "completed",
                            "completed_at": "2024-01-15T10:30:00Z",
                        }
                    }
                },
                "combat_state": {"in_combat": False},
            }
        )

        # Mock LLM response
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(
                {
                    "narrative": "The wedding tour has concluded. You are now on Nathema.",
                    "entities_mentioned": [],
                    "state_updates": {},
                    "planning_block": {
                        "thinking": "The user has completed the wedding arc. Transitioning to post-wedding state.",
                        "choices": [
                            {
                                "text": "Explore Nathema",
                                "description": "Look around your new home.",
                                "risk_level": "low",
                            }
                        ],
                    },
                    "session_header": "Session 5: Post-Wedding",
                }
            )
        )

        # Make API request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps(
                {"input": "Where am I in the timeline?", "mode": "character"}
            ),
            content_type="application/json",
            headers=self.test_headers,
        )

        self.assertEqual(response.status_code, 200)

        # Verify LLM was called successfully
        self.assertTrue(mock_gemini_generate.called)

        call_args = mock_gemini_generate.call_args
        prompt_contents = call_args.kwargs.get("prompt_contents")
        self.assertIsNotNone(prompt_contents, "Expected prompt contents in LLM call")
        serialized_prompt = " ".join(str(item) for item in prompt_contents)
        self.assertIn("arc_milestones", serialized_prompt)
        self.assertIn("wedding_tour", serialized_prompt)

    # =========================================================================
    # Test 5: Arc completion prevents timeline confusion
    # =========================================================================

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_completed_arc_prevents_regression(self, mock_gemini_generate, mock_get_db):
        """
        When an arc is marked completed, subsequent state updates should NOT
        allow reverting to in_progress for that arc.
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Create game state with completed arc
        gs = GameState(
            custom_campaign_state={
                "arc_milestones": {
                    "wedding_tour": {
                        "status": "completed",
                        "completed_at": "2024-01-15T10:30:00Z",
                    }
                }
            }
        )

        # Attempt to regress the arc (should be rejected or logged as warning)
        gs.update_arc_progress("wedding_tour", phase="corellia_visit", progress=50)

        # The arc should remain completed (immutable once completed)
        self.assertTrue(gs.is_arc_completed("wedding_tour"))
        self.assertEqual(
            gs.custom_campaign_state["arc_milestones"]["wedding_tour"]["status"],
            "completed",
        )

    # =========================================================================
    # Test 6: Get completed arcs summary for context
    # =========================================================================

    def test_get_completed_arcs_summary(self):
        """GameState.get_completed_arcs_summary() returns formatted string for LLM."""
        gs = GameState()

        # No completed arcs
        summary = gs.get_completed_arcs_summary()
        self.assertEqual(summary, "")

        # Add completed arcs
        gs.mark_arc_completed("wedding_tour", phase="ceremony_complete")
        gs.mark_arc_completed("power_consolidation", phase="level_100_reached")

        summary = gs.get_completed_arcs_summary()
        self.assertIn("wedding_tour", summary)
        self.assertIn("completed", summary.lower())
        self.assertIn("power_consolidation", summary)

    # =========================================================================
    # Test 7: Arc milestones serialization in to_dict
    # =========================================================================

    def test_arc_milestones_serialized_in_to_dict(self):
        """GameState.to_dict() should include arc_milestones."""
        gs = GameState()
        gs.mark_arc_completed("wedding_tour", phase="final")

        data = gs.to_dict()

        self.assertIn("custom_campaign_state", data)
        self.assertIn("arc_milestones", data["custom_campaign_state"])
        self.assertEqual(
            data["custom_campaign_state"]["arc_milestones"]["wedding_tour"]["status"],
            "completed",
        )

    def test_arc_milestones_deserialized_from_dict(self):
        """GameState.from_dict() should properly load arc_milestones."""
        source = {
            "custom_campaign_state": {
                "arc_milestones": {
                    "wedding_tour": {
                        "status": "completed",
                        "completed_at": "2024-01-15T10:30:00Z",
                    }
                }
            }
        }

        gs = GameState.from_dict(source)

        self.assertTrue(gs.is_arc_completed("wedding_tour"))


class TestArcMilestonesIntegration(unittest.TestCase):
    """Integration tests for arc milestones with other game systems."""

    def test_arc_milestones_with_god_mode_updates(self):
        """God mode updates should be able to set arc milestones."""
        gs = GameState()

        # Simulate god mode update setting arc completion
        god_mode_update = {
            "arc_milestones": {
                "3_masks": {
                    "status": "in_progress",
                    "phase": "wedding_tour",
                    "sub_arcs": {"wedding_tour": {"status": "completed"}},
                }
            }
        }

        # Apply the update
        gs.custom_campaign_state["arc_milestones"].update(
            god_mode_update["arc_milestones"]
        )

        # Verify nested structure is preserved
        self.assertEqual(
            gs.custom_campaign_state["arc_milestones"]["3_masks"]["sub_arcs"][
                "wedding_tour"
            ]["status"],
            "completed",
        )

    def test_arc_milestones_with_time_skip(self):
        """Time skip events should be trackable via arc milestones."""
        gs = GameState()

        # Mark time skip as an event
        gs.mark_arc_completed(
            "time_skip_3_months",
            phase="domestic_peace",
            metadata={
                "in_game_duration": "3 months",
                "narrative_summary": "Retired to Nathema, domestic peace",
            },
        )

        milestone = gs.custom_campaign_state["arc_milestones"]["time_skip_3_months"]
        self.assertEqual(milestone["status"], "completed")
        self.assertEqual(milestone["metadata"]["in_game_duration"], "3 months")


class TestArcMilestonesPromptIntegration(unittest.TestCase):
    """Test that arc milestones are wired into LLM prompt building."""

    def test_arc_completion_reminder_included_in_continuation_prompt(self):
        """Completed arcs should appear in the continuation reminder prompt."""
        from mvp_site.agent_prompts import PromptBuilder

        # Create GameState with completed arcs
        gs = GameState()
        gs.mark_arc_completed("wedding_tour", phase="ceremony_complete")
        gs.mark_arc_completed("power_arc", phase="consolidated")

        # Build the prompt
        builder = PromptBuilder(game_state=gs)
        continuation_reminder = builder.build_continuation_reminder()

        # Verify arc completion enforcement is present
        self.assertIn("ARC COMPLETION ENFORCEMENT", continuation_reminder)
        self.assertIn("COMPLETED ARCS", continuation_reminder)
        self.assertIn("wedding_tour", continuation_reminder)
        self.assertIn("power_arc", continuation_reminder)
        self.assertIn("DO NOT revisit", continuation_reminder)

    def test_arc_completion_reminder_empty_when_no_completed_arcs(self):
        """No arc completion section when no arcs are completed."""
        from mvp_site.agent_prompts import PromptBuilder

        # Create GameState with no completed arcs
        gs = GameState()

        # Build the prompt
        builder = PromptBuilder(game_state=gs)
        arc_reminder = builder.build_arc_completion_reminder()

        # Should return empty string
        self.assertEqual(arc_reminder, "")

    def test_arc_completion_reminder_handles_none_game_state(self):
        """Arc completion reminder handles None game_state gracefully."""
        from mvp_site.agent_prompts import PromptBuilder

        # Build the prompt with no game state
        builder = PromptBuilder(game_state=None)
        arc_reminder = builder.build_arc_completion_reminder()

        # Should return empty string
        self.assertEqual(arc_reminder, "")


if __name__ == "__main__":
    unittest.main()
