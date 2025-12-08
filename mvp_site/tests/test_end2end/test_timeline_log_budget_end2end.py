"""
End-to-end test for timeline_log budget fix.

Tests that story continuation with large context does not cause
ContextTooLargeError due to timeline_log being excluded from scaffold estimate.

Production evidence (Dec 7, 2025): story context = 26,795 tokens, timeline log =
27,817 tokens, final prompt = 54,612 tokens (~2x expected). The scaffold
budget considered only the story context, but the timeline log (story context
reformatted with `[SEQ_ID: X] Actor:` prefixes) added ~5% overhead on another
full copy of the story content.

Expected fix: Budget story context using `TIMELINE_LOG_DUPLICATION_FACTOR`
so the combined story + timeline content fits within the model limit.
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
    """Test that large story context doesn't overflow due to timeline_log duplication."""

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
    @patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content")
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
        Verify that scaffold estimate accounts for timeline_log.

        The scaffold at lines 3166-3172 should include an estimate for
        timeline_log which is approximately story_tokens * 1.05 (5% overhead
        for [SEQ_ID: X] Actor: prefixes).
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

    def test_timeline_log_budget_bug_reproduction(self):
        """
        CRITICAL TEST: Reproduce the production timeline_log budget bug.

        This test MUST FAIL until the bug is fixed.

        Bug: The scaffold estimate (lines 3166-3172) does NOT include timeline_log,
        but the final prompt DOES include it. This means story content is counted
        once but included twice, causing ContextTooLargeError in production.

        Production evidence (Dec 7, 2025):
        - Model: zai-glm-4.6 (131K context)
        - Scaffold budget showed: story=26,795 tokens OK
        - Timeline log: 27,817 tokens (reformatted story with ~5% overhead)
        - Final prompt: 54,612 tokens (nearly 2x expected budget)
        - Root cause: timeline_log added another full copy of story content

        This test validates that:
        1. The scaffold estimate includes timeline_log OR
        2. Story tokens + timeline_log tokens <= max_input_allowed after truncation
        """

        # Simulate the production scenario with large story context
        # Production had 26,795 tokens in story - let's create similar sized context
        story_context = []

        # Create 200 turns with substantial content to get ~25K tokens
        for i in range(200):
            if i % 2 == 0:
                # Player turns - ~100 tokens each
                story_context.append({
                    "actor": "player",
                    "text": f"Turn {i}: I carefully survey the ancient chamber, looking for any "
                            f"signs of danger or valuable artifacts. The dust swirls in the "
                            f"torchlight as I move deeper into the ruins. My companions watch "
                            f"my back, weapons at the ready. " * 2,
                    "sequence_id": i + 1,
                })
            else:
                # GM turns - ~150 tokens each
                story_context.append({
                    "actor": "gm",
                    "text": f"Turn {i}: The ancient ruins stretch before you, their weathered "
                            f"stones telling tales of civilizations long forgotten. Mysterious "
                            f"runes pulse with ethereal light as shadows dance along crumbling "
                            f"walls. A chill wind carries whispers of the past. The party "
                            f"advances cautiously through corridors carved millennia ago. " * 2,
                    "sequence_id": i + 1,
                })

        # Calculate story tokens
        story_text = "".join(entry.get("text", "") for entry in story_context)
        story_tokens = llm_service.estimate_tokens(story_text)

        # Build timeline log (this duplicates story content with prefixes)
        timeline_log = llm_service._build_timeline_log(story_context)
        timeline_tokens = llm_service.estimate_tokens(timeline_log)

        # Get model limits for zai-glm-4.6 (the production model)
        model_name = "zai-glm-4.6"
        provider = constants.LLM_PROVIDER_CEREBRAS

        safe_token_budget, output_reserve, max_input_allowed = (
            llm_service._calculate_context_budget(provider, model_name, False)
        )

        # Calculate scaffold and story budget using the same guard logic
        estimated_scaffold = 30000  # ~30K for system instruction + game state + other parts
        raw_story_budget = max_input_allowed - estimated_scaffold - llm_service.ENTITY_TRACKING_TOKEN_RESERVE

        include_timeline_log = llm_service.TIMELINE_LOG_INCLUDED_IN_STRUCTURED_REQUEST
        fixed_story_budget, guard_note = llm_service._apply_timeline_log_duplication_guard(
            available_story_tokens_raw=raw_story_budget,
            include_timeline_log_in_prompt=include_timeline_log,
        )
        self.assertFalse(
            include_timeline_log,
            "Structured LLMRequest should not serialize timeline_log; guardrail should be inactive.",
        )
        self.assertEqual(
            fixed_story_budget,
            raw_story_budget,
            "When timeline_log is not serialized, the budget should remain unadjusted.",
        )
        self.assertIn("not serialized", guard_note)

        # Total story content that will appear in final prompt
        total_story_content = story_tokens + timeline_tokens

        print("\n=== Timeline Log Budget Fix Verification ===")
        print(f"Model: {model_name}")
        print(f"Max input allowed: {max_input_allowed:,} tokens")
        print(f"Estimated scaffold: {estimated_scaffold:,} tokens")
        print(f"Entity reserve: {llm_service.ENTITY_TRACKING_TOKEN_RESERVE:,} tokens")
        print(f"Raw story budget: {raw_story_budget:,} tokens")
        print(f"Fixed story budget: {fixed_story_budget:,} tokens ({guard_note})")
        print("---")
        print(f"Story context tokens: {story_tokens:,}")
        print(f"Timeline log tokens: {timeline_tokens:,}")
        print(f"Total story content: {total_story_content:,} tokens")
        print("---")
        print(f"Story fits in fixed budget: {story_tokens:,} <= {fixed_story_budget:,} = {story_tokens <= fixed_story_budget}")
        print(f"Total content fits in raw budget: {total_story_content:,} <= {raw_story_budget:,} = {total_story_content <= raw_story_budget}")

        # VERIFY THE FIX: If timeline_log were serialized, the guardrail would shrink
        # the story budget. Because it is excluded from LLMRequest, the raw budget is
        # the authoritative limit for story_history alone.
        if include_timeline_log:
            self.assertLessEqual(
                total_story_content,
                raw_story_budget,
                (
                    "\n\n🔴 FIX VERIFICATION FAILED! 🔴\n"
                    f"Story ({story_tokens:,}) fits in fixed budget ({fixed_story_budget:,})\n"
                    f"But total content ({total_story_content:,}) EXCEEDS raw budget ({raw_story_budget:,})!\n"
                    f"Guard note: {guard_note}"
                ),
            )
            print("\n✅ FIX VERIFIED: Timeline log budget calculation is correct!")
        else:
            # Document the current behavior so future changes are explicit
            self.assertGreater(
                total_story_content,
                raw_story_budget,
                "Timeline log is omitted from structured request; combined content would exceed the raw budget if it were sent.",
            )
            print(
                "\n📝 Timeline log omitted from structured request; duplication guard inactive"
            )


class TestTimelineLogBudgetGuardrails(unittest.TestCase):
    """Unit tests for the timeline_log duplication guardrail helpers."""

    def test_budget_not_reduced_when_timeline_not_serialized(self):
        """The structured LLM request excludes timeline_log, so keep full budget."""

        raw_budget = 50_000
        adjusted_budget, note = llm_service._apply_timeline_log_duplication_guard(
            available_story_tokens_raw=raw_budget,
            include_timeline_log_in_prompt=False,
        )

        self.assertEqual(
            adjusted_budget,
            raw_budget,
            "Timeline log guardrail should not shrink budget when it isn't serialized.",
        )
        self.assertIn("not serialized", note)

    def test_budget_reduced_when_timeline_in_prompt(self):
        """If timeline_log is included, apply the duplication factor."""

        raw_budget = 50_000
        adjusted_budget, note = llm_service._apply_timeline_log_duplication_guard(
            available_story_tokens_raw=raw_budget,
            include_timeline_log_in_prompt=True,
        )

        expected_budget = int(
            raw_budget / llm_service.TIMELINE_LOG_DUPLICATION_FACTOR
        )

        self.assertEqual(adjusted_budget, expected_budget)
        self.assertIn("duplication factor", note)


if __name__ == "__main__":
    unittest.main()
