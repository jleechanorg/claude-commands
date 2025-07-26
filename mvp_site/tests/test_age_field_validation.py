"""Test age field validation in Character classes."""

import os
import sys
import unittest

from pydantic import ValidationError

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from schemas.entities_pydantic import NPC, HealthStatus, PlayerCharacter


class TestAgeFieldValidation(unittest.TestCase):
    """Test age field validation and functionality."""

    def setUp(self):
        """Set up common test data."""
        self.health = HealthStatus(hp=50, hp_max=50)

    def test_npc_with_age(self):
        """Test NPC creation with age field."""
        npc = NPC(
            entity_id="npc_aged_001",
            display_name="Aged Character",
            health=self.health,
            current_location="loc_test_001",
            gender="female",
            age=45,
        )

        self.assertEqual(npc.age, 45)
        self.assertEqual(npc.gender, "female")

    def test_npc_without_age(self):
        """Test NPC creation without age (should be allowed)."""
        npc = NPC(
            entity_id="npc_no_age_001",
            display_name="Ageless Character",
            health=self.health,
            current_location="loc_test_001",
            gender="male",
            # No age specified
        )

        self.assertIsNone(npc.age)
        self.assertEqual(npc.gender, "male")

    def test_pc_with_age(self):
        """Test PlayerCharacter creation with age field."""
        pc = PlayerCharacter(
            entity_id="pc_aged_001",
            display_name="Young Hero",
            health=self.health,
            current_location="loc_test_001",
            gender="non-binary",
            age=23,
        )

        self.assertEqual(pc.age, 23)
        self.assertEqual(pc.gender, "non-binary")

    def test_pc_without_age(self):
        """Test PlayerCharacter creation without age (should be allowed)."""
        pc = PlayerCharacter(
            entity_id="pc_no_age_001",
            display_name="Mysterious Hero",
            health=self.health,
            current_location="loc_test_001",
            gender="female",
            # No age specified
        )

        self.assertIsNone(pc.age)
        self.assertEqual(pc.gender, "female")

    def test_age_validation_negative(self):
        """Test that negative ages are rejected."""

        with self.assertRaises(ValidationError) as context:
            NPC(
                entity_id="npc_negative_age_001",
                display_name="Invalid Age",
                health=self.health,
                current_location="loc_test_001",
                gender="male",
                age=-5,
            )

        self.assertIn("greater than or equal to 0", str(context.exception))

    def test_age_validation_too_high(self):
        """Test that unreasonably high ages are rejected."""

        with self.assertRaises(ValidationError) as context:
            NPC(
                entity_id="npc_too_old_001",
                display_name="Too Old",
                health=self.health,
                current_location="loc_test_001",
                gender="female",
                age=100000,  # Beyond 50000 limit
            )

        self.assertIn("less than or equal to 50000", str(context.exception))

    def test_fantasy_ages(self):
        """Test that fantasy-appropriate ages work."""
        fantasy_ages = [1, 18, 100, 500, 1000, 5000, 50000]

        for age in fantasy_ages:
            npc = NPC(
                entity_id=f"npc_fantasy_{age}_001",
                display_name=f"Fantasy Being Age {age}",
                health=self.health,
                current_location="loc_test_001",
                gender="other",
                age=age,
            )

            self.assertEqual(npc.age, age)

    def test_age_type_validation(self):
        """Test that non-integer ages are rejected."""

        invalid_ages = [25.5, "young", [1, 2], {"age": 25}]

        for invalid_age in invalid_ages:
            with self.assertRaises(ValidationError):
                NPC(
                    entity_id="npc_invalid_type_001",
                    display_name="Invalid Age Type",
                    health=self.health,
                    current_location="loc_test_001",
                    gender="male",
                    age=invalid_age,
                )

    def test_narrative_consistency_helpers(self):
        """Test that age enables narrative consistency helpers."""
        # Young character
        young_npc = NPC(
            entity_id="npc_young_001",
            display_name="Young Apprentice",
            health=self.health,
            current_location="loc_test_001",
            gender="female",
            age=16,
        )

        # Middle-aged character
        middle_npc = NPC(
            entity_id="npc_middle_001",
            display_name="Experienced Warrior",
            health=self.health,
            current_location="loc_test_001",
            gender="male",
            age=45,
        )

        # Ancient character
        ancient_npc = NPC(
            entity_id="npc_ancient_001",
            display_name="Ancient Sage",
            health=self.health,
            current_location="loc_test_001",
            gender="non-binary",
            age=2000,
        )

        # Verify narrative consistency can be checked
        self.assertTrue(young_npc.age < 20)  # Can describe as "young"
        self.assertTrue(20 <= middle_npc.age < 60)  # Can describe as "middle-aged"
        self.assertTrue(ancient_npc.age > 500)  # Can describe as "ancient"

        # This prevents inconsistent descriptions like:
        # - 16-year-old described as "grizzled veteran"
        # - 2000-year-old described as "young apprentice"


if __name__ == "__main__":
    unittest.main()
