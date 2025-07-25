#!/usr/bin/env python3
"""
Test the complete Combined approach (Structured Generation + Validation)
Demonstrates the full implementation of Milestone 1
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import unittest

from entity_tracking import create_from_game_state
from narrative_response_schema import (
    NarrativeResponse,
    create_structured_prompt_injection,
    parse_structured_response,
    validate_entity_coverage,
)
from narrative_sync_validator import NarrativeSyncValidator


class TestCompleteCombinedApproach(unittest.TestCase):
    """Test the complete Combined approach implementation"""

    def setUp(self):
        """Set up test scenario"""
        self.game_state = {
            "player_character_data": {
                "name": "Gideon",
                "hp": 45,
                "hp_max": 60,
                "level": 3,
            },
            "npc_data": {
                "Sariel": {
                    "name": "Sariel",
                    "hp": 38,
                    "hp_max": 50,
                    "present": True,
                    "conscious": True,
                    "hidden": False,
                },
                "Rowan": {
                    "name": "Rowan",
                    "hp": 22,
                    "hp_max": 40,
                    "present": True,
                    "conscious": True,
                    "hidden": False,
                },
                "Hidden_Assassin": {
                    "name": "Hidden Assassin",
                    "hp": 30,
                    "hp_max": 30,
                    "present": True,
                    "conscious": True,
                    "hidden": True,
                },
            },
            "location": "The Silver Stag Tavern",
            "world_data": {"current_location_name": "The Silver Stag Tavern"},
        }

    def test_step1_structured_generation_prompt_creation(self):
        """Step 1: Create structured generation prompt with entity manifest"""
        print("\n🔧 Step 1: Creating structured generation prompt")

        # Create entity manifest
        manifest = create_from_game_state(
            self.game_state, session_number=2, turn_number=15
        )
        expected_entities = manifest.get_expected_entities()
        manifest_text = manifest.to_prompt_format()

        # Should exclude hidden entities
        self.assertIn("Gideon", expected_entities)
        self.assertIn("Sariel", expected_entities)
        self.assertIn("Rowan", expected_entities)
        self.assertNotIn("Hidden Assassin", expected_entities)

        # Create structured prompt injection
        structured_prompt = create_structured_prompt_injection(
            manifest_text, expected_entities
        )

        # Verify prompt contains all required components
        self.assertIn("=== SCENE MANIFEST ===", structured_prompt)
        self.assertIn("CRITICAL ENTITY TRACKING REQUIREMENT", structured_prompt)
        # JSON format instructions are now handled automatically by always-JSON mode
        self.assertIn("Gideon, Sariel, Rowan", structured_prompt)

        print(f"   ✅ Expected entities: {expected_entities}")
        print(f"   ✅ Prompt injection created ({len(structured_prompt)} chars)")

        return structured_prompt, expected_entities

    def test_step2_structured_response_parsing(self):
        """Step 2: Parse structured JSON response from LLM"""
        print("\n🔧 Step 2: Parsing structured JSON response")

        # Simulate perfect LLM response
        mock_llm_response = {
            "narrative": "The tension in the Silver Stag Tavern was palpable. Gideon gripped his sword hilt, his wounded shoulder still causing him pain. Sariel stood beside him, her magic crackling faintly around her fingers as she scanned the room for threats. Rowan stepped forward, placing a protective hand on both their shoulders. 'We need to move quickly,' she whispered, 'before they find us here.'",
            "entities_mentioned": ["Gideon", "Sariel", "Rowan"],
            "location_confirmed": "The Silver Stag Tavern",
        }

        # Convert to JSON string (as LLM would return)
        response_text = json.dumps(mock_llm_response)

        # Parse structured response
        narrative, structured_response = parse_structured_response(response_text)

        # Validate parsing
        self.assertEqual(narrative, mock_llm_response["narrative"])
        self.assertIsInstance(structured_response, NarrativeResponse)
        self.assertEqual(
            structured_response.entities_mentioned,
            mock_llm_response["entities_mentioned"],
        )
        self.assertEqual(
            structured_response.location_confirmed,
            mock_llm_response["location_confirmed"],
        )

        print("   ✅ JSON parsed successfully")
        print(f"   ✅ Narrative extracted ({len(narrative)} chars)")
        print(f"   ✅ Entities found: {structured_response.entities_mentioned}")

        return narrative, structured_response

    def test_step3_schema_validation(self):
        """Step 3: Validate structured response against expected schema"""
        print("\n🔧 Step 3: Schema validation of structured response")

        # Get expected entities from manifest
        manifest = create_from_game_state(
            self.game_state, session_number=2, turn_number=15
        )
        expected_entities = manifest.get_expected_entities()

        # Create mock response
        structured_response = NarrativeResponse(
            narrative="Gideon, Sariel, and Rowan gathered in the tavern to plan their next move.",
            entities_mentioned=["Gideon", "Sariel", "Rowan"],
            location_confirmed="The Silver Stag Tavern",
        )

        # Validate entity coverage
        coverage_validation = validate_entity_coverage(
            structured_response, expected_entities
        )

        # Check validation results
        self.assertTrue(coverage_validation["schema_valid"])
        self.assertTrue(coverage_validation["narrative_valid"])
        self.assertEqual(coverage_validation["coverage_rate"], 1.0)
        self.assertEqual(len(coverage_validation["missing_from_schema"]), 0)
        self.assertEqual(len(coverage_validation["missing_from_narrative"]), 0)

        print(f"   ✅ Schema validation: {coverage_validation['schema_valid']}")
        print(f"   ✅ Narrative validation: {coverage_validation['narrative_valid']}")
        print(f"   ✅ Coverage rate: {coverage_validation['coverage_rate']:.2f}")

        return coverage_validation

    def test_step4_narrative_sync_validation(self):
        """Step 4: Additional validation with NarrativeSyncValidator"""
        print("\n🔧 Step 4: Additional narrative sync validation")

        # Get expected entities
        manifest = create_from_game_state(
            self.game_state, session_number=2, turn_number=15
        )
        expected_entities = manifest.get_expected_entities()

        # Test narrative
        narrative = "In the Silver Stag Tavern, Gideon looked around nervously. Sariel placed a calming hand on his arm while Rowan kept watch at the door. The three companions knew they were being hunted."

        # Run narrative sync validator
        validator = NarrativeSyncValidator()
        validation_result = validator.validate(
            narrative_text=narrative,
            expected_entities=expected_entities,
            location="The Silver Stag Tavern",
        )

        # Check validation
        self.assertTrue(validation_result.all_entities_present)
        self.assertEqual(len(validation_result.entities_missing), 0)
        self.assertGreaterEqual(validation_result.confidence, 0.9)

        print(f"   ✅ All entities present: {validation_result.all_entities_present}")
        print(f"   ✅ Entities found: {validation_result.entities_found}")
        print(f"   ✅ Confidence: {validation_result.confidence:.2f}")

        return validation_result

    def test_complete_combined_approach_integration(self):
        """Test complete Combined approach integration flow"""
        print("\n🚀 Complete Combined Approach Integration Test")
        print("=" * 60)

        # Step 1: Structured Generation
        structured_prompt, expected_entities = (
            self.test_step1_structured_generation_prompt_creation()
        )

        # Step 2: Response Parsing
        narrative, structured_response = self.test_step2_structured_response_parsing()

        # Step 3: Schema Validation
        coverage_validation = self.test_step3_schema_validation()

        # Step 4: Narrative Sync Validation
        sync_validation = self.test_step4_narrative_sync_validation()

        # Final assessment
        print("\n📊 Combined Approach Results:")
        print("   🎯 Structured Generation: ✅ PASS")
        print("   🎯 Response Parsing: ✅ PASS")
        print("   🎯 Schema Validation: ✅ PASS (100% coverage)")
        print(
            f"   🎯 Sync Validation: ✅ PASS ({sync_validation.confidence:.0%} confidence)"
        )
        print("   🎯 Overall: ✅ 100% SUCCESS")

        # Assert final success
        self.assertTrue(coverage_validation["schema_valid"])
        self.assertTrue(sync_validation.all_entities_present)
        self.assertEqual(coverage_validation["coverage_rate"], 1.0)

        print("\n🎉 Combined Approach Implementation VERIFIED!")
        print("   The Cassian Problem is SOLVED!")

    def test_failure_case_handling(self):
        """Test how the system handles failure cases"""
        print("\n🧪 Testing failure case handling")

        # Test case where LLM doesn't return JSON and misses entities clearly
        plain_text_response = "The lone warrior stood in the empty tavern, contemplating his next move. No companions were with him."

        # Parse should fall back gracefully
        narrative, structured_response = parse_structured_response(plain_text_response)

        self.assertEqual(narrative, plain_text_response)
        self.assertIsInstance(structured_response, NarrativeResponse)
        self.assertEqual(
            structured_response.entities_mentioned, []
        )  # Empty for fallback

        # Validation should still work on the narrative text
        expected_entities = ["Gideon", "Sariel", "Rowan"]
        validator = NarrativeSyncValidator()
        result = validator.validate(narrative, expected_entities)

        # Should detect missing entities (all entities missing in this case)
        self.assertFalse(result.all_entities_present)
        self.assertGreater(len(result.entities_missing), 0)

        print("   ✅ Graceful fallback for non-JSON response")
        print(
            f"   ✅ Validation still detects missing entities: {result.entities_missing}"
        )


if __name__ == "__main__":
    print("🎯 Complete Combined Approach Implementation Test")
    print("Testing Milestone 1: Production Entity Tracking")
    print("=" * 70)

    unittest.main(verbosity=2)
