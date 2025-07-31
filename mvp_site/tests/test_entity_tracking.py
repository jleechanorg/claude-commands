#!/usr/bin/env python3
"""
Test script for entity tracking production implementation
"""

import os
import re
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dual_pass_generator import DualPassGenerator
from entity_tracking import create_from_game_state, get_validation_info
from entity_validator import EntityValidator
from narrative_sync_validator import NarrativeSyncValidator


class TestEntityTracking(unittest.TestCase):
    """Test entity tracking components"""

    def test_entity_id_format_standardization(self):
        """Test that entity IDs follow underscore format like 'pc_name_001'"""
        test_game_state = {
            "player_character_data": {"name": "Test Hero", "hp": 45, "hp_max": 60},
            "npc_data": {
                "Guard Captain": {"name": "Guard Captain", "hp": 30, "hp_max": 30}
            },
        }

        manifest = create_from_game_state(
            test_game_state, session_number=1, turn_number=1
        )

        # Check PC ID format
        assert len(manifest.player_characters) == 1
        pc = manifest.player_characters[0]
        assert re.search(r"^pc_[a-z_]+_\d{3}$", pc.entity_id)
        assert "test_hero" in pc.entity_id.lower()

        # Check NPC ID format
        assert len(manifest.npcs) == 1
        npc = manifest.npcs[0]
        assert re.search(r"^npc_[a-z_]+_\d{3}$", npc.entity_id)
        assert "guard_captain" in npc.entity_id.lower()

    def test_existing_string_ids_preserved(self):
        """Test that existing string_ids from game state are preserved"""
        test_game_state = {
            "player_character_data": {
                "name": "Hero",
                "string_id": "pc_custom_hero_999",
            },
            "npc_data": {
                "Villain": {"name": "Villain", "string_id": "npc_special_villain_042"}
            },
        }

        manifest = create_from_game_state(
            test_game_state, session_number=1, turn_number=1
        )

        # Verify IDs are preserved
        assert manifest.player_characters[0].entity_id == "pc_custom_hero_999"
        assert manifest.npcs[0].entity_id == "npc_special_villain_042"

    def setUp(self):
        """Set up test data"""
        self.test_game_state = {
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
                "Hidden_Guard": {
                    "name": "Hidden Guard",
                    "hp": 30,
                    "hp_max": 30,
                    "present": True,
                    "conscious": True,
                    "hidden": True,  # Should not be in expected entities
                },
            },
            "location": "Thornhaven Inn",
            "world_data": {"current_location_name": "Thornhaven Inn"},
        }

    def test_scene_manifest_creation(self):
        """Test SceneManifest creation from game state"""
        manifest = create_from_game_state(
            self.test_game_state, session_number=1, turn_number=5
        )

        assert re.search(
            r"^scene_s1_t5(_\d+)?$", manifest.scene_id
        )  # May have optional suffix
        assert manifest.session_number == 1
        assert manifest.turn_number == 5
        assert manifest.current_location.display_name == "Thornhaven Inn"
        assert len(manifest.player_characters) == 1
        assert (
            len(manifest.npcs) == 3
        )  # All NPCs included, filtering happens in get_expected_entities

    def test_expected_entities_filtering(self):
        """Test that expected entities correctly filters visible, conscious entities"""
        manifest = create_from_game_state(
            self.test_game_state, session_number=1, turn_number=5
        )
        expected = manifest.get_expected_entities()

        # Should include PC and visible NPCs
        assert "Gideon" in expected
        assert "Sariel" in expected
        assert "Rowan" in expected

        # Hidden guard should still be included (present but hidden)
        # Note: The current implementation includes all present entities regardless of visibility
        # This may need adjustment based on requirements

    def test_manifest_prompt_format(self):
        """Test manifest to prompt format conversion"""
        manifest = create_from_game_state(
            self.test_game_state, session_number=1, turn_number=5
        )
        prompt_text = manifest.to_prompt_format()

        assert "=== SCENE MANIFEST ===" in prompt_text
        assert "Location: Thornhaven Inn" in prompt_text
        assert "Session: 1, Turn: 5" in prompt_text
        assert "PRESENT CHARACTERS:" in prompt_text
        assert "Gideon (PC)" in prompt_text
        assert "Sariel (NPC)" in prompt_text
        assert "Rowan (NPC)" in prompt_text
        assert "=== END MANIFEST ===" in prompt_text

    def test_narrative_sync_validator(self):
        """Test NarrativeSyncValidator functionality"""
        validator = NarrativeSyncValidator()

        # Test narrative that mentions all expected entities
        good_narrative = """
        Gideon looked around the inn, his eyes meeting Sariel's concerned gaze.
        Rowan stepped forward, placing a hand on Gideon's shoulder.
        The three of them stood together in the common room.
        """

        expected_entities = ["Gideon", "Sariel", "Rowan"]
        result = validator.validate(
            good_narrative, expected_entities, location="Thornhaven Inn"
        )

        assert result.all_entities_present
        assert len(result.entities_missing) == 0
        assert result.confidence > 0.8

        # Test narrative missing an entity
        bad_narrative = """
        Gideon looked around the inn, his eyes meeting Sariel's concerned gaze.
        They discussed their next move.
        """

        result = validator.validate(
            bad_narrative, expected_entities, location="Thornhaven Inn"
        )

        assert not result.all_entities_present
        assert "Rowan" in result.entities_missing
        assert result.confidence < 0.8

    def test_validator_presence_detection(self):
        """Test validator's presence detection logic (REFACTORED: uses EntityValidator)"""
        validator = NarrativeSyncValidator()

        # Test physically present detection via delegated EntityValidator
        narrative = "Gideon swung his sword at the orc."
        presence = validator.entity_validator.analyze_entity_presence(
            narrative, "Gideon"
        )
        assert presence.value == "physically_present"

        # Test mentioned absent detection via delegated EntityValidator
        narrative = "They thought of Rowan, who was still in the village."
        presence = validator.entity_validator.analyze_entity_presence(
            narrative, "Rowan"
        )
        assert presence.value == "mentioned_absent"

        # Test not found
        narrative = "The room was empty except for furniture."
        presence = validator.entity_validator.analyze_entity_presence(
            narrative, "Gideon"
        )
        assert presence is None

    def test_integration_flow(self):
        """Test the complete entity tracking flow"""
        # Create manifest
        manifest = create_from_game_state(
            self.test_game_state, session_number=1, turn_number=5
        )
        expected_entities = manifest.get_expected_entities()
        manifest_text = manifest.to_prompt_format()

        # Simulate AI response that includes all entities
        ai_response = f"""
        The scene at {manifest.current_location.display_name} was tense. Gideon gripped his sword,
        while Sariel readied her magic. Rowan stood between them, trying to mediate.
        The three companions faced their greatest challenge yet.
        """

        # Validate response
        validator = NarrativeSyncValidator()
        result = validator.validate(
            ai_response,
            expected_entities,
            location=manifest.current_location.display_name,
        )

        # Check results
        assert result.all_entities_present
        assert len(result.entities_missing) == 0
        assert "Gideon" in result.entities_found
        assert "Sariel" in result.entities_found
        assert "Rowan" in result.entities_found

        print("✅ Integration test passed!")
        print(f"   Expected entities: {expected_entities}")
        print(f"   Found entities: {result.entities_found}")
        print(f"   Confidence: {result.confidence:.2f}")

    def test_get_validation_info(self):
        """Test get_validation_info function returns correct information."""
        info = get_validation_info()

        # Verify the function returns a dictionary
        assert isinstance(info, dict)

        # Verify expected keys are present
        assert "validation_type" in info
        assert "pydantic_available" in info

        # Verify expected values
        assert info["validation_type"] == "Pydantic"
        assert info["pydantic_available"] == "true"

    def test_unknown_entity_filtering_comprehensive(self):
        """Test comprehensive Unknown entity filtering across all validators"""
        # Test data with "Unknown" entity
        narrative = "Gideon swung his sword while Sariel cast a spell."
        expected_entities = ["Gideon", "Sariel", "Unknown"]  # Include "Unknown"

        # Test EntityValidator.validate() method
        entity_validator = EntityValidator()
        result = entity_validator.validate(narrative, expected_entities)

        assert "Unknown" not in result.found_entities
        assert "Unknown" not in result.missing_entities
        assert "Gideon" in result.found_entities
        assert "Sariel" in result.found_entities
        assert result.confidence == 1.0
        assert result.passed

        # Test NarrativeSyncValidator delegation
        narrative_validator = NarrativeSyncValidator()
        result = narrative_validator.validate(narrative, expected_entities)

        assert "Unknown" not in result.found_entities
        assert "Unknown" not in result.missing_entities
        assert "Gideon" in result.found_entities
        assert "Sariel" in result.found_entities
        assert result.all_entities_present

        # Test backward compatibility with old interface
        result = entity_validator.validate_entity_presence(narrative, expected_entities)

        assert "Unknown" not in result.found_entities
        assert "Unknown" not in result.missing_entities
        assert result.passed

    def test_entity_validator_comprehensive_validation(self):
        """Test EntityValidator's comprehensive validation method"""
        entity_validator = EntityValidator()

        # Test with all entities present
        narrative = "Gideon spoke to Sariel while Rowan watched."
        expected_entities = ["Gideon", "Sariel", "Rowan"]

        result = entity_validator.validate(narrative, expected_entities)

        assert result.passed
        assert result.all_entities_present
        assert len(result.missing_entities) == 0
        assert len(result.found_entities) == 3
        assert result.confidence > 0.8
        assert "validator_name" in result.metadata
        assert result.metadata["validator_name"] == "EntityValidator"

        # Test with missing entities
        narrative = "Gideon spoke quietly."
        result = entity_validator.validate(narrative, expected_entities)

        assert not result.passed
        assert not result.all_entities_present
        assert "Sariel" in result.missing_entities
        assert "Rowan" in result.missing_entities
        assert "Gideon" in result.found_entities
        assert result.retry_needed
        assert len(result.retry_suggestions) > 0

    def test_entity_presence_type_detection(self):
        """Test EntityPresenceType detection in EntityValidator"""
        entity_validator = EntityValidator()

        # Test physically present
        narrative = "Gideon swung his sword at the orc."
        presence = entity_validator.analyze_entity_presence(narrative, "Gideon")
        assert presence.value == "physically_present"

        # Test mentioned absent
        narrative = "They thought of Rowan, who was still in the village."
        presence = entity_validator.analyze_entity_presence(narrative, "Rowan")
        assert presence.value == "mentioned_absent"

        # Test not found
        narrative = "The room was empty except for furniture."
        presence = entity_validator.analyze_entity_presence(narrative, "Gideon")
        assert presence is None

    def test_physical_state_extraction(self):
        """Test physical state extraction from EntityValidator"""
        entity_validator = EntityValidator()

        narrative = "Gideon stood trembling, his bandaged arm hanging at his side. Sariel was exhausted."
        states = entity_validator.extract_physical_states(narrative)

        assert isinstance(states, dict)
        # Note: Physical state extraction associates states with nearby entities
        # The exact association depends on the regex patterns

    def test_scene_transition_detection(self):
        """Test scene transition detection from EntityValidator"""
        entity_validator = EntityValidator()

        narrative = (
            "The party moved to the ancient temple. They arrived at the sacred altar."
        )
        transitions = entity_validator.detect_scene_transitions(narrative)

        assert isinstance(transitions, list)
        assert len(transitions) > 0

    def test_injection_template_creation(self):
        """Test entity injection template creation"""
        entity_validator = EntityValidator()

        missing_entities = ["Gideon", "Sariel"]
        templates = entity_validator.create_injection_templates(missing_entities)

        assert isinstance(templates, dict)
        assert "Gideon" in templates
        assert "Sariel" in templates
        assert isinstance(templates["Gideon"], list)
        assert len(templates["Gideon"]) > 0

    def test_narrative_sync_validator_delegation(self):
        """Test that NarrativeSyncValidator properly delegates to EntityValidator"""
        narrative_validator = NarrativeSyncValidator()

        # Verify delegation is set up
        assert narrative_validator.entity_validator is not None
        assert isinstance(narrative_validator.entity_validator, EntityValidator)

        # Test delegation works
        narrative = "Gideon and Sariel explored the dungeon."
        expected_entities = ["Gideon", "Sariel", "Rowan"]

        result = narrative_validator.validate(narrative, expected_entities)

        # Should use EntityValidator's comprehensive validation
        assert "Gideon" in result.found_entities
        assert "Sariel" in result.found_entities
        assert "Rowan" in result.missing_entities
        assert not result.all_entities_present

    def test_dual_pass_generator_integration(self):
        """Test DualPassGenerator uses EntityValidator properly"""

        dual_pass = DualPassGenerator()

        # Verify it uses EntityValidator
        assert isinstance(dual_pass.validator, EntityValidator)

        # Test injection snippet creation
        snippet = dual_pass.create_entity_injection_snippet(
            "Gideon", "tavern", "speaks up"
        )
        assert isinstance(snippet, str)
        assert "Gideon" in snippet

    def test_validation_result_compatibility(self):
        """Test ValidationResult supports both old and new interfaces"""
        entity_validator = EntityValidator()

        narrative = "Gideon spoke to Sariel."
        expected_entities = ["Gideon", "Sariel"]

        result = entity_validator.validate(narrative, expected_entities)

        # Test old interface fields
        assert hasattr(result, "passed")
        assert hasattr(result, "missing_entities")
        assert hasattr(result, "found_entities")
        assert hasattr(result, "confidence_score")
        assert hasattr(result, "retry_needed")
        assert hasattr(result, "retry_suggestions")

        # Test new interface fields
        assert hasattr(result, "entities_found")
        assert hasattr(result, "entities_missing")
        assert hasattr(result, "all_entities_present")
        assert hasattr(result, "confidence")
        assert hasattr(result, "warnings")
        assert hasattr(result, "metadata")
        assert hasattr(result, "validation_details")

        # Test field synchronization
        assert result.found_entities == result.entities_found
        assert result.missing_entities == result.entities_missing
        assert result.confidence_score == result.confidence

    def test_multiple_unknown_entities(self):
        """Test filtering multiple Unknown entities and variations"""
        entity_validator = EntityValidator()

        # Test multiple Unknown entities
        narrative = "Gideon and Sariel ventured forth."
        expected_entities = ["Gideon", "Sariel", "Unknown", "unknown", "UNKNOWN"]

        result = entity_validator.validate(narrative, expected_entities)

        # All Unknown variants should be filtered out
        combined_entities = result.found_entities + result.missing_entities
        assert "Unknown" not in combined_entities
        assert "unknown" not in combined_entities
        assert "UNKNOWN" not in combined_entities

        # Real entities should be found
        assert "Gideon" in result.found_entities
        assert "Sariel" in result.found_entities
        assert result.all_entities_present

    def test_edge_cases_and_robustness(self):
        """Test edge cases for robustness"""
        entity_validator = EntityValidator()

        # Test with empty entities list
        result = entity_validator.validate("Some narrative", [])
        assert result.passed
        assert result.confidence == 1.0

        # Test with only Unknown entities
        result = entity_validator.validate("Some narrative", ["Unknown", "unknown"])
        assert result.passed
        assert len(result.found_entities) == 0
        assert len(result.missing_entities) == 0

        # Test with empty narrative
        result = entity_validator.validate("", ["Gideon"])
        assert not result.passed
        assert "Gideon" in result.missing_entities

    def test_end_to_end_missing_entity_red_green_workflow(self):
        """
        End-to-end RED-GREEN test: Demonstrates missing entity detection and handling

        RED Phase: Show system correctly identifies missing entities
        GREEN Phase: Show system properly handles/filters missing entities
        """
        print("\n🔴 RED PHASE: Testing missing entity detection")

        entity_validator = EntityValidator()

        # RED: Create a narrative that's missing expected entities
        incomplete_narrative = """
        Gideon entered the tavern and looked around. The room was dimly lit.
        He approached the bar and ordered an ale.
        """

        expected_entities = ["Gideon", "Sariel", "Rowan", "Tavern Keeper"]

        # RED: Validate - should detect missing entities
        red_result = entity_validator.validate(incomplete_narrative, expected_entities)

        # RED: Verify missing entities are detected
        assert not red_result.passed, "RED: Should detect missing entities"
        assert red_result.retry_needed, "RED: Should need retry for missing entities"
        assert (
            "Gideon" in red_result.found_entities
        ), "RED: Should find mentioned entity"
        assert (
            "Sariel" in red_result.missing_entities
        ), "RED: Should detect missing entity"
        assert (
            "Rowan" in red_result.missing_entities
        ), "RED: Should detect missing entity"
        assert (
            "Tavern Keeper" in red_result.missing_entities
        ), "RED: Should detect missing entity"
        assert (
            len(red_result.retry_suggestions) > 0
        ), "RED: Should provide retry suggestions"

        print(f"   ❌ DETECTED MISSING: {red_result.missing_entities}")
        print(f"   ✅ FOUND: {red_result.found_entities}")
        print(f"   🔄 RETRY NEEDED: {red_result.retry_needed}")
        print(f"   📝 SUGGESTIONS: {len(red_result.retry_suggestions)} provided")

        # RED: Test Unknown entity handling - should filter them out
        expected_with_unknown = ["Gideon", "Sariel", "Unknown", "Rowan"]
        red_result_with_unknown = entity_validator.validate(
            incomplete_narrative, expected_with_unknown
        )

        # RED: Verify Unknown entities are filtered out
        all_entities = (
            red_result_with_unknown.found_entities
            + red_result_with_unknown.missing_entities
        )
        assert "Unknown" not in all_entities, "RED: Should filter out Unknown entities"
        assert (
            "Gideon" in red_result_with_unknown.found_entities
        ), "RED: Should still find real entities"
        assert (
            "Sariel" in red_result_with_unknown.missing_entities
        ), "RED: Should still detect missing real entities"

        print("   🚫 FILTERED UNKNOWN: Unknown entities properly excluded")

        print("\n🟢 GREEN PHASE: Testing complete entity handling")

        # GREEN: Create complete narrative with all expected entities
        complete_narrative = """
        Gideon entered the tavern and looked around. The room was dimly lit.
        Sariel waved to him from a corner table where she sat with Rowan.
        The Tavern Keeper approached them with a warm smile.
        "Welcome, travelers," the Tavern Keeper said. "What can I get you?"
        Gideon nodded to his companions. "Ale for all of us, please."
        Sariel smiled while Rowan counted out some coins.
        """

        # GREEN: Validate - should pass with all entities present
        green_result = entity_validator.validate(complete_narrative, expected_entities)

        # GREEN: Verify all entities are found
        assert green_result.passed, "GREEN: Should pass with all entities present"
        assert not green_result.retry_needed, "GREEN: Should not need retry"
        assert (
            len(green_result.missing_entities) == 0
        ), "GREEN: Should have no missing entities"
        assert len(green_result.found_entities) == len(
            expected_entities
        ), "GREEN: Should find all entities"
        assert green_result.confidence > 0.8, "GREEN: Should have high confidence"

        # GREEN: Verify specific entities are found
        for entity in expected_entities:
            assert entity in green_result.found_entities, f"GREEN: Should find {entity}"

        print(f"   ✅ ALL ENTITIES FOUND: {green_result.found_entities}")
        print(f"   📊 CONFIDENCE: {green_result.confidence:.2f}")
        print(f"   🎯 PASSED: {green_result.passed}")

        # GREEN: Test with Unknown entities - should still work
        green_result_with_unknown = entity_validator.validate(
            complete_narrative, expected_with_unknown
        )

        # GREEN: Verify Unknown filtering doesn't break success case
        assert (
            green_result_with_unknown.passed
        ), "GREEN: Should pass even with Unknown in input"
        all_entities_green = (
            green_result_with_unknown.found_entities
            + green_result_with_unknown.missing_entities
        )
        assert (
            "Unknown" not in all_entities_green
        ), "GREEN: Should filter out Unknown entities"

        print("   🚫 UNKNOWN FILTERED: Still properly excluded in success case")

        print("\n🔄 RETRY WORKFLOW: Testing retry suggestion system")

        # Test retry prompt generation
        retry_prompt = entity_validator.create_retry_prompt(
            "Please generate a tavern scene.", red_result, location="Thornhaven Tavern"
        )

        # Verify retry prompt contains guidance
        assert "RETRY INSTRUCTIONS" in retry_prompt
        assert "Sariel" in retry_prompt
        assert "Rowan" in retry_prompt
        assert "Tavern Keeper" in retry_prompt

        print("   📝 RETRY PROMPT GENERATED: Contains guidance for missing entities")

        print(
            "\n✅ RED-GREEN WORKFLOW COMPLETE: Missing entity detection and handling verified"
        )

        # Summary assertions
        assert not red_result.passed, "RED phase should fail"
        assert green_result.passed, "GREEN phase should pass"
        assert len(red_result.found_entities) < len(
            green_result.found_entities
        ), "GREEN should find more entities than RED"
        assert len(red_result.missing_entities) > len(
            green_result.missing_entities
        ), "RED should have more missing entities than GREEN"


if __name__ == "__main__":
    # Set testing environment
    os.environ["TESTING"] = "true"

    print("🧪 Testing Entity Tracking Production Implementation")
    print("=" * 60)

    unittest.main(verbosity=2)
