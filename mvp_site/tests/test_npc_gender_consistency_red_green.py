"""Red-Green test for NPC gender consistency issue."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from pydantic import ValidationError
from schemas.entities_pydantic import NPC, HealthStatus


class TestNPCGenderConsistencyRedGreen(unittest.TestCase):
    """Red-Green test for NPC gender consistency."""

    def test_red_npc_missing_gender_field(self):
        """RED TEST: NPC creation should fail without mandatory gender field."""
        # Attempting to create an NPC without gender field should raise ValueError
        health = HealthStatus(hp=50, hp_max=50)

        with pytest.raises(ValidationError) as context:
            NPC(
                entity_id="npc_jedi_master_001",
                display_name="Jedi Master",
                health=health,
                current_location="loc_imperial_installation_001",
                faction="Jedi Order",
                role="Jedi Master",
                # Missing gender field - should fail
            )

        # Verify the error message mentions gender requirement
        assert "Gender is required for NPCs" in str(context.value)

    def test_green_npc_with_mandatory_gender_field(self):
        """GREEN TEST: NPC class should have mandatory gender field."""
        # After fix, NPC should require gender field
        health = HealthStatus(hp=50, hp_max=50)

        # This should work after the fix
        npc = NPC(
            entity_id="npc_jedi_master_001",
            display_name="Jedi Master",
            health=health,
            current_location="loc_imperial_installation_001",
            faction="Jedi Order",
            role="Jedi Master",
            gender="female",  # This should be required
        )

        # After fix, gender should be accessible
        if hasattr(npc, "gender"):
            assert npc.gender == "female"
        else:
            self.fail("NPC should have gender field after fix (GREEN test)")

    def test_green_npc_gender_validation(self):
        """GREEN TEST: Gender field should be validated."""
        health = HealthStatus(hp=50, hp_max=50)

        # Valid genders should work
        valid_genders = ["male", "female", "non-binary", "other"]

        for gender in valid_genders:
            npc = NPC(
                entity_id=f"npc_test_{gender.replace('-', '_')}_001",
                display_name=f"Test {gender.title()}",
                health=health,
                current_location="loc_test_001",
                gender=gender,
            )
            if hasattr(npc, "gender"):
                assert npc.gender == gender

    def test_green_npc_gender_prevents_inconsistency(self):
        """GREEN TEST: Gender field should prevent narrative inconsistency."""
        health = HealthStatus(hp=50, hp_max=50)

        # Create female Jedi Master
        jedi_master = NPC(
            entity_id="npc_jedi_master_001",
            display_name="Jedi Master",
            health=health,
            current_location="loc_imperial_installation_001",
            faction="Jedi Order",
            role="Jedi Master",
            gender="female",
        )

        # Verify gender is stored and accessible
        if hasattr(jedi_master, "gender"):
            assert jedi_master.gender == "female"

            # This ensures narrative generation can check:
            # if npc.gender == "female": use "she/her" pronouns
            # This prevents the Eldrin/male pronoun bug from Luke's campaign
        else:
            self.fail("Gender field should prevent narrative inconsistency")

    def test_edge_cases_gender_field(self):
        """Test edge cases for gender field."""
        health = HealthStatus(hp=30, hp_max=30)

        # Test empty string (should be handled)
        try:
            npc_empty = NPC(
                entity_id="npc_empty_gender_001",
                display_name="Empty Gender Test",
                health=health,
                current_location="loc_test_001",
                gender="",  # Edge case: empty string
            )
            # If gender field exists, empty string might need validation
            if hasattr(npc_empty, "gender"):
                assert npc_empty.gender is not None
        except ValueError:
            # It's okay if empty string raises validation error
            pass

        # Test None (should be handled)
        try:
            npc_none = NPC(
                entity_id="npc_none_gender_001",
                display_name="None Gender Test",
                health=health,
                current_location="loc_test_001",
                gender=None,  # Edge case: None
            )
            if hasattr(npc_none, "gender"):
                assert npc_none.gender is not None
        except (ValueError, TypeError):
            # It's okay if None raises validation error
            pass


if __name__ == "__main__":
    unittest.main()
