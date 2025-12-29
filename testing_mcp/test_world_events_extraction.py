#!/usr/bin/env python3
"""
Test: World Events Extraction from Nested Locations
Bead: W2-7m1

BUG REPRODUCTION: When LLM outputs world_events nested inside
`state_updates.custom_campaign_state.world_events` instead of the correct
`state_updates.world_events`, the extraction code doesn't find it.

Evidence: Campaign STpjRuwjeUt97tpCl5nK has:
- game_state.world_events: Turn 27 events (correct location)
- custom_campaign_state.world_events: Turn 138 events (WRONG location)

This test reproduces the extraction failure.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mvp_site.structured_fields_utils import extract_structured_fields


class TestWorldEventsExtraction(unittest.TestCase):
    """Test world_events extraction from various LLM output locations."""

    def test_world_events_extracted_from_top_level_state_updates(self):
        """BASELINE: world_events at state_updates.world_events is extracted."""
        # Create mock LLM response with world_events at correct location
        mock_response = MagicMock()
        mock_response.structured_response = MagicMock()
        mock_response.structured_response.state_updates = {
            "world_events": {
                "background_events": [
                    {"actor": "Test Actor", "action": "Did something", "turn_generated": 27}
                ],
                "turn_generated": 27
            }
        }
        # Set other required attributes to avoid AttributeError
        mock_response.structured_response.session_header = ""
        mock_response.structured_response.planning_block = ""
        mock_response.structured_response.dice_rolls = []
        mock_response.structured_response.dice_audit_events = []
        mock_response.structured_response.resources = {}
        mock_response.structured_response.debug_info = {}
        mock_response.structured_response.god_mode_response = ""

        result = extract_structured_fields(mock_response)

        # Verify world_events was extracted
        self.assertIn("world_events", result,
            "world_events should be extracted when at top-level state_updates")
        self.assertEqual(result["world_events"]["turn_generated"], 27)

    def test_world_events_extracted_from_custom_campaign_state(self):
        """BUG REPRODUCTION: world_events nested in custom_campaign_state is NOT extracted.

        This test FAILS before the fix - proving the bug exists.
        """
        # Create mock LLM response with world_events nested INSIDE custom_campaign_state
        # This is what the LLM sometimes outputs incorrectly
        mock_response = MagicMock()
        mock_response.structured_response = MagicMock()
        mock_response.structured_response.state_updates = {
            "custom_campaign_state": {
                "world_events": {
                    "background_events": [
                        {"actor": "Nested Actor", "action": "Nested action", "turn_generated": 138}
                    ],
                    "turn_generated": 138
                },
                "success_streak": 5
            }
        }
        # Set other required attributes
        mock_response.structured_response.session_header = ""
        mock_response.structured_response.planning_block = ""
        mock_response.structured_response.dice_rolls = []
        mock_response.structured_response.dice_audit_events = []
        mock_response.structured_response.resources = {}
        mock_response.structured_response.debug_info = {}
        mock_response.structured_response.god_mode_response = ""

        result = extract_structured_fields(mock_response)

        # BUG: This assertion FAILS before the fix
        # The world_events nested in custom_campaign_state is NOT extracted
        self.assertIn("world_events", result,
            f"BEAD W2-7m1: world_events nested in custom_campaign_state should be "
            f"extracted to prevent split storage. Got keys: {list(result.keys())}")
        self.assertEqual(result["world_events"]["turn_generated"], 138,
            "Extracted world_events should have turn_generated=138 from nested location")

    def test_world_events_in_both_locations_prefers_top_level(self):
        """When world_events exists in both locations, prefer top-level."""
        mock_response = MagicMock()
        mock_response.structured_response = MagicMock()
        mock_response.structured_response.state_updates = {
            "world_events": {
                "background_events": [{"actor": "Top Level", "turn_generated": 27}],
                "turn_generated": 27
            },
            "custom_campaign_state": {
                "world_events": {
                    "background_events": [{"actor": "Nested", "turn_generated": 138}],
                    "turn_generated": 138
                }
            }
        }
        # Set other required attributes
        mock_response.structured_response.session_header = ""
        mock_response.structured_response.planning_block = ""
        mock_response.structured_response.dice_rolls = []
        mock_response.structured_response.dice_audit_events = []
        mock_response.structured_response.resources = {}
        mock_response.structured_response.debug_info = {}
        mock_response.structured_response.god_mode_response = ""

        result = extract_structured_fields(mock_response)

        # Top-level should take precedence
        self.assertIn("world_events", result)
        self.assertEqual(result["world_events"]["turn_generated"], 27,
            "Top-level world_events should take precedence over nested")


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
