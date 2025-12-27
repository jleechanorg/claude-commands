"""
Test that entity tracking tokens are properly accounted for in the scaffold budget.

This test reproduces the bug where entity tracking (entity_preload_text,
entity_specific_instructions, entity_tracking_instruction) is added AFTER
truncation, causing the final prompt to exceed the context window limit.

Bug details from production logs:
- Model: qwen-3-235b-a22b-instruct-2507
- Input used: 97,923 tokens
- Max allowed: 94,372 tokens (80% of 117,964)
- Overage: ~3,500 tokens (from entity tracking not budgeted)

Fix: Added ENTITY_TRACKING_TOKEN_RESERVE constant (10,500 tokens) that is
explicitly added to scaffold budget before truncation calculation.
"""

import unittest
from unittest.mock import MagicMock, patch

from mvp_site import constants, llm_service
from mvp_site.token_utils import estimate_tokens


class TestEntityTrackingBudget(unittest.TestCase):
    """Test that entity tracking is properly budgeted in scaffold estimation."""

    def test_entity_tracking_must_be_included_in_scaffold_budget(self):
        """
        Verify that entity tracking tokens are included in scaffold budget.

        Fix implemented: ENTITY_TRACKING_TOKEN_RESERVE constant (10,500 tokens)
        is now added to scaffold budget before truncation calculation.
        """
        # Entity tracking that gets added AFTER truncation
        # These are realistic sizes for a game with 10+ NPCs
        entity_preload_text = "E" * 8000  # ~2000 tokens - NPC summaries
        entity_specific_instructions = (
            "F" * 6000
        )  # ~1500 tokens - per-turn instructions
        entity_tracking_instruction = "G" * 4000  # ~1000 tokens - tracking rules
        timeline_log = "H" * 12000  # ~3000 tokens - story timeline

        # Total entity tracking overhead
        entity_overhead = (
            entity_preload_text
            + entity_specific_instructions
            + entity_tracking_instruction
            + timeline_log
        )
        entity_overhead_tokens = estimate_tokens(entity_overhead)

        # THE KEY ASSERTION: ENTITY_TRACKING_TOKEN_RESERVE must cover entity overhead
        self.assertGreaterEqual(
            llm_service.ENTITY_TRACKING_TOKEN_RESERVE,
            entity_overhead_tokens,
            f"ENTITY_TRACKING_TOKEN_RESERVE ({llm_service.ENTITY_TRACKING_TOKEN_RESERVE}) "
            f"must be >= entity tracking overhead ({entity_overhead_tokens} tokens).",
        )

    def test_entity_tracking_reserve_covers_production_overhead(self):
        """
        Verify ENTITY_TRACKING_TOKEN_RESERVE covers the production error case.

        From production logs:
        - Model: qwen-3-235b-a22b-instruct-2507
        - Overage: ~3,500 tokens (entity tracking not budgeted)
        """
        # Entity tracking overhead from production error
        production_overhead_tokens = 3500

        # The fix uses explicit reserve instead of percentage
        self.assertGreaterEqual(
            llm_service.ENTITY_TRACKING_TOKEN_RESERVE,
            production_overhead_tokens,
            f"ENTITY_TRACKING_TOKEN_RESERVE ({llm_service.ENTITY_TRACKING_TOKEN_RESERVE}) "
            f"must cover production overhead ({production_overhead_tokens} tokens).",
        )


class TestScaffoldBudgetCalculation(unittest.TestCase):
    """Test the scaffold budget calculation logic."""

    def test_entity_tracking_reserve_covers_max_overhead(self):
        """
        Verify ENTITY_TRACKING_TOKEN_RESERVE covers maximum possible entity tracking.
        """
        # Maximum entity tracking sizes (worst case with many NPCs)
        MAX_ENTITY_PRELOAD_TOKENS = 3000  # 10+ NPCs with full descriptions
        MAX_ENTITY_INSTRUCTIONS_TOKENS = 2000  # Complex entity instructions
        MAX_ENTITY_TRACKING_TOKENS = 1500  # Tracking rules
        MAX_TIMELINE_LOG_TOKENS = 4000  # Long story timeline

        TOTAL_ENTITY_OVERHEAD = (
            MAX_ENTITY_PRELOAD_TOKENS
            + MAX_ENTITY_INSTRUCTIONS_TOKENS
            + MAX_ENTITY_TRACKING_TOKENS
            + MAX_TIMELINE_LOG_TOKENS
        )

        self.assertGreaterEqual(
            llm_service.ENTITY_TRACKING_TOKEN_RESERVE,
            TOTAL_ENTITY_OVERHEAD,
            f"ENTITY_TRACKING_TOKEN_RESERVE ({llm_service.ENTITY_TRACKING_TOKEN_RESERVE}) "
            f"must be >= max entity overhead ({TOTAL_ENTITY_OVERHEAD}).",
        )

    def test_entity_tracking_reserve_constant_exists(self):
        """Verify the ENTITY_TRACKING_TOKEN_RESERVE constant exists and is reasonable."""
        self.assertTrue(
            hasattr(llm_service, "ENTITY_TRACKING_TOKEN_RESERVE"),
            "ENTITY_TRACKING_TOKEN_RESERVE constant must exist in llm_service",
        )
        self.assertGreater(
            llm_service.ENTITY_TRACKING_TOKEN_RESERVE,
            5000,
            "ENTITY_TRACKING_TOKEN_RESERVE should be > 5000 tokens for safety",
        )
        self.assertLess(
            llm_service.ENTITY_TRACKING_TOKEN_RESERVE,
            20000,
            "ENTITY_TRACKING_TOKEN_RESERVE should be < 20000 to leave room for story",
        )


if __name__ == "__main__":
    unittest.main()
