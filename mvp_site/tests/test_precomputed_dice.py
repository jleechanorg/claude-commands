"""
Tests for pre-computed dice results (backend-authoritative dice).

These tests verify that the backend correctly computes dice results
BEFORE calling the LLM, ensuring the LLM only needs to narrate
pre-determined outcomes.
"""

import unittest

from mvp_site.game_state import (
    compute_combat_results,
    detect_action_type,
    generate_pre_rolled_dice,
)


class TestDetectActionType(unittest.TestCase):
    """Tests for detect_action_type() function."""

    def test_detect_attack(self):
        """Test detection of attack actions."""
        actions = [
            "I attack the goblin",
            "Strike the enemy with my sword",
            "I slash at the orc",
            "Shoot an arrow at the guard",
            "I stab the bandit",
        ]
        for action in actions:
            result = detect_action_type(action)
            self.assertEqual(
                result["type"], "attack", f"Failed for action: {action}"
            )

    def test_detect_skill_check(self):
        """Test detection of skill check actions."""
        actions = [
            "I make a stealth check",
            "Try to pick the lock",
            "Attempt to persuade the merchant",
            "Roll for perception",
            "I check for traps using investigation",
        ]
        for action in actions:
            result = detect_action_type(action)
            self.assertEqual(
                result["type"], "skill_check", f"Failed for action: {action}"
            )

    def test_detect_saving_throw(self):
        """Test detection of saving throw actions."""
        actions = [
            "Make a dexterity saving throw",
            "Save against the fireball",
            "I resist the charm spell",
            "Dex save vs the trap",
        ]
        for action in actions:
            result = detect_action_type(action)
            self.assertEqual(
                result["type"], "saving_throw", f"Failed for action: {action}"
            )

    def test_detect_advantage(self):
        """Test detection of advantage conditions."""
        result = detect_action_type("I attack with advantage")
        self.assertTrue(result["has_advantage"])
        self.assertFalse(result["has_disadvantage"])

        result = detect_action_type("Sneak attack the guard")
        self.assertTrue(result["has_advantage"])

    def test_detect_disadvantage(self):
        """Test detection of disadvantage conditions."""
        result = detect_action_type("I attack with disadvantage")
        self.assertTrue(result["has_disadvantage"])
        self.assertFalse(result["has_advantage"])

    def test_advantage_disadvantage_cancel(self):
        """Test that advantage and disadvantage cancel out."""
        result = detect_action_type(
            "Attack with advantage while blinded"
        )
        self.assertFalse(result["has_advantage"])
        self.assertFalse(result["has_disadvantage"])

    def test_detect_skill_ability(self):
        """Test detection of skill and associated ability."""
        result = detect_action_type("I make a stealth check")
        self.assertEqual(result["type"], "skill_check")
        self.assertEqual(result["skill"], "stealth")
        self.assertEqual(result["ability"], "DEX")

        result = detect_action_type("Roll perception")
        self.assertEqual(result["type"], "skill_check")
        self.assertEqual(result["skill"], "perception")
        self.assertEqual(result["ability"], "WIS")

    def test_detect_other(self):
        """Test that non-roll actions return 'other'."""
        actions = [
            "I walk to the tavern",
            "What's in the room?",
            "I talk to the innkeeper",
            "Rest for the night",
        ]
        for action in actions:
            result = detect_action_type(action)
            self.assertEqual(
                result["type"], "other", f"Failed for action: {action}"
            )


class TestComputeAttackRoll(unittest.TestCase):
    """Tests for attack roll computation."""

    def setUp(self):
        """Set up test fixtures."""
        self.pre_rolled = {
            "d20": [5, 14, 18, 3, 20, 1, 12, 8],
            "d12": [7, 11, 4],
            "d10": [6, 9, 2],
            "d8": [6, 3, 8, 5],
            "d6": [4, 2, 6, 3, 5, 1],
            "d4": [3, 1, 4, 2],
            "d100": [42, 87],
        }
        self.player_char = {
            "stats": {
                "strength": 16,  # +3 modifier
                "dexterity": 14,  # +2 modifier
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8,
            },
            "level": 5,  # +3 proficiency
        }

    def test_simple_attack(self):
        """Test a simple attack without advantage."""
        action_info = {"type": "attack", "has_advantage": False, "has_disadvantage": False}
        result = compute_combat_results(
            action_info, self.pre_rolled, self.player_char, {"ac": 15}
        )

        attack = result["attack_roll"]
        self.assertIsNotNone(attack)
        self.assertEqual(attack["d20_values"], [5])
        self.assertEqual(attack["roll_used"], 5)
        # STR +3 + PROF +3 = +6, total = 5 + 6 = 11
        self.assertEqual(attack["total"], 11)
        self.assertEqual(attack["outcome"], "Miss")
        self.assertFalse(attack["is_hit"])
        self.assertIn("header_text", attack)

    def test_attack_with_advantage_uses_higher(self):
        """Test that advantage uses the higher of two d20 rolls."""
        action_info = {"type": "attack", "has_advantage": True, "has_disadvantage": False}
        result = compute_combat_results(
            action_info, self.pre_rolled, self.player_char, {"ac": 15}
        )

        attack = result["attack_roll"]
        self.assertIsNotNone(attack)
        self.assertEqual(attack["d20_values"], [5, 14])
        self.assertEqual(attack["roll_used"], 14)  # Higher of 5 and 14
        self.assertTrue(attack["advantage"])
        # total = 14 + 6 = 20
        self.assertEqual(attack["total"], 20)
        self.assertEqual(attack["outcome"], "Hit")
        self.assertTrue(attack["is_hit"])

    def test_attack_with_disadvantage_uses_lower(self):
        """Test that disadvantage uses the lower of two d20 rolls."""
        action_info = {"type": "attack", "has_advantage": False, "has_disadvantage": True}
        result = compute_combat_results(
            action_info, self.pre_rolled, self.player_char, {"ac": 10}
        )

        attack = result["attack_roll"]
        self.assertIsNotNone(attack)
        self.assertEqual(attack["d20_values"], [5, 14])
        self.assertEqual(attack["roll_used"], 5)  # Lower of 5 and 14
        self.assertTrue(attack["disadvantage"])

    def test_critical_hit(self):
        """Test that natural 20 is a critical hit."""
        # Use dice array that has 20 at position 0
        pre_rolled = {"d20": [20, 8, 12], "d8": [6, 3]}
        action_info = {"type": "attack", "has_advantage": False, "has_disadvantage": False}
        result = compute_combat_results(
            action_info, pre_rolled, self.player_char, {"ac": 25}
        )

        attack = result["attack_roll"]
        self.assertTrue(attack["is_crit"])
        self.assertEqual(attack["outcome"], "Critical Hit!")
        self.assertTrue(attack["is_hit"])  # Crits always hit

    def test_natural_one_auto_miss(self):
        """Test that natural 1 is an automatic miss."""
        # Use dice array that has 1 at position 0
        pre_rolled = {"d20": [1, 19, 15], "d8": [6]}
        action_info = {"type": "attack", "has_advantage": False, "has_disadvantage": False}
        result = compute_combat_results(
            action_info, pre_rolled, self.player_char, {"ac": 5}  # Very low AC
        )

        attack = result["attack_roll"]
        self.assertTrue(attack["is_fumble"])
        self.assertEqual(attack["outcome"], "Miss (Natural 1)")
        self.assertFalse(attack["is_hit"])  # Natural 1 always misses

    def test_damage_computed_on_hit(self):
        """Test that damage is computed when attack hits."""
        # Use high roll that will hit
        pre_rolled = {"d20": [18, 12], "d8": [6], "d6": [4, 3]}
        action_info = {"type": "attack", "has_advantage": False, "has_disadvantage": False}
        result = compute_combat_results(
            action_info, pre_rolled, self.player_char, {"ac": 15}
        )

        self.assertTrue(result["attack_roll"]["is_hit"])
        damage = result["damage_roll"]
        self.assertIsNotNone(damage)
        self.assertEqual(damage["dice_values"], [6])
        # 1d8 (6) + STR mod (+3) = 9
        self.assertEqual(damage["total"], 9)
        self.assertIn("header_text", damage)

    def test_no_damage_on_miss(self):
        """Test that damage is not computed when attack misses."""
        # Use low roll that will miss
        pre_rolled = {"d20": [3], "d8": [6]}
        action_info = {"type": "attack", "has_advantage": False, "has_disadvantage": False}
        result = compute_combat_results(
            action_info, pre_rolled, self.player_char, {"ac": 20}
        )

        self.assertFalse(result["attack_roll"]["is_hit"])
        self.assertIsNone(result["damage_roll"])

    def test_dice_consumed_tracking(self):
        """Test that dice consumption is tracked correctly."""
        action_info = {"type": "attack", "has_advantage": True, "has_disadvantage": False}
        # High roll to ensure hit and damage
        pre_rolled = {"d20": [15, 18], "d8": [6]}
        result = compute_combat_results(
            action_info, pre_rolled, self.player_char, {"ac": 10}
        )

        consumed = result["dice_consumed"]
        self.assertEqual(consumed["d20"], 2)  # Advantage uses 2
        self.assertEqual(consumed["d8"], 1)   # Damage uses 1


class TestComputeSkillCheck(unittest.TestCase):
    """Tests for skill check computation."""

    def setUp(self):
        """Set up test fixtures."""
        self.pre_rolled = generate_pre_rolled_dice()
        self.player_char = {
            "stats": {
                "strength": 10,
                "dexterity": 16,  # +3
                "constitution": 12,
                "intelligence": 14,  # +2
                "wisdom": 15,  # +2
                "charisma": 8,
            },
            "level": 3,  # +2 proficiency
        }

    def test_skill_check_with_proficiency(self):
        """Test skill check with proficiency bonus."""
        pre_rolled = {"d20": [12], "d8": []}
        action_info = {
            "type": "skill_check",
            "skill": "stealth",
            "ability": "DEX",
            "has_advantage": False,
            "has_disadvantage": False,
        }
        result = compute_combat_results(
            action_info, pre_rolled, self.player_char
        )

        check = result["skill_check"]
        self.assertIsNotNone(check)
        # DEX +3 + PROF +2 = +5, roll 12, total = 17
        self.assertEqual(check["ability_modifier"], 3)
        self.assertEqual(check["proficiency_bonus"], 2)
        self.assertEqual(check["total"], 17)
        # vs DC 15 (default)
        self.assertEqual(check["outcome"], "Success")

    def test_skill_check_failure(self):
        """Test skill check that fails."""
        pre_rolled = {"d20": [5], "d8": []}
        action_info = {
            "type": "skill_check",
            "skill": "perception",
            "ability": "WIS",
            "has_advantage": False,
            "has_disadvantage": False,
        }
        result = compute_combat_results(
            action_info, pre_rolled, self.player_char
        )

        check = result["skill_check"]
        # WIS +2 + PROF +2 = +4, roll 5, total = 9
        self.assertEqual(check["total"], 9)
        # vs DC 15 (default)
        self.assertEqual(check["outcome"], "Failure")
        self.assertFalse(check["is_success"])


class TestHeaderTextFormat(unittest.TestCase):
    """Tests for header text formatting."""

    def test_attack_header_format(self):
        """Test that attack header text is correctly formatted."""
        pre_rolled = {"d20": [14], "d8": [6]}
        player_char = {"stats": {"strength": 14}, "level": 1}  # +2 STR, +2 PROF
        action_info = {"type": "attack", "has_advantage": False, "has_disadvantage": False}

        result = compute_combat_results(
            action_info, pre_rolled, player_char, {"ac": 15}
        )

        header = result["attack_roll"]["header_text"]
        # Should contain: roll, modifier, total, AC, outcome
        self.assertIn("Attack:", header)
        self.assertIn("1d20", header)
        self.assertIn("vs AC 15", header)

    def test_advantage_header_shows_both_rolls(self):
        """Test that advantage header shows both d20 values."""
        pre_rolled = {"d20": [5, 14], "d8": [6]}
        player_char = {"stats": {"strength": 14}, "level": 1}
        action_info = {"type": "attack", "has_advantage": True, "has_disadvantage": False}

        result = compute_combat_results(
            action_info, pre_rolled, player_char, {"ac": 10}
        )

        header = result["attack_roll"]["header_text"]
        self.assertIn("[5,14]", header)
        self.assertIn("Advantage", header)


class TestOtherActionType(unittest.TestCase):
    """Tests for 'other' action type handling."""

    def test_other_returns_empty_results(self):
        """Test that 'other' action type returns empty results."""
        pre_rolled = generate_pre_rolled_dice()
        player_char = {"stats": {"strength": 10}, "level": 1}
        action_info = {"type": "other"}

        result = compute_combat_results(
            action_info, pre_rolled, player_char
        )

        self.assertIsNone(result["attack_roll"])
        self.assertIsNone(result["damage_roll"])
        self.assertIsNone(result["skill_check"])
        self.assertIsNone(result["saving_throw"])
        self.assertEqual(result["dice_consumed"], {})


if __name__ == "__main__":
    unittest.main()
