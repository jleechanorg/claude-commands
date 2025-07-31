"""Test enhanced Pydantic entities with integrated fields from entities_simple.py and game_state_instruction.md"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from schemas.entities_pydantic import NPC, HealthStatus, PlayerCharacter, Stats


class TestPydanticEntityIntegration(unittest.TestCase):
    """Test comprehensive Pydantic entity integration"""

    def setUp(self):
        """Set up common test data"""
        self.health = HealthStatus(hp=50, hp_max=50)

    def test_npc_gender_validation_mandatory(self):
        """Test that gender is mandatory for NPCs (critical for narrative consistency)"""
        # Test that we can create an NPC without gender first (to verify Pydantic allows it)
        # then check that our custom validation catches it
        try:
            npc = NPC(
                entity_id="npc_test_001",
                display_name="Test NPC",
                health=self.health,
                current_location="loc_test_001",
                gender=None,  # Explicitly set to None
            )
            # If we get here, the validation didn't catch it - this should be a failure case
            # but it might pass if our validator isn't triggering properly
            # In that case, we need to examine what's happening
            self.fail("NPC creation should have failed due to missing gender")
        except ValueError as e:
            assert "Gender is required for NPCs" in str(e)
            assert "narrative consistency" in str(e)
        except Exception as e:
            # If a different error occurs, let's see what it is
            self.fail(f"Unexpected error type: {type(e).__name__}: {e}")

    def test_npc_gender_validation_valid(self):
        """Test valid gender values for NPCs"""
        valid_genders = ["male", "female", "non-binary", "other"]

        for gender in valid_genders:
            npc = NPC(
                entity_id="npc_test_001",
                display_name="Test NPC",
                health=self.health,
                current_location="loc_test_001",
                gender=gender,
            )
            assert npc.gender == gender.lower()

    def test_npc_creative_gender_accepted(self):
        """Test that creative gender values are accepted (updated for permissive validation)"""
        npc = NPC(
            entity_id="npc_test_001",
            display_name="Test NPC",
            health=self.health,
            current_location="loc_test_001",
            gender="creative_gender",  # Now accepted
        )
        assert npc.gender == "creative_gender"

    def test_pc_gender_optional(self):
        """Test that gender is optional for PCs"""
        # Should work without gender
        pc = PlayerCharacter(
            entity_id="pc_test_001",
            display_name="Test PC",
            health=self.health,
            current_location="loc_test_001",
            gender=None,  # Explicitly optional for PCs
        )
        assert pc.gender is None

    def test_age_validation_fantasy_ranges(self):
        """Test age validation with fantasy-appropriate ranges"""
        # Valid ages
        valid_ages = [0, 16, 25, 100, 500, 1000, 50000]

        for age in valid_ages:
            npc = NPC(
                entity_id="npc_age_test_001",
                display_name="Age Test NPC",
                health=self.health,
                current_location="loc_test_001",
                gender="male",
                age=age,
            )
            assert npc.age == age

    def test_age_validation_invalid_ranges(self):
        """Test age validation rejects invalid ranges"""
        # Test negative age
        with self.assertRaises(ValueError) as context:
            NPC(
                entity_id="npc_negative_age_001",
                display_name="Negative Age NPC",
                health=self.health,
                current_location="loc_test_001",
                gender="female",
                age=-1,
            )
        assert "greater than or equal to 0" in str(context.exception)

        # Test unreasonably high age
        with self.assertRaises(ValueError) as context:
            NPC(
                entity_id="npc_too_old_001",
                display_name="Too Old NPC",
                health=self.health,
                current_location="loc_test_001",
                gender="male",
                age=100000,  # Exceeds 50,000 limit
            )
        assert "less than or equal to 50000" in str(context.exception)

    def test_mbti_validation(self):
        """Test MBTI personality type validation"""
        valid_mbti_types = [
            "INTJ",
            "INTP",
            "ENTJ",
            "ENTP",
            "INFJ",
            "INFP",
            "ENFJ",
            "ENFP",
            "ISTJ",
            "ISFJ",
            "ESTJ",
            "ESFJ",
            "ISTP",
            "ISFP",
            "ESTP",
            "ESFP",
        ]

        # Test valid MBTI types
        for mbti in valid_mbti_types:
            npc = NPC(
                entity_id="npc_mbti_test_001",
                display_name="MBTI Test NPC",
                health=self.health,
                current_location="loc_test_001",
                gender="male",
                mbti=mbti.lower(),  # Test case insensitivity
            )
            assert npc.mbti == mbti.lower().strip()  # We passed mbti.lower(), validation strips whitespace

        # Test creative personality description (now accepted)
        npc2 = NPC(
            entity_id="npc_invalid_mbti_001",
            display_name="Creative Personality NPC",
            health=self.health,
            current_location="loc_test_001",
            gender="female",
            mbti="analytical and methodical thinker",  # Now accepted
        )
        assert npc2.mbti == "analytical and methodical thinker"

    def test_alignment_validation(self):
        """Test D&D alignment validation"""
        valid_alignments = [
            "Lawful Good",
            "Neutral Good",
            "Chaotic Good",
            "Lawful Neutral",
            "True Neutral",
            "Chaotic Neutral",
            "Lawful Evil",
            "Neutral Evil",
            "Chaotic Evil",
        ]

        # Test valid alignments
        for alignment in valid_alignments:
            npc = NPC(
                entity_id="npc_alignment_test_001",
                display_name="Alignment Test NPC",
                health=self.health,
                current_location="loc_test_001",
                gender="male",
                alignment=alignment,
            )
            assert npc.alignment == alignment

        # Test creative alignment (now accepted)
        npc2 = NPC(
            entity_id="npc_creative_alignment_001",
            display_name="Creative Alignment NPC",
            health=self.health,
            current_location="loc_test_001",
            gender="female",
            alignment="Chaotic Awesome",  # Now accepted
        )
        assert npc2.alignment == "Chaotic Awesome"

    def test_dnd_fundamentals_integration(self):
        """Test D&D fundamental fields integration"""
        npc = NPC(
            entity_id="npc_dnd_test_001",
            display_name="D&D Test NPC",
            health=self.health,
            current_location="loc_test_001",
            gender="male",
            age=30,
            mbti="INTJ",
            alignment="Lawful Good",
            class_name="Fighter",
            background="Soldier",
        )

        # Verify all D&D fields are set correctly
        assert npc.gender == "male"
        assert npc.age == 30
        assert npc.mbti == "INTJ"
        assert npc.alignment == "Lawful Good"
        assert npc.class_name == "Fighter"
        assert npc.background == "Soldier"

    def test_defensive_numeric_conversion_stats(self):
        """Test defensive numeric conversion for stats"""
        # This test verifies that DefensiveNumericConverter is properly integrated
        # Note: The actual conversion behavior depends on DefensiveNumericConverter implementation
        stats = Stats(strength=15, dexterity=14, constitution=13)

        # Verify stats are set correctly and modifier calculation works
        assert stats.strength == 15
        assert stats.get_modifier("strength") == 2  # (15-10)//2 = 2
        assert stats.get_modifier("dexterity") == 2  # (14-10)//2 = 2
        assert stats.get_modifier("constitution") == 1  # (13-10)//2 = 1

    def test_defensive_numeric_conversion_health(self):
        """Test defensive numeric conversion for health values"""
        health = HealthStatus(hp=25, hp_max=30, temp_hp=5)

        assert health.hp == 25
        assert health.hp_max == 30
        assert health.temp_hp == 5

    def test_npc_creative_gender_values(self):
        """Test that creative gender values are now accepted"""
        test_genders = [
            "mixed",
            "fluid",
            "shapeshifter",
            "androgynous",
            "non-conforming",
        ]

        for i, gender in enumerate(test_genders):
            npc = NPC(
                entity_id=f"npc_creative_test_{i:03d}",
                display_name=f"Creative Gender Test NPC {i}",
                health=self.health,
                current_location="loc_test_001",
                gender=gender,
            )
            assert npc.gender == gender

    def test_npc_invalid_gender_types_still_fail(self):
        """Test that non-string gender values still fail validation"""
        with self.assertRaises(ValueError) as context:
            npc = NPC(
                entity_id="npc_invalid_test_001",
                display_name="Invalid Gender Type Test NPC",
                health=self.health,
                current_location="loc_test_001",
                gender=123,  # Wrong type - should fail
            )
        # Check that the error message indicates type validation failure
        assert "string_type" in str(context.exception)

    def test_creative_alignment_values(self):
        """Test that creative alignment values are accepted"""
        creative_alignments = [
            "Chaotic Awesome",
            "Lawful Annoying",
            "Neutral Mischievous",
            "True Lazy",
        ]

        for i, alignment in enumerate(creative_alignments):
            npc = NPC(
                entity_id=f"npc_alignment_test_{i:03d}",
                display_name=f"Creative Alignment Test NPC {i}",
                health=self.health,
                current_location="loc_test_001",
                gender="test",
                alignment=alignment,
            )
            assert npc.alignment == alignment

    def test_creative_mbti_values(self):
        """Test that creative personality descriptions are accepted"""
        creative_personalities = [
            "mysterious and brooding",
            "cheerful optimist",
            "ENFP",
            "analytical thinker",
        ]

        for i, mbti in enumerate(creative_personalities):
            npc = NPC(
                entity_id=f"npc_mbti_test_{i:03d}",
                display_name=f"Creative MBTI Test NPC {i}",
                health=self.health,
                current_location="loc_test_001",
                gender="test",
                mbti=mbti,
            )
            assert npc.mbti == mbti

    def test_comprehensive_npc_creation(self):
        """Test creating a comprehensive NPC with all enhanced fields"""
        npc = NPC(
            entity_id="npc_comprehensive_001",
            display_name="Comprehensive Test NPC",
            health=HealthStatus(hp=45, hp_max=45),
            current_location="loc_test_001",
            # Critical narrative consistency fields
            gender="female",
            age=35,
            # D&D fundamentals
            mbti="ENFJ",
            alignment="Neutral Good",
            class_name="Cleric",
            background="Acolyte",
            # Existing fields
            faction="Temple of Light",
            role="High Priestess",
            attitude_to_party="friendly",
            level=5,
            stats=Stats(wisdom=16, charisma=15),
        )

        # Verify comprehensive integration
        assert npc.display_name == "Comprehensive Test NPC"
        assert npc.gender == "female"
        assert npc.age == 35
        assert npc.mbti == "ENFJ"
        assert npc.alignment == "Neutral Good"
        assert npc.class_name == "Cleric"
        assert npc.background == "Acolyte"
        assert npc.faction == "Temple of Light"
        assert npc.role == "High Priestess"
        assert npc.attitude_to_party == "friendly"
        assert npc.level == 5
        assert npc.stats.wisdom == 16
        assert npc.stats.charisma == 15

    def test_backward_compatibility(self):
        """Test that existing NPC creation still works (backward compatibility)"""
        # This should still work for NPCs that provide gender
        npc = NPC(
            entity_id="npc_compat_001",
            display_name="Backward Compat NPC",
            health=self.health,
            current_location="loc_test_001",
            gender="male",  # Minimum required for NPCs
        )

        assert npc.display_name == "Backward Compat NPC"
        assert npc.gender == "male"
        assert npc.age is None  # Optional fields default to None
        assert npc.mbti is None
        assert npc.alignment is None


if __name__ == "__main__":
    unittest.main()
