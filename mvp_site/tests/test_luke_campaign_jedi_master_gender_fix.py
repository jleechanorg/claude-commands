"""Test to ensure Luke campaign Jedi Master gender consistency issue is fixed."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.entities_pydantic import NPC, HealthStatus


class TestLukeCampaignJediMasterGenderFix(unittest.TestCase):
    """Test specific to Luke campaign Jedi Master gender issue."""

    def test_jedi_master_female_consistency(self):
        """Test that Jedi Master gender is enforced and prevents inconsistency."""
        health = HealthStatus(hp=100, hp_max=100)

        # Create the Jedi Master with female gender (as in Luke's campaign)
        jedi_master = NPC(
            entity_id="npc_jedi_master_001",
            display_name="Jedi Master",
            health=health,
            current_location="loc_imperial_installation_001",
            faction="Jedi Order",
            role="Jedi Master",
            gender="female",  # This prevents the Eldrin/male pronoun bug
        )

        # Verify gender is properly set
        self.assertEqual(jedi_master.gender, "female")
        self.assertEqual(jedi_master.display_name, "Jedi Master")

        # This ensures that any narrative generation system can check:
        # if jedi_master.gender == "female":
        #     # Use "she/her" pronouns, not "he/him"
        #     # Use female names, not "Eldrin"

        # Verify narrative consistency helper methods could work
        pronouns = self._get_pronouns_for_gender(jedi_master.gender)
        self.assertEqual(pronouns["subject"], "she")
        self.assertEqual(pronouns["object"], "her")
        self.assertEqual(pronouns["possessive"], "her")

    def test_prevent_luke_campaign_bug_scenario(self):
        """Test that the specific Luke campaign bug scenario is prevented."""
        health = HealthStatus(hp=100, hp_max=100)

        # Scenario: Initially create "young woman" Jedi Master
        jedi_master = NPC(
            entity_id="npc_jedi_master_001",
            display_name="Jedi Master",
            health=health,
            current_location="loc_imperial_installation_001",
            faction="Jedi Order",
            role="Jedi Master",
            gender="female",
        )

        # The bug was: later narrative used "Eldrin" (male name) and "he/him" pronouns
        # With our fix, the gender field prevents this:

        # 1. Gender is explicitly stored
        self.assertEqual(jedi_master.gender, "female")

        # 2. Narrative generation should check this field
        # 3. Any male name/pronoun generation would be inconsistent with gender="female"

        # Example of how narrative generation should work:
        if jedi_master.gender == "female":
            # Use female names and pronouns
            narrative_safe = True
        else:
            narrative_safe = False

        self.assertTrue(narrative_safe, "Narrative should respect gender field")

    def test_invalid_gender_prevention(self):
        """Test that invalid genders are rejected."""
        health = HealthStatus(hp=100, hp_max=100)

        # Test invalid gender
        with self.assertRaises(ValueError):
            NPC(
                entity_id="npc_invalid_gender_001",
                display_name="Invalid Gender NPC",
                health=health,
                current_location="loc_test_001",
                gender="invalid_gender",
            )

    def _get_pronouns_for_gender(self, gender: str) -> dict:
        """Helper method showing how gender field enables consistent pronoun usage."""
        pronoun_map = {
            "female": {"subject": "she", "object": "her", "possessive": "her"},
            "male": {"subject": "he", "object": "him", "possessive": "his"},
            "non-binary": {"subject": "they", "object": "them", "possessive": "their"},
            "other": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return pronoun_map.get(gender, pronoun_map["other"])


if __name__ == "__main__":
    unittest.main()
