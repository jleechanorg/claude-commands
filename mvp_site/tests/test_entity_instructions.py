"""
Unit tests for Enhanced Explicit Entity Instructions (Option 5 Enhanced)
Tests entity instruction generation and enforcement checking.
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

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
            assert category in templates
            assert isinstance(templates[category], dict)
            assert len(templates[category]) > 0

    def test_build_entity_priorities(self):
        """Test that entity priorities are properly configured"""
        priorities = self.generator._build_entity_priorities()

        assert priorities["player_character"] == 1
        assert priorities["npc_referenced"] == 1
        assert priorities["location_owner"] == 1
        assert priorities["story_critical"] == 2
        assert priorities["background"] == 3

    def test_generate_entity_instructions_empty_entities(self):
        """Test instruction generation with empty entity list"""
        result = self.generator.generate_entity_instructions([], [])

        assert result == ""

    def test_generate_entity_instructions_basic(self):
        """Test basic entity instruction generation"""
        entities = ["Sariel", "Cassian"]
        player_references = ["Cassian"]

        result = self.generator.generate_entity_instructions(
            entities, player_references
        )

        assert "=== MANDATORY ENTITY REQUIREMENTS ===" in result
        assert "REQUIRED and MUST appear" in result
        assert "Sariel" in result
        assert "Cassian" in result
        assert "DO NOT complete your response without including" in result
        assert "The player specifically mentioned Cassian" in result

    def test_generate_entity_instructions_with_location(self):
        """Test entity instruction generation with location"""
        entities = ["Sariel", "Valerius"]
        result = self.generator.generate_entity_instructions(
            entities, [], location="Valerius's Study"
        )

        assert "Valerius" in result
        # Valerius should be mandatory in his own study
        assert "MANDATORY ENTITY REQUIREMENTS" in result

    def test_create_entity_instruction_player_character(self):
        """Test entity instruction creation for player characters"""
        instruction = self.generator._create_entity_instruction(
            "Sariel", [], None, None
        )

        assert instruction.entity_name == "Sariel"
        assert instruction.instruction_type == "background"
        assert instruction.priority == 3
        assert "should be acknowledged" in instruction.specific_instruction

    def test_create_entity_instruction_npc_referenced(self):
        """Test entity instruction creation for referenced NPCs"""
        instruction = self.generator._create_entity_instruction(
            "Cassian", ["Cassian"], None, None
        )

        assert instruction.entity_name == "Cassian"
        assert instruction.instruction_type == "mandatory"
        assert instruction.priority == 1
        assert "directly referenced" in instruction.specific_instruction
        assert "narrative continuity" in instruction.specific_instruction

    def test_create_entity_instruction_location_owner(self):
        """Test entity instruction creation for location owners"""
        instruction = self.generator._create_entity_instruction(
            "Valerius", [], "Valerius's Study", None
        )

        assert instruction.entity_name == "Valerius"
        assert instruction.instruction_type == "background"
        assert instruction.priority == 3
        assert "should be acknowledged" in instruction.specific_instruction

    def test_create_entity_instruction_background(self):
        """Test entity instruction creation for background entities"""
        instruction = self.generator._create_entity_instruction(
            "Random Guard", [], None, None
        )

        assert instruction.entity_name == "Random Guard"
        assert instruction.instruction_type == "background"
        assert instruction.priority == 3

    def test_create_entity_instruction_cassian_emotional(self):
        """Test special Cassian emotional handling"""
        instruction = self.generator._create_entity_instruction(
            "Cassian", ["scared", "helpless"], None, None
        )

        # No special Cassian handling - falls to background
        assert instruction.instruction_type == "background"
        assert instruction.priority == 3

    def test_is_player_character(self):
        """Test player character detection"""
        # Method now returns False for all entities (no hardcoding)
        assert not self.generator._is_player_character("Sariel")
        assert not self.generator._is_player_character("SARIEL")
        assert not self.generator._is_player_character("Cassian")

    def test_is_location_owner_valerius(self):
        """Test location owner detection for Valerius"""
        # Method now returns False for all (no hardcoding)
        assert not self.generator._is_location_owner("Valerius", "Valerius's Study")
        assert not self.generator._is_location_owner("Valerius", "The Grand Study")
        assert not self.generator._is_location_owner("Valerius", "Throne Room")

    def test_is_location_owner_cressida(self):
        """Test location owner detection for Lady Cressida"""
        # Method now returns False for all (no hardcoding)
        assert not self.generator._is_location_owner("Lady Cressida", "Lady Cressida's Chambers")
        assert not self.generator._is_location_owner("Cressida", "Private Chambers")
        assert not self.generator._is_location_owner("Cressida", "Throne Room")

    def test_create_cassian_specific_instruction_emotional(self):
        """Test Cassian-specific instruction for emotional context"""
        result = self.generator.create_entity_specific_instruction(
            "Cassian", "Tell Cassian I was scared and helpless"
        )

        assert "CRITICAL" in result
        assert "emotional appeal" in result
        assert "vulnerable moment" in result
        assert "MUST appear and respond" in result

    def test_create_cassian_specific_instruction_normal(self):
        """Test Cassian-specific instruction for normal reference"""
        result = self.generator.create_entity_specific_instruction(
            "Cassian", "Where is Cassian?"
        )

        assert "IMPORTANT" in result
        assert "directly mentioned" in result
        assert "CRITICAL" not in result

    def test_create_cassian_specific_instruction_no_reference(self):
        """Test Cassian-specific instruction when not referenced"""
        result = self.generator.create_entity_specific_instruction(
            "Cassian", "Look around the room"
        )

        assert result == ""

    def test_create_location_specific_instructions(self):
        """Test location-specific instruction generation"""
        result = self.generator.create_location_specific_instructions(
            "Throne Room", ["Sariel", "Guard Captain"]
        )

        assert "LOCATION REQUIREMENT for Throne Room" in result
        assert "court setting" in result.lower()

    def test_create_location_specific_instructions_valerius_study(self):
        """Test location-specific instructions for Valerius's study"""
        result = self.generator.create_location_specific_instructions(
            "Valerius's Study", ["Valerius"]
        )

        # Generic location instructions now
        assert "LOCATION REQUIREMENT" in result
        assert "Valerius's Study" in result


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
            assert category in patterns
            assert isinstance(patterns[category], list)
            assert len(patterns[category]) > 0

    def test_check_instruction_compliance_success(self):
        """Test successful instruction compliance checking"""
        narrative = "Sariel draws her sword while Cassian watches nervously."
        mandatory_entities = ["Sariel", "Cassian"]

        result = self.checker.check_instruction_compliance(
            narrative, mandatory_entities
        )

        assert result["overall_compliance"]
        assert set(result["compliant_entities"]) == set(mandatory_entities)
        assert len(result["non_compliant_entities"]) == 0

    def test_check_instruction_compliance_failure(self):
        """Test failed instruction compliance checking"""
        narrative = "Sariel looks around the empty room."
        mandatory_entities = ["Sariel", "Cassian", "Lady Cressida"]

        result = self.checker.check_instruction_compliance(
            narrative, mandatory_entities
        )

        assert not result["overall_compliance"]
        assert "Sariel" in result["compliant_entities"]
        assert "Cassian" in result["non_compliant_entities"]
        assert "Lady Cressida" in result["non_compliant_entities"]

    def test_check_entity_compliance_present_with_dialogue(self):
        """Test entity compliance detection with dialogue"""
        narrative = 'cassian says "i understand the situation"'

        compliance = self.checker._check_entity_compliance(narrative, "Cassian")

        assert compliance["present"]
        assert compliance["has_dialogue"]
        assert compliance["mention_count"] == 1

    def test_check_entity_compliance_present_with_action(self):
        """Test entity compliance detection with action"""
        narrative = "cassian moves quickly across the room"

        compliance = self.checker._check_entity_compliance(narrative, "Cassian")

        assert compliance["present"]
        assert compliance["has_action"]
        assert compliance["mention_count"] == 1

    def test_check_entity_compliance_not_present(self):
        """Test entity compliance when entity is not present"""
        narrative = "sariel looks around the empty room"

        compliance = self.checker._check_entity_compliance(narrative, "Cassian")

        assert not compliance["present"]
        assert not compliance["has_dialogue"]
        assert not compliance["has_action"]
        assert compliance["mention_count"] == 0

    def test_check_entity_compliance_multiple_mentions(self):
        """Test entity compliance with multiple mentions"""
        narrative = "cassian speaks to sariel. later, cassian nods in agreement."

        compliance = self.checker._check_entity_compliance(narrative, "Cassian")

        assert compliance["present"]
        assert compliance["mention_count"] == 2


class TestEntityInstructionDataClass(unittest.TestCase):
    def test_entity_instruction_creation(self):
        """Test EntityInstruction dataclass creation"""
        instruction = EntityInstruction(
            entity_name="Sariel",
            instruction_type="mandatory",
            specific_instruction="Player character must be present",
            priority=1,
        )

        assert instruction.entity_name == "Sariel"
        assert instruction.instruction_type == "mandatory"
        assert instruction.specific_instruction == "Player character must be present"
        assert instruction.priority == 1


class TestGlobalInstances(unittest.TestCase):
    def test_global_entity_instruction_generator_exists(self):
        """Test that global entity instruction generator instance exists"""
        assert isinstance(entity_instruction_generator, EntityInstructionGenerator)

    def test_global_entity_enforcement_checker_exists(self):
        """Test that global entity enforcement checker instance exists"""
        assert isinstance(entity_enforcement_checker, EntityEnforcementChecker)


if __name__ == "__main__":
    unittest.main()
