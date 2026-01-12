"""Tests for action_resolution field consolidation (Phases 2-4)

Tests cover:
- action_resolution as primary field name
- reinterpreted field support
- Normalization from legacy fields (dice_rolls, dice_audit_events)
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvp_site.narrative_response_schema import NarrativeResponse, parse_structured_response


class TestActionResolution(unittest.TestCase):
    """Test action_resolution field consolidation"""

    def test_action_resolution_primary_field(self):
        """Test action_resolution is accepted as primary field name"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution={
                "player_input": "I attack the goblin",
                "interpreted_as": "melee_attack",
                "reinterpreted": False,
                "mechanics": {
                    "rolls": [{"purpose": "attack", "notation": "1d20+5", "result": 17}],
                },
                "audit_flags": [],
            },
        )
        # Should have action_resolution
        self.assertTrue(hasattr(response, "action_resolution"))
        self.assertIsInstance(response.action_resolution, dict)
        self.assertEqual(response.action_resolution["player_input"], "I attack the goblin")
        self.assertEqual(response.action_resolution["interpreted_as"], "melee_attack")
        self.assertFalse(response.action_resolution["reinterpreted"])


    def test_reinterpreted_field_defaults_to_false(self):
        """Test reinterpreted field defaults to False if not provided"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution={
                "player_input": "I attack",
                "interpreted_as": "attack",
                "audit_flags": [],
            },
        )
        # Should default to False
        self.assertFalse(response.action_resolution["reinterpreted"])

    def test_reinterpreted_field_explicit_true(self):
        """Test reinterpreted field can be explicitly set to True"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution={
                "player_input": "The king agrees",
                "interpreted_as": "persuasion_attempt",
                "reinterpreted": True,
                "audit_flags": ["player_declared_outcome"],
            },
        )
        self.assertTrue(response.action_resolution["reinterpreted"])

    def test_audit_flags_defaults_to_empty_list(self):
        """Test audit_flags defaults to empty list if not provided"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution={
                "player_input": "I attack",
                "interpreted_as": "attack",
            },
        )
        # Should default to empty list
        self.assertEqual(response.action_resolution.get("audit_flags"), [])

    def test_normalize_legacy_dice_rolls(self):
        """Test normalization from legacy dice_rolls field"""
        response = NarrativeResponse(
            narrative="Test narrative",
            dice_rolls=["1d20+5 = 17", "1d8+3 = 8"],
            dice_audit_events=[
                {"type": "attack_roll", "result": 17},
                {"type": "damage_roll", "result": 8},
            ],
        )
        # Should normalize legacy fields to action_resolution format
        unified = response.get_unified_action_resolution()
        self.assertIsInstance(unified, dict)
        # Should have mechanics with rolls
        self.assertIn("mechanics", unified)
        self.assertIn("rolls", unified["mechanics"])
        self.assertEqual(len(unified["mechanics"]["rolls"]), 2)
        # Should have audit_events
        self.assertIn("audit_events", unified["mechanics"])
        self.assertEqual(len(unified["mechanics"]["audit_events"]), 2)
        # Should have normalized_from_legacy flag
        self.assertIn("normalized_from_legacy", unified.get("audit_flags", []))

    def test_normalize_legacy_no_dice_rolls(self):
        """Test normalization returns empty dict when no legacy fields"""
        response = NarrativeResponse(
            narrative="Test narrative",
        )
        unified = response.get_unified_action_resolution()
        self.assertEqual(unified, {})

    def test_normalize_legacy_preserves_existing_action_resolution(self):
        """Test normalization doesn't override existing action_resolution"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution={
                "player_input": "I attack",
                "interpreted_as": "attack",
                "reinterpreted": False,
                "audit_flags": [],
            },
            dice_rolls=["1d20+5 = 17"],  # Should be ignored
        )
        unified = response.get_unified_action_resolution()
        # Should use existing action_resolution, not normalize from legacy
        self.assertEqual(unified["player_input"], "I attack")
        self.assertNotIn("normalized_from_legacy", unified.get("audit_flags", []))

    def test_explicit_empty_action_resolution_does_not_normalize(self):
        """Test that explicitly empty action_resolution dict doesn't normalize from legacy"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution={},  # Explicitly empty - should not normalize
            dice_rolls=["1d20+5 = 17"],
            dice_audit_events=[{"type": "attack_roll", "result": 17}],
        )
        unified = response.get_unified_action_resolution()
        # Should return empty dict, not normalize from legacy
        self.assertEqual(unified, {"reinterpreted": False, "audit_flags": []})
        self.assertNotIn("normalized_from_legacy", unified.get("audit_flags", []))

    def test_outcome_resolution_provided_flag_set_correctly(self):
        """Test that _action_resolution_provided is True when outcome_resolution is provided.
        
        Bug fix: When only outcome_resolution (legacy) is provided, _action_resolution_provided
        should be True so get_unified_action_resolution() returns the validated data instead
        of trying to normalize from dice_rolls/dice_audit_events.
        """
        # Test with only outcome_resolution (no action_resolution, no dice_rolls)
        response = NarrativeResponse(
            narrative="Test narrative",
            outcome_resolution={
                "player_input": "The king agrees",
                "interpreted_as": "persuasion_attempt",
                "reinterpreted": True,
                "audit_flags": ["player_declared_outcome"],
            },
        )
        
        # get_unified_action_resolution() should return the validated outcome_resolution data
        # not try to normalize from legacy fields (which don't exist)
        unified = response.get_unified_action_resolution()
        
        # Should return the validated outcome_resolution data, not {}
        self.assertIsInstance(unified, dict)
        self.assertEqual(unified["player_input"], "The king agrees")
        self.assertEqual(unified["interpreted_as"], "persuasion_attempt")
        self.assertTrue(unified["reinterpreted"])
        self.assertIn("player_declared_outcome", unified.get("audit_flags", []))
        
        # Should NOT have normalized_from_legacy flag (since we used provided data, not normalized)
        self.assertNotIn("normalized_from_legacy", unified.get("audit_flags", []))

    def test_to_dict_includes_action_resolution(self):
        """Test to_dict() includes action_resolution in output"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution={
                "player_input": "I attack",
                "interpreted_as": "attack",
                "reinterpreted": False,
                "audit_flags": [],
            },
        )
        result = response.to_dict()
        self.assertIn("action_resolution", result)
        self.assertEqual(result["action_resolution"]["player_input"], "I attack")

    def test_outcome_resolution_consistency_in_to_dict(self):
        """Test that outcome_resolution and action_resolution have consistent values in to_dict().
        
        Bug fix: When outcome_resolution is provided, both fields should have the same
        validated, normalized data structure (not raw unvalidated outcome_resolution).
        """
        # Test with outcome_resolution provided (legacy field)
        # Note: outcome_resolution might be missing required fields like "reinterpreted" or "audit_flags"
        raw_outcome_resolution = {
            "player_input": "The king agrees",
            "interpreted_as": "persuasion_attempt",
            # Missing "reinterpreted" and "audit_flags" - should be normalized by validation
        }
        
        response = NarrativeResponse(
            narrative="Test narrative",
            outcome_resolution=raw_outcome_resolution,
        )
        
        result = response.to_dict()
        
        # Both fields should be present
        self.assertIn("action_resolution", result)
        self.assertIn("outcome_resolution", result)
        
        # Both should have the same validated values (not raw outcome_resolution)
        action_res = result["action_resolution"]
        outcome_res = result["outcome_resolution"]
        
        # Should be identical (same validated dict)
        self.assertEqual(action_res, outcome_res)
        
        # Should have normalized fields (reinterpreted defaults to False, audit_flags defaults to [])
        self.assertIn("reinterpreted", action_res)
        self.assertIn("audit_flags", action_res)
        self.assertEqual(action_res["reinterpreted"], False)
        self.assertEqual(action_res["audit_flags"], [])
        
        # Should preserve original fields
        self.assertEqual(action_res["player_input"], "The king agrees")
        self.assertEqual(action_res["interpreted_as"], "persuasion_attempt")
        
        # Verify outcome_resolution has same normalized values
        self.assertEqual(outcome_res["reinterpreted"], False)
        self.assertEqual(outcome_res["audit_flags"], [])
        self.assertEqual(outcome_res["player_input"], "The king agrees")


    def test_validate_action_resolution_with_invalid_type(self):
        """Test validation handles invalid action_resolution type"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution="not a dict",  # Invalid type
        )
        # Should handle gracefully - return empty dict or log warning
        # Based on implementation, it should return empty dict
        self.assertEqual(response.action_resolution, {})

    def test_validate_action_resolution_with_none(self):
        """Test validation handles None action_resolution"""
        response = NarrativeResponse(
            narrative="Test narrative",
            action_resolution=None,
        )
        # Should return empty dict
        self.assertEqual(response.action_resolution, {})

    def test_parse_structured_response_with_action_resolution(self):
        """Test parse_structured_response handles action_resolution in JSON"""
        json_response = json.dumps({
            "narrative": "Test narrative",
            "action_resolution": {
                "player_input": "I attack",
                "interpreted_as": "attack",
                "reinterpreted": False,
                "audit_flags": [],
            },
        })
        narrative, response = parse_structured_response(json_response)
        self.assertTrue(hasattr(response, "action_resolution"))
        self.assertEqual(response.action_resolution["player_input"], "I attack")

