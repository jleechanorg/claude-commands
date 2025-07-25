#!/usr/bin/env python3
"""
Simple integration test for the prototype validation system.
Run from mvp_site directory with: TESTING=true vpython test_prototype_validation.py
"""

import unittest
import sys
import os
import time

from game_state_integration import MockGameState
from validators.fuzzy_token_validator import FuzzyTokenValidator
from validators.hybrid_validator import HybridValidator
from validators.llm_validator import LLMValidator
from validators.token_validator import SimpleTokenValidator, TokenValidator

# Add prototype directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'prototype'))

# Import prototype modules
try:





    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_SUCCESSFUL = False


class TestPrototypeValidation(unittest.TestCase):
    """Test the prototype validation system works correctly."""
    
    @unittest.skipIf(not IMPORTS_SUCCESSFUL, "Prototype imports failed")
    def test_basic_validators(self):
        """Test each validator type independently."""
        narrative = "Gideon raised his sword while Rowan prepared her spells."
        expected_entities = ["Gideon", "Rowan"]
        
        # Test SimpleTokenValidator
        simple = SimpleTokenValidator()
        result = simple.validate(narrative, expected_entities)
        self.assertTrue(result["all_entities_present"])
        self.assertEqual(set(result["entities_found"]), set(expected_entities))
        
        # Test TokenValidator with descriptors
        token = TokenValidator()
        narrative_desc = "The knight and the healer stood ready."
        result = token.validate(narrative_desc, expected_entities)
        self.assertTrue(result["all_entities_present"])
        
        # Test FuzzyTokenValidator
        fuzzy = FuzzyTokenValidator()
        narrative_fuzzy = "Gid-- was cut off while speaking to the healer."
        result = fuzzy.validate(narrative_fuzzy, expected_entities)
        self.assertEqual(len(result["entities_found"]), 2)
        
    @unittest.skipIf(not IMPORTS_SUCCESSFUL, "Prototype imports failed")
    def test_game_state_integration(self):
        """Test game state integration."""
        game_state = MockGameState()
        
        # Test manifest generation
        manifest = game_state.get_active_entity_manifest()
        self.assertEqual(manifest["entity_count"], 2)
        self.assertEqual(manifest["location"], "Kaelan's Cell")
        
        # Test validation
        result = game_state.validate_narrative_consistency(
            "Gideon and Rowan entered the chamber."
        )
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["missing_entities"], [])
        
    @unittest.skipIf(not IMPORTS_SUCCESSFUL, "Prototype imports failed")
    def test_performance_requirement(self):
        """Test validation meets <50ms requirement."""
        fuzzy = FuzzyTokenValidator()
        narrative = "Gideon and Rowan battled the dragon."
        entities = ["Gideon", "Rowan"]
        
        # Warm up
        fuzzy.validate(narrative, entities)
        
        # Time 10 validations
        start = time.time()
        for _ in range(10):
            fuzzy.validate(narrative, entities)
        avg_time = (time.time() - start) / 10
        
        # Should be under 50ms
        self.assertLess(avg_time, 0.05, f"Validation too slow: {avg_time*1000:.1f}ms")
        
    @unittest.skipIf(not IMPORTS_SUCCESSFUL, "Prototype imports failed")
    def test_hybrid_validator(self):
        """Test hybrid validator combines approaches correctly."""
        hybrid = HybridValidator()
        
        # Test simple case
        result = hybrid.validate(
            "Gideon and Rowan stood ready.",
            ["Gideon", "Rowan"]
        )
        self.assertTrue(result["all_entities_present"])
        self.assertGreater(result["confidence"], 0.9)
        
        # Test confidence cascade
        result = hybrid.validate(
            "Someone moved in the shadows.",
            ["Gideon", "Rowan"]
        )
        self.assertFalse(result["all_entities_present"])
        self.assertLess(result["confidence"], 0.5)


if __name__ == "__main__":
    if not IMPORTS_SUCCESSFUL:
        print("\nERROR: Cannot run tests - prototype imports failed")
        print("Make sure you're running from mvp_site directory")
        sys.exit(1)
    
    # Run tests
    unittest.main(verbosity=2)