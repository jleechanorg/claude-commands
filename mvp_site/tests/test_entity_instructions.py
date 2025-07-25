"""
Unit tests for Enhanced Explicit Entity Instructions (Option 5 Enhanced)
Tests entity instruction generation and enforcement checking.
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

from entity_instructions import (
    EntityEnforcementChecker,
    EntityInstruction,
    EntityInstructionGenerator,
    entity_enforcement_checker,
    entity_instruction_generator,
)


class TestEntityInstructionGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = EntityInstructionGenerator()

    def test_build_instruction_templates(self):
        """Test that instruction templates are properly built"""
        templates = self.generator._build_instruction_templates()

        expected_categories = [
            "player_character",
            "npc_referenced",
            "location_npc",
            "story_critical",
            "background",
        ]
        for category in expected_categories:
            self.assertIn(category, templates)
            self.assertIsInstance(templates[category], dict)
            self.assertGreater(len(templates[category]), 0)

    def test_build_entity_priorities(self):
        """Test that entity priorities are properly configured"""
        priorities = self.generator._build_entity_priorities()

        self.assertEqual(priorities["player_character"], 1)
        self.assertEqual(priorities["npc_referenced"], 1)
        self.assertEqual(priorities["location_owner"], 1)
        self.assertEqual(priorities["story_critical"], 2)
        self.assertEqual(priorities["background"], 3)

    def test_generate_entity_instructions_empty_entities(self):
        """Test instruction generation with empty entity list"""
        result = self.generator.generate_entity_instructions([], [])

        self.assertEqual(result, "")

    def test_generate_entity_instructions_basic(self):
        """Test basic entity instruction generation"""
        entities = ["Sariel", "Cassian"]
        player_references = ["Cassian"]

        result = self.generator.generate_entity_instructions(
            entities, player_references
        )

        self.assertIn("=== MANDATORY ENTITY REQUIREMENTS ===", result)
        self.assertIn("REQUIRED and MUST appear", result)
        self.assertIn("Sariel", result)
        self.assertIn("Cassian", result)
        self.assertIn("DO NOT complete your response without including", result)
        self.assertIn("The player specifically mentioned Cassian", result)

    def test_generate_entity_instructions_with_location(self):
        """Test entity instruction generation with location"""
        entities = ["Sariel", "Valerius"]
        result = self.generator.generate_entity_instructions(
            entities, [], location="Valerius's Study"
        )

        self.assertIn("Valerius", result)
        # Valerius should be mandatory in his own study
        self.assertIn("MANDATORY ENTITY REQUIREMENTS", result)

    def test_create_entity_instruction_player_character(self):
        """Test entity instruction creation for player characters"""
        instruction = self.generator._create_entity_instruction(
            "Sariel", [], None, None
        )

        self.assertEqual(instruction.entity_name, "Sariel")
        self.assertEqual(instruction.instruction_type, "background")
        self.assertEqual(instruction.priority, 3)
        self.assertIn("should be acknowledged", instruction.specific_instruction)

    def test_create_entity_instruction_npc_referenced(self):
        """Test entity instruction creation for referenced NPCs"""
        instruction = self.generator._create_entity_instruction(
            "Cassian", ["Cassian"], None, None
        )

        self.assertEqual(instruction.entity_name, "Cassian")
        self.assertEqual(instruction.instruction_type, "mandatory")
        self.assertEqual(instruction.priority, 1)
        self.assertIn("directly referenced", instruction.specific_instruction)
        self.assertIn("narrative continuity", instruction.specific_instruction)

    def test_create_entity_instruction_location_owner(self):
        """Test entity instruction creation for location owners"""
        instruction = self.generator._create_entity_instruction(
            "Valerius", [], "Valerius's Study", None
        )

        self.assertEqual(instruction.entity_name, "Valerius")
        self.assertEqual(instruction.instruction_type, "background")
        self.assertEqual(instruction.priority, 3)
        self.assertIn("should be acknowledged", instruction.specific_instruction)

    def test_create_entity_instruction_background(self):
        """Test entity instruction creation for background entities"""
        instruction = self.generator._create_entity_instruction(
            "Random Guard", [], None, None
        )

        self.assertEqual(instruction.entity_name, "Random Guard")
        self.assertEqual(instruction.instruction_type, "background")
        self.assertEqual(instruction.priority, 3)

    def test_create_entity_instruction_cassian_emotional(self):
        """Test special Cassian emotional handling"""
        instruction = self.generator._create_entity_instruction(
            "Cassian", ["scared", "helpless"], None, None
        )

        # No special Cassian handling - falls to background
        self.assertEqual(instruction.instruction_type, "background")
        self.assertEqual(instruction.priority, 3)

    def test_is_player_character(self):
        """Test player character detection"""
        # Method now returns False for all entities (no hardcoding)
        self.assertFalse(self.generator._is_player_character("Sariel"))
        self.assertFalse(self.generator._is_player_character("SARIEL"))
        self.assertFalse(self.generator._is_player_character("Cassian"))

    def test_is_location_owner_valerius(self):
        """Test location owner detection for Valerius"""
        # Method now returns False for all (no hardcoding)
        self.assertFalse(
            self.generator._is_location_owner("Valerius", "Valerius's Study")
        )
        self.assertFalse(
            self.generator._is_location_owner("Valerius", "The Grand Study")
        )
        self.assertFalse(self.generator._is_location_owner("Valerius", "Throne Room"))

    def test_is_location_owner_cressida(self):
        """Test location owner detection for Lady Cressida"""
        # Method now returns False for all (no hardcoding)
        self.assertFalse(
            self.generator._is_location_owner(
                "Lady Cressida", "Lady Cressida's Chambers"
            )
        )
        self.assertFalse(
            self.generator._is_location_owner("Cressida", "Private Chambers")
        )
        self.assertFalse(self.generator._is_location_owner("Cressida", "Throne Room"))

    def test_create_cassian_specific_instruction_emotional(self):
        """Test Cassian-specific instruction for emotional context"""
        result = self.generator.create_entity_specific_instruction(
            "Cassian", "Tell Cassian I was scared and helpless"
        )

        self.assertIn("CRITICAL", result)
        self.assertIn("emotional appeal", result)
        self.assertIn("vulnerable moment", result)
        self.assertIn("MUST appear and respond", result)

    def test_create_cassian_specific_instruction_normal(self):
        """Test Cassian-specific instruction for normal reference"""
        result = self.generator.create_entity_specific_instruction(
            "Cassian", "Where is Cassian?"
        )

        self.assertIn("IMPORTANT", result)
        self.assertIn("directly mentioned", result)
        self.assertNotIn("CRITICAL", result)

    def test_create_cassian_specific_instruction_no_reference(self):
        """Test Cassian-specific instruction when not referenced"""
        result = self.generator.create_entity_specific_instruction(
            "Cassian", "Look around the room"
        )

        self.assertEqual(result, "")

    def test_create_location_specific_instructions(self):
        """Test location-specific instruction generation"""
        result = self.generator.create_location_specific_instructions(
            "Throne Room", ["Sariel", "Guard Captain"]
        )

        self.assertIn("LOCATION REQUIREMENT for Throne Room", result)
        self.assertIn("court setting", result.lower())

    def test_create_location_specific_instructions_valerius_study(self):
        """Test location-specific instructions for Valerius's study"""
        result = self.generator.create_location_specific_instructions(
            "Valerius's Study", ["Valerius"]
        )

        # Generic location instructions now
        self.assertIn("LOCATION REQUIREMENT", result)
        self.assertIn("Valerius's Study", result)


class TestEntityEnforcementChecker(unittest.TestCase):
    def setUp(self):
        self.checker = EntityEnforcementChecker()

    def test_build_compliance_patterns(self):
        """Test that compliance patterns are properly built"""
        patterns = self.checker._build_compliance_patterns()

        expected_categories = [
            "presence_indicators",
            "action_indicators",
            "dialogue_indicators",
        ]
        for category in expected_categories:
            self.assertIn(category, patterns)
            self.assertIsInstance(patterns[category], list)
            self.assertGreater(len(patterns[category]), 0)

    def test_check_instruction_compliance_success(self):
        """Test successful instruction compliance checking"""
        narrative = "Sariel draws her sword while Cassian watches nervously."
        mandatory_entities = ["Sariel", "Cassian"]

        result = self.checker.check_instruction_compliance(
            narrative, mandatory_entities
        )

        self.assertTrue(result["overall_compliance"])
        self.assertEqual(set(result["compliant_entities"]), set(mandatory_entities))
        self.assertEqual(len(result["non_compliant_entities"]), 0)

    def test_check_instruction_compliance_failure(self):
        """Test failed instruction compliance checking"""
        narrative = "Sariel looks around the empty room."
        mandatory_entities = ["Sariel", "Cassian", "Lady Cressida"]

        result = self.checker.check_instruction_compliance(
            narrative, mandatory_entities
        )

        self.assertFalse(result["overall_compliance"])
        self.assertIn("Sariel", result["compliant_entities"])
        self.assertIn("Cassian", result["non_compliant_entities"])
        self.assertIn("Lady Cressida", result["non_compliant_entities"])

    def test_check_entity_compliance_present_with_dialogue(self):
        """Test entity compliance detection with dialogue"""
        narrative = 'cassian says "i understand the situation"'

        compliance = self.checker._check_entity_compliance(narrative, "Cassian")

        self.assertTrue(compliance["present"])
        self.assertTrue(compliance["has_dialogue"])
        self.assertEqual(compliance["mention_count"], 1)

    def test_check_entity_compliance_present_with_action(self):
        """Test entity compliance detection with action"""
        narrative = "cassian moves quickly across the room"

        compliance = self.checker._check_entity_compliance(narrative, "Cassian")

        self.assertTrue(compliance["present"])
        self.assertTrue(compliance["has_action"])
        self.assertEqual(compliance["mention_count"], 1)

    def test_check_entity_compliance_not_present(self):
        """Test entity compliance when entity is not present"""
        narrative = "sariel looks around the empty room"

        compliance = self.checker._check_entity_compliance(narrative, "Cassian")

        self.assertFalse(compliance["present"])
        self.assertFalse(compliance["has_dialogue"])
        self.assertFalse(compliance["has_action"])
        self.assertEqual(compliance["mention_count"], 0)

    def test_check_entity_compliance_multiple_mentions(self):
        """Test entity compliance with multiple mentions"""
        narrative = "cassian speaks to sariel. later, cassian nods in agreement."

        compliance = self.checker._check_entity_compliance(narrative, "Cassian")

        self.assertTrue(compliance["present"])
        self.assertEqual(compliance["mention_count"], 2)


class TestEntityInstructionDataClass(unittest.TestCase):
    def test_entity_instruction_creation(self):
        """Test EntityInstruction dataclass creation"""
        instruction = EntityInstruction(
            entity_name="Sariel",
            instruction_type="mandatory",
            specific_instruction="Player character must be present",
            priority=1,
        )

        self.assertEqual(instruction.entity_name, "Sariel")
        self.assertEqual(instruction.instruction_type, "mandatory")
        self.assertEqual(
            instruction.specific_instruction, "Player character must be present"
        )
        self.assertEqual(instruction.priority, 1)


class TestGlobalInstances(unittest.TestCase):
    def test_global_entity_instruction_generator_exists(self):
        """Test that global entity instruction generator instance exists"""
        self.assertIsInstance(entity_instruction_generator, EntityInstructionGenerator)

    def test_global_entity_enforcement_checker_exists(self):
        """Test that global entity enforcement checker instance exists"""
        self.assertIsInstance(entity_enforcement_checker, EntityEnforcementChecker)


if __name__ == "__main__":
    unittest.main()
