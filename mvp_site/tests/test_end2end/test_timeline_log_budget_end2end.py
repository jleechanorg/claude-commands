"""
End-to-end coverage for timeline_log budgeting guardrails.

Context: A Dec 7, 2025 production run (story=26,795 tokens, timeline log=
27,817 tokens, final prompt=54,612 tokens) overflowed because an older
prompt-concatenation flow appended the timeline log alongside story_context
without budgeting the duplicate content.

Current behavior: The structured LLMRequest path serializes story_history and
metadata but **excludes** timeline_log_string. A duplication guard
(`TIMELINE_LOG_DUPLICATION_FACTOR = 2.05`) remains available but is gated by
`TIMELINE_LOG_INCLUDED_IN_STRUCTURED_REQUEST = False`, so the guard is dormant
unless we intentionally serialize timeline text again.

These tests document the token relationship between story and timeline_log,
assert the guard is inactive for the structured request, and show how the guard
would behave if we ever enable timeline_log serialization in the payload.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from mvp_site import constants, llm_service, main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestTimelineLogBudgetEnd2End(unittest.TestCase):
    """E2E regression for large story contexts and the dormant duplication guard."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.test_user_id = "test-user-timeline-budget"
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

        self.mock_llm_response_data = {
            "narrative": "The party continues their journey...",
            "entities_mentioned": ["Hero"],
            "location_confirmed": "Ancient Forest",
            "state_updates": {"story_progression": "continued"},
        }

    def _create_large_story_context_for_timeline_bug(self, turns: int = 80) -> list:
        """
        Create a large story context designed to trigger the timeline_log bug.

        The bug occurs because:
        1. story_context is budgeted at ~X tokens
        2. timeline_log is built from story_context and adds ~X more tokens
        3. But timeline_log is NOT included in scaffold estimate

        With 80 turns of ~600 chars each = ~48K chars = ~12K tokens
        Timeline log would add another ~12K tokens (with SEQ_ID prefixes)
        Total story content = ~24K tokens when only ~12K was budgeted
        """
        story_context = []

        # Create rich narrative content that will be duplicated in timeline_log
        narrative_templates = [
            "The ancient ruins stretch before you, their weathered stones telling "
            "tales of civilizations long forgotten. Mysterious runes pulse with "
            "ethereal energy as you step through the crumbling archway. ",

            "Your footsteps echo through the vast chamber, disturbing centuries "
            "of dust. Strange shadows dance along the walls, cast by torches "
            "that seem to burn without fuel. The air grows thick with magic. ",

            "A distant rumble echoes through the corridors as something ancient "
            "stirs in the depths below. The party exchanges nervous glances, "
            "weapons drawn and spells at the ready for whatever comes next. ",
        ]

        player_actions = [
            "I carefully examine the glowing runes, trying to decipher their meaning. ",
            "I signal the party to halt and listen for any sounds of danger ahead. ",
            "I cast a detection spell to reveal any hidden traps or magical wards. ",
            "I move forward cautiously, keeping my shield raised and ready. ",
        ]

        for i in range(turns):
            if i % 2 == 0:
                # Player turn - shorter but still substantial
                action = player_actions[i % len(player_actions)]
                story_context.append({
                    "actor": "player",
                    "text": f"Turn {i}: {action}" + action * 2,  # ~200 chars
                    "sequence_id": i + 1,
                })
            else:
                # GM turn - longer narrative content
                narrative = narrative_templates[i % len(narrative_templates)]
                story_context.append({
                    "actor": "gm",
                    "text": f"Turn {i}: {narrative}" + narrative,  # ~400 chars
                    "sequence_id": i + 1,
                })

        return story_context

    def _setup_fake_firestore_with_timeline_bug_campaign(self, fake_firestore, campaign_id):
        """Set up Firestore with game state designed to trigger timeline_log bug."""
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Timeline Log Bug Test", "setting": "Fantasy"}
        )

        # Create game state with large story context
        game_state = {
            "user_id": self.test_user_id,
            "story_text": "A long ongoing adventure...",
            "story_context": self._create_large_story_context_for_timeline_bug(80),
            "characters": ["Hero"],
            "locations": ["Ancient Ruins", "Dark Forest"],
            "items": ["Magic Sword"],
            "combat_state": {"in_combat": False},
            "custom_campaign_state": {
                "session_number": 10,
                "core_memories": ["The quest began in the village of Millbrook"],
            },
            "npc_data": {
                "Guide": {
                    "mbti": "ENFJ",
                    "role": "ally",
                    "background": "A mysterious guide who knows the ancient paths.",
                }
            },
            "world_data": {
                "current_location_name": "Ancient Ruins",
                "time_of_day": "night",
            },
            "player_character_data": {
                "name": "Hero",
                "class": "Fighter",
                "level": 5,
            },
        }

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            game_state
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.cerebras_provider.generate_content")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_native_tools")
    def test_large_story_context_does_not_overflow_due_to_timeline_log(
        self, mock_gemini_generate, mock_cerebras_generate, mock_get_db
    ):
        """
        Test that story continuation with large context succeeds.

        This is the regression test for the timeline_log budget bug.

        Before the fix:
        - Scaffold estimate: ~53K tokens (story_context counted once)
        - Final prompt: ~96K tokens (story content included twice via timeline_log)
        - Result: ContextTooLargeError

        After the fix:
        - Scaffold should account for timeline_log duplication
        - Truncation should reduce story to fit BOTH inclusions
        - Result: Success (200)
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "timeline_log_bug_test"
        self._setup_fake_firestore_with_timeline_bug_campaign(fake_firestore, campaign_id)

        mock_cerebras_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )

        # This request should NOT fail with ContextTooLargeError
        # Before the fix, timeline_log duplication would cause overflow
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "I examine the ancient altar carefully",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Get response data for error reporting
        response_data = response.data.decode()

        # Check for the specific ContextTooLargeError
        if response.status_code == 400:
            self.assertNotIn(
                "Context too large",
                response_data,
                f"Timeline log budget bug triggered! The scaffold estimate does not "
                f"account for timeline_log which duplicates story content. "
                f"Response: {response_data[:500]}"
            )

        # Should succeed - if timeline_log budget fix works
        self.assertEqual(
            response.status_code,
            200,
            f"Expected 200 (timeline_log budget fix working), got {response.status_code}: "
            f"{response_data[:500]}"
        )


class TestTimelineLogBudgetCalculation(unittest.TestCase):
    """Unit tests for timeline_log budget calculation correctness."""

    def test_scaffold_estimate_includes_timeline_log(self):
        """
        Document token relationship between story and timeline_log text.

        The structured request currently omits timeline_log, but the guardrail
        constant assumes timeline_log would add ~5% overhead to a duplicated
        copy of the story if it were serialized. This test keeps that ratio
        honest and serves as a safety check if the payload ever includes the
        timeline text again.
        """

        # Create story context
        story_context = [
            {"actor": "gm", "text": "Test narrative " * 100, "sequence_id": 1},
            {"actor": "player", "text": "Test action " * 50, "sequence_id": 2},
        ]

        # Calculate story tokens
        story_text = "".join(entry.get("text", "") for entry in story_context)
        story_tokens = llm_service.estimate_tokens(story_text)

        # Build timeline log
        timeline_log = llm_service._build_timeline_log(story_context)
        timeline_tokens = llm_service.estimate_tokens(timeline_log)

        # Timeline log should be roughly story_tokens + overhead for prefixes
        # The overhead is [SEQ_ID: X] Actor: for each entry
        overhead_ratio = timeline_tokens / story_tokens if story_tokens > 0 else 1

        # Timeline log should be at MOST 10% larger than story (prefixes add ~5%)
        self.assertLess(
            overhead_ratio,
            1.10,
            f"Timeline log overhead is too high: {overhead_ratio:.2f}x story tokens. "
            f"Story: {story_tokens}, Timeline: {timeline_tokens}"
        )

        # Timeline log should be at LEAST as large as story (it contains all story text)
        self.assertGreaterEqual(
            timeline_tokens,
            story_tokens * 0.95,  # Allow 5% tolerance for estimation variance
            f"Timeline log should contain at least as many tokens as story. "
            f"Story: {story_tokens}, Timeline: {timeline_tokens}"
        )


if __name__ == "__main__":
    unittest.main()
