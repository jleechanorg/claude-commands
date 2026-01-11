import unittest
import sys
import os

# Ensure project root is in path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mvp_site.stats_display import (
    build_stats_summary,
    compute_saving_throws,
    extract_equipment_bonuses,
    extract_equipped_weapons,
    get_proficiency_bonus,
    get_spellcasting_ability,
)


class TestStatsDisplay(unittest.TestCase):
    def test_get_proficiency_bonus_coerces_and_clamps(self):
        """String, invalid, and high levels should coerce and clamp safely."""
        self.assertEqual(get_proficiency_bonus("5"), 3)
        self.assertEqual(get_proficiency_bonus("0"), 2)
        self.assertEqual(get_proficiency_bonus(25), 6)
        self.assertEqual(get_proficiency_bonus("abc"), 2)

    def test_get_spellcasting_ability_variations(self):
        """Covers multi-class parsing and additional class variants."""
        self.assertEqual(get_spellcasting_ability("Fighter/Wizard"), "int")
        self.assertEqual(get_spellcasting_ability("Rogue/Paladin"), "cha")
        self.assertEqual(get_spellcasting_ability("Blood Hunter"), "int")
        self.assertEqual(get_spellcasting_ability("Eldritch Knight"), "int")
        self.assertIsNone(get_spellcasting_ability("fighter"))

    def test_extract_equipped_weapons_handles_thrown(self):
        """Thrown weapons are tracked distinctly but are not finesse by default."""
        pc_data = {
            "equipment": {
                "main_hand": {
                    "name": "Handaxe",
                    "damage": "1d6 slashing",
                    "properties": ["Light", "Thrown"],
                    "equipped": True,
                }
            }
        }

        weapons = extract_equipped_weapons(pc_data)

        self.assertEqual(len(weapons), 1)
        self.assertTrue(weapons[0]["is_thrown"])
        self.assertFalse(weapons[0]["is_finesse"])
        self.assertFalse(weapons[0]["is_ranged"])

    def test_extract_equipped_weapons_uses_registry(self):
        """Registry item ids should resolve into weapon data."""
        pc_data = {
            "equipment": {"equipped": {"main_hand": "rapier_01"}},
            "item_registry": {
                "rapier_01": {
                    "name": "Registry Rapier",
                    "damage": "1d8 piercing",
                    "properties": ["Finesse"],
                }
            },
        }

        weapons = extract_equipped_weapons(pc_data)

        self.assertEqual(len(weapons), 1)
        self.assertEqual(weapons[0]["name"], "Registry Rapier")
        self.assertTrue(weapons[0]["is_finesse"])

    def test_extract_equipped_weapons_handles_missing_equipment(self):
        """Non-dict equipment data should return an empty list."""
        pc_data = {"equipment": "not_a_dict"}
        self.assertEqual(extract_equipped_weapons(pc_data), [])

    def test_build_stats_summary_uses_strength_for_thrown(self):
        """Thrown melee weapons without finesse should default to STR."""
        pc_data = {
            "level": "1",
            "stats": {"strength": 18, "dexterity": 10},
            "weapon_proficiencies": ["handaxe"],
            "equipment": {
                "main_hand": {
                    "name": "Handaxe",
                    "damage": "1d6 slashing",
                    "properties": "Light, Thrown",
                    "equipped": True,
                }
            },
        }

        summary = build_stats_summary({"player_character_data": pc_data})

        self.assertIn("Handaxe: +6 to hit | 1d6 slashing+4 damage", summary)

    def test_build_stats_summary_marks_non_proficient_weapon(self):
        """Weapons without proficiency should omit the proficiency bonus."""
        pc_data = {
            "level": 3,
            "stats": {"strength": 8, "dexterity": 16},
            "equipment": {
                "main_hand": {
                    "name": "Longbow",
                    "damage": "1d8 piercing",
                    "properties": ["ranged", "ammunition"],
                    "equipped": True,
                    "proficient": False,
                }
            },
        }

        summary = build_stats_summary({"player_character_data": pc_data})

        self.assertIn("Longbow: +3 to hit | 1d8 piercing+3 damage (not proficient)", summary)

    def test_extract_equipment_bonuses_caps_at_max(self):
        """Equipment bonuses should respect (Max X) caps from registry items."""
        pc_data = {
            "stats": {"strength": 16},
            "equipment": {"equipped": {"main_hand": "giant_belt"}},
            "item_registry": {
                "giant_belt": {"stats": "+4 STR (Max 19)"},
            },
        }

        bonuses = extract_equipment_bonuses(
            pc_data, base_stats={"str": 16}, item_registry=pc_data["item_registry"]
        )

        self.assertEqual(bonuses.get("str"), 3)

    def test_build_stats_summary_handles_multiclass_saving_throws(self):
        """Multiclass names should aggregate saving throw proficiencies."""
        pc_data = {
            "level": 5,
            "class_name": "Fighter/Wizard",
            "stats": {
                "strength": 16,
                "dexterity": 10,
                "constitution": 14,
                "intelligence": 16,
                "wisdom": 12,
                "charisma": 8,
            },
        }

        summary = build_stats_summary({"player_character_data": pc_data})

        # Proficient saves should include proficiency bonus (+3 at level 5)
        self.assertIn("● STR: +6", summary)  # STR mod +3 + proficiency
        self.assertIn("● CON: +5", summary)  # CON mod +2 + proficiency
        self.assertIn("● INT: +6", summary)  # INT mod +3 + proficiency
        self.assertIn("● WIS: +4", summary)  # WIS mod +1 + proficiency

    def test_build_stats_summary_handles_expertise_case_variants(self):
        """Expertise should be detected regardless of casing or string digits."""
        pc_data = {
            "level": 3,
            "class_name": "Rogue",
            "stats": {
                "strength": 10,
                "dexterity": 16,
                "constitution": 12,
                "intelligence": 10,
                "wisdom": 14,
                "charisma": 10,
            },
            "skills": {
                "perception": "Expertise",
                "investigation": " 2 ",
            },
        }

        summary = build_stats_summary({"player_character_data": pc_data})

        self.assertIn("◆ Perception:", summary)
        self.assertIn("◆ Investigation:", summary)

    def test_compute_saving_throws_structured_output(self):
        """Structured saving throws should include proficiency markers."""
        scores = {"str": 16, "dex": 10, "con": 14, "int": 16, "wis": 12, "cha": 8}

        saves = compute_saving_throws("Fighter/Wizard", scores, proficiency_bonus=3)

        str_save = next(s for s in saves if s["stat"] == "str")
        int_save = next(s for s in saves if s["stat"] == "int")
        wis_save = next(s for s in saves if s["stat"] == "wis")

        self.assertTrue(str_save["proficient"])
        self.assertEqual(str_save["bonus"], 6)  # +3 mod +3 prof
        self.assertEqual(int_save["bonus"], 6)  # +3 mod +3 prof
        self.assertEqual(wis_save["bonus"], 4)  # +1 mod +3 prof

    def test_build_stats_summary_handles_missing_damage(self):
        """Weapons without damage should display as '—' without modifiers."""
        
        pc_data = {
            "level": 1,
            "stats": {"strength": 14, "dexterity": 10},
            "equipment": {
                "main_hand": {
                    "name": "Shield",
                    "damage": "",  # Empty damage
                    "properties": [],
                    "equipped": True,
                }
            },
        }
        
        summary = build_stats_summary({"player_character_data": pc_data})
        
        self.assertIn("Shield: +4 to hit | — damage", summary)
        self.assertNotIn("—+2 damage", summary)

    def test_build_spells_summary_handles_malformed_slots(self):
        """Malformed spell slots with non-numeric strings should be ignored safely."""
        from mvp_site.stats_display import build_spells_summary
        
        game_state = {
            "player_character_data": {
                "spell_slots": {
                    "1": {"current": "invalid_string", "max": 4}
                }
            }
        }
        
        # Should not raise ValueError
        summary = build_spells_summary(game_state)
        # Malformed slot should be skipped
        self.assertNotIn("L1:", summary)


if __name__ == "__main__":
    unittest.main()
