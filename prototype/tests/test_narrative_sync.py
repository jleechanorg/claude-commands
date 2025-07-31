"""
Test suite for the Narrative Sync Validator
Tests against real desync scenarios from mock and Sariel campaigns
"""

import unittest

from ..validators.narrative_sync_validator import (
    EntityContext,
    EntityPresenceType,
    NarrativeSyncValidator,
)


class TestNarrativeSyncValidator(unittest.TestCase):
    """Test the narrative sync validator against known desync patterns"""

    def setUp(self):
        self.validator = NarrativeSyncValidator()

    def test_thornwood_split_party(self):
        """Test Case 1: Split party from Thornwood Conspiracy"""
        narrative = """
        The wizard and cleric waited anxiously in the tavern, discussing their
        next move. The barkeep brought them another round of ale as they pored
        over the city maps.
        """

        expected_entities = ["Kira", "Aldric", "Finn"]

        result = self.validator.validate(narrative, expected_entities)

        # Should detect Kira as missing
        assert "Kira" in result.entities_missing
        assert "Aldric" in result.entities_found
        assert "Finn" in result.entities_found
        assert not result.all_entities_present

        # Check metadata
        assert result.metadata["entity_analysis"]["Kira"] == "missing"

    def test_sariel_ambiguous_presence(self):
        """Test Case 2: Ambiguous presence from Sariel campaign"""
        narrative = """
        Cassian's voice was tight and strained. "Uncle Titus is leading a
        punitive campaign against Mordan's entire clan. We will burn them

        """

        expected_entities = ["Cassian", "Titus"]

        result = self.validator.validate(narrative, expected_entities)

        # Should detect Cassian as present, Titus as mentioned-absent
        assert "Cassian" in result.entities_found
        assert (
            result.metadata["entity_analysis"]["Titus"] == "mentioned_absent"
        )

    def test_scene_transition_without_movement(self):
        """Test Case 3: Scene transition from Sariel campaign"""
        narrative = """
        You found yourself in Valerius's study, the cold precision of his
        workspace reflecting his analytical nature. He looked up from his
        reports with calculating eyes.
        """

        expected_entities = ["Sariel", "Valerius"]
        location = "Valerius's Study"

        result = self.validator.validate(narrative, expected_entities, location)

        # Should warn about unclear transition
        assert any("transition" in warning for warning in result.warnings)

    def test_physical_state_continuity(self):
        """Test Case 4: Physical state tracking"""
        narrative = """
        Sariel entered the chamber, her mourning robes trailing behind her.
        The old magister noticed her arrival and gestured to a chair.
        """

        expected_entities = ["Sariel", "Magister"]

        # Previous state had bandaged ear
        previous_states = {
            "Sariel": EntityContext(
                name="Sariel",
                presence_type=EntityPresenceType.PHYSICALLY_PRESENT,
                physical_markers=["bandaged ear", "trembling hands"],
            )
        }

        result = self.validator.validate(
            narrative, expected_entities, previous_states=previous_states
        )

        # Should warn about missing physical markers
        assert any("bandaged ear" in warning for warning in result.warnings)

    def test_invisible_character_detection(self):
        """Test Case 5: Invisible character from Darkmoor"""
        narrative = """
        Only Finn was visible in the moonlit courtyard as the guards
        approached with torches raised. The cleric stood calmly, prepared
        to bluff their way through the encounter.
        """

        expected_entities = ["Kira", "Aldric", "Finn"]

        result = self.validator.validate(narrative, expected_entities)

        # Special case: "Only Finn visible" implies others are present but hidden
        # This is a complex inference case
        assert "Finn" in result.entities_found
        # Kira and Aldric should be detected as ambiguous or missing
        self.assertTrue(
            result.metadata["entity_analysis"]["Kira"] in ["missing", "ambiguous"]
        )

    def test_perfect_entity_tracking(self):
        """Test Case 6: Good entity tracking example"""
        narrative = """
        Sariel clung to Cressida, burying her face in the soft silk of her
        shoulder. Cressida's hand stroked her hair gently, providing the
        first true comfort since Mother's death. "I don't blame you,"
        Cressida said firmly.
        """

        expected_entities = ["Sariel", "Cressida"]

        result = self.validator.validate(narrative, expected_entities)

        # Should detect both as physically present
        assert len(result.entities_found) == 2
        assert len(result.entities_missing) == 0
        assert result.all_entities_present
        assert result.confidence > 0.9

    def test_mass_combat_scenario(self):
        """Test Case 7: Mass combat from Frostholm Siege"""
        narrative = """
        The siege began at dawn. Soldiers poured through the breach while
        catapults continued their bombardment. The battlefield was chaos.
        """

        # Simplified for testing - in reality would have many more
        expected_entities = ["Captain Aldric", "Sergeant Vale", "Commander Roth"]

        result = self.validator.validate(narrative, expected_entities)

        # Should detect all as missing in this generic description
        assert len(result.entities_missing) == 3
        assert result.confidence < 0.1

    def test_entity_with_descriptors(self):
        """Test Case 8: Entity referenced by descriptor only"""
        narrative = """
        The wizard cast a protection spell while the rogue disappeared into
        the shadows. Meanwhile, the cleric prepared healing potions for the
        coming battle.
        """

        expected_entities = ["Aldric", "Kira", "Finn"]

        # Note: This tests if the validator can handle descriptor-only references
        # Current implementation would mark these as missing
        result = self.validator.validate(narrative, expected_entities)

        # All should be missing since only descriptors used
        assert len(result.entities_missing) == 3


class TestEntityContextTracking(unittest.TestCase):
    """Test entity context tracking functionality"""

    def setUp(self):
        self.validator = NarrativeSyncValidator()

    def test_emotional_state_extraction(self):
        """Test extraction of emotional states"""
        narrative = """
        Sariel stood there, grief-stricken and trembling. Her guilty
        expression told Cressida everything she needed to know.
        """

        # Test physical state extraction
        states = self.validator._extract_physical_states(narrative)

        # Should detect trembling associated with Sariel
        assert "Sariel" in states
        assert any("trembling" in s for s in states["Sariel"])

    def test_scene_transition_detection(self):
        """Test detection of scene transitions"""
        narrative = """
        Leaving the chamber behind, Sariel moved to the archives. She
        arrived at the dusty repository of ancient knowledge.
        """

        transitions = self.validator._detect_scene_transitions(narrative)

        assert len(transitions) > 0
        assert any("moved to" in t for t in transitions)
        assert any("arrived at" in t for t in transitions)

    def test_presence_type_analysis(self):
        """Test entity presence type detection"""
        test_cases = [
            {
                "narrative": "John entered the room and sat down.",
                "entity": "John",
                "expected": EntityPresenceType.PHYSICALLY_PRESENT,
            },
            {
                "narrative": "She thought of Marcus, who remained at the castle.",
                "entity": "Marcus",
                "expected": EntityPresenceType.MENTIONED_ABSENT,
            },
            {
                "narrative": "The letter mentioned Sarah's recent travels.",
                "entity": "Sarah",
                "expected": EntityPresenceType.AMBIGUOUS,
            },
        ]

        for case in test_cases:
            result = self.validator._analyze_entity_presence(
                case["narrative"], case["entity"]
            )
            assert result == case["expected"]


if __name__ == "__main__":
    unittest.main()
